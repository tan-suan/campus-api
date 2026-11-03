"""
订单明细表服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 OrderItemService 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 重点业务：商品快照与成交价解析、小计计算、订单归属隔离（经 order.user_id）、
  明细变更后订单金额/件数联动、仅待付款订单可编辑。
"""

import pytest

from schemas.order_item import OrderItemCreate, OrderItemUpdate
from service.order_item_service import OrderItemService


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderItemService 单元测试后移除 skip")
async def test_order_item_service_create_placeholder(session):
    """占位：追加明细（解析商品快照与成交价，subtotal = 单价 × 数量）"""
    service = OrderItemService(session)
    # data = OrderItemCreate(order_id=1, goods_id=1, goods_spec_id=2, qty=2)
    # result = await service.create(1, data)
    # assert result.subtotal == Decimal("31.00")
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderItemService 单元测试后移除 skip")
async def test_order_item_service_get_detail_placeholder(session):
    """占位：详情（经 order.user_id 校验归属，越权应 404）"""
    service = OrderItemService(session)
    # result = await service.get_detail(1, 1)
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderItemService 单元测试后移除 skip")
async def test_order_item_service_update_placeholder(session):
    """占位：修改数量（按冻结单价重算小计，并联动订单金额）"""
    service = OrderItemService(session)
    # result = await service.update(1, 1, OrderItemUpdate(qty=1))
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderItemService 单元测试后移除 skip")
async def test_order_item_service_delete_placeholder(session):
    """占位：软删除明细并联动订单金额（终态订单应 409）"""
    service = OrderItemService(session)
    # await service.delete(1, 1)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderItemService 单元测试后移除 skip")
async def test_order_item_service_get_list_placeholder(session):
    """占位：分页列表（通过 order_id 关联订单做用户隔离，支持 order_id 过滤）"""
    service = OrderItemService(session)
    # result = await service.get_list(user_id=1, page=1, size=10, filters={"order_id": 1})
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


# ---------- 在下方添加更多业务方法的单元测试占位 ----------
