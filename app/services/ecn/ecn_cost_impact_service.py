# -*- coding: utf-8 -*-
"""
ECN成本影响跟踪服务

功能：
1. cost_impact_analysis    — 分析ECN的成本影响（直接+间接）
2. get_cost_tracking       — 成本执行跟踪（预算vs实际、趋势）
3. create_cost_record      — 记录实际发生的成本
4. get_project_ecn_cost_summary — 项目维度ECN成本汇总
5. check_cost_alerts       — 成本预警检查
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, extract, case
from sqlalchemy.orm import Session

from app.models.ecn.core import Ecn
from app.models.ecn.cost_record import EcnCostRecord
from app.models.ecn.impact import EcnAffectedMaterial
from app.models.project.change_impact import ProjectChangeImpact
from app.models.project.core import Project

logger = logging.getLogger(__name__)

# 成本类型标签映射
COST_TYPE_LABELS = {
    "SCRAP": "物料报废",
    "REWORK": "返工成本",
    "NEW_PURCHASE": "新物料采购",
    "CLAIM": "供应商索赔",
    "DELAY": "延期成本",
    "ADMIN": "管理成本",
}

DIRECT_COST_TYPES = {"SCRAP", "REWORK", "NEW_PURCHASE"}
INDIRECT_COST_TYPES = {"CLAIM", "DELAY", "ADMIN"}


# ═══════════════════════════════════════════════════════════════
#  1. 成本影响分析
# ═══════════════════════════════════════════════════════════════


def cost_impact_analysis(
    db: Session,
    ecn_id: int,
) -> Dict[str, Any]:
    """
    分析ECN导致的成本影响。

    数据来源：
    - ecn_cost_records: 已录入的成本记录（实际发生）
    - ecn_affected_materials: 受影响物料的报废/呆滞成本
    - project_change_impacts: 评估阶段的成本预估
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    # 1) 从成本记录表按类型汇总
    type_summary = (
        db.query(
            EcnCostRecord.cost_type,
            func.sum(EcnCostRecord.estimated_amount).label("estimated_total"),
            func.sum(EcnCostRecord.actual_amount).label("actual_total"),
            func.count(EcnCostRecord.id).label("record_count"),
        )
        .filter(EcnCostRecord.ecn_id == ecn_id)
        .group_by(EcnCostRecord.cost_type)
        .all()
    )

    cost_by_type = []
    type_map = {}
    for row in type_summary:
        item = {
            "cost_type": row.cost_type,
            "cost_type_label": COST_TYPE_LABELS.get(row.cost_type, row.cost_type),
            "estimated_total": row.estimated_total or 0,
            "actual_total": row.actual_total or 0,
            "record_count": row.record_count or 0,
        }
        cost_by_type.append(item)
        type_map[row.cost_type] = item

    # 按直接/间接归类
    scrap = Decimal(str(type_map.get("SCRAP", {}).get("actual_total", 0)))
    rework = Decimal(str(type_map.get("REWORK", {}).get("actual_total", 0)))
    new_purchase = Decimal(str(type_map.get("NEW_PURCHASE", {}).get("actual_total", 0)))
    claim = Decimal(str(type_map.get("CLAIM", {}).get("actual_total", 0)))
    delay = Decimal(str(type_map.get("DELAY", {}).get("actual_total", 0)))
    admin = Decimal(str(type_map.get("ADMIN", {}).get("actual_total", 0)))

    direct_total = scrap + rework + new_purchase
    indirect_total = claim + delay + admin
    total = direct_total + indirect_total

    # 2) 受影响物料成本影响排行
    material_impacts = (
        db.query(
            EcnAffectedMaterial.material_id,
            EcnAffectedMaterial.material_code,
            EcnAffectedMaterial.material_name,
            EcnAffectedMaterial.cost_impact,
            EcnAffectedMaterial.obsolete_cost,
        )
        .filter(EcnAffectedMaterial.ecn_id == ecn_id)
        .order_by(EcnAffectedMaterial.cost_impact.desc())
        .limit(10)
        .all()
    )

    top_materials = []
    for m in material_impacts:
        mat_scrap = Decimal(str(m.obsolete_cost or 0))
        mat_total = Decimal(str(m.cost_impact or 0))
        top_materials.append(
            {
                "material_id": m.material_id,
                "material_code": m.material_code,
                "material_name": m.material_name,
                "scrap_cost": mat_scrap,
                "new_purchase_cost": max(Decimal("0"), mat_total - mat_scrap),
                "total_impact": mat_total,
            }
        )

    # 3) 评估阶段预估总成本
    assessed = (
        db.query(func.sum(ProjectChangeImpact.total_cost_impact))
        .filter(ProjectChangeImpact.ecn_id == ecn_id)
        .scalar()
    ) or 0

    return {
        "ecn_id": ecn_id,
        "ecn_no": ecn.ecn_no,
        "project_id": ecn.project_id,
        "scrap_cost": scrap,
        "rework_cost": rework,
        "new_purchase_cost": new_purchase,
        "claim_cost": claim,
        "delay_cost": delay,
        "admin_cost": admin,
        "direct_cost_total": direct_total,
        "indirect_cost_total": indirect_total,
        "total_cost_impact": total,
        "cost_by_type": cost_by_type,
        "top_material_impacts": top_materials,
        "assessed_cost_impact": Decimal(str(assessed)),
        "analyzed_at": datetime.now(),
    }


# ═══════════════════════════════════════════════════════════════
#  2. 成本执行跟踪
# ═══════════════════════════════════════════════════════════════


def get_cost_tracking(
    db: Session,
    ecn_id: int,
) -> Dict[str, Any]:
    """成本执行跟踪：预算vs实际、趋势、预计最终成本"""
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    records = (
        db.query(EcnCostRecord).filter(EcnCostRecord.ecn_id == ecn_id).all()
    )

    total_estimated = Decimal("0")
    total_actual = Decimal("0")
    approved_count = 0
    pending_count = 0

    # 按类型汇总
    type_agg: Dict[str, Dict] = {}
    # 按月趋势
    month_agg: Dict[str, Dict] = {}

    for r in records:
        est = Decimal(str(r.estimated_amount or 0))
        act = Decimal(str(r.actual_amount or 0))
        total_estimated += est
        total_actual += act

        if r.approval_status == "APPROVED":
            approved_count += 1
        elif r.approval_status == "PENDING":
            pending_count += 1

        # 类型
        ct = r.cost_type
        if ct not in type_agg:
            type_agg[ct] = {
                "cost_type": ct,
                "cost_type_label": COST_TYPE_LABELS.get(ct, ct),
                "estimated_total": Decimal("0"),
                "actual_total": Decimal("0"),
                "record_count": 0,
            }
        type_agg[ct]["estimated_total"] += est
        type_agg[ct]["actual_total"] += act
        type_agg[ct]["record_count"] += 1

        # 月份
        if r.cost_date:
            month_key = r.cost_date.strftime("%Y-%m")
        else:
            month_key = (r.created_at or datetime.now()).strftime("%Y-%m")
        if month_key not in month_agg:
            month_agg[month_key] = {"estimated": Decimal("0"), "actual": Decimal("0")}
        month_agg[month_key]["estimated"] += est
        month_agg[month_key]["actual"] += act

    # 构建趋势（按月排序）
    trend = []
    cumulative = Decimal("0")
    for month_key in sorted(month_agg.keys()):
        d = month_agg[month_key]
        cumulative += d["actual"]
        trend.append(
            {
                "period": month_key,
                "estimated": d["estimated"],
                "actual": d["actual"],
                "cumulative_actual": cumulative,
            }
        )

    # 偏差
    variance = total_actual - total_estimated
    variance_ratio = (
        float(variance / total_estimated * 100) if total_estimated else 0
    )

    # 预计最终成本 = 已发生 + 未审批的预估
    pending_estimated = sum(
        Decimal(str(r.estimated_amount or 0))
        for r in records
        if r.approval_status == "PENDING"
    )
    forecast = total_actual + pending_estimated

    return {
        "ecn_id": ecn_id,
        "ecn_no": ecn.ecn_no,
        "total_estimated": total_estimated,
        "total_actual": total_actual,
        "variance": variance,
        "variance_ratio": round(variance_ratio, 2),
        "cost_by_type": list(type_agg.values()),
        "cost_trend": trend,
        "forecast_final_cost": forecast,
        "total_records": len(records),
        "approved_records": approved_count,
        "pending_records": pending_count,
    }


# ═══════════════════════════════════════════════════════════════
#  3. 成本记录 CRUD
# ═══════════════════════════════════════════════════════════════


def create_cost_record(
    db: Session,
    current_user_id: int,
    *,
    ecn_id: int,
    cost_type: str,
    project_id: Optional[int] = None,
    machine_id: Optional[int] = None,
    cost_category: Optional[str] = None,
    estimated_amount: Decimal = Decimal("0"),
    actual_amount: Decimal = Decimal("0"),
    currency: str = "CNY",
    cost_date: Optional[date] = None,
    material_id: Optional[int] = None,
    material_code: Optional[str] = None,
    material_name: Optional[str] = None,
    quantity: Optional[float] = None,
    unit_price: Optional[float] = None,
    rework_hours: Optional[float] = None,
    hourly_rate: Optional[float] = None,
    voucher_type: Optional[str] = None,
    voucher_no: Optional[str] = None,
    voucher_attachment_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    description: Optional[str] = None,
) -> EcnCostRecord:
    """创建一条ECN成本记录"""
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    if cost_type not in COST_TYPE_LABELS:
        raise ValueError(f"无效的成本类型: {cost_type}")

    # 如果未指定 project_id，从 ECN 继承
    if project_id is None:
        project_id = ecn.project_id

    record = EcnCostRecord(
        ecn_id=ecn_id,
        project_id=project_id,
        machine_id=machine_id,
        cost_type=cost_type,
        cost_category=cost_category,
        estimated_amount=estimated_amount,
        actual_amount=actual_amount,
        currency=currency,
        cost_date=cost_date or date.today(),
        material_id=material_id,
        material_code=material_code,
        material_name=material_name,
        quantity=quantity,
        unit_price=unit_price,
        rework_hours=rework_hours,
        hourly_rate=hourly_rate,
        voucher_type=voucher_type,
        voucher_no=voucher_no,
        voucher_attachment_id=voucher_attachment_id,
        vendor_id=vendor_id,
        description=description,
        recorded_by=current_user_id,
        approval_status="PENDING",
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("ECN %s 新增成本记录 id=%s type=%s amount=%s", ecn.ecn_no, record.id, cost_type, actual_amount)
    return record


def list_cost_records(
    db: Session,
    ecn_id: int,
    cost_type: Optional[str] = None,
    approval_status: Optional[str] = None,
) -> List[EcnCostRecord]:
    """查询ECN的成本记录列表"""
    q = db.query(EcnCostRecord).filter(EcnCostRecord.ecn_id == ecn_id)
    if cost_type:
        q = q.filter(EcnCostRecord.cost_type == cost_type)
    if approval_status:
        q = q.filter(EcnCostRecord.approval_status == approval_status)
    return q.order_by(EcnCostRecord.cost_date.desc()).all()


def approve_cost_record(
    db: Session,
    record_id: int,
    current_user_id: int,
    approved: bool,
    note: Optional[str] = None,
) -> EcnCostRecord:
    """审批成本记录"""
    record = db.query(EcnCostRecord).filter(EcnCostRecord.id == record_id).first()
    if not record:
        raise ValueError(f"成本记录 {record_id} 不存在")

    record.approval_status = "APPROVED" if approved else "REJECTED"
    record.approved_by = current_user_id
    record.approved_at = datetime.now()
    record.approval_note = note

    db.commit()
    db.refresh(record)
    return record


# ═══════════════════════════════════════════════════════════════
#  4. 项目ECN成本汇总
# ═══════════════════════════════════════════════════════════════


def get_project_ecn_cost_summary(
    db: Session,
    project_id: int,
) -> Dict[str, Any]:
    """获取项目下所有ECN的成本汇总"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"项目 {project_id} 不存在")

    # 查出该项目关联的所有ECN
    ecns = db.query(Ecn).filter(Ecn.project_id == project_id).all()

    ecn_details = []
    total_estimated = Decimal("0")
    total_actual = Decimal("0")
    type_agg: Dict[str, Dict] = {}

    for ecn in ecns:
        # 该ECN的成本记录汇总
        summary = (
            db.query(
                func.sum(EcnCostRecord.estimated_amount).label("est"),
                func.sum(EcnCostRecord.actual_amount).label("act"),
                func.count(EcnCostRecord.id).label("cnt"),
            )
            .filter(EcnCostRecord.ecn_id == ecn.id)
            .first()
        )

        est = Decimal(str(summary.est or 0))
        act = Decimal(str(summary.act or 0))
        cnt = summary.cnt or 0

        total_estimated += est
        total_actual += act

        ecn_details.append(
            {
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "status": ecn.status,
                "total_estimated": est,
                "total_actual": act,
                "record_count": cnt,
            }
        )

        # 按类型汇总（跨ECN）
        type_rows = (
            db.query(
                EcnCostRecord.cost_type,
                func.sum(EcnCostRecord.estimated_amount).label("est"),
                func.sum(EcnCostRecord.actual_amount).label("act"),
                func.count(EcnCostRecord.id).label("cnt"),
            )
            .filter(EcnCostRecord.ecn_id == ecn.id)
            .group_by(EcnCostRecord.cost_type)
            .all()
        )
        for row in type_rows:
            ct = row.cost_type
            if ct not in type_agg:
                type_agg[ct] = {
                    "cost_type": ct,
                    "cost_type_label": COST_TYPE_LABELS.get(ct, ct),
                    "estimated_total": Decimal("0"),
                    "actual_total": Decimal("0"),
                    "record_count": 0,
                }
            type_agg[ct]["estimated_total"] += Decimal(str(row.est or 0))
            type_agg[ct]["actual_total"] += Decimal(str(row.act or 0))
            type_agg[ct]["record_count"] += row.cnt or 0

    # 项目预算
    budget = Decimal(str(project.budget_amount or 0)) if hasattr(project, "budget_amount") else None
    ecn_ratio = None
    if budget and budget > 0 and total_actual > 0:
        ecn_ratio = round(float(total_actual / budget * 100), 2)

    return {
        "project_id": project_id,
        "project_name": project.project_name if hasattr(project, "project_name") else None,
        "total_ecn_count": len(ecns),
        "total_estimated_cost": total_estimated,
        "total_actual_cost": total_actual,
        "project_budget": budget,
        "ecn_cost_ratio": ecn_ratio,
        "ecn_details": ecn_details,
        "cost_by_type": list(type_agg.values()),
    }


# ═══════════════════════════════════════════════════════════════
#  5. 成本预警
# ═══════════════════════════════════════════════════════════════


def check_cost_alerts(
    db: Session,
    ecn_id: int,
    budget_threshold: Optional[Decimal] = None,
    large_amount_threshold: Optional[Decimal] = None,
    trend_check: bool = True,
) -> Dict[str, Any]:
    """检查ECN成本预警"""
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    records = db.query(EcnCostRecord).filter(EcnCostRecord.ecn_id == ecn_id).all()

    total_estimated = sum(Decimal(str(r.estimated_amount or 0)) for r in records)
    total_actual = sum(Decimal(str(r.actual_amount or 0)) for r in records)

    alerts = []

    # 1) 预算超支预警
    if budget_threshold is not None and total_actual > budget_threshold:
        level = "CRITICAL" if total_actual > budget_threshold * Decimal("1.2") else "WARNING"
        alerts.append(
            {
                "alert_type": "OVER_BUDGET",
                "alert_level": level,
                "message": f"ECN成本已超预算：实际 {total_actual} > 阈值 {budget_threshold}",
                "current_value": total_actual,
                "threshold_value": budget_threshold,
                "related_record_id": None,
            }
        )

    # 如果没有设定预算阈值，用预估总额作为基线
    if budget_threshold is None and total_estimated > 0 and total_actual > total_estimated:
        over_ratio = (total_actual - total_estimated) / total_estimated
        if over_ratio > Decimal("0.1"):
            level = "CRITICAL" if over_ratio > Decimal("0.3") else "WARNING"
            alerts.append(
                {
                    "alert_type": "OVER_BUDGET",
                    "alert_level": level,
                    "message": f"实际成本超预估 {round(float(over_ratio * 100), 1)}%",
                    "current_value": total_actual,
                    "threshold_value": total_estimated,
                    "related_record_id": None,
                }
            )

    # 2) 大额成本审批提醒
    if large_amount_threshold is not None:
        for r in records:
            amt = Decimal(str(r.actual_amount or 0))
            if amt >= large_amount_threshold and r.approval_status == "PENDING":
                alerts.append(
                    {
                        "alert_type": "LARGE_AMOUNT",
                        "alert_level": "WARNING",
                        "message": f"大额成本待审批：{r.cost_type} ¥{amt}",
                        "current_value": amt,
                        "threshold_value": large_amount_threshold,
                        "related_record_id": r.id,
                    }
                )

    # 3) 成本趋势异常
    if trend_check and len(records) >= 3:
        # 简单检测：最近3笔实际成本是否持续上涨
        recent = sorted(records, key=lambda r: r.created_at or datetime.min)[-3:]
        amounts = [Decimal(str(r.actual_amount or 0)) for r in recent]
        if amounts[0] < amounts[1] < amounts[2] and amounts[2] > Decimal("0"):
            growth_rate = float((amounts[2] - amounts[0]) / amounts[0] * 100) if amounts[0] > 0 else 0
            if growth_rate > 50:
                alerts.append(
                    {
                        "alert_type": "TREND_ABNORMAL",
                        "alert_level": "WARNING",
                        "message": f"成本持续上涨，最近3笔增长 {round(growth_rate, 1)}%",
                        "current_value": amounts[2],
                        "threshold_value": None,
                        "related_record_id": None,
                    }
                )

    return {
        "ecn_id": ecn_id,
        "ecn_no": ecn.ecn_no,
        "alerts": alerts,
        "total_estimated": total_estimated,
        "total_actual": total_actual,
        "alert_count": len(alerts),
        "checked_at": datetime.now(),
    }
