"""
自提点表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 列表分页、过滤、状态变更、跨表流程等均视为业务逻辑，写在本层。
- 表含状态/标识位字段（status）时，额外提供 update_status（禁止走通用 Update Schema）。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.pickup_point import PickupPoint
from repository.pickup_point_repository import PickupPointRepository
from schemas.pickup_point import (
    PickupPointCreate,
    PickupPointResponse,
    PickupPointStatusUpdate,
    PickupPointUpdate,
)


class PickupPointService:
    """
    自提点表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表及其他业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PickupPointRepository(db)

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, data: PickupPointCreate) -> PickupPointResponse:
        """创建自提点"""
        obj = await self.repo.create(data)
        return PickupPointResponse.model_validate(obj)

    async def get_detail(self, id: int) -> PickupPointResponse:
        """详情（单条）"""
        obj = await self.repo.get(id)
        return PickupPointResponse.model_validate(obj)

    async def update(self, id: int, data: PickupPointUpdate) -> PickupPointResponse:
        """更新（不含状态/标识位字段；状态请用 update_status）"""
        obj = await self.repo.update(id, data)
        return PickupPointResponse.model_validate(obj)

    async def delete(self, id: int) -> None:
        """删除（软删除）"""
        await self.repo.delete(id)

    # -------------------- 业务逻辑：列表 --------------------

    async def get_list(
        self,
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """分页列表（业务逻辑：分页 / 过滤 / 排除软删除 / 按 sort 升序）"""
        conditions = [PickupPoint.is_deleted == False]  # noqa: E712
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(PickupPoint, field):
                    conditions.append(getattr(PickupPoint, field) == value)

        stmt = select(PickupPoint).order_by(PickupPoint.sort.asc(), PickupPoint.id.asc())
        count_stmt = select(func.count()).select_from(PickupPoint)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [PickupPointResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # -------------------- 业务逻辑：状态/标识位 --------------------

    async def update_status(self, id: int, data: PickupPointStatusUpdate) -> PickupPointResponse:
        """
        修改状态（status：1启用 0停用）

        业务入口在 Service；持久化走 Repository.update（传入字段字典）。
        """
        obj = await self.repo.update(
            id,
            data.model_dump(exclude_unset=True),
        )
        return PickupPointResponse.model_validate(obj)

    # ---------- 在下方添加商业逻辑方法 ----------
