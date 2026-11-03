"""
商品规格表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 默认不启用鉴权（接口开箱即用、无需登录）；如需登录鉴权，见文件底部「鉴权启用」注释。
- 字段校验由 Schema 在进入端点前完成。
- 规格通过 goods_id 关联商品，商品存在性校验与过滤逻辑均在 Service 实现。
- 状态字段通过 PATCH /{id}/status 专用修改。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from schemas.goods_spec import (
    GoodsSpecCreate,
    GoodsSpecResponse,
    GoodsSpecStatusUpdate,
    GoodsSpecUpdate,
)
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.dependencies import get_goods_spec_service
from service.goods_spec_service import GoodsSpecService
from utils.custom_exceptions import handle_service_exceptions

router = APIRouter(prefix="/goods-spec", tags=["商品规格管理"])

# ===== 鉴权（默认关闭，接口开箱即用）=====
# 本脚手架生成的 CRUD 接口默认不需要登录。若项目需要登录鉴权，可统一在 router
# 上挂载依赖（推荐），或在单个路由上添加该 Depends：
#   from core.permissions import get_current_active_user
#   router = APIRouter(
#       prefix="/goods-spec",
#       tags=["商品规格管理"],
#       dependencies=[Depends(get_current_active_user)],
#   )


@router.get(
    "",
    response_model=PaginationResponse[GoodsSpecResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取商品规格列表",
)
@handle_service_exceptions
async def get_goods_spec_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    goods_id: int | None = Query(None, description="所属商品ID"),
    status: int | None = Query(None, ge=0, le=1, description="状态：1启用 0停用"),
    service: GoodsSpecService = Depends(get_goods_spec_service),
):
    """获取商品规格分页列表（可按所属商品与状态过滤）"""
    result = await service.get_list(
        page=page,
        size=page_size,
        filters={
            "goods_id": goods_id,
            "status": status,
        },
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=SuccessResponse[GoodsSpecResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取商品规格详情",
)
@handle_service_exceptions
async def get_goods_spec_detail(
    id: int = Path(..., description="规格ID"),
    service: GoodsSpecService = Depends(get_goods_spec_service),
):
    """获取商品规格详情"""
    result = await service.get_detail(id)
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[GoodsSpecResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="创建商品规格",
)
@handle_service_exceptions
async def create_goods_spec(
    data: GoodsSpecCreate,
    service: GoodsSpecService = Depends(get_goods_spec_service),
):
    """创建商品规格（需指定所属商品 goods_id）"""
    result = await service.create(data)
    return success_response(result, message="商品规格创建成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[GoodsSpecResponse],
    summary="更新商品规格",
)
@handle_service_exceptions
async def update_goods_spec(
    id: int = Path(..., description="规格ID"),
    data: GoodsSpecUpdate = ...,
    service: GoodsSpecService = Depends(get_goods_spec_service),
):
    """更新商品规格（不含状态字段）"""
    result = await service.update(id, data)
    return success_response(result, message="商品规格更新成功")


@router.patch(
    "/{id}/status",
    response_model=SuccessResponse[GoodsSpecResponse],
    summary="修改商品规格状态",
)
@handle_service_exceptions
async def update_goods_spec_status(
    id: int = Path(..., description="规格ID"),
    data: GoodsSpecStatusUpdate = ...,
    service: GoodsSpecService = Depends(get_goods_spec_service),
):
    """
    专用修改状态（status：1启用 0停用）
    """
    result = await service.update_status(id, data)
    return success_response(result, message="商品规格状态更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除商品规格",
)
@handle_service_exceptions
async def delete_goods_spec(
    id: int = Path(..., description="规格ID"),
    service: GoodsSpecService = Depends(get_goods_spec_service),
):
    """删除商品规格（软删除）"""
    await service.delete(id)
    return success_response(None, message="商品规格删除成功")
