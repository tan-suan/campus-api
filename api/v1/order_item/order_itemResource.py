"""
订单明细表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 【本表启用登录鉴权】明细经 order_id 关联订单，按订单归属用户隔离（Service 内校验）。
- 商品快照、成交价与小计由 Service 从商品/规格表解析并计算，不接受前端传入。
- 明细无状态字段；删除为软删除，并联动刷新所属订单金额与件数。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from core.permissions import CurrentUser, get_current_active_user
from schemas.order_item import OrderItemCreate, OrderItemResponse, OrderItemUpdate
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.dependencies import get_order_item_service
from service.order_item_service import OrderItemService
from utils.custom_exceptions import AuthenticationException, handle_service_exceptions

router = APIRouter(prefix="/order-item", tags=["订单明细管理"])


def _current_user_id(current_user: CurrentUser) -> int:
    """把无状态 JWT 主体中的用户ID转为整型（与 user.id 对齐）"""
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("令牌中的用户信息无效") from exc


@router.get(
    "",
    response_model=PaginationResponse[OrderItemResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取我的订单明细列表",
)
@handle_service_exceptions
async def get_order_item_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    order_id: int | None = Query(None, description="所属订单ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderItemService = Depends(get_order_item_service),
):
    """获取当前登录用户订单下的明细分页列表（最新明细优先）"""
    result = await service.get_list(
        user_id=_current_user_id(current_user),
        page=page,
        size=page_size,
        filters={"order_id": order_id},
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[OrderItemResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取订单明细详情",
)
@handle_service_exceptions
async def get_order_item_detail(
    id: int = Path(..., description="明细ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderItemService = Depends(get_order_item_service),
):
    """获取订单明细详情（仅限本人订单下的明细）"""
    result = await service.get_detail(id, _current_user_id(current_user))
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[OrderItemResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="向订单追加明细",
)
@handle_service_exceptions
async def create_order_item(
    data: OrderItemCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderItemService = Depends(get_order_item_service),
):
    """
    追加明细（仅待付款订单）

    服务端读取商品/规格快照与成交价，计算小计并联动刷新订单金额与件数。
    """
    result = await service.create(_current_user_id(current_user), data)
    return success_response(result, message="订单明细添加成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[OrderItemResponse],
    summary="修改明细数量",
)
@handle_service_exceptions
async def update_order_item(
    id: int = Path(..., description="明细ID"),
    data: OrderItemUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderItemService = Depends(get_order_item_service),
):
    """修改购买数量（按冻结的成交单价重算小计，并联动订单金额）"""
    result = await service.update(id, _current_user_id(current_user), data)
    return success_response(result, message="订单明细更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除订单明细",
)
@handle_service_exceptions
async def delete_order_item(
    id: int = Path(..., description="明细ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: OrderItemService = Depends(get_order_item_service),
):
    """删除明细（软删除，并联动订单金额与件数）"""
    await service.delete(id, _current_user_id(current_user))
    return success_response(None, message="订单明细删除成功")
