"""API v1 路由包

脚手架生成表模块后，在此追加：
    from api.v1.xxx import router as xxx_router
    v1_router.include_router(xxx_router)

注：资源目录与 HTTP 前缀均为单数（表名原样 / 下划线转连字符）。
"""

from fastapi import APIRouter

from api.v1.address import router as address_router
from api.v1.cart import router as cart_router
from api.v1.category import router as category_router
from api.v1.coupon import router as coupon_router
from api.v1.favorite import router as favorite_router
from api.v1.goods import router as goods_router
from api.v1.goods_spec import router as goods_spec_router
from api.v1.order import router as order_router
from api.v1.order_item import router as order_item_router
from api.v1.pickup_point import router as pickup_point_router
from api.v1.user import router as user_router

v1_router = APIRouter()

# ---- 脚手架追加区 ----
v1_router.include_router(user_router)
v1_router.include_router(category_router)
v1_router.include_router(pickup_point_router)
v1_router.include_router(goods_router)
v1_router.include_router(goods_spec_router)
v1_router.include_router(address_router)
v1_router.include_router(coupon_router)
v1_router.include_router(favorite_router)
v1_router.include_router(cart_router)
v1_router.include_router(order_router)
v1_router.include_router(order_item_router)

__all__ = ["v1_router"]
