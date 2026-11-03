"""
订单明细表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- 商品名称、规格名称、图标、成交单价等为**下单快照**，由 Service 从商品/规格表读取后写入，
  不接受前端传入（防止客户端伪造价格）。
- 小计 subtotal 由 Service 按「成交单价 × 数量」计算，不接受前端传入。
- 明细的商品与成交价在下单时冻结，通用 Update 仅允许修改数量。
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    """
    订单明细表创建模型（向已有订单追加明细）

    order_id 为所属订单；goods_id / goods_spec_id / qty 由前端指定，
    其余快照与金额字段由 Service 计算写入。
    """

    order_id: int = Field(..., description="所属订单ID")
    goods_id: int = Field(..., description="商品ID")
    goods_spec_id: int | None = Field(default=None, description="规格ID，空表示默认规格")
    qty: int = Field(default=1, ge=1, le=999, description="购买数量")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "order_id": 1,
                "goods_id": 1,
                "goods_spec_id": 2,
                "qty": 2,
            }
        },
    )


class OrderItemUpdate(BaseModel):
    """
    订单明细表更新模型（仅允许修改数量）

    说明：快照（商品名/规格名/成交价）为下单时冻结值，不随商品改价变化；
    Service 会依据新数量重算 subtotal，并同步刷新所属订单的金额与件数。
    """

    qty: int = Field(..., ge=1, le=999, description="购买数量")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"qty": 3}},
    )


class OrderItemResponse(BaseModel):
    """
    订单明细表响应模型
    """

    id: int = Field(..., description="明细ID")
    order_id: int = Field(..., description="所属订单ID")
    goods_id: int = Field(..., description="商品ID")
    goods_spec_id: int | None = Field(..., description="规格ID")
    goods_name: str = Field(..., max_length=200, description="商品名称快照")
    spec_name: str = Field(..., max_length=50, description="规格名称快照")
    emoji: str = Field(..., max_length=16, description="商品图标快照")
    tint: str = Field(..., max_length=16, description="图标底色快照")
    price: Decimal = Field(..., description="成交单价")
    origin_price: Decimal = Field(..., description="原价")
    qty: int = Field(..., description="购买数量")
    subtotal: Decimal = Field(..., description="小计金额")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "order_id": 1,
                "goods_id": 1,
                "goods_spec_id": 2,
                "goods_name": "冰美式",
                "spec_name": "大杯",
                "emoji": "☕",
                "tint": "#F3E9DC",
                "price": "15.50",
                "origin_price": "19.90",
                "qty": 2,
                "subtotal": "31.00",
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
