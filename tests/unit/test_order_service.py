"""
订单表服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 OrderService 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 重点业务：下单金额计算（goods_total / freight / discount / pay_amount）、取货码生成、
  状态机流转（pending → picking → done / canceled）、取消与确认完成、用户隔离。
"""

from decimal import Decimal

import pytest

from models.order import OrderMode, OrderStatus
from schemas.order import OrderCreate, OrderItemInput, OrderStatusUpdate, OrderUpdate
from service.order_service import OrderService, calc_freight, calc_pay_amount


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderService 单元测试后移除 skip")
async def test_order_service_create_placeholder(session):
    """占位：下单（校验自提点/地址、冻结商品快照、计算金额、生成订单号与取货码）"""
    service = OrderService(session)
    # data = OrderCreate(mode=OrderMode.PICKUP, pickup_point_id=1, items=[OrderItemInput(goods_id=1, qty=2)])
    # result = await service.create(1, data)
    # assert result.goods_total == Decimal("31.00") and result.pickup_code.startswith("A-")
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderService 单元测试后移除 skip")
async def test_order_service_get_detail_placeholder(session):
    """占位：详情（含明细快照 + 用户归属校验：非本人订单 404）"""
    service = OrderService(session)
    # result = await service.get_detail(1, 1)
    # assert len(result.items) >= 1
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderService 单元测试后移除 skip")
async def test_order_service_update_placeholder(session):
    """占位：更新备注/期望时间（已取消、已完成订单应 409）"""
    service = OrderService(session)
    # result = await service.update(1, 1, OrderUpdate(remark="放门口"))
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderService 单元测试后移除 skip")
async def test_order_service_delete_placeholder(session):
    """占位：软删除（委托 Repository.delete，仅置 is_deleted）"""
    service = OrderService(session)
    # await service.delete(1, 1)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 OrderService 单元测试后移除 skip")
async def test_order_service_get_list_placeholder(session):
    """占位：分页列表（按 user_id 隔离 + status/mode 过滤 + 订单号检索 + 排除软删除）"""
    service = OrderService(session)
    # result = await service.get_list(user_id=1, page=1, size=10, filters={"status": OrderStatus.PENDING})
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐状态机测试后移除 skip")
async def test_order_service_update_status_placeholder(session):
    """占位：状态变更（状态机校验：pending→picking 合法，picking→pending 应 409）"""
    service = OrderService(session)
    # result = await service.update_status(1, 1, OrderStatusUpdate(status=OrderStatus.PICKING))
    # assert result.pay_time is not None
    assert False, "请实现 update_status 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐取消/完成业务测试后移除 skip")
async def test_order_service_cancel_and_complete_placeholder(session):
    """占位：取消订单与确认完成（cancel 记录 cancel_time；confirm_done 记录 done_time）"""
    service = OrderService(session)
    # canceled = await service.cancel(1, 1)
    # assert canceled.status is OrderStatus.CANCELED and canceled.cancel_time is not None
    assert False, "请实现 cancel / confirm_done 单元测试"


def test_order_amount_rules_placeholder():
    """占位（无需数据库）：配送费与实付金额的纯函数规则"""
    assert calc_freight(OrderMode.PICKUP) == Decimal("0.00")
    assert calc_freight(OrderMode.DORM) > 0
    assert calc_pay_amount(10, 2, 3) == Decimal("9.00")


# ---------- 在下方添加更多业务方法的单元测试占位 ----------
