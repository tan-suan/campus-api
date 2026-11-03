"""
订单表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id、订单号 order_no、金额字段（goods_total / freight / discount / pay_amount）、
  取货码 pickup_code、各类快照（pickup_point_name / address_text）、时间戳
  全部由 **Service 计算或生成**，不接受前端传入（extra="forbid" 会拒绝多余字段）。
- user_id 由登录态（JWT）注入，不在请求模型中。
- status 为状态字段：从通用 Update 中排除，改由 OrderStatusUpdate + PATCH /{id}/status，
  并按状态机校验（pending → picking → done / canceled）。
- mode（取货方式）是业务枚举，不是状态字段，保留在 Create 中，下单后不可修改。
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from models.order import OrderMode, OrderStatus
from schemas.order_item import OrderItemResponse


class OrderItemInput(BaseModel):
    """
    下单明细入参：只指定商品、规格与数量，单价与快照由服务端读取
    """

    goods_id: int = Field(..., description="商品ID")
    goods_spec_id: int | None = Field(default=None, description="规格ID，空表示默认规格")
    qty: int = Field(default=1, ge=1, le=999, description="购买数量")

    model_config = ConfigDict(extra="forbid")


class OrderCreate(BaseModel):
    """
    订单表创建模型（下单）

    金额、取货码、订单号、快照均由 Service 生成：
    - goods_total = Σ 明细小计
    - freight = 自提 0 / 送寝固定配送费
    - discount = 优惠券可抵扣额（不超过商品金额）
    - pay_amount = goods_total + freight - discount
    """

    mode: OrderMode = Field(default=OrderMode.PICKUP, description="取货方式：pickup校内自提 dorm送到寝室")
    pickup_point_id: int | None = Field(default=None, description="自提点ID（自提必填）")
    address_id: int | None = Field(default=None, description="收货地址ID（送寝必填）")
    coupon_id: int | None = Field(default=None, description="使用的优惠券ID")
    expect_time: str = Field(default="尽快送达", max_length=50, description="期望时间文案")
    pay_method: str = Field(default="微信支付", max_length=20, description="支付方式")
    remark: str = Field(default="", max_length=255, description="订单备注")
    items: list[OrderItemInput] = Field(..., min_length=1, description="下单商品明细")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "mode": "pickup",
                "pickup_point_id": 1,
                "coupon_id": None,
                "expect_time": "尽快送达",
                "pay_method": "微信支付",
                "remark": "少冰",
                "items": [{"goods_id": 1, "goods_spec_id": 2, "qty": 2}],
            }
        },
    )


class OrderUpdate(BaseModel):
    """
    订单表更新模型

    说明：商品明细、取货方式、金额与快照在下单时确定，不支持通过 PUT 修改；
    如需变更请取消订单后重新下单。状态字段请使用 PATCH /{id}/status。
    """

    expect_time: str | None = Field(default=None, max_length=50, description="期望时间文案")
    pay_method: str | None = Field(default=None, max_length=20, description="支付方式")
    remark: str | None = Field(default=None, max_length=255, description="订单备注")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"expect_time": "12:00 前送达", "remark": "放宿舍门口"}},
    )


class OrderStatusUpdate(BaseModel):
    """
    订单表状态更新模型（专用）

    合法流转：pending → picking / canceled；picking → done / canceled；
    done、canceled 为终态，不可再变更。
    """

    status: OrderStatus = Field(..., description="订单状态：pending/picking/done/canceled")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "picking"}},
    )


class OrderResponse(BaseModel):
    """
    订单表响应模型（列表用，不含明细）
    """

    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., max_length=32, description="订单号")
    user_id: int = Field(..., description="下单用户ID")
    status: OrderStatus = Field(..., description="订单状态")
    mode: OrderMode = Field(..., description="取货方式")
    pickup_point_id: int | None = Field(..., description="自提点ID")
    pickup_point_name: str = Field(..., max_length=100, description="自提点名称快照")
    address_id: int | None = Field(..., description="收货地址ID")
    address_text: str = Field(..., max_length=255, description="收货地址快照")
    pickup_code: str = Field(..., max_length=16, description="取货码")
    expect_time: str = Field(..., max_length=50, description="期望时间文案")
    goods_total: Decimal = Field(..., description="商品金额")
    freight: Decimal = Field(..., description="配送费")
    discount: Decimal = Field(..., description="优惠减免")
    pay_amount: Decimal = Field(..., description="实付金额")
    coupon_id: int | None = Field(..., description="使用的优惠券ID")
    pay_method: str = Field(..., max_length=20, description="支付方式")
    remark: str = Field(..., max_length=255, description="订单备注")
    goods_count: int = Field(..., description="商品总件数")
    pay_time: datetime | None = Field(..., description="支付时间")
    done_time: datetime | None = Field(..., description="完成时间")
    cancel_time: datetime | None = Field(..., description="取消时间")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "order_no": "CF20260926100821",
                "user_id": 1,
                "status": "pending",
                "mode": "pickup",
                "pickup_point_id": 1,
                "pickup_point_name": "菜鸟驿站（梅园店）",
                "address_id": None,
                "address_text": "",
                "pickup_code": "A-1088",
                "expect_time": "尽快送达",
                "goods_total": "31.00",
                "freight": "0.00",
                "discount": "3.00",
                "pay_amount": "28.00",
                "coupon_id": 1,
                "pay_method": "微信支付",
                "remark": "",
                "goods_count": 2,
                "pay_time": None,
                "done_time": None,
                "cancel_time": None,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )


class OrderDetailResponse(OrderResponse):
    """
    订单详情响应模型（含明细快照）
    """

    items: list[OrderItemResponse] = Field(default_factory=list, description="订单明细")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "order_no": "CF20260926100821",
                "user_id": 1,
                "status": "pending",
                "mode": "pickup",
                "pickup_point_name": "菜鸟驿站（梅园店）",
                "pickup_code": "A-1088",
                "goods_total": "31.00",
                "freight": "0.00",
                "discount": "3.00",
                "pay_amount": "28.00",
                "goods_count": 2,
                "items": [
                    {
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
                ],
            }
        },
    )
