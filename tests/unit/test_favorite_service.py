"""
商品收藏表服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 FavoriteService 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 单条 CRUD 可测 Service 对 Repository 的委托；用户隔离、同一用户同一商品唯一（409）在此补充。
"""

import pytest

from schemas.favorite import FavoriteCreate, FavoriteUpdate
from service.favorite_service import FavoriteService


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 FavoriteService 单元测试后移除 skip")
async def test_favorite_service_create_placeholder(session):
    """占位：创建（校验商品存在 + 同一用户同一商品唯一）"""
    service = FavoriteService(session)
    # data = FavoriteCreate(goods_id=1)
    # result = await service.create(1, data)
    # assert result is not None
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 FavoriteService 单元测试后移除 skip")
async def test_favorite_service_get_detail_placeholder(session):
    """占位：详情（含用户归属校验：非本人收藏应 404）"""
    service = FavoriteService(session)
    # result = await service.get_detail(1, 1)
    # assert result.user_id == 1
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 FavoriteService 单元测试后移除 skip")
async def test_favorite_service_update_placeholder(session):
    """占位：更换收藏商品（委托 Repository.update，仍需唯一）"""
    service = FavoriteService(session)
    # result = await service.update(1, 1, FavoriteUpdate(goods_id=2))
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 FavoriteService 单元测试后移除 skip")
async def test_favorite_service_delete_placeholder(session):
    """占位：取消收藏（本表无软删字段，物理删除）"""
    service = FavoriteService(session)
    # await service.delete(1, 1)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐列表业务测试后移除 skip")
async def test_favorite_service_get_list_placeholder(session):
    """占位：分页列表（业务逻辑：按 user_id 隔离 + 可选 goods_id 过滤）"""
    service = FavoriteService(session)
    # result = await service.get_list(user_id=1, page=1, size=10)
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐唯一性业务测试后移除 skip")
async def test_favorite_service_duplicate_placeholder(session):
    """占位：重复收藏应抛 ConflictException（同一用户同一商品唯一）"""
    service = FavoriteService(session)
    # with pytest.raises(ConflictException):
    #     await service.create(1, FavoriteCreate(goods_id=1))
    assert False, "请实现重复收藏单元测试"


# ---------- 在下方添加更多业务方法的单元测试占位 ----------
