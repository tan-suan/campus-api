"""
订单表接口集成测试（直连真实 MySQL）

路径：/api/v1/order
说明：
- 主键字段：id（类型 int）
- user_id 不由请求体传入，而是取当前登录用户（JWT 的 sub），因此本用例先创建测试用户并签发 token。
- 金额全部由服务端计算：goods_total = Σ 明细小计；freight = 自提 0 / 送寝 2.00；
  discount = 优惠券抵扣（不超过商品金额）；pay_amount = goods_total + freight - discount。
- 取货码仅自提订单生成（A-xxxx），送寝订单为空串。
- 状态机：pending → picking / canceled；picking → done / canceled；done、canceled 为终态（非法流转 409）。
- 状态走 PATCH /{id}/status；取消 / 确认完成走 POST /{id}/cancel、POST /{id}/complete。
- DELETE 为软删除（is_deleted=True/1），记录仍留在表中，详情应 404。

【覆盖策略】文件已存在则 skill 跳过（人手维护）。
"""

import uuid
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from core import database
from models.order import Order
from utils.auth import jwt_authenticator


def _new_openid() -> str:
    """生成测试用唯一 openid，避免多次运行冲突"""
    return f"skill_order_{uuid.uuid4().hex[:12]}"[:64]


def _new_goods_no() -> str:
    """生成测试用唯一商品编号"""
    return f"skill_order_no_{uuid.uuid4().hex[:8]}"[:32]


def _new_category_code() -> str:
    """生成测试用唯一分类标识"""
    return f"skill_order_c_{uuid.uuid4().hex[:8]}"[:32]


def _new_coupon_code() -> str:
    """生成测试用唯一优惠券编码"""
    return f"skill_order_cp_{uuid.uuid4().hex[:8]}"[:32]


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


async def _create_goods(client: httpx.AsyncClient, category_id: int) -> int:
    """创建测试商品（闪购价 12.90 / 原价 19.90），返回主键"""
    resp = await client.post(
        "/api/v1/goods",
        json={
            "goods_no": _new_goods_no(),
            "name": "订单测试商品",
            "category_id": category_id,
            "price": "12.90",
            "origin_price": "19.90",
            "stock": 100,
            "total_stock": 100,
            "emoji": "☕",
            "tint": "#F3E9DC",
            "sort": 99,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_spec(client: httpx.AsyncClient, goods_id: int) -> int:
    """创建商品规格（大杯 15.50），返回主键"""
    resp = await client.post(
        "/api/v1/goods-spec",
        json={
            "goods_id": goods_id,
            "spec_name": "大杯",
            "price": "15.50",
            "origin_price": "19.90",
            "stock": 50,
            "sort": 1,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_pickup_point(client: httpx.AsyncClient) -> tuple[int, str]:
    """创建自提点，返回 (主键, 名称)"""
    name = f"订单测试驿站_{uuid.uuid4().hex[:6]}"
    resp = await client.post(
        "/api/v1/pickup-point",
        json={
            "name": name,
            "business_hours": "08:00 - 21:00",
            "distance_desc": "步行 3 分钟",
            "address": "东校区梅园 1 号楼一层",
            "contact_phone": "13800138000",
            "sort": 99,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"], name


async def _create_address(client: httpx.AsyncClient, headers: dict) -> int:
    """创建收货地址（需登录态），返回主键"""
    resp = await client.post(
        "/api/v1/address",
        json={
            "receiver_name": "订单测试收件人",
            "phone": "13800138000",
            "campus": "东校区",
            "building": "梅园 7 号楼",
            "detail": "305 室",
            "is_default": True,
            "status": 1,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _create_coupon(client: httpx.AsyncClient, threshold: str, amount: str) -> int:
    """创建优惠券（满 threshold 减 amount），返回主键"""
    resp = await client.post(
        "/api/v1/coupon",
        json={
            "code": _new_coupon_code(),
            "name": f"订单测试券 满{threshold}减{amount}",
            "threshold": threshold,
            "amount": amount,
            "scope": "全场通用",
            "total": 100,
            "received": 0,
            "status": 1,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


async def _db_row(pk: int) -> Order | None:
    """直接读取真实库中的订单记录"""
    async with database.AsyncSessionLocal() as s:
        return (
            await s.execute(select(Order).where(Order.id == pk))
        ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_order_crud_flow(app):
    """下单金额 + 状态机 + 取消/完成 + 用户隔离集成测试（真实 MySQL）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0) 准备数据：两个用户、分类、商品、规格、自提点、地址、优惠券
        user_id = await _create_user(client, "订单测试用户")
        other_user_id = await _create_user(client, "订单测试用户2")
        headers = _auth_headers(user_id)
        other_headers = _auth_headers(other_user_id)

        resp = await client.post(
            "/api/v1/category",
            json={"code": _new_category_code(), "name": "订单测试分类", "sort": 99},
        )
        assert resp.status_code == 201, resp.text
        category_id = resp.json()["data"]["id"]

        goods_id = await _create_goods(client, category_id)
        spec_id = await _create_spec(client, goods_id)
        point_id, point_name = await _create_pickup_point(client)
        address_id = await _create_address(client, headers)
        coupon_id = await _create_coupon(client, "20.00", "3.00")

        # 0b) 未携带 token 应 401
        resp = await client.get("/api/v1/order")
        assert resp.status_code == 401, resp.text

        # 1) 自提下单：规格价 15.50 × 2 = 31.00，免配送费
        resp = await client.post(
            "/api/v1/order",
            json={
                "mode": "pickup",
                "pickup_point_id": point_id,
                "expect_time": "尽快送达",
                "remark": "少冰",
                "items": [{"goods_id": goods_id, "goods_spec_id": spec_id, "qty": 2}],
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        order = resp.json()["data"]
        pk = order["id"]

        assert order["user_id"] == user_id, "user_id 必须取登录态"
        assert order["status"] == "pending"
        assert order["mode"] == "pickup"
        assert _amount(order["goods_total"]) == Decimal("31.00")
        assert _amount(order["freight"]) == Decimal("0.00")
        assert _amount(order["discount"]) == Decimal("0.00")
        assert _amount(order["pay_amount"]) == Decimal("31.00")
        assert order["goods_count"] == 2
        assert order["pickup_point_name"] == point_name, "自提点名称应为快照"
        assert order["pickup_code"].startswith("A-"), "自提订单应生成取货码"
        assert len(order["items"]) == 1

        item = order["items"][0]
        assert item["goods_name"] == "订单测试商品"
        assert item["spec_name"] == "大杯"
        assert item["emoji"] == "☕"
        assert _amount(item["price"]) == Decimal("15.50")
        assert _amount(item["subtotal"]) == Decimal("31.00")

        row = await _db_row(pk)
        assert row is not None, "下单后未在真实 order 表中找到记录"
        assert row.is_deleted in (False, 0)

        # 2) 未达优惠券门槛（12.90 < 20.00）应 422
        resp = await client.post(
            "/api/v1/order",
            json={
                "mode": "pickup",
                "pickup_point_id": point_id,
                "coupon_id": coupon_id,
                "items": [{"goods_id": goods_id, "qty": 1}],
            },
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 3) 送寝下单 + 优惠券：12.90 × 2 = 25.80，配送费 2.00，优惠 3.00 → 24.80
        resp = await client.post(
            "/api/v1/order",
            json={
                "mode": "dorm",
                "address_id": address_id,
                "coupon_id": coupon_id,
                "expect_time": "12:00 前送达",
                "items": [{"goods_id": goods_id, "qty": 2}],
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        dorm = resp.json()["data"]
        dorm_pk = dorm["id"]
        assert dorm["mode"] == "dorm"
        assert _amount(dorm["goods_total"]) == Decimal("25.80")
        assert _amount(dorm["freight"]) == Decimal("2.00")
        assert _amount(dorm["discount"]) == Decimal("3.00")
        assert _amount(dorm["pay_amount"]) == Decimal("24.80")
        assert dorm["pickup_code"] == "", "送寝订单不生成取货码"
        assert "订单测试收件人" in dorm["address_text"], "收货地址应为快照"

        # 3b) 缺少自提点 / 缺少收货地址应 422
        resp = await client.post(
            "/api/v1/order",
            json={"mode": "pickup", "items": [{"goods_id": goods_id, "qty": 1}]},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text
        resp = await client.post(
            "/api/v1/order",
            json={"mode": "dorm", "items": [{"goods_id": goods_id, "qty": 1}]},
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 3c) 商品不存在应 404；他人地址应 404（地址按用户隔离）
        resp = await client.post(
            "/api/v1/order",
            json={
                "mode": "pickup",
                "pickup_point_id": point_id,
                "items": [{"goods_id": 9_000_000_001, "qty": 1}],
            },
            headers=headers,
        )
        assert resp.status_code == 404, resp.text

        # 3d) 请求体携带服务端字段应被拒绝
        resp = await client.post(
            "/api/v1/order",
            json={
                "mode": "pickup",
                "pickup_point_id": point_id,
                "pay_amount": "0.01",
                "items": [{"goods_id": goods_id, "qty": 1}],
            },
            headers=headers,
        )
        assert resp.status_code == 422, resp.text

        # 4) 列表（状态过滤 + 订单号检索）
        resp = await client.get(
            "/api/v1/order", params={"status": "pending"}, headers=headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] >= 2

        resp = await client.get(
            "/api/v1/order", params={"keyword": order["order_no"]}, headers=headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 1

        # 5) 详情
        resp = await client.get(f"/api/v1/order/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text
        assert len(resp.json()["data"]["items"]) == 1

        # 6) 更新备注（状态字段不可走 PUT）
        resp = await client.put(
            f"/api/v1/order/{pk}", json={"remark": "放宿舍门口"}, headers=headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["remark"] == "放宿舍门口"

        resp = await client.put(f"/api/v1/order/{pk}", json={"status": "picking"}, headers=headers)
        assert resp.status_code == 422, resp.text

        # 7) 状态机：pending → picking 记录支付时间；picking → pending 非法
        resp = await client.patch(
            f"/api/v1/order/{pk}/status", json={"status": "picking"}, headers=headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == "picking"
        assert resp.json()["data"]["pay_time"] is not None

        resp = await client.patch(
            f"/api/v1/order/{pk}/status", json={"status": "pending"}, headers=headers
        )
        assert resp.status_code == 409, resp.text

        # 7b) 非法状态值应 422（Schema 枚举校验）
        resp = await client.patch(
            f"/api/v1/order/{pk}/status", json={"status": "unknown"}, headers=headers
        )
        assert resp.status_code == 422, resp.text

        # 7c) 确认完成：picking → done 记录完成时间；终态不可再变更
        resp = await client.post(f"/api/v1/order/{pk}/complete", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == "done"
        assert resp.json()["data"]["done_time"] is not None

        resp = await client.patch(
            f"/api/v1/order/{pk}/status", json={"status": "canceled"}, headers=headers
        )
        assert resp.status_code == 409, resp.text
        resp = await client.post(f"/api/v1/order/{pk}/cancel", headers=headers)
        assert resp.status_code == 409, resp.text

        # 8) 取消另一单：记录取消时间；重复取消 409
        resp = await client.post(f"/api/v1/order/{dorm_pk}/cancel", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == "canceled"
        assert resp.json()["data"]["cancel_time"] is not None

        resp = await client.post(f"/api/v1/order/{dorm_pk}/cancel", headers=headers)
        assert resp.status_code == 409, resp.text

        # 9) 用户隔离：他人不可读、不可改、不可操作状态、不可删，列表为空
        resp = await client.get(f"/api/v1/order/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.put(
            f"/api/v1/order/{pk}", json={"remark": "越权修改"}, headers=other_headers
        )
        assert resp.status_code == 404, resp.text

        resp = await client.patch(
            f"/api/v1/order/{pk}/status", json={"status": "canceled"}, headers=other_headers
        )
        assert resp.status_code == 404, resp.text

        resp = await client.post(f"/api/v1/order/{pk}/cancel", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.delete(f"/api/v1/order/{pk}", headers=other_headers)
        assert resp.status_code == 404, resp.text

        resp = await client.get("/api/v1/order", headers=other_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["meta"]["total"] == 0, "他人列表不应包含我的订单"

        # 10) 删除（软删除）
        resp = await client.delete(f"/api/v1/order/{pk}", headers=headers)
        assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/order/{pk}", headers=headers)
        assert resp.status_code == 404, resp.text

        row = await _db_row(pk)
        assert row is not None, "软删除后记录应仍留在 order 表中"
        assert row.is_deleted in (True, 1)

        # 清理：另一单、地址、优惠券、规格、商品、自提点、分类、用户
        resp = await client.delete(f"/api/v1/order/{dorm_pk}", headers=headers)
        assert resp.status_code == 200, resp.text
        for path in (
            f"/api/v1/address/{address_id}",
            f"/api/v1/coupon/{coupon_id}",
            f"/api/v1/goods-spec/{spec_id}",
            f"/api/v1/goods/{goods_id}",
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
@pytest.mark.skip(reason="占位：补齐商业逻辑接口测试后移除 skip")
async def test_order_business_api_placeholder(app):
    """
    占位：商业逻辑接口集成测试（如支付回调、超时自动取消、订单统计）

    在 Service/Resource 增加非基础 CRUD 业务接口后，在此补充真实请求断言。
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # resp = await client.post("/api/v1/order/...", json={...}, headers={...})
        # assert resp.status_code == 200, resp.text
        assert False, "请实现商业逻辑接口集成测试"
