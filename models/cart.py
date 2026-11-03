"""
购物车表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from models.base import BaseModel


class Cart(BaseModel):
    """
    购物车表：按「用户 + 商品 + 规格」唯一，同一规格重复加购只累加数量

    说明：
    - 本表按 DDL 无 status / is_deleted 字段，删除即为物理删除。
    - 联合唯一键为 (user_id, goods_id, goods_spec_id)；MySQL 唯一索引允许多个 NULL，
      因此 goods_spec_id 为空（默认规格）时的唯一性由 Service 显式校验保证。
    """

    __tablename__ = "cart"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "goods_id",
            "goods_spec_id",
            name="uk_cart_user_goods_spec",
        ),
    )

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="购物车条目ID",
    )
    user_id = Column(
        BigInteger,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户ID",
    )
    goods_id = Column(
        BigInteger,
        ForeignKey("goods.id"),
        nullable=False,
        index=True,
        comment="商品ID",
    )
    goods_spec_id = Column(
        BigInteger,
        ForeignKey("goods_spec.id"),
        nullable=True,
        index=True,
        comment="规格ID，空表示默认规格",
    )
    spec_name = Column(
        String(50),
        nullable=False,
        default="默认",
        comment="规格名称快照",
    )
    qty = Column(Integer, nullable=False, default=1, comment="购买数量")
    selected = Column(Boolean, nullable=False, default=True, comment="是否勾选结算：0否 1是")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
