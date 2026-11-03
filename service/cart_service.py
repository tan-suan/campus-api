"""
购物车表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 用户归属隔离、加购数量累加、规格快照与校验、数量修改、勾选切换、删除条目等业务均在本层实现。

业务规则概览：
- 同一「用户 + 商品 + 规格」只保留一条记录：重复加购时累加 qty 并自动勾选。
- goods_spec_id 为空表示默认规格；因 MySQL 唯一索引允许多个 NULL，
  该场景的唯一性由本层 select 查询显式保证（不依赖数据库唯一键）。
- 单条数量上限 999，超出返回 422。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.cart import Cart
from models.goods import Goods
from models.goods_spec import GoodsSpec
from repository.cart_repository import CartRepository
from schemas.cart import (
    CartCreate,
    CartResponse,
    CartSelectedUpdate,
    CartUpdate,
)
from utils.custom_exceptions import ConflictException, NotFoundException, ValidationException

# 单条购物车数量上限（业务常量）
MAX_QTY = 999
# 未指定规格时写入的规格名称快照
DEFAULT_SPEC_NAME = "默认"


class CartService:
    """
    购物车表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 耦合业务（加购累加、数量、勾选、用户隔离）：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CartRepository(db)

    # -------------------- 业务校验 --------------------

    async def _get_owned(self, id: int, user_id: int) -> Cart:
        """
        取单条并校验归属：只能操作自己的购物车条目

        越权访问统一按「不存在」处理，避免泄露他人购物车数据。
        """
        obj = await self.repo.get(id)
        if obj.user_id != user_id:
            raise NotFoundException("购物车条目不存在")
        return obj

    async def _ensure_goods_exists(self, goods_id: int) -> None:
        """业务校验：商品必须存在且未被软删除"""
        exists = await self.db.scalar(
            select(Goods.id).where(
                Goods.id == goods_id,
                Goods.is_deleted == False,  # noqa: E712
            )
        )
        if not exists:
            raise NotFoundException("商品不存在")

    async def _resolve_spec_name(self, goods_id: int, goods_spec_id: Optional[int]) -> str:
        """
        业务处理：解析规格名称快照

        - 未指定规格：返回默认快照名
        - 指定规格：规格必须存在且未被软删除，并且属于当前商品
        """
        if goods_spec_id is None:
            return DEFAULT_SPEC_NAME

        spec = await self.db.scalar(
            select(GoodsSpec).where(
                GoodsSpec.id == goods_spec_id,
                GoodsSpec.is_deleted == False,  # noqa: E712
            )
        )
        if not spec:
            raise NotFoundException("商品规格不存在")
        if spec.goods_id != goods_id:
            raise ValidationException("该规格不属于所选商品")
        return spec.spec_name

    async def _find_entry(
        self, user_id: int, goods_id: int, goods_spec_id: Optional[int]
    ) -> Optional[Cart]:
        """业务查询：定位同一「用户 + 商品 + 规格」的购物车条目（规格为空需用 IS NULL）"""
        conditions = [Cart.user_id == user_id, Cart.goods_id == goods_id]
        if goods_spec_id is None:
            conditions.append(Cart.goods_spec_id.is_(None))
        else:
            conditions.append(Cart.goods_spec_id == goods_spec_id)
        return await self.db.scalar(select(Cart).where(*conditions))

    async def _accumulate(self, entry: Cart, add_qty: int) -> CartResponse:
        """业务处理：同规格重复加购时累加数量（并自动勾选），超出上限报 422"""
        total = (entry.qty or 0) + add_qty
        if total > MAX_QTY:
            raise ValidationException(f"单条购物车数量不能超过 {MAX_QTY}")
        obj = await self.repo.update(entry.id, {"qty": total, "selected": True})
        return CartResponse.model_validate(obj)

    # -------------------- 单条 CRUD 与加购业务 --------------------

    async def create(self, user_id: int, data: CartCreate) -> CartResponse:
        """
        加购（归属当前登录用户）

        - 商品/规格存在性校验，规格快照由服务端写入
        - 同一「用户 + 商品 + 规格」已存在时累加数量，不新增条目
        """
        await self._ensure_goods_exists(data.goods_id)
        spec_name = await self._resolve_spec_name(data.goods_id, data.goods_spec_id)

        existing = await self._find_entry(user_id, data.goods_id, data.goods_spec_id)
        if existing:
            return await self._accumulate(existing, data.qty)

        try:
            obj = await self.repo.create(data, user_id, spec_name)
        except IntegrityError:
            # 并发加购时由数据库唯一键兜底：回滚后改为累加
            await self.db.rollback()
            existing = await self._find_entry(user_id, data.goods_id, data.goods_spec_id)
            if not existing:
                raise ConflictException("购物车条目冲突，请重试")
            return await self._accumulate(existing, data.qty)

        return CartResponse.model_validate(obj)

    async def get_detail(self, id: int, user_id: int) -> CartResponse:
        """详情（仅限本人购物车）"""
        obj = await self._get_owned(id, user_id)
        return CartResponse.model_validate(obj)

    async def update(self, id: int, user_id: int, data: CartUpdate) -> CartResponse:
        """修改购买数量（仅限本人购物车；勾选请用 update_selected）"""
        await self._get_owned(id, user_id)
        obj = await self.repo.update(id, data)
        return CartResponse.model_validate(obj)

    async def update_selected(
        self, id: int, user_id: int, data: CartSelectedUpdate
    ) -> CartResponse:
        """勾选 / 取消勾选结算（仅限本人购物车）"""
        await self._get_owned(id, user_id)
        obj = await self.repo.update(id, data.model_dump(exclude_unset=True))
        return CartResponse.model_validate(obj)

    async def delete(self, id: int, user_id: int) -> None:
        """删除条目（仅限本人购物车；本表无软删字段，直接物理删除）"""
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
        分页列表（只返回当前登录用户的购物车条目）

        业务逻辑（本层）：
        - 强制按 user_id 隔离
        - 支持按勾选状态（selected）、商品（goods_id）过滤
        - 排序：最近更新优先（id 倒序）
        """
        filters = filters or {}
        conditions = [Cart.user_id == user_id]

        for field in ("selected", "goods_id"):
            value = filters.get(field)
            if value is not None:
                conditions.append(getattr(Cart, field) == value)

        stmt = select(Cart).order_by(Cart.id.desc())
        count_stmt = select(func.count()).select_from(Cart)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [CartResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # ---------- 在下方添加商业逻辑方法 ----------
