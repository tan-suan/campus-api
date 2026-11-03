"""
收货地址表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 用户归属隔离（按登录用户过滤与鉴权）、默认地址唯一、状态变更、软删除等业务均在本层实现。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.address import Address
from repository.address_repository import AddressRepository
from schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressStatusUpdate,
    AddressUpdate,
)
from utils.custom_exceptions import NotFoundException


class AddressService:
    """
    收货地址表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表、用户隔离、默认地址等业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AddressRepository(db)

    # -------------------- 业务逻辑：用户隔离 --------------------

    async def _get_owned(self, id: int, user_id: int) -> Address:
        """
        取单条并校验归属：只能操作自己的地址

        越权访问统一按「不存在」处理，避免泄露其他用户的地址是否存在。
        """
        obj = await self.repo.get(id)
        if obj.user_id != user_id:
            raise NotFoundException("收货地址不存在")
        return obj

    async def _clear_other_defaults(self, user_id: int, exclude_id: int) -> None:
        """业务规则：同一用户仅保留一个默认地址（把其他地址的 is_default 置为否）"""
        await self.db.execute(
            update(Address)
            .where(
                Address.user_id == user_id,
                Address.id != exclude_id,
                Address.is_default == True,  # noqa: E712
                Address.is_deleted == False,  # noqa: E712
            )
            .values(is_default=False)
        )
        await self.db.commit()

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, user_id: int, data: AddressCreate) -> AddressResponse:
        """创建地址（归属当前登录用户；设为默认时自动取消其他默认地址）"""
        obj = await self.repo.create(data, user_id)
        if obj.is_default:
            await self._clear_other_defaults(user_id, obj.id)
        return AddressResponse.model_validate(obj)

    async def get_detail(self, id: int, user_id: int) -> AddressResponse:
        """详情（仅限本人地址）"""
        obj = await self._get_owned(id, user_id)
        return AddressResponse.model_validate(obj)

    async def update(self, id: int, user_id: int, data: AddressUpdate) -> AddressResponse:
        """更新（仅限本人地址；不含状态字段，状态请用 update_status）"""
        await self._get_owned(id, user_id)
        obj = await self.repo.update(id, data)
        if obj.is_default:
            await self._clear_other_defaults(user_id, obj.id)
        return AddressResponse.model_validate(obj)

    async def delete(self, id: int, user_id: int) -> None:
        """删除（仅限本人地址；软删除：仅置 is_deleted）"""
        await self._get_owned(id, user_id)
        await self.repo.delete(id)

    # -------------------- 业务逻辑：列表 --------------------

    async def get_list(
        self,
        user_id: int,
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        分页列表（只返回当前登录用户的地址）

        业务逻辑（本层）：
        - 强制按 user_id 隔离，排除已软删除的记录
        - 支持按状态（status）过滤
        - 排序：默认地址优先，其次创建时间倒序
        """
        filters = filters or {}
        conditions = [
            Address.user_id == user_id,
            Address.is_deleted == False,  # noqa: E712
        ]

        status = filters.get("status")
        if status is not None:
            conditions.append(Address.status == status)

        stmt = select(Address).order_by(Address.is_default.desc(), Address.id.desc())
        count_stmt = select(func.count()).select_from(Address)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [AddressResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # -------------------- 业务逻辑：状态/标识位 --------------------

    async def update_status(
        self, id: int, user_id: int, data: AddressStatusUpdate
    ) -> AddressResponse:
        """
        修改状态（status：1有效 0停用），仅限本人地址

        业务入口在 Service；持久化走 Repository.update（传入字段字典）。
        """
        await self._get_owned(id, user_id)
        obj = await self.repo.update(id, data.model_dump(exclude_unset=True))
        return AddressResponse.model_validate(obj)

    # ---------- 在下方添加商业逻辑方法 ----------
