"""
优惠券表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 本表为平台级配置数据（不属于某个用户），按脚手架默认不启用鉴权；
  如需限制为管理员维护，见文件底部「鉴权启用」注释。
- 字段校验由 Schema 在进入端点前完成。
- 状态字段通过 PATCH /{id}/status 专用修改。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from schemas.coupon import (
    CouponCreate,
    CouponResponse,
    CouponStatusUpdate,
    CouponUpdate,
)
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.coupon_service import CouponService
from service.dependencies import get_coupon_service
from utils.custom_exceptions import handle_service_exceptions

router = APIRouter(prefix="/coupon", tags=["优惠券管理"])

# ===== 鉴权（默认关闭，接口开箱即用）=====
# 优惠券为平台配置数据，如需限制为登录/管理员可维护，统一在 router 上挂载依赖：
#   from core.permissions import get_current_active_user, require_admin
#   router = APIRouter(
#       prefix="/coupon",
#       tags=["优惠券管理"],
#       dependencies=[Depends(require_admin)],
#   )


@router.get(
    "",
    response_model=PaginationResponse[CouponResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取优惠券列表",
)
@handle_service_exceptions
async def get_coupon_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: int | None = Query(None, ge=0, le=1, description="状态：1可用 0停用"),
    keyword: str | None = Query(None, max_length=50, description="关键字（券名称 / 编码）"),
    service: CouponService = Depends(get_coupon_service),
):
    """获取优惠券分页列表（支持状态过滤与关键字检索）"""
    result = await service.get_list(
        page=page,
        size=page_size,
        filters={"status": status, "keyword": keyword},
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[CouponResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取优惠券详情",
)
@handle_service_exceptions
async def get_coupon_detail(
    id: int = Path(..., description="优惠券ID"),
    service: CouponService = Depends(get_coupon_service),
):
    """获取优惠券详情"""
    result = await service.get_detail(id)
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[CouponResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="创建优惠券",
)
@handle_service_exceptions
async def create_coupon(
    data: CouponCreate,
    service: CouponService = Depends(get_coupon_service),
):
    """创建优惠券（编码全局唯一）"""
    result = await service.create(data)
    return success_response(result, message="优惠券创建成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[CouponResponse],
    summary="更新优惠券",
)
@handle_service_exceptions
async def update_coupon(
    id: int = Path(..., description="优惠券ID"),
    data: CouponUpdate = ...,
    service: CouponService = Depends(get_coupon_service),
):
    """更新优惠券（不含状态字段）"""
    result = await service.update(id, data)
    return success_response(result, message="优惠券更新成功")


@router.patch(
    "/{id}/status",
    response_model=SuccessResponse[CouponResponse],
    summary="修改优惠券状态",
)
@handle_service_exceptions
async def update_coupon_status(
    id: int = Path(..., description="优惠券ID"),
    data: CouponStatusUpdate = ...,
    service: CouponService = Depends(get_coupon_service),
):
    """
    专用修改状态（status：1可用 0停用）
    """
    result = await service.update_status(id, data)
    return success_response(result, message="优惠券状态更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除优惠券",
)
@handle_service_exceptions
async def delete_coupon(
    id: int = Path(..., description="优惠券ID"),
    service: CouponService = Depends(get_coupon_service),
):
    """删除优惠券（软删除）"""
    await service.delete(id)
    return success_response(None, message="优惠券删除成功")
