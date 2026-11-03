"""
商品规格表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 与商品的关联（goods_id）校验、按商品过滤、状态变更、软删除等业务均在本层实现。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.goods import Goods
from models.goods_spec import GoodsSpec
from repository.goods_spec_repository import GoodsSpecRepository
from schemas.goods_spec import (
    GoodsSpecCreate,
    GoodsSpecResponse,
    GoodsSpecStatusUpdate,
    GoodsSpecUpdate,
)
from utils.custom_exceptions import NotFoundException


class GoodsSpecService:
    """
    商品规格表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表及其他业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GoodsSpecRepository(db)

    # -------------------- 业务校验（跨表）--------------------

    async def _ensure_goods_exists(self, goods_id: Optional[int]) -> None:
        """业务校验：关联商品必须存在且未被软删除"""
        if goods_id is None:
            return
        exists = await self.db.scalar(
            select(Goods.id).where(
                Goods.id == goods_id,
                Goods.is_deleted == False,  # noqa: E712
            )
        )
        if not exists:
            raise NotFoundException("商品不存在")

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, data: GoodsSpecCreate) -> GoodsSpecResponse:
        """创建商品规格（校验所属商品存在）"""
        await self._ensure_goods_exists(data.goods_id)
        obj = await self.repo.create(data)
        return GoodsSpecResponse.model_validate(obj)

    async def get_detail(self, id: int) -> GoodsSpecResponse:
        """详情（单条，已软删除视为不存在）"""
        obj = await self.repo.get(id)
        return GoodsSpecResponse.model_validate(obj)

    async def update(self, id: int, data: GoodsSpecUpdate) -> GoodsSpecResponse:
        """更新（不含状态字段；状态请用 update_status）"""
        await self._ensure_goods_exists(data.goods_id)
        obj = await self.repo.update(id, data)
        return GoodsSpecResponse.model_validate(obj)

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
        - 排除已软删除（is_deleted=True）的规格
        - 支持按所属商品（goods_id）、状态（status）过滤
        - 排序：sort 升序，其次 id 升序
        """
        filters = filters or {}
        conditions = [GoodsSpec.is_deleted == False]  # noqa: E712

        for field in ("goods_id", "status"):
            value = filters.get(field)
            if value is not None:
                conditions.append(getattr(GoodsSpec, field) == value)

        stmt = select(GoodsSpec).order_by(GoodsSpec.sort.asc(), GoodsSpec.id.asc())
        count_stmt = select(func.count()).select_from(GoodsSpec)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [GoodsSpecResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # -------------------- 业务逻辑：状态/标识位 --------------------

    async def update_status(self, id: int, data: GoodsSpecStatusUpdate) -> GoodsSpecResponse:
        """
        修改状态（status：1启用 0停用）

        业务入口在 Service；持久化走 Repository.update（传入字段字典）。
        """
        obj = await self.repo.update(
            id,
            data.model_dump(exclude_unset=True),
        )
        return GoodsSpecResponse.model_validate(obj)

    # ---------- 在下方添加商业逻辑方法 ----------
