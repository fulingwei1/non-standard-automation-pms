# -*- coding: utf-8 -*-
"""
定时任务 - 项目健康度任务
包含：健康度计算、每日健康度快照
"""
import logging
from datetime import date, datetime

from app.models.base import get_db_session
from app.models.project import Project

logger = logging.getLogger(__name__)


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

            logger.info(
                f"健康度计算完成: 总计 {result['total']} 个项目, "
                f"更新 {result['updated']} 个, 未变化 {result['unchanged']} 个"
            )

            return result
    except Exception as e:
        logger.error(f"健康度计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_health_snapshot():
    """
    每日健康度快照
    每天凌晨2点执行，生成所有项目的健康度快照
    """
    try:
        from app.models.alert import ProjectHealthSnapshot
        from app.services.health_calculator import HealthCalculator

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

            logger.info(f"健康度快照生成完成: 生成 {snapshot_count} 个快照")

            return {
                'snapshot_count': snapshot_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"健康度快照生成失败: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
