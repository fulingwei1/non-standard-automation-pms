# -*- coding: utf-8 -*-
"""
问题管理工具函数

包含：预警创建/关闭、编号生成等
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
from app.models.issue import Issue


def create_blocking_issue_alert(db: Session, issue: Issue) -> Optional[AlertRecord]:
    """
    为阻塞问题创建预警记录

    Args:
        db: 数据库会话
        issue: 问题对象

    Returns:
        AlertRecord: 创建的预警记录，如果已存在则返回None
    """
    if not issue.is_blocking or issue.status == 'DELETED':
        return None

    # 检查是否已有预警记录
    existing_alert = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'ISSUE',
        AlertRecord.target_id == issue.id,
        AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED', 'PROCESSING'])
    ).first()

    if existing_alert:
        return None  # 已存在预警，不重复创建

    # 获取或创建预警规则
    rule = db.query(AlertRule).filter(
        AlertRule.rule_code == 'BLOCKING_ISSUE',
        AlertRule.is_enabled
    ).first()

    if not rule:
        # 创建默认规则
        rule = AlertRule(
            rule_code='BLOCKING_ISSUE',
            rule_name='阻塞问题预警',
            rule_type=AlertRuleTypeEnum.QUALITY_ISSUE.value,
            target_type='ISSUE',
            condition_type='THRESHOLD',
            condition_operator='EQ',
            threshold_value='1',
            alert_level=AlertLevelEnum.WARNING.value,
            is_enabled=True,
            is_system=True,
            description='当问题被标记为阻塞时触发预警'
        )
        db.add(rule)
        db.flush()

    # 根据问题严重程度设置预警级别
    alert_level = AlertLevelEnum.WARNING.value
    if issue.severity == 'CRITICAL':
        alert_level = AlertLevelEnum.URGENT.value
    elif issue.severity == 'MAJOR':
        alert_level = AlertLevelEnum.CRITICAL.value
    elif issue.severity == 'MINOR':
        alert_level = AlertLevelEnum.WARNING.value

    # 生成预警编号
    today = datetime.now().strftime('%Y%m%d')
    count_query = db.query(AlertRecord)
    count_query = apply_like_filter(
        count_query,
        AlertRecord,
        f'AL{today}%',
        "alert_no",
        use_ilike=False,
    )
    count = count_query.count()
    alert_no = f'AL{today}{str(count + 1).zfill(4)}'

    # 构建预警内容
    alert_content = f'问题 {issue.issue_no} 标记为阻塞问题'
    if issue.impact_scope:
        alert_content += f'，影响范围：{issue.impact_scope}'
    if issue.description:
        alert_content += f'。问题描述：{issue.description[:100]}'

    # 创建预警记录
    alert = AlertRecord(
        alert_no=alert_no,
        rule_id=rule.id,
        target_type='ISSUE',
        target_id=issue.id,
        target_no=issue.issue_no,
        target_name=issue.title,
        project_id=issue.project_id,
        machine_id=issue.machine_id,
        alert_level=alert_level,
        alert_title=f'阻塞问题：{issue.title}',
        alert_content=alert_content,
        alert_data={
            'issue_no': issue.issue_no,
            'severity': issue.severity,
            'priority': issue.priority,
            'impact_scope': issue.impact_scope,
            'impact_level': issue.impact_level,
        },
        status=AlertStatusEnum.PENDING.value,
        triggered_at=datetime.now()
    )

    db.add(alert)
    db.flush()

    return alert


def close_blocking_issue_alerts(db: Session, issue: Issue) -> int:
    """
    关闭阻塞问题的相关预警记录

    Args:
        db: 数据库会话
        issue: 问题对象

    Returns:
        int: 关闭的预警数量
    """
    # 查找所有待处理/已确认/处理中的预警
    alerts = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'ISSUE',
        AlertRecord.target_id == issue.id,
        AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED', 'PROCESSING'])
    ).all()

    closed_count = 0
    for alert in alerts:
        alert.status = AlertStatusEnum.RESOLVED.value
        alert.handle_end_at = datetime.now()
        alert.handle_result = f'问题 {issue.issue_no} 已解决，自动关闭预警'
        closed_count += 1

    return closed_count


def generate_issue_no(db: Session) -> str:
    """生成问题编号"""
    today = datetime.now().strftime('%Y%m%d')
    count_query = db.query(Issue)
    count_query = apply_like_filter(
        count_query,
        Issue,
        f'IS{today}%',
        "issue_no",
        use_ilike=False,
    )
    count = count_query.count()
    return f'IS{today}{str(count + 1).zfill(3)}'
