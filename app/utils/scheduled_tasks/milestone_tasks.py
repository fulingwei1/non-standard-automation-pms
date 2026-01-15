# -*- coding: utf-8 -*-
"""
定时任务 - 里程碑相关任务
包含：里程碑预警、里程碑状态监控与收款计划调整、里程碑风险预警
"""
import logging
from datetime import datetime, date, timedelta

from app.models.base import get_db_session
from app.models.project import ProjectMilestone
from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum

logger = logging.getLogger(__name__)


def check_milestone_alerts():
    """
    里程碑预警服务
    每天执行一次，检查即将到期或已逾期的里程碑
    """
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
                        alert_content=f'里程碑 {milestone.milestone_code} 将在 {days_left} 天后到期'
                                      f'（计划日期：{milestone.planned_date}）',
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
                        alert_content=f'里程碑 {milestone.milestone_code} 已逾期 {days_overdue} 天'
                                      f'（计划日期：{milestone.planned_date}）',
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now()
                    )
                    db.add(alert)
                    alert_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 里程碑预警检查完成: "
                f"即将到期 {len(upcoming_milestones)} 个, "
                f"已逾期 {len(overdue_milestones)} 个, 生成 {alert_count} 个预警"
            )

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
    监控项目里程碑状态变化并自动调整收款计划
    每小时执行一次，检查里程碑状态变化（延期、提前完成）并调整关联的收款计划
    """
    try:
        with get_db_session() as db:
            from app.services.payment_adjustment_service import PaymentAdjustmentService

            service = PaymentAdjustmentService(db)
            result = service.check_and_adjust_all()

            logger.info(
                f"[{datetime.now()}] 里程碑-收款计划调整检查完成: "
                f"检查 {result.get('checked', 0)} 个里程碑, "
                f"调整 {result.get('adjusted', 0)} 个收款计划"
            )

            return result
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑-收款计划调整检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_milestone_risk_alerts():
    """
    里程碑风险预警服务
    每天执行一次，分析里程碑完成趋势并预警高风险项目
    """
    try:
        with get_db_session() as db:
            from app.models.project import Project

            today = date.today()

            # 查询活跃项目
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.is_archived == False
            ).all()

            risk_count = 0

            for project in projects:
                # 获取项目的里程碑
                milestones = db.query(ProjectMilestone).filter(
                    ProjectMilestone.project_id == project.id,
                    ProjectMilestone.status != 'COMPLETED'
                ).all()

                if not milestones:
                    continue

                # 计算风险指标
                overdue_count = sum(
                    1 for m in milestones
                    if m.planned_date and m.planned_date < today
                )

                total_count = len(milestones)
                risk_ratio = overdue_count / total_count if total_count > 0 else 0

                # 如果逾期比例超过30%，生成风险预警
                if risk_ratio >= 0.3:
                    # 检查是否已有预警
                    existing = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'PROJECT',
                        AlertRecord.target_id == project.id,
                        AlertRecord.alert_title.like('%里程碑风险%'),
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if not existing:
                        alert_no = f'MR{today.strftime("%Y%m%d")}{str(risk_count + 1).zfill(4)}'

                        alert = AlertRecord(
                            alert_no=alert_no,
                            target_type='PROJECT',
                            target_id=project.id,
                            target_no=project.project_code,
                            target_name=project.project_name,
                            project_id=project.id,
                            alert_level=AlertLevelEnum.WARNING.value
                            if risk_ratio < 0.5 else AlertLevelEnum.CRITICAL.value,
                            alert_title=f'里程碑风险预警：{project.project_name}',
                            alert_content=f'项目 {project.project_code} 有 {overdue_count}/{total_count} '
                                          f'个里程碑已逾期（{risk_ratio * 100:.1f}%），请及时关注',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now()
                        )
                        db.add(alert)
                        risk_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 里程碑风险预警检查完成: "
                f"检查 {len(projects)} 个项目, 生成 {risk_count} 个风险预警"
            )

            return {
                'checked_projects': len(projects),
                'risk_alerts': risk_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑风险预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
