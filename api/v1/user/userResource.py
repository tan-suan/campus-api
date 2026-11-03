"""
用户表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 默认不启用鉴权（接口开箱即用、无需登录）；如需登录鉴权，见文件底部「鉴权启用」注释。
- 字段校验由 Schema 在进入端点前完成。
- 状态/标识位字段通过 PATCH /{id}/status 专用修改。
"""

from fastapi import APIRouter, Depends, Path, Query, status

from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from schemas.user import (
    UserCreate,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from service.dependencies import get_user_service
from service.user_service import UserService
from utils.custom_exceptions import handle_service_exceptions

router = APIRouter(prefix="/user", tags=["用户管理"])

# ===== 鉴权（默认关闭，接口开箱即用）=====
# 本脚手架生成的 CRUD 接口默认不需要登录。若项目需要登录鉴权，可统一在 router
# 上挂载依赖（推荐），或在单个路由上添加该 Depends：
#   from core.permissions import get_current_active_user
#   router = APIRouter(
#       prefix="/user",
#       tags=["用户管理"],
#       dependencies=[Depends(get_current_active_user)],
#   )


@router.get(
    "",
    response_model=PaginationResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="获取用户列表",
)
@handle_service_exceptions
async def get_user_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: UserService = Depends(get_user_service),
):
    """获取用户分页列表"""
    result = await service.get_list(page=page, size=page_size)
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="获取用户详情",
)
@handle_service_exceptions
async def get_user_detail(
    id: int = Path(..., description="用户ID"),
    service: UserService = Depends(get_user_service),
):
    """获取用户详情"""
    result = await service.get_detail(id)
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
)
@handle_service_exceptions
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """创建用户"""
    result = await service.create(data)
    return success_response(result, message="用户创建成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[UserResponse],
    summary="更新用户",
)
@handle_service_exceptions
async def update_user(
    id: int = Path(..., description="用户ID"),
    data: UserUpdate = ...,
    service: UserService = Depends(get_user_service),
):
    """更新用户（不含状态/标识位字段）"""
    result = await service.update(id, data)
    return success_response(result, message="用户更新成功")


@router.patch(
    "/{id}/status",
    response_model=SuccessResponse[UserResponse],
    summary="修改用户状态",
)
@handle_service_exceptions
async def update_user_status(
    id: int = Path(..., description="用户ID"),
    data: UserStatusUpdate = ...,
    service: UserService = Depends(get_user_service),
):
    """
    专用修改用户状态（status：1正常 0禁用）
    """
    result = await service.update_status(id, data)
    return success_response(result, message="用户状态更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除用户",
)
@handle_service_exceptions
async def delete_user(
    id: int = Path(..., description="用户ID"),
    service: UserService = Depends(get_user_service),
):
    """删除用户（软删除）"""
    await service.delete(id)
    return success_response(None, message="用户删除成功")
