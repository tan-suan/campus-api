"""
商品表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 秒杀（flash）、热销（hot）、上下架（status）、软删除等业务逻辑均在本层实现：
  列表过滤与关键字检索、排除已软删除数据、分类存在性校验、专用改状态入口。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.category import Category
from models.goods import Goods
from repository.goods_repository import GoodsRepository
from schemas.goods import (
    GoodsCreate,
    GoodsResponse,
    GoodsStatusUpdate,
    GoodsUpdate,
)
from utils.custom_exceptions import NotFoundException


class GoodsService:
    """
    商品表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表及其他业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GoodsRepository(db)

    # -------------------- 业务校验 --------------------

    async def _ensure_category_exists(self, category_id: Optional[int]) -> None:
        """业务校验：分类必须存在且未被软删除"""
        if category_id is None:
            return
        exists = await self.db.scalar(
            select(Category.id).where(
                Category.id == category_id,
                Category.is_deleted == False,  # noqa: E712
            )
        )
        if not exists:
            raise NotFoundException("商品分类不存在")

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, data: GoodsCreate) -> GoodsResponse:
        """创建商品（校验分类存在）"""
        await self._ensure_category_exists(data.category_id)
        obj = await self.repo.create(data)
        return GoodsResponse.model_validate(obj)

    async def get_detail(self, id: int) -> GoodsResponse:
        """详情（单条，已软删除视为不存在）"""
        obj = await self.repo.get(id)
        return GoodsResponse.model_validate(obj)

    async def update(self, id: int, data: GoodsUpdate) -> GoodsResponse:
        """更新（不含上下架状态；状态请用 update_status）"""
        await self._ensure_category_exists(data.category_id)
        obj = await self.repo.update(id, data)
        return GoodsResponse.model_validate(obj)

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
        - 排除已软删除（is_deleted=True）的商品
        - 支持按分类（category_id）、秒杀（flash）、热销（hot）、上下架（status）过滤
        - 支持商品名称 / 商品编号关键字检索
        - 排序：sort 升序，其次 id 升序
        """
        filters = filters or {}
        conditions = [Goods.is_deleted == False]  # noqa: E712

        for field in ("category_id", "flash", "hot", "status"):
            value = filters.get(field)
            if value is not None:
                conditions.append(getattr(Goods, field) == value)

        keyword = filters.get("keyword")
        if keyword:
            like_value = f"%{keyword.strip()}%"
            conditions.append(or_(Goods.name.like(like_value), Goods.goods_no.like(like_value)))

        stmt = select(Goods).order_by(Goods.sort.asc(), Goods.id.asc())
        count_stmt = select(func.count()).select_from(Goods)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [GoodsResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # -------------------- 业务逻辑：状态/标识位（上下架）--------------------

    async def update_status(self, id: int, data: GoodsStatusUpdate) -> GoodsResponse:
        """
        修改上下架状态（status：1上架 0下架）

        业务入口在 Service；持久化走 Repository.update（传入字段字典）。
        """
        obj = await self.repo.update(
            id,
            data.model_dump(exclude_unset=True),
        )
        return GoodsResponse.model_validate(obj)

    # ---------- 在下方添加商业逻辑方法 ----------
