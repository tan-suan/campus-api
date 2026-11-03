"""Models 包

导出 ORM 基类；具体业务表模型由脚手架按 DDL 生成后在此追加 import。
"""

from .base import BaseModel, TimestampMixin, SoftDeleteMixin

# 与 core.database.Base 同源，便于 metadata.create_all / 测试建表
from core.database import Base

# ---- 脚手架追加区：按表生成的具体模型 ----
from .address import Address
from .cart import Cart
from .category import Category
from .coupon import Coupon
from .favorite import Favorite
from .goods import Goods
from .goods_spec import GoodsSpec
from .order import Order, OrderMode, OrderStatus
from .order_item import OrderItem
from .pickup_point import PickupPoint
from .user import User

__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "User",
    "Category",
    "PickupPoint",
    "Goods",
    "GoodsSpec",
    "Address",
    "Coupon",
    "Favorite",
    "Cart",
    "Order",
    "OrderItem",
    "OrderStatus",
    "OrderMode",
]
