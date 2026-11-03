"""
商品规格表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.base import BaseModel


class GoodsSpec(BaseModel):
    """
    商品规格表：一个商品多种可选规格（辣度、冰量、尺寸、口味等）
    """

    __tablename__ = "goods_spec"

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="规格ID",
    )
    goods_id = Column(
        BigInteger,
        ForeignKey("goods.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属商品ID",
    )
    spec_name = Column(String(50), nullable=False, comment="规格名称，如 微辣 / 少冰 / 1.5m")
    price = Column(Numeric(10, 2), nullable=False, comment="规格售价")
    origin_price = Column(Numeric(10, 2), nullable=False, default=0, comment="规格原价")
    stock = Column(Integer, nullable=False, default=0, comment="规格库存")
    sort = Column(Integer, nullable=False, default=0, comment="排序值，越小越靠前")
    status = Column(Integer, nullable=False, default=1, comment="状态：1启用 0停用")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # 通过 goods_id 关联商品（单向引用，避免跨表双向依赖）
    # lazy="selectin"：异步会话下访问 spec.goods 不会触发 MissingGreenlet
    goods = relationship("Goods", foreign_keys=[goods_id], lazy="selectin")
