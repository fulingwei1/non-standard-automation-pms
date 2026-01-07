"""
BOM管理模块 - API路由
"""
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.bom_schemas import (
    # 物料相关
    MaterialCreate, MaterialUpdate, MaterialResponse, MaterialListResponse,
    # BOM相关
    BomHeaderCreate, BomHeaderUpdate, BomHeaderResponse,
    BomDetailResponse, BomListResponse,
    # BOM明细相关
    BomItemCreate, BomItemUpdate, BomItemResponse,
    # 版本相关
    BomVersionCreate, BomVersionResponse, BomVersionListResponse,
    # 统计相关
    BomStatistics, CategoryStatistics, KitRateStatistics,
    ShortageItem, ShortageListResponse,
    # 操作相关
    BomReviewRequest, BomPublishRequest,
    BomCompareRequest, BomCompareResponse,
    BatchUpdateProcurementStatus, BatchUpdateSupplier, BatchDeleteItems
)
from app.services.bom_service import (
    MaterialService, BomService, BomItemService,
    BomVersionService, BomStatisticsService
)

router = APIRouter(prefix="/bom", tags=["BOM管理"])


# ==================== 物料管理接口 ====================

@router.post("/materials", response_model=MaterialResponse, summary="创建物料")
async def create_material(
    data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新物料"""
    # 检查物料编码是否重复
    existing = await MaterialService.get_material_by_code(db, data.material_code)
    if existing:
        raise HTTPException(status_code=400, detail="物料编码已存在")

    material = await MaterialService.create_material(
        db, data, current_user["user_id"]
    )
    return material


@router.get("/materials", response_model=MaterialListResponse, summary="物料列表")
async def list_materials(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="物料类别"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """查询物料列表"""
    materials, total = await MaterialService.list_materials(
        db, keyword, category, status, page, page_size
    )
    return {"total": total, "items": materials}


@router.get("/materials/{material_id}", response_model=MaterialResponse, summary="物料详情")
async def get_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取物料详情"""
    material = await MaterialService.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    return material


@router.put("/materials/{material_id}", response_model=MaterialResponse, summary="更新物料")
async def update_material(
    material_id: int,
    data: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新物料信息"""
    material = await MaterialService.update_material(db, material_id, data)
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    return material


@router.delete("/materials/{material_id}", summary="删除物料")
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除物料"""
    success = await MaterialService.delete_material(db, material_id)
    if not success:
        raise HTTPException(status_code=404, detail="物料不存在")
    return {"message": "删除成功"}


# ==================== BOM管理接口 ====================

@router.post("/headers", response_model=BomHeaderResponse, summary="创建BOM")
async def create_bom(
    data: BomHeaderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建新BOM"""
    bom = await BomService.create_bom(db, data, current_user["user_id"])
    return bom


@router.get("/headers", response_model=BomListResponse, summary="BOM列表")
async def list_boms(
    project_id: Optional[int] = Query(None, description="项目ID"),
    machine_no: Optional[str] = Query(None, description="机台号"),
    status: Optional[str] = Query(None, description="状态"),
    designer_id: Optional[int] = Query(None, description="设计人ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """查询BOM列表"""
    boms, total = await BomService.list_boms(
        db, project_id, machine_no, status, designer_id, page, page_size
    )
    return {"total": total, "items": boms}


@router.get("/headers/{bom_id}", response_model=BomDetailResponse, summary="BOM详情")
async def get_bom(
    bom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取BOM详情（含明细）"""
    bom = await BomService.get_bom(db, bom_id, include_items=True)
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    return bom


@router.put("/headers/{bom_id}", response_model=BomHeaderResponse, summary="更新BOM")
async def update_bom(
    bom_id: int,
    data: BomHeaderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新BOM头信息"""
    try:
        bom = await BomService.update_bom(db, bom_id, data)
        if not bom:
            raise HTTPException(status_code=404, detail="BOM不存在")
        return bom
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/headers/{bom_id}", summary="删除BOM")
async def delete_bom(
    bom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除BOM"""
    try:
        success = await BomService.delete_bom(db, bom_id)
        if not success:
            raise HTTPException(status_code=404, detail="BOM不存在")
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== BOM明细接口 ====================

@router.post("/headers/{bom_id}/items", response_model=BomItemResponse, summary="添加BOM明细")
async def add_bom_item(
    bom_id: int,
    data: BomItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """添加BOM明细"""
    try:
        item = await BomItemService.add_item(db, bom_id, data)
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/items/{item_id}", response_model=BomItemResponse, summary="更新BOM明细")
async def update_bom_item(
    item_id: int,
    data: BomItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新BOM明细"""
    try:
        item = await BomItemService.update_item(db, item_id, data)
        if not item:
            raise HTTPException(status_code=404, detail="明细不存在")
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/items/{item_id}", summary="删除BOM明细")
async def delete_bom_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除BOM明细"""
    try:
        success = await BomItemService.delete_item(db, item_id)
        if not success:
            raise HTTPException(status_code=404, detail="明细不存在")
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/items/batch-delete", summary="批量删除明细")
async def batch_delete_items(
    data: BatchDeleteItems,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量删除BOM明细"""
    count = await BomItemService.batch_delete_items(db, data.item_ids)
    return {"message": f"成功删除{count}条明细"}


@router.post("/items/batch-update-status", summary="批量更新采购状态")
async def batch_update_procurement_status(
    data: BatchUpdateProcurementStatus,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量更新采购状态"""
    count = await BomItemService.batch_update_procurement_status(
        db, data.item_ids, data.procurement_status,
        data.ordered_qty, data.received_qty
    )
    return {"message": f"成功更新{count}条明细"}


# ==================== BOM版本接口 ====================

@router.post("/headers/{bom_id}/publish", response_model=BomVersionResponse, summary="发布BOM")
async def publish_bom(
    bom_id: int,
    data: BomPublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """发布BOM（创建新版本）"""
    try:
        version_data = BomVersionCreate(
            version_type=data.version_type,
            change_summary=data.change_summary
        )
        version = await BomVersionService.create_version(
            db, bom_id, version_data,
            current_user["user_id"],
            current_user["user_name"]
        )
        return version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/headers/{bom_id}/versions", response_model=BomVersionListResponse, summary="版本历史")
async def list_bom_versions(
    bom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取BOM版本历史"""
    versions = await BomVersionService.list_versions(db, bom_id)
    return {"total": len(versions), "items": versions}


@router.get("/versions/{version_id}", response_model=BomVersionResponse, summary="版本详情")
async def get_bom_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取版本详情"""
    version = await BomVersionService.get_version(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return version


@router.post("/versions/compare", response_model=BomCompareResponse, summary="版本对比")
async def compare_versions(
    data: BomCompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """对比两个版本"""
    try:
        result = await BomVersionService.compare_versions(
            db, data.version_id_1, data.version_id_2
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== BOM统计接口 ====================

@router.get("/statistics", response_model=BomStatistics, summary="BOM统计")
async def get_bom_statistics(
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取BOM统计信息"""
    stats = await BomStatisticsService.get_bom_statistics(db, project_id)
    return stats


@router.get("/headers/{bom_id}/category-statistics", summary="类别统计")
async def get_category_statistics(
    bom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取BOM物料类别统计"""
    stats = await BomStatisticsService.get_category_statistics(db, bom_id)
    return {"items": stats}


@router.get("/headers/{bom_id}/kit-rate", response_model=KitRateStatistics, summary="齐套率")
async def get_kit_rate(
    bom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """计算BOM齐套率"""
    result = await BomStatisticsService.calculate_kit_rate(db, bom_id)
    return result


@router.get("/shortage-list", response_model=ShortageListResponse, summary="缺料清单")
async def get_shortage_list(
    project_id: Optional[int] = Query(None, description="项目ID"),
    bom_id: Optional[int] = Query(None, description="BOM ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取缺料清单"""
    items, total = await BomStatisticsService.get_shortage_list(
        db, project_id, bom_id, page, page_size
    )
    return {"total": total, "items": items}


# ==================== BOM导入导出接口 ====================

@router.post("/headers/{bom_id}/import", summary="导入BOM明细")
async def import_bom_items(
    bom_id: int,
    file: UploadFile = File(...),
    update_mode: str = Query("append", description="更新模式：append/replace"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """从Excel导入BOM明细"""
    # 检查BOM存在且状态为草稿
    bom = await BomService.get_bom(db, bom_id)
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    if bom.status != "草稿":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能导入")

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="请上传Excel或CSV文件")

    # TODO: 实现Excel解析和导入逻辑
    # 这里返回模拟结果
    return {
        "message": "导入成功",
        "imported_count": 0,
        "updated_count": 0,
        "error_count": 0,
        "errors": []
    }


@router.get("/headers/{bom_id}/export", summary="导出BOM")
async def export_bom(
    bom_id: int,
    file_type: str = Query("excel", description="文件类型：excel/csv/pdf"),
    include_price: bool = Query(False, description="是否包含价格"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """导出BOM为Excel/CSV/PDF"""
    bom = await BomService.get_bom(db, bom_id, include_items=True)
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # TODO: 实现文件生成和下载逻辑
    # 这里返回模拟结果
    return {
        "message": "导出成功",
        "file_url": f"/api/v1/files/bom_{bom_id}.{file_type}"
    }


@router.get("/export-template", summary="下载导入模板")
async def download_import_template(
    current_user: dict = Depends(get_current_user)
):
    """下载BOM导入模板"""
    # TODO: 生成并返回模板文件
    return {
        "message": "模板下载",
        "file_url": "/api/v1/files/bom_import_template.xlsx"
    }
