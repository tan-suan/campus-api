"""
商品规格表接口集成测试（直连真实 MySQL）

路径：/api/v1/goods-spec
说明：
- 主键字段：id（类型 int）
- 外键：goods_id → goods(id)，用例会先创建测试分类与商品再创建规格
- DELETE 为软删除（is_deleted=True/1），记录仍留在表中，详情应 404。
- 状态字段走 PATCH /{id}/status；通用 PUT 不得携带 status（期望 422）。
- 关联商品不存在时，创建规格应返回 404（业务校验在 Service）。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.goods_spec import GoodsSpec


def _new_goods_no() -> str:
    """生成测试用唯一商品编号"""
    return f"skill_spec_{uuid.uuid4().hex[:10]}"[:32]


def _new_category_code() -> str:
    """生成测试用唯一分类标识"""
    return f"skill_spec_c_{uuid.uuid4().hex[:8]}"[:32]


def _missing_goods_id() -> int:
    """生成一个几乎不可能存在的商品ID，用于校验关联校验"""
    return 9_000_000_000 + (uuid.uuid4().int % 10_000_000)


async def _db_row(pk: int) -> GoodsSpec | None:
    """直接读取真实库中的规格记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(GoodsSpec).where(GoodsSpec.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_goods_spec_crud_flow(app):
    """基础 CRUD 集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0) 准备外键依赖：测试分类 + 测试商品
        resp = await client.post(
            "/api/v1/category",
            json={"code": _new_category_code(), "name": "集成测试规格分类", "sort": 99},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        category_id = resp.json()["data"]["id"]

        resp = await client.post(
            "/api/v1/goods",
            json={
                "goods_no": _new_goods_no(),
                "name": "规格测试商品",
                "category_id": category_id,
                "price": "12.90",
                "origin_price": "19.90",
                "stock": 20,
                "total_stock": 20,
                "sort": 99,
                "status": 1,
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        goods_id = resp.json()["data"]["id"]

        # 0b) 关联商品不存在时应被 Service 拒绝
        resp = await client.post(
            "/api/v1/goods-spec",
            json={"goods_id": _missing_goods_id(), "spec_name": "幽灵规格", "price": "1.00"},
            headers=headers,
        )
        assert resp.status_code == 404, resp.text

        # --- 生成 Create 请求体：通过 goods_id 关联商品 ---
        payload = {
            "goods_id": goods_id,
            "spec_name": "微辣",
            "price": "12.90",
            "origin_price": "19.90",
            "stock": 20,
            "sort": 99,
            "status": 1,
        }

        # 1) 创建
        resp = await client.post("/api/v1/goods-spec", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        pk = data["id"]
        assert data["goods_id"] == goods_id

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 goods_spec 表中找到记录"
        assert row.is_deleted in (False, 0)

        # 2) 列表（按所属商品过滤）
        resp = await client.get(
            "/api/v1/goods-spec",
            params={"page": 1, "page_size": 10, "goods_id": goods_id},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] >= 1

        # 3) 详情
        resp = await client.get(f"/api/v1/goods-spec/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 4) 更新（不含状态字段）
        update_payload = {
            "spec_name": "中辣",
            "price": "13.90",
            "stock": 15,
            "sort": 98,
        }
        resp = await client.put(
            f"/api/v1/goods-spec/{pk}",
            json=update_payload,
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["spec_name"] == "中辣"

        # 4b) PUT 携带状态字段应被 Schema 拒绝
        resp = await client.put(
            f"/api/v1/goods-spec/{pk}",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 5) 专用改状态（停用 -> 启用）
        resp = await client.patch(
            f"/api/v1/goods-spec/{pk}/status",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 0

        resp = await client.patch(
            f"/api/v1/goods-spec/{pk}/status",
            json={"status": 1},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 1

        # 删除（软删除）
        resp = await client.delete(f"/api/v1/goods-spec/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/goods-spec/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        assert row is not None, "软删除后记录应仍留在 goods_spec 表中"
        assert row.is_deleted in (True, 1)

        # 清理外键依赖：测试商品 + 测试分类
        resp = await client.delete(f"/api/v1/goods/{goods_id}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.delete(f"/api/v1/category/{category_id}", headers=headers)
        assert resp.status_code == 200, resp.text


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_goods_spec_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/goods-spec/...", json={...}, headers=headers)
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
