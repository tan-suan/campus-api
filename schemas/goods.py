"""
商品表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- status 为状态/标识位（上下架）字段，从通用 Update 中排除，改由 StatusUpdate + PATCH 接口维护。
- flash（秒杀）/ hot（热销）为普通业务标识，可按常规字段在创建/更新时指定，业务规则在 Service。
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoodsBase(BaseModel):
    """
    商品表基础模型（不含主键与数据库托管字段）
    """

    goods_no: str = Field(..., max_length=32, description="商品编号")
    name: str = Field(..., max_length=200, description="商品名称")
    category_id: int = Field(..., description="分类ID")
    price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2, description="闪购价")
    origin_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="原价",
    )
    stock: int = Field(default=0, ge=0, description="剩余库存")
    total_stock: int = Field(default=0, ge=0, description="总库存（用于展示抢购进度）")
    sold: int = Field(default=0, ge=0, description="已售数量")
    emoji: str = Field(default="", max_length=16, description="商品图标（原型占位图）")
    tint: str = Field(default="", max_length=16, description="图标底色")
    main_image: str = Field(default="", max_length=255, description="商品主图地址")
    tag: str = Field(default="", max_length=50, description="角标文案，如 秒杀价")
    summary: str = Field(default="", max_length=255, description="一句话描述")
    detail: str | None = Field(default=None, description="商品详情")
    flash: bool = Field(default=False, description="是否秒杀：0否 1是")
    hot: bool = Field(default=False, description="是否热销：0否 1是")
    sort: int = Field(default=0, description="排序值，越小越靠前")
    status: int = Field(default=1, ge=0, le=1, description="状态：1上架 0下架")


class GoodsCreate(GoodsBase):
    """
    商品表创建模型
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goods_no": "SP20261103001",
                "name": "香辣鸡腿堡套餐",
                "category_id": 1,
                "price": "12.90",
                "origin_price": "19.90",
                "stock": 50,
                "total_stock": 100,
                "sold": 0,
                "emoji": "🍔",
                "tint": "#FFF1E6",
                "main_image": "https://example.com/goods/001.png",
                "tag": "秒杀价",
                "summary": "现做现炸，配薯条与可乐",
                "detail": "含香辣鸡腿堡 1 个、薯条 1 份、可乐 1 杯",
                "flash": True,
                "hot": True,
                "sort": 1,
                "status": 1,
            }
        }
    )


class GoodsUpdate(BaseModel):
    """
    商品表更新模型

    注意：上下架状态字段（status）不在此模型中，请使用专用改状态接口。
    """

    goods_no: str | None = Field(default=None, max_length=32, description="商品编号")
    name: str | None = Field(default=None, max_length=200, description="商品名称")
    category_id: int | None = Field(default=None, description="分类ID")
    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="闪购价",
    )
    origin_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="原价",
    )
    stock: int | None = Field(default=None, ge=0, description="剩余库存")
    total_stock: int | None = Field(default=None, ge=0, description="总库存（用于展示抢购进度）")
    sold: int | None = Field(default=None, ge=0, description="已售数量")
    emoji: str | None = Field(default=None, max_length=16, description="商品图标（原型占位图）")
    tint: str | None = Field(default=None, max_length=16, description="图标底色")
    main_image: str | None = Field(default=None, max_length=255, description="商品主图地址")
    tag: str | None = Field(default=None, max_length=50, description="角标文案，如 秒杀价")
    summary: str | None = Field(default=None, max_length=255, description="一句话描述")
    detail: str | None = Field(default=None, description="商品详情")
    flash: bool | None = Field(default=None, description="是否秒杀：0否 1是")
    hot: bool | None = Field(default=None, description="是否热销：0否 1是")
    sort: int | None = Field(default=None, description="排序值，越小越靠前")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "香辣鸡腿堡套餐（大份）",
                "price": "15.90",
                "stock": 40,
                "flash": False,
                "hot": True,
                "sort": 2,
            }
        },
    )


class GoodsStatusUpdate(BaseModel):
    """
    商品表状态/标识位更新模型（专用，用于上下架）
    """

    status: int = Field(..., ge=0, le=1, description="状态：1上架 0下架")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": 0}},
    )


class GoodsResponse(BaseModel):
    """
    商品表响应模型
    """

    id: int = Field(..., description="商品ID")
    goods_no: str = Field(..., max_length=32, description="商品编号")
    name: str = Field(..., max_length=200, description="商品名称")
    category_id: int = Field(..., description="分类ID")
    price: Decimal = Field(..., description="闪购价")
    origin_price: Decimal = Field(..., description="原价")
    stock: int = Field(..., description="剩余库存")
    total_stock: int = Field(..., description="总库存（用于展示抢购进度）")
    sold: int = Field(..., description="已售数量")
    emoji: str = Field(..., max_length=16, description="商品图标（原型占位图）")
    tint: str = Field(..., max_length=16, description="图标底色")
    main_image: str = Field(..., max_length=255, description="商品主图地址")
    tag: str = Field(..., max_length=50, description="角标文案，如 秒杀价")
    summary: str = Field(..., max_length=255, description="一句话描述")
    detail: str | None = Field(..., description="商品详情")
    flash: bool = Field(..., description="是否秒杀：0否 1是")
    hot: bool = Field(..., description="是否热销：0否 1是")
    sort: int = Field(..., description="排序值，越小越靠前")
    status: int = Field(..., description="状态：1上架 0下架")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "goods_no": "SP20261103001",
                "name": "香辣鸡腿堡套餐",
                "category_id": 1,
                "price": "12.90",
                "origin_price": "19.90",
                "stock": 50,
                "total_stock": 100,
                "sold": 0,
                "emoji": "🍔",
                "tint": "#FFF1E6",
                "main_image": "https://example.com/goods/001.png",
                "tag": "秒杀价",
                "summary": "现做现炸，配薯条与可乐",
                "detail": "含香辣鸡腿堡 1 个、薯条 1 份、可乐 1 杯",
                "flash": True,
                "hot": True,
                "sort": 1,
                "status": 1,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
