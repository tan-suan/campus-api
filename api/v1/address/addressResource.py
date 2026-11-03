"""
收货地址表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 【本表启用登录鉴权】地址按当前登录用户隔离：user_id 从 JWT 主体取，
  不接受前端传入，避免越权读写他人地址。
- 字段校验由 Schema 在进入端点前完成。
- 状态字段通过 PATCH /{id}/status 专用修改。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from core.permissions import CurrentUser, get_current_active_user
from schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressStatusUpdate,
    AddressUpdate,
)
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.address_service import AddressService
from service.dependencies import get_address_service
from utils.custom_exceptions import AuthenticationException, handle_service_exceptions

router = APIRouter(prefix="/address", tags=["收货地址管理"])


def _current_user_id(current_user: CurrentUser) -> int:
    """把无状态 JWT 主体中的用户ID转为整型（与 user.id 对齐）"""
    try:
        return int(current_user.user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("令牌中的用户信息无效") from exc


@router.get(
    "",
    response_model=PaginationResponse[AddressResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取我的收货地址列表",
)
@handle_service_exceptions
async def get_address_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: int | None = Query(None, ge=0, le=1, description="状态：1有效 0停用"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
):
    """获取当前登录用户的收货地址分页列表（默认地址优先）"""
    result = await service.get_list(
        user_id=_current_user_id(current_user),
        page=page,
        size=page_size,
        filters={"status": status},
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[AddressResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取收货地址详情",
)
@handle_service_exceptions
async def get_address_detail(
    id: int = Path(..., description="地址ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
):
    """获取收货地址详情（仅限本人地址）"""
    result = await service.get_detail(id, _current_user_id(current_user))
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[AddressResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="创建收货地址",
)
@handle_service_exceptions
async def create_address(
    data: AddressCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
):
    """创建收货地址（归属当前登录用户；设为默认时自动取消其他默认地址）"""
    result = await service.create(_current_user_id(current_user), data)
    return success_response(result, message="收货地址创建成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[AddressResponse],
    summary="更新收货地址",
)
@handle_service_exceptions
async def update_address(
    id: int = Path(..., description="地址ID"),
    data: AddressUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
):
    """更新收货地址（仅限本人地址，不含状态字段）"""
    result = await service.update(id, _current_user_id(current_user), data)
    return success_response(result, message="收货地址更新成功")


@router.patch(
    "/{id}/status",
    response_model=SuccessResponse[AddressResponse],
    summary="修改收货地址状态",
)
@handle_service_exceptions
async def update_address_status(
    id: int = Path(..., description="地址ID"),
    data: AddressStatusUpdate = ...,
    current_user: CurrentUser = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
):
    """
    专用修改状态（status：1有效 0停用），仅限本人地址
    """
    result = await service.update_status(id, _current_user_id(current_user), data)
    return success_response(result, message="收货地址状态更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除收货地址",
)
@handle_service_exceptions
async def delete_address(
    id: int = Path(..., description="地址ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
):
    """删除收货地址（仅限本人地址，软删除）"""
    await service.delete(id, _current_user_id(current_user))
    return success_response(None, message="收货地址删除成功")
