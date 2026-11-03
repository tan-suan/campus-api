"""
优惠券表服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 CouponService 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 单条 CRUD 可测 Service 对 Repository 的委托；编码唯一、列表过滤、状态变更在此补充。
"""

import pytest

from schemas.coupon import CouponCreate, CouponStatusUpdate, CouponUpdate
from service.coupon_service import CouponService


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CouponService 单元测试后移除 skip")
async def test_coupon_service_create_placeholder(session):
    """占位：创建（委托 Repository.create，并校验编码唯一）"""
    service = CouponService(session)
    # data = CouponCreate(code="FULL20MINUS3", name="满 20 减 3", threshold="20.00", amount="3.00")
    # result = await service.create(data)
    # assert result is not None
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CouponService 单元测试后移除 skip")
async def test_coupon_service_get_detail_placeholder(session):
    """占位：详情（委托 Repository.get）"""
    service = CouponService(session)
    # result = await service.get_detail(1)
    # assert result.id is not None
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CouponService 单元测试后移除 skip")
async def test_coupon_service_update_placeholder(session):
    """占位：更新（委托 Repository.update）"""
    service = CouponService(session)
    # result = await service.update(1, CouponUpdate(amount="5.00"))
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 CouponService 单元测试后移除 skip")
async def test_coupon_service_delete_placeholder(session):
    """占位：软删除（委托 Repository.delete，仅置 is_deleted）"""
    service = CouponService(session)
    # await service.delete(1)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐列表业务测试后移除 skip")
async def test_coupon_service_get_list_placeholder(session):
    """占位：分页列表（业务逻辑：排除软删除 + 状态过滤 + 关键字检索）"""
    service = CouponService(session)
    # result = await service.get_list(page=1, size=10, filters={"keyword": "满"})
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐状态变更业务测试后移除 skip")
async def test_coupon_service_update_status_placeholder(session):
    """占位：状态变更（Service.update_status）"""
    service = CouponService(session)
    # result = await service.update_status(1, CouponStatusUpdate(status=0))
    assert False, "请实现 update_status 单元测试"


# ---------- 在下方添加更多业务方法的单元测试占位 ----------
