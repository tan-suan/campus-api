"""
收货地址表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from models.base import BaseModel


class Address(BaseModel):
    """
    收货地址表：送给寝室时使用的宿舍地址，按用户隔离
    """

    __tablename__ = "address"

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="地址ID",
    )
    user_id = Column(
        BigInteger,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属用户ID",
    )
    receiver_name = Column(String(50), nullable=False, comment="收货人姓名")
    phone = Column(String(20), nullable=False, comment="收货人手机号")
    campus = Column(String(50), nullable=False, default="", comment="校区")
    building = Column(String(100), nullable=False, comment="楼栋，如 梅园 7 号楼")
    detail = Column(String(100), nullable=False, default="", comment="门牌，如 305 室")
    is_default = Column(Boolean, nullable=False, default=False, comment="是否默认地址：0否 1是")
    status = Column(Integer, nullable=False, default=1, comment="状态：1有效 0停用")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
