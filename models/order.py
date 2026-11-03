"""
订单表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成

注意：表名 `order` 是 MySQL / SQLite 保留字，SQLAlchemy 会自动加反引号，
手写原生 SQL 时必须使用 `order`（反引号）。
"""

import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from models.base import BaseModel


class OrderStatus(str, enum.Enum):
    """订单状态枚举（数据库存储英文值）"""

    PENDING = "pending"  # 待付款
    PICKING = "picking"  # 待取货
    DONE = "done"  # 已完成
    CANCELED = "canceled"  # 已取消


class OrderMode(str, enum.Enum):
    """取货方式枚举"""

    PICKUP = "pickup"  # 校内自提
    DORM = "dorm"  # 送到寝室


class Order(BaseModel):
    """
    订单表：状态流转 pending → picking → done / canceled，取货方式 pickup / dorm
    """

    __tablename__ = "order"

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="订单ID",
    )
    order_no = Column(String(32), nullable=False, unique=True, comment="订单号，如 CF20260926100821")
    user_id = Column(
        BigInteger,
        ForeignKey("user.id"),
        nullable=False,
        index=True,
        comment="下单用户ID",
    )
    status = Column(
        Enum(
            OrderStatus,
            name="order_status",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
        comment="订单状态：pending待付款 picking待取货 done已完成 canceled已取消",
    )
    mode = Column(
        Enum(
            OrderMode,
            name="order_mode",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=OrderMode.PICKUP,
        server_default=OrderMode.PICKUP.value,
        comment="取货方式：pickup校内自提 dorm送到寝室",
    )
    pickup_point_id = Column(
        Integer,
        ForeignKey("pickup_point.id"),
        nullable=True,
        comment="自提点ID（自提时）",
    )
    pickup_point_name = Column(String(100), nullable=False, default="", comment="自提点名称快照")
    address_id = Column(
        BigInteger,
        ForeignKey("address.id"),
        nullable=True,
        comment="收货地址ID（送寝时）",
    )
    address_text = Column(String(255), nullable=False, default="", comment="收货地址快照")
    pickup_code = Column(String(16), nullable=False, default="", comment="取货码，如 A-1088")
    expect_time = Column(String(50), nullable=False, default="尽快送达", comment="期望时间文案")
    goods_total = Column(Numeric(10, 2), nullable=False, default=0, comment="商品金额")
    freight = Column(Numeric(10, 2), nullable=False, default=0, comment="配送费")
    discount = Column(Numeric(10, 2), nullable=False, default=0, comment="优惠减免")
    pay_amount = Column(Numeric(10, 2), nullable=False, default=0, comment="实付金额")
    coupon_id = Column(
        BigInteger,
        ForeignKey("coupon.id"),
        nullable=True,
        comment="使用的优惠券ID",
    )
    pay_method = Column(String(20), nullable=False, default="微信支付", comment="支付方式")
    remark = Column(String(255), nullable=False, default="", comment="订单备注")
    goods_count = Column(Integer, nullable=False, default=0, comment="商品总件数")
    pay_time = Column(DateTime, nullable=True, comment="支付时间")
    done_time = Column(DateTime, nullable=True, comment="完成时间")
    cancel_time = Column(DateTime, nullable=True, comment="取消时间")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
