"""
商品表接口集成测试（直连真实 MySQL）

路径：/api/v1/goods
说明：
- 主键字段：id（类型 int）
- 外键：category_id → category(id)，用例会先创建测试分类再创建商品
- DELETE 为软删除（is_deleted=True/1），记录仍留在表中，详情应 404。
- 上下架状态走 PATCH /{id}/status；通用 PUT 不得携带 status（期望 422）。
- flash（秒杀）/ hot（热销）为业务标识，可通过 PUT 修改，并可在列表接口过滤。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.goods import Goods


def _new_goods_no() -> str:
    """生成测试用唯一商品编号，避免多次运行冲突"""
    return f"skill_no_{uuid.uuid4().hex[:10]}"[:32]


def _new_category_code() -> str:
    """生成测试用唯一分类标识，供商品外键使用"""
    return f"skill_goods_{uuid.uuid4().hex[:8]}"[:32]


async def _db_row(pk: int) -> Goods | None:
    """直接读取真实库中的商品记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(Goods).where(Goods.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_goods_crud_flow(app):
    """基础 CRUD 集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0) 准备外键依赖：测试分类
        resp = await client.post(
            "/api/v1/category",
            json={"code": _new_category_code(), "name": "集成测试商品分类", "sort": 99},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        category_id = resp.json()["data"]["id"]

        # --- 生成 Create 请求体：goods_no 唯一，使用 _new_goods_no() ---
        payload = {
            "goods_no": _new_goods_no(),
            "name": "集成测试商品",
            "category_id": category_id,
            "price": "12.90",
            "origin_price": "19.90",
            "stock": 50,
            "total_stock": 100,
            "sold": 0,
            "emoji": "🍔",
            "tint": "#FFF1E6",
            "main_image": "https://example.com/goods/it.png",
            "tag": "秒杀价",
            "summary": "集成测试用商品",
            "detail": "集成测试用商品详情",
            "flash": True,
            "hot": True,
            "sort": 99,
            "status": 1,
        }

        # 1) 创建
        resp = await client.post("/api/v1/goods", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        pk = data["id"]
        assert data["flash"] is True and data["hot"] is True

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 goods 表中找到记录"
        assert row.is_deleted in (False, 0)

        # 2) 列表（含分类 / 秒杀 / 热销过滤）
        resp = await client.get(
            "/api/v1/goods",
            params={"page": 1, "page_size": 10, "category_id": category_id, "flash": True},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] >= 1

        # 3) 详情
        resp = await client.get(f"/api/v1/goods/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 4) 更新（不含上下架状态字段；flash/hot 属普通业务字段）
        update_payload = {
            "name": "集成测试商品-已更新",
            "stock": 40,
            "flash": False,
            "hot": True,
            "sort": 98,
        }
        resp = await client.put(
            f"/api/v1/goods/{pk}",
            json=update_payload,
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        updated = resp.json()["data"]
        assert updated["name"] == "集成测试商品-已更新"
        assert updated["flash"] is False

        # 4b) PUT 携带上下架状态字段应被 Schema 拒绝
        resp = await client.put(
            f"/api/v1/goods/{pk}",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 5) 专用上下架接口（下架 -> 上架）
        resp = await client.patch(
            f"/api/v1/goods/{pk}/status",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 0

        resp = await client.patch(
            f"/api/v1/goods/{pk}/status",
            json={"status": 1},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 1

        # 删除（软删除）
        resp = await client.delete(f"/api/v1/goods/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/goods/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        assert row is not None, "软删除后记录应仍留在 goods 表中"
        assert row.is_deleted in (True, 1)

        # 清理外键依赖：测试分类
        resp = await client.delete(f"/api/v1/category/{category_id}", headers=headers)
        assert resp.status_code == 200, resp.text


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_goods_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/goods/...", json={...}, headers=headers)
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
