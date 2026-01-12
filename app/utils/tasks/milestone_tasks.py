# -*- coding: utf-8 -*-
"""
里程碑和成本定时任务

包含里程碑预警、成本超支预警、收款计划调整等
"""

import logging
from datetime import datetime, date, timedelta
from sqlalchemy import func

from app.models.base import get_db_session
from app.models.project import Project, ProjectMilestone, ProjectCost
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
    try:
        with get_db_session() as db:
            from app.services.payment_adjustment_service import PaymentAdjustmentService

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


def check_milestone_risk_alerts():
    """
    里程碑风险预警服务
    每天执行一次，检查里程碑进度风险
    """
    try:
        with get_db_session() as db:
            today = date.today()

            # 查询进行中的里程碑
            active_milestones = db.query(ProjectMilestone).filter(
                ProjectMilestone.status.in_(['NOT_STARTED', 'IN_PROGRESS']),
                ProjectMilestone.planned_date.isnot(None)
            ).all()

            risk_count = 0

            for milestone in active_milestones:
                # 计算剩余天数
                days_left = (milestone.planned_date - today).days

                # 获取完成进度
                progress = milestone.progress or 0

                # 计算预期进度
                if milestone.start_date:
                    total_days = (milestone.planned_date - milestone.start_date).days
                    elapsed_days = (today - milestone.start_date).days
                    expected_progress = (elapsed_days / total_days * 100) if total_days > 0 else 0
                else:
                    expected_progress = 0

                # 判断是否存在风险（进度落后超过20%）
                if progress < expected_progress - 20 and days_left <= 7:
                    # 检查是否已有风险预警
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'MILESTONE',
                        AlertRecord.target_id == milestone.id,
                        AlertRecord.alert_title.like('%进度风险%'),
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if not existing_alert:
                        alert_no = f'MR{today.strftime("%Y%m%d")}{str(risk_count + 1).zfill(4)}'

                        alert = AlertRecord(
                            alert_no=alert_no,
                            target_type='MILESTONE',
                            target_id=milestone.id,
                            target_no=milestone.milestone_code,
                            target_name=milestone.milestone_name,
                            project_id=milestone.project_id,
                            alert_level=AlertLevelEnum.WARNING.value,
                            alert_title=f'里程碑进度风险：{milestone.milestone_name}',
                            alert_content=f'里程碑 {milestone.milestone_code} 当前进度 {progress}%，预期进度 {expected_progress:.1f}%，剩余 {days_left} 天',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now()
                        )
                        db.add(alert)
                        risk_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 里程碑风险预警检查完成: 检查 {len(active_milestones)} 个里程碑, 发现 {risk_count} 个风险")

            return {
                'checked_count': len(active_milestones),
                'risk_count': risk_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 里程碑风险预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_cost_overrun_alerts():
    """
    成本超支预警服务
    每天执行一次，检查项目成本是否超支
    """
    try:
        with get_db_session() as db:
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
