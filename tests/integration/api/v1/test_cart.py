"""
购物车表接口集成测试（直连真实 MySQL）

路径：/api/v1/cart
说明：
- 主键字段：id（类型 int）
- user_id 不由请求体传入，而是取当前登录用户（JWT 的 sub），因此本用例先创建测试用户并签发 token。
- 加购累加：同一「用户 + 商品 + 规格」重复 POST 只累加 qty，不新增条目；
  goods_spec_id 为空（默认规格）时同样累加（Service 用 IS NULL 显式判重）。
- 勾选标识位走 PATCH /{id}/selected；通用 PUT 只能改 qty，携带 selected 返回 422。
- 用户隔离：他人条目一律 404；列表只返回本人条目。
- 本表无 is_deleted 字段，DELETE 为物理删除（库中记录应消失）。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.cart import Cart
from utils.auth import jwt_authenticator


def _new_openid() -> str:
    """生成测试用唯一 openid，避免多次运行冲突"""
    return f"skill_cart_{uuid.uuid4().hex[:12]}"[:64]


def _new_category_code() -> str:
    """生成测试用唯一分类标识"""
    return f"skill_cart_c_{uuid.uuid4().hex[:8]}"[:32]


def _new_goods_no() -> str:
    """生成测试用唯一商品编号"""
    return f"skill_cart_no_{uuid.uuid4().hex[:8]}"[:32]


def _auth_headers(user_id: int) -> dict:
    """按当前项目 JWT 配置签发测试用认证头（sub = user_id）"""
    token = jwt_authenticator.create_access_token(
        {"sub": str(user_id), "user_type": 1, "status": 1, "username": "it_user"}
    )
    return {"Authorization": f"Bearer {token}"}


async def _create_user(client: httpx.AsyncClient, nickname: str) -> int:
    """通过接口创建测试用户，返回其主键"""
    resp = await client.post(
        "/api/v1/user",
        json={"openid": _new_openid(), "nickname": nickname},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_goods(client: httpx.AsyncClient, category_id: int, name: str) -> int:
    """创建测试商品并返回主键"""
    resp = await client.post(
        "/api/v1/goods",
        json={
            "goods_no": _new_goods_no(),
            "name": name,
            "category_id": category_id,
            "price": "12.90",
            "origin_price": "19.90",
            "stock": 20,
            "total_stock": 20,
            "sort": 99,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_spec(client: httpx.AsyncClient, goods_id: int, spec_name: str) -> int:
    """创建测试商品规格并返回主键"""
    resp = await client.post(
        "/api/v1/goods-spec",
        json={"goods_id": goods_id, "spec_name": spec_name, "price": "12.90", "sort": 1},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _db_row(pk: int) -> Cart | None:
    """直接读取真实库中的购物车记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(Cart).where(Cart.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_cart_crud_flow(app):
    """加购累加 + 数量/勾选 + 用户隔离集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0) 准备数据：两个用户 + 一个分类 + 两个商品 + 两个规格
        user_id = await _create_user(client, "购物车测试用户")
        other_user_id = await _create_user(client, "购物车测试用户2")
        headers = _auth_headers(user_id)
        other_headers = _auth_headers(other_user_id)

        resp = await client.post(
            "/api/v1/category",
            json={"code": _new_category_code(), "name": "购物车测试分类", "sort": 99},
        )
        assert resp.status_code == 201, resp.text
        category_id = resp.json()["data"]["id"]

        goods_id = await _create_goods(client, category_id, "购物车测试商品")
        other_goods_id = await _create_goods(client, category_id, "购物车测试商品2")
        spec_id = await _create_spec(client, goods_id, "微辣")
        other_spec_id = await _create_spec(client, other_goods_id, "大杯")

        # 0b) 未携带 token 应 401
        resp = await client.get("/api/v1/cart")
        assert resp.status_code == 401, resp.text

        # --- 请求体不含 user_id / spec_name：由登录态与规格表注入 ---
        payload = {"goods_id": goods_id, "goods_spec_id": spec_id, "qty": 1}

        # 1) 加购（首次）
        resp = await client.post("/api/v1/cart", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        pk = data["id"]
        assert data["user_id"] == user_id, "user_id 必须取登录态"
        assert data["spec_name"] == "微辣", "规格名称应为服务端快照"
        assert data["qty"] == 1 and data["selected"] is True

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 cart 表中找到记录"

        # 1b) 重复加购应累加数量且不新增条目
        resp = await client.post(
            "/api/v1/cart",
            json={**payload, "qty": 2},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["data"]["id"] == pk, "同规格加购不应新增条目"
        assert resp.json()["data"]["qty"] == 3

        # 1c) 不传规格（默认规格）：同样累加
        resp = await client.post("/api/v1/cart", json={"goods_id": goods_id}, headers=headers)
        assert resp.status_code == 201, resp.text
        default_pk = resp.json()["data"]["id"]
        assert resp.json()["data"]["spec_name"] == "默认"
        assert resp.json()["data"]["goods_spec_id"] is None

        resp = await client.post("/api/v1/cart", json={"goods_id": goods_id}, headers=headers)
        assert resp.status_code == 201, resp.text
        assert resp.json()["data"]["id"] == default_pk, "默认规格加购不应新增条目"
        assert resp.json()["data"]["qty"] == 2

        # 1d) 规格不属于该商品 -> 422
        resp = await client.post(
            "/api/v1/cart",
            json={"goods_id": goods_id, "goods_spec_id": other_spec_id},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 1e) 商品不存在 -> 404
        resp = await client.post(
            "/api/v1/cart",
            json={"goods_id": 9_000_000_001},
            headers=headers,
        )
        assert resp.status_code == 404, resp.text

        # 2) 列表（含勾选过滤）
        resp = await client.get(
            "/api/v1/cart",
            params={"page": 1, "page_size": 10, "selected": True},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 2

        # 3) 详情
        resp = await client.get(f"/api/v1/cart/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 4) 修改数量
        resp = await client.put(f"/api/v1/cart/{pk}", json={"qty": 5}, headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["qty"] == 5

        # 4b) 数量非法 / 携带 selected 均应被 Schema 拒绝
        resp = await client.put(f"/api/v1/cart/{pk}", json={"qty": 0}, headers=headers)
        assert resp.status_code == 422, resp.text
        resp = await client.put(
            f"/api/v1/cart/{pk}",
            json={"qty": 2, "selected": False},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 5) 专用勾选接口（取消勾选 -> 勾选）
        resp = await client.patch(
            f"/api/v1/cart/{pk}/selected",
            json={"selected": False},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["selected"] is False

        resp = await client.patch(
            f"/api/v1/cart/{pk}/selected",
            json={"selected": True},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["selected"] is True

        # 6) 用户隔离：他人不可读、不可改、不可勾选、不可删，列表为空
        resp = await client.get(f"/api/v1/cart/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.put(f"/api/v1/cart/{pk}", json={"qty": 1}, headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.patch(
            f"/api/v1/cart/{pk}/selected",
            json={"selected": False},
            headers=other_headers,
        )
        assert resp.status_code == 404, resp.text

        resp = await client.delete(f"/api/v1/cart/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.get("/api/v1/cart", headers=other_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 0, "他人列表不应包含我的购物车条目"

        # 7) 删除条目（物理删除）
        resp = await client.delete(f"/api/v1/cart/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/cart/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        assert await _db_row(pk) is None, "本表无软删字段，删除后记录应从库中消失"

        # 清理：默认规格条目 + 规格 + 商品 + 分类 + 用户
        resp = await client.delete(f"/api/v1/cart/{default_pk}", headers=headers)
        assert resp.status_code == 200, resp.text
        for sid in (spec_id, other_spec_id):
            resp = await client.delete(f"/api/v1/goods-spec/{sid}")
            assert resp.status_code == 200, resp.text
        for gid in (goods_id, other_goods_id):
            resp = await client.delete(f"/api/v1/goods/{gid}")
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
async def test_cart_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试（如购物车合计金额、清空购物车、批量勾选）

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/cart/...", json={...}, headers={...})
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
