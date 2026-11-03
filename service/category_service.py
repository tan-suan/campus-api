"""
商品分类表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 列表分页、过滤、状态变更、跨表流程等均视为业务逻辑，写在本层。
- 表含状态/标识位字段（status）时，额外提供 update_status（禁止走通用 Update Schema）。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.category import Category
from repository.category_repository import CategoryRepository
from schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryStatusUpdate,
    CategoryUpdate,
)


class CategoryService:
    """
    商品分类表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表及其他业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CategoryRepository(db)

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, data: CategoryCreate) -> CategoryResponse:
        """创建商品分类"""
        obj = await self.repo.create(data)
        return CategoryResponse.model_validate(obj)

    async def get_detail(self, id: int) -> CategoryResponse:
        """详情（单条）"""
        obj = await self.repo.get(id)
        return CategoryResponse.model_validate(obj)

    async def update(self, id: int, data: CategoryUpdate) -> CategoryResponse:
        """更新（不含状态/标识位字段；状态请用 update_status）"""
        obj = await self.repo.update(id, data)
        return CategoryResponse.model_validate(obj)

    async def delete(self, id: int) -> None:
        """删除（软删除）"""
        await self.repo.delete(id)

    # -------------------- 业务逻辑：列表 --------------------

    async def get_list(
        self,
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """分页列表（业务逻辑：分页 / 过滤 / 排除软删除 / 按 sort 升序）"""
        conditions = [Category.is_deleted == False]  # noqa: E712
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(Category, field):
                    conditions.append(getattr(Category, field) == value)

        stmt = select(Category).order_by(Category.sort.asc(), Category.id.asc())
        count_stmt = select(func.count()).select_from(Category)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [CategoryResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # -------------------- 业务逻辑：状态/标识位 --------------------

    async def update_status(self, id: int, data: CategoryStatusUpdate) -> CategoryResponse:
        """
        修改状态（status：1显示 0隐藏）

        业务入口在 Service；持久化走 Repository.update（传入字段字典）。
        """
        obj = await self.repo.update(
            id,
            data.model_dump(exclude_unset=True),
        )
        return CategoryResponse.model_validate(obj)

    # ---------- 在下方添加商业逻辑方法 ----------
