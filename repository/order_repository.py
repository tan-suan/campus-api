"""
订单表数据访问层（Repository）

【AUTO-GENERATED】由 sql-to-FastAPI-restfulapi-scaffold 生成，可被 skill 覆盖。
禁止在此文件编写业务规则。
Resource/API 层不要直接依赖本 Repository。

职责边界（强制）：
- 本层只做「单表、单条记录」的基础 CRUD，方法名固定为（按增删改查顺序）：
  create / delete / update / get
- 用户归属隔离、金额计算、取货码生成、状态机校验、明细联动等业务逻辑一律写在 Service。

注意：表名 order 为保留字，SQLAlchemy 会自动加反引号，无需手工转义。
"""

from typing import Any, Dict, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from schemas.order import OrderCreate, OrderUpdate
from utils.custom_exceptions import NotFoundException


class OrderRepository:
    """
    订单表仓储：仅负责单表单条记录的 CRUD（方法顺序：增删改查）
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Union[OrderCreate, Dict[str, Any]], user_id: int) -> Order:
        """增：插入一条记录并提交（user_id 由 Service 从登录态注入）"""
        if hasattr(data, "model_dump"):
            fields = data.model_dump(exclude_unset=True)
            # 嵌套明细分表存储，不属于 order 字段
            fields.pop("items", None)
        else:
            fields = dict(data)
        obj = Order(user_id=user_id, **fields)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: int) -> None:
        """删：有软删字段则软删，否则硬删"""
        obj = await self.get(id)
        setattr(obj, "is_deleted", True)
        await self.db.commit()

    async def update(self, id: int, data: Union[OrderUpdate, Dict[str, Any]]) -> Order:
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

    async def get(self, id: int) -> Order:
        """查：按主键获取一条（软删除视为不存在）"""
        obj = await self.db.scalar(
            select(Order).where(
                Order.id == id,
                Order.is_deleted == False,  # noqa: E712
            )
        )
        if not obj:
            raise NotFoundException("订单不存在")
        return obj
