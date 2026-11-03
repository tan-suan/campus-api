"""
商品收藏表数据访问层（Repository）

【AUTO-GENERATED】由 sql-to-FastAPI-restfulapi-scaffold 生成，可被 skill 覆盖。
禁止在此文件编写业务规则。
Resource/API 层不要直接依赖本 Repository。

职责边界（强制）：
- 本层只做「单表、单条记录」的基础 CRUD，方法名固定为（按增删改查顺序）：
  create / delete / update / get
- 用户归属隔离、收藏唯一性、商品存在性等业务逻辑一律写在 Service。
- 本表无 is_deleted 字段，删除即物理删除。
"""

from typing import Any, Dict, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from schemas.favorite import FavoriteCreate, FavoriteUpdate
from utils.custom_exceptions import NotFoundException


class FavoriteRepository:
    """
    商品收藏表仓储：仅负责单表单条记录的 CRUD（方法顺序：增删改查）
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: FavoriteCreate, user_id: int) -> Favorite:
        """增：插入一条记录并提交（user_id 由 Service 从登录态注入）"""
        obj = Favorite(user_id=user_id, **data.model_dump(exclude_unset=True))
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: int) -> None:
        """删：本表无软删字段，直接物理删除"""
        obj = await self.get(id)
        await self.db.delete(obj)
        await self.db.commit()

    async def update(self, id: int, data: Union[FavoriteUpdate, Dict[str, Any]]) -> Favorite:
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

    async def get(self, id: int) -> Favorite:
        """查：按主键获取一条记录"""
        obj = await self.db.scalar(select(Favorite).where(Favorite.id == id))
        if not obj:
            raise NotFoundException("收藏记录不存在")
        return obj
