"""
商品收藏表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.sql import func

from models.base import BaseModel


class Favorite(BaseModel):
    """
    商品收藏表：用户收藏商品，同一用户对同一商品只能收藏一次（取消即物理删除）

    说明：本表按 DDL 无 status / is_deleted 字段，
    因此删除为物理删除，唯一性由联合唯一键 (user_id, goods_id) 兜底。
    """

    __tablename__ = "favorite"
    __table_args__ = (
        UniqueConstraint("user_id", "goods_id", name="uk_favorite_user_goods"),
    )

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="收藏ID",
    )
    user_id = Column(
        BigInteger,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户ID",
    )
    goods_id = Column(
        BigInteger,
        ForeignKey("goods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="商品ID",
    )
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
