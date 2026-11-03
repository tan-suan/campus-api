"""
购物车表服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 CartService 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 单条 CRUD 可测 Service 对 Repository 的委托；加购累加、规格快照、用户隔离、上下限等业务在此补充。
"""

import pytest

from schemas.cart import CartCreate, CartSelectedUpdate, CartUpdate
from service.cart_service import CartService


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CartService 单元测试后移除 skip")
async def test_cart_service_create_placeholder(session):
    """占位：加购（校验商品/规格存在 + 写入规格快照）"""
    service = CartService(session)
    # data = CartCreate(goods_id=1, goods_spec_id=None, qty=1)
    # result = await service.create(1, data)
    # assert result.spec_name == "默认"
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CartService 单元测试后移除 skip")
async def test_cart_service_create_accumulate_placeholder(session):
    """占位：同「用户+商品+规格」重复加购应累加 qty（不新增条目）"""
    service = CartService(session)
    # await service.create(1, CartCreate(goods_id=1, qty=1))
    # result = await service.create(1, CartCreate(goods_id=1, qty=2))
    # assert result.qty == 3
    assert False, "请实现加购累加单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CartService 单元测试后移除 skip")
async def test_cart_service_get_detail_placeholder(session):
    """占位：详情（含用户归属校验：非本人条目应 404）"""
    service = CartService(session)
    # result = await service.get_detail(1, 1)
    # assert result.user_id == 1
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CartService 单元测试后移除 skip")
async def test_cart_service_update_placeholder(session):
    """占位：修改数量（委托 Repository.update）"""
    service = CartService(session)
    # result = await service.update(1, 1, CartUpdate(qty=5))
    # assert result.qty == 5
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CartService 单元测试后移除 skip")
async def test_cart_service_update_selected_placeholder(session):
    """占位：勾选 / 取消勾选（Service.update_selected）"""
    service = CartService(session)
    # result = await service.update_selected(1, 1, CartSelectedUpdate(selected=False))
    # assert result.selected is False
    assert False, "请实现 update_selected 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CartService 单元测试后移除 skip")
async def test_cart_service_delete_placeholder(session):
    """占位：删除条目（本表无软删字段，物理删除）"""
    service = CartService(session)
    # await service.delete(1, 1)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐列表业务测试后移除 skip")
async def test_cart_service_get_list_placeholder(session):
    """占位：分页列表（业务逻辑：按 user_id 隔离 + selected / goods_id 过滤）"""
    service = CartService(session)
    # result = await service.get_list(user_id=1, page=1, size=10, filters={"selected": True})
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


# ---------- 在下方添加更多业务方法的单元测试占位（如数量上限 999）----------
