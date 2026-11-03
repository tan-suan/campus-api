"""
购物车表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 【本表启用登录鉴权】购物车按当前登录用户隔离：user_id 从 JWT 主体取，
  不接受前端传入，避免越权读写他人购物车。
- 字段校验由 Schema 在进入端点前完成。
- 加购累加、数量修改、勾选切换、删除条目等业务逻辑均在 Service 实现。
- 勾选标识位（selected）通过 PATCH /{id}/selected 专用修改。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from core.permissions import CurrentUser, get_current_active_user
from schemas.cart import (
    CartCreate,
    CartResponse,
    CartSelectedUpdate,
    CartUpdate,
)
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.cart_service import CartService
from service.dependencies import get_cart_service
from utils.custom_exceptions import AuthenticationException, handle_service_exceptions

router = APIRouter(prefix="/cart", tags=["购物车管理"])


def _current_user_id(current_user: CurrentUser) -> int:
    """把无状态 JWT 主体中的用户ID转为整型（与 user.id 对齐）"""
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("令牌中的用户信息无效") from exc


@router.get(
    "",
    response_model=PaginationResponse[CartResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取我的购物车列表",
)
@handle_service_exceptions
async def get_cart_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    selected: bool | None = Query(None, description="是否只看已勾选结算的条目"),
    goods_id: int | None = Query(None, description="商品ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: CartService = Depends(get_cart_service),
):
    """获取当前登录用户的购物车分页列表（最近更新优先）"""
    result = await service.get_list(
        user_id=_current_user_id(current_user),
        page=page,
        size=page_size,
        filters={"selected": selected, "goods_id": goods_id},
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[CartResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取购物车条目详情",
)
@handle_service_exceptions
async def get_cart_detail(
    id: int = Path(..., description="购物车条目ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: CartService = Depends(get_cart_service),
):
    """获取购物车条目详情（仅限本人购物车）"""
    result = await service.get_detail(id, _current_user_id(current_user))
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[CartResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="加入购物车",
)
@handle_service_exceptions
async def create_cart(
    data: CartCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: CartService = Depends(get_cart_service),
):
    """
    加入购物车（归属当前登录用户）

    同一「用户 + 商品 + 规格」重复加购时累加数量（不新增条目），并自动勾选结算。
    """
    result = await service.create(_current_user_id(current_user), data)
    return success_response(result, message="已加入购物车")


@router.put(
    "/{id}",
    response_model=SuccessResponse[CartResponse],
    summary="修改购物车数量",
)
@handle_service_exceptions
async def update_cart(
    id: int = Path(..., description="购物车条目ID"),
    data: CartUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: CartService = Depends(get_cart_service),
):
    """修改购买数量（仅限本人购物车；勾选请用 PATCH /cart/{id}/selected）"""
    result = await service.update(id, _current_user_id(current_user), data)
    return success_response(result, message="购物车数量更新成功")


@router.patch(
    "/{id}/selected",
    response_model=SuccessResponse[CartResponse],
    summary="勾选 / 取消勾选购物车条目",
)
@handle_service_exceptions
async def update_cart_selected(
    id: int = Path(..., description="购物车条目ID"),
    data: CartSelectedUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: CartService = Depends(get_cart_service),
):
    """
    专用修改勾选标识位（selected：0否 1是），仅限本人购物车
    """
    result = await service.update_selected(id, _current_user_id(current_user), data)
    return success_response(result, message="购物车勾选状态更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除购物车条目",
)
@handle_service_exceptions
async def delete_cart(
    id: int = Path(..., description="购物车条目ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: CartService = Depends(get_cart_service),
):
    """删除购物车条目（仅限本人购物车；本表无软删字段，直接物理删除）"""
    await service.delete(id, _current_user_id(current_user))
    return success_response(None, message="购物车条目删除成功")
