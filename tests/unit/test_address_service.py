"""
收货地址表服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 AddressService 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 单条 CRUD 可测 Service 对 Repository 的委托；用户隔离、默认地址互斥等业务逻辑在此补充。
"""

import pytest

from schemas.address import AddressCreate, AddressStatusUpdate, AddressUpdate
from service.address_service import AddressService


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 AddressService 单元测试后移除 skip")
async def test_address_service_create_placeholder(session):
    """占位：创建（委托 Repository.create，user_id 由登录态注入）"""
    service = AddressService(session)
    # data = AddressCreate(receiver_name="小闪", phone="13800138000", building="梅园 7 号楼")
    # result = await service.create(1, data)
    # assert result is not None
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 AddressService 单元测试后移除 skip")
async def test_address_service_get_detail_placeholder(session):
    """占位：详情（含用户归属校验：非本人地址应 404）"""
    service = AddressService(session)
    # result = await service.get_detail(1, 1)
    # assert result.user_id == 1
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 AddressService 单元测试后移除 skip")
async def test_address_service_update_placeholder(session):
    """占位：更新（委托 Repository.update，仅限本人地址）"""
    service = AddressService(session)
    # result = await service.update(1, 1, AddressUpdate(building="梅园 8 号楼"))
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 AddressService 单元测试后移除 skip")
async def test_address_service_delete_placeholder(session):
    """占位：软删除（委托 Repository.delete，仅置 is_deleted）"""
    service = AddressService(session)
    # await service.delete(1, 1)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐列表业务测试后移除 skip")
async def test_address_service_get_list_placeholder(session):
    """占位：分页列表（业务逻辑：按 user_id 隔离 + 排除软删除 + 状态过滤 + 默认地址优先）"""
    service = AddressService(session)
    # result = await service.get_list(user_id=1, page=1, size=10)
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐状态变更业务测试后移除 skip")
async def test_address_service_update_status_placeholder(session):
    """占位：状态变更（Service.update_status，仅限本人地址）"""
    service = AddressService(session)
    # result = await service.update_status(1, 1, AddressStatusUpdate(status=0))
    assert False, "请实现 update_status 单元测试"


# ---------- 在下方添加更多业务方法的单元测试占位（如默认地址互斥）----------
