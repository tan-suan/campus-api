"""
收货地址表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- user_id 不在创建/更新模型中：由登录态（JWT）注入，避免越权写入他人地址。
- status 为状态/标识位字段，从通用 Update 中排除，改由 StatusUpdate + PATCH 接口维护。
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressBase(BaseModel):
    """
    收货地址表基础模型（不含主键、user_id 与数据库托管字段）
    """

    receiver_name: str = Field(..., max_length=50, description="收货人姓名")
    phone: str = Field(..., max_length=20, description="收货人手机号")
    campus: str = Field(default="", max_length=50, description="校区")
    building: str = Field(..., max_length=100, description="楼栋，如 梅园 7 号楼")
    detail: str = Field(default="", max_length=100, description="门牌，如 305 室")
    is_default: bool = Field(default=False, description="是否默认地址：0否 1是")
    status: int = Field(default=1, ge=0, le=1, description="状态：1有效 0停用")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """校验收货人手机号格式（中国大陆手机号）"""
        if not re.match(r"^1[3-9]\d{9}$", v or ""):
            raise ValueError("手机号格式不正确")
        return v


class AddressCreate(AddressBase):
    """
    收货地址表创建模型（user_id 由登录态注入）
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "receiver_name": "小闪",
                "phone": "13800138000",
                "campus": "东校区",
                "building": "梅园 7 号楼",
                "detail": "305 室",
                "is_default": True,
                "status": 1,
            }
        }
    )


class AddressUpdate(BaseModel):
    """
    收货地址表更新模型

    注意：
    - 状态/标识位字段（status）不在此模型中，请使用专用改状态接口。
    - user_id 不允许修改，地址归属用户保持不变。
    """

    receiver_name: str | None = Field(default=None, max_length=50, description="收货人姓名")
    phone: str | None = Field(default=None, max_length=20, description="收货人手机号")
    campus: str | None = Field(default=None, max_length=50, description="校区")
    building: str | None = Field(default=None, max_length=100, description="楼栋，如 梅园 7 号楼")
    detail: str | None = Field(default=None, max_length=100, description="门牌，如 305 室")
    is_default: bool | None = Field(default=None, description="是否默认地址：0否 1是")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "building": "梅园 8 号楼",
                "detail": "512 室",
                "is_default": True,
            }
        },
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """校验收货人手机号格式（为空表示不修改）"""
        if v and not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class AddressStatusUpdate(BaseModel):
    """
    收货地址表状态/标识位更新模型（专用）
    """

    status: int = Field(..., ge=0, le=1, description="状态：1有效 0停用")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": 0}},
    )


class AddressResponse(BaseModel):
    """
    收货地址表响应模型
    """

    id: int = Field(..., description="地址ID")
    user_id: int = Field(..., description="所属用户ID")
    receiver_name: str = Field(..., max_length=50, description="收货人姓名")
    phone: str = Field(..., max_length=20, description="收货人手机号")
    campus: str = Field(..., max_length=50, description="校区")
    building: str = Field(..., max_length=100, description="楼栋，如 梅园 7 号楼")
    detail: str = Field(..., max_length=100, description="门牌，如 305 室")
    is_default: bool = Field(..., description="是否默认地址：0否 1是")
    status: int = Field(..., description="状态：1有效 0停用")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "receiver_name": "小闪",
                "phone": "13800138000",
                "campus": "东校区",
                "building": "梅园 7 号楼",
                "detail": "305 室",
                "is_default": True,
                "status": 1,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
