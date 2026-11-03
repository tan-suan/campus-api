"""
商品规格表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- status 为状态/标识位字段，从通用 Update 中排除，改由 StatusUpdate + PATCH 接口维护。
- goods_id 关联 goods 表，商品是否存在的业务校验在 Service 完成。
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoodsSpecBase(BaseModel):
    """
    商品规格表基础模型（不含主键与数据库托管字段）
    """

    goods_id: int = Field(..., description="所属商品ID")
    spec_name: str = Field(..., max_length=50, description="规格名称，如 微辣 / 少冰 / 1.5m")
    price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2, description="规格售价")
    origin_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="规格原价",
    )
    stock: int = Field(default=0, ge=0, description="规格库存")
    sort: int = Field(default=0, description="排序值，越小越靠前")
    status: int = Field(default=1, ge=0, le=1, description="状态：1启用 0停用")


class GoodsSpecCreate(GoodsSpecBase):
    """
    商品规格表创建模型
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goods_id": 1,
                "spec_name": "微辣",
                "price": "12.90",
                "origin_price": "19.90",
                "stock": 30,
                "sort": 1,
                "status": 1,
            }
        }
    )


class GoodsSpecUpdate(BaseModel):
    """
    商品规格表更新模型

    注意：状态/标识位字段（status）不在此模型中，请使用专用改状态接口。
    """

    goods_id: int | None = Field(default=None, description="所属商品ID")
    spec_name: str | None = Field(default=None, max_length=50, description="规格名称，如 微辣 / 少冰 / 1.5m")
    price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="规格售价",
    )
    origin_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="规格原价",
    )
    stock: int | None = Field(default=None, ge=0, description="规格库存")
    sort: int | None = Field(default=None, description="排序值，越小越靠前")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "spec_name": "中辣",
                "price": "13.90",
                "stock": 20,
                "sort": 2,
            }
        },
    )


class GoodsSpecStatusUpdate(BaseModel):
    """
    商品规格表状态/标识位更新模型（专用）
    """

    status: int = Field(..., ge=0, le=1, description="状态：1启用 0停用")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": 0}},
    )


class GoodsSpecResponse(BaseModel):
    """
    商品规格表响应模型
    """

    id: int = Field(..., description="规格ID")
    goods_id: int = Field(..., description="所属商品ID")
    spec_name: str = Field(..., max_length=50, description="规格名称，如 微辣 / 少冰 / 1.5m")
    price: Decimal = Field(..., description="规格售价")
    origin_price: Decimal = Field(..., description="规格原价")
    stock: int = Field(..., description="规格库存")
    sort: int = Field(..., description="排序值，越小越靠前")
    status: int = Field(..., description="状态：1启用 0停用")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "goods_id": 1,
                "spec_name": "微辣",
                "price": "12.90",
                "origin_price": "19.90",
                "stock": 30,
                "sort": 1,
                "status": 1,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
