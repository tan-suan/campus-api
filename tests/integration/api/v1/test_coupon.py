"""
优惠券表接口集成测试（直连真实 MySQL）

路径：/api/v1/coupon
说明：
- 主键字段：id（类型 int）
- 本表为平台配置数据，接口按脚手架默认不启用鉴权。
- code 全局唯一：重复编码创建应返回 409。
- DELETE 为软删除（is_deleted=True/1），记录仍留在表中，详情应 404。
- 状态字段走 PATCH /{id}/status；通用 PUT 不得携带 status（期望 422）。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.coupon import Coupon


def _new_code() -> str:
    """生成测试用唯一优惠券编码，避免多次运行冲突"""
    return f"skill_cp_{uuid.uuid4().hex[:8]}"[:32]


async def _db_row(pk: int) -> Coupon | None:
    """直接读取真实库中的优惠券记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(Coupon).where(Coupon.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_coupon_crud_flow(app):
    """基础 CRUD 集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        code = _new_code()

        # --- 生成 Create 请求体：code 唯一，使用 _new_code() ---
        payload = {
            "code": code,
            "name": "集成测试满减券",
            "threshold": "20.00",
            "amount": "3.00",
            "scope": "全场通用",
            "description": "集成测试用满减券",
            "total": 100,
            "received": 0,
            "start_time": "2026-11-01T00:00:00",
            "end_time": "2026-12-31T23:59:59",
            "status": 1,
        }

        # 1) 创建
        resp = await client.post("/api/v1/coupon", json=payload)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        pk = data["id"]

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 coupon 表中找到记录"
        assert row.is_deleted in (False, 0)

        # 1b) 编码重复应返回 409
        resp = await client.post("/api/v1/coupon", json=payload)
        assert resp.status_code == 409, resp.text

        # 2) 列表（关键字检索）
        resp = await client.get(
            "/api/v1/coupon",
            params={"page": 1, "page_size": 10, "keyword": code},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] >= 1

        # 3) 详情
        resp = await client.get(f"/api/v1/coupon/{pk}")
        assert resp.status_code == 200, resp.text

        # 4) 更新（不含状态字段）
        update_payload = {
            "name": "集成测试满减券-已更新",
            "threshold": "30.00",
            "amount": "5.00",
        }
        resp = await client.put(f"/api/v1/coupon/{pk}", json=update_payload)
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["name"] == "集成测试满减券-已更新"

        # 4b) PUT 携带状态字段应被 Schema 拒绝
        resp = await client.put(f"/api/v1/coupon/{pk}", json={"status": 0})
        assert resp.status_code == 422, resp.text

        # 5) 专用改状态（停用 -> 可用）
        resp = await client.patch(f"/api/v1/coupon/{pk}/status", json={"status": 0})
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 0

        resp = await client.patch(f"/api/v1/coupon/{pk}/status", json={"status": 1})
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 1

        # 删除（软删除）
        resp = await client.delete(f"/api/v1/coupon/{pk}")
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/coupon/{pk}")
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        assert row is not None, "软删除后记录应仍留在 coupon 表中"
        assert row.is_deleted in (True, 1)


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_coupon_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试（如领券、可用券校验）

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/coupon/...", json={...})
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
