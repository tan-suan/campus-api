"""
商品表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from models.base import BaseModel


class Goods(BaseModel):
    """
    商品表：闪购商品（含秒杀、热销标识与软删除）
    """

    __tablename__ = "goods"

    id = Column(
        # MySQL 为 BIGINT AUTO_INCREMENT；sqlite（单元测试）需 INTEGER 才能自增
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="商品ID",
    )
    goods_no = Column(String(32), nullable=False, unique=True, comment="商品编号")
    name = Column(String(200), nullable=False, comment="商品名称")
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False, comment="分类ID")
    price = Column(Numeric(10, 2), nullable=False, comment="闪购价")
    origin_price = Column(Numeric(10, 2), nullable=False, default=0, comment="原价")
    stock = Column(Integer, nullable=False, default=0, comment="剩余库存")
    total_stock = Column(Integer, nullable=False, default=0, comment="总库存（用于展示抢购进度）")
    sold = Column(Integer, nullable=False, default=0, comment="已售数量")
    emoji = Column(String(16), nullable=False, default="", comment="商品图标（原型占位图）")
    tint = Column(String(16), nullable=False, default="", comment="图标底色")
    main_image = Column(String(255), nullable=False, default="", comment="商品主图地址")
    tag = Column(String(50), nullable=False, default="", comment="角标文案，如 秒杀价")
    summary = Column(String(255), nullable=False, default="", comment="一句话描述")
    detail = Column(Text, nullable=True, comment="商品详情")
    flash = Column(Boolean, nullable=False, default=False, comment="是否秒杀：0否 1是")
    hot = Column(Boolean, nullable=False, default=False, comment="是否热销：0否 1是")
    sort = Column(Integer, nullable=False, default=0, comment="排序值，越小越靠前")
    status = Column(Integer, nullable=False, default=1, comment="状态：1上架 0下架")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
