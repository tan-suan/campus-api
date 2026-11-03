"""
商品表服务层单元测试（占位）

【HAND-WRITTEN 占位】由 sql-to-fastapi-restfulapi-scaffold 首次生成；已存在则跳过。
目标：面向 GoodsService 的单元测试（建议使用 conftest 的 sqlite `session` fixture）。

说明：
- 本文件为占位骨架，默认用例可先 skip，待业务稳定后补齐断言。
- 单条 CRUD 可测 Service 对 Repository 的委托；秒杀/热销/上下架/软删除等业务逻辑在此补充。
"""

import pytest

from schemas.goods import GoodsCreate, GoodsStatusUpdate, GoodsUpdate
from service.goods_service import GoodsService


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 GoodsService 单元测试后移除 skip")
async def test_goods_service_create_placeholder(session):
    """占位：创建（委托 Repository.create，并校验分类存在）"""
    service = GoodsService(session)
    # data = GoodsCreate(goods_no="SP001", name="香辣鸡腿堡", category_id=1, price="12.90")
    # result = await service.create(data)
    # assert result is not None
    assert False, "请实现 create 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 GoodsService 单元测试后移除 skip")
async def test_goods_service_get_detail_placeholder(session):
    """占位：详情（委托 Repository.get）"""
    service = GoodsService(session)
    # result = await service.get_detail(1)
    # assert result.id is not None
    assert False, "请实现 get_detail 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 GoodsService 单元测试后移除 skip")
async def test_goods_service_update_placeholder(session):
    """占位：更新（委托 Repository.update）"""
    service = GoodsService(session)
    # result = await service.update(1, GoodsUpdate(name="香辣鸡腿堡（大份）"))
    assert False, "请实现 update 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐 GoodsService 单元测试后移除 skip")
async def test_goods_service_delete_placeholder(session):
    """占位：软删除（委托 Repository.delete，仅置 is_deleted）"""
    service = GoodsService(session)
    # await service.delete(1)
    assert False, "请实现 delete 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐列表业务测试后移除 skip")
async def test_goods_service_get_list_placeholder(session):
    """占位：分页列表（Service 业务逻辑：排除软删除 + 分类/秒杀/热销/上下架过滤）"""
    service = GoodsService(session)
    # result = await service.get_list(page=1, size=10, filters={"flash": True})
    # assert "items" in result and "total" in result
    assert False, "请实现 get_list 单元测试"


@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐上下架业务测试后移除 skip")
async def test_goods_service_update_status_placeholder(session):
    """占位：上下架状态变更（Service.update_status）"""
    service = GoodsService(session)
    # result = await service.update_status(1, GoodsStatusUpdate(status=0))
    assert False, "请实现 update_status 单元测试"


# ---------- 在下方添加更多业务方法的单元测试占位 ----------
