# -*- coding: utf-8 -*-
"""
项目-变更单联动集成服务

三大核心功能：
1. assess_impact     — ECN 审批时：评估变更对项目的影响
2. execute_linkage   — ECN 执行后：联动更新项目数据
3. get_project_change_summary — 项目视图：查看关联变更汇总
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ecn.core import Ecn
from app.models.pmo.change_risk import PmoProjectRisk
from app.models.project.change_impact import ProjectChangeImpact
from app.models.project.core import Machine, Project
from app.models.project.financial import ProjectCost, ProjectMilestone

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  1. 变更影响评估（ECN 审批阶段）
# ═══════════════════════════════════════════════════════════════


def assess_impact(
    db: Session,
    ecn_id: int,
    project_id: int,
    current_user_id: int,
    *,
    machine_id: Optional[int] = None,
    schedule_impact_days: int = 0,
    affected_milestones: Optional[List[Dict[str, Any]]] = None,
    rework_cost: Decimal = Decimal("0"),
    scrap_cost: Decimal = Decimal("0"),
    additional_cost: Decimal = Decimal("0"),
    cost_breakdown: Optional[Dict[str, Any]] = None,
    risk_level: str = "LOW",
    risk_description: Optional[str] = None,
    impact_summary: Optional[str] = None,
    remark: Optional[str] = None,
) -> ProjectChangeImpact:
    """
    ECN 审批时调用：读取项目当前状态，创建影响评估记录。

    Returns:
        ProjectChangeImpact 记录
    """
    # 读取 ECN
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    # 读取项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"项目 {project_id} 不存在")

    # 计算总成本影响
    total_cost = rework_cost + scrap_cost + additional_cost

    # 自动推断风险等级（如果未手动指定或为默认值）
    if risk_level == "LOW":
        risk_level = _infer_risk_level(schedule_impact_days, total_cost, ecn.priority)

    # 如果没有手动填写里程碑影响，自动评估
    if not affected_milestones and schedule_impact_days > 0:
        affected_milestones = _auto_assess_milestone_impact(
            db, project_id, machine_id, schedule_impact_days
        )

    # 生成影响摘要
    if not impact_summary:
        impact_summary = _generate_impact_summary(
            ecn, project, schedule_impact_days, total_cost, risk_level, affected_milestones
        )

    # 构建完整影响报告
    impact_report = {
        "schedule": {
            "delay_days": schedule_impact_days,
            "affected_milestones": affected_milestones or [],
        },
        "cost": {
            "rework": float(rework_cost),
            "scrap": float(scrap_cost),
            "additional": float(additional_cost),
            "total": float(total_cost),
            "breakdown": cost_breakdown,
        },
        "risk": {
            "level": risk_level,
            "description": risk_description,
        },
        "recommendation": _generate_recommendation(schedule_impact_days, total_cost, risk_level),
    }

    # 创建记录
    record = ProjectChangeImpact(
        ecn_id=ecn_id,
        ecn_no=ecn.ecn_no,
        project_id=project_id,
        machine_id=machine_id,
        project_stage_snapshot=project.stage,
        project_progress_snapshot=project.progress_pct,
        schedule_impact_days=schedule_impact_days,
        affected_milestones=affected_milestones,
        rework_cost=rework_cost,
        scrap_cost=scrap_cost,
        additional_cost=additional_cost,
        total_cost_impact=total_cost,
        cost_breakdown=cost_breakdown,
        risk_level=risk_level,
        risk_description=risk_description,
        impact_summary=impact_summary,
        impact_report=impact_report,
        assessed_by=current_user_id,
        assessed_at=datetime.now(),
        status="ASSESSED",
        remark=remark,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info("ECN %s 对项目 %s 的影响评估已创建 (ID=%s)", ecn.ecn_no, project.project_code, record.id)
    return record


# ═══════════════════════════════════════════════════════════════
#  2. 变更执行联动（ECN 执行后）
# ═══════════════════════════════════════════════════════════════


def execute_linkage(
    db: Session,
    impact_id: int,
    current_user_id: int,
    *,
    update_milestones: bool = True,
    record_costs: bool = True,
    create_risk: bool = True,
    actual_delay_days: Optional[int] = None,
    actual_cost_impact: Optional[Decimal] = None,
    remark: Optional[str] = None,
) -> ProjectChangeImpact:
    """
    ECN 执行后调用：联动更新项目里程碑、成本、风险。

    Returns:
        更新后的 ProjectChangeImpact 记录
    """
    record = db.query(ProjectChangeImpact).filter(ProjectChangeImpact.id == impact_id).first()
    if not record:
        raise ValueError(f"影响记录 {impact_id} 不存在")

    if record.status not in ("ASSESSED", "EXECUTING"):
        raise ValueError(f"影响记录状态为 {record.status}，无法执行联动")

    record.status = "EXECUTING"

    # 使用实际值或评估值
    delay_days = actual_delay_days if actual_delay_days is not None else record.schedule_impact_days
    cost_impact = actual_cost_impact if actual_cost_impact is not None else record.total_cost_impact

    record.actual_delay_days = delay_days
    record.actual_cost_impact = cost_impact

    # ── 2a. 更新项目里程碑 ──
    if update_milestones and delay_days and delay_days > 0:
        milestone_details = _update_project_milestones(
            db, record.project_id, record.machine_id, delay_days, record.affected_milestones
        )
        record.milestones_updated = True
        record.milestone_update_detail = milestone_details

        # 同步更新项目计划结束日期
        project = db.query(Project).filter(Project.id == record.project_id).first()
        if project and project.planned_end_date:
            project.planned_end_date = project.planned_end_date + timedelta(days=delay_days)
            db.add(project)

    # ── 2b. 记录项目成本 ──
    if record_costs and cost_impact and cost_impact > 0:
        cost_ids = _record_project_costs(
            db, record, current_user_id
        )
        record.costs_recorded = True
        record.cost_record_ids = cost_ids

    # ── 2c. 创建项目风险记录（重大变更） ──
    if create_risk and record.risk_level in ("HIGH", "CRITICAL"):
        risk_id = _create_project_risk(
            db, record, current_user_id
        )
        record.risk_created = True
        record.risk_record_id = risk_id

    record.executed_by = current_user_id
    record.executed_at = datetime.now()
    record.status = "COMPLETED"
    if remark:
        record.remark = remark

    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info("ECN %s 项目联动执行完成 (impact_id=%s)", record.ecn_no, record.id)
    return record


# ═══════════════════════════════════════════════════════════════
#  3. 项目视图查询
# ═══════════════════════════════════════════════════════════════


def get_project_change_summary(
    db: Session,
    project_id: int,
) -> Dict[str, Any]:
    """
    获取项目的变更影响汇总（用于项目详情页展示）。
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"项目 {project_id} 不存在")

    impacts = (
        db.query(ProjectChangeImpact)
        .filter(ProjectChangeImpact.project_id == project_id)
        .order_by(ProjectChangeImpact.created_at.desc())
        .all()
    )

    # 统计
    status_counts = {"ASSESSED": 0, "EXECUTING": 0, "COMPLETED": 0, "CANCELLED": 0}
    total_delay = 0
    total_cost = Decimal("0")
    high_risk_count = 0

    for imp in impacts:
        status_counts[imp.status] = status_counts.get(imp.status, 0) + 1
        actual_delay = imp.actual_delay_days if imp.actual_delay_days is not None else imp.schedule_impact_days
        total_delay += actual_delay or 0
        actual_cost = imp.actual_cost_impact if imp.actual_cost_impact is not None else imp.total_cost_impact
        total_cost += actual_cost or Decimal("0")
        if imp.risk_level in ("HIGH", "CRITICAL"):
            high_risk_count += 1

    return {
        "project_id": project_id,
        "project_name": project.project_name,
        "total_ecn_count": len(impacts),
        "assessed_count": status_counts.get("ASSESSED", 0),
        "executing_count": status_counts.get("EXECUTING", 0),
        "completed_count": status_counts.get("COMPLETED", 0),
        "total_delay_days": total_delay,
        "total_cost_impact": total_cost,
        "high_risk_count": high_risk_count,
        "impacts": impacts,
    }


def get_ecn_project_impacts(
    db: Session,
    ecn_id: int,
) -> List[ProjectChangeImpact]:
    """
    获取某个 ECN 影响的所有项目记录。
    """
    return (
        db.query(ProjectChangeImpact)
        .filter(ProjectChangeImpact.ecn_id == ecn_id)
        .order_by(ProjectChangeImpact.created_at.desc())
        .all()
    )


def get_impact_detail(
    db: Session,
    impact_id: int,
) -> Optional[ProjectChangeImpact]:
    """获取单条影响记录详情。"""
    return db.query(ProjectChangeImpact).filter(ProjectChangeImpact.id == impact_id).first()


def get_project_delay_history(
    db: Session,
    project_id: int,
) -> List[Dict[str, Any]]:
    """
    获取项目因变更导致的历史延期记录。
    """
    impacts = (
        db.query(ProjectChangeImpact)
        .filter(
            ProjectChangeImpact.project_id == project_id,
            ProjectChangeImpact.schedule_impact_days > 0,
        )
        .order_by(ProjectChangeImpact.assessed_at.asc())
        .all()
    )

    history = []
    cumulative_delay = 0
    for imp in impacts:
        delay = imp.actual_delay_days if imp.actual_delay_days is not None else imp.schedule_impact_days
        cumulative_delay += delay or 0
        history.append({
            "impact_id": imp.id,
            "ecn_id": imp.ecn_id,
            "ecn_no": imp.ecn_no,
            "delay_days": delay,
            "cumulative_delay_days": cumulative_delay,
            "risk_level": imp.risk_level,
            "status": imp.status,
            "assessed_at": imp.assessed_at.isoformat() if imp.assessed_at else None,
            "executed_at": imp.executed_at.isoformat() if imp.executed_at else None,
        })

    return history


# ═══════════════════════════════════════════════════════════════
#  内部辅助函数
# ═══════════════════════════════════════════════════════════════


def _infer_risk_level(delay_days: int, total_cost: Decimal, priority: Optional[str]) -> str:
    """根据延期天数、成本和优先级推断风险等级。"""
    if priority == "URGENT" or delay_days > 30 or total_cost > 100000:
        return "CRITICAL"
    if delay_days > 14 or total_cost > 50000:
        return "HIGH"
    if delay_days > 7 or total_cost > 10000:
        return "MEDIUM"
    return "LOW"


def _auto_assess_milestone_impact(
    db: Session,
    project_id: int,
    machine_id: Optional[int],
    delay_days: int,
) -> List[Dict[str, Any]]:
    """自动评估受影响的里程碑（当前日期之后的未完成里程碑）。"""
    query = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status.in_(["PENDING", "IN_PROGRESS"]),
    )
    if machine_id:
        query = query.filter(ProjectMilestone.machine_id == machine_id)

    milestones = query.order_by(ProjectMilestone.planned_date.asc()).all()
    result = []
    for ms in milestones:
        if ms.planned_date:
            new_date = ms.planned_date + timedelta(days=delay_days)
            result.append({
                "milestone_id": ms.id,
                "name": ms.milestone_name,
                "original_date": ms.planned_date.isoformat(),
                "new_date": new_date.isoformat(),
                "delay_days": delay_days,
            })
        else:
            result.append({
                "milestone_id": ms.id,
                "name": ms.milestone_name,
                "original_date": None,
                "new_date": None,
                "delay_days": delay_days,
            })
    return result


def _generate_impact_summary(
    ecn: Ecn,
    project: Project,
    delay_days: int,
    total_cost: Decimal,
    risk_level: str,
    affected_milestones: Optional[List[Dict[str, Any]]],
) -> str:
    """生成影响摘要文本。"""
    parts = [f"ECN {ecn.ecn_no} 对项目 {project.project_code} 的影响评估："]

    if delay_days > 0:
        parts.append(f"预计延期 {delay_days} 天")
    else:
        parts.append("无进度影响")

    if total_cost > 0:
        parts.append(f"成本影响 ¥{total_cost:,.2f}")
    else:
        parts.append("无成本影响")

    risk_labels = {"LOW": "低", "MEDIUM": "中", "HIGH": "高", "CRITICAL": "严重"}
    parts.append(f"风险等级：{risk_labels.get(risk_level, risk_level)}")

    if affected_milestones:
        parts.append(f"影响 {len(affected_milestones)} 个里程碑")

    return "；".join(parts)


def _generate_recommendation(delay_days: int, total_cost: Decimal, risk_level: str) -> str:
    """根据影响程度生成建议。"""
    if risk_level == "CRITICAL":
        return "建议立即组织评审会议，制定专项应对方案，考虑是否需要调整项目基线。"
    if risk_level == "HIGH":
        return "建议项目经理重点关注，评估是否需要赶工或调整资源分配。"
    if risk_level == "MEDIUM":
        return "建议纳入项目周报跟踪，监控后续影响。"
    return "影响可控，按常规流程执行即可。"


def _update_project_milestones(
    db: Session,
    project_id: int,
    machine_id: Optional[int],
    delay_days: int,
    affected_milestones: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """实际更新项目里程碑的计划日期。"""
    details = []

    if affected_milestones:
        # 按评估中指定的里程碑更新
        for ms_info in affected_milestones:
            ms = db.query(ProjectMilestone).filter(
                ProjectMilestone.id == ms_info.get("milestone_id")
            ).first()
            if ms and ms.planned_date:
                old_date = ms.planned_date
                ms.planned_date = ms.planned_date + timedelta(days=delay_days)
                db.add(ms)
                details.append({
                    "milestone_id": ms.id,
                    "name": ms.milestone_name,
                    "old_date": old_date.isoformat(),
                    "new_date": ms.planned_date.isoformat(),
                })
    else:
        # 没有指定则更新所有未完成里程碑
        query = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id,
            ProjectMilestone.status.in_(["PENDING", "IN_PROGRESS"]),
        )
        if machine_id:
            query = query.filter(ProjectMilestone.machine_id == machine_id)

        for ms in query.all():
            if ms.planned_date:
                old_date = ms.planned_date
                ms.planned_date = ms.planned_date + timedelta(days=delay_days)
                db.add(ms)
                details.append({
                    "milestone_id": ms.id,
                    "name": ms.milestone_name,
                    "old_date": old_date.isoformat(),
                    "new_date": ms.planned_date.isoformat(),
                })

    return details


def _record_project_costs(
    db: Session,
    record: ProjectChangeImpact,
    user_id: int,
) -> List[int]:
    """将变更成本写入项目成本表。"""
    cost_ids = []
    cost_items = []

    if record.rework_cost and record.rework_cost > 0:
        cost_items.append(("ECN_REWORK", "返工成本", record.rework_cost))
    if record.scrap_cost and record.scrap_cost > 0:
        cost_items.append(("ECN_SCRAP", "报废成本", record.scrap_cost))
    if record.additional_cost and record.additional_cost > 0:
        cost_items.append(("ECN_ADDITIONAL", "变更新增成本", record.additional_cost))

    for cost_type, description, amount in cost_items:
        cost = ProjectCost(
            project_id=record.project_id,
            machine_id=record.machine_id,
            cost_type=cost_type,
            cost_category="ECN_CHANGE",
            source_module="ecn",
            source_type="ECN",
            source_id=record.ecn_id,
            source_no=record.ecn_no,
            amount=amount,
            cost_date=date.today(),
            description=f"{description} - ECN {record.ecn_no}",
            created_by=user_id,
        )
        db.add(cost)
        db.flush()
        cost_ids.append(cost.id)

    return cost_ids


def _create_project_risk(
    db: Session,
    record: ProjectChangeImpact,
    user_id: int,
) -> int:
    """为重大变更创建项目风险记录。"""
    # 生成风险编号
    count = db.query(func.count(PmoProjectRisk.id)).filter(
        PmoProjectRisk.project_id == record.project_id
    ).scalar() or 0
    risk_no = f"RISK-{record.project_id:04d}-{count + 1:03d}"

    risk = PmoProjectRisk(
        project_id=record.project_id,
        risk_no=risk_no,
        risk_category="CHANGE",
        risk_name=f"ECN变更风险 - {record.ecn_no}",
        description=(
            f"ECN {record.ecn_no} 引发的项目风险。"
            f"预计延期 {record.schedule_impact_days} 天，"
            f"成本影响 ¥{record.total_cost_impact:,.2f}。"
            f"{record.risk_description or ''}"
        ),
        probability="HIGH" if record.risk_level == "CRITICAL" else "MEDIUM",
        impact=record.risk_level,
        risk_level=record.risk_level,
        response_strategy="MITIGATE",
        response_plan=f"跟踪 ECN {record.ecn_no} 执行进度，确保变更按计划完成。",
        owner_id=user_id,
        status="IDENTIFIED",
        trigger_condition=f"ECN {record.ecn_no} 执行偏差超过预期",
    )
    db.add(risk)
    db.flush()

    logger.info("为项目 %s 创建风险记录 %s (ECN: %s)", record.project_id, risk_no, record.ecn_no)
    return risk.id
