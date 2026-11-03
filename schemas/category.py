"""
商品分类表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- status 为状态/标识位字段，从通用 Update 中排除，改由 StatusUpdate + PATCH 接口维护。
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """
    商品分类表基础模型（不含主键与数据库托管字段）
    """

    code: str = Field(..., max_length=32, description="分类标识：hot/canteen/drink 等")
    name: str = Field(..., max_length=50, description="分类名称")
    emoji: str = Field(default="", max_length=16, description="分类图标")
    tint: str = Field(default="", max_length=16, description="主题底色，如 #EAF3DE")
    sort: int = Field(default=0, description="排序值，越小越靠前")
    status: int = Field(default=1, ge=0, le=1, description="状态：1显示 0隐藏")


class CategoryCreate(CategoryBase):
    """
    商品分类表创建模型
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "hot",
                "name": "热销爆款",
                "emoji": "🔥",
                "tint": "#EAF3DE",
                "sort": 1,
                "status": 1,
            }
        }
    )


class CategoryUpdate(BaseModel):
    """
    商品分类表更新模型

    注意：状态/标识位字段（status）不在此模型中，请使用专用改状态接口。
    """

    code: str | None = Field(default=None, max_length=32, description="分类标识：hot/canteen/drink 等")
    name: str | None = Field(default=None, max_length=50, description="分类名称")
    emoji: str | None = Field(default=None, max_length=16, description="分类图标")
    tint: str | None = Field(default=None, max_length=16, description="主题底色，如 #EAF3DE")
    sort: int | None = Field(default=None, description="排序值，越小越靠前")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "热销爆款",
                "emoji": "🔥",
                "tint": "#EAF3DE",
                "sort": 2,
            }
        },
    )


class CategoryStatusUpdate(BaseModel):
    """
    商品分类表状态/标识位更新模型（专用）
    """

    status: int = Field(..., ge=0, le=1, description="状态：1显示 0隐藏")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": 0}},
    )


class CategoryResponse(BaseModel):
    """
    商品分类表响应模型
    """

    id: int = Field(..., description="分类ID")
    code: str = Field(..., max_length=32, description="分类标识：hot/canteen/drink 等")
    name: str = Field(..., max_length=50, description="分类名称")
    emoji: str = Field(..., max_length=16, description="分类图标")
    tint: str = Field(..., max_length=16, description="主题底色，如 #EAF3DE")
    sort: int = Field(..., description="排序值，越小越靠前")
    status: int = Field(..., description="状态：1显示 0隐藏")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "code": "hot",
                "name": "热销爆款",
                "emoji": "🔥",
                "tint": "#EAF3DE",
                "sort": 1,
                "status": 1,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
