"""
自提点表接口集成测试（直连真实 MySQL）

路径：/api/v1/pickup-point
说明：
- 主键字段：id（类型 int）
- DELETE 为软删除（is_deleted=True/1），记录仍留在表中，详情应 404。
- 状态字段走 PATCH /{id}/status；通用 PUT 不得携带状态字段（期望 422）。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.pickup_point import PickupPoint


async def _db_row(pk: int) -> PickupPoint | None:
    """直接读取真实库中的自提点记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(PickupPoint).where(PickupPoint.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_pickup_point_crud_flow(app):
    """基础 CRUD 集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # --- 生成 Create 请求体：本表无唯一约束字段 ---
        payload = {
            "name": "集成测试自提点",
            "business_hours": "08:00 - 21:00",
            "distance_desc": "步行 3 分钟",
            "address": "东校区 3 号宿舍楼一层",
            "contact_phone": "0571-88888888",
            "sort": 99,
            "status": 1,
        }

        # 1) 创建
        resp = await client.post("/api/v1/pickup-point", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        pk = data["id"]

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 pickup_point 表中找到记录"
        assert row.is_deleted in (False, 0)

        # 2) 列表
        resp = await client.get(
            "/api/v1/pickup-point",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] >= 1

        # 3) 详情
        resp = await client.get(f"/api/v1/pickup-point/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 4) 更新（不含状态/标识位字段）
        update_payload = {
            "name": "集成测试自提点-已更新",
            "business_hours": "09:00 - 22:00",
            "sort": 98,
        }
        resp = await client.put(
            f"/api/v1/pickup-point/{pk}",
            json=update_payload,
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["name"] == "集成测试自提点-已更新"

        # 4b) PUT 携带状态字段应被 Schema 拒绝
        resp = await client.put(
            f"/api/v1/pickup-point/{pk}",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 5) 专用改状态（停用 -> 启用）
        resp = await client.patch(
            f"/api/v1/pickup-point/{pk}/status",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 0

        resp = await client.patch(
            f"/api/v1/pickup-point/{pk}/status",
            json={"status": 1},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 1

        # 删除
        resp = await client.delete(f"/api/v1/pickup-point/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/pickup-point/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        assert row is not None, "软删除后记录应仍留在 pickup_point 表中"
        assert row.is_deleted in (True, 1)


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_pickup_point_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    headers = {"Authorization": "Bearer test-token"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/pickup-point/...", json={...}, headers=headers)
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
