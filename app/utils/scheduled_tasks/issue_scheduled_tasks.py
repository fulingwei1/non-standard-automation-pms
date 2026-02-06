# -*- coding: utf-8 -*-
"""
问题管理定时任务模块
包含问题逾期检查、阻塞问题预警、问题升级等任务
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.base import get_db_session
from app.models.issue import Issue, IssueStatisticsSnapshot

# 模块级 logger
logger = logging.getLogger(__name__)


def check_overdue_issues():
    """
    问题逾期预警服务
    每小时执行一次，检查逾期问题并发送提醒
    """
    try:
        with get_db_session() as db:
            from app.models.alert import AlertRecord

            # 查询逾期的问题
            now = datetime.now()
            overdue_issues = db.query(Issue).filter(
                Issue.status.in_(['OPEN', 'IN_PROGRESS']),
                Issue.due_date < now
            ).all()

            alert_count = 0

            for issue in overdue_issues:
                # 检查是否已存在相同预警（使用target_type和target_id）
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'issue',
                    AlertRecord.target_id == issue.id,
                    AlertRecord.alert_title.contains('逾期'),
                    AlertRecord.status == 'PENDING'
                ).first()

                if existing_alert:
                    continue

                # 计算逾期天数
                overdue_days = (now - issue.due_date).days

                # 创建逾期预警
                urgency = 'CRITICAL' if overdue_days >= 7 else 'HIGH' if overdue_days >= 3 else 'MEDIUM'

                alert = AlertRecord(
                    alert_no=f"ALT-IO-{issue.id}-{now.strftime('%Y%m%d%H%M%S')}",
                    rule_id=1,  # 使用默认规则ID
                    target_type='issue',
                    target_id=issue.id,
                    target_no=issue.issue_code if hasattr(issue, 'issue_code') else str(issue.id),
                    target_name=issue.title,
                    alert_title=f'问题逾期预警',
                    alert_content=f'问题 "{issue.title}" 已逾期 {overdue_days} 天，截止日期为 {issue.due_date.strftime("%Y-%m-%d")}，当前状态为 {issue.status}。',
                    alert_level=urgency,
                    status='PENDING',
                    triggered_at=now,
                    project_id=issue.project_id
                )

                db.add(alert)
                alert_count += 1

            db.commit()

            logger.info(f"问题逾期检查完成: 发现 {len(overdue_issues)} 个逾期问题, 生成 {alert_count} 个预警")

            return {
                'overdue_issues': len(overdue_issues),
                'alerts_created': alert_count,
                'timestamp': now.isoformat()
            }

    except Exception as e:
        logger.error(f"问题逾期检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_blocking_issues():
    """
    阻塞问题预警服务
    每小时执行一次，检查阻塞问题并触发项目健康度更新
    """
    try:
        with get_db_session() as db:
            from app.models.alert import AlertRecord

            # 查询阻塞级别的问题（URGENT优先级，状态为OPEN或IN_PROGRESS）
            blocking_issues = db.query(Issue).filter(
                Issue.priority == 'URGENT',
                Issue.status.in_(['OPEN', 'IN_PROGRESS'])
            ).all()

            alert_count = 0

            for issue in blocking_issues:
                # 检查是否已存在相同预警（使用target_type和target_id）
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'issue',
                    AlertRecord.target_id == issue.id,
                    AlertRecord.alert_title.contains('阻塞'),
                    AlertRecord.status == 'PENDING'
                ).first()

                if existing_alert:
                    continue

                # 计算问题存在时间
                days_open = (datetime.now() - issue.created_at).days if issue.created_at else 0

                # 创建阻塞预警
                alert = AlertRecord(
                    alert_no=f"ALT-IB-{issue.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    rule_id=1,  # 使用默认规则ID
                    target_type='issue',
                    target_id=issue.id,
                    target_no=issue.issue_code if hasattr(issue, 'issue_code') else str(issue.id),
                    target_name=issue.title,
                    alert_title=f'阻塞问题预警',
                    alert_content=f'紧急问题 "{issue.title}" 已存在 {days_open} 天仍未解决，可能影响项目进度。问题描述：{issue.description[:100] if issue.description else ""}...',
                    alert_level='CRITICAL',
                    status='PENDING',
                    triggered_at=datetime.now(),
                    project_id=issue.project_id
                )

                db.add(alert)
                alert_count += 1

            db.commit()

            logger.info(f"阻塞问题检查完成: 发现 {len(blocking_issues)} 个阻塞问题, 生成 {alert_count} 个预警")

            return {
                'blocking_issues': len(blocking_issues),
                'alerts_created': alert_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"阻塞问题检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_timeout_issues():
    """
    问题超时升级服务
    每天执行一次，检查长时间未处理的问题并自动升级
    """
    try:
        with get_db_session() as db:

            # 查询超时未处理的问题（超过7天未更新）
            timeout_threshold = datetime.now() - timedelta(days=7)
            timeout_issues = db.query(Issue).filter(
                Issue.status.in_(['OPEN', 'IN_PROGRESS']),
                Issue.updated_at < timeout_threshold).all()

            upgraded_count = 0

            for issue in timeout_issues:
                # 自动升级优先级
                if issue.priority == 'LOW':
                    issue.priority = 'MEDIUM'
                    upgraded_count += 1
                elif issue.priority == 'MEDIUM':
                    issue.priority = 'HIGH'
                    upgraded_count += 1
                elif issue.priority == 'HIGH':
                    issue.priority = 'URGENT'
                    upgraded_count += 1

                # 记录跟进
                from app.models.issue import IssueFollowUpRecord
                follow_up = IssueFollowUpRecord(
                    issue_id=issue.id,
                    follow_up_type='STATUS_CHANGE',
                    content=f'问题超时自动升级优先级至 {issue.priority}',
                    operator_id=None,  # 系统自动操作
                    operator_name='系统',
                    old_status=issue.status,
                    new_status=issue.status
                )
                db.add(follow_up)
                db.add(issue)

            db.commit()

            logger.info(f"问题超时检查完成: 发现 {len(timeout_issues)} 个超时问题, 升级 {upgraded_count} 个问题优先级")

            return {
                'timeout_count': len(timeout_issues),
                'upgraded_count': upgraded_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"问题超时检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_issue_statistics_snapshot():
    """
    问题统计快照服务
    每天凌晨3点执行，生成问题统计快照并保存到数据库
    """
    try:
        with get_db_session() as db:

            # 计算统计数据
            total_issues = db.query(Issue).filter().count()
            open_issues = db.query(Issue).filter(
                Issue.status == 'OPEN').count()
            processing_issues = db.query(Issue).filter(
                Issue.status == 'IN_PROGRESS').count()
            resolved_issues = db.query(Issue).filter(
                Issue.status == 'RESOLVED').count()

            # ��优先级统计
            urgent_issues = db.query(Issue).filter(
                Issue.priority == 'URGENT').count()
            high_priority_issues = db.query(Issue).filter(
                Issue.priority == 'HIGH').count()
            medium_priority_issues = db.query(Issue).filter(
                Issue.priority == 'MEDIUM').count()
            low_priority_issues = db.query(Issue).filter(
                Issue.priority == 'LOW').count()

            # 按项目统计
            project_stats = db.query(
                Issue.project_id,
                func.count(Issue.id).label('issue_count')
            ).filter(
                Issue.project_id.isnot(None)).group_by(Issue.project_id).all()

            # 创建统计快照
            snapshot = IssueStatisticsSnapshot(
                snapshot_date=datetime.now().date(),
                total_issues=total_issues,
                open_issues=open_issues,
                processing_issues=processing_issues,
                resolved_issues=resolved_issues,
                urgent_issues=urgent_issues,
                high_priority_issues=high_priority_issues,
                medium_priority_issues=medium_priority_issues,
                low_priority_issues=low_priority_issues,
                status_distribution={str(p.project_id): p.issue_count for p in project_stats}
            )

            db.add(snapshot)
            db.commit()

            logger.info(f"问题统计快照生成完成: 总问题数 {total_issues}, 待处理 {open_issues}, 进行中 {processing_issues}, 已解决 {resolved_issues}")

            return {
                'total_issues': total_issues,
                'open_issues': open_issues,
                'processing_issues': processing_issues,
                'resolved_issues': resolved_issues,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"问题统计快照生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_issue_assignment_timeout():
    """
    问题分配超时检查
    每小时执行一次，检查长时间未分配的问题
    """
    try:
        with get_db_session() as db:
            from app.models.alert import AlertRecord

            # 查询24小时内未分配的问题
            assignment_timeout = datetime.now() - timedelta(hours=24)
            unassigned_issues = db.query(Issue).filter(
                Issue.status == 'OPEN',
                Issue.assignee_id.is_(None),
                Issue.created_at < assignment_timeout).all()

            alert_count = 0

            for issue in unassigned_issues:
                # 检查是否已存在相同预警（使用target_type和target_id）
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'issue',
                    AlertRecord.target_id == issue.id,
                    AlertRecord.alert_title.contains('分配超时'),
                    AlertRecord.status == 'PENDING'
                ).first()

                if existing_alert:
                    continue

                # 创建分配超时预警
                alert = AlertRecord(
                    alert_no=f"ALT-IA-{issue.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    rule_id=1,  # 使用默认规则ID
                    target_type='issue',
                    target_id=issue.id,
                    target_no=issue.issue_code if hasattr(issue, 'issue_code') else str(issue.id),
                    target_name=issue.title,
                    alert_title=f'问题分配超时预警',
                    alert_content=f'问题 "{issue.title}" 已创建超过24小时仍未分配处理人，请及时分配。',
                    alert_level='MEDIUM',
                    status='PENDING',
                    triggered_at=datetime.now(),
                    project_id=issue.project_id
                )

                db.add(alert)
                alert_count += 1

            db.commit()

            logger.info(f"问题分配超时检查完成: 发现 {len(unassigned_issues)} 个未分配问题, 生成 {alert_count} 个预警")

            return {
                'unassigned_issues': len(unassigned_issues),
                'alerts_created': alert_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"问题分配超时检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_issue_resolution_timeout():
    """
    问题解决超时检查
    每天执行一次，检查超过预期解决时间的问题
    """
    try:
        with get_db_session() as db:
            from app.models.alert import AlertRecord

            # 查询超过预期解决时间的问题（使用due_date字段）
            now = datetime.now()
            overdue_resolution_issues = db.query(Issue).filter(
                Issue.status == 'IN_PROGRESS',
                Issue.due_date.isnot(None),
                Issue.due_date < now.date()).all()

            alert_count = 0

            for issue in overdue_resolution_issues:
                # 检查是否已存在相同预警（使用target_type和target_id）
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'issue',
                    AlertRecord.target_id == issue.id,
                    AlertRecord.alert_title.contains('解决超时'),
                    AlertRecord.status == 'PENDING'
                ).first()

                if existing_alert:
                    continue

                # 计算超时天数
                overdue_days = (now.date() - issue.due_date).days

                # 创建解决超时预警
                urgency = 'HIGH' if overdue_days >= 3 else 'MEDIUM'

                alert = AlertRecord(
                    alert_no=f"ALT-IR-{issue.id}-{now.strftime('%Y%m%d%H%M%S')}",
                    rule_id=1,  # 使用默认规则ID
                    target_type='issue',
                    target_id=issue.id,
                    target_no=issue.issue_code if hasattr(issue, 'issue_code') else str(issue.id),
                    target_name=issue.title,
                    alert_title=f'问题解决超时预警',
                    alert_content=f'问题 "{issue.title}" 已超过预期解决时间 {overdue_days} 天，截止日期为 {issue.due_date.strftime("%Y-%m-%d")}。',
                    alert_level=urgency,
                    status='PENDING',
                    triggered_at=now,
                    project_id=issue.project_id
                )

                db.add(alert)
                alert_count += 1

            db.commit()

            logger.info(f"问题解决超时检查完成: 发现 {len(overdue_resolution_issues)} 个超时问题, 生成 {alert_count} 个预警")

            return {
                'overdue_resolution_issues': len(overdue_resolution_issues),
                'alerts_created': alert_count,
                'timestamp': now.isoformat()
            }

    except Exception as e:
        logger.error(f"问题解决超时检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# 导出所有任务函数
__all__ = [
    'check_overdue_issues',
    'check_blocking_issues',
    'check_timeout_issues',
    'daily_issue_statistics_snapshot',
    'check_issue_assignment_timeout',
    'check_issue_resolution_timeout',
]
