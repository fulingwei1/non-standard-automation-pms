# -*- coding: utf-8 -*-
"""
统一齐套率查询端点

整合三种齐套率计算方式:
1. kit_rate: 按数量/金额比例计算
2. kit_check: 按物料项计数计算（二值化）
3. assembly_kit: 按装配阶段计算（含阻塞物料）

返回统一的响应格式，便于前端展示和对比
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project
from app.services.kit_rate import KitRateService
from app.models.user import User

router = APIRouter()


def _get_stage_kit_rate(db: Session, project_id: int, machine_id: Optional[int] = None) -> Dict[str, Any]:
    """
    获取基于装配阶段的齐套率（工艺齐套率）

    整合自 assembly_kit 模块的计算逻辑
    """
    try:
        import json

        from app.models import AssemblyStage, MaterialReadiness, ShortageDetail

        # 查询物料齐套状态（取最新一次分析）
        query = db.query(MaterialReadiness).filter(
            MaterialReadiness.project_id == project_id
        )
        if machine_id:
            query = query.filter(MaterialReadiness.machine_id == machine_id)

        readiness = query.order_by(MaterialReadiness.analysis_time.desc()).first()

        if not readiness:
            return {
                "method": "stage_based",
                "description": "工艺齐套率（按装配阶段）",
                "available": False,
                "message": "未找到物料齐套数据，请先执行齐套分析",
            }

        stages = db.query(AssemblyStage).all()
        stages_sorted = sorted(stages, key=lambda s: s.stage_order or 0)
        stage_map = {s.stage_code: s for s in stages_sorted}

        stage_rates = {}
        if readiness.stage_kit_rates:
            if isinstance(readiness.stage_kit_rates, str):
                try:
                    stage_rates = json.loads(readiness.stage_kit_rates)
                except json.JSONDecodeError:
                    stage_rates = {}
            elif isinstance(readiness.stage_kit_rates, dict):
                stage_rates = readiness.stage_kit_rates

        stage_stats = []
        for stage in stages_sorted:
            rate_info = stage_rates.get(stage.stage_code, {}) if stage_rates else {}
            kit_rate = rate_info.get("kit_rate")
            stage_stats.append(
                {
                    "stage_code": stage.stage_code,
                    "stage_name": stage.stage_name,
                    "kit_rate": round(float(kit_rate), 2) if kit_rate is not None else 100.0,
                }
            )

        if not stage_stats:
            # 兜底：用缺料明细估算（仅缺料项）
            shortages = db.query(ShortageDetail).filter(
                ShortageDetail.readiness_id == readiness.id
            ).all()
            stage_map = {s.stage_code: s for s in stages_sorted}
            shortage_stats = {}
            for shortage in shortages:
                stage_code = shortage.assembly_stage or "UNKNOWN"
                if stage_code not in shortage_stats:
                    shortage_stats[stage_code] = {
                        "stage_code": stage_code,
                        "stage_name": stage_map.get(stage_code).stage_name
                        if stage_map.get(stage_code)
                        else stage_code,
                        "total_items": 0,
                        "shortage_items": 0,
                    }
                shortage_stats[stage_code]["total_items"] += 1
                if shortage.shortage_qty and shortage.shortage_qty > 0:
                    shortage_stats[stage_code]["shortage_items"] += 1

            for stats in shortage_stats.values():
                if stats["total_items"] > 0:
                    stats["kit_rate"] = round(
                        (stats["total_items"] - stats["shortage_items"])
                        / stats["total_items"]
                        * 100,
                        2,
                    )
                stage_stats.append(
                    {
                        "stage_code": stats["stage_code"],
                        "stage_name": stats["stage_name"],
                        "kit_rate": stats.get("kit_rate", 0),
                    }
                )

        blocking_shortage_count = max(
            (readiness.blocking_total or 0) - (readiness.blocking_fulfilled or 0), 0
        )

        return {
            "method": "stage_based",
            "description": "工艺齐套率（按装配阶段）",
            "available": True,
            "overall_kit_rate": float(readiness.overall_kit_rate or 0),
            "total_items": readiness.total_items or 0,
            "fulfilled_items": readiness.fulfilled_items or 0,
            "blocking_shortage_count": blocking_shortage_count,
            "stages": stage_stats,
        }

    except Exception as e:
        return {
            "method": "stage_based",
            "description": "工艺齐套率（按装配阶段）",
            "available": False,
            "message": f"计算失败: {str(e)}",
        }


@router.get("/kit-rates/unified/{project_id}")
def get_unified_kit_rates(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    machine_id: Optional[int] = Query(None, description="机台ID（可选，不传则计算项目级）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    统一齐套率查询

    同时返回三种齐套率计算结果:
    - quantity_based: 按数量比例计算的齐套率
    - item_count_based: 按物料项计数的齐套率
    - stage_based: 按装配阶段的工艺齐套率

    这三种方法各有适用场景:
    - quantity_based: 适合整体物料保障评估
    - item_count_based: 适合开工前齐套检查
    - stage_based: 适合装配过程管控（需先配置装配阶段）
    """
    # 验证项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = KitRateService(db)
    bom_items = []
    if machine_id:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")
        bom_items = service.list_bom_items_for_machine(machine_id)
    else:
        # 项目级：获取所有机台的BOM
        bom_items = service.list_bom_items_for_project(project_id)

    # 1. 按数量计算的齐套率
    quantity_result = service.calculate_kit_rate(bom_items, calculate_by="quantity")
    quantity_kit_rate = {
        "method": "quantity_based",
        "description": "按数量比例计算的齐套率",
        "available": len(bom_items) > 0,
        **quantity_result,
    }

    # 2. 按金额计算的齐套率
    amount_result = service.calculate_kit_rate(bom_items, calculate_by="amount")
    amount_kit_rate = {
        "method": "amount_based",
        "description": "按金额比例计算的齐套率",
        "available": len(bom_items) > 0,
        **amount_result,
    }

    # 3. 按项目计数的齐套率（简化版）
    item_count_kit_rate = {
        "method": "item_count_based",
        "description": "按物料项计数的齐套率",
        "available": len(bom_items) > 0,
        "total_items": quantity_result["total_items"],
        "fulfilled_items": quantity_result["fulfilled_items"],
        "shortage_items": quantity_result["shortage_items"],
        "in_transit_items": quantity_result["in_transit_items"],
        "kit_rate": round(
            quantity_result["fulfilled_items"] / quantity_result["total_items"] * 100, 2
        ) if quantity_result["total_items"] > 0 else 0.0,
        "kit_status": quantity_result["kit_status"],
    }

    # 4. 按装配阶段的齐套率
    stage_kit_rate = _get_stage_kit_rate(db, project_id, machine_id)

    return {
        "project_id": project_id,
        "project_no": project.project_code,
        "project_name": project.project_name,
        "machine_id": machine_id,
        "calculation_methods": {
            "quantity_based": quantity_kit_rate,
            "amount_based": amount_kit_rate,
            "item_count_based": item_count_kit_rate,
            "stage_based": stage_kit_rate,
        },
        "summary": {
            "recommended_method": "stage_based" if stage_kit_rate.get("available") else "quantity_based",
            "primary_kit_rate": stage_kit_rate.get("overall_kit_rate") if stage_kit_rate.get("available") else quantity_kit_rate.get("kit_rate"),
            "has_blocking_shortage": stage_kit_rate.get("blocking_shortage_count", 0) > 0,
        },
    }


@router.get("/kit-rates/comparison")
def compare_project_kit_rates(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: str = Query(..., description="项目ID列表，逗号分隔"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    多项目齐套率对比

    对比多个项目的齐套率，便于PMC整体管控
    """
    try:
        ids = [int(id.strip()) for id in project_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的项目ID格式")

    if len(ids) > 10:
        raise HTTPException(status_code=400, detail="最多支持10个项目同时对比")

    service = KitRateService(db)
    results = []
    for project_id in ids:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            continue

        # 获取项目所有机台的BOM
        bom_items = service.list_bom_items_for_project(project_id)

        # 按数量计算的齐套率
        quantity_result = service.calculate_kit_rate(bom_items, calculate_by="quantity")

        # 按阶段计算的齐套率
        stage_result = _get_stage_kit_rate(db, project_id)

        results.append({
            "project_id": project_id,
            "project_no": project.project_code,
            "project_name": project.project_name,
            "quantity_kit_rate": quantity_result.get("kit_rate", 0),
            "stage_kit_rate": stage_result.get("overall_kit_rate") if stage_result.get("available") else None,
            "kit_status": quantity_result.get("kit_status", "unknown"),
            "total_items": quantity_result.get("total_items", 0),
            "shortage_items": quantity_result.get("shortage_items", 0),
            "has_blocking_shortage": stage_result.get("blocking_shortage_count", 0) > 0 if stage_result.get("available") else False,
        })

    # 按齐套率排序
    results.sort(key=lambda x: x.get("quantity_kit_rate", 0))

    return {
        "total_projects": len(results),
        "projects": results,
        "statistics": {
            "complete_count": len([r for r in results if r.get("kit_status") == "complete"]),
            "partial_count": len([r for r in results if r.get("kit_status") == "partial"]),
            "shortage_count": len([r for r in results if r.get("kit_status") == "shortage"]),
            "avg_kit_rate": round(sum(r.get("quantity_kit_rate", 0) for r in results) / len(results), 2) if results else 0,
        },
    }
