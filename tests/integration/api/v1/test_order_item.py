"""
订单明细表接口集成测试（直连真实 MySQL）

路径：/api/v1/order-item
说明：
- 主键字段：id（类型 int）
- 明细经 order_id 关联订单，按订单所属用户隔离（JWT 的 sub），因此本用例先建用户并签发 token。
- 商品名称/规格/成交价为下单快照，由服务端从商品表读取（前端传价格无效）；
  subtotal = 成交单价 × 数量，由服务端计算。
- 明细变更（增/改/删）后，所属订单 goods_total / goods_count / pay_amount 自动重算。
- 仅「待付款（pending）」订单可增减或修改明细，其他状态返回 409。
- DELETE 为软删除（is_deleted=True/1），记录仍留在表中，详情应 404。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.order_item import OrderItem
from utils.auth import jwt_authenticator


def _new_openid() -> str:
    """生成测试用唯一 openid，避免多次运行冲突"""
    return f"skill_oitem_{uuid.uuid4().hex[:12]}"[:64]


def _new_goods_no() -> str:
    """生成测试用唯一商品编号"""
    return f"skill_oitem_no_{uuid.uuid4().hex[:8]}"[:32]


def _new_category_code() -> str:
    """生成测试用唯一分类标识"""
    return f"skill_oitem_c_{uuid.uuid4().hex[:8]}"[:32]


def _amount(value) -> Decimal:
    """把响应中的金额（字符串/数字）统一转 Decimal，便于精确比较"""
    return Decimal(str(value))


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
    """创建测试商品（闪购价 12.90），返回主键"""
    resp = await client.post(
        "/api/v1/goods",
        json={
            "goods_no": _new_goods_no(),
            "name": name,
            "category_id": category_id,
            "price": "12.90",
            "origin_price": "19.90",
            "stock": 100,
            "total_stock": 100,
            "emoji": "🍜",
            "tint": "#FFF1E6",
            "sort": 99,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_spec(
    client: httpx.AsyncClient, goods_id: int, spec_name: str, price: str
) -> int:
    """创建商品规格，返回主键"""
    resp = await client.post(
        "/api/v1/goods-spec",
        json={
            "goods_id": goods_id,
            "spec_name": spec_name,
            "price": price,
            "origin_price": "19.90",
            "stock": 50,
            "sort": 1,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_pickup_point(client: httpx.AsyncClient) -> int:
    """创建自提点，返回主键"""
    resp = await client.post(
        "/api/v1/pickup-point",
        json={
            "name": f"明细测试驿站_{uuid.uuid4().hex[:6]}",
            "business_hours": "08:00 - 21:00",
            "address": "东校区梅园 1 号楼一层",
            "contact_phone": "13800138000",
            "sort": 99,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_order(
    client: httpx.AsyncClient,
    headers: dict,
    pickup_point_id: int,
    goods_id: int,
    spec_id: int,
) -> dict:
    """下自提单（1 件规格商品），返回订单详情"""
    resp = await client.post(
        "/api/v1/order",
        json={
            "mode": "pickup",
            "pickup_point_id": pickup_point_id,
            "items": [{"goods_id": goods_id, "goods_spec_id": spec_id, "qty": 1}],
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _db_row(pk: int) -> OrderItem | None:
    """直接读取真实库中的明细记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(OrderItem).where(OrderItem.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_order_item_crud_flow(app):
    """明细快照/小计 + 订单金额联动 + 用户隔离集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0) 准备数据：两个用户、分类、两个商品（含规格）、自提点
        user_id = await _create_user(client, "明细测试用户")
        other_user_id = await _create_user(client, "明细测试用户2")
        headers = _auth_headers(user_id)
        other_headers = _auth_headers(other_user_id)

        resp = await client.post(
            "/api/v1/category",
            json={"code": _new_category_code(), "name": "明细测试分类", "sort": 99},
        )
        assert resp.status_code == 201, resp.text
        category_id = resp.json()["data"]["id"]

        goods_id = await _create_goods(client, category_id, "明细测试商品")
        spec_id = await _create_spec(client, goods_id, "大碗", "15.50")
        other_goods_id = await _create_goods(client, category_id, "明细测试商品2")
        other_spec_id = await _create_spec(client, other_goods_id, "加辣", "16.50")
        point_id = await _create_pickup_point(client)

        order = await _create_order(client, headers, point_id, goods_id, spec_id)
        order_id = order["id"]
        assert _amount(order["goods_total"]) == Decimal("15.50")

        # 0b) 未携带 token 应 401
        resp = await client.get("/api/v1/order-item")
        assert resp.status_code == 401, resp.text

        # 1) 追加明细：规格价 15.50 × 2 = 31.00
        resp = await client.post(
            "/api/v1/order-item",
            json={"order_id": order_id, "goods_id": goods_id, "goods_spec_id": spec_id, "qty": 2},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        item = resp.json()["data"]
        pk = item["id"]
        assert item["order_id"] == order_id
        assert item["goods_name"] == "明细测试商品", "商品名称应为服务端快照"
        assert item["spec_name"] == "大碗", "规格名称应为服务端快照"
        assert item["emoji"] == "🍜"
        assert _amount(item["price"]) == Decimal("15.50"), "成交单价应取规格价"
        assert _amount(item["subtotal"]) == Decimal("31.00"), "小计应为单价 × 数量"

        row = await _db_row(pk)
        assert row is not None, "创建后未在真实 order_item 表中找到记录"
        assert row.is_deleted in (False, 0)

        # 1b) 订单金额与件数应自动联动：15.50 + 31.00 = 46.50，共 3 件
        resp = await client.get(f"/api/v1/order/{order_id}", headers=headers)
        assert resp.status_code == 200, resp.text
        refreshed = resp.json()["data"]
        assert _amount(refreshed["goods_total"]) == Decimal("46.50")
        assert _amount(refreshed["pay_amount"]) == Decimal("46.50")
        assert refreshed["goods_count"] == 3
        assert len(refreshed["items"]) == 2

        # 1c) 请求体携带快照/金额字段应被拒绝
        resp = await client.post(
            "/api/v1/order-item",
            json={
                "order_id": order_id,
                "goods_id": goods_id,
                "qty": 1,
                "price": "0.01",
            },
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 1d) 规格不属于该商品应 422；商品不存在应 404；订单不存在应 404
        resp = await client.post(
            "/api/v1/order-item",
            json={"order_id": order_id, "goods_id": goods_id, "goods_spec_id": other_spec_id},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text
        resp = await client.post(
            "/api/v1/order-item",
            json={"order_id": order_id, "goods_id": 9_000_000_001, "qty": 1},
            headers=headers,
        )
        assert resp.status_code == 404, resp.text
        resp = await client.post(
            "/api/v1/order-item",
            json={"order_id": 9_000_000_001, "goods_id": goods_id, "qty": 1},
            headers=headers,
        )
        assert resp.status_code == 404, resp.text

        # 2) 列表（按所属订单过滤）
        resp = await client.get(
            "/api/v1/order-item", params={"order_id": order_id}, headers=headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 2

        # 3) 详情
        resp = await client.get(f"/api/v1/order-item/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        # 4) 修改数量：15.50 × 1 = 15.50；订单商品金额回到 31.00、共 2 件
        resp = await client.put(f"/api/v1/order-item/{pk}", json={"qty": 1}, headers=headers)
        assert resp.status_code == 200, resp.text
        assert _amount(resp.json()["data"]["subtotal"]) == Decimal("15.50")

        resp = await client.get(f"/api/v1/order/{order_id}", headers=headers)
        assert _amount(resp.json()["data"]["goods_total"]) == Decimal("31.00")
        assert resp.json()["data"]["goods_count"] == 2

        # 4b) 数量越界 / 携带其他字段应 422
        resp = await client.put(f"/api/v1/order-item/{pk}", json={"qty": 0}, headers=headers)
        assert resp.status_code == 422, resp.text
        resp = await client.put(
            f"/api/v1/order-item/{pk}", json={"qty": 1, "price": "0.01"}, headers=headers
        )
        assert resp.status_code == 422, resp.text

        # 5) 用户隔离：他人不可读、不可改、不可删，列表为空
        resp = await client.get(f"/api/v1/order-item/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.put(f"/api/v1/order-item/{pk}", json={"qty": 1}, headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.delete(f"/api/v1/order-item/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.get(
            "/api/v1/order-item", params={"order_id": order_id}, headers=other_headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 0, "他人列表不应包含我的明细"

        # 6) 删除明细（软删除）并联动订单金额：只剩 1 件 15.50
        resp = await client.delete(f"/api/v1/order-item/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/order-item/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        assert row is not None, "软删除后记录应仍留在 order_item 表中"
        assert row.is_deleted in (True, 1)

        resp = await client.get(f"/api/v1/order/{order_id}", headers=headers)
        assert _amount(resp.json()["data"]["goods_total"]) == Decimal("15.50")
        assert resp.json()["data"]["goods_count"] == 1

        # 7) 非待付款订单不可增减明细（409）
        resp = await client.patch(
            f"/api/v1/order/{order_id}/status", json={"status": "picking"}, headers=headers
        )
        assert resp.status_code == 200, resp.text

        resp = await client.post(
            "/api/v1/order-item",
            json={"order_id": order_id, "goods_id": goods_id, "qty": 1},
            headers=headers,
        )
        assert resp.status_code == 409, resp.text

        resp = await client.delete(f"/api/v1/order-item/{order['items'][0]['id']}", headers=headers)
        assert resp.status_code == 409, resp.text

        # 清理：订单、规格、商品、自提点、分类、用户
        for path in (
            f"/api/v1/order/{order_id}",
            f"/api/v1/goods-spec/{spec_id}",
            f"/api/v1/goods-spec/{other_spec_id}",
            f"/api/v1/goods/{goods_id}",
            f"/api/v1/goods/{other_goods_id}",
            f"/api/v1/pickup-point/{point_id}",
            f"/api/v1/category/{category_id}",
            f"/api/v1/user/{user_id}",
            f"/api/v1/user/{other_user_id}",
        ):
            resp = await client.delete(path, headers=headers)
            assert resp.status_code == 200, f"{path} -> {resp.text}"


# ===========================================================================
# 商业逻辑接口测试占位（后续业务 API 在此补充；默认 skip）
# ===========================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="占位：补齐商业逻辑接口集成测试后移除 skip")
async def test_order_item_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试（如批量替换明细、明细拆单）

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/order-item/...", json={...}, headers={...})
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
