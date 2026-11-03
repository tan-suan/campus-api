"""
订单明细表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 商品快照与小计计算、订单归属校验（经 order.user_id 隔离）、
  订单金额/件数联动等业务均在本层实现。

业务规则概览：
- 明细保存下单时的商品快照（名称、规格、图标、原价、成交价）与小计 subtotal = 成交价 × 数量。
- 成交价只取商品/规格表，不接受前端传值（防篡改）。
- 仅「待付款（pending）」订单可增减或修改明细；改动后自动重算订单
  goods_total / goods_count / pay_amount。
- 删除明细为软删除（is_deleted），保留历史痕迹。
"""

from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order, OrderStatus
from models.order_item import OrderItem
from repository.order_item_repository import OrderItemRepository
from repository.order_repository import OrderRepository
from schemas.order_item import (
    OrderItemCreate,
    OrderItemResponse,
    OrderItemUpdate,
)
from service.order_service import CENT, ZERO, OrderService, calc_pay_amount
from utils.custom_exceptions import ConflictException, NotFoundException


class OrderItemService:
    """
    订单明细表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 快照解析复用 OrderService.resolve_item_snapshot（同一套价格与规格校验）
    - 订单金额联动：改动明细后重算所属订单的金额与件数
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderItemRepository(db)
        self.order_repo = OrderRepository(db)
        self.order_service = OrderService(db)

    # -------------------- 业务校验 --------------------

    async def _get_owned_order(self, order_id: int, user_id: int) -> Order:
        """业务校验：订单存在且属于当前登录用户（越权统一 404）"""
        order = await self.order_repo.get(order_id)
        if order.user_id != user_id:
            raise NotFoundException("订单不存在")
        return order

    async def _get_owned(self, id: int, user_id: int) -> Tuple[OrderItem, Order]:
        """业务校验：明细存在，且其所属订单属于当前登录用户"""
        item = await self.repo.get(id)
        order = await self._get_owned_order(item.order_id, user_id)
        return item, order

    @staticmethod
    def _ensure_editable(order: Order) -> None:
        """业务校验：仅待付款订单可增减或修改明细"""
        if order.status is not OrderStatus.PENDING:
            raise ConflictException("仅待付款订单可增减明细，请先取消后重新下单")

    async def _recalc_order(self, order: Order) -> None:
        """
        业务处理：按未删除明细重算订单金额与件数

        goods_total = Σ subtotal；goods_count = Σ qty；
        pay_amount = goods_total + freight - discount（不小于 0）。
        """
        stmt = select(
            func.coalesce(func.sum(OrderItem.subtotal), 0),
            func.coalesce(func.sum(OrderItem.qty), 0),
        ).where(
            OrderItem.order_id == order.id,
            OrderItem.is_deleted == False,  # noqa: E712
        )
        total_raw, count_raw = (await self.db.execute(stmt)).one()

        goods_total = Decimal(total_raw or ZERO).quantize(CENT)
        goods_count = int(count_raw or 0)
        pay_amount = calc_pay_amount(
            goods_total,
            Decimal(order.freight or ZERO),
            Decimal(order.discount or ZERO),
        )
        await self.order_repo.update(
            order.id,
            {
                "goods_total": goods_total,
                "goods_count": goods_count,
                "pay_amount": pay_amount,
            },
        )

    # -------------------- 单条 CRUD --------------------

    async def create(self, user_id: int, data: OrderItemCreate) -> OrderItemResponse:
        """向订单追加明细（仅待付款订单；快照与成交价由服务端解析，并联动订单金额）"""
        order = await self._get_owned_order(data.order_id, user_id)
        self._ensure_editable(order)

        snapshot = await self.order_service.resolve_item_snapshot(
            data.goods_id, data.goods_spec_id, data.qty
        )
        obj = await self.repo.create({"order_id": order.id, **snapshot})
        await self._recalc_order(order)
        return OrderItemResponse.model_validate(obj)

    async def get_detail(self, id: int, user_id: int) -> OrderItemResponse:
        """详情（仅限本人订单下的明细）"""
        item, _ = await self._get_owned(id, user_id)
        return OrderItemResponse.model_validate(item)

    async def update(self, id: int, user_id: int, data: OrderItemUpdate) -> OrderItemResponse:
        """修改数量（仅限本人订单；按冻结的成交单价重算小计，并联动订单金额）"""
        item, order = await self._get_owned(id, user_id)
        self._ensure_editable(order)

        subtotal = (Decimal(item.price or ZERO) * data.qty).quantize(CENT)
        obj = await self.repo.update(id, {"qty": data.qty, "subtotal": subtotal})
        await self._recalc_order(order)
        return OrderItemResponse.model_validate(obj)

    async def delete(self, id: int, user_id: int) -> None:
        """删除明细（仅限本人订单；软删除，并联动订单金额）"""
        item, order = await self._get_owned(id, user_id)
        self._ensure_editable(order)
        await self.repo.delete(item.id)
        await self._recalc_order(order)

    # -------------------- 业务逻辑：列表 --------------------

    async def get_list(
        self,
        user_id: int,
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        分页列表（只返回当前登录用户订单下的明细）

        业务逻辑（本层）：
        - 通过 order_id 关联订单，按 order.user_id 强制隔离，排除软删除明细与订单
        - 支持按所属订单（order_id）过滤
        - 排序：最新明细优先（id 倒序）
        """
        filters = filters or {}
        conditions = [
            Order.user_id == user_id,
            Order.is_deleted == False,  # noqa: E712
            OrderItem.is_deleted == False,  # noqa: E712
        ]

        order_id = filters.get("order_id")
        if order_id is not None:
            conditions.append(OrderItem.order_id == order_id)

        stmt = (
            select(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .where(*conditions)
            .order_by(OrderItem.id.desc())
        )
        count_stmt = (
            select(func.count())
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .where(*conditions)
        )

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [OrderItemResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # ---------- 在下方添加商业逻辑方法 ----------
