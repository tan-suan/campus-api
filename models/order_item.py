"""
订单明细表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.sql import func

from models.base import BaseModel


class OrderItem(BaseModel):
    """
    订单明细表：下单时的商品快照（名称、规格、成交价不随商品改价变化）

    说明：按 DDL，goods_spec_id 仅建索引、未建外键，故此处保持普通字段；
    小计 subtotal 由 Service 按「成交单价 × 数量」计算后写入。
    """

    __tablename__ = "order_item"

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="明细ID",
    )
    order_id = Column(
        BigInteger,
        ForeignKey("order.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属订单ID",
    )
    goods_id = Column(
        BigInteger,
        ForeignKey("goods.id"),
        nullable=False,
        index=True,
        comment="商品ID",
    )
    goods_spec_id = Column(BigInteger, nullable=True, comment="规格ID")
    goods_name = Column(String(200), nullable=False, comment="商品名称快照")
    spec_name = Column(String(50), nullable=False, default="默认", comment="规格名称快照")
    emoji = Column(String(16), nullable=False, default="", comment="商品图标快照")
    tint = Column(String(16), nullable=False, default="", comment="图标底色快照")
    price = Column(Numeric(10, 2), nullable=False, comment="成交单价")
    origin_price = Column(Numeric(10, 2), nullable=False, default=0, comment="原价")
    qty = Column(Integer, nullable=False, default=1, comment="购买数量")
    subtotal = Column(Numeric(10, 2), nullable=False, default=0, comment="小计金额")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
