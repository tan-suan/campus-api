"""
购物车表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（create_time / update_time）不进入创建模型。
- user_id 不在请求模型中：由登录态（JWT）注入，避免越权操作他人购物车。
- spec_name 为服务端写入的规格快照（由 Service 按 goods_spec_id 查得），不接受前端传入。
- selected 为勾选标识位，从通用 Update 中排除，改由 SelectedUpdate + PATCH 接口维护。
- qty（购买数量）通过 PUT /cart/{id} 修改；加购请用 POST /cart（同规格自动累加）。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CartBase(BaseModel):
    """
    购物车表基础模型（不含主键、user_id、规格快照与数据库托管字段）
    """

    goods_id: int = Field(..., description="商品ID")
    goods_spec_id: int | None = Field(default=None, description="规格ID，空表示默认规格")
    qty: int = Field(default=1, ge=1, le=999, description="购买数量")


class CartCreate(CartBase):
    """
    购物车表创建模型（加购：同一用户 + 同一商品 + 同一规格重复加购时累加数量）
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "goods_id": 1,
                "goods_spec_id": 2,
                "qty": 1,
            }
        },
    )


class CartUpdate(BaseModel):
    """
    购物车表更新模型（修改购买数量）

    注意：
    - 勾选标识位（selected）不在此模型中，请使用专用 PATCH /cart/{id}/selected 接口。
    - 商品与规格不可修改（会破坏唯一性），如需更换请删除后重新加购。
    """

    qty: int = Field(..., ge=1, le=999, description="购买数量")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"qty": 3}},
    )


class CartSelectedUpdate(BaseModel):
    """
    购物车表勾选标识位更新模型（专用，用于勾选/取消勾选结算）
    """

    selected: bool = Field(..., description="是否勾选结算：0否 1是")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"selected": False}},
    )


class CartResponse(BaseModel):
    """
    购物车表响应模型
    """

    id: int = Field(..., description="购物车条目ID")
    user_id: int = Field(..., description="所属用户ID")
    goods_id: int = Field(..., description="商品ID")
    goods_spec_id: int | None = Field(..., description="规格ID，空表示默认规格")
    spec_name: str = Field(..., max_length=50, description="规格名称快照")
    qty: int = Field(..., description="购买数量")
    selected: bool = Field(..., description="是否勾选结算：0否 1是")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "goods_id": 1,
                "goods_spec_id": 2,
                "spec_name": "微辣",
                "qty": 2,
                "selected": True,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
