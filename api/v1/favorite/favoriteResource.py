"""
商品收藏表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 【本表启用登录鉴权】收藏按当前登录用户隔离：user_id 从 JWT 主体取，
  不接受前端传入；同一用户对同一商品仅能收藏一次（重复收藏返回 409）。
- 字段校验由 Schema 在进入端点前完成。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from core.permissions import CurrentUser, get_current_active_user
from schemas.favorite import FavoriteCreate, FavoriteResponse, FavoriteUpdate
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.dependencies import get_favorite_service
from service.favorite_service import FavoriteService
from utils.custom_exceptions import AuthenticationException, handle_service_exceptions

router = APIRouter(prefix="/favorite", tags=["商品收藏"])


def _current_user_id(current_user: CurrentUser) -> int:
    """把无状态 JWT 主体中的用户ID转为整型（与 user.id 对齐）"""
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("令牌中的用户信息无效") from exc


@router.get(
    "",
    response_model=PaginationResponse[FavoriteResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取我的收藏列表",
)
@handle_service_exceptions
async def get_favorite_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    goods_id: int | None = Query(None, description="商品ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: FavoriteService = Depends(get_favorite_service),
):
    """获取当前登录用户的收藏分页列表（最新收藏优先）"""
    result = await service.get_list(
        user_id=_current_user_id(current_user),
        page=page,
        size=page_size,
        filters={"goods_id": goods_id},
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[FavoriteResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取收藏详情",
)
@handle_service_exceptions
async def get_favorite_detail(
    id: int = Path(..., description="收藏ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: FavoriteService = Depends(get_favorite_service),
):
    """获取收藏详情（仅限本人收藏）"""
    result = await service.get_detail(id, _current_user_id(current_user))
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[FavoriteResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="收藏商品",
)
@handle_service_exceptions
async def create_favorite(
    data: FavoriteCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: FavoriteService = Depends(get_favorite_service),
):
    """收藏商品（归属当前登录用户；重复收藏返回 409）"""
    result = await service.create(_current_user_id(current_user), data)
    return success_response(result, message="收藏成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[FavoriteResponse],
    summary="更换收藏的商品",
)
@handle_service_exceptions
async def update_favorite(
    id: int = Path(..., description="收藏ID"),
    data: FavoriteUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: FavoriteService = Depends(get_favorite_service),
):
    """更换收藏的商品（仅限本人收藏，仍需满足同一商品唯一）"""
    result = await service.update(id, _current_user_id(current_user), data)
    return success_response(result, message="收藏更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="取消收藏",
)
@handle_service_exceptions
async def delete_favorite(
    id: int = Path(..., description="收藏ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: FavoriteService = Depends(get_favorite_service),
):
    """取消收藏（仅限本人收藏；本表无软删字段，直接物理删除）"""
    await service.delete(id, _current_user_id(current_user))
    return success_response(None, message="取消收藏成功")
