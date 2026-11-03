"""
商品表API路由

此文件由 SQL-to-FastAPI-Scaffold 自动生成。

约定：
- HTTP 层统一只依赖 Service，不直接依赖 Repository。
- 默认不启用鉴权（接口开箱即用、无需登录）；如需登录鉴权，见文件底部「鉴权启用」注释。
- 字段校验由 Schema 在进入端点前完成。
- 秒杀（flash）、热销（hot）、上下架（status）过滤与软删除逻辑均由 Service 实现。
- 上下架状态通过 PATCH /{id}/status 专用修改。
"""

from fastapi import APIRouter, Depends, Path, Query
from fastapi import status as http_status

from schemas.goods import (
    GoodsCreate,
    GoodsResponse,
    GoodsStatusUpdate,
    GoodsUpdate,
)
from schemas.response import (
    PaginationResponse,
    SuccessResponse,
    paginated_response,
    success_response,
)
from service.dependencies import get_goods_service
from service.goods_service import GoodsService
from utils.custom_exceptions import handle_service_exceptions

router = APIRouter(prefix="/goods", tags=["商品管理"])

# ===== 鉴权（默认关闭，接口开箱即用）=====
# 本脚手架生成的 CRUD 接口默认不需要登录。若项目需要登录鉴权，可统一在 router
# 上挂载依赖（推荐），或在单个路由上添加该 Depends：
#   from core.permissions import get_current_active_user
#   router = APIRouter(
#       prefix="/goods",
#       tags=["商品管理"],
#       dependencies=[Depends(get_current_active_user)],
#   )


@router.get(
    "",
    response_model=PaginationResponse[GoodsResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取商品列表",
)
@handle_service_exceptions
async def get_goods_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: int | None = Query(None, description="分类ID"),
    flash: bool | None = Query(None, description="是否只看秒杀商品"),
    hot: bool | None = Query(None, description="是否只看热销商品"),
    status: int | None = Query(None, ge=0, le=1, description="上下架状态：1上架 0下架"),
    keyword: str | None = Query(None, max_length=100, description="关键字（商品名称 / 商品编号）"),
    service: GoodsService = Depends(get_goods_service),
):
    """获取商品分页列表（支持分类、秒杀、热销、上下架过滤与关键字检索）"""
    result = await service.get_list(
        page=page,
        size=page_size,
        filters={
            "category_id": category_id,
            "flash": flash,
            "hot": hot,
            "status": status,
            "keyword": keyword,
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
    response_model=SuccessResponse[GoodsResponse],
    status_code=http_status.HTTP_200_OK,
    summary="获取商品详情",
)
@handle_service_exceptions
async def get_goods_detail(
    id: int = Path(..., description="商品ID"),
    service: GoodsService = Depends(get_goods_service),
):
    """获取商品详情"""
    result = await service.get_detail(id)
    return success_response(result)


@router.post(
    "",
    response_model=SuccessResponse[GoodsResponse],
    status_code=http_status.HTTP_201_CREATED,
    summary="创建商品",
)
@handle_service_exceptions
async def create_goods(
    data: GoodsCreate,
    service: GoodsService = Depends(get_goods_service),
):
    """创建商品"""
    result = await service.create(data)
    return success_response(result, message="商品创建成功")


@router.put(
    "/{id}",
    response_model=SuccessResponse[GoodsResponse],
    summary="更新商品",
)
@handle_service_exceptions
async def update_goods(
    id: int = Path(..., description="商品ID"),
    data: GoodsUpdate = ...,
    service: GoodsService = Depends(get_goods_service),
):
    """更新商品（不含上下架状态字段）"""
    result = await service.update(id, data)
    return success_response(result, message="商品更新成功")


@router.patch(
    "/{id}/status",
    response_model=SuccessResponse[GoodsResponse],
    summary="修改商品上下架状态",
)
@handle_service_exceptions
async def update_goods_status(
    id: int = Path(..., description="商品ID"),
    data: GoodsStatusUpdate = ...,
    service: GoodsService = Depends(get_goods_service),
):
    """
    专用修改上下架状态（status：1上架 0下架）
    """
    result = await service.update_status(id, data)
    return success_response(result, message="商品上下架状态更新成功")


@router.delete(
    "/{id}",
    response_model=SuccessResponse[None],
    summary="删除商品",
)
@handle_service_exceptions
async def delete_goods(
    id: int = Path(..., description="商品ID"),
    service: GoodsService = Depends(get_goods_service),
):
    """删除商品（软删除）"""
    await service.delete(id)
    return success_response(None, message="商品删除成功")
