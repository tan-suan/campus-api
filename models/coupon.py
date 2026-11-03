"""
优惠券表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String
from sqlalchemy.sql import func

from models.base import BaseModel


class Coupon(BaseModel):
    """
    优惠券表：满减券（满 20 减 3、满 35 减 6、满 60 减 12 等）
    """

    __tablename__ = "coupon"

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="优惠券ID",
    )
    code = Column(String(32), nullable=False, unique=True, comment="优惠券编码")
    name = Column(String(50), nullable=False, comment="券名称，如 满 20 减 3")
    threshold = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
        comment="使用门槛金额，0 表示无门槛",
    )
    amount = Column(Numeric(10, 2), nullable=False, default=0, comment="减免金额")
    scope = Column(String(50), nullable=False, default="全场通用", comment="适用范围")
    description = Column(String(255), nullable=False, default="", comment="使用说明")
    total = Column(Integer, nullable=False, default=0, comment="发行总量，0 表示不限量")
    received = Column(Integer, nullable=False, default=0, comment="已领取数量")
    start_time = Column(DateTime, nullable=True, comment="生效时间，空表示立即生效")
    end_time = Column(DateTime, nullable=True, comment="失效时间，空表示长期有效")
    status = Column(Integer, nullable=False, default=1, comment="状态：1可用 0停用")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
