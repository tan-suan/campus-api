"""
商品分类表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from models.base import BaseModel


class Category(BaseModel):
    """
    商品分类表：首页/分类页的商品分类（热销爆款、食堂套餐、奶茶饮品等）
    """

    __tablename__ = "category"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="分类ID",
    )
    code = Column(String(32), nullable=False, unique=True, comment="分类标识：hot/canteen/drink 等")
    name = Column(String(50), nullable=False, comment="分类名称")
    emoji = Column(String(16), nullable=False, default="", comment="分类图标")
    tint = Column(String(16), nullable=False, default="", comment="主题底色，如 #EAF3DE")
    sort = Column(Integer, nullable=False, default=0, comment="排序值，越小越靠前")
    status = Column(Integer, nullable=False, default=1, comment="状态：1显示 0隐藏")
    is_deleted = Column(Boolean, nullable=False, default=False, comment="是否删除：0未删除 1已删除")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
