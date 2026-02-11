# -*- coding: utf-8 -*-
"""
预算执行检查服务
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.alert import AlertRecord, AlertRule
from app.models.budget import ProjectBudget
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
from app.models.project import Project, ProjectCost


def get_project_budget(db: Session, project_id: int, project: Project) -> float:
    """
    获取项目预算金额

    Returns:
        float: 预算金额
    """
    budget = (
        db.query(ProjectBudget)
        .filter(
            ProjectBudget.project_id == project_id,
            ProjectBudget.is_active == True,
            ProjectBudget.status == "APPROVED"
        )
        .order_by(ProjectBudget.version.desc())
        .first()
    )

    return float(budget.total_amount) if budget else float(project.budget_amount or 0)


def get_actual_cost(db: Session, project_id: int, project: Project) -> float:
    """
    获取项目实际成本

    Returns:
        float: 实际成本
    """
    if project.actual_cost:
        return float(project.actual_cost)

    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    return sum([float(c.amount or 0) for c in costs])


def get_or_create_alert_rule(db: Session) -> AlertRule:
    """
    获取或创建成本预警规则

    Returns:
        AlertRule: 预警规则对象
    """
    alert_rule = db.query(AlertRule).filter(
        AlertRule.rule_code == 'COST_OVERRUN',
        AlertRule.is_enabled == True
    ).first()

    if not alert_rule:
        alert_rule = AlertRule(
            rule_code='COST_OVERRUN',
            rule_name='成本超支预警',
            rule_type=AlertRuleTypeEnum.COST_OVERRUN.value,
            target_type='PROJECT',
            condition_type='THRESHOLD',
            condition_operator='GT',
            threshold_value='5',
            alert_level=AlertLevelEnum.WARNING.value,
            is_enabled=True,
            is_system=True,
            description='当项目成本超支超过5%时触发预警'
        )
        db.add(alert_rule)
        db.flush()

    return alert_rule


def determine_alert_level(
    execution_rate: float,
    overrun_ratio: float,
    project_name: str,
    project_code: str,
    budget_amount: float,
    actual_cost: float
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    判断预警级别

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: (预警级别, 标题, 内容)
    """
    if execution_rate >= 100:
        # 已超支
        if overrun_ratio >= 20:
            return (
                AlertLevelEnum.URGENT.value,
                f'项目成本严重超支：{project_name}',
                f'项目 {project_code} 成本严重超支 {overrun_ratio:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，超支：{actual_cost - budget_amount:,.2f}）'
            )
        elif overrun_ratio >= 10:
            return (
                AlertLevelEnum.CRITICAL.value,
                f'项目成本超支：{project_name}',
                f'项目 {project_code} 成本超支 {overrun_ratio:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，超支：{actual_cost - budget_amount:,.2f}）'
            )
        elif overrun_ratio >= 5:
            return (
                AlertLevelEnum.WARNING.value,
                f'项目成本超支：{project_name}',
                f'项目 {project_code} 成本超支 {overrun_ratio:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，超支：{actual_cost - budget_amount:,.2f}）'
            )
    elif execution_rate >= 90:
        # 接近预算
        return (
            AlertLevelEnum.WARNING.value,
            f'项目成本接近预算：{project_name}',
            f'项目 {project_code} 成本执行率 {execution_rate:.2f}%，接近预算（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，剩余：{budget_amount - actual_cost:,.2f}）'
        )
    elif execution_rate >= 80:
        # 注意
        return (
            AlertLevelEnum.INFO.value,
            f'项目成本执行率较高：{project_name}',
            f'项目 {project_code} 成本执行率 {execution_rate:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}）'
        )

    return None, None, None


def find_existing_alert(
    db: Session,
    project_id: int,
    alert_rule: AlertRule,
    alert_level: str
) -> Optional[AlertRecord]:
    """
    查找现有的预警记录

    Returns:
        Optional[AlertRecord]: 现有预警记录
    """
    return db.query(AlertRecord).filter(
        AlertRecord.target_type == 'PROJECT',
        AlertRecord.target_id == project_id,
        AlertRecord.rule_id == alert_rule.id,
        AlertRecord.alert_level == alert_level,
        AlertRecord.status == AlertStatusEnum.PENDING.value
    ).first()


def generate_alert_no(db: Session) -> str:
    """
    生成预警编号

    Returns:
        str: 预警编号
    """
    today = date.today()
    max_alert_query = db.query(AlertRecord)
    max_alert_query = apply_like_filter(
        max_alert_query,
        AlertRecord,
        f'CO{today.strftime("%Y%m%d")}%',
        "alert_no",
        use_ilike=False,
    )
    max_alert = max_alert_query.order_by(AlertRecord.alert_no.desc()).first()

    if max_alert:
        seq = int(max_alert.alert_no[-4:]) + 1
    else:
        seq = 1

    return f'CO{today.strftime("%Y%m%d")}{str(seq).zfill(4)}'


def create_alert_record(
    db: Session,
    project: Project,
    project_id: int,
    alert_rule: AlertRule,
    alert_level: str,
    alert_title: str,
    alert_content: str,
    budget_amount: float,
    actual_cost: float,
    trigger_source: Optional[str],
    source_id: Optional[int]
) -> AlertRecord:
    """
    创建预警记录

    Returns:
        AlertRecord: 预警记录对象
    """
    alert_no = generate_alert_no(db)

    alert = AlertRecord(
        alert_no=alert_no,
        rule_id=alert_rule.id,
        target_type='PROJECT',
        target_id=project_id,
        target_no=project.project_code,
        target_name=project.project_name,
        project_id=project_id,
        alert_level=alert_level,
        alert_title=alert_title,
        alert_content=alert_content,
        status=AlertStatusEnum.PENDING.value,
        triggered_at=datetime.now(),
        source_module=trigger_source or 'COST',
        source_id=source_id
    )

    db.add(alert)
    db.flush()

    return alert
