"""
优惠券表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 编码唯一性、列表过滤、状态变更、软删除等业务均在本层实现。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.coupon import Coupon
from repository.coupon_repository import CouponRepository
from schemas.coupon import (
    CouponCreate,
    CouponResponse,
    CouponStatusUpdate,
    CouponUpdate,
)
from utils.custom_exceptions import ConflictException


class CouponService:
    """
    优惠券表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表及其他业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CouponRepository(db)

    # -------------------- 业务校验：编码唯一 --------------------

    async def _ensure_code_unique(self, code: Optional[str], exclude_id: Optional[int] = None) -> None:
        """业务校验：优惠券编码全局唯一（软删除的记录不占用编码）"""
        if not code:
            return
        stmt = select(Coupon.id).where(
            Coupon.code == code,
            Coupon.is_deleted == False,  # noqa: E712
        )
        if exclude_id is not None:
            stmt = stmt.where(Coupon.id != exclude_id)
        if await self.db.scalar(stmt):
            raise ConflictException("优惠券编码已存在")

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, data: CouponCreate) -> CouponResponse:
        """创建优惠券（编码唯一）"""
        await self._ensure_code_unique(data.code)
        try:
            obj = await self.repo.create(data)
        except IntegrityError:
            # 并发下由数据库唯一键兜底
            await self.db.rollback()
            raise ConflictException("优惠券编码已存在")
        return CouponResponse.model_validate(obj)

    async def get_detail(self, id: int) -> CouponResponse:
        """详情（单条，已软删除视为不存在）"""
        obj = await self.repo.get(id)
        return CouponResponse.model_validate(obj)

    async def update(self, id: int, data: CouponUpdate) -> CouponResponse:
        """更新（不含状态字段；状态请用 update_status）"""
        await self._ensure_code_unique(data.code, exclude_id=id)
        try:
            obj = await self.repo.update(id, data)
        except IntegrityError:
            await self.db.rollback()
            raise ConflictException("优惠券编码已存在")
        return CouponResponse.model_validate(obj)

    async def delete(self, id: int) -> None:
        """删除（软删除：仅置 is_deleted，不做物理删除）"""
        await self.repo.delete(id)

    # -------------------- 业务逻辑：列表 --------------------

    async def get_list(
        self,
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        分页列表

        业务逻辑（本层）：
        - 排除已软删除（is_deleted=True）的优惠券
        - 支持按状态（status）过滤
        - 支持券名称 / 编码关键字检索
        - 排序：最新创建优先（id 倒序）
        """
        filters = filters or {}
        conditions = [Coupon.is_deleted == False]  # noqa: E712

        status = filters.get("status")
        if status is not None:
            conditions.append(Coupon.status == status)

        keyword = filters.get("keyword")
        if keyword:
            like_value = f"%{keyword.strip()}%"
            conditions.append(or_(Coupon.name.like(like_value), Coupon.code.like(like_value)))

        stmt = select(Coupon).order_by(Coupon.id.desc())
        count_stmt = select(func.count()).select_from(Coupon)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [CouponResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # -------------------- 业务逻辑：状态/标识位 --------------------

    async def update_status(self, id: int, data: CouponStatusUpdate) -> CouponResponse:
        """
        修改状态（status：1可用 0停用）

        业务入口在 Service；持久化走 Repository.update（传入字段字典）。
        """
        obj = await self.repo.update(id, data.model_dump(exclude_unset=True))
        return CouponResponse.model_validate(obj)

    # ---------- 在下方添加商业逻辑方法 ----------
