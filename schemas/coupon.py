"""
优惠券表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- status 为状态/标识位字段，从通用 Update 中排除，改由 StatusUpdate + PATCH 接口维护。
- code 全局唯一，唯一性校验在 Service 完成。
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CouponBase(BaseModel):
    """
    优惠券表基础模型（不含主键与数据库托管字段）
    """

    code: str = Field(..., max_length=32, description="优惠券编码")
    name: str = Field(..., max_length=50, description="券名称，如 满 20 减 3")
    threshold: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="使用门槛金额，0 表示无门槛",
    )
    amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="减免金额",
    )
    scope: str = Field(default="全场通用", max_length=50, description="适用范围")
    description: str = Field(default="", max_length=255, description="使用说明")
    total: int = Field(default=0, ge=0, description="发行总量，0 表示不限量")
    received: int = Field(default=0, ge=0, description="已领取数量")
    start_time: datetime | None = Field(default=None, description="生效时间，空表示立即生效")
    end_time: datetime | None = Field(default=None, description="失效时间，空表示长期有效")
    status: int = Field(default=1, ge=0, le=1, description="状态：1可用 0停用")


class CouponCreate(CouponBase):
    """
    优惠券表创建模型
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "FULL20MINUS3",
                "name": "满 20 减 3",
                "threshold": "20.00",
                "amount": "3.00",
                "scope": "全场通用",
                "description": "全场商品可用，不与其他优惠叠加",
                "total": 1000,
                "received": 0,
                "start_time": "2026-11-01T00:00:00",
                "end_time": "2026-12-31T23:59:59",
                "status": 1,
            }
        }
    )


class CouponUpdate(BaseModel):
    """
    优惠券表更新模型

    注意：状态/标识位字段（status）不在此模型中，请使用专用改状态接口。
    """

    code: str | None = Field(default=None, max_length=32, description="优惠券编码")
    name: str | None = Field(default=None, max_length=50, description="券名称，如 满 20 减 3")
    threshold: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="使用门槛金额，0 表示无门槛",
    )
    amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="减免金额",
    )
    scope: str | None = Field(default=None, max_length=50, description="适用范围")
    description: str | None = Field(default=None, max_length=255, description="使用说明")
    total: int | None = Field(default=None, ge=0, description="发行总量，0 表示不限量")
    received: int | None = Field(default=None, ge=0, description="已领取数量")
    start_time: datetime | None = Field(default=None, description="生效时间，空表示立即生效")
    end_time: datetime | None = Field(default=None, description="失效时间，空表示长期有效")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "满 30 减 5",
                "threshold": "30.00",
                "amount": "5.00",
                "description": "全场商品可用，不与其他优惠叠加",
            }
        },
    )


class CouponStatusUpdate(BaseModel):
    """
    优惠券表状态/标识位更新模型（专用）
    """

    status: int = Field(..., ge=0, le=1, description="状态：1可用 0停用")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": 0}},
    )


class CouponResponse(BaseModel):
    """
    优惠券表响应模型
    """

    id: int = Field(..., description="优惠券ID")
    code: str = Field(..., max_length=32, description="优惠券编码")
    name: str = Field(..., max_length=50, description="券名称，如 满 20 减 3")
    threshold: Decimal = Field(..., description="使用门槛金额，0 表示无门槛")
    amount: Decimal = Field(..., description="减免金额")
    scope: str = Field(..., max_length=50, description="适用范围")
    description: str = Field(..., max_length=255, description="使用说明")
    total: int = Field(..., description="发行总量，0 表示不限量")
    received: int = Field(..., description="已领取数量")
    start_time: datetime | None = Field(..., description="生效时间，空表示立即生效")
    end_time: datetime | None = Field(..., description="失效时间，空表示长期有效")
    status: int = Field(..., description="状态：1可用 0停用")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "code": "FULL20MINUS3",
                "name": "满 20 减 3",
                "threshold": "20.00",
                "amount": "3.00",
                "scope": "全场通用",
                "description": "全场商品可用，不与其他优惠叠加",
                "total": 1000,
                "received": 0,
                "start_time": "2026-11-01T00:00:00",
                "end_time": "2026-12-31T23:59:59",
                "status": 1,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
