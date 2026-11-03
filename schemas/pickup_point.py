"""
自提点表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- status 为状态/标识位字段，从通用 Update 中排除，改由 StatusUpdate + PATCH 接口维护。
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 联系电话：支持手机号与座机（如 0571-88888888）
CONTACT_PHONE_PATTERN = re.compile(r"^[0-9+\-\s()]{6,20}$")


class PickupPointBase(BaseModel):
    """
    自提点表基础模型（不含主键与数据库托管字段）
    """

    name: str = Field(..., max_length=100, description="自提点名称")
    business_hours: str = Field(default="", max_length=50, description="营业时间，如 08:00 - 21:00")
    distance_desc: str = Field(default="", max_length=50, description="距离描述，如 步行 3 分钟")
    address: str = Field(default="", max_length=255, description="详细位置")
    contact_phone: str = Field(default="", max_length=20, description="联系电话")
    sort: int = Field(default=0, description="排序值，越小越靠前")
    status: int = Field(default=1, ge=0, le=1, description="状态：1启用 0停用")

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, v: str) -> str:
        """校验联系电话格式（允许为空；非空时仅允许数字、+、-、空格与括号）"""
        if v and not CONTACT_PHONE_PATTERN.match(v):
            raise ValueError("联系电话格式不正确")
        return v


class PickupPointCreate(PickupPointBase):
    """
    自提点表创建模型
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "菜鸟驿站（东区店）",
                "business_hours": "08:00 - 21:00",
                "distance_desc": "步行 3 分钟",
                "address": "东校区 3 号宿舍楼一层",
                "contact_phone": "0571-88888888",
                "sort": 1,
                "status": 1,
            }
        }
    )


class PickupPointUpdate(BaseModel):
    """
    自提点表更新模型

    注意：状态/标识位字段（status）不在此模型中，请使用专用改状态接口。
    """

    name: str | None = Field(default=None, max_length=100, description="自提点名称")
    business_hours: str | None = Field(default=None, max_length=50, description="营业时间，如 08:00 - 21:00")
    distance_desc: str | None = Field(default=None, max_length=50, description="距离描述，如 步行 3 分钟")
    address: str | None = Field(default=None, max_length=255, description="详细位置")
    contact_phone: str | None = Field(default=None, max_length=20, description="联系电话")
    sort: int | None = Field(default=None, description="排序值，越小越靠前")

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, v: str | None) -> str | None:
        """校验联系电话格式（允许为空；非空时仅允许数字、+、-、空格与括号）"""
        if v and not CONTACT_PHONE_PATTERN.match(v):
            raise ValueError("联系电话格式不正确")
        return v

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "菜鸟驿站（西区店）",
                "business_hours": "09:00 - 22:00",
                "distance_desc": "步行 5 分钟",
                "address": "西校区 1 号宿舍楼一层",
                "contact_phone": "0571-66666666",
                "sort": 2,
            }
        },
    )


class PickupPointStatusUpdate(BaseModel):
    """
    自提点表状态/标识位更新模型（专用）
    """

    status: int = Field(..., ge=0, le=1, description="状态：1启用 0停用")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": 0}},
    )


class PickupPointResponse(BaseModel):
    """
    自提点表响应模型
    """

    id: int = Field(..., description="自提点ID")
    name: str = Field(..., max_length=100, description="自提点名称")
    business_hours: str = Field(..., max_length=50, description="营业时间，如 08:00 - 21:00")
    distance_desc: str = Field(..., max_length=50, description="距离描述，如 步行 3 分钟")
    address: str = Field(..., max_length=255, description="详细位置")
    contact_phone: str = Field(..., max_length=20, description="联系电话")
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
                "name": "菜鸟驿站（东区店）",
                "business_hours": "08:00 - 21:00",
                "distance_desc": "步行 3 分钟",
                "address": "东校区 3 号宿舍楼一层",
                "contact_phone": "0571-88888888",
                "sort": 1,
                "status": 1,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
