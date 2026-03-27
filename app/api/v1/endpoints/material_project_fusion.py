# -*- coding: utf-8 -*-
"""
项目管理 × 物料管理 深度融合端点

端点:
- POST /material/goods-received-project-sync   物料到货自动更新项目齐套率
- POST /material/shortage-to-project-risk       缺料自动创建项目风险
- GET  /projects/{id}/material-status           项目物料齐套率看板
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app.core.schemas.response import error_response, success_response
from app.dependencies import get_db
from app.models.material import BomHeader, BomItem, Material, MaterialShortage
from app.models.notification import Notification
from app.models.project.core import Project
from app.models.project.lifecycle import ProjectStatusLog
from app.models.project_risk import ProjectRisk, RiskStatusEnum, RiskTypeEnum
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)

router = APIRouter()  # POST endpoints under /material prefix
project_router = APIRouter()  # GET endpoint under /projects prefix
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _dec(v: Any) -> Decimal:
    if v is None:
        return Decimal("0")
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def _calc_project_kitting(db: Session, project_id: int) -> Dict[str, Any]:
    """
    计算项目齐套率（与 kitting_analysis 一致的逻辑）。
    返回 {kitting_rate, total_items, kitted_items, shortage_items, shortage_details}
    """
    bom_items = (
        db.query(BomItem)
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .filter(
            BomHeader.project_id == project_id,
            BomHeader.status != "DRAFT",
            BomHeader.is_latest.is_(True),
        )
        .all()
    )

    if not bom_items:
        return {
            "kitting_rate": Decimal("0"),
            "total_items": 0,
            "kitted_items": 0,
            "shortage_items": 0,
            "shortage_details": [],
        }

    total = len(bom_items)
    kitted = 0
    shortages: List[Dict[str, Any]] = []

    # 批量加载库存
    mat_ids = [bi.material_id for bi in bom_items if bi.material_id]
    stock_map: Dict[int, Decimal] = {}
    if mat_ids:
        rows = (
            db.query(Material.id, Material.current_stock)
            .filter(Material.id.in_(set(mat_ids)))
            .all()
        )
        stock_map = {r[0]: _dec(r[1]) for r in rows}

    for bi in bom_items:
        required = _dec(bi.quantity)
        received = _dec(bi.received_qty)
        stock = stock_map.get(bi.material_id, Decimal("0")) if bi.material_id else Decimal("0")
        available = received + stock

        if available >= required:
            kitted += 1
            # 同步 BomItem 齐套状态
            if bi.kitting_status != "COMPLETE":
                bi.kitting_status = "COMPLETE"
        else:
            shortage_qty = required - available
            purchased = _dec(bi.purchased_qty)
            in_transit = max(Decimal("0"), purchased - received)

            # 齐套状态
            if purchased > 0 or received > 0:
                bi.kitting_status = "IN_PROGRESS" if in_transit > 0 else "SHORTAGE"
            else:
                bi.kitting_status = "SHORTAGE" if required > 0 else "PENDING"

            shortages.append({
                "bom_item_id": bi.id,
                "material_id": bi.material_id,
                "material_code": bi.material_code,
                "material_name": bi.material_name,
                "specification": bi.specification,
                "required_qty": float(required),
                "received_qty": float(received),
                "available_qty": float(available),
                "shortage_qty": float(shortage_qty),
                "in_transit_qty": float(in_transit),
                "is_key_item": bi.is_key_item,
                "expected_arrival_date": (
                    bi.expected_arrival_date.isoformat() if bi.expected_arrival_date else None
                ),
            })

    rate = round(Decimal(kitted) / Decimal(total) * 100, 1) if total else Decimal("0")

    return {
        "kitting_rate": rate,
        "total_items": total,
        "kitted_items": kitted,
        "shortage_items": total - kitted,
        "shortage_details": shortages,
    }


def _derive_material_status(kitting_rate: Decimal, shortage_count: int, has_purchased: bool) -> str:
    """根据齐套率推导物料状态"""
    if kitting_rate >= 100:
        return "齐套"
    if shortage_count > 0 and kitting_rate < 50:
        return "缺料"
    if kitting_rate > 0:
        return "部分到货"
    if has_purchased:
        return "采购中"
    return "待采购"


def _generate_risk_code(db: Session) -> str:
    """生成风险编号 RSK-YYYYMMDD-NNN"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"RSK-{today}-"
    last = (
        db.query(ProjectRisk.risk_code)
        .filter(ProjectRisk.risk_code.like(f"{prefix}%"))
        .order_by(ProjectRisk.risk_code.desc())
        .first()
    )
    if last and last[0]:
        try:
            seq = int(last[0].split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


# ---------------------------------------------------------------------------
# 1. 物料到货自动更新项目 (Phase 2)
# ---------------------------------------------------------------------------

@router.post("/goods-received-project-sync")
def goods_received_project_sync(
    receipt_id: int = Query(..., description="收货单ID"),
    db: Session = Depends(get_db),
):
    """
    物料入库自动计算项目齐套率

    - 更新 BomItem 到货数量和齐套状态
    - 重算 Project.kitting_rate / material_status / shortage_items_count
    - 齐套率变化时记录 ProjectStatusLog
    - 齐套率 < 90% 自动标记项目健康度为警告(H2)
    """

    # 1. 查收货单
    receipt = (
        db.query(GoodsReceipt)
        .options(joinedload(GoodsReceipt.order))
        .filter(GoodsReceipt.id == receipt_id)
        .first()
    )
    if not receipt:
        return error_response("收货单不存在", code=404)

    order = receipt.order
    if not order or not order.project_id:
        return error_response("收货单未关联项目", code=400)

    project = db.query(Project).filter(Project.id == order.project_id).first()
    if not project:
        return error_response("项目不存在", code=404)

    old_kitting_rate = float(project.kitting_rate or 0)
    old_health = project.health

    # 2. 更新 BomItem 到货数量 & 实际到货日期
    receipt_items = (
        db.query(GoodsReceiptItem)
        .filter(GoodsReceiptItem.receipt_id == receipt_id)
        .all()
    )
    updated_bom_count = 0
    for ri in receipt_items:
        if not ri.order_item_id:
            continue
        oi = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == ri.order_item_id).first()
        if not oi or not oi.bom_item_id:
            continue
        bom_item = db.query(BomItem).filter(BomItem.id == oi.bom_item_id).first()
        if not bom_item:
            continue
        bom_item.received_qty = _dec(bom_item.received_qty) + _dec(ri.qualified_qty)
        bom_item.actual_arrival_date = date.today()
        updated_bom_count += 1

    # 3. 重算项目齐套率
    kitting = _calc_project_kitting(db, project.id)
    new_rate = float(kitting["kitting_rate"])

    # 判断是否有采购中的物料
    has_purchased = (
        db.query(BomItem.id)
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .filter(
            BomHeader.project_id == project.id,
            BomItem.purchased_qty > 0,
        )
        .first()
        is not None
    )

    project.kitting_rate = kitting["kitting_rate"]
    project.shortage_items_count = kitting["shortage_items"]
    project.material_status = _derive_material_status(
        kitting["kitting_rate"], kitting["shortage_items"], has_purchased
    )

    # 4. 齐套率 < 90% → 项目健康度警告
    new_health = old_health
    if new_rate < 90 and project.health == "H1":
        project.health = "H2"
        new_health = "H2"
    elif new_rate >= 100 and project.health == "H2":
        # 齐套后恢复健康
        project.health = "H1"
        new_health = "H1"

    # 5. 齐套率变化时记录日志
    rate_changed = abs(new_rate - old_kitting_rate) > 0.05
    health_changed = new_health != old_health
    if rate_changed or health_changed:
        log = ProjectStatusLog(
            project_id=project.id,
            old_health=old_health,
            new_health=new_health,
            change_type="HEALTH_CHANGE" if health_changed else "STATUS_CHANGE",
            change_reason=(
                f"物料到货更新齐套率: {old_kitting_rate}% → {new_rate}%"
            ),
            change_note=f"收货单: {receipt.receipt_no}",
            changed_at=datetime.now(),
        )
        db.add(log)

    # 6. 通知项目经理
    if project.pm_id:
        notif = Notification(
            user_id=project.pm_id,
            notification_type="KITTING_UPDATE",
            source_type="goods_receipt",
            source_id=receipt_id,
            title=f"项目齐套率更新 - {project.project_code}",
            content=(
                f"项目 {project.project_name} 齐套率: {old_kitting_rate}% → {new_rate}%。"
                f"缺料项: {kitting['shortage_items']}。"
                f"物料状态: {project.material_status}。"
            ),
            priority="HIGH" if new_rate < 90 else "NORMAL",
        )
        db.add(notif)

    db.commit()

    return success_response(
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "receipt_id": receipt_id,
            "receipt_no": receipt.receipt_no,
            "bom_items_updated": updated_bom_count,
            "kitting_rate_before": old_kitting_rate,
            "kitting_rate_after": new_rate,
            "material_status": project.material_status,
            "shortage_items_count": kitting["shortage_items"],
            "health_before": old_health,
            "health_after": new_health,
            "status_log_created": rate_changed or health_changed,
        },
        message=f"项目齐套率已更新: {new_rate}%",
    )


# ---------------------------------------------------------------------------
# 2. 缺料自动创建项目风险 (Phase 2)
# ---------------------------------------------------------------------------

@router.post("/shortage-to-project-risk")
def shortage_to_project_risk(
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
):
    """
    识别缺料项，自动创建项目风险记录

    - 识别缺料项（BOM需求 - 已到货 < 0）
    - 按影响程度判定风险等级
    - 创建 ProjectRisk 记录
    - 通知项目经理
    """

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return error_response("项目不存在", code=404)

    # 计算缺料
    kitting = _calc_project_kitting(db, project_id)
    shortages = kitting["shortage_details"]

    if not shortages:
        return success_response(
            data={"project_id": project_id, "risks_created": 0, "message": "无缺料项"},
            message="项目物料齐套，无需创建风险",
        )

    # 按缺料严重程度分组
    created_risks: List[Dict[str, Any]] = []

    for s in shortages:
        shortage_ratio = s["shortage_qty"] / s["required_qty"] if s["required_qty"] > 0 else 1

        # 判定风险等级
        if s["is_key_item"] or shortage_ratio >= 0.8:
            probability, impact, risk_level = 5, 5, "CRITICAL"
        elif shortage_ratio >= 0.5:
            probability, impact, risk_level = 4, 4, "HIGH"
        elif shortage_ratio >= 0.2:
            probability, impact, risk_level = 3, 3, "MEDIUM"
        else:
            probability, impact, risk_level = 2, 2, "LOW"

        # 检查是否已有该物料的未关闭风险
        existing = (
            db.query(ProjectRisk)
            .filter(
                ProjectRisk.project_id == project_id,
                ProjectRisk.risk_type == RiskTypeEnum.SCHEDULE,
                ProjectRisk.status != RiskStatusEnum.CLOSED,
                ProjectRisk.description.contains(s["material_code"]),
            )
            .first()
        )
        if existing:
            # 更新已有风险等级
            existing.probability = probability
            existing.impact = impact
            existing.risk_score = probability * impact
            existing.risk_level = risk_level
            existing.description = (
                f"物料缺料风险: {s['material_code']} {s['material_name']}，"
                f"缺口: {s['shortage_qty']}/{s['required_qty']}，"
                f"在途: {s['in_transit_qty']}"
            )
            created_risks.append({
                "risk_id": existing.id,
                "risk_code": existing.risk_code,
                "action": "updated",
                "material_code": s["material_code"],
                "risk_level": risk_level,
            })
            continue

        # 创建新风险
        risk = ProjectRisk(
            risk_code=_generate_risk_code(db),
            project_id=project_id,
            risk_name=f"物料缺料 - {s['material_code']} {s['material_name']}",
            description=(
                f"物料缺料风险: {s['material_code']} {s['material_name']}，"
                f"规格: {s.get('specification', '-')}，"
                f"需求: {s['required_qty']}，可用: {s['available_qty']}，"
                f"缺口: {s['shortage_qty']}，在途: {s['in_transit_qty']}。"
                f"预计到货: {s.get('expected_arrival_date', '未知')}。"
            ),
            risk_type=RiskTypeEnum.SCHEDULE,
            probability=probability,
            impact=impact,
            risk_score=probability * impact,
            risk_level=risk_level,
            mitigation_plan=(
                f"加急采购缺口物料 {s['shortage_qty']} {s.get('specification', '')}，"
                f"联系供应商确认交期，必要时寻找替代料。"
            ),
            status=RiskStatusEnum.IDENTIFIED,
            identified_date=datetime.now(),
        )
        db.add(risk)
        db.flush()

        created_risks.append({
            "risk_id": risk.id,
            "risk_code": risk.risk_code,
            "action": "created",
            "material_code": s["material_code"],
            "material_name": s["material_name"],
            "shortage_qty": s["shortage_qty"],
            "risk_level": risk_level,
            "risk_score": probability * impact,
        })

    # 通知项目经理
    if project.pm_id and created_risks:
        new_count = sum(1 for r in created_risks if r["action"] == "created")
        updated_count = sum(1 for r in created_risks if r["action"] == "updated")
        critical_count = sum(1 for r in created_risks if r["risk_level"] == "CRITICAL")

        notif = Notification(
            user_id=project.pm_id,
            notification_type="SHORTAGE_RISK",
            source_type="project_risk",
            source_id=project_id,
            title=f"缺料风险提醒 - {project.project_code}",
            content=(
                f"项目 {project.project_name} 检测到 {len(created_risks)} 项缺料风险"
                f"（新增{new_count}项, 更新{updated_count}项）。"
                + (f"其中{critical_count}项为极高风险，请优先处理。" if critical_count else "")
            ),
            priority="HIGH" if critical_count > 0 else "NORMAL",
        )
        db.add(notif)

    db.commit()

    return success_response(
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "total_shortage_items": len(shortages),
            "risks_created": sum(1 for r in created_risks if r["action"] == "created"),
            "risks_updated": sum(1 for r in created_risks if r["action"] == "updated"),
            "risks": created_risks,
        },
        message=f"已处理 {len(created_risks)} 项缺料风险",
    )


# ---------------------------------------------------------------------------
# 3. 项目物料齐套率看板 (Phase 3)
# ---------------------------------------------------------------------------

@project_router.get("/{project_id}/material-status")
def get_project_material_status(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db),
):
    """
    项目物料齐套率看板

    - 项目物料齐套率概览
    - 缺料明细（物料/数量/预计到货）
    - 物料进度对项目交付的影响
    - 建议措施
    """

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return error_response("项目不存在", code=404)

    # 1. 齐套率计算
    kitting = _calc_project_kitting(db, project_id)
    shortages = kitting["shortage_details"]

    # 2. 按 BOM 维度统计
    bom_stats = []
    bom_rows = (
        db.query(BomHeader)
        .filter(
            BomHeader.project_id == project_id,
            BomHeader.status != "DRAFT",
            BomHeader.is_latest.is_(True),
        )
        .all()
    )
    for bom in bom_rows:
        items = bom.items.all()
        if not items:
            continue
        total = len(items)
        complete = sum(1 for i in items if _dec(i.received_qty) >= _dec(i.quantity))
        rate = round(complete / total * 100, 1) if total else 0
        bom_stats.append({
            "bom_id": bom.id,
            "bom_no": bom.bom_no,
            "bom_name": bom.bom_name,
            "machine_id": bom.machine_id,
            "total_items": total,
            "kitted_items": complete,
            "shortage_items": total - complete,
            "kitting_rate": rate,
        })

    # 3. 关键缺料（关键物料优先）
    key_shortages = sorted(
        shortages,
        key=lambda x: (not x["is_key_item"], -x["shortage_qty"]),
    )

    # 4. 交付影响评估
    today = date.today()
    planned_end = project.planned_end_date
    delivery_impact = {
        "project_planned_end": planned_end.isoformat() if planned_end else None,
        "kitting_rate": float(kitting["kitting_rate"]),
        "risk_level": "LOW",
        "impact_description": "",
    }

    rate_val = float(kitting["kitting_rate"])
    if rate_val >= 100:
        delivery_impact["risk_level"] = "NONE"
        delivery_impact["impact_description"] = "物料齐套，不影响交付"
    elif rate_val >= 90:
        delivery_impact["risk_level"] = "LOW"
        delivery_impact["impact_description"] = (
            f"齐套率 {rate_val}%，少量缺料({kitting['shortage_items']}项)，"
            f"预计对交付影响较小"
        )
    elif rate_val >= 60:
        delivery_impact["risk_level"] = "MEDIUM"
        delivery_impact["impact_description"] = (
            f"齐套率 {rate_val}%，{kitting['shortage_items']}项缺料，"
            f"可能影响项目交付进度"
        )
    else:
        delivery_impact["risk_level"] = "HIGH"
        delivery_impact["impact_description"] = (
            f"齐套率仅 {rate_val}%，{kitting['shortage_items']}项缺料，"
            f"严重影响项目交付，需立即处理"
        )

    # 5. 建议措施
    suggestions: List[Dict[str, str]] = []

    critical_shortages = [s for s in shortages if s["is_key_item"]]
    if critical_shortages:
        suggestions.append({
            "priority": "HIGH",
            "action": "加急关键物料",
            "detail": (
                f"有 {len(critical_shortages)} 项关键物料缺料，建议立即联系供应商加急: "
                + ", ".join(s["material_code"] for s in critical_shortages[:5])
            ),
        })

    no_arrival = [s for s in shortages if not s.get("expected_arrival_date")]
    if no_arrival:
        suggestions.append({
            "priority": "MEDIUM",
            "action": "确认到货日期",
            "detail": (
                f"有 {len(no_arrival)} 项缺料物料无预计到货日期，建议跟进: "
                + ", ".join(s["material_code"] for s in no_arrival[:5])
            ),
        })

    high_shortage = [s for s in shortages if s["shortage_qty"] > s["required_qty"] * 0.5]
    if high_shortage:
        suggestions.append({
            "priority": "MEDIUM",
            "action": "寻找替代料",
            "detail": (
                f"有 {len(high_shortage)} 项物料缺口超过50%，建议评估替代方案: "
                + ", ".join(s["material_code"] for s in high_shortage[:5])
            ),
        })

    if rate_val < 90 and not suggestions:
        suggestions.append({
            "priority": "LOW",
            "action": "持续跟踪",
            "detail": "齐套率尚未达到90%，建议持续跟踪在途物料进度",
        })

    return success_response(
        data={
            "overview": {
                "project_id": project.id,
                "project_code": project.project_code,
                "project_name": project.project_name,
                "material_status": project.material_status or _derive_material_status(
                    kitting["kitting_rate"], kitting["shortage_items"], False
                ),
                "kitting_rate": float(kitting["kitting_rate"]),
                "total_items": kitting["total_items"],
                "kitted_items": kitting["kitted_items"],
                "shortage_items": kitting["shortage_items"],
                "health": project.health,
            },
            "bom_breakdown": bom_stats,
            "shortage_details": key_shortages[:50],
            "delivery_impact": delivery_impact,
            "suggestions": suggestions,
        },
        message="获取项目物料状态成功",
    )
