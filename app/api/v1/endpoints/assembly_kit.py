# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.api import deps
from app.models import (
    AssemblyStage, AssemblyTemplate, CategoryStageMapping,
    BomItemAssemblyAttrs, MaterialReadiness, ShortageDetail,
    ShortageAlertRule, SchedulingSuggestion,
    Project, Machine, BomHeader, BomItem, Material, MaterialCategory,
    User
)
from app.models.enums import (
    AssemblyStageEnum, ImportanceLevelEnum, ShortageAlertLevelEnum,
    SuggestionTypeEnum, SuggestionStatusEnum
)
from app.schemas.assembly_kit import (
    # Stage
    AssemblyStageCreate, AssemblyStageUpdate, AssemblyStageResponse,
    # Template
    AssemblyTemplateCreate, AssemblyTemplateUpdate, AssemblyTemplateResponse,
    # Category Mapping
    CategoryStageMappingCreate, CategoryStageMappingUpdate, CategoryStageMappingResponse,
    # BOM Assembly Attrs
    BomItemAssemblyAttrsCreate, BomItemAssemblyAttrsBatchCreate,
    BomItemAssemblyAttrsUpdate, BomItemAssemblyAttrsResponse,
    BomAssemblyAttrsAutoRequest, BomAssemblyAttrsTemplateRequest,
    # Readiness
    MaterialReadinessCreate, MaterialReadinessResponse, MaterialReadinessDetailResponse, StageKitRate,
    # Shortage
    ShortageDetailResponse, ShortageAlertItem, ShortageAlertListResponse,
    # Alert Rule
    ShortageAlertRuleCreate, ShortageAlertRuleUpdate, ShortageAlertRuleResponse,
    # Suggestion
    SchedulingSuggestionResponse, SchedulingSuggestionAccept, SchedulingSuggestionReject,
    # Dashboard
    AssemblyDashboardResponse, AssemblyDashboardStats, AssemblyDashboardStageStats
)
from app.schemas.common import ResponseModel, MessageResponse

router = APIRouter()


# ==================== 装配阶段管理 ====================

@router.get("/stages", response_model=ResponseModel)
async def get_assembly_stages(
    db: Session = Depends(deps.get_db),
    include_inactive: bool = Query(False, description="是否包含已禁用阶段")
):
    """获取所有装配阶段"""
    query = db.query(AssemblyStage)
    if not include_inactive:
        query = query.filter(AssemblyStage.is_active == True)
    stages = query.order_by(AssemblyStage.stage_order).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[AssemblyStageResponse.model_validate(s) for s in stages]
    )


@router.put("/stages/{stage_code}", response_model=ResponseModel)
async def update_assembly_stage(
    stage_code: str,
    stage_data: AssemblyStageUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新装配阶段"""
    stage = db.query(AssemblyStage).filter(AssemblyStage.stage_code == stage_code).first()
    if not stage:
        raise HTTPException(status_code=404, detail=f"装配阶段 {stage_code} 不存在")

    update_data = stage_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stage, key, value)
    stage.updated_at = datetime.now()

    db.commit()
    db.refresh(stage)

    return ResponseModel(
        code=200,
        message="更新成功",
        data=AssemblyStageResponse.model_validate(stage)
    )


# ==================== 物料分类映射 ====================

@router.get("/category-mappings", response_model=ResponseModel)
async def get_category_mappings(
    db: Session = Depends(deps.get_db),
    category_id: Optional[int] = Query(None, description="物料分类ID"),
    stage_code: Optional[str] = Query(None, description="装配阶段编码")
):
    """获取物料分类映射列表"""
    query = db.query(CategoryStageMapping)
    if category_id:
        query = query.filter(CategoryStageMapping.category_id == category_id)
    if stage_code:
        query = query.filter(CategoryStageMapping.stage_code == stage_code)

    mappings = query.all()

    # 关联物料分类和阶段名称
    result = []
    for m in mappings:
        data = CategoryStageMappingResponse.model_validate(m)
        category = db.query(MaterialCategory).filter(MaterialCategory.id == m.category_id).first()
        stage = db.query(AssemblyStage).filter(AssemblyStage.stage_code == m.stage_code).first()
        data.category_name = category.name if category else None
        data.stage_name = stage.stage_name if stage else None
        result.append(data)

    return ResponseModel(code=200, message="success", data=result)


@router.post("/category-mappings", response_model=ResponseModel)
async def create_category_mapping(
    mapping_data: CategoryStageMappingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建物料分类映射"""
    # 检查是否已存在
    existing = db.query(CategoryStageMapping).filter(
        CategoryStageMapping.category_id == mapping_data.category_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该物料分类已存在映射配置")

    mapping = CategoryStageMapping(**mapping_data.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return ResponseModel(
        code=200,
        message="创建成功",
        data=CategoryStageMappingResponse.model_validate(mapping)
    )


@router.put("/category-mappings/{mapping_id}", response_model=ResponseModel)
async def update_category_mapping(
    mapping_id: int,
    mapping_data: CategoryStageMappingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新物料分类映射"""
    mapping = db.query(CategoryStageMapping).filter(CategoryStageMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="映射配置不存在")

    update_data = mapping_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mapping, key, value)
    mapping.updated_at = datetime.now()

    db.commit()
    db.refresh(mapping)

    return ResponseModel(code=200, message="更新成功", data=CategoryStageMappingResponse.model_validate(mapping))


@router.delete("/category-mappings/{mapping_id}", response_model=MessageResponse)
async def delete_category_mapping(
    mapping_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """删除物料分类映射"""
    mapping = db.query(CategoryStageMapping).filter(CategoryStageMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="映射配置不存在")

    db.delete(mapping)
    db.commit()

    return MessageResponse(code=200, message="删除成功")


# ==================== BOM装配属性 ====================

@router.get("/bom/{bom_id}/assembly-attrs", response_model=ResponseModel)
async def get_bom_assembly_attrs(
    bom_id: int,
    db: Session = Depends(deps.get_db),
    stage_code: Optional[str] = Query(None, description="筛选装配阶段"),
    is_blocking: Optional[bool] = Query(None, description="筛选阻塞性物料")
):
    """获取BOM装配属性列表"""
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    query = db.query(BomItemAssemblyAttrs).filter(BomItemAssemblyAttrs.bom_id == bom_id)
    if stage_code:
        query = query.filter(BomItemAssemblyAttrs.assembly_stage == stage_code)
    if is_blocking is not None:
        query = query.filter(BomItemAssemblyAttrs.is_blocking == is_blocking)

    attrs = query.order_by(BomItemAssemblyAttrs.assembly_stage, BomItemAssemblyAttrs.stage_order).all()

    # 关联物料信息
    result = []
    for attr in attrs:
        data = BomItemAssemblyAttrsResponse.model_validate(attr)
        bom_item = db.query(BomItem).filter(BomItem.id == attr.bom_item_id).first()
        if bom_item:
            material = db.query(Material).filter(Material.id == bom_item.material_id).first()
            if material:
                data.material_code = material.code
                data.material_name = material.name
            data.required_qty = bom_item.quantity
        stage = db.query(AssemblyStage).filter(AssemblyStage.stage_code == attr.assembly_stage).first()
        if stage:
            data.stage_name = stage.stage_name
        result.append(data)

    return ResponseModel(code=200, message="success", data=result)


@router.post("/bom/{bom_id}/assembly-attrs/batch", response_model=ResponseModel)
async def batch_set_assembly_attrs(
    bom_id: int,
    batch_data: BomItemAssemblyAttrsBatchCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """批量设置BOM装配属性"""
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    created_count = 0
    updated_count = 0

    for item in batch_data.items:
        if item.bom_id != bom_id:
            continue

        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == item.bom_item_id
        ).first()

        if existing:
            # 更新
            for key, value in item.model_dump().items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now()
            updated_count += 1
        else:
            # 创建
            attr = BomItemAssemblyAttrs(**item.model_dump())
            db.add(attr)
            created_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量设置完成，新增 {created_count} 条，更新 {updated_count} 条",
        data={"created": created_count, "updated": updated_count}
    )


@router.put("/bom/assembly-attrs/{attr_id}", response_model=ResponseModel)
async def update_assembly_attr(
    attr_id: int,
    attr_data: BomItemAssemblyAttrsUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新单个物料装配属性"""
    attr = db.query(BomItemAssemblyAttrs).filter(BomItemAssemblyAttrs.id == attr_id).first()
    if not attr:
        raise HTTPException(status_code=404, detail="装配属性不存在")

    update_data = attr_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(attr, key, value)
    attr.updated_at = datetime.now()

    db.commit()
    db.refresh(attr)

    return ResponseModel(code=200, message="更新成功", data=BomItemAssemblyAttrsResponse.model_validate(attr))


@router.post("/bom/{bom_id}/assembly-attrs/auto", response_model=ResponseModel)
async def auto_assign_assembly_attrs(
    bom_id: int,
    request: BomAssemblyAttrsAutoRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """自动分配装配属性（基于物料分类映射）"""
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()

    assigned_count = 0
    skipped_count = 0

    for bom_item in bom_items:
        # 检查是否已有配置
        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id
        ).first()

        if existing and not request.overwrite:
            skipped_count += 1
            continue

        # 获取物料分类
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        if not material or not material.category_id:
            skipped_count += 1
            continue

        # 获取映射配置
        mapping = db.query(CategoryStageMapping).filter(
            CategoryStageMapping.category_id == material.category_id
        ).first()

        if not mapping:
            # 使用默认阶段
            stage_code = "MECH"
            is_blocking = True
            can_postpone = False
        else:
            stage_code = mapping.stage_code
            is_blocking = mapping.is_blocking
            can_postpone = mapping.can_postpone

        if existing:
            existing.assembly_stage = stage_code
            existing.is_blocking = is_blocking
            existing.can_postpone = can_postpone
            existing.updated_at = datetime.now()
        else:
            attr = BomItemAssemblyAttrs(
                bom_item_id=bom_item.id,
                bom_id=bom_id,
                assembly_stage=stage_code,
                importance_level="NORMAL",
                is_blocking=is_blocking,
                can_postpone=can_postpone
            )
            db.add(attr)

        assigned_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"自动分配完成，处理 {assigned_count} 条，跳过 {skipped_count} 条",
        data={"assigned": assigned_count, "skipped": skipped_count}
    )


@router.get("/bom/{bom_id}/assembly-attrs/recommendations", response_model=ResponseModel)
async def get_assembly_attr_recommendations(
    bom_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取装配属性推荐结果（不应用，仅返回推荐）"""
    from app.services.assembly_attr_recommender import AssemblyAttrRecommender
    
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()

    # 批量推荐
    recommendations = AssemblyAttrRecommender.batch_recommend(db, bom_id, bom_items)

    # 构建响应
    result = []
    for bom_item in bom_items:
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        if not material:
            continue
        
        rec = recommendations.get(bom_item.id)
        if rec:
            result.append({
                "bom_item_id": bom_item.id,
                "material_code": material.code,
                "material_name": material.name,
                "recommended_stage": rec.stage_code,
                "recommended_blocking": rec.is_blocking,
                "recommended_postpone": rec.can_postpone,
                "recommended_importance": rec.importance_level,
                "confidence": rec.confidence,
                "source": rec.source,
                "reason": rec.reason
            })

    return ResponseModel(
        code=200,
        message="推荐结果获取成功",
        data={"recommendations": result, "total": len(result)}
    )


@router.post("/bom/{bom_id}/assembly-attrs/smart-recommend", response_model=ResponseModel)
async def smart_recommend_assembly_attrs(
    bom_id: int,
    request: BomAssemblyAttrsAutoRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """智能推荐装配属性（多级推荐规则）"""
    from app.services.assembly_attr_recommender import AssemblyAttrRecommender
    
    # 验证BOM存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()

    # 批量推荐
    recommendations = AssemblyAttrRecommender.batch_recommend(db, bom_id, bom_items)

    assigned_count = 0
    skipped_count = 0
    recommendation_stats = {
        "HISTORY": 0,
        "CATEGORY": 0,
        "KEYWORD": 0,
        "SUPPLIER": 0,
        "DEFAULT": 0
    }

    for bom_item in bom_items:
        # 检查是否已有配置
        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id
        ).first()

        if existing and not request.overwrite:
            skipped_count += 1
            continue

        # 获取推荐结果
        rec = recommendations.get(bom_item.id)
        if not rec:
            skipped_count += 1
            continue

        # 统计推荐来源
        recommendation_stats[rec.source] = recommendation_stats.get(rec.source, 0) + 1

        if existing:
            existing.assembly_stage = rec.stage_code
            existing.is_blocking = rec.is_blocking
            existing.can_postpone = rec.can_postpone
            existing.importance_level = rec.importance_level
            existing.setting_source = rec.source
            existing.updated_at = datetime.now()
        else:
            attr = BomItemAssemblyAttrs(
                bom_item_id=bom_item.id,
                bom_id=bom_id,
                assembly_stage=rec.stage_code,
                importance_level=rec.importance_level,
                is_blocking=rec.is_blocking,
                can_postpone=rec.can_postpone,
                setting_source=rec.source,
                created_by=current_user.id
            )
            db.add(attr)

        assigned_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"智能推荐完成，处理 {assigned_count} 条，跳过 {skipped_count} 条",
        data={
            "assigned": assigned_count,
            "skipped": skipped_count,
            "recommendation_stats": recommendation_stats
        }
    )


@router.post("/bom/{bom_id}/assembly-attrs/template", response_model=ResponseModel)
async def apply_assembly_template(
    bom_id: int,
    request: BomAssemblyAttrsTemplateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """套用装配模板"""
    # 验证BOM和模板存在
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    template = db.query(AssemblyTemplate).filter(AssemblyTemplate.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.stage_config:
        raise HTTPException(status_code=400, detail="模板配置为空")

    # 解析模板配置并应用
    # stage_config格式: {"category_code": {"stage": "MECH", "blocking": true, "postpone": false}}
    stage_config = template.stage_config

    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == bom_id).all()
    applied_count = 0

    for bom_item in bom_items:
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        if not material:
            continue

        # 查找模板中匹配的配置
        config = None
        if material.category_id:
            category = db.query(MaterialCategory).filter(MaterialCategory.id == material.category_id).first()
            if category and category.code in stage_config:
                config = stage_config[category.code]

        if not config:
            continue

        existing = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id
        ).first()

        if existing and not request.overwrite:
            continue

        if existing:
            existing.assembly_stage = config.get("stage", "MECH")
            existing.is_blocking = config.get("blocking", True)
            existing.can_postpone = config.get("postpone", False)
            existing.updated_at = datetime.now()
        else:
            attr = BomItemAssemblyAttrs(
                bom_item_id=bom_item.id,
                bom_id=bom_id,
                assembly_stage=config.get("stage", "MECH"),
                importance_level="NORMAL",
                is_blocking=config.get("blocking", True),
                can_postpone=config.get("postpone", False)
            )
            db.add(attr)

        applied_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"模板套用完成，应用 {applied_count} 条配置",
        data={"applied": applied_count}
    )


# ==================== 齐套分析 ====================

def generate_readiness_no() -> str:
    """生成齐套分析单号"""
    now = datetime.now()
    return f"KR{now.strftime('%Y%m%d%H%M%S')}"


def calculate_available_qty(
    db: Session,
    material_id: int,
    check_date: date
) -> tuple:
    """计算物料可用数量

    返回: (库存数量, 已分配数量, 在途数量, 可用数量)
    """
    from app.models import PurchaseOrderItem, PurchaseOrder

    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        return (Decimal(0), Decimal(0), Decimal(0), Decimal(0))

    # 库存数量(简化处理，实际应从库存表获取)
    stock_qty = getattr(material, 'stock_qty', Decimal(0)) or Decimal(0)

    # 已分配数量(简化处理)
    allocated_qty = Decimal(0)

    # 在途数量(已采购未到货，预计在check_date前到货)
    in_transit_qty = Decimal(0)
    try:
        in_transit = db.query(func.sum(PurchaseOrderItem.quantity)).join(
            PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
        ).filter(
            PurchaseOrderItem.material_id == material_id,
            PurchaseOrder.status.in_(['approved', 'partial_received']),
            PurchaseOrder.expected_date <= check_date
        ).scalar()
        in_transit_qty = Decimal(in_transit or 0)
    except Exception:
        pass

    available = max(Decimal(0), stock_qty - allocated_qty + in_transit_qty)
    return (stock_qty, allocated_qty, in_transit_qty, available)


def calculate_estimated_ready_date(
    db: Session,
    blocking_items: List[Dict],
    check_date: date
) -> Optional[date]:
    """
    计算预计完全齐套日期
    
    基于阻塞物料的预计到货日期，取最晚的日期
    """
    from app.models import PurchaseOrderItem, PurchaseOrder
    
    if not blocking_items:
        return None
    
    latest_date = None
    
    for item in blocking_items:
        material_id = item.get("material_id")
        shortage_qty = item.get("shortage_qty", Decimal(0))
        expected_arrival = item.get("expected_arrival")
        
        # 如果缺料明细中已有预计到货日期，直接使用
        if expected_arrival:
            if latest_date is None or expected_arrival > latest_date:
                latest_date = expected_arrival
            continue
        
        # 否则从采购订单查找
        if not material_id or shortage_qty <= 0:
            continue
        
        try:
            po_items = db.query(PurchaseOrderItem).join(
                PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
            ).filter(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrder.status.in_(['approved', 'partial_received']),
                or_(
                    PurchaseOrder.promised_date.isnot(None),
                    PurchaseOrder.required_date.isnot(None)
                )
            ).order_by(
                PurchaseOrder.promised_date.desc(),
                PurchaseOrder.required_date.desc()
            ).all()
            
            for po_item in po_items:
                if po_item.order:
                    # 优先使用承诺交期，其次使用要求交期
                    expected_date = po_item.order.promised_date or po_item.order.required_date
                    if expected_date:
                        if latest_date is None or expected_date > latest_date:
                            latest_date = expected_date
                        break
        except Exception:
            continue
    
    return latest_date


def determine_alert_level(
    db: Session,
    is_blocking: bool,
    shortage_rate: Decimal,
    days_to_required: int
) -> str:
    """确定预警级别"""
    rules = db.query(ShortageAlertRule).filter(
        ShortageAlertRule.is_active == True
    ).order_by(ShortageAlertRule.days_before_required).all()

    for rule in rules:
        if rule.only_blocking and not is_blocking:
            continue
        if shortage_rate < (rule.min_shortage_rate or 0):
            continue
        if days_to_required <= rule.days_before_required:
            return rule.alert_level

    return "L4"  # 默认常规预警


@router.post("/analysis", response_model=ResponseModel)
async def execute_kit_analysis(
    request: MaterialReadinessCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """执行齐套分析"""
    # 验证项目
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证BOM
    bom = db.query(BomHeader).filter(BomHeader.id == request.bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 验证机台(可选)
    machine = None
    if request.machine_id:
        machine = db.query(Machine).filter(Machine.id == request.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")

    check_date = request.check_date or date.today()

    # 获取BOM物料及装配属性
    bom_items = db.query(BomItem).filter(BomItem.bom_header_id == request.bom_id).all()

    if not bom_items:
        raise HTTPException(status_code=400, detail="BOM无物料明细")

    # 获取装配阶段
    stages = db.query(AssemblyStage).filter(
        AssemblyStage.is_active == True
    ).order_by(AssemblyStage.stage_order).all()

    stage_map = {s.stage_code: s for s in stages}

    # 按阶段分组统计
    stage_results = {}
    for stage in stages:
        stage_results[stage.stage_code] = {
            "total": 0,
            "fulfilled": 0,
            "blocking_total": 0,
            "blocking_fulfilled": 0,
            "stage": stage
        }

    # 缺料明细
    shortage_details = []

    # 遍历BOM物料
    for bom_item in bom_items:
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        if not material:
            continue

        # 获取装配属性
        attr = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id
        ).first()

        if attr:
            stage_code = attr.assembly_stage
            is_blocking = attr.is_blocking
        else:
            # 默认分配到机械模组阶段
            stage_code = "MECH"
            is_blocking = True

        if stage_code not in stage_results:
            stage_code = "MECH"

        # 计算可用数量
        required_qty = bom_item.quantity or Decimal(1)
        stock_qty, allocated_qty, in_transit_qty, available_qty = calculate_available_qty(
            db, material.id, check_date
        )

        shortage_qty = max(Decimal(0), required_qty - available_qty)
        is_fulfilled = shortage_qty == 0
        shortage_rate = (shortage_qty / required_qty * 100) if required_qty > 0 else Decimal(0)

        # 更新阶段统计
        stage_results[stage_code]["total"] += 1
        if is_fulfilled:
            stage_results[stage_code]["fulfilled"] += 1

        if is_blocking:
            stage_results[stage_code]["blocking_total"] += 1
            if is_fulfilled:
                stage_results[stage_code]["blocking_fulfilled"] += 1

        # 记录缺料明细
        if shortage_qty > 0:
            # 计算距需求日期的天数
            days_to_required = 7  # 默认7天
            if bom_item.required_date:
                days_to_required = (bom_item.required_date - check_date).days
            
            alert_level = determine_alert_level(db, is_blocking, shortage_rate, days_to_required)
            
            # 获取预计到货日期（从采购订单）
            expected_arrival = None
            try:
                from app.models import PurchaseOrderItem, PurchaseOrder
                po_item = db.query(PurchaseOrderItem).join(
                    PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
                ).filter(
                    PurchaseOrderItem.material_id == material.id,
                    PurchaseOrder.status.in_(['approved', 'partial_received']),
                    PurchaseOrder.promised_date.isnot(None)
                ).order_by(PurchaseOrder.promised_date.asc()).first()
                
                if po_item and po_item.order and po_item.order.promised_date:
                    expected_arrival = po_item.order.promised_date
            except Exception:
                pass

            shortage_details.append({
                "bom_item_id": bom_item.id,
                "material_id": material.id,
                "material_code": material.code,
                "material_name": material.name,
                "assembly_stage": stage_code,
                "is_blocking": is_blocking,
                "required_qty": required_qty,
                "stock_qty": stock_qty,
                "allocated_qty": allocated_qty,
                "in_transit_qty": in_transit_qty,
                "available_qty": available_qty,
                "shortage_qty": shortage_qty,
                "shortage_rate": shortage_rate,
                "alert_level": alert_level,
                "expected_arrival": expected_arrival,
                "required_date": bom_item.required_date
            })

    # 计算各阶段齐套率和是否可开始
    stage_kit_rates = []
    can_proceed = True
    first_blocked_stage = None
    current_workable_stage = None
    overall_total = 0
    overall_fulfilled = 0
    blocking_total = 0
    blocking_fulfilled = 0
    all_blocking_items = []  # 收集所有阻塞物料

    for stage in stages:
        stats = stage_results.get(stage.stage_code, {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0})

        total = stats["total"]
        fulfilled = stats["fulfilled"]
        b_total = stats["blocking_total"]
        b_fulfilled = stats["blocking_fulfilled"]

        overall_total += total
        overall_fulfilled += fulfilled
        blocking_total += b_total
        blocking_fulfilled += b_fulfilled

        kit_rate = Decimal(fulfilled / total * 100) if total > 0 else Decimal(100)
        blocking_rate = Decimal(b_fulfilled / b_total * 100) if b_total > 0 else Decimal(100)

        # 判断是否可开始: 前序阶段都可开始 && 当前阶段阻塞齐套率100%
        stage_can_start = can_proceed and (blocking_rate == 100)

        if stage_can_start:
            current_workable_stage = stage.stage_code

        if not stage_can_start and can_proceed:
            first_blocked_stage = stage.stage_code
            can_proceed = False
            # 收集该阶段的阻塞物料
            for detail in shortage_details:
                if detail.get("assembly_stage") == stage.stage_code and detail.get("is_blocking"):
                    all_blocking_items.append(detail)

        stage_kit_rates.append(StageKitRate(
            stage_code=stage.stage_code,
            stage_name=stage.stage_name,
            stage_order=stage.stage_order,
            total_items=total,
            fulfilled_items=fulfilled,
            kit_rate=round(kit_rate, 2),
            blocking_total=b_total,
            blocking_fulfilled=b_fulfilled,
            blocking_rate=round(blocking_rate, 2),
            can_start=stage_can_start,
            color_code=stage.color_code
        ))

    # 计算整体齐套率
    overall_kit_rate = Decimal(overall_fulfilled / overall_total * 100) if overall_total > 0 else Decimal(100)
    blocking_kit_rate = Decimal(blocking_fulfilled / blocking_total * 100) if blocking_total > 0 else Decimal(100)
    
    # 计算预计完全齐套日期（基于阻塞物料的预计到货日期）
    estimated_ready_date = calculate_estimated_ready_date(db, all_blocking_items, check_date)

    # 创建齐套分析记录
    readiness = MaterialReadiness(
        readiness_no=generate_readiness_no(),
        project_id=request.project_id,
        machine_id=request.machine_id,
        bom_id=request.bom_id,
        planned_start_date=request.planned_start_date or project.planned_start_date,
        overall_kit_rate=round(overall_kit_rate, 2),
        blocking_kit_rate=round(blocking_kit_rate, 2),
        stage_kit_rates=json.dumps({s.stage_code: {"kit_rate": float(s.kit_rate), "blocking_rate": float(s.blocking_rate), "can_start": s.can_start} for s in stage_kit_rates}),
        total_items=overall_total,
        fulfilled_items=overall_fulfilled,
        shortage_items=len(shortage_details),
        blocking_total=blocking_total,
        blocking_fulfilled=blocking_fulfilled,
        can_start=first_blocked_stage is None,
        current_workable_stage=current_workable_stage,
        first_blocked_stage=first_blocked_stage,
        estimated_ready_date=estimated_ready_date,
        analysis_time=datetime.now(),
        analyzed_by=current_user.id
    )
    db.add(readiness)
    db.flush()

    # 创建缺料明细
    for detail in shortage_details:
        shortage = ShortageDetail(
            readiness_id=readiness.id,
            bom_item_id=detail["bom_item_id"],
            material_id=detail["material_id"],
            material_code=detail["material_code"],
            material_name=detail["material_name"],
            assembly_stage=detail["assembly_stage"],
            is_blocking=detail["is_blocking"],
            required_qty=detail["required_qty"],
            stock_qty=detail["stock_qty"],
            allocated_qty=detail["allocated_qty"],
            in_transit_qty=detail["in_transit_qty"],
            available_qty=detail["available_qty"],
            shortage_qty=detail["shortage_qty"],
            alert_level=detail["alert_level"],
            expected_arrival=detail.get("expected_arrival"),
            required_date=detail.get("required_date")
        )
        db.add(shortage)
        
        # 如果是L1或L2级别，发送企业微信预警
        if detail["alert_level"] in ["L1", "L2"]:
            try:
                from app.services.wechat_alert_service import WeChatAlertService
                WeChatAlertService.send_shortage_alert(
                    db, shortage, detail["alert_level"]
                )
            except Exception as e:
                # 预警发送失败不影响分析结果
                print(f"发送企业微信预警失败: {e}")

    db.commit()
    db.refresh(readiness)

    # 构建响应
    response_data = MaterialReadinessResponse(
        id=readiness.id,
        readiness_no=readiness.readiness_no,
        project_id=readiness.project_id,
        machine_id=readiness.machine_id,
        bom_id=readiness.bom_id,
        check_date=check_date,
        overall_kit_rate=readiness.overall_kit_rate,
        blocking_kit_rate=readiness.blocking_kit_rate,
        can_start=readiness.can_start,
        first_blocked_stage=readiness.first_blocked_stage,
        estimated_ready_date=readiness.estimated_ready_date,
        stage_kit_rates=stage_kit_rates,
        project_no=project.project_code if project else None,
        project_name=project.project_name if project else None,
        machine_no=machine.machine_code if machine else None,
        bom_no=bom.bom_no,
        analysis_time=readiness.analysis_time,
        analyzed_by=readiness.analyzed_by,
        created_at=readiness.created_at
    )

    return ResponseModel(
        code=200,
        message="齐套分析完成",
        data=response_data
    )


@router.get("/analysis/{readiness_id}/optimize", response_model=ResponseModel)
async def get_optimization_suggestions(
    readiness_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取齐套分析优化建议"""
    from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
    
    readiness = db.query(MaterialReadiness).filter(MaterialReadiness.id == readiness_id).first()
    if not readiness:
        raise HTTPException(status_code=404, detail="齐套分析记录不存在")
    
    suggestions = AssemblyKitOptimizer.generate_optimization_suggestions(db, readiness)
    optimized_date = AssemblyKitOptimizer.optimize_estimated_ready_date(db, readiness)
    
    return ResponseModel(
        code=200,
        message="优化建议获取成功",
        data={
            "suggestions": suggestions,
            "optimized_ready_date": optimized_date.isoformat() if optimized_date else None,
            "current_ready_date": readiness.estimated_ready_date.isoformat() if readiness.estimated_ready_date else None
        }
    )


@router.get("/analysis/{readiness_id}", response_model=ResponseModel)
async def get_analysis_detail(
    readiness_id: int,
    db: Session = Depends(deps.get_db)
):
    """获取齐套分析详情"""
    readiness = db.query(MaterialReadiness).filter(MaterialReadiness.id == readiness_id).first()
    if not readiness:
        raise HTTPException(status_code=404, detail="齐套分析记录不存在")

    # 获取关联信息
    project = db.query(Project).filter(Project.id == readiness.project_id).first()
    machine = db.query(Machine).filter(Machine.id == readiness.machine_id).first() if readiness.machine_id else None
    bom = db.query(BomHeader).filter(BomHeader.id == readiness.bom_id).first()

    # 获取阶段信息构建stage_kit_rates
    stages = db.query(AssemblyStage).filter(AssemblyStage.is_active == True).order_by(AssemblyStage.stage_order).all()
    stage_rates_data = readiness.stage_kit_rates or {}

    stage_kit_rates = []
    for stage in stages:
        rate_data = stage_rates_data.get(stage.stage_code, {})
        stage_kit_rates.append(StageKitRate(
            stage_code=stage.stage_code,
            stage_name=stage.stage_name,
            stage_order=stage.stage_order,
            total_items=0,
            fulfilled_items=0,
            kit_rate=Decimal(rate_data.get("kit_rate", 0)),
            blocking_total=0,
            blocking_fulfilled=0,
            blocking_rate=Decimal(rate_data.get("blocking_rate", 0)),
            can_start=rate_data.get("can_start", False),
            color_code=stage.color_code
        ))

    # 获取缺料明细
    shortage_details = db.query(ShortageDetail).filter(
        ShortageDetail.readiness_id == readiness_id
    ).all()

    shortage_responses = [ShortageDetailResponse.model_validate(s) for s in shortage_details]

    # 获取优化建议（可选）
    optimization_suggestions = None
    try:
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        optimization_suggestions = AssemblyKitOptimizer.generate_optimization_suggestions(db, readiness)
    except Exception:
        pass
    
    response_data = MaterialReadinessDetailResponse(
        id=readiness.id,
        readiness_no=readiness.readiness_no,
        project_id=readiness.project_id,
        machine_id=readiness.machine_id,
        bom_id=readiness.bom_id,
        check_date=readiness.planned_start_date or date.today(),
        overall_kit_rate=readiness.overall_kit_rate,
        blocking_kit_rate=readiness.blocking_kit_rate,
        can_start=readiness.can_start,
        first_blocked_stage=readiness.first_blocked_stage,
        estimated_ready_date=readiness.estimated_ready_date,
        stage_kit_rates=stage_kit_rates,
        project_no=project.project_code if project else None,
        project_name=project.project_name if project else None,
        machine_no=machine.machine_code if machine else None,
        bom_no=bom.bom_no if bom else None,
        analysis_time=readiness.analysis_time,
        analyzed_by=readiness.analyzed_by,
        created_at=readiness.created_at,
        shortage_details=shortage_responses
    )
    
    # 将优化建议添加到响应数据中
    if optimization_suggestions:
        # 使用dict方式返回，包含优化建议
        return ResponseModel(
            code=200,
            message="success",
            data={
                **response_data.model_dump(),
                'optimization_suggestions': optimization_suggestions
            }
        )

    return ResponseModel(code=200, message="success", data=response_data)


@router.get("/projects/{project_id}/assembly-readiness", response_model=ResponseModel)
async def get_project_readiness_list(
    project_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取项目齐套分析列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(MaterialReadiness).filter(MaterialReadiness.project_id == project_id)
    total = query.count()

    readiness_list = query.order_by(MaterialReadiness.analysis_time.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for r in readiness_list:
        bom = db.query(BomHeader).filter(BomHeader.id == r.bom_id).first()
        machine = db.query(Machine).filter(Machine.id == r.machine_id).first() if r.machine_id else None

        result.append(MaterialReadinessResponse(
            id=r.id,
            readiness_no=r.readiness_no,
            project_id=r.project_id,
            machine_id=r.machine_id,
            bom_id=r.bom_id,
            check_date=r.planned_start_date or date.today(),
            overall_kit_rate=r.overall_kit_rate,
            blocking_kit_rate=r.blocking_kit_rate,
            can_start=r.can_start,
            first_blocked_stage=r.first_blocked_stage,
            estimated_ready_date=r.estimated_ready_date,
            stage_kit_rates=[],
            project_no=project.project_code if project else None,
            project_name=project.project_name if project else None,
            machine_no=machine.machine_code if machine else None,
            bom_no=bom.bom_no if bom else None,
            analysis_time=r.analysis_time,
            analyzed_by=r.analyzed_by,
            created_at=r.created_at
        ))

    return ResponseModel(
        code=200,
        message="success",
        data={"total": total, "items": result, "page": page, "page_size": page_size}
    )


# ==================== 缺料预警 ====================

@router.get("/shortage-alerts", response_model=ResponseModel)
async def get_shortage_alerts(
    db: Session = Depends(deps.get_db),
    alert_level: Optional[str] = Query(None, description="预警级别(L1/L2/L3/L4)"),
    is_blocking: Optional[bool] = Query(None, description="是否阻塞性物料"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取缺料预警列表"""
    query = db.query(ShortageDetail).filter(ShortageDetail.shortage_qty > 0)

    if alert_level:
        query = query.filter(ShortageDetail.alert_level == alert_level)
    if is_blocking is not None:
        query = query.filter(ShortageDetail.is_blocking == is_blocking)
    if project_id:
        # 通过readiness关联项目
        readiness_ids = db.query(MaterialReadiness.id).filter(
            MaterialReadiness.project_id == project_id
        ).subquery()
        query = query.filter(ShortageDetail.readiness_id.in_(readiness_ids))

    total = query.count()

    # 统计各级别数量
    l1_count = query.filter(ShortageDetail.alert_level == "L1").count()
    l2_count = query.filter(ShortageDetail.alert_level == "L2").count()
    l3_count = query.filter(ShortageDetail.alert_level == "L3").count()
    l4_count = query.filter(ShortageDetail.alert_level == "L4").count()

    shortages = query.order_by(
        ShortageDetail.alert_level,
        ShortageDetail.is_blocking.desc(),
        ShortageDetail.shortage_rate.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    # 构建预警项
    alert_items = []
    stages = {s.stage_code: s for s in db.query(AssemblyStage).all()}

    for s in shortages:
        readiness = db.query(MaterialReadiness).filter(MaterialReadiness.id == s.readiness_id).first()
        if not readiness:
            continue

        project = db.query(Project).filter(Project.id == readiness.project_id).first()
        machine = db.query(Machine).filter(Machine.id == readiness.machine_id).first() if readiness.machine_id else None
        stage = stages.get(s.assembly_stage)

        # 获取响应时限
        rule = db.query(ShortageAlertRule).filter(ShortageAlertRule.alert_level == s.alert_level).first()
        response_hours = rule.response_deadline_hours if rule else 24

        alert_items.append(ShortageAlertItem(
            shortage_id=s.id,
            readiness_id=s.readiness_id,
            project_id=readiness.project_id,
            project_no=project.project_no if project else "",
            project_name=project.name if project else "",
            machine_id=readiness.machine_id,
            machine_no=machine.machine_no if machine else None,
            material_code=s.material_code,
            material_name=s.material_name,
            assembly_stage=s.assembly_stage,
            stage_name=stage.stage_name if stage else s.assembly_stage,
            is_blocking=s.is_blocking,
            required_qty=s.required_qty,
            shortage_qty=s.shortage_qty,
            alert_level=s.alert_level,
            expected_arrival_date=s.expected_arrival_date,
            days_to_required=7,  # 简化处理
            response_deadline=datetime.now() + timedelta(hours=response_hours)
        ))

    return ResponseModel(
        code=200,
        message="success",
        data=ShortageAlertListResponse(
            total=total,
            l1_count=l1_count,
            l2_count=l2_count,
            l3_count=l3_count,
            l4_count=l4_count,
            items=alert_items
        )
    )


# ==================== 预警规则 ====================

@router.get("/alert-rules", response_model=ResponseModel)
async def get_alert_rules(
    db: Session = Depends(deps.get_db),
    include_inactive: bool = Query(False)
):
    """获取预警规则列表"""
    query = db.query(ShortageAlertRule)
    if not include_inactive:
        query = query.filter(ShortageAlertRule.is_active == True)

    rules = query.order_by(ShortageAlertRule.alert_level).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[ShortageAlertRuleResponse.model_validate(r) for r in rules]
    )


@router.post("/alert-rules", response_model=ResponseModel)
async def create_alert_rule(
    rule_data: ShortageAlertRuleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建预警规则"""
    existing = db.query(ShortageAlertRule).filter(
        ShortageAlertRule.rule_code == rule_data.rule_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="规则编码已存在")

    rule = ShortageAlertRule(**rule_data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ResponseModel(
        code=200,
        message="创建成功",
        data=ShortageAlertRuleResponse.model_validate(rule)
    )


@router.put("/alert-rules/{rule_id}", response_model=ResponseModel)
async def update_alert_rule(
    rule_id: int,
    rule_data: ShortageAlertRuleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新预警规则"""
    rule = db.query(ShortageAlertRule).filter(ShortageAlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="预警规则不存在")

    update_data = rule_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    rule.updated_at = datetime.now()

    db.commit()
    db.refresh(rule)

    return ResponseModel(code=200, message="更新成功", data=ShortageAlertRuleResponse.model_validate(rule))


# ==================== 企业微信配置 ====================

@router.get("/wechat/config", response_model=ResponseModel)
async def get_wechat_config(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取企业微信配置（仅显示是否已配置，不返回敏感信息）"""
    from app.core.config import settings
    
    config = {
        "enabled": settings.WECHAT_ENABLED,
        "corp_id_configured": bool(settings.WECHAT_CORP_ID),
        "agent_id_configured": bool(settings.WECHAT_AGENT_ID),
        "secret_configured": bool(settings.WECHAT_SECRET),
        "fully_configured": all([
            settings.WECHAT_CORP_ID,
            settings.WECHAT_AGENT_ID,
            settings.WECHAT_SECRET
        ])
    }
    
    return ResponseModel(
        code=200,
        message="success",
        data=config
    )


@router.post("/wechat/test", response_model=ResponseModel)
async def test_wechat_connection(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """测试企业微信连接"""
    from app.utils.wechat_client import WeChatClient
    from app.core.config import settings
    
    if not settings.WECHAT_ENABLED:
        raise HTTPException(status_code=400, detail="企业微信功能未启用")
    
    try:
        client = WeChatClient()
        token = client.get_access_token()
        
        return ResponseModel(
            code=200,
            message="企业微信连接成功",
            data={"access_token_obtained": bool(token)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"配置不完整: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


# ==================== 排产建议 ====================

@router.post("/suggestions/generate", response_model=ResponseModel)
async def generate_scheduling_suggestions(
    db: Session = Depends(deps.get_db),
    scope: str = Query("WEEKLY", description="排产范围：WEEKLY/MONTHLY"),
    project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔")
):
    """生成智能排产建议"""
    from app.services.scheduling_suggestion_service import SchedulingSuggestionService
    
    project_id_list = None
    if project_ids:
        project_id_list = [int(x.strip()) for x in project_ids.split(",") if x.strip().isdigit()]
    
    suggestions = SchedulingSuggestionService.generate_scheduling_suggestions(
        db, scope=scope, project_ids=project_id_list
    )
    
    return ResponseModel(
        code=200,
        message="排产建议生成成功",
        data={"suggestions": suggestions, "total": len(suggestions)}
    )


@router.get("/suggestions", response_model=ResponseModel)
async def get_scheduling_suggestions(
    db: Session = Depends(deps.get_db),
    status: Optional[str] = Query(None, description="状态筛选"),
    project_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取排产建议列表"""
    query = db.query(SchedulingSuggestion)

    if status:
        query = query.filter(SchedulingSuggestion.status == status)
    if project_id:
        query = query.filter(SchedulingSuggestion.project_id == project_id)

    total = query.count()
    suggestions = query.order_by(
        SchedulingSuggestion.priority_score.desc(),
        SchedulingSuggestion.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for s in suggestions:
        project = db.query(Project).filter(Project.id == s.project_id).first()
        machine = db.query(Machine).filter(Machine.id == s.machine_id).first() if s.machine_id else None

        data = SchedulingSuggestionResponse.model_validate(s)
        data.project_no = project.project_no if project else None
        data.project_name = project.name if project else None
        data.machine_no = machine.machine_no if machine else None
        result.append(data)

    return ResponseModel(
        code=200,
        message="success",
        data={"total": total, "items": result, "page": page, "page_size": page_size}
    )


@router.post("/suggestions/{suggestion_id}/accept", response_model=ResponseModel)
async def accept_suggestion(
    suggestion_id: int,
    accept_data: SchedulingSuggestionAccept,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """接受排产建议"""
    suggestion = db.query(SchedulingSuggestion).filter(SchedulingSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="排产建议不存在")

    if suggestion.status != "pending":
        raise HTTPException(status_code=400, detail="该建议已处理")

    suggestion.status = "accepted"
    suggestion.accepted_by = current_user.id
    suggestion.accepted_at = datetime.now()
    if accept_data.actual_start_date:
        suggestion.suggested_start_date = accept_data.actual_start_date
    suggestion.updated_at = datetime.now()

    db.commit()
    db.refresh(suggestion)

    return ResponseModel(code=200, message="已接受建议", data=SchedulingSuggestionResponse.model_validate(suggestion))


@router.post("/suggestions/{suggestion_id}/reject", response_model=ResponseModel)
async def reject_suggestion(
    suggestion_id: int,
    reject_data: SchedulingSuggestionReject,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """拒绝排产建议"""
    suggestion = db.query(SchedulingSuggestion).filter(SchedulingSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="排产建议不存在")

    if suggestion.status != "pending":
        raise HTTPException(status_code=400, detail="该建议已处理")

    suggestion.status = "rejected"
    suggestion.reject_reason = reject_data.reject_reason
    suggestion.updated_at = datetime.now()

    db.commit()
    db.refresh(suggestion)

    return ResponseModel(code=200, message="已拒绝建议", data=SchedulingSuggestionResponse.model_validate(suggestion))


# ==================== 看板 ====================

@router.get("/dashboard", response_model=ResponseModel)
async def get_assembly_dashboard(
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔")
):
    """获取装配齐套看板数据"""
    # 获取最近的齐套分析记录(每个项目取最新一条)
    subquery = db.query(
        MaterialReadiness.project_id,
        func.max(MaterialReadiness.id).label("max_id")
    ).group_by(MaterialReadiness.project_id).subquery()

    query = db.query(MaterialReadiness).join(
        subquery,
        and_(
            MaterialReadiness.project_id == subquery.c.project_id,
            MaterialReadiness.id == subquery.c.max_id
        )
    )

    if project_ids:
        ids = [int(x) for x in project_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(MaterialReadiness.project_id.in_(ids))

    recent_analyses = query.all()

    if not recent_analyses:
        return ResponseModel(
            code=200,
            message="success",
            data=AssemblyDashboardResponse(
                stats=AssemblyDashboardStats(
                    total_projects=0,
                    can_start_count=0,
                    partial_ready_count=0,
                    not_ready_count=0,
                    avg_kit_rate=Decimal(0),
                    avg_blocking_rate=Decimal(0)
                ),
                stage_stats=[],
                alert_summary={"L1": 0, "L2": 0, "L3": 0, "L4": 0},
                recent_analyses=[],
                pending_suggestions=[]
            )
        )

    # 统计
    total_projects = len(recent_analyses)
    can_start_count = sum(1 for r in recent_analyses if r.can_start)
    not_ready_count = sum(1 for r in recent_analyses if r.blocking_kit_rate < 50)
    partial_ready_count = total_projects - can_start_count - not_ready_count

    avg_kit_rate = sum(r.overall_kit_rate for r in recent_analyses) / total_projects if total_projects > 0 else Decimal(0)
    avg_blocking_rate = sum(r.blocking_kit_rate for r in recent_analyses) / total_projects if total_projects > 0 else Decimal(0)

    # 分阶段统计
    stages = db.query(AssemblyStage).filter(AssemblyStage.is_active == True).order_by(AssemblyStage.stage_order).all()
    stage_stats = []
    for stage in stages:
        can_start = 0
        blocked = 0
        total_rate = Decimal(0)

        for r in recent_analyses:
            stage_rates = r.stage_kit_rates or {}
            rate_info = stage_rates.get(stage.stage_code, {})
            if rate_info.get("can_start", False):
                can_start += 1
            else:
                blocked += 1
            total_rate += Decimal(rate_info.get("kit_rate", 0))

        stage_stats.append(AssemblyDashboardStageStats(
            stage_code=stage.stage_code,
            stage_name=stage.stage_name,
            can_start_count=can_start,
            blocked_count=blocked,
            avg_kit_rate=round(total_rate / total_projects, 2) if total_projects > 0 else Decimal(0)
        ))

    # 预警汇总
    alert_summary = {
        "L1": db.query(ShortageDetail).filter(ShortageDetail.alert_level == "L1", ShortageDetail.shortage_qty > 0).count(),
        "L2": db.query(ShortageDetail).filter(ShortageDetail.alert_level == "L2", ShortageDetail.shortage_qty > 0).count(),
        "L3": db.query(ShortageDetail).filter(ShortageDetail.alert_level == "L3", ShortageDetail.shortage_qty > 0).count(),
        "L4": db.query(ShortageDetail).filter(ShortageDetail.alert_level == "L4", ShortageDetail.shortage_qty > 0).count(),
    }

    # 构建响应数据
    recent_list = []
    for r in recent_analyses[:10]:  # 只返回最近10条
        project = db.query(Project).filter(Project.id == r.project_id).first()
        bom = db.query(BomHeader).filter(BomHeader.id == r.bom_id).first()
        machine = db.query(Machine).filter(Machine.id == r.machine_id).first() if r.machine_id else None

        recent_list.append(MaterialReadinessResponse(
            id=r.id,
            readiness_no=r.readiness_no,
            project_id=r.project_id,
            machine_id=r.machine_id,
            bom_id=r.bom_id,
            check_date=r.planned_start_date or date.today(),
            overall_kit_rate=r.overall_kit_rate,
            blocking_kit_rate=r.blocking_kit_rate,
            can_start=r.can_start,
            first_blocked_stage=r.first_blocked_stage,
            estimated_ready_date=r.estimated_ready_date,
            stage_kit_rates=[],
            project_no=project.project_code if project else None,
            project_name=project.project_name if project else None,
            machine_no=machine.machine_code if machine else None,
            bom_no=bom.bom_no if bom else None,
            analysis_time=r.analysis_time,
            analyzed_by=r.analyzed_by,
            created_at=r.created_at
        ))

    # 待处理建议
    pending_suggestions = db.query(SchedulingSuggestion).filter(
        SchedulingSuggestion.status == "pending"
    ).order_by(SchedulingSuggestion.priority_score.desc()).limit(5).all()

    suggestion_list = []
    for s in pending_suggestions:
        project = db.query(Project).filter(Project.id == s.project_id).first()
        machine = db.query(Machine).filter(Machine.id == s.machine_id).first() if s.machine_id else None

        data = SchedulingSuggestionResponse.model_validate(s)
        data.project_no = project.project_no if project else None
        data.project_name = project.name if project else None
        data.machine_no = machine.machine_no if machine else None
        suggestion_list.append(data)

    return ResponseModel(
        code=200,
        message="success",
        data=AssemblyDashboardResponse(
            stats=AssemblyDashboardStats(
                total_projects=total_projects,
                can_start_count=can_start_count,
                partial_ready_count=partial_ready_count,
                not_ready_count=not_ready_count,
                avg_kit_rate=round(avg_kit_rate, 2),
                avg_blocking_rate=round(avg_blocking_rate, 2)
            ),
            stage_stats=stage_stats,
            alert_summary=alert_summary,
            recent_analyses=recent_list,
            pending_suggestions=suggestion_list
        )
    )


# ==================== 装配模板管理 ====================

@router.get("/templates", response_model=ResponseModel)
async def get_assembly_templates(
    db: Session = Depends(deps.get_db),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    include_inactive: bool = Query(False)
):
    """获取装配模板列表"""
    query = db.query(AssemblyTemplate)
    if equipment_type:
        query = query.filter(AssemblyTemplate.equipment_type == equipment_type)
    if not include_inactive:
        query = query.filter(AssemblyTemplate.is_active == True)

    templates = query.order_by(AssemblyTemplate.is_default.desc(), AssemblyTemplate.created_at.desc()).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[AssemblyTemplateResponse.model_validate(t) for t in templates]
    )


@router.post("/templates", response_model=ResponseModel)
async def create_assembly_template(
    template_data: AssemblyTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建装配模板"""
    existing = db.query(AssemblyTemplate).filter(
        AssemblyTemplate.template_code == template_data.template_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = AssemblyTemplate(**template_data.model_dump(), created_by=current_user.id)
    db.add(template)
    db.commit()
    db.refresh(template)

    return ResponseModel(
        code=200,
        message="创建成功",
        data=AssemblyTemplateResponse.model_validate(template)
    )


@router.put("/templates/{template_id}", response_model=ResponseModel)
async def update_assembly_template(
    template_id: int,
    template_data: AssemblyTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新装配模板"""
    template = db.query(AssemblyTemplate).filter(AssemblyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    update_data = template_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    template.updated_at = datetime.now()

    db.commit()
    db.refresh(template)

    return ResponseModel(code=200, message="更新成功", data=AssemblyTemplateResponse.model_validate(template))


@router.delete("/templates/{template_id}", response_model=MessageResponse)
async def delete_assembly_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """删除装配模板"""
    template = db.query(AssemblyTemplate).filter(AssemblyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 软删除
    template.is_active = False
    template.updated_at = datetime.now()
    db.commit()

    return MessageResponse(code=200, message="删除成功")
