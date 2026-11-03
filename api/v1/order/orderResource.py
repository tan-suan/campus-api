"""
订单表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 【本表启用登录鉴权】订单按当前登录用户隔离：user_id 从 JWT 主体取，
  不接受前端传入，避免越权读写他人订单。
- 字段校验由 Schema 在进入端点前完成；金额、取货码、订单号、快照均由 Service 生成。
- 状态字段通过 PATCH /{id}/status 专用修改（Service 内做状态机校验）；
  取消与确认完成提供专用动作接口 POST /{id}/cancel、POST /{id}/complete。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from core.permissions import CurrentUser, get_current_active_user
from models.order import OrderMode, OrderStatus
from schemas.order import (
    OrderCreate,
    OrderDetailResponse,
    OrderResponse,
    OrderStatusUpdate,
    OrderUpdate,
)
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.dependencies import get_order_service
from service.order_service import OrderService
from utils.custom_exceptions import AuthenticationException, handle_service_exceptions

router = APIRouter(prefix="/order", tags=["订单管理"])


def _current_user_id(current_user: CurrentUser) -> int:
    """把无状态 JWT 主体中的用户ID转为整型（与 user.id 对齐）"""
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("令牌中的用户信息无效") from exc


@router.get(
    "",
    response_model=PaginationResponse[OrderResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取我的订单列表",
)
@handle_service_exceptions
async def get_order_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: OrderStatus | None = Query(None, description="订单状态"),
    mode: OrderMode | None = Query(None, description="取货方式：pickup自提 dorm送寝"),
    keyword: str | None = Query(None, max_length=32, description="订单号关键字"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """获取当前登录用户的订单分页列表（最新下单优先）"""
    result = await service.get_list(
        user_id=_current_user_id(current_user),
        page=page,
        size=page_size,
        filters={"status": status, "mode": mode, "keyword": keyword},
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[OrderDetailResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取订单详情",
)
@handle_service_exceptions
async def get_order_detail(
    id: int = Path(..., description="订单ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """获取订单详情（仅限本人订单，含商品明细快照）"""
    result = await service.get_detail(id, _current_user_id(current_user))
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[OrderDetailResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="下单",
)
@handle_service_exceptions
async def create_order(
    data: OrderCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """
    下单（归属当前登录用户）

    服务端计算：明细小计、goods_total、freight、discount、pay_amount，
    并生成订单号与取货码（仅自提），明细保存商品快照。
    """
    result = await service.create(_current_user_id(current_user), data)
    return success_response(result, message="下单成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[OrderDetailResponse],
    summary="更新订单备注 / 期望时间 / 支付方式",
)
@handle_service_exceptions
async def update_order(
    id: int = Path(..., description="订单ID"),
    data: OrderUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """
    更新订单非金额字段（仅限本人订单，且仅待付款 / 待取货状态）

    明细、取货方式与金额在下单时冻结；状态字段请用 PATCH /order/{id}/status。
    """
    result = await service.update(id, _current_user_id(current_user), data)
    return success_response(result, message="订单更新成功")


@router.patch(
    "/{id}/status",
    response_model=SuccessResponse[OrderDetailResponse],
    summary="修改订单状态",
)
@handle_service_exceptions
async def update_order_status(
    id: int = Path(..., description="订单ID"),
    data: OrderStatusUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """
    专用状态变更（pending / picking / done / canceled），仅限本人订单

    合法流转：pending → picking / canceled；picking → done / canceled；
    done、canceled 为终态。进入 picking 记录支付时间，done 记录完成时间，canceled 记录取消时间。
    """
    result = await service.update_status(id, _current_user_id(current_user), data)
    return success_response(result, message="订单状态更新成功")


@router.post(
    "/{id}/cancel",
    response_model=SuccessResponse[OrderDetailResponse],
    summary="取消订单",
)
@handle_service_exceptions
async def cancel_order(
    id: int = Path(..., description="订单ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """取消订单（仅限本人订单；待付款 / 待取货可取消，记录取消时间）"""
    result = await service.cancel(id, _current_user_id(current_user))
    return success_response(result, message="订单已取消")


@router.post(
    "/{id}/complete",
    response_model=SuccessResponse[OrderDetailResponse],
    summary="确认订单完成",
)
@handle_service_exceptions
async def complete_order(
    id: int = Path(..., description="订单ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """确认订单完成（仅限本人订单；仅待取货可确认，记录完成时间）"""
    result = await service.confirm_done(id, _current_user_id(current_user))
    return success_response(result, message="订单已完成")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除订单",
)
@handle_service_exceptions
async def delete_order(
    id: int = Path(..., description="订单ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderService = Depends(get_order_service),
):
    """删除订单（仅限本人订单；软删除，明细保留历史记录）"""
    await service.delete(id, _current_user_id(current_user))
    return success_response(None, message="订单删除成功")
