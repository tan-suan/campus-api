"""
商品收藏表业务服务（Service）

【HAND-WRITTEN】业务逻辑写在本文件；skill 仅在文件不存在时生成一次，之后不再覆盖。

约定：
- API/Resource 层统一只依赖本 Service，不直接调用 Repository。
- Repository 仅提供单条 CRUD：create / delete / update / get（增删改查顺序）。
- 用户归属隔离、同一用户对同一商品唯一、商品存在性、物理删除等业务均在本层实现。
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.goods import Goods
from repository.favorite_repository import FavoriteRepository
from schemas.favorite import (
    FavoriteCreate,
    FavoriteResponse,
    FavoriteUpdate,
)
from utils.custom_exceptions import ConflictException, NotFoundException


class FavoriteService:
    """
    商品收藏表业务服务

    - 单条 CRUD：委托 Repository.create / delete / update / get
    - 列表、用户隔离、收藏唯一性等业务：在本类实现
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FavoriteRepository(db)

    # -------------------- 业务校验 --------------------

    async def _get_owned(self, id: int, user_id: int) -> Favorite:
        """
        取单条并校验归属：只能操作自己的收藏

        越权访问统一按「不存在」处理，避免泄露其他用户的收藏记录。
        """
        obj = await self.repo.get(id)
        if obj.user_id != user_id:
            raise NotFoundException("收藏记录不存在")
        return obj

    async def _ensure_goods_exists(self, goods_id: int) -> None:
        """业务校验：收藏的商品必须存在且未被软删除"""
        exists = await self.db.scalar(
            select(Goods.id).where(
                Goods.id == goods_id,
                Goods.is_deleted == False,  # noqa: E712
            )
        )
        if not exists:
            raise NotFoundException("商品不存在")

    async def _ensure_not_favorited(
        self, user_id: int, goods_id: int, exclude_id: Optional[int] = None
    ) -> None:
        """业务校验：同一用户对同一商品只能收藏一次"""
        stmt = select(Favorite.id).where(
            Favorite.user_id == user_id,
            Favorite.goods_id == goods_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(Favorite.id != exclude_id)
        if await self.db.scalar(stmt):
            raise ConflictException("该商品已收藏")

    # -------------------- 单条 CRUD（委托 Repository）--------------------

    async def create(self, user_id: int, data: FavoriteCreate) -> FavoriteResponse:
        """收藏商品（归属当前登录用户；同一用户同一商品唯一）"""
        await self._ensure_goods_exists(data.goods_id)
        await self._ensure_not_favorited(user_id, data.goods_id)
        try:
            obj = await self.repo.create(data, user_id)
        except IntegrityError:
            # 并发下由联合唯一键 uk_favorite_user_goods 兜底
            await self.db.rollback()
            raise ConflictException("该商品已收藏")
        return FavoriteResponse.model_validate(obj)

    async def get_detail(self, id: int, user_id: int) -> FavoriteResponse:
        """详情（仅限本人收藏）"""
        obj = await self._get_owned(id, user_id)
        return FavoriteResponse.model_validate(obj)

    async def update(self, id: int, user_id: int, data: FavoriteUpdate) -> FavoriteResponse:
        """更换收藏的商品（仅限本人收藏，且仍需满足唯一性）"""
        await self._get_owned(id, user_id)
        if data.goods_id is not None:
            await self._ensure_goods_exists(data.goods_id)
            await self._ensure_not_favorited(user_id, data.goods_id, exclude_id=id)
        try:
            obj = await self.repo.update(id, data)
        except IntegrityError:
            await self.db.rollback()
            raise ConflictException("该商品已收藏")
        return FavoriteResponse.model_validate(obj)

    async def delete(self, id: int, user_id: int) -> None:
        """取消收藏（仅限本人收藏；本表无软删字段，直接物理删除）"""
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
        分页列表（只返回当前登录用户的收藏）

        业务逻辑（本层）：
        - 强制按 user_id 隔离
        - 支持按商品（goods_id）过滤
        - 排序：最新收藏优先（id 倒序）
        """
        filters = filters or {}
        conditions = [Favorite.user_id == user_id]

        goods_id = filters.get("goods_id")
        if goods_id is not None:
            conditions.append(Favorite.goods_id == goods_id)

        stmt = select(Favorite).order_by(Favorite.id.desc())
        count_stmt = select(func.count()).select_from(Favorite)
        for cond in conditions:
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        offset = (page - 1) * size
        rows = (await self.db.execute(stmt.offset(offset).limit(size))).scalars().all()
        return {
            "items": [FavoriteResponse.model_validate(item) for item in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size else 0,
        }

    # ---------- 在下方添加商业逻辑方法 ----------
