"""服务依赖工厂（FastAPI 原生 Depends）

约定：
- Resource 统一注入 get_*_service
- Service 内部组合 Repository（不要在 Resource 注入 Repository）
- 本文件由脚手架在生成新表时追加 get_*_service /（可选）get_*_repository
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session

# ---- 脚手架追加区：import Service / Repository，并注册 get_*_service ----
from repository.address_repository import AddressRepository
from repository.cart_repository import CartRepository
from repository.category_repository import CategoryRepository
from repository.coupon_repository import CouponRepository
from repository.favorite_repository import FavoriteRepository
from repository.goods_repository import GoodsRepository
from repository.goods_spec_repository import GoodsSpecRepository
from repository.order_item_repository import OrderItemRepository
from repository.order_repository import OrderRepository
from repository.pickup_point_repository import PickupPointRepository
from repository.user_repository import UserRepository
from service.address_service import AddressService
from service.cart_service import CartService
from service.category_service import CategoryService
from service.coupon_service import CouponService
from service.favorite_service import FavoriteService
from service.goods_service import GoodsService
from service.goods_spec_service import GoodsSpecService
from service.order_item_service import OrderItemService
from service.order_service import OrderService
from service.pickup_point_service import PickupPointService
from service.user_service import UserService


def get_user_service(db: AsyncSession = Depends(get_async_session)) -> UserService:
    """用户表服务依赖"""
    return UserService(db)


def get_user_repository(db: AsyncSession = Depends(get_async_session)) -> UserRepository:
    """用户表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return UserRepository(db)


def get_category_service(db: AsyncSession = Depends(get_async_session)) -> CategoryService:
    """商品分类表服务依赖"""
    return CategoryService(db)


def get_category_repository(db: AsyncSession = Depends(get_async_session)) -> CategoryRepository:
    """商品分类表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return CategoryRepository(db)


def get_pickup_point_service(db: AsyncSession = Depends(get_async_session)) -> PickupPointService:
    """自提点表服务依赖"""
    return PickupPointService(db)


def get_pickup_point_repository(db: AsyncSession = Depends(get_async_session)) -> PickupPointRepository:
    """自提点表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return PickupPointRepository(db)


def get_goods_service(db: AsyncSession = Depends(get_async_session)) -> GoodsService:
    """商品表服务依赖"""
    return GoodsService(db)


def get_goods_repository(db: AsyncSession = Depends(get_async_session)) -> GoodsRepository:
    """商品表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return GoodsRepository(db)


def get_goods_spec_service(db: AsyncSession = Depends(get_async_session)) -> GoodsSpecService:
    """商品规格表服务依赖"""
    return GoodsSpecService(db)


def get_goods_spec_repository(db: AsyncSession = Depends(get_async_session)) -> GoodsSpecRepository:
    """商品规格表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return GoodsSpecRepository(db)


def get_address_service(db: AsyncSession = Depends(get_async_session)) -> AddressService:
    """收货地址表服务依赖"""
    return AddressService(db)


def get_address_repository(db: AsyncSession = Depends(get_async_session)) -> AddressRepository:
    """收货地址表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return AddressRepository(db)


def get_coupon_service(db: AsyncSession = Depends(get_async_session)) -> CouponService:
    """优惠券表服务依赖"""
    return CouponService(db)


def get_coupon_repository(db: AsyncSession = Depends(get_async_session)) -> CouponRepository:
    """优惠券表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return CouponRepository(db)


def get_favorite_service(db: AsyncSession = Depends(get_async_session)) -> FavoriteService:
    """商品收藏表服务依赖"""
    return FavoriteService(db)


def get_favorite_repository(db: AsyncSession = Depends(get_async_session)) -> FavoriteRepository:
    """商品收藏表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return FavoriteRepository(db)


def get_cart_service(db: AsyncSession = Depends(get_async_session)) -> CartService:
    """购物车表服务依赖"""
    return CartService(db)


def get_cart_repository(db: AsyncSession = Depends(get_async_session)) -> CartRepository:
    """购物车表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return CartRepository(db)


def get_order_service(db: AsyncSession = Depends(get_async_session)) -> OrderService:
    """订单表服务依赖"""
    return OrderService(db)


def get_order_repository(db: AsyncSession = Depends(get_async_session)) -> OrderRepository:
    """订单表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return OrderRepository(db)


def get_order_item_service(db: AsyncSession = Depends(get_async_session)) -> OrderItemService:
    """订单明细表服务依赖"""
    return OrderItemService(db)


def get_order_item_repository(
    db: AsyncSession = Depends(get_async_session),
) -> OrderItemRepository:
    """订单明细表仓储依赖（仅供 Service/测试使用，Resource 勿注入）"""
    return OrderItemRepository(db)
