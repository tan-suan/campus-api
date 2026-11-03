"""
收货地址表接口集成测试（直连真实 MySQL）

路径：/api/v1/address
说明：
- 主键字段：id（类型 int）
- user_id 不由请求体传入，而是取当前登录用户（JWT 的 sub），因此本用例先创建测试用户并签发 token。
- 用户隔离：他人地址一律 404；列表只返回本人地址。
- 默认地址互斥：同一用户仅一个默认地址。
- DELETE 为软删除（is_deleted=True/1），记录仍留在表中，详情应 404。
- 状态字段走 PATCH /{id}/status；通用 PUT 不得携带 status / user_id（期望 422）。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.address import Address
from utils.auth import jwt_authenticator


def _new_openid() -> str:
    """生成测试用唯一 openid，避免多次运行冲突"""
    return f"skill_addr_{uuid.uuid4().hex[:12]}"[:64]


def _auth_headers(user_id: int) -> dict:
    """按当前项目 JWT 配置签发测试用认证头（sub = user_id）"""
    token = jwt_authenticator.create_access_token(
        {"sub": str(user_id), "user_type": 1, "status": 1, "username": "it_user"}
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_user(client: httpx.AsyncClient) -> int:
    """通过接口创建测试用户，返回其主键"""
    resp = await client.post(
        "/api/v1/user",
        json={"openid": _new_openid(), "nickname": "地址测试用户"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _db_row(pk: int) -> Address | None:
    """直接读取真实库中的地址记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(Address).where(Address.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_address_crud_flow(app):
    """基础 CRUD + 用户隔离集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0) 准备两个登录用户（用于验证隔离）
        user_id = await _create_user(client)
        other_user_id = await _create_user(client)
        headers = _auth_headers(user_id)
        other_headers = _auth_headers(other_user_id)

        # 0b) 未携带 token 应 401
        resp = await client.get("/api/v1/address")
        assert resp.status_code == 401, resp.text

        # --- 请求体不含 user_id：由登录态注入 ---
        payload = {
            "receiver_name": "集成测试收件人",
            "phone": "13800138000",
            "campus": "东校区",
            "building": "梅园 7 号楼",
            "detail": "305 室",
            "is_default": True,
            "status": 1,
        }

        # 1) 创建
        resp = await client.post("/api/v1/address", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        pk = data["id"]
        assert data["user_id"] == user_id, "user_id 必须取登录态"

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 address 表中找到记录"
        assert row.is_deleted in (False, 0)

        # 1b) 再创建一个默认地址：旧的默认地址应被自动取消
        resp = await client.post(
            "/api/v1/address",
            json={**payload, "detail": "512 室"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        second_pk = resp.json()["data"]["id"]

        resp = await client.get(
            "/api/v1/address",
            params={"page": 1, "page_size": 10, "status": 1},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        items = resp.json()["data"]
        defaults = [item for item in items if item["is_default"]]
        assert len(defaults) == 1, "同一用户只允许一个默认地址"
        assert defaults[0]["id"] == second_pk

        # 2) 详情
        resp = await client.get(f"/api/v1/address/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 3) 更新（不含状态字段）
        resp = await client.put(
            f"/api/v1/address/{pk}",
            json={"building": "梅园 8 号楼", "detail": "101 室"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["building"] == "梅园 8 号楼"

        # 3b) PUT 携带 status / user_id 均应被 Schema 拒绝
        resp = await client.put(f"/api/v1/address/{pk}", json={"status": 0}, headers=headers)
        assert resp.status_code == 422, resp.text
        resp = await client.put(
            f"/api/v1/address/{pk}",
            json={"user_id": other_user_id},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 4) 专用改状态（停用 -> 有效）
        resp = await client.patch(
            f"/api/v1/address/{pk}/status",
            json={"status": 0},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 0

        resp = await client.patch(
            f"/api/v1/address/{pk}/status",
            json={"status": 1},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == 1

        # 5) 用户隔离：他人不可读、不可改、不可删，列表为空
        resp = await client.get(f"/api/v1/address/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.put(
            f"/api/v1/address/{pk}",
            json={"detail": "越权修改"},
            headers=other_headers,
        )
        assert resp.status_code == 404, resp.text

        resp = await client.patch(
            f"/api/v1/address/{pk}/status",
            json={"status": 0},
            headers=other_headers,
        )
        assert resp.status_code == 404, resp.text

        resp = await client.delete(f"/api/v1/address/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.get("/api/v1/address", headers=other_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 0, "他人列表不应包含我的地址"

        # 6) 删除（软删除）
        resp = await client.delete(f"/api/v1/address/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/address/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        assert row is not None, "软删除后记录应仍留在 address 表中"
        assert row.is_deleted in (True, 1)

        # 清理：删除第二个地址 + 两个测试用户（均为软删除）
        resp = await client.delete(f"/api/v1/address/{second_pk}", headers=headers)
        assert resp.status_code == 200, resp.text
        for uid in (user_id, other_user_id):
            resp = await client.delete(f"/api/v1/user/{uid}")
            assert resp.status_code == 200, resp.text


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_address_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试（如默认地址设置、地址选择器联动）

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/address/...", json={...}, headers={...})
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
