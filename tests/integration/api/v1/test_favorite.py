"""
商品收藏表接口集成测试（直连真实 MySQL）

路径：/api/v1/favorite
说明：
- 主键字段：id（类型 int）
- user_id 不由请求体传入，而是取当前登录用户（JWT 的 sub），因此本用例先创建测试用户并签发 token。
- 唯一性：同一用户对同一商品重复收藏返回 409；不同用户可收藏同一商品。
- 用户隔离：他人收藏一律 404；列表只返回本人收藏。
- 本表无 is_deleted 字段，DELETE 为物理删除（库中记录应消失）。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.favorite import Favorite
from utils.auth import jwt_authenticator


def _new_openid() -> str:
    """生成测试用唯一 openid，避免多次运行冲突"""
    return f"skill_fav_{uuid.uuid4().hex[:12]}"[:64]


def _new_goods_no() -> str:
    """生成测试用唯一商品编号"""
    return f"skill_fav_no_{uuid.uuid4().hex[:8]}"[:32]


def _new_category_code() -> str:
    """生成测试用唯一分类标识"""
    return f"skill_fav_c_{uuid.uuid4().hex[:8]}"[:32]


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
        json={"openid": _new_openid(), "nickname": "收藏测试用户"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_goods(client: httpx.AsyncClient) -> tuple[int, int]:
    """创建测试分类与商品，返回 (category_id, goods_id)"""
    resp = await client.post(
        "/api/v1/category",
        json={"code": _new_category_code(), "name": "收藏测试分类", "sort": 99},
    )
    assert resp.status_code == 201, resp.text
    category_id = resp.json()["data"]["id"]

    resp = await client.post(
        "/api/v1/goods",
        json={
            "goods_no": _new_goods_no(),
            "name": "收藏测试商品",
            "category_id": category_id,
            "price": "9.90",
            "origin_price": "15.90",
            "stock": 10,
            "total_stock": 10,
            "sort": 99,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return category_id, resp.json()["data"]["id"]


async def _db_row(pk: int) -> Favorite | None:
    """直接读取真实库中的收藏记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(Favorite).where(Favorite.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_favorite_crud_flow(app):
    """基础 CRUD + 唯一性 + 用户隔离集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0) 准备数据：两个用户 + 一个商品
        user_id = await _create_user(client)
        other_user_id = await _create_user(client)
        category_id, goods_id = await _create_goods(client)
        headers = _auth_headers(user_id)
        other_headers = _auth_headers(other_user_id)

        # 0b) 未携带 token 应 401
        resp = await client.get("/api/v1/favorite")
        assert resp.status_code == 401, resp.text

        # 0c) 收藏不存在的商品应 404
        resp = await client.post(
            "/api/v1/favorite",
            json={"goods_id": 9_000_000_001},
            headers=headers,
        )
        assert resp.status_code == 404, resp.text

        # 1) 收藏
        resp = await client.post("/api/v1/favorite", json={"goods_id": goods_id}, headers=headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        pk = data["id"]
        assert data["user_id"] == user_id, "user_id 必须取登录态"
        assert data["goods_id"] == goods_id

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 favorite 表中找到记录"

        # 1b) 同一用户重复收藏应 409
        resp = await client.post("/api/v1/favorite", json={"goods_id": goods_id}, headers=headers)
        assert resp.status_code == 409, resp.text

        # 1c) 不同用户可收藏同一商品
        resp = await client.post(
            "/api/v1/favorite",
            json={"goods_id": goods_id},
            headers=other_headers,
        )
        assert resp.status_code == 201, resp.text
        other_pk = resp.json()["data"]["id"]

        # 2) 列表（按商品过滤）
        resp = await client.get(
            "/api/v1/favorite",
            params={"page": 1, "page_size": 10, "goods_id": goods_id},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] >= 1

        # 3) 详情
        resp = await client.get(f"/api/v1/favorite/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 4) 更换收藏商品（与自身相同不触发唯一冲突）
        resp = await client.put(
            f"/api/v1/favorite/{pk}",
            json={"goods_id": goods_id},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["goods_id"] == goods_id

        # 5) 用户隔离：他人不可读、不可改、不可删，列表不含我的收藏
        resp = await client.get(f"/api/v1/favorite/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.put(
            f"/api/v1/favorite/{pk}",
            json={"goods_id": goods_id},
            headers=other_headers,
        )
        assert resp.status_code == 404, resp.text

        resp = await client.delete(f"/api/v1/favorite/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.get("/api/v1/favorite", headers=other_headers)
        assert resp.status_code == 200, resp.text
        other_items = resp.json()["data"]
        assert all(item["id"] != pk for item in other_items), "他人列表不应包含我的收藏"

        # 6) 取消收藏（物理删除）
        resp = await client.delete(f"/api/v1/favorite/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/favorite/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        assert await _db_row(pk) is None, "本表无软删字段，删除后记录应从库中消失"

        # 清理：他人收藏 + 商品 + 分类 + 两个测试用户
        resp = await client.delete(f"/api/v1/favorite/{other_pk}", headers=other_headers)
        assert resp.status_code == 200, resp.text
        resp = await client.delete(f"/api/v1/goods/{goods_id}")
        assert resp.status_code == 200, resp.text
        resp = await client.delete(f"/api/v1/category/{category_id}")
        assert resp.status_code == 200, resp.text
        for uid in (user_id, other_user_id):
            resp = await client.delete(f"/api/v1/user/{uid}")
            assert resp.status_code == 200, resp.text


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_favorite_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试（如收藏与取消收藏的幂等切换）

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/favorite/...", json={...}, headers={...})
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
