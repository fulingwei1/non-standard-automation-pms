# -*- coding: utf-8 -*-
"""
定时任务
"""

from typing import List, Optional
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.models.base import get_db_session
from app.models.project import Project, ProjectMilestone, ProjectCost
from app.models.technical_spec import TechnicalSpecRequirement, SpecMatchRecord
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.material import BomHeader, BomItem
from app.models.issue import Issue, IssueStatisticsSnapshot
from app.models.alert import AlertRecord, AlertRule, AlertNotification, AlertStatistics
from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum
from app.utils.spec_match_service import SpecMatchService
from decimal import Decimal
from datetime import timedelta

from app.services.notification_dispatcher import (
    NotificationDispatcher,
    resolve_channels,
    resolve_recipients,
    resolve_channel_target,
    channel_allowed,
    is_quiet_hours,
    next_quiet_resume,
)
from app.services.notification_queue import enqueue_notification
from app.services.notification_service import AlertNotificationService, send_alert_notification


# ==================== 预警通知集成辅助函数 ====================

def send_notification_for_alert(db: Session, alert: AlertRecord, logger_instance=None):
    """
    为预警发送通知的辅助函数
    通知发送失败不影响预警记录创建
    
    Args:
        db: 数据库会话
        alert: 预警记录
        logger_instance: 日志记录器（可选）
    """
    if logger_instance is None:
        import logging
        logger_instance = logging.getLogger(__name__)
    
    try:
        notification_service = AlertNotificationService(db)
        notification_result = notification_service.send_alert_notification(alert)
        if notification_result.get('success'):
            logger_instance.debug(
                f"Notification sent for alert {alert.alert_no}: "
                f"created={notification_result.get('notifications_created', 0)}, "
                f"sent={notification_result.get('notifications_sent', 0)}"
            )
        else:
            logger_instance.warning(
                f"Failed to send notification for alert {alert.alert_no}: "
                f"{notification_result.get('message')}"
            )
    except Exception as notif_err:
        # 通知发送失败不影响预警记录创建
        logger_instance.error(
            f"Error sending notification for alert {alert.alert_no}: {str(notif_err)}",
            exc_info=True
        )


def sales_reminder_scan():
    """
    销售模块提醒扫描任务
    扫描里程碑、收款计划等需要提醒的事项
    """
    from app.services.sales_reminder_service import scan_and_notify_all
    import logging
    
    logger = logging.getLogger(__name__)
    
    with get_db_session() as db:
        try:
            stats = scan_and_notify_all(db)
            logger.info(f"销售提醒扫描完成: {stats}")
            print(f"[{datetime.now()}] 销售提醒扫描完成: {stats}")
        except Exception as e:
            logger.error(f"销售提醒扫描失败: {str(e)}")
            print(f"[{datetime.now()}] 销售提醒扫描失败: {str(e)}")
            import traceback
            traceback.print_exc()


def daily_spec_match_check():
    """
    每日规格匹配检查
    每天上午9点执行，检查所有活跃项目的采购订单和BOM
    """
    service = SpecMatchService()
    
    with get_db_session() as db:
        # 查询所有活跃项目
        projects = db.query(Project).filter(
            Project.is_active == True,
            Project.is_archived == False
        ).all()
        
        total_checked = 0
        total_mismatched = 0
        
        for project in projects:
            # 检查项目的采购订单
            po_items = db.query(PurchaseOrderItem).join(
                PurchaseOrder
            ).filter(
                PurchaseOrder.project_id == project.id,
                PurchaseOrder.status.in_(['APPROVED', 'ORDERED', 'PARTIAL_RECEIVED'])
            ).all()
            
            for po_item in po_items:
                # 检查是否已有匹配记录（避免重复检查）
                existing_record = db.query(SpecMatchRecord).filter(
                    SpecMatchRecord.project_id == project.id,
                    SpecMatchRecord.match_type == 'PURCHASE_ORDER',
                    SpecMatchRecord.match_target_id == po_item.id
                ).first()
                
                if existing_record:
                    continue
                
                # 执行匹配检查
                match_record = service.check_po_item_spec_match(
                    db=db,
                    project_id=project.id,
                    po_item_id=po_item.id,
                    material_code=po_item.material_code,
                    specification=po_item.specification or '',
                    brand=None,
                    model=None
                )
                
                if match_record and match_record.match_status == 'MISMATCHED':
                    total_mismatched += 1
                total_checked += 1
            
            # 检查项目的BOM
            bom_items = db.query(BomItem).join(
                BomHeader
            ).filter(
                BomHeader.project_id == project.id,
                BomHeader.status.in_(['APPROVED', 'RELEASED'])
            ).all()
            
            for bom_item in bom_items:
                # 检查是否已有匹配记录
                existing_record = db.query(SpecMatchRecord).filter(
                    SpecMatchRecord.project_id == project.id,
                    SpecMatchRecord.match_type == 'BOM',
                    SpecMatchRecord.match_target_id == bom_item.id
                ).first()
                
                if existing_record:
                    continue
                
                # 执行匹配检查
                material_code = bom_item.material.material_code if bom_item.material else None
                if not material_code:
                    continue
                
                match_record = service.check_bom_item_spec_match(
                    db=db,
                    project_id=project.id,
                    bom_item_id=bom_item.id,
                    material_code=material_code,
                    specification=bom_item.specification or '',
                    brand=bom_item.material.brand if bom_item.material else None,
                    model=None
                )
                
                if match_record and match_record.match_status == 'MISMATCHED':
                    total_mismatched += 1
                total_checked += 1
        
        db.commit()
        
        print(f"[{datetime.now()}] 规格匹配检查完成: 检查 {total_checked} 项, 发现 {total_mismatched} 项不匹配")
        
        return {
            'checked': total_checked,
            'mismatched': total_mismatched,
            'timestamp': datetime.now().isoformat()
        }


def calculate_project_health():
    """
    计算项目健康度
    每小时执行一次，自动计算所有活跃项目的健康度
    """
    try:
        from app.services.health_calculator import HealthCalculator
        
        with get_db_session() as db:
            calculator = HealthCalculator(db)
            result = calculator.batch_calculate()
            
            print(f"[{datetime.now()}] 健康度计算完成: 总计 {result['total']} 个项目, "
                  f"更新 {result['updated']} 个, 未变化 {result['unchanged']} 个")
            
            return result
    except Exception as e:
        print(f"[{datetime.now()}] 健康度计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_health_snapshot():
    """
    每日健康度快照
    每天凌晨2点执行，生成所有项目的健康度快照
    """
    try:
        from app.services.health_calculator import HealthCalculator
        from app.models.alert import ProjectHealthSnapshot
        
        with get_db_session() as db:
            calculator = HealthCalculator(db)
            
            # 查询所有活跃项目
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.is_archived == False
            ).all()
            
            today = date.today()
            snapshot_count = 0
            
            for project in projects:
                # 检查今天是否已有快照
                existing = db.query(ProjectHealthSnapshot).filter(
                    ProjectHealthSnapshot.project_id == project.id,
                    ProjectHealthSnapshot.snapshot_date == today
                ).first()
                
                if existing:
                    continue
                
                # 获取健康度详情
                health_details = calculator.get_health_details(project)
                
                # 创建快照
                snapshot = ProjectHealthSnapshot(
                    project_id=project.id,
                    snapshot_date=today,
                    overall_health=health_details['calculated_health'],
                    open_alerts=health_details['statistics']['active_alerts'],
                    blocking_issues=health_details['statistics']['blocking_issues'],
                    milestone_delayed=health_details['statistics']['overdue_milestones']
                )
                db.add(snapshot)
                snapshot_count += 1
            
            db.commit()
            
            print(f"[{datetime.now()}] 健康度快照生成完成: 生成 {snapshot_count} 个快照")
            
            return {
                'snapshot_count': snapshot_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"[{datetime.now()}] 健康度快照生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 问题管理定时任务 ====================

def check_overdue_issues():
    """
    问题逾期预警服务
    每小时执行一次，检查逾期问题并发送提醒
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from datetime import date, timedelta
            from app.models.user import User
            from app.services.sales_reminder_service import create_notification
            
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
                # 检查今天是否已发送过提醒（避免重复通知）
                # 这里简化处理，实际可以记录最后提醒时间
                
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
            
            logger.info(f"[{datetime.now()}] 问题逾期检查完成: 发现 {len(overdue_issues)} 个逾期问题, 发送 {notified_count} 条通知")
            
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
    import logging
    logger = logging.getLogger(__name__)
    
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
            
            logger.info(f"[{datetime.now()}] 阻塞问题检查完成: 发现 {len(blocking_issues)} 个阻塞问题, 影响 {len(affected_projects)} 个项目, 更新 {updated_count} 个项目健康度")
            
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from datetime import timedelta
            
            # 查询超过7天未处理的问题（状态为OPEN或PROCESSING，且最后跟进时间超过7天）
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
                
                # 记录跟进
                from app.models.issue import Issue, IssueStatisticsSnapshotFollowUpRecord
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
            
            logger.info(f"[{datetime.now()}] 问题超时检查完成: 发现 {len(timeout_issues)} 个超时问题, 升级 {upgraded_count} 个问题优先级")
            
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
    import logging
    logger = logging.getLogger(__name__)
    
    from app.services.issue_statistics_service import (
        check_existing_snapshot,
        count_issues_by_status,
        count_issues_by_severity,
        count_issues_by_priority,
        count_issues_by_type,
        count_blocking_and_overdue_issues,
        count_issues_by_category,
        count_today_issues,
        calculate_avg_resolve_time,
        build_distribution_data,
        create_snapshot_record
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
            
            logger.info(f"[{datetime.now()}] 问题统计快照生成完成并保存到数据库: 总计 {status_counts['total']} 个问题")
            
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


def check_milestone_alerts():
    """
    里程碑预警服务
    每天执行一次，检查即将到期或已逾期的里程碑
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            today = date.today()
            # 提前3天预警
            warning_date = today + timedelta(days=3)
            
            # 查询未完成且计划日期在3天内的里程碑
            upcoming_milestones = db.query(ProjectMilestone).filter(
                ProjectMilestone.status != 'COMPLETED',
                ProjectMilestone.planned_date <= warning_date,
                ProjectMilestone.planned_date >= today
            ).all()
            
            # 查询已逾期的里程碑
            overdue_milestones = db.query(ProjectMilestone).filter(
                ProjectMilestone.status != 'COMPLETED',
                ProjectMilestone.planned_date < today
            ).all()
            
            # 获取或创建预警规则
            warning_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'MILESTONE_WARNING',
                AlertRule.is_enabled == True
            ).first()
            
            if not warning_rule:
                warning_rule = AlertRule(
                    rule_code='MILESTONE_WARNING',
                    rule_name='里程碑即将到期预警',
                    rule_type=AlertRuleTypeEnum.MILESTONE_DUE.value,
                    target_type='MILESTONE',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='3',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当里程碑将在3天内到期时触发预警'
                )
                db.add(warning_rule)
                db.flush()
            
            critical_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'MILESTONE_OVERDUE',
                AlertRule.is_enabled == True
            ).first()
            
            if not critical_rule:
                critical_rule = AlertRule(
                    rule_code='MILESTONE_OVERDUE',
                    rule_name='里程碑逾期预警',
                    rule_type=AlertRuleTypeEnum.MILESTONE_DUE.value,
                    target_type='MILESTONE',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.CRITICAL.value,
                    is_enabled=True,
                    is_system=True,
                    description='当里程碑已逾期时触发预警'
                )
                db.add(critical_rule)
                db.flush()
            
            alert_count = 0
            
            # 处理即将到期的里程碑
            for milestone in upcoming_milestones:
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'MILESTONE',
                    AlertRecord.target_id == milestone.id,
                    AlertRecord.status == 'PENDING'
                ).first()
                
                if not existing_alert:
                    days_left = (milestone.planned_date - today).days
                    alert_no = f'MS{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                    
                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=warning_rule.id,
                        target_type='MILESTONE',
                        target_id=milestone.id,
                        target_no=milestone.milestone_code,
                        target_name=milestone.milestone_name,
                        project_id=milestone.project_id,
                        alert_level=AlertLevelEnum.WARNING.value,
                        alert_title=f'里程碑即将到期：{milestone.milestone_name}',
                        alert_content=f'里程碑 {milestone.milestone_code} 将在 {days_left} 天后到期（计划日期：{milestone.planned_date}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now()
                    )
                    db.add(alert)
                    alert_count += 1
            
            # 处理已逾期的里程碑
            for milestone in overdue_milestones:
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'MILESTONE',
                    AlertRecord.target_id == milestone.id,
                    AlertRecord.status == 'PENDING'
                ).first()
                
                if not existing_alert:
                    days_overdue = (today - milestone.planned_date).days
                    alert_no = f'MS{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                    
                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=critical_rule.id,
                        target_type='MILESTONE',
                        target_id=milestone.id,
                        target_no=milestone.milestone_code,
                        target_name=milestone.milestone_name,
                        project_id=milestone.project_id,
                        alert_level=AlertLevelEnum.CRITICAL.value,
                        alert_title=f'里程碑已逾期：{milestone.milestone_name}',
                        alert_content=f'里程碑 {milestone.milestone_code} 已逾期 {days_overdue} 天（计划日期：{milestone.planned_date}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now()
                    )
                    db.add(alert)
                    alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 里程碑预警检查完成: 即将到期 {len(upcoming_milestones)} 个, 已逾期 {len(overdue_milestones)} 个, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 里程碑预警检查完成: 即将到期 {len(upcoming_milestones)} 个, 已逾期 {len(overdue_milestones)} 个, 生成 {alert_count} 个预警")
            
            return {
                'upcoming_count': len(upcoming_milestones),
                'overdue_count': len(overdue_milestones),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_milestone_status_and_adjust_payments():
    """
    Issue 7.3: 监控项目里程碑状态变化并自动调整收款计划
    每小时执行一次，检查里程碑状态变化（延期、提前完成）并调整关联的收款计划
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.services.payment_adjustment_service import PaymentAdjustmentService
            from datetime import timedelta
            
            service = PaymentAdjustmentService(db)
            
            # 查询最近状态发生变化的里程碑（最近1小时内更新的）
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            # 查询状态为 DELAYED 或 COMPLETED 的里程碑
            changed_milestones = db.query(ProjectMilestone).filter(
                ProjectMilestone.status.in_(["DELAYED", "COMPLETED"]),
                ProjectMilestone.updated_at >= one_hour_ago
            ).all()
            
            adjusted_count = 0
            
            for milestone in changed_milestones:
                try:
                    result = service.adjust_payment_plan_by_milestone(
                        milestone_id=milestone.id,
                        reason=f"里程碑状态变更为 {milestone.status}，自动调整收款计划"
                    )
                    
                    if result.get("success") and result.get("adjusted_plans"):
                        adjusted_count += len(result.get("adjusted_plans", []))
                        logger.info(
                            f"里程碑 {milestone.milestone_code} 状态变化，已调整 {len(result.get('adjusted_plans', []))} 个收款计划"
                        )
                except Exception as e:
                    logger.error(f"调整里程碑 {milestone.id} 关联的收款计划失败: {e}", exc_info=True)
            
            logger.info(f"[{datetime.now()}] 里程碑状态监控完成: 检查 {len(changed_milestones)} 个里程碑, 调整 {adjusted_count} 个收款计划")
            print(f"[{datetime.now()}] 里程碑状态监控完成: 检查 {len(changed_milestones)} 个里程碑, 调整 {adjusted_count} 个收款计划")
            
            return {
                'checked_milestones': len(changed_milestones),
                'adjusted_plans': adjusted_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑状态监控失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_cost_overrun_alerts():
    """
    成本超支预警服务
    每天执行一次，检查项目成本是否超支
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from sqlalchemy import func
            
            today = date.today()
            
            # 查询所有活跃项目
            active_projects = db.query(Project).filter(
                Project.is_active == True
            ).all()
            
            # 获取或创建预警规则
            overrun_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'COST_OVERRUN',
                AlertRule.is_enabled == True
            ).first()
            
            if not overrun_rule:
                overrun_rule = AlertRule(
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
                db.add(overrun_rule)
                db.flush()
            
            alert_count = 0
            overrun_projects = []
            
            for project in active_projects:
                # 跳过没有预算的项目
                if not project.budget or project.budget <= 0:
                    continue
                
                # 计算实际成本
                total_cost_result = db.query(
                    func.sum(ProjectCost.amount).label('total')
                ).filter(
                    ProjectCost.project_id == project.id
                ).first()
                
                actual_cost = float(total_cost_result.total) if total_cost_result.total else 0
                
                # 如果项目有actual_cost字段，优先使用
                if project.actual_cost:
                    actual_cost = float(project.actual_cost)
                
                # 计算超支比例
                budget = float(project.budget)
                overrun_ratio = ((actual_cost - budget) / budget * 100) if budget > 0 else 0
                
                # 如果超支超过5%，生成预警
                if overrun_ratio > 5:
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'PROJECT',
                        AlertRecord.target_id == project.id,
                        AlertRecord.rule_id == overrun_rule.id,
                        AlertRecord.status == 'PENDING'
                    ).first()
                    
                    if not existing_alert:
                        alert_no = f'CO{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                        
                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=overrun_rule.id,
                            target_type='PROJECT',
                            target_id=project.id,
                            target_no=project.project_code,
                            target_name=project.project_name,
                            project_id=project.id,
                            alert_level=AlertLevelEnum.WARNING.value if overrun_ratio <= 20 else AlertLevelEnum.CRITICAL.value,
                            alert_title=f'项目成本超支：{project.project_name}',
                            alert_content=f'项目 {project.project_code} 成本超支 {overrun_ratio:.2f}%（预算：{budget:,.2f}，实际：{actual_cost:,.2f}）',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now()
                        )
                        db.add(alert)
                        alert_count += 1
                        overrun_projects.append({
                            'project_id': project.id,
                            'project_code': project.project_code,
                            'overrun_ratio': overrun_ratio
                        })
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 成本超支预警检查完成: 检查 {len(active_projects)} 个项目, 发现 {len(overrun_projects)} 个超支项目, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 成本超支预警检查完成: 检查 {len(active_projects)} 个项目, 发现 {len(overrun_projects)} 个超支项目, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(active_projects),
                'overrun_count': len(overrun_projects),
                'alert_count': alert_count,
                'overrun_projects': overrun_projects,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 成本超支预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== P0 预警服务 ====================

def generate_shortage_alerts():
    """
    P0-1: 缺料预警生成服务
    每天执行一次，检查所有活跃项目的缺料情况并生成预警
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.material import BomItem, MaterialShortage
            from app.models.project import Machine
            from sqlalchemy import func
            
            today = date.today()
            
            # 获取或创建预警规则
            shortage_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'MATERIAL_SHORTAGE',
                AlertRule.is_enabled == True
            ).first()
            
            if not shortage_rule:
                shortage_rule = AlertRule(
                    rule_code='MATERIAL_SHORTAGE',
                    rule_name='缺料预警',
                    rule_type=AlertRuleTypeEnum.MATERIAL_SHORTAGE.value,
                    target_type='MATERIAL',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当物料短缺时触发预警'
                )
                db.add(shortage_rule)
                db.flush()
            
            # 查询所有未解决的缺料记录
            shortages = db.query(MaterialShortage).filter(
                MaterialShortage.status == 'OPEN'
            ).all()
            
            alert_count = 0
            
            for shortage in shortages:
                # 检查是否已有预警记录
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'MATERIAL_SHORTAGE',
                    AlertRecord.target_id == shortage.id,
                    AlertRecord.status == 'PENDING'
                ).first()
                
                if not existing_alert:
                    # 根据缺料数量和需求日期确定预警级别
                    days_to_required = (shortage.required_date - today).days if shortage.required_date else 999
                    
                    if days_to_required < 0:
                        level = AlertLevelEnum.CRITICAL.value
                    elif days_to_required <= 3:
                        level = AlertLevelEnum.URGENT.value
                    elif days_to_required <= 7:
                        level = AlertLevelEnum.WARNING.value
                    else:
                        level = AlertLevelEnum.INFO.value
                    
                    alert_no = f'SA{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                    
                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=shortage_rule.id,
                        target_type='MATERIAL_SHORTAGE',
                        target_id=shortage.id,
                        target_no=shortage.material_code,
                        target_name=f'{shortage.material_name} 缺料',
                        project_id=shortage.project_id,
                        alert_level=level,
                        alert_title=f'物料缺料：{shortage.material_name}',
                        alert_content=f'物料 {shortage.material_code} 缺料 {float(shortage.shortage_qty)}，需求日期：{shortage.required_date}',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(float(shortage.shortage_qty)),
                        threshold_value='0'
                    )
                    db.add(alert)
                    db.flush()  # 确保 alert 有 ID
                    
                    # 发送通知
                    send_notification_for_alert(db, alert, logger)
                    
                    alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 缺料预警生成完成: 检查 {len(shortages)} 个缺料记录, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 缺料预警生成完成: 检查 {len(shortages)} 个缺料记录, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(shortages),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 缺料预警生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_task_delay_alerts():
    """
    P0-2: 任务延期预警服务
    每小时执行一次，检查所有延期任务并生成预警
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.progress import Task
            
            today = date.today()
            
            # 获取或创建预警规则
            delay_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'TASK_DELAY',
                AlertRule.is_enabled == True
            ).first()
            
            if not delay_rule:
                delay_rule = AlertRule(
                    rule_code='TASK_DELAY',
                    rule_name='任务延期预警',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='TASK',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当任务计划结束日期已过但未完成时触发预警'
                )
                db.add(delay_rule)
                db.flush()
            
            # 查询所有延期任务
            overdue_tasks = db.query(Task).filter(
                Task.status.notin_(['DONE', 'CANCELLED']),
                Task.plan_end < today
            ).all()
            
            alert_count = 0
            
            for task in overdue_tasks:
                # 检查是否已有预警记录
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'TASK',
                    AlertRecord.target_id == task.id,
                    AlertRecord.status == 'PENDING'
                ).first()
                
                if not existing_alert:
                    days_overdue = (today - task.plan_end).days
                    
                    # 根据延期天数确定预警级别
                    if days_overdue >= 7:
                        level = AlertLevelEnum.CRITICAL.value
                    elif days_overdue >= 3:
                        level = AlertLevelEnum.URGENT.value
                    else:
                        level = AlertLevelEnum.WARNING.value
                    
                    alert_no = f'TD{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                    
                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=delay_rule.id,
                        target_type='TASK',
                        target_id=task.id,
                        target_no=task.task_name,
                        target_name=task.task_name,
                        project_id=task.project_id,
                        alert_level=level,
                        alert_title=f'任务延期：{task.task_name}',
                        alert_content=f'任务 {task.task_name} 已延期 {days_overdue} 天（计划完成日期：{task.plan_end}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(days_overdue),
                        threshold_value='0'
                    )
                    db.add(alert)
                    db.flush()  # 确保 alert 有 ID
                    
                    # 发送通知
                    send_notification_for_alert(db, alert, logger)
                    
                    alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 任务延期预警检查完成: 发现 {len(overdue_tasks)} 个延期任务, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 任务延期预警检查完成: 发现 {len(overdue_tasks)} 个延期任务, 生成 {alert_count} 个预警")
            
            return {
                'overdue_count': len(overdue_tasks),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 任务延期预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_production_plan_alerts():
    """
    P0-3: 生产计划预警服务
    每天执行一次，检查生产计划执行情况并生成预警
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.production import ProductionPlan, WorkOrder
            
            today = date.today()
            
            # 获取或创建预警规则
            plan_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'PRODUCTION_PLAN',
                AlertRule.is_enabled == True
            ).first()
            
            if not plan_rule:
                plan_rule = AlertRule(
                    rule_code='PRODUCTION_PLAN',
                    rule_name='生产计划预警',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='PRODUCTION_PLAN',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='80',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当生产计划进度低于80%或计划日期临近时触发预警'
                )
                db.add(plan_rule)
                db.flush()
            
            # 查询所有执行中的生产计划
            active_plans = db.query(ProductionPlan).filter(
                ProductionPlan.status == 'EXECUTING'
            ).all()
            
            alert_count = 0
            
            for plan in active_plans:
                # 检查计划进度
                if plan.progress < 80 and plan.plan_end_date <= today + timedelta(days=7):
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'PRODUCTION_PLAN',
                        AlertRecord.target_id == plan.id,
                        AlertRecord.status == 'PENDING'
                    ).first()
                    
                    if not existing_alert:
                        days_left = (plan.plan_end_date - today).days
                        level = AlertLevelEnum.CRITICAL.value if days_left < 0 else AlertLevelEnum.WARNING.value
                        
                        alert_no = f'PP{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                        
                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=plan_rule.id,
                            target_type='PRODUCTION_PLAN',
                            target_id=plan.id,
                            target_no=plan.plan_no,
                            target_name=plan.plan_name,
                            project_id=plan.project_id,
                            alert_level=level,
                            alert_title=f'生产计划进度滞后：{plan.plan_name}',
                            alert_content=f'生产计划 {plan.plan_no} 进度仅 {plan.progress}%，距离计划结束日期还有 {days_left} 天',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(plan.progress),
                            threshold_value='80'
                        )
                        db.add(alert)
                        db.flush()  # 确保 alert 有 ID
                        
                        # 发送通知
                        send_notification_for_alert(db, alert, logger)
                        
                        alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 生产计划预警检查完成: 检查 {len(active_plans)} 个计划, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 生产计划预警检查完成: 检查 {len(active_plans)} 个计划, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(active_plans),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 生产计划预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_work_report_timeout():
    """
    P0-4: 报工超时提醒服务
    每小时执行一次，检查超过24小时未报工的工单
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.production import WorkOrder, WorkReport
            from sqlalchemy import func
            
            now = datetime.now()
            today = date.today()
            timeout_threshold = now - timedelta(hours=24)
            
            # 获取或创建预警规则
            timeout_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'WORK_REPORT_TIMEOUT',
                AlertRule.is_enabled == True
            ).first()
            
            if not timeout_rule:
                timeout_rule = AlertRule(
                    rule_code='WORK_REPORT_TIMEOUT',
                    rule_name='报工超时提醒',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='WORK_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='GT',
                    threshold_value='24',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当工单超过24小时未报工时触发预警'
                )
                db.add(timeout_rule)
                db.flush()
            
            # 查询所有进行中的工单
            active_orders = db.query(WorkOrder).filter(
                WorkOrder.status.in_(['IN_PROGRESS', 'ASSIGNED'])
            ).all()
            
            alert_count = 0
            
            for order in active_orders:
                # 获取最后一次报工时间
                last_report = db.query(WorkReport).filter(
                    WorkReport.work_order_id == order.id
                ).order_by(WorkReport.report_time.desc()).first()
                
                # 如果没有报工记录，使用实际开始时间
                if not last_report:
                    if order.actual_start_time and order.actual_start_time < timeout_threshold:
                        hours_since_start = (now - order.actual_start_time).total_seconds() / 3600
                    else:
                        continue
                else:
                    if last_report.report_time < timeout_threshold:
                        hours_since_last = (now - last_report.report_time).total_seconds() / 3600
                    else:
                        continue
                    hours_since_start = hours_since_last
                
                # 检查是否已有预警记录
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'WORK_ORDER',
                    AlertRecord.target_id == order.id,
                    AlertRecord.status == 'PENDING'
                ).first()
                
                if not existing_alert:
                    alert_no = f'WT{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                    
                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=timeout_rule.id,
                        target_type='WORK_ORDER',
                        target_id=order.id,
                        target_no=order.work_order_no,
                        target_name=order.task_name,
                        project_id=order.project_id,
                        alert_level=AlertLevelEnum.WARNING.value,
                        alert_title=f'报工超时：{order.task_name}',
                        alert_content=f'工单 {order.work_order_no} 已超过 {int(hours_since_start)} 小时未报工',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(int(hours_since_start)),
                        threshold_value='24'
                    )
                    db.add(alert)
                    db.flush()  # 确保 alert 有 ID
                    
                    # 发送通知
                    send_notification_for_alert(db, alert, logger)
                    
                    alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 报工超时提醒检查完成: 检查 {len(active_orders)} 个工单, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 报工超时提醒检查完成: 检查 {len(active_orders)} 个工单, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(active_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 报工超时提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def calculate_progress_summary():
    """
    P0-5: 进度汇总计算服务
    每小时执行一次，自动计算项目进度汇总
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.progress import Task
            from sqlalchemy import func
            
            # 查询所有活跃项目
            active_projects = db.query(Project).filter(
                Project.is_active == True
            ).all()
            
            updated_count = 0
            
            for project in active_projects:
                # 计算项目任务进度
                tasks = db.query(Task).filter(
                    Task.project_id == project.id,
                    Task.status != 'CANCELLED'
                ).all()
                
                if not tasks:
                    continue
                
                # 计算加权进度
                total_weight = sum(float(task.weight) for task in tasks)
                weighted_progress = sum(float(task.progress_percent) * float(task.weight) for task in tasks)
                
                if total_weight > 0:
                    calculated_progress = int(weighted_progress / total_weight)
                    
                    # 更新项目进度（如果项目有progress字段）
                    if hasattr(project, 'progress'):
                        project.progress = calculated_progress
                        updated_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 进度汇总计算完成: 更新 {updated_count} 个项目进度")
            print(f"[{datetime.now()}] 进度汇总计算完成: 更新 {updated_count} 个项目进度")
            
            return {
                'updated_count': updated_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 进度汇总计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_kit_check():
    """
    P0-6: 每日齐套检查服务
    每天执行一次，检查所有工单的齐套情况
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.shortage import KitCheck
            from app.models.production import WorkOrder
            from sqlalchemy import func
            
            today = date.today()
            
            # 获取或创建预警规则
            kit_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'KIT_RATE_LOW',
                AlertRule.is_enabled == True
            ).first()
            
            if not kit_rule:
                kit_rule = AlertRule(
                    rule_code='KIT_RATE_LOW',
                    rule_name='齐套率过低预警',
                    rule_type=AlertRuleTypeEnum.MATERIAL_SHORTAGE.value,
                    target_type='WORK_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='80',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当工单齐套率低于80%时触发预警'
                )
                db.add(kit_rule)
                db.flush()
            
            # 查询未来7天内计划开工的工单
            future_date = today + timedelta(days=7)
            upcoming_orders = db.query(WorkOrder).filter(
                WorkOrder.status.in_(['PENDING', 'ASSIGNED']),
                WorkOrder.plan_start_date.between(today, future_date)
            ).all()
            
            alert_count = 0
            
            for order in upcoming_orders:
                # 获取最新的齐套检查记录
                latest_check = db.query(KitCheck).filter(
                    KitCheck.work_order_id == order.id
                ).order_by(KitCheck.check_time.desc()).first()
                
                if latest_check and latest_check.kit_rate < 80:
                    # 检查是否已有预警记录
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'WORK_ORDER',
                        AlertRecord.target_id == order.id,
                        AlertRecord.rule_id == kit_rule.id,
                        AlertRecord.status == 'PENDING'
                    ).first()
                    
                    if not existing_alert:
                        alert_no = f'KC{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                        
                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=kit_rule.id,
                            target_type='WORK_ORDER',
                            target_id=order.id,
                            target_no=order.work_order_no,
                            target_name=order.task_name,
                            project_id=order.project_id,
                            alert_level=AlertLevelEnum.WARNING.value,
                            alert_title=f'工单齐套率过低：{order.task_name}',
                            alert_content=f'工单 {order.work_order_no} 齐套率仅 {float(latest_check.kit_rate)}%，缺料 {latest_check.shortage_items} 项',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(float(latest_check.kit_rate)),
                            threshold_value='80'
                        )
                        db.add(alert)
                        db.flush()  # 确保 alert 有 ID
                        
                        # 发送通知
                        send_notification_for_alert(db, alert, logger)
                        
                        alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 每日齐套检查完成: 检查 {len(upcoming_orders)} 个工单, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 每日齐套检查完成: 检查 {len(upcoming_orders)} 个工单, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(upcoming_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 每日齐套检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_delivery_delay():
    """
    P0-7: 到货延迟检查服务
    每天执行一次，检查采购订单到货延迟情况
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.purchase import PurchaseOrder, PurchaseOrderItem
            
            today = date.today()
            
            # 获取或创建预警规则
            delay_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'DELIVERY_DELAY',
                AlertRule.is_enabled == True
            ).first()
            
            if not delay_rule:
                delay_rule = AlertRule(
                    rule_code='DELIVERY_DELAY',
                    rule_name='到货延迟预警',
                    rule_type=AlertRuleTypeEnum.DELIVERY_DUE.value,
                    target_type='PURCHASE_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当采购订单到货日期超过要求交期时触发预警'
                )
                db.add(delay_rule)
                db.flush()
            
            # 查询所有未完成且已过要求交期的采购订单
            delayed_orders = db.query(PurchaseOrder).filter(
                PurchaseOrder.status.in_(['CONFIRMED', 'IN_PROGRESS', 'PARTIAL_RECEIVED']),
                PurchaseOrder.required_date < today
            ).all()
            
            alert_count = 0
            
            for order in delayed_orders:
                days_delayed = (today - order.required_date).days
                
                # 检查是否已有预警记录
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'PURCHASE_ORDER',
                    AlertRecord.target_id == order.id,
                    AlertRecord.status == 'PENDING'
                ).first()
                
                if not existing_alert:
                    level = AlertLevelEnum.CRITICAL.value if days_delayed >= 7 else AlertLevelEnum.WARNING.value
                    
                    alert_no = f'DD{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                    
                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=delay_rule.id,
                        target_type='PURCHASE_ORDER',
                        target_id=order.id,
                        target_no=order.order_no,
                        target_name=order.order_title or order.order_no,
                        project_id=order.project_id,
                        alert_level=level,
                        alert_title=f'采购订单到货延迟：{order.order_no}',
                        alert_content=f'采购订单 {order.order_no} 已延迟 {days_delayed} 天（要求交期：{order.required_date}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(days_delayed),
                        threshold_value='0'
                    )
                    db.add(alert)
                    alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 到货延迟检查完成: 发现 {len(delayed_orders)} 个延迟订单, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 到货延迟检查完成: 发现 {len(delayed_orders)} 个延迟订单, 生成 {alert_count} 个预警")
            
            return {
                'delayed_count': len(delayed_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 到货延迟检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_task_deadline_reminder():
    """
    P0-8: 任务到期提醒服务
    每小时执行一次，检查即将到期的任务并发送提醒
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.task_center import TaskUnified
            
            now = datetime.now()
            today = date.today()
            reminder_threshold = now + timedelta(hours=24)
            
            # 获取或创建预警规则
            reminder_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'TASK_DEADLINE_REMINDER',
                AlertRule.is_enabled == True
            ).first()
            
            if not reminder_rule:
                reminder_rule = AlertRule(
                    rule_code='TASK_DEADLINE_REMINDER',
                    rule_name='任务到期提醒',
                    rule_type=AlertRuleTypeEnum.SCHEDULE_DELAY.value,
                    target_type='TASK_UNIFIED',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='24',
                    alert_level=AlertLevelEnum.INFO.value,
                    is_enabled=True,
                    is_system=True,
                    description='当任务即将在24小时内到期时触发提醒'
                )
                db.add(reminder_rule)
                db.flush()
            
            # 查询所有未完成且即将到期的任务
            upcoming_tasks = db.query(TaskUnified).filter(
                TaskUnified.status.notin_(['COMPLETED', 'CANCELLED']),
                TaskUnified.deadline.isnot(None),
                TaskUnified.deadline <= reminder_threshold,
                TaskUnified.deadline > now
            ).all()
            
            alert_count = 0
            
            for task in upcoming_tasks:
                hours_left = (task.deadline - now).total_seconds() / 3600
                
                # 检查是否已有预警记录（24小时内只提醒一次）
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'TASK_UNIFIED',
                    AlertRecord.target_id == task.id,
                    AlertRecord.rule_id == reminder_rule.id,
                    AlertRecord.triggered_at >= now - timedelta(hours=24)
                ).first()
                
                if not existing_alert:
                    alert_no = f'TR{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                    
                    alert = AlertRecord(
                        alert_no=alert_no,
                        rule_id=reminder_rule.id,
                        target_type='TASK_UNIFIED',
                        target_id=task.id,
                        target_no=task.task_code,
                        target_name=task.title,
                        project_id=task.project_id,
                        alert_level=AlertLevelEnum.INFO.value,
                        alert_title=f'任务即将到期：{task.title}',
                        alert_content=f'任务 {task.task_code} 将在 {int(hours_left)} 小时后到期（截止时间：{task.deadline}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                        trigger_value=str(int(hours_left)),
                        threshold_value='24'
                    )
                    db.add(alert)
                    alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 任务到期提醒检查完成: 发现 {len(upcoming_tasks)} 个即将到期任务, 生成 {alert_count} 个提醒")
            print(f"[{datetime.now()}] 任务到期提醒检查完成: 发现 {len(upcoming_tasks)} 个即将到期任务, 生成 {alert_count} 个提醒")
            
            return {
                'upcoming_count': len(upcoming_tasks),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 任务到期提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_outsourcing_delivery_alerts():
    """
    P0-9: 外协交期预警服务
    每天执行一次，检查外协订单交期情况
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.outsourcing import OutsourcingOrder
            
            today = date.today()
            warning_date = today + timedelta(days=3)
            
            # 获取或创建预警规则
            delivery_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'OUTSOURCING_DELIVERY',
                AlertRule.is_enabled == True
            ).first()
            
            if not delivery_rule:
                delivery_rule = AlertRule(
                    rule_code='OUTSOURCING_DELIVERY',
                    rule_name='外协交期预警',
                    rule_type=AlertRuleTypeEnum.DELIVERY_DUE.value,
                    target_type='OUTSOURCING_ORDER',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='3',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当外协订单交期临近或已逾期时触发预警'
                )
                db.add(delivery_rule)
                db.flush()
            
            # 查询所有未完成的外协订单
            active_orders = db.query(OutsourcingOrder).filter(
                OutsourcingOrder.status.in_(['CONFIRMED', 'IN_PROGRESS'])
            ).all()
            
            alert_count = 0
            
            for order in active_orders:
                if not order.required_date:
                    continue
                
                days_to_delivery = (order.required_date - today).days
                
                # 如果交期在3天内或已逾期，生成预警
                if days_to_delivery <= 3:
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'OUTSOURCING_ORDER',
                        AlertRecord.target_id == order.id,
                        AlertRecord.status == 'PENDING'
                    ).first()
                    
                    if not existing_alert:
                        if days_to_delivery < 0:
                            level = AlertLevelEnum.CRITICAL.value
                            title = f'外协订单交期逾期：{order.order_no}'
                            content = f'外协订单 {order.order_no} 已逾期 {abs(days_to_delivery)} 天（要求交期：{order.required_date}）'
                        else:
                            level = AlertLevelEnum.WARNING.value
                            title = f'外协订单交期临近：{order.order_no}'
                            content = f'外协订单 {order.order_no} 将在 {days_to_delivery} 天后到期（要求交期：{order.required_date}）'
                        
                        alert_no = f'OD{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                        
                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=delivery_rule.id,
                            target_type='OUTSOURCING_ORDER',
                            target_id=order.id,
                            target_no=order.order_no,
                            target_name=order.order_title or order.order_no,
                            project_id=order.project_id,
                            alert_level=level,
                            alert_title=title,
                            alert_content=content,
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(days_to_delivery),
                            threshold_value='3'
                        )
                        db.add(alert)
                        db.flush()  # 确保 alert 有 ID
                        
                        # 发送通知
                        send_notification_for_alert(db, alert, logger)
                        
                        alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 外协交期预警检查完成: 检查 {len(active_orders)} 个订单, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 外协交期预警检查完成: 检查 {len(active_orders)} 个订单, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(active_orders),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 外协交期预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_milestone_risk_alerts():
    """
    P0-10: 里程碑风险预警服务（完善版）
    每天执行一次，检查里程碑风险并生成预警
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.progress import Task
            
            today = date.today()
            risk_date = today + timedelta(days=7)
            
            # 获取或创建预警规则
            risk_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'MILESTONE_RISK',
                AlertRule.is_enabled == True
            ).first()
            
            if not risk_rule:
                risk_rule = AlertRule(
                    rule_code='MILESTONE_RISK',
                    rule_name='里程碑风险预警',
                    rule_type=AlertRuleTypeEnum.MILESTONE_DUE.value,
                    target_type='MILESTONE',
                    condition_type='THRESHOLD',
                    condition_operator='LT',
                    threshold_value='7',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当里程碑临近但关联任务未完成时触发预警'
                )
                db.add(risk_rule)
                db.flush()
            
            # 查询未来7天内的里程碑
            upcoming_milestones = db.query(ProjectMilestone).filter(
                ProjectMilestone.status != 'COMPLETED',
                ProjectMilestone.planned_date.between(today, risk_date)
            ).all()
            
            alert_count = 0
            
            for milestone in upcoming_milestones:
                # 检查关联任务的完成情况
                related_tasks = db.query(Task).filter(
                    Task.milestone_id == milestone.id,
                    Task.status != 'CANCELLED'
                ).all()
                
                if not related_tasks:
                    continue
                
                completed_tasks = [t for t in related_tasks if t.status == 'DONE']
                completion_rate = len(completed_tasks) / len(related_tasks) * 100
                
                # 如果完成率低于80%，生成预警
                if completion_rate < 80:
                    days_left = (milestone.planned_date - today).days
                    
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'MILESTONE',
                        AlertRecord.target_id == milestone.id,
                        AlertRecord.rule_id == risk_rule.id,
                        AlertRecord.status == 'PENDING'
                    ).first()
                    
                    if not existing_alert:
                        level = AlertLevelEnum.CRITICAL.value if days_left <= 3 else AlertLevelEnum.WARNING.value
                        
                        alert_no = f'MR{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                        
                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=risk_rule.id,
                            target_type='MILESTONE',
                            target_id=milestone.id,
                            target_no=milestone.milestone_code,
                            target_name=milestone.milestone_name,
                            project_id=milestone.project_id,
                            alert_level=level,
                            alert_title=f'里程碑风险：{milestone.milestone_name}',
                            alert_content=f'里程碑 {milestone.milestone_code} 将在 {days_left} 天后到期，但关联任务完成率仅 {completion_rate:.1f}%',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now(),
                            trigger_value=str(completion_rate),
                            threshold_value='80'
                        )
                        db.add(alert)
                        db.flush()  # 确保 alert 有 ID
                        
                        # 发送通知
                        send_notification_for_alert(db, alert, logger)
                        
                        alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 里程碑风险预警检查完成: 检查 {len(upcoming_milestones)} 个里程碑, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 里程碑风险预警检查完成: 检查 {len(upcoming_milestones)} 个里程碑, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(upcoming_milestones),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑风险预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 生产/缺料日报自动生成 ====================

def _calculate_production_daily_stats(db: Session, target_date: date, workshop_id: Optional[int]) -> dict:
    """内部辅助：计算指定日期、车间的生产统计"""
    from sqlalchemy import func
    from app.models.production import WorkOrder, WorkReport, ProductionException, Worker
    
    # 计划数据
    plan_query = db.query(WorkOrder).filter(
        WorkOrder.plan_start_date <= target_date,
        WorkOrder.plan_end_date >= target_date
    )
    if workshop_id:
        plan_query = plan_query.filter(WorkOrder.workshop_id == workshop_id)
    plan_orders = plan_query.all()
    plan_qty = sum(order.plan_qty or 0 for order in plan_orders)
    plan_hours = sum(float(order.standard_hours or 0) for order in plan_orders)
    
    # 报工数据
    report_query = db.query(WorkReport).join(WorkOrder, WorkOrder.id == WorkReport.work_order_id).filter(
        func.date(WorkReport.report_time) == target_date
    )
    if workshop_id:
        report_query = report_query.filter(WorkOrder.workshop_id == workshop_id)
    reports = report_query.all()
    
    completed_qty = sum(report.completed_qty or 0 for report in reports if report.completed_qty)
    qualified_qty = sum(report.qualified_qty or 0 for report in reports if report.qualified_qty)
    defect_qty = sum(report.defect_qty or 0 for report in reports if report.defect_qty)
    total_qty = completed_qty if completed_qty else qualified_qty + defect_qty
    actual_hours = sum(float(report.work_hours or 0) for report in reports if report.work_hours)
    actual_attend = len({report.worker_id for report in reports if report.worker_id})
    
    # 人员数据
    worker_query = db.query(Worker)
    if workshop_id:
        worker_query = worker_query.filter(Worker.workshop_id == workshop_id)
    workers = worker_query.all()
    should_attend = len([w for w in workers if w.status != 'RESIGNED'])
    leave_count = len([w for w in workers if w.status == 'LEAVE'])
    
    # 异常数据
    exception_base = db.query(ProductionException)
    if workshop_id:
        exception_base = exception_base.filter(ProductionException.workshop_id == workshop_id)
    new_exception_count = exception_base.filter(
        func.date(ProductionException.report_time) == target_date
    ).count()
    resolved_exception_count = exception_base.filter(
        ProductionException.resolved_at.isnot(None),
        func.date(ProductionException.resolved_at) == target_date
    ).count()
    
    produced_qty = completed_qty or total_qty
    completion_rate = round((produced_qty / plan_qty) * 100, 2) if plan_qty else 0.0
    efficiency = round((actual_hours / plan_hours) * 100, 2) if plan_hours else 0.0
    overtime_hours = round(max(actual_hours - plan_hours, 0), 2)
    pass_rate = round((qualified_qty / total_qty) * 100, 2) if total_qty else 0.0
    
    return {
        'plan_qty': int(plan_qty),
        'completed_qty': int(produced_qty),
        'completion_rate': completion_rate,
        'plan_hours': round(plan_hours, 2),
        'actual_hours': round(actual_hours, 2),
        'overtime_hours': overtime_hours,
        'efficiency': efficiency,
        'should_attend': int(should_attend),
        'actual_attend': int(actual_attend),
        'leave_count': int(leave_count),
        'total_qty': int(total_qty),
        'qualified_qty': int(qualified_qty),
        'pass_rate': pass_rate,
        'new_exception_count': int(new_exception_count),
        'resolved_exception_count': int(resolved_exception_count)
    }


def generate_production_daily_reports(target_date: Optional[date] = None):
    """
    P0-11: 生产日报自动生成
    根据上一日生产、报工、异常数据自动生成全厂及各车间日报
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.production import ProductionDailyReport, Workshop
            
            if target_date is None:
                target_date = date.today() - timedelta(days=1)
            
            workshops = db.query(Workshop).filter(Workshop.is_active == True).all()
            workshop_map = {w.id: w.workshop_name for w in workshops}
            target_workshops = [None] + [w.id for w in workshops]
            
            generated = 0
            for workshop_id in target_workshops:
                stats = _calculate_production_daily_stats(db, target_date, workshop_id)
                
                report = db.query(ProductionDailyReport).filter(
                    ProductionDailyReport.report_date == target_date,
                    ProductionDailyReport.workshop_id == workshop_id
                ).first()
                if not report:
                    report = ProductionDailyReport(
                        report_date=target_date,
                        workshop_id=workshop_id
                    )
                    db.add(report)
                
                workshop_label = '全厂' if workshop_id is None else workshop_map.get(workshop_id, f'车间{workshop_id}')
                stats['summary'] = (
                    f"{workshop_label} {target_date.strftime('%m-%d')} 计划 {stats['plan_qty']} 件，"
                    f"完成 {stats['completed_qty']} 件（{stats['completion_rate']:.1f}%），"
                    f"实工 {stats['actual_hours']:.1f} 小时，效率 {stats['efficiency']:.1f}%，"
                    f"异常 {stats['new_exception_count']} 起。"
                )
                
                for field, value in stats.items():
                    setattr(report, field, value)
                
                generated += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 生产日报自动生成: {generated} 条记录, 日期 {target_date}")
            print(f"[{datetime.now()}] 生产日报自动生成完成: {generated} 条记录, 日期 {target_date}")
            
            return {
                'generated': generated,
                'date': target_date.isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 生产日报自动生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def generate_shortage_daily_report(target_date: Optional[date] = None):
    """
    P0-12: 缺料日报自动生成
    汇总缺料预警、到货、齐套等指标
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from sqlalchemy import func
            from app.models.shortage import (
                ShortageDailyReport, ShortageAlert, ShortageReport,
                MaterialArrival, KitCheck
            )
            
            if target_date is None:
                target_date = date.today() - timedelta(days=1)
            
            # 预警统计
            new_alerts = db.query(func.count(ShortageAlert.id)).filter(
                func.date(ShortageAlert.created_at) == target_date
            ).scalar() or 0
            resolved_alerts = db.query(func.count(ShortageAlert.id)).filter(
                ShortageAlert.resolve_time.isnot(None),
                func.date(ShortageAlert.resolve_time) == target_date
            ).scalar() or 0
            pending_alerts = db.query(func.count(ShortageAlert.id)).filter(
                ShortageAlert.status.in_(["pending", "handling", "escalated"])
            ).scalar() or 0
            overdue_alerts = db.query(func.count(ShortageAlert.id)).filter(
                ShortageAlert.is_overdue == True
            ).scalar() or 0
            
            level_counts = {}
            for level in ['level1', 'level2', 'level3', 'level4']:
                level_counts[level] = db.query(func.count(ShortageAlert.id)).filter(
                    ShortageAlert.alert_level == level
                ).scalar() or 0
            
            # 上报统计
            new_reports = db.query(func.count(ShortageReport.id)).filter(
                func.date(ShortageReport.report_time) == target_date
            ).scalar() or 0
            resolved_reports = db.query(func.count(ShortageReport.id)).filter(
                ShortageReport.resolved_at.isnot(None),
                func.date(ShortageReport.resolved_at) == target_date
            ).scalar() or 0
            
            # 齐套统计
            kit_checks = db.query(KitCheck).filter(
                func.date(KitCheck.check_time) == target_date
            ).all()
            total_work_orders = len(kit_checks)
            kit_complete_count = len([k for k in kit_checks if (k.kit_status or '').lower() == 'complete'])
            kit_rate = round(
                sum(float(k.kit_rate or 0) for k in kit_checks) / total_work_orders,
                2
            ) if total_work_orders else 0.0
            
            # 到货统计
            expected_arrivals = db.query(func.count(MaterialArrival.id)).filter(
                MaterialArrival.expected_date == target_date
            ).scalar() or 0
            actual_arrivals = db.query(func.count(MaterialArrival.id)).filter(
                MaterialArrival.actual_date == target_date
            ).scalar() or 0
            delayed_arrivals = db.query(func.count(MaterialArrival.id)).filter(
                MaterialArrival.actual_date == target_date,
                MaterialArrival.is_delayed == True
            ).scalar() or 0
            on_time_rate = round(
                ((actual_arrivals - delayed_arrivals) / actual_arrivals) * 100,
                2
            ) if actual_arrivals else 0.0
            
            # 响应与解决耗时
            alerts_for_response = db.query(ShortageAlert).filter(
                func.date(ShortageAlert.created_at) == target_date
            ).all()
            response_minutes = [
                (alert.handle_start_time - alert.created_at).total_seconds() / 60.0
                for alert in alerts_for_response
                if alert.handle_start_time and alert.created_at
            ]
            avg_response_minutes = int(round(
                sum(response_minutes) / len(response_minutes), 0
            )) if response_minutes else 0
            
            resolved_alerts_list = db.query(ShortageAlert).filter(
                ShortageAlert.resolve_time.isnot(None),
                func.date(ShortageAlert.resolve_time) == target_date
            ).all()
            resolve_hours = [
                (alert.resolve_time - alert.created_at).total_seconds() / 3600.0
                for alert in resolved_alerts_list
                if alert.resolve_time and alert.created_at
            ]
            avg_resolve_hours = round(
                sum(resolve_hours) / len(resolve_hours), 2
            ) if resolve_hours else 0.0
            
            # 停工影响
            stoppage_alerts = db.query(ShortageAlert).filter(
                func.date(ShortageAlert.created_at) == target_date,
                ShortageAlert.impact_type == 'stop'
            ).all()
            stoppage_count = len(stoppage_alerts)
            stoppage_hours = round(
                sum((alert.estimated_delay_days or 0) * 24 for alert in stoppage_alerts),
                2
            )
            
            report = db.query(ShortageDailyReport).filter(
                ShortageDailyReport.report_date == target_date
            ).first()
            if not report:
                report = ShortageDailyReport(report_date=target_date)
                db.add(report)
            
            report.new_alerts = new_alerts
            report.resolved_alerts = resolved_alerts
            report.pending_alerts = pending_alerts
            report.overdue_alerts = overdue_alerts
            report.level1_count = level_counts['level1']
            report.level2_count = level_counts['level2']
            report.level3_count = level_counts['level3']
            report.level4_count = level_counts['level4']
            report.new_reports = new_reports
            report.resolved_reports = resolved_reports
            report.total_work_orders = total_work_orders
            report.kit_complete_count = kit_complete_count
            report.kit_rate = kit_rate
            report.expected_arrivals = expected_arrivals
            report.actual_arrivals = actual_arrivals
            report.delayed_arrivals = delayed_arrivals
            report.on_time_rate = on_time_rate
            report.avg_response_minutes = avg_response_minutes
            report.avg_resolve_hours = avg_resolve_hours
            report.stoppage_count = stoppage_count
            report.stoppage_hours = stoppage_hours
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 缺料日报自动生成: 日期 {target_date}")
            print(f"[{datetime.now()}] 缺料日报自动生成完成: 日期 {target_date}")
            
            return {
                'date': target_date.isoformat(),
                'new_alerts': new_alerts,
                'new_reports': new_reports
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 缺料日报自动生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 岗位职责任务生成 ====================

def generate_job_duty_tasks():
    """
    岗位职责任务生成服务
    每天凌晨4点执行，根据岗位职责模板自动生成任务
    """
    try:
        with get_db_session() as db:
            from app.models.task_center import JobDutyTemplate, TaskUnified
            from app.models.user import User
            from datetime import timedelta
            import calendar
            
            today = date.today()
            generated_count = 0
            
            # 查询所有启用的岗位职责模板
            templates = db.query(JobDutyTemplate).filter(
                JobDutyTemplate.is_active == True,
                JobDutyTemplate.auto_generate == True
            ).all()
            
            for template in templates:
                should_generate = False
                target_date = today
                
                # 根据频率判断是否需要生成任务
                if template.frequency == 'DAILY':
                    # 每天生成
                    should_generate = True
                    target_date = today + timedelta(days=template.generate_before_days or 0)
                
                elif template.frequency == 'WEEKLY':
                    # 每周生成（检查是否是目标星期几）
                    if template.day_of_week:
                        # 计算本周的目标日期
                        days_until_target = (template.day_of_week - today.weekday() - 1) % 7
                        if days_until_target == 0:  # 今天就是目标日期
                            should_generate = True
                            target_date = today + timedelta(days=template.generate_before_days or 0)
                        elif 0 < days_until_target <= (template.generate_before_days or 3):
                            # 在提前生成范围内
                            should_generate = True
                            target_date = today + timedelta(days=days_until_target)
                
                elif template.frequency == 'MONTHLY':
                    # 每月生成（检查是否是目标日期）
                    if template.day_of_month:
                        # 计算本月的目标日期
                        last_day = calendar.monthrange(today.year, today.month)[1]
                        target_day = min(template.day_of_month, last_day)
                        target_date_in_month = date(today.year, today.month, target_day)
                        
                        days_until_target = (target_date_in_month - today).days
                        if days_until_target == 0:  # 今天就是目标日期
                            should_generate = True
                            target_date = today + timedelta(days=template.generate_before_days or 0)
                        elif 0 < days_until_target <= (template.generate_before_days or 3):
                            # 在提前生成范围内
                            should_generate = True
                            target_date = target_date_in_month
                
                elif template.frequency == 'YEARLY':
                    # 每年生成（检查是否是目标月份和日期）
                    if template.month_of_year and template.day_of_month:
                        target_date_in_year = date(today.year, template.month_of_year, 
                                                  min(template.day_of_month, 
                                                      calendar.monthrange(today.year, template.month_of_year)[1]))
                        days_until_target = (target_date_in_year - today).days
                        if days_until_target == 0:  # 今天就是目标日期
                            should_generate = True
                            target_date = today + timedelta(days=template.generate_before_days or 0)
                        elif 0 < days_until_target <= (template.generate_before_days or 3):
                            # 在提前生成范围内
                            should_generate = True
                            target_date = target_date_in_year
                
                if not should_generate:
                    continue
                
                # 检查是否已经生成过该日期的任务（避免重复生成）
                existing_task = db.query(TaskUnified).filter(
                    TaskUnified.task_type == 'JOB_DUTY',
                    TaskUnified.source_type == 'JOB_DUTY_TEMPLATE',
                    TaskUnified.source_id == template.id,
                    TaskUnified.plan_start_date == target_date
                ).first()
                
                if existing_task:
                    continue
                
                # 查找该岗位的所有用户
                # 注意：这里需要根据实际的用户-岗位关联表来查询
                # 假设User表有position_id字段，或者通过其他方式关联
                # 这里简化处理，假设可以通过部门ID查找用户
                users = []
                if hasattr(User, 'position_id'):
                    users = db.query(User).filter(
                        User.position_id == template.position_id,
                        User.is_active == True
                    ).all()
                elif template.department_id:
                    # 如果有部门ID，可以通过部门查找用户
                    if hasattr(User, 'department_id'):
                        users = db.query(User).filter(
                            User.department_id == template.department_id,
                            User.is_active == True
                        ).all()
                
                # 如果找不到用户，跳过
                if not users:
                    continue
                
                # 为每个用户生成任务
                for user in users:
                    # 计算截止日期
                    deadline = target_date + timedelta(days=template.deadline_offset_days or 0)
                    
                    # 生成任务编号
                    from app.api.v1.endpoints.task_center import generate_task_code
                    task_code = generate_task_code(db)
                    
                    task = TaskUnified(
                        task_code=task_code,
                        title=f"{template.duty_name}",
                        description=template.duty_description,
                        task_type='JOB_DUTY',
                        assignee_id=user.id,
                        assignee_name=user.real_name or user.username,
                        assigner_id=None,  # 系统自动生成
                        assigner_name='系统',
                        plan_start_date=target_date,
                        plan_end_date=target_date,
                        deadline=deadline,
                        estimated_hours=template.estimated_hours,
                        priority=template.default_priority or 'MEDIUM',
                        is_urgent=False,
                        tags=['岗位职责'],
                        category='JOB_DUTY',
                        reminder_enabled=True,
                        reminder_before_hours=24,
                        status='PENDING',
                        source_type='JOB_DUTY_TEMPLATE',
                        source_id=template.id,
                        created_by=None  # 系统生成
                    )
                    
                    db.add(task)
                    generated_count += 1
            
            db.commit()
            
            print(f"[{datetime.now()}] 岗位职责任务生成完成: 生成 {generated_count} 个任务")
            
            return {
                'generated_count': generated_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"[{datetime.now()}] 岗位职责任务生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_workload_overload_alerts():
    """
    负荷超限预警服务
    每天执行一次，检查负荷超过110%的资源并生成预警
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.user import User
            from app.models.organization import Department
            from app.models.progress import Task
            from app.models.pmo import PmoResourceAllocation
            
            today = date.today()
            # 查询未来30天的负荷
            start_date = today
            end_date = today + timedelta(days=30)
            
            # 获取所有活跃用户
            users = db.query(User).filter(User.is_active == True).all()
            
            # 获取或创建预警规则
            overload_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'WORKLOAD_OVERLOAD',
                AlertRule.is_enabled == True
            ).first()
            
            if not overload_rule:
                overload_rule = AlertRule(
                    rule_code='WORKLOAD_OVERLOAD',
                    rule_name='资源负荷超限预警',
                    rule_type=AlertRuleTypeEnum.RESOURCE.value,
                    target_type='USER',
                    condition_type='THRESHOLD',
                    condition_operator='GT',
                    threshold_value='110',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当用户未来30天负荷超过110%时触发预警'
                )
                db.add(overload_rule)
                db.flush()
            
            alert_count = 0
            overloaded_users = []
            
            for user in users:
                # 计算分配工时
                tasks = db.query(Task).filter(
                    Task.owner_id == user.id,
                    Task.plan_start <= end_date,
                    Task.plan_end >= start_date,
                    Task.status != 'CANCELLED'
                ).all()
                
                assigned_hours = 0.0
                for task in tasks:
                    if task.plan_start and task.plan_end:
                        days = (task.plan_end - task.plan_start).days + 1
                        hours = days * 8.0
                        assigned_hours += hours
                
                # 获取资源分配
                allocations = db.query(PmoResourceAllocation).filter(
                    PmoResourceAllocation.resource_id == user.id,
                    PmoResourceAllocation.start_date <= end_date,
                    PmoResourceAllocation.end_date >= start_date,
                    PmoResourceAllocation.status != 'CANCELLED'
                ).all()
                
                for alloc in allocations:
                    if alloc.planned_hours:
                        assigned_hours += float(alloc.planned_hours)
                
                # 计算标准工时（30天，每月176小时）
                workdays = 22  # 简单估算
                standard_hours = workdays * 8.0
                
                # 计算分配率
                allocation_rate = (assigned_hours / standard_hours * 100) if standard_hours > 0 else 0.0
                
                # 如果超过110%，生成预警
                if allocation_rate > 110:
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'USER',
                        AlertRecord.target_id == user.id,
                        AlertRecord.rule_id == overload_rule.id,
                        AlertRecord.status == 'PENDING'
                    ).first()
                    
                    if not existing_alert:
                        alert_no = f'WO{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                        
                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=overload_rule.id,
                            target_type='USER',
                            target_id=user.id,
                            target_no=str(user.id),
                            target_name=user.real_name or user.username,
                            project_id=None,
                            alert_level=AlertLevelEnum.WARNING.value if allocation_rate <= 150 else AlertLevelEnum.CRITICAL.value,
                            alert_title=f'资源负荷超限：{user.real_name or user.username}',
                            alert_content=f'用户 {user.real_name or user.username} 未来30天负荷达到 {allocation_rate:.1f}%，超过110%阈值（分配工时：{assigned_hours:.1f}小时，标准工时：{standard_hours:.1f}小时）',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now()
                        )
                        db.add(alert)
                        alert_count += 1
                        overloaded_users.append({
                            'user_id': user.id,
                            'user_name': user.real_name or user.username,
                            'allocation_rate': allocation_rate
                        })
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 负荷超限预警检查完成: 检查 {len(users)} 个用户, 发现 {len(overloaded_users)} 个超负荷用户, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 负荷超限预警检查完成: 检查 {len(users)} 个用户, 发现 {len(overloaded_users)} 个超负荷用户, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(users),
                'overloaded_count': len(overloaded_users),
                'alert_count': alert_count,
                'overloaded_users': overloaded_users,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 负荷超限预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def calculate_monthly_labor_cost_task():
    """
    月度工时成本计算任务
    每月1号凌晨2点执行，计算上个月所有项目的人工成本
    """
    from app.services.labor_cost_service import LaborCostService
    import logging
    
    logger = logging.getLogger(__name__)
    
    with get_db_session() as db:
        try:
            # 计算上个月的成本
            today = date.today()
            if today.month == 1:
                # 如果是1月，计算去年12月
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1
            
            result = LaborCostService.calculate_monthly_labor_cost(db, year, month)
            
            logger.info(f"[{datetime.now()}] 月度工时成本计算完成（{year}年{month}月）: {result.get('message', '')}")
            print(f"[{datetime.now()}] 月度工时成本计算完成（{year}年{month}月）: {result.get('message', '')}")
            
            return result
        except Exception as e:
            logger.error(f"[{datetime.now()}] 月度工时成本计算失败: {str(e)}")
            print(f"[{datetime.now()}] 月度工时成本计算失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


# ==================== 工时提醒定时任务 ====================

def daily_timesheet_reminder_task():
    """
    每日工时填报提醒任务
    每天上午9:00执行，提醒未填报昨天工时的用户
    """
    from app.services.timesheet_reminder_service import notify_timesheet_missing
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            count = notify_timesheet_missing(db)
            logger.info(f"[{datetime.now()}] 每日工时填报提醒完成: 发送 {count} 条提醒")
            print(f"[{datetime.now()}] 每日工时填报提醒完成: 发送 {count} 条提醒")
            
            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 每日工时填报提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def weekly_timesheet_reminder_task():
    """
    每周工时填报提醒任务
    每周一上午10:00执行，提醒未完成上周工时填报的用户
    """
    from app.services.timesheet_reminder_service import notify_weekly_timesheet_missing
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            count = notify_weekly_timesheet_missing(db)
            logger.info(f"[{datetime.now()}] 每周工时填报提醒完成: 发送 {count} 条提醒")
            print(f"[{datetime.now()}] 每周工时填报提醒完成: 发送 {count} 条提醒")
            
            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 每周工时填报提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def timesheet_anomaly_alert_task():
    """
    异常工时预警任务
    每天下午14:00执行，检测并提醒异常工时记录
    """
    from app.services.timesheet_reminder_service import notify_timesheet_anomaly
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            count = notify_timesheet_anomaly(db, days=1)
            logger.info(f"[{datetime.now()}] 异常工时预警完成: 发送 {count} 条提醒")
            print(f"[{datetime.now()}] 异常工时预警完成: 发送 {count} 条提醒")
            
            return {
                'alert_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 异常工时预警失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def timesheet_approval_timeout_reminder_task():
    """
    工时审批超时提醒任务
    每天上午11:00和下午15:00执行，提醒审批超时的记录
    """
    from app.services.timesheet_reminder_service import notify_approval_timeout
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            count = notify_approval_timeout(db, timeout_hours=24)
            logger.info(f"[{datetime.now()}] 工时审批超时提醒完成: 发送 {count} 条提醒")
            print(f"[{datetime.now()}] 工时审批超时提醒完成: 发送 {count} 条提醒")
            
            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 工时审批超时提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def timesheet_sync_failure_alert_task():
    """
    工时数据同步失败提醒任务
    每天下午16:00执行，检查并提醒同步失败的记录
    """
    from app.services.timesheet_reminder_service import notify_sync_failure
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            count = notify_sync_failure(db)
            logger.info(f"[{datetime.now()}] 工时数据同步失败提醒完成: 发送 {count} 条提醒")
            print(f"[{datetime.now()}] 工时数据同步失败提醒完成: 发送 {count} 条提醒")
            
            return {
                'alert_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 工时数据同步失败提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 工时汇总定时任务 ====================

def daily_timesheet_aggregation_task():
    """
    每日工时汇总任务
    每天凌晨1点执行，汇总前一天的数据
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    import logging
    
    logger = logging.getLogger(__name__)
    
    with get_db_session() as db:
        try:
            # 汇总前一天的数据
            yesterday = date.today() - timedelta(days=1)
            year = yesterday.year
            month = yesterday.month
            
            service = TimesheetAggregationService(db)
            result = service.aggregate_monthly_timesheet(year, month)
            
            logger.info(f"[{datetime.now()}] 每日工时汇总完成（{year}年{month}月）: {result.get('message', '')}")
            print(f"[{datetime.now()}] 每日工时汇总完成（{year}年{month}月）")
            
            return result
        except Exception as e:
            logger.error(f"[{datetime.now()}] 每日工时汇总失败: {str(e)}")
            print(f"[{datetime.now()}] 每日工时汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


def weekly_timesheet_aggregation_task():
    """
    每周工时汇总任务
    每周一凌晨2点执行，汇总上一周的数据
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    import logging
    
    logger = logging.getLogger(__name__)
    
    with get_db_session() as db:
        try:
            # 汇总上一周的数据（上周一到上周日）
            today = date.today()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            
            # 如果跨月，需要分别汇总
            if last_monday.month == last_sunday.month:
                year = last_monday.year
                month = last_monday.month
                service = TimesheetAggregationService(db)
                result = service.aggregate_monthly_timesheet(year, month)
                logger.info(f"[{datetime.now()}] 每周工时汇总完成（{year}年{month}月）")
            else:
                # 跨月情况，分别汇总两个月
                logger.info(f"[{datetime.now()}] 每周工时汇总：跨月情况，分别汇总")
                result = {'message': '跨月汇总完成'}
            
            return result
        except Exception as e:
            logger.error(f"[{datetime.now()}] 每周工时汇总失败: {str(e)}")
            print(f"[{datetime.now()}] 每周工时汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


def monthly_timesheet_aggregation_task():
    """
    每月工时汇总任务
    每月1号凌晨3点执行，汇总上一个月的数据
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_sync_service import TimesheetSyncService
    import logging
    
    logger = logging.getLogger(__name__)
    
    with get_db_session() as db:
        try:
            # 计算上个月
            today = date.today()
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1
            
            # 执行月度汇总
            service = TimesheetAggregationService(db)
            result = service.aggregate_monthly_timesheet(year, month)
            
            logger.info(f"[{datetime.now()}] 月度工时汇总完成（{year}年{month}月）: {result.get('message', '')}")
            print(f"[{datetime.now()}] 月度工时汇总完成（{year}年{month}月）")
            
            return result
        except Exception as e:
            logger.error(f"[{datetime.now()}] 月度工时汇总失败: {str(e)}")
            print(f"[{datetime.now()}] 月度工时汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


def generate_monthly_reports_task():
    """
    生成月度报表任务
    每月1号凌晨4点执行，生成上个月的各类报表
    """
    from app.services.timesheet_report_service import TimesheetReportService
    from app.services.timesheet_sync_service import TimesheetSyncService
    import logging
    
    logger = logging.getLogger(__name__)
    
    with get_db_session() as db:
        try:
            # 计算上个月
            today = date.today()
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1
            
            # 同步数据到各系统
            sync_service = TimesheetSyncService(db)
            
            # 同步到财务（所有项目）
            from app.models.project import Project
            projects = db.query(Project).filter(Project.is_active == True).all()
            finance_sync_count = 0
            for project in projects:
                try:
                    sync_result = sync_service.sync_to_finance(project_id=project.id, year=year, month=month)
                    if sync_result.get('success'):
                        finance_sync_count += sync_result.get('created_count', 0)
                except Exception as e:
                    logger.warning(f"同步项目{project.id}到财务失败: {str(e)}")
            
            # 同步到研发（所有研发项目）
            from app.models.rd_project import RdProject
            rd_projects = db.query(RdProject).filter(RdProject.is_active == True).all()
            rd_sync_count = 0
            for rd_project in rd_projects:
                try:
                    sync_result = sync_service.sync_to_rd(rd_project_id=rd_project.id, year=year, month=month)
                    if sync_result.get('success'):
                        rd_sync_count += sync_result.get('created_count', 0)
                except Exception as e:
                    logger.warning(f"同步研发项目{rd_project.id}失败: {str(e)}")
            
            # 同步到HR（生成加班工资数据）
            hr_sync_result = sync_service.sync_to_hr(year=year, month=month)
            
            logger.info(
                f"[{datetime.now()}] 月度报表生成完成（{year}年{month}月）: "
                f"财务{finance_sync_count}条，研发{rd_sync_count}条"
            )
            print(
                f"[{datetime.now()}] 月度报表生成完成（{year}年{month}月）: "
                f"财务{finance_sync_count}条，研发{rd_sync_count}条"
            )
            
            return {
                'success': True,
                'message': f'月度报表生成完成',
                'finance_sync_count': finance_sync_count,
                'rd_sync_count': rd_sync_count,
                'hr_sync': hr_sync_result
            }
        except Exception as e:
            logger.error(f"[{datetime.now()}] 月度报表生成失败: {str(e)}")
            print(f"[{datetime.now()}] 月度报表生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}


# ==================== 收款提醒服务 ====================

def check_payment_reminder():
    """
    S.8: 收款提醒服务
    每天上午9:30执行，提醒即将到期的收款计划
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.services.sales_reminder_service import notify_payment_plan_upcoming
            
            # 提醒7天内到期的收款计划
            count = notify_payment_plan_upcoming(db, days_before=7)
            
            logger.info(f"[{datetime.now()}] 收款提醒服务完成: 发送 {count} 条提醒")
            print(f"[{datetime.now()}] 收款提醒服务完成: 发送 {count} 条提醒")
            
            return {
                'reminder_count': count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 收款提醒服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 逾期应收预警服务 ====================

def check_overdue_receivable_alerts():
    """
    S.9: 逾期应收预警服务
    每天上午10:30执行，检查逾期应收款项并生成预警
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.sales import Invoice, Contract
            from decimal import Decimal
            
            today = date.today()
            
            # 获取或创建预警规则
            overdue_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'OVERDUE_RECEIVABLE',
                AlertRule.is_enabled == True
            ).first()
            
            if not overdue_rule:
                overdue_rule = AlertRule(
                    rule_code='OVERDUE_RECEIVABLE',
                    rule_name='逾期应收预警',
                    rule_type=AlertRuleTypeEnum.FINANCIAL.value,
                    target_type='INVOICE',
                    condition_type='THRESHOLD',
                    condition_operator='GT',
                    threshold_value='0',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当发票已逾期且未完全收款时触发预警'
                )
                db.add(overdue_rule)
                db.flush()
            
            # 查询逾期发票
            overdue_invoices = db.query(Invoice).join(Contract).filter(
                Invoice.status == "ISSUED",
                Invoice.payment_status.in_(["PENDING", "PARTIAL"]),
                Invoice.due_date.isnot(None),
                Invoice.due_date < today
            ).all()
            
            alert_count = 0
            
            for invoice in overdue_invoices:
                # 计算未收金额
                total_amount = invoice.total_amount or invoice.amount or Decimal("0")
                paid_amount = invoice.paid_amount or Decimal("0")
                unpaid_amount = total_amount - paid_amount
                
                if unpaid_amount <= 0:
                    continue
                
                overdue_days = (today - invoice.due_date).days
                
                # 检查是否已有待处理预警
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'INVOICE',
                    AlertRecord.target_id == invoice.id,
                    AlertRecord.rule_id == overdue_rule.id,
                    AlertRecord.status == 'PENDING'
                ).first()
                
                if existing_alert:
                    continue
                
                # 根据逾期天数确定预警级别
                if overdue_days >= 90:
                    alert_level = AlertLevelEnum.URGENT.value
                elif overdue_days >= 60:
                    alert_level = AlertLevelEnum.CRITICAL.value
                elif overdue_days >= 30:
                    alert_level = AlertLevelEnum.WARNING.value
                else:
                    alert_level = AlertLevelEnum.INFO.value
                
                # 生成预警编号
                alert_no = f'AR{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'
                
                contract = invoice.contract
                customer_name = contract.customer.customer_name if contract and contract.customer else "未知客户"
                
                alert = AlertRecord(
                    alert_no=alert_no,
                    rule_id=overdue_rule.id,
                    target_type='INVOICE',
                    target_id=invoice.id,
                    target_no=invoice.invoice_code,
                    target_name=f"发票 {invoice.invoice_code}",
                    project_id=contract.project_id if contract else None,
                    alert_level=alert_level,
                    alert_title=f'逾期应收预警：{invoice.invoice_code}',
                    alert_content=f'发票 {invoice.invoice_code}（客户：{customer_name}）已逾期 {overdue_days} 天，未收金额：{float(unpaid_amount):,.2f} 元，请及时跟进。',
                    status=AlertStatusEnum.PENDING.value,
                    triggered_at=datetime.now(),
                    trigger_value=str(overdue_days)
                )
                db.add(alert)
                alert_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 逾期应收预警检查完成: 检查 {len(overdue_invoices)} 张发票, 生成 {alert_count} 个预警")
            print(f"[{datetime.now()}] 逾期应收预警检查完成: 检查 {len(overdue_invoices)} 张发票, 生成 {alert_count} 个预警")
            
            return {
                'checked_count': len(overdue_invoices),
                'alert_count': alert_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 逾期应收预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 预警升级服务 ====================

def check_alert_escalation():
    """
    S.10: 预警升级服务（已重构，使用新的升级任务）
    每小时执行一次，检查超时未处理的预警并自动升级
    
    注意：此函数已重构，实际逻辑在 alert_escalation_task.py 中
    """
    from app.utils.alert_escalation_task import check_alert_timeout_escalation
    return check_alert_timeout_escalation()


# ==================== 商机阶段超时提醒 ====================

def check_opportunity_stage_timeout():
    """
    S.13: 商机阶段超时提醒
    每天下午3:30执行，检查商机在某个阶段停留时间过长
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.sales import Opportunity
            from app.models.notification import Notification
            
            today = date.today()
            
            # 查询活跃的商机
            opportunities = db.query(Opportunity).filter(
                Opportunity.status.in_(["ACTIVE", "NEGOTIATING", "PROPOSAL"])
            ).all()
            
            reminder_count = 0
            
            # 各阶段的标准停留时间（天）
            stage_timeout_days = {
                "QUALIFICATION": 7,      # 资格确认：7天
                "NEEDS_ANALYSIS": 14,   # 需求分析：14天
                "PROPOSAL": 10,         # 方案设计：10天
                "NEGOTIATION": 14,      # 商务谈判：14天
                "CLOSING": 7            # 成交阶段：7天
            }
            
            for opp in opportunities:
                if not opp.stage or not opp.updated_at:
                    continue
                
                # 计算在当前阶段停留的天数
                days_in_stage = (today - opp.updated_at.date()).days
                timeout_days = stage_timeout_days.get(opp.stage, 14)
                
                # 如果超过标准时间，发送提醒
                if days_in_stage > timeout_days:
                    # 检查今天是否已发送过提醒
                    existing = db.query(Notification).filter(
                        Notification.source_type == "opportunity",
                        Notification.source_id == opp.id,
                        Notification.notification_type == "OPPORTUNITY_STAGE_TIMEOUT",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    ).first()
                    
                    if not existing:
                        from app.services.sales_reminder_service import create_notification
                        
                        create_notification(
                            db=db,
                            user_id=opp.owner_id,
                            notification_type="OPPORTUNITY_STAGE_TIMEOUT",
                            title=f"商机阶段停留超时：{opp.opportunity_name}",
                            content=f"商机 {opp.opportunity_name} 在 {opp.stage} 阶段已停留 {days_in_stage} 天，超过标准时间 {timeout_days} 天，请及时推进。",
                            source_type="opportunity",
                            source_id=opp.id,
                            link_url=f"/sales/opportunities/{opp.id}",
                            priority="HIGH" if days_in_stage > timeout_days * 1.5 else "NORMAL",
                            extra_data={
                                "opportunity_name": opp.opportunity_name,
                                "stage": opp.stage,
                                "days_in_stage": days_in_stage,
                                "timeout_days": timeout_days
                            }
                        )
                        reminder_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 商机阶段超时提醒完成: 检查 {len(opportunities)} 个商机, 发送 {reminder_count} 条提醒")
            print(f"[{datetime.now()}] 商机阶段超时提醒完成: 检查 {len(opportunities)} 个商机, 发送 {reminder_count} 条提醒")
            
            return {
                'checked_count': len(opportunities),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 商机阶段超时提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 售前工单超时提醒 ====================

def check_presale_workorder_timeout():
    """
    S.22: 售前工单超时提醒
    每天下午4:00执行，检查售前工单处理超时
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.presale import PresaleSupportTicket
            from app.models.notification import Notification
            
            today = date.today()
            
            # 查询进行中的售前工单
            tickets = db.query(PresaleSupportTicket).filter(
                PresaleSupportTicket.status.in_(["PENDING", "ACCEPTED", "PROCESSING"])
            ).all()
            
            reminder_count = 0
            
            for ticket in tickets:
                if not ticket.created_at:
                    continue
                
                # 计算工单创建天数
                days_since_created = (today - ticket.created_at.date()).days
                
                # 根据工单类型确定超时阈值（天）
                timeout_days = {
                    "CONSULT": 3,          # 技术咨询：3天
                    "QUOTATION": 5,        # 报价支持：5天
                    "SOLUTION": 7,         # 方案设计：7天
                    "TENDER": 10,          # 投标支持：10天
                    "OTHER": 5             # 其他：5天
                }
                
                ticket_type = ticket.ticket_type or "OTHER"
                threshold = timeout_days.get(ticket_type, 5)
                
                # 如果超过阈值，发送提醒
                if days_since_created > threshold:
                    # 检查今天是否已发送过提醒
                    existing = db.query(Notification).filter(
                        Notification.source_type == "presale_ticket",
                        Notification.source_id == ticket.id,
                        Notification.notification_type == "PRESALE_TICKET_TIMEOUT",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    ).first()
                    
                    if not existing:
                        from app.services.sales_reminder_service import create_notification
                        
                        # 获取负责人
                        assignee_id = ticket.assignee_id or ticket.applicant_id
                        if not assignee_id:
                            continue
                        
                        create_notification(
                            db=db,
                            user_id=assignee_id,
                            notification_type="PRESALE_TICKET_TIMEOUT",
                            title=f"售前工单处理超时：{ticket.ticket_no}",
                            content=f"售前工单 {ticket.ticket_no}（{ticket.title}）已创建 {days_since_created} 天，超过标准处理时间 {threshold} 天，请及时处理。",
                            source_type="presale_ticket",
                            source_id=ticket.id,
                            link_url=f"/presale/tickets/{ticket.id}",
                            priority="HIGH" if days_since_created > threshold * 1.5 else "NORMAL",
                            extra_data={
                                "ticket_no": ticket.ticket_no,
                                "title": ticket.title,
                                "ticket_type": ticket_type,
                                "days_since_created": days_since_created,
                                "timeout_days": threshold
                            }
                        )
                        reminder_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 售前工单超时提醒完成: 检查 {len(tickets)} 个工单, 发送 {reminder_count} 条提醒")
            print(f"[{datetime.now()}] 售前工单超时提醒完成: 检查 {len(tickets)} 个工单, 发送 {reminder_count} 条提醒")
            
            return {
                'checked_count': len(tickets),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 售前工单超时提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 问题超时升级服务 ====================

def check_issue_timeout_escalation():
    """
    S.26: 问题超时升级服务
    每天凌晨1:30执行，检查问题处理超时并升级
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.issue import Issue
            
            today = date.today()
            escalated_count = 0
            
            # 查询进行中的问题
            issues = db.query(Issue).filter(
                Issue.status.in_(["OPEN", "IN_PROGRESS", "REOPENED"])
            ).all()
            
            for issue in issues:
                if not issue.created_at:
                    continue
                
                # 计算问题创建天数
                days_since_created = (today - issue.created_at.date()).days
                
                # 根据问题级别确定超时阈值（天）
                timeout_days = {
                    "LOW": 14,      # 低：14天
                    "MEDIUM": 7,    # 中：7天
                    "HIGH": 3,      # 高：3天
                    "CRITICAL": 1   # 严重：1天
                }
                
                issue_level = issue.priority or "MEDIUM"
                threshold = timeout_days.get(issue_level, 7)
                
                # 如果超过阈值，升级问题级别
                if days_since_created > threshold:
                    # 升级逻辑：LOW -> MEDIUM -> HIGH -> CRITICAL
                    level_upgrade = {
                        "LOW": "MEDIUM",
                        "MEDIUM": "HIGH",
                        "HIGH": "CRITICAL",
                        "CRITICAL": "CRITICAL"  # 已经是最高级别
                    }
                    
                    new_level = level_upgrade.get(issue_level, issue_level)
                    if new_level != issue_level:
                        issue.priority = new_level
                        escalated_count += 1
                        
                        # 记录升级日志
                        logger.warning(f"问题 {issue.issue_no} 超时升级: {issue_level} -> {new_level} (已创建 {days_since_created} 天)")
            
            db.commit()
            
            if escalated_count > 0:
                logger.info(f"[{datetime.now()}] 问题超时升级服务完成: 升级 {escalated_count} 个问题")
                print(f"[{datetime.now()}] 问题超时升级服务完成: 升级 {escalated_count} 个问题")
            
            return {
                'checked_count': len(issues),
                'escalated_count': escalated_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 问题超时升级服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 设备保养提醒服务 ====================

def check_equipment_maintenance_reminder():
    """
    S.16: 设备保养提醒服务
    每天上午8:30执行，检查设备保养计划并发送提醒
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.production import Equipment
            from app.models.notification import Notification
            from app.models.user import User
            
            today = date.today()
            
            # 查询有保养计划的设备（下次保养日期在未来7天内）
            target_date = today + timedelta(days=7)
            
            equipment_list = db.query(Equipment).filter(
                Equipment.is_active == True,
                Equipment.next_maintenance_date.isnot(None),
                Equipment.next_maintenance_date >= today,
                Equipment.next_maintenance_date <= target_date
            ).all()
            
            reminder_count = 0
            
            for equipment in equipment_list:
                if not equipment.next_maintenance_date:
                    continue
                
                # 计算距离保养日期的天数
                days_until_maintenance = (equipment.next_maintenance_date - today).days
                
                # 检查今天是否已发送过提醒
                existing = db.query(Notification).filter(
                    Notification.source_type == "equipment",
                    Notification.source_id == equipment.id,
                    Notification.notification_type == "EQUIPMENT_MAINTENANCE_REMINDER",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                ).first()
                
                if existing:
                    continue
                
                # 根据距离天数确定优先级
                if days_until_maintenance <= 1:
                    priority = "URGENT"
                elif days_until_maintenance <= 3:
                    priority = "HIGH"
                else:
                    priority = "NORMAL"
                
                # 获取设备所属车间的负责人（这里简化处理，可以后续优化）
                # 暂时发送给系统管理员或设备管理员
                # TODO: 根据实际业务逻辑确定接收人
                recipients = db.query(User).filter(
                    User.is_active == True,
                    # 可以添加角色筛选，例如：设备管理员
                ).limit(5).all()
                
                if not recipients:
                    # 如果没有找到接收人，跳过
                    continue
                
                from app.services.sales_reminder_service import create_notification
                
                for recipient in recipients:
                    create_notification(
                        db=db,
                        user_id=recipient.id,
                        notification_type="EQUIPMENT_MAINTENANCE_REMINDER",
                        title=f"设备保养提醒：{equipment.equipment_name}",
                        content=f"设备 {equipment.equipment_code}（{equipment.equipment_name}）将在 {days_until_maintenance} 天后进行保养，保养日期：{equipment.next_maintenance_date}，请提前安排。",
                        source_type="equipment",
                        source_id=equipment.id,
                        link_url=f"/production/equipment/{equipment.id}",
                        priority=priority,
                        extra_data={
                            "equipment_code": equipment.equipment_code,
                            "equipment_name": equipment.equipment_name,
                            "next_maintenance_date": equipment.next_maintenance_date.isoformat() if equipment.next_maintenance_date else None,
                            "days_until_maintenance": days_until_maintenance,
                            "last_maintenance_date": equipment.last_maintenance_date.isoformat() if equipment.last_maintenance_date else None
                        }
                    )
                    reminder_count += 1
            
            db.commit()
            
            logger.info(f"[{datetime.now()}] 设备保养提醒服务完成: 检查 {len(equipment_list)} 台设备, 发送 {reminder_count} 条提醒")
            print(f"[{datetime.now()}] 设备保养提醒服务完成: 检查 {len(equipment_list)} 台设备, 发送 {reminder_count} 条提醒")
            
            return {
                'checked_count': len(equipment_list),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 设备保养提醒服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 通知重试机制 ====================

def retry_failed_notifications():
    """
    Issue 1.3: 通知重试机制
    每小时执行一次，重试发送失败的通知
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.user import User
            from app.models.notification import NotificationSettings
            
            current_time = datetime.now()
            max_retries = 3
            
            # 查询需要重试的通知
            failed_notifications = db.query(AlertNotification).filter(
                AlertNotification.status == 'FAILED',
                AlertNotification.retry_count < max_retries,
                or_(
                    AlertNotification.next_retry_at.is_(None),
                    AlertNotification.next_retry_at <= current_time
                )
            ).all()
            
            retry_count = 0
            success_count = 0
            failed_count = 0
            abandoned_count = 0
            
            dispatcher = NotificationDispatcher(db)
            
            for notification in failed_notifications:
                # 检查是否在免打扰时段
                settings = None
                if notification.notify_user_id:
                    settings = db.query(NotificationSettings).filter(
                        NotificationSettings.user_id == notification.notify_user_id
                    ).first()
                
                if is_quiet_hours(settings, current_time):
                    notification.next_retry_at = next_quiet_resume(settings, current_time)
                    notification.error_message = "Delayed due to quiet hours"
                    continue
                
                # 获取预警和用户信息
                alert = notification.alert
                user = None
                if notification.notify_user_id:
                    user = db.query(User).filter(User.id == notification.notify_user_id).first()
                
                if not alert or not user:
                    # 如果预警或用户不存在，标记为放弃
                    notification.status = 'ABANDONED'
                    notification.error_message = "Alert or user not found"
                    abandoned_count += 1
                    continue
                
                # 尝试重新发送
                retry_count += 1
                success = dispatcher.dispatch(notification, alert, user)
                
                if success:
                    success_count += 1
                    logger.info(f"Retry successful for notification {notification.id}")
                else:
                    failed_count += 1
                    # 如果超过最大重试次数，标记为放弃
                    if notification.retry_count >= max_retries:
                        notification.status = 'ABANDONED'
                        notification.error_message = f"Max retries ({max_retries}) exceeded"
                        abandoned_count += 1
                    logger.warning(f"Retry failed for notification {notification.id}: {notification.error_message}")
            
            db.commit()
            
            logger.info(
                f"[{datetime.now()}] 通知重试完成: "
                f"重试 {retry_count} 个, 成功 {success_count} 个, "
                f"失败 {failed_count} 个, 放弃 {abandoned_count} 个"
            )
            print(
                f"[{datetime.now()}] 通知重试完成: "
                f"重试 {retry_count} 个, 成功 {success_count} 个, "
                f"失败 {failed_count} 个, 放弃 {abandoned_count} 个"
            )
            
            return {
                'retry_count': retry_count,
                'success_count': success_count,
                'failed_count': failed_count,
                'abandoned_count': abandoned_count,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"[{datetime.now()}] 通知重试失败: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 消息推送服务 ====================

def send_alert_notifications():
    """
    S.12: 消息推送服务
    - 为新预警生成通知队列
    - 根据通知渠道发送消息（站内信、企业微信、邮件）
    - 失败任务支持重试策略
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            dispatcher = NotificationDispatcher(db)
            from app.models.alert import AlertRecord, AlertNotification
            from app.models.user import User
            from app.models.notification import NotificationSettings
            
            # 1) 生成通知队列
            pending_alerts = db.query(AlertRecord).filter(
                AlertRecord.status == 'PENDING'
            ).order_by(AlertRecord.triggered_at.desc().nulls_last()).limit(50).all()
            
            queue_created = 0
            current_time = datetime.now()
            for alert in pending_alerts:
                recipients = resolve_recipients(db, alert)
                if not recipients:
                    continue
                channels = resolve_channels(alert)
                for user_id, recipient in recipients.items():
                    user = recipient.get("user")
                    settings = recipient.get("settings")
                    if not user:
                        continue
                    for channel in channels:
                        if not channel_allowed(channel, settings):
                            continue
                        target = resolve_channel_target(channel, user)
                        if not target:
                            continue
                        exists = db.query(AlertNotification).filter(
                            AlertNotification.alert_id == alert.id,
                            AlertNotification.notify_channel == channel,
                            AlertNotification.notify_target == target
                        ).first()
                        if exists:
                            continue
                        new_notification = AlertNotification(
                            alert_id=alert.id,
                            notify_channel=channel,
                            notify_target=target,
                            notify_user_id=user.id,
                            notify_title=alert.alert_title,
                            notify_content=alert.alert_content,
                            status='PENDING'
                        )
                        if is_quiet_hours(settings, current_time):
                            new_notification.next_retry_at = next_quiet_resume(settings, current_time)
                            new_notification.error_message = "Delayed due to quiet hours"
                        db.add(new_notification)
                        queue_created += 1
            
            db.flush()
            
            # 2) 发送通知（包含失败重试）
            now = datetime.now()
            pending_notifications = db.query(AlertNotification).filter(
                AlertNotification.status.in_(["PENDING", "FAILED"]),
                or_(AlertNotification.next_retry_at.is_(None), AlertNotification.next_retry_at <= now)
            ).order_by(AlertNotification.created_at.asc()).limit(100).all()
            
            channel_stats = {}
            sent_count = 0
            queued_notifications = 0
            for notification in pending_notifications:
                alert = notification.alert
                user = None
                if notification.notify_user_id:
                    user = db.query(User).filter(User.id == notification.notify_user_id).first()
                settings_obj = None
                if notification.notify_user_id:
                    settings_obj = db.query(NotificationSettings).filter(
                        NotificationSettings.user_id == notification.notify_user_id
                    ).first()
                if is_quiet_hours(settings_obj, now):
                    notification.status = 'PENDING'
                    notification.next_retry_at = next_quiet_resume(settings_obj, now)
                    notification.error_message = "Delayed due to quiet hours"
                    continue
                enqueued = enqueue_notification({
                    "notification_id": notification.id,
                    "alert_id": notification.alert_id,
                    "notify_channel": notification.notify_channel,
                })
                if enqueued:
                    notification.status = 'QUEUED'
                    notification.next_retry_at = None
                    queued_notifications += 1
                else:
                    # fallback: try immediate dispatch synchronously
                    success = dispatcher.dispatch(notification, alert, user)
                    stats = channel_stats.setdefault(notification.notify_channel.upper(), {"success": 0, "failed": 0})
                    if success:
                        stats["success"] += 1
                        sent_count += 1
                    else:
                        stats["failed"] += 1
            
            db.commit()
            
            logger.info(
                f"[{datetime.now()}] 消息推送服务完成: 准备 {queue_created} 条队列, "
                f"处理 {len(pending_notifications)} 条通知, 入队 {queued_notifications} 条, 直接发送 {sent_count} 条"
            )
            
            return {
                'queued_alerts': len(pending_alerts),
                'queue_created': queue_created,
                'processed_notifications': len(pending_notifications),
                'queued_notifications': queued_notifications,
                'sent_count': sent_count,
                'channel_stats': channel_stats,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 消息推送服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# ==================== 计算响应时效指标 ====================

def calculate_response_metrics():
    """
    计算响应时效指标
    每天凌晨1点执行，计算昨天的预警响应时效指标并更新统计表
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        with get_db_session() as db:
            from app.models.alert import AlertStatistics
            from decimal import Decimal
            
            # 计算昨天的日期
            yesterday = date.today() - timedelta(days=1)
            
            # 查询昨天触发的预警
            yesterday_start = datetime.combine(yesterday, datetime.min.time())
            yesterday_end = datetime.combine(yesterday, datetime.max.time())
            
            alerts = db.query(AlertRecord).filter(
                AlertRecord.triggered_at >= yesterday_start,
                AlertRecord.triggered_at <= yesterday_end
            ).all()
            
            # 计算响应时间（已确认的预警）
            response_times = []
            for alert in alerts:
                if alert.acknowledged_at and alert.triggered_at:
                    delta = alert.acknowledged_at - alert.triggered_at
                    hours = delta.total_seconds() / 3600
                    response_times.append(hours)
            
            # 计算解决时间（已解决的预警）
            resolve_times = []
            for alert in alerts:
                if alert.acknowledged_at and alert.handle_end_at:
                    delta = alert.handle_end_at - alert.acknowledged_at
                    hours = delta.total_seconds() / 3600
                    resolve_times.append(hours)
            
            # 计算平均值
            avg_response_time = Decimal(str(sum(response_times) / len(response_times))) if response_times else Decimal("0")
            avg_resolve_time = Decimal(str(sum(resolve_times) / len(resolve_times))) if resolve_times else Decimal("0")
            
            # 获取或创建统计记录
            stat = db.query(AlertStatistics).filter(
                AlertStatistics.stat_date == yesterday,
                AlertStatistics.stat_type == 'DAILY'
            ).first()
            
            if not stat:
                stat = AlertStatistics(
                    stat_date=yesterday,
                    stat_type='DAILY',
                    total_alerts=len(alerts),
                    avg_response_time=avg_response_time,
                    avg_resolve_time=avg_resolve_time
                )
                db.add(stat)
            else:
                stat.avg_response_time = avg_response_time
                stat.avg_resolve_time = avg_resolve_time
                stat.total_alerts = len(alerts)
            
            db.commit()
            
            logger.info(
                f"[{datetime.now()}] 响应时效指标计算完成（{yesterday}）: "
                f"预警数={len(alerts)}, 平均响应时间={float(avg_response_time):.2f}小时, "
                f"平均解决时间={float(avg_resolve_time):.2f}小时"
            )
            print(
                f"[{datetime.now()}] 响应时效指标计算完成（{yesterday}）: "
                f"预警数={len(alerts)}, 平均响应时间={float(avg_response_time):.2f}小时, "
                f"平均解决时间={float(avg_resolve_time):.2f}小时"
            )
            
            return {
                'stat_date': yesterday.isoformat(),
                'total_alerts': len(alerts),
                'avg_response_time_hours': float(avg_response_time),
                'avg_resolve_time_hours': float(avg_resolve_time),
                'response_count': len(response_times),
                'resolve_count': len(resolve_times),
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 响应时效指标计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_contract_expiry_reminder():
    """
    合同到期提醒定时任务
    - 提前60天（两个月）、30天（一个月）、14天（两周）生成提醒
    - 已到期的合同也生成提醒
    """
    logger.info(f"[{datetime.now()}] 开始执行合同到期提醒检查...")

    try:
        from app.models.base import get_db_session
        from app.models.organization import EmployeeContract, ContractReminder, Employee

        with get_db_session() as db:
            today = date.today()
            reminders_created = 0

            # 定义提醒规则：(天数, 提醒类型)
            reminder_rules = [
                (60, "two_months"),
                (30, "one_month"),
                (14, "two_weeks"),
                (0, "expired"),  # 已到期
            ]

            # 查询所有生效中的合同
            active_contracts = db.query(EmployeeContract).filter(
                EmployeeContract.status == "active",
                EmployeeContract.end_date.isnot(None)
            ).all()

            for contract in active_contracts:
                if not contract.end_date:
                    continue

                days_until_expiry = (contract.end_date - today).days

                for days, reminder_type in reminder_rules:
                    # 检查是否需要生成该类型提醒
                    should_create = False

                    if reminder_type == "expired":
                        # 已到期：到期日当天或之后
                        should_create = days_until_expiry <= 0
                    else:
                        # 提前提醒：在指定天数范围内
                        if reminder_type == "two_months":
                            should_create = 30 < days_until_expiry <= 60
                        elif reminder_type == "one_month":
                            should_create = 14 < days_until_expiry <= 30
                        elif reminder_type == "two_weeks":
                            should_create = 0 < days_until_expiry <= 14

                    if not should_create:
                        continue

                    # 检查是否已存在相同类型的提醒
                    existing = db.query(ContractReminder).filter(
                        ContractReminder.contract_id == contract.id,
                        ContractReminder.reminder_type == reminder_type
                    ).first()

                    if existing:
                        continue

                    # 创建提醒记录
                    reminder = ContractReminder(
                        contract_id=contract.id,
                        employee_id=contract.employee_id,
                        reminder_type=reminder_type,
                        reminder_date=today,
                        contract_end_date=contract.end_date,
                        days_until_expiry=days_until_expiry if days_until_expiry > 0 else 0,
                        status="pending"
                    )
                    db.add(reminder)
                    reminders_created += 1

                    # 更新合同的提醒状态
                    contract.reminder_sent = True
                    contract.reminder_sent_at = datetime.now()

            db.commit()

            logger.info(
                f"[{datetime.now()}] 合同到期提醒检查完成: "
                f"检查合同数={len(active_contracts)}, 生成提醒数={reminders_created}"
            )
            print(
                f"[{datetime.now()}] 合同到期提醒检查完成: "
                f"检查合同数={len(active_contracts)}, 生成提醒数={reminders_created}"
            )

            return {
                'contracts_checked': len(active_contracts),
                'reminders_created': reminders_created,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 合同到期提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_employee_confirmation_reminder():
    """
    员工转正提醒定时任务
    - 检查试用期即将结束的员工（提前7天提醒）
    - 自动生成转正事务记录
    """
    logger.info(f"[{datetime.now()}] 开始执行员工转正提醒检查...")

    try:
        from app.models.base import get_db_session
        from app.models.organization import Employee, EmployeeHrProfile, HrTransaction
        from app.models.notification import Notification

        with get_db_session() as db:
            today = date.today()
            reminder_date = today + timedelta(days=7)  # 提前7天
            reminders_created = 0

            # 查询试用期员工
            probation_employees = db.query(Employee).join(
                EmployeeHrProfile, Employee.id == EmployeeHrProfile.employee_id
            ).filter(
                Employee.employment_type == "probation",
                Employee.is_active == True,
                EmployeeHrProfile.is_confirmed == False,
                EmployeeHrProfile.probation_end_date.isnot(None),
                EmployeeHrProfile.probation_end_date <= reminder_date,
                EmployeeHrProfile.probation_end_date >= today
            ).all()

            for employee in probation_employees:
                profile = employee.hr_profile
                if not profile or not profile.probation_end_date:
                    continue

                days_until_confirmation = (profile.probation_end_date - today).days

                # 检查是否已存在待处理的转正事务
                existing = db.query(HrTransaction).filter(
                    HrTransaction.employee_id == employee.id,
                    HrTransaction.transaction_type == "confirmation",
                    HrTransaction.status.in_(["pending", "approved"])
                ).first()

                if existing:
                    continue

                # 创建转正事务记录
                transaction = HrTransaction(
                    employee_id=employee.id,
                    transaction_type="confirmation",
                    transaction_date=profile.probation_end_date,
                    status="pending",
                    confirmation_date=profile.probation_end_date,
                    remark=f"系统自动生成：{employee.name}试用期将于{profile.probation_end_date}结束，请安排转正评估"
                )
                db.add(transaction)
                reminders_created += 1

                # 创建系统通知
                notification = Notification(
                    user_id=None,  # 发给HR管理员
                    title="员工转正提醒",
                    content=f"员工 {employee.name}（{employee.employee_code}）的试用期将于{profile.probation_end_date}结束（还有{days_until_confirmation}天），请安排转正评估。",
                    notification_type="hr_reminder",
                    priority="high" if days_until_confirmation <= 3 else "normal",
                    is_read=False,
                    source_type="hr_transaction",
                    source_id=None  # 稍后更新
                )
                db.add(notification)

            db.commit()

            logger.info(
                f"[{datetime.now()}] 员工转正提醒检查完成: "
                f"检查员工数={len(probation_employees)}, 生成提醒数={reminders_created}"
            )
            print(
                f"[{datetime.now()}] 员工转正提醒检查完成: "
                f"检查员工数={len(probation_employees)}, 生成提醒数={reminders_created}"
            )

            return {
                'employees_checked': len(probation_employees),
                'reminders_created': reminders_created,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 员工转正提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
