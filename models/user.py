"""
用户表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from models.base import BaseModel


class User(BaseModel):
    """
    用户表：校园闪购小程序用户（微信登录 + 校园卡余额）
    """

    __tablename__ = "user"

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="用户ID",
    )
    openid = Column(String(64), nullable=False, unique=True, comment="微信 openid")
    nickname = Column(String(50), nullable=False, default="", comment="昵称")
    avatar = Column(String(255), nullable=False, default="", comment="头像地址")
    phone = Column(String(20), nullable=False, default="", comment="手机号")
    gender = Column(Integer, nullable=False, default=0, comment="性别：0未知 1男 2女")
    campus = Column(String(50), nullable=False, default="", comment="所在校区")
    balance = Column(Numeric(10, 2), nullable=False, default=0, comment="校园卡余额")
    status = Column(Integer, nullable=False, default=1, comment="状态：1正常 0禁用")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    @property
    def masked_phone(self) -> str:
        """
        脱敏后的手机号
        """
        if self.phone and len(self.phone) >= 11:
            return f"{self.phone[:3]}****{self.phone[-4:]}"
        return "****"
