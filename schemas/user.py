"""
用户表数据验证模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

约定：
- 主键 id 与数据库托管字段（is_deleted / create_time / update_time）不进入创建模型。
- status 为状态/标识位字段，从通用 Update 中排除，改由 StatusUpdate + PATCH 接口维护。
"""

import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    """
    用户表基础模型（不含主键与数据库托管字段）
    """

    openid: str = Field(..., max_length=64, description="微信 openid")
    nickname: str = Field(default="", max_length=50, description="昵称")
    avatar: str = Field(default="", max_length=255, description="头像地址")
    phone: str = Field(default="", max_length=20, description="手机号")
    gender: int = Field(default=0, ge=0, le=2, description="性别：0未知 1男 2女")
    campus: str = Field(default="", max_length=50, description="所在校区")
    balance: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="校园卡余额",
    )
    status: int = Field(default=1, ge=0, le=1, description="状态：1正常 0禁用")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """校验手机号格式（允许为空，非空时须为中国大陆手机号）"""
        if v and not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class UserCreate(UserBase):
    """
    用户表创建模型
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "openid": "wx_openid_9f8c7b6a",
                "nickname": "小闪",
                "avatar": "https://example.com/avatar.png",
                "phone": "13800138000",
                "gender": 1,
                "campus": "东校区",
                "balance": "0.00",
                "status": 1,
            }
        }
    )


class UserUpdate(BaseModel):
    """
    用户表更新模型

    注意：状态/标识位字段（status）不在此模型中，请使用专用改状态接口。
    """

    openid: str | None = Field(default=None, max_length=64, description="微信 openid")
    nickname: str | None = Field(default=None, max_length=50, description="昵称")
    avatar: str | None = Field(default=None, max_length=255, description="头像地址")
    phone: str | None = Field(default=None, max_length=20, description="手机号")
    gender: int | None = Field(default=None, ge=0, le=2, description="性别：0未知 1男 2女")
    campus: str | None = Field(default=None, max_length=50, description="所在校区")
    balance: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        description="校园卡余额",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """校验手机号格式（允许为空，非空时须为中国大陆手机号）"""
        if v and not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "nickname": "小闪",
                "avatar": "https://example.com/avatar.png",
                "phone": "13800138000",
                "gender": 1,
                "campus": "东校区",
                "balance": "20.00",
            }
        },
    )


class UserStatusUpdate(BaseModel):
    """
    用户表状态/标识位更新模型（专用）
    """

    status: int = Field(..., ge=0, le=1, description="状态：1正常 0禁用")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": 0}},
    )


class UserResponse(BaseModel):
    """
    用户表响应模型
    """

    id: int = Field(..., description="用户ID")
    openid: str = Field(..., max_length=64, description="微信 openid")
    nickname: str = Field(..., max_length=50, description="昵称")
    avatar: str = Field(..., max_length=255, description="头像地址")
    phone: str = Field(..., max_length=20, description="手机号")
    gender: int = Field(..., description="性别：0未知 1男 2女")
    campus: str = Field(..., max_length=50, description="所在校区")
    balance: Decimal = Field(..., description="校园卡余额")
    status: int = Field(..., description="状态：1正常 0禁用")
    is_deleted: bool = Field(..., description="是否删除：0未删除 1已删除")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "openid": "wx_openid_9f8c7b6a",
                "nickname": "小闪",
                "avatar": "https://example.com/avatar.png",
                "phone": "13800138000",
                "gender": 1,
                "campus": "东校区",
                "balance": "0.00",
                "status": 1,
                "is_deleted": False,
                "create_time": "2026-11-03T10:00:00",
                "update_time": "2026-11-03T10:00:00",
            }
        },
    )
