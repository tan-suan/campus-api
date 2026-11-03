"""
商品分类表数据访问层（Repository）

【AUTO-GENERATED】由 sql-to-fastapi-restfulapi-scaffold 生成，可被 skill 覆盖。
禁止在此文件编写业务规则。
Resource/API 层不要直接依赖本 Repository。

职责边界（强制）：
- 本层只做「单表、单条记录」的基础 CRUD，方法名固定为（按增删改查顺序）：
  create / delete / update / get
- 列表分页、过滤、状态变更、跨表流程等一律视为业务逻辑，写在 Service。
"""

from typing import Any, Dict, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate
from utils.custom_exceptions import NotFoundException


class CategoryRepository:
    """
    商品分类表仓储：仅负责单表单条记录的 CRUD（方法顺序：增删改查）
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CategoryCreate) -> Category:
        """增：插入一条记录并提交"""
        # exclude_unset：未显式传入的字段交由数据库/模型默认值处理，
        # 避免把 is_deleted / create_time / update_time 等默认列写成 NULL。
        obj = Category(**data.model_dump(exclude_unset=True))
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: int) -> None:
        """删：有软删字段则软删，否则硬删"""
        obj = await self.get(id)
        setattr(obj, "is_deleted", True)
        await self.db.commit()

    async def update(self, id: int, data: Union[CategoryUpdate, Dict[str, Any]]) -> Category:
        """改：按主键更新一条记录（仅更新传入字段）"""
        if hasattr(data, "model_dump"):
            fields = data.model_dump(exclude_unset=True)
        else:
            fields = data
        obj = await self.get(id)
        for key, value in fields.items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get(self, id: int) -> Category:
        """查：按主键获取一条（软删除视为不存在）"""
        obj = await self.db.scalar(
            select(Category).where(
                Category.id == id,
                Category.is_deleted == False,  # noqa: E712
            )
        )
        if not obj:
            raise NotFoundException("商品分类不存在")
        return obj
