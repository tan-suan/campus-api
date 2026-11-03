"""
订单表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 下单、金额计算、取货码生成、优惠券校验、状态机流转、取消/确认完成、用户隔离均在本层实现。

业务规则概览：
- 金额：goods_total = Σ 明细小计；freight = 自提 0 / 送寝固定配送费；
  discount = 优惠券可抵扣额（不超过商品金额）；pay_amount = goods_total + freight - discount（不小于 0）。
- 明细快照：商品名称、规格名称、图标、原价、成交单价在下单时冻结（读取商品/规格表，不信任前端价格）。
- 取货码：仅自提订单生成（A-xxxx）；送寝订单为空字符串。
- 状态机：pending → picking / canceled；picking → done / canceled；done / canceled 为终态。
  进入 picking 记录支付时间，进入 done 记录完成时间，进入 canceled 记录取消时间。
- 库存扣减不在本层范围内（由库存/秒杀流程单独处理）。
"""

import secrets
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.address import Address
from models.coupon import Coupon
from models.goods import Goods
from models.goods_spec import GoodsSpec
from models.order import Order, OrderMode, OrderStatus
from models.order_item import OrderItem
from models.pickup_point import PickupPoint
from repository.order_repository import OrderRepository
from schemas.order import (
    OrderCreate,
    OrderDetailResponse,
    OrderItemInput,
    OrderResponse,
    OrderStatusUpdate,
    OrderUpdate,
)
from schemas.order_item import OrderItemResponse
from utils.custom_exceptions import ConflictException, NotFoundException, ValidationException
from utils.ids import new_business_id

# -------------------- 业务常量 --------------------

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
# 配送费：校内自提免费，送到寝室收取固定配送费
PICKUP_FREIGHT = Decimal("0.00")
DORM_FREIGHT = Decimal("2.00")
# 取货码前缀（自提订单到店报码取货）
PICKUP_CODE_PREFIX = "A-"
# 订单号生成失败（并发生成重复号）时的重试次数
ORDER_NO_RETRY = 3

# 状态机：当前状态 -> 允许流转到的目标状态
ALLOWED_TRANSITIONS: Dict[OrderStatus, set] = {
    OrderStatus.PENDING: {OrderStatus.PICKING, OrderStatus.CANCELED},
    OrderStatus.PICKING: {OrderStatus.DONE, OrderStatus.CANCELED},
    OrderStatus.DONE: set(),
    OrderStatus.CANCELED: set(),
}

# 允许修改备注/期望时间等非金额字段的状态
EDITABLE_STATUSES = (OrderStatus.PENDING, OrderStatus.PICKING)


def to_decimal(value: Any) -> Decimal:
    """把数值安全转换为 Decimal（None → 0.00，兼容 int / float / str / Decimal）"""
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def calc_freight(mode: Any) -> Decimal:
    """业务规则：按取货方式计算配送费（校内自提 0，送到寝室固定配送费）"""
    return PICKUP_FREIGHT if OrderMode(mode) is OrderMode.PICKUP else DORM_FREIGHT


def calc_pay_amount(goods_total: Any, freight: Any, discount: Any) -> Decimal:
    """业务规则：实付金额 = 商品金额 + 配送费 - 优惠减免（不小于 0）"""
    amount = to_decimal(goods_total) + to_decimal(freight) - to_decimal(discount)
    return amount.quantize(CENT) if amount > ZERO else ZERO


class OrderService:
    """
    订单表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 下单、金额、状态机、取消/完成等业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderRepository(db)

    # -------------------- 业务校验：用户隔离 --------------------

    async def _get_owned(self, id: int, user_id: int) -> Order:
        """
        取单条并校验归属：只能操作自己的订单

        越权访问统一按「不存在」处理，避免泄露他人订单是否存在。
        """
        obj = await self.repo.get(id)
        if obj.user_id != user_id:
            raise NotFoundException("订单不存在")
        return obj

    # -------------------- 业务逻辑：下单前解析 --------------------

    async def _resolve_delivery(
        self,
        user_id: int,
        mode: OrderMode,
        pickup_point_id: Optional[int],
        address_id: Optional[int],
    ) -> tuple[str, str]:
        """
        业务处理：校验取货方式对应的自提点 / 收货地址，并返回名称快照

        返回 (pickup_point_name, address_text)。
        """
        if mode is OrderMode.PICKUP:
            if not pickup_point_id:
                raise ValidationException("自提订单请先选择自提点")
            point = await self.db.scalar(
                select(PickupPoint).where(
                    PickupPoint.id == pickup_point_id,
                    PickupPoint.is_deleted == False,  # noqa: E712
                )
            )
            if not point:
                raise NotFoundException("自提点不存在")
            if point.status != 1:
                raise ValidationException("自提点已停用，请重新选择")
            return point.name, ""

        if not address_id:
            raise ValidationException("送寝订单请先选择收货地址")
        address = await self.db.scalar(
            select(Address).where(
                Address.id == address_id,
                Address.is_deleted == False,  # noqa: E712
            )
        )
        if not address or address.user_id != user_id:
            raise NotFoundException("收货地址不存在")
        text = (
            f"{address.receiver_name} {address.phone} "
            f"{address.campus}{address.building}{address.detail}"
        ).strip()
        return "", text

    async def resolve_item_snapshot(
        self, goods_id: int, goods_spec_id: Optional[int], qty: int
    ) -> Dict[str, Any]:
        """
        业务处理：解析单条明细的商品快照与成交价（下单与追加明细共用）

        返回可直接写入 order_item 的字段字典（含小计 subtotal）。
        只信任商品/规格表中的价格，前端传价格无效（Schema 已禁传）。
        """
        goods = await self.db.scalar(
            select(Goods).where(
                Goods.id == goods_id,
                Goods.is_deleted == False,  # noqa: E712
            )
        )
        if not goods:
            raise NotFoundException(f"商品不存在（ID={goods_id}）")
        if goods.status != 1:
            raise ValidationException(f"商品已下架：{goods.name}")

        price = Decimal(goods.price or ZERO)
        origin_price = Decimal(goods.origin_price or ZERO)
        spec_name = "默认"
        resolved_spec_id: Optional[int] = None

        if goods_spec_id is not None:
            spec = await self.db.scalar(
                select(GoodsSpec).where(
                    GoodsSpec.id == goods_spec_id,
                    GoodsSpec.is_deleted == False,  # noqa: E712
                )
            )
            if not spec:
                raise NotFoundException("商品规格不存在")
            if spec.goods_id != goods.id:
                raise ValidationException("该规格不属于所选商品")
            if spec.status != 1:
                raise ValidationException(f"规格已停用：{spec.spec_name}")
            price = Decimal(spec.price or ZERO)
            origin_price = Decimal(spec.origin_price or ZERO)
            spec_name = spec.spec_name
            resolved_spec_id = spec.id

        return {
            "goods_id": goods.id,
            "goods_spec_id": resolved_spec_id,
            "goods_name": goods.name,
            "spec_name": spec_name,
            "emoji": goods.emoji or "",
            "tint": goods.tint or "",
            "price": price,
            "origin_price": origin_price,
            "qty": qty,
            "subtotal": (price * qty).quantize(CENT),
        }

    async def _resolve_items(self, items: list[OrderItemInput]) -> list[Dict[str, Any]]:
        """业务处理：批量解析下单明细的快照与成交价"""
        return [
            await self.resolve_item_snapshot(item.goods_id, item.goods_spec_id, item.qty)
            for item in items
        ]

    async def _resolve_discount(self, coupon_id: Optional[int], goods_total: Decimal) -> Decimal:
        """
        业务处理：校验优惠券并计算可抵扣金额

        规则：券存在、启用、在有效期内、商品金额达到门槛；抵扣额不超过商品金额。
        """
        if coupon_id is None:
            return ZERO

        coupon = await self.db.scalar(
            select(Coupon).where(
                Coupon.id == coupon_id,
                Coupon.is_deleted == False,  # noqa: E712
            )
        )
        if not coupon:
            raise NotFoundException("优惠券不存在")
        if coupon.status != 1:
            raise ValidationException("优惠券不可用")

        now = datetime.now()
        if coupon.start_time and now < coupon.start_time:
            raise ValidationException("优惠券尚未生效")
        if coupon.end_time and now > coupon.end_time:
            raise ValidationException("优惠券已过期")

        threshold = Decimal(coupon.threshold or ZERO)
        if goods_total < threshold:
            raise ValidationException(f"未达到优惠券使用门槛（满 {threshold} 元可用）")

        amount = Decimal(coupon.amount or ZERO)
        return min(amount, goods_total).quantize(CENT)

    # -------------------- 业务逻辑：编号与取货码 --------------------

    @staticmethod
    def _generate_order_no() -> str:
        """业务处理：生成订单号（CF + 时间戳 + 随机数，唯一约束由数据库兜底）"""
        return new_business_id(prefix="CF", max_length=32)

    @staticmethod
    def _generate_pickup_code() -> str:
        """业务处理：生成自提取货码，如 A-1088"""
        return f"{PICKUP_CODE_PREFIX}{secrets.randbelow(10000):04d}"

    # -------------------- 业务逻辑：下单 --------------------

    async def create(self, user_id: int, data: OrderCreate) -> OrderDetailResponse:
        """
        下单（归属当前登录用户）

        1. 校验取货方式对应的自提点 / 收货地址，生成快照
        2. 校验商品与规格，冻结商品快照与成交价，计算明细小计
        3. 计算 goods_total / freight / discount / pay_amount
        4. 生成订单号与取货码，落库订单主记录后写入明细
        """
        mode = OrderMode(data.mode)
        pickup_point_name, address_text = await self._resolve_delivery(
            user_id, mode, data.pickup_point_id, data.address_id
        )
        items = await self._resolve_items(data.items)

        goods_total = sum((item["subtotal"] for item in items), ZERO)
        goods_count = sum(item["qty"] for item in items)
        freight = calc_freight(mode)
        discount = await self._resolve_discount(data.coupon_id, goods_total)
        pay_amount = calc_pay_amount(goods_total, freight, discount)

        payload: Dict[str, Any] = {
            "status": OrderStatus.PENDING,
            "mode": mode,
            "pickup_point_id": data.pickup_point_id if mode is OrderMode.PICKUP else None,
            "pickup_point_name": pickup_point_name,
            "address_id": data.address_id if mode is OrderMode.DORM else None,
            "address_text": address_text,
            "pickup_code": self._generate_pickup_code() if mode is OrderMode.PICKUP else "",
            "expect_time": data.expect_time,
            "goods_total": goods_total,
            "freight": freight,
            "discount": discount,
            "pay_amount": pay_amount,
            "coupon_id": data.coupon_id,
            "pay_method": data.pay_method,
            "remark": data.remark,
            "goods_count": goods_count,
        }

        order: Optional[Order] = None
        for _ in range(ORDER_NO_RETRY):
            payload["order_no"] = self._generate_order_no()
            try:
                order = await self.repo.create(payload, user_id)
                break
            except IntegrityError:
                # 订单号唯一键冲突（并发下极小概率）：回滚后重新生成
                await self.db.rollback()
        if order is None:
            raise ConflictException("订单号生成冲突，请稍后重试")

        rows = [OrderItem(order_id=order.id, **item) for item in items]
        self.db.add_all(rows)
        await self.db.commit()

        return self._to_detail(order, rows)

    # -------------------- 业务逻辑：明细与响应组装 --------------------

    async def _load_items(self, order_id: int) -> list[OrderItem]:
        """业务查询：读取订单的未删除明细（按明细ID升序）"""
        rows = (
            await self.db.execute(
                select(OrderItem)
                .where(
                    OrderItem.order_id == order_id,
                    OrderItem.is_deleted == False,  # noqa: E712
                )
                .order_by(OrderItem.id.asc())
            )
        ).scalars().all()
        return list(rows)

    @staticmethod
    def _to_detail(order: Order, items: list[OrderItem]) -> OrderDetailResponse:
        """组装订单详情响应（主表 + 明细快照）"""
        base = OrderResponse.model_validate(order)
        return OrderDetailResponse(
            **base.model_dump(),
            items=[OrderItemResponse.model_validate(item) for item in items],
        )

    async def get_detail(self, id: int, user_id: int) -> OrderDetailResponse:
        """详情（仅限本人订单，含明细快照）"""
        order = await self._get_owned(id, user_id)
        items = await self._load_items(order.id)
        return self._to_detail(order, items)

    async def update(self, id: int, user_id: int, data: OrderUpdate) -> OrderDetailResponse:
        """
        更新备注 / 期望时间 / 支付方式（仅限本人，且仅待付款、待取货订单）

        金额、明细与取货方式在下单时冻结，不支持通过本接口修改。
        """
        order = await self._get_owned(id, user_id)
        if order.status not in EDITABLE_STATUSES:
            raise ConflictException("已完成或已取消的订单不可修改")
        obj = await self.repo.update(id, data)
        items = await self._load_items(obj.id)
        return self._to_detail(obj, items)

    async def delete(self, id: int, user_id: int) -> None:
        """删除订单（仅限本人；软删除，明细保留历史记录）"""
        await self._get_owned(id, user_id)
        await self.repo.delete(id)

    # -------------------- 业务逻辑：列表 --------------------

    async def get_list(
        self,
        user_id: int,
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        分页列表（只返回当前登录用户的订单）

        业务逻辑（本层）：
        - 强制按 user_id 隔离，排除已软删除订单
        - 支持按状态（status）、取货方式（mode）过滤，支持订单号关键字检索
        - 排序：最新下单优先（id 倒序）
        """
        filters = filters or {}
        conditions = [
            Order.user_id == user_id,
            Order.is_deleted == False,  # noqa: E712
        ]

        status = filters.get("status")
        if status is not None:
            conditions.append(Order.status == status)

        mode = filters.get("mode")
        if mode is not None:
            conditions.append(Order.mode == mode)

        keyword = filters.get("keyword")
        if keyword:
            conditions.append(Order.order_no.like(f"%{keyword.strip()}%"))

        stmt = select(Order).order_by(Order.id.desc())
        count_stmt = select(func.count()).select_from(Order)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [OrderResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # -------------------- 业务逻辑：状态流转 --------------------

    async def update_status(
        self, id: int, user_id: int, data: OrderStatusUpdate
    ) -> OrderDetailResponse:
        """
        状态变更（专用入口，按状态机校验，仅限本人订单）

        - pending → picking：记录支付时间
        - picking → done：记录完成时间
        - pending / picking → canceled：记录取消时间
        - 目标状态与当前一致时幂等返回，不报错
        """
        order = await self._get_owned(id, user_id)
        target = OrderStatus(data.status)

        if target is order.status:
            items = await self._load_items(order.id)
            return self._to_detail(order, items)

        if target not in ALLOWED_TRANSITIONS[order.status]:
            raise ConflictException(
                f"订单状态不允许从 {order.status.value} 变更为 {target.value}"
            )

        fields: Dict[str, Any] = {"status": target}
        now = datetime.now()
        if target is OrderStatus.PICKING:
            fields["pay_time"] = now
        elif target is OrderStatus.DONE:
            fields["done_time"] = now
        elif target is OrderStatus.CANCELED:
            fields["cancel_time"] = now

        obj = await self.repo.update(id, fields)
        items = await self._load_items(obj.id)
        return self._to_detail(obj, items)

    async def cancel(self, id: int, user_id: int) -> OrderDetailResponse:
        """取消订单（业务入口：仅待付款 / 待取货可取消，记录取消时间）"""
        order = await self._get_owned(id, user_id)
        if order.status is OrderStatus.CANCELED:
            raise ConflictException("订单已取消，请勿重复操作")
        if OrderStatus.CANCELED not in ALLOWED_TRANSITIONS[order.status]:
            raise ConflictException(f"订单当前状态（{order.status.value}）不可取消")

        obj = await self.repo.update(
            id, {"status": OrderStatus.CANCELED, "cancel_time": datetime.now()}
        )
        items = await self._load_items(obj.id)
        return self._to_detail(obj, items)

    async def confirm_done(self, id: int, user_id: int) -> OrderDetailResponse:
        """确认完成（业务入口：仅待取货订单可确认完成，记录完成时间）"""
        order = await self._get_owned(id, user_id)
        if order.status is not OrderStatus.PICKING:
            raise ConflictException("仅待取货订单可确认完成")

        obj = await self.repo.update(
            id, {"status": OrderStatus.DONE, "done_time": datetime.now()}
        )
        items = await self._load_items(obj.id)
        return self._to_detail(obj, items)

    # ---------- 在下方添加商业逻辑方法 ----------
