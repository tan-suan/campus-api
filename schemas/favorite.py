"""
商品收藏表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（create_time / update_time）不进入创建模型。
- user_id 不在请求模型中：由登录态（JWT）注入，保证只操作自己的收藏。
- 唯一性（同一用户对同一商品仅一条）由 Service 校验 + 数据库联合唯一键双重保证。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FavoriteCreate(BaseModel):
    """
    商品收藏表创建模型（user_id 由登录态注入）
    """

    goods_id: int = Field(..., description="商品ID")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"goods_id": 1}},
    )


class FavoriteUpdate(BaseModel):
    """
    商品收藏表更新模型

    说明：收藏表无业务可改字段，仅支持更换收藏的商品（goods_id），
    更换后仍会做同一用户唯一性校验。
    """

    goods_id: int | None = Field(default=None, description="商品ID")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"goods_id": 2}},
    )


class FavoriteResponse(BaseModel):
    """
    商品收藏表响应模型
    """

    id: int = Field(..., description="收藏ID")
    user_id: int = Field(..., description="所属用户ID")
    goods_id: int = Field(..., description="商品ID")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "goods_id": 1,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
