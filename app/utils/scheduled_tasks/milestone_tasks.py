# -*- coding: utf-8 -*-
"""
定时任务 - 里程碑相关任务
包含：里程碑预警、里程碑状态监控与收款计划调整、里程碑风险预警
"""
import logging
from datetime import date, datetime

from app.common.query_filters import apply_keyword_filter
from app.models.alert import AlertRecord
from app.dependencies import get_db_session
from app.models.enums import AlertLevelEnum, AlertStatusEnum
from app.models.project import ProjectMilestone

logger = logging.getLogger(__name__)


def check_milestone_alerts():
    """
    里程碑预警服务

    使用重构后的MilestoneAlertService，将原来133行的复杂函数拆分为多个小函数
    """
    try:
        with get_db_session() as db:
            from app.services.alert.milestone_alert_service import MilestoneAlertService

            alert_service = MilestoneAlertService(db)
            alert_count = alert_service.check_milestone_alerts()

            db.commit()

            logger.info(
                f"[{datetime.now()}] 里程碑预警检查完成: "
                f"生成 {alert_count} 个预警"
            )

            return {
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
                Project.is_active,
                not Project.is_archived
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
                    existing_query = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'PROJECT',
                        AlertRecord.target_id == project.id,
                        AlertRecord.status == 'PENDING'
                    )
                    existing_query = apply_keyword_filter(
                        existing_query,
                        AlertRecord,
                        "里程碑风险",
                        "alert_title",
                        use_ilike=False,
                    )
                    existing = existing_query.first()

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
