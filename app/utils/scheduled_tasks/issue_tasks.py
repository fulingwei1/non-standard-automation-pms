# -*- coding: utf-8 -*-
"""
定时任务 - 问题管理任务
包含：逾期问题检查、阻塞问题预警、超时问题升级、问题统计快照
"""
import logging
from datetime import date, datetime, timedelta

from app.models.alert import AlertRecord, AlertRule
from app.models.base import get_db_session
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
from app.models.issue import Issue, IssueStatisticsSnapshot
from app.models.project import Project

logger = logging.getLogger(__name__)


def check_overdue_issues():
    """
    问题逾期预警服务
    每小时执行一次，检查逾期问题并发送提醒
    """
    try:
        with get_db_session() as db:
            from app.services.sales_reminder import create_notification

            today = date.today()

            # 查询逾期问题（状态为OPEN或PROCESSING，且due_date < today）
            overdue_issues = db.query(Issue).filter(
                Issue.status.in_(['OPEN', 'PROCESSING']),
                Issue.due_date.isnot(None),
                Issue.due_date < today,
                Issue.status != 'DELETED'
            ).all()

            notified_count = 0

            for issue in overdue_issues:
                # 发送通知给处理人
                if issue.assignee_id:
                    try:
                        create_notification(
                            db=db,
                            user_id=issue.assignee_id,
                            notification_type='ISSUE_OVERDUE',
                            title=f'问题已逾期：{issue.title}',
                            content=f'问题 {issue.issue_no} 已逾期，要求完成日期：{issue.due_date}',
                            source_type='ISSUE',
                            source_id=issue.id,
                            link_url=f'/issues/{issue.id}',
                            priority='HIGH'
                        )
                        notified_count += 1
                    except Exception as e:
                        logger.error(f"发送逾期提醒失败 (问题ID: {issue.id}): {str(e)}")

                # 发送通知给项目经理（如果有项目）
                if issue.project_id:
                    project = db.query(Project).filter(Project.id == issue.project_id).first()
                    if project and project.pm_id and project.pm_id != issue.assignee_id:
                        try:
                            create_notification(
                                db=db,
                                user_id=project.pm_id,
                                notification_type='ISSUE_OVERDUE',
                                title=f'项目问题已逾期：{issue.title}',
                                content=f'项目 {project.project_name} 的问题 {issue.issue_no} 已逾期',
                                source_type='ISSUE',
                                source_id=issue.id,
                                link_url=f'/issues/{issue.id}',
                                priority='HIGH'
                            )
                        except Exception as e:
                            logger.error(f"发送逾期提醒给PM失败 (问题ID: {issue.id}): {str(e)}")

            db.commit()

            logger.info(
                f"[{datetime.now()}] 问题逾期检查完成: "
                f"发现 {len(overdue_issues)} 个逾期问题, 发送 {notified_count} 条通知"
            )

            return {
                'overdue_count': len(overdue_issues),
                'notified_count': notified_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 问题逾期检查失败: {str(e)}")
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
            from app.services.health_calculator import HealthCalculator

            # 查询所有阻塞问题（is_blocking=True 且状态为OPEN或PROCESSING）
            blocking_issues = db.query(Issue).filter(
                Issue.is_blocking == True,
                Issue.status.in_(['OPEN', 'PROCESSING']),
                Issue.status != 'DELETED'
            ).all()

            affected_projects = set()

            for issue in blocking_issues:
                if issue.project_id:
                    affected_projects.add(issue.project_id)

                    # 创建或更新预警记录
                    rule = db.query(AlertRule).filter(
                        AlertRule.rule_code == 'BLOCKING_ISSUE',
                        AlertRule.is_enabled == True
                    ).first()

                    if not rule:
                        # 创建默认规则（如果不存在）
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

                    # 检查是否已有预警记录
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'ISSUE',
                        AlertRecord.target_id == issue.id,
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if not existing_alert:
                        # 生成预警编号
                        today = datetime.now().strftime('%Y%m%d')
                        count = db.query(AlertRecord).filter(
                            AlertRecord.alert_no.like(f'AL{today}%')
                        ).count()
                        alert_no = f'AL{today}{str(count + 1).zfill(4)}'

                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=rule.id,
                            target_type='ISSUE',
                            target_id=issue.id,
                            target_no=issue.issue_no,
                            target_name=issue.title,
                            project_id=issue.project_id,
                            alert_level=AlertLevelEnum.WARNING.value,
                            alert_title=f'阻塞问题：{issue.title}',
                            alert_content=f'问题 {issue.issue_no} 标记为阻塞问题，可能影响项目进度',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now()
                        )
                        db.add(alert)

            # 更新受影响项目的健康度
            calculator = HealthCalculator(db)
            updated_count = 0
            for project_id in affected_projects:
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    calculator.calculate_health(project)
                    updated_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 阻塞问题检查完成: "
                f"发现 {len(blocking_issues)} 个阻塞问题, "
                f"影响 {len(affected_projects)} 个项目, 更新 {updated_count} 个项目健康度"
            )

            return {
                'blocking_count': len(blocking_issues),
                'affected_projects': len(affected_projects),
                'health_updated': updated_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 阻塞问题检查失败: {str(e)}")
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
            # 查询超过7天未处理的问题
            timeout_threshold = datetime.now() - timedelta(days=7)

            timeout_issues = db.query(Issue).filter(
                Issue.status.in_(['OPEN', 'PROCESSING']),
                Issue.status != 'DELETED',
                (
                    (Issue.last_follow_up_at.is_(None)) |
                    (Issue.last_follow_up_at < timeout_threshold)
                )
            ).all()

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

                db.add(issue)

            db.commit()

            logger.info(
                f"[{datetime.now()}] 问题超时检查完成: "
                f"发现 {len(timeout_issues)} 个超时问题, 升级 {upgraded_count} 个问题优先级"
            )

            return {
                'timeout_count': len(timeout_issues),
                'upgraded_count': upgraded_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 问题超时检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_issue_statistics_snapshot():
    """
    问题统计快照服务
    每天凌晨3点执行，生成问题统计快照并保存到数据库
    """
    from app.services.issue_statistics_service import (
        build_distribution_data,
        calculate_avg_resolve_time,
        check_existing_snapshot,
        count_blocking_and_overdue_issues,
        count_issues_by_category,
        count_issues_by_priority,
        count_issues_by_severity,
        count_issues_by_status,
        count_issues_by_type,
        count_today_issues,
        create_snapshot_record,
    )

    try:
        with get_db_session() as db:
            today = date.today()

            # 检查今天是否已生成快照
            if check_existing_snapshot(db, today):
                logger.info(f"[{datetime.now()}] 今日快照已存在，跳过生成")
                return {'message': 'Snapshot already exists for today'}

            # 统计各类问题数量
            status_counts = count_issues_by_status(db)
            severity_counts = count_issues_by_severity(db)
            priority_counts = count_issues_by_priority(db)
            type_counts = count_issues_by_type(db)
            blocking_overdue = count_blocking_and_overdue_issues(db, today)
            category_counts = count_issues_by_category(db)
            today_counts = count_today_issues(db, today)
            avg_resolve_time = calculate_avg_resolve_time(db)

            # 生成分布数据
            distributions = build_distribution_data(
                status_counts, severity_counts, priority_counts, category_counts
            )

            # 创建快照记录
            snapshot = create_snapshot_record(
                db, today, status_counts, severity_counts, priority_counts,
                type_counts, blocking_overdue, category_counts, today_counts,
                avg_resolve_time, distributions
            )

            db.commit()

            logger.info(
                f"问题统计快照 [{today.isoformat()}]: "
                f"总计={status_counts['total']}, 待处理={status_counts['open']}, "
                f"处理中={status_counts['processing']}, 已解决={status_counts['resolved']}, "
                f"已关闭={status_counts['closed']}, 阻塞={blocking_overdue['blocking']}, "
                f"逾期={blocking_overdue['overdue']}"
            )

            return {
                'snapshot_date': today.isoformat(),
                'total_issues': status_counts['total'],
                'open_issues': status_counts['open'],
                'processing_issues': status_counts['processing'],
                'resolved_issues': status_counts['resolved'],
                'closed_issues': status_counts['closed'],
                'blocking_issues': blocking_overdue['blocking'],
                'overdue_issues': blocking_overdue['overdue'],
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 问题统计快照生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
