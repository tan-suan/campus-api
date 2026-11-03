"""
购物车表数据访问层（Repository）

【AUTO-GENERATED】由 sql-to-FastAPI-restfulapi-scaffold 生成，可被 skill 覆盖。
禁止在此文件编写业务规则。
Resource/API 层不要直接依赖本 Repository。

职责边界（强制）：
- 本层只做「单表、单条记录」的基础 CRUD，方法名固定为（按增删改查顺序）：
  create / delete / update / get
- 用户归属隔离、加购累加、数量修改、勾选切换等业务逻辑一律写在 Service。
- 本表无 is_deleted 字段，删除即物理删除。
"""

from typing import Any, Dict, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cart import Cart
from schemas.cart import CartCreate, CartUpdate
from utils.custom_exceptions import NotFoundException


class CartRepository:
    """
    购物车表仓储：仅负责单表单条记录的 CRUD（方法顺序：增删改查）
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CartCreate, user_id: int, spec_name: str) -> Cart:
        """增：插入一条记录并提交（user_id 与规格快照由 Service 注入）"""
        # exclude_unset：未显式传入的字段交由数据库/模型默认值处理，
        # 避免把 selected / create_time / update_time 等默认列写成 NULL。
        obj = Cart(
            user_id=user_id,
            spec_name=spec_name,
            **data.model_dump(exclude_unset=True),
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: int) -> None:
        """删：本表无软删字段，直接物理删除"""
        obj = await self.get(id)
        await self.db.delete(obj)
        await self.db.commit()

    async def update(self, id: int, data: Union[CartUpdate, Dict[str, Any]]) -> Cart:
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

    async def get(self, id: int) -> Cart:
        """查：按主键获取一条记录"""
        obj = await self.db.scalar(select(Cart).where(Cart.id == id))
        if not obj:
            raise NotFoundException("购物车条目不存在")
        return obj
