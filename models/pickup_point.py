"""
自提点表数据模型

此文件由 SQL-to-FastAPI-Scaffold 自动生成
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from models.base import BaseModel


class PickupPoint(BaseModel):
    """
    自提点表：校内自提的取货地点（菜鸟驿站、自提柜、服务台等）
    """

    __tablename__ = "pickup_point"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="自提点ID",
    )
    name = Column(String(100), nullable=False, comment="自提点名称")
    business_hours = Column(String(50), nullable=False, default="", comment="营业时间，如 08:00 - 21:00")
    distance_desc = Column(String(50), nullable=False, default="", comment="距离描述，如 步行 3 分钟")
    address = Column(String(255), nullable=False, default="", comment="详细位置")
    contact_phone = Column(String(20), nullable=False, default="", comment="联系电话")
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

    @property
    def masked_contact_phone(self) -> str:
        """
        脱敏后的联系电话
        """
        if self.contact_phone and len(self.contact_phone) >= 7:
            return f"{self.contact_phone[:3]}****{self.contact_phone[-4:]}"
        return "****"
