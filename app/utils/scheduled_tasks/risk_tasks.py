# -*- coding: utf-8 -*-
"""
定时任务 - 项目风险自动计算

包含：
1. 批量计算所有活跃项目的风险等级
2. 创建风险快照（用于趋势分析）
3. 检测风险升级并触发通知
"""

import logging
from datetime import datetime
from typing import Dict, Any

from app.models.base import get_db_session
from app.common.query_filters import apply_keyword_filter

logger = logging.getLogger(__name__)


def calculate_all_project_risks() -> Dict[str, Any]:
    """
    批量计算所有活跃项目的风险等级

    每天执行一次，自动评估所有活跃项目的风险状态，
    检测风险升级并记录历史。

    Returns:
        执行结果统计
    """
    try:
        with get_db_session() as db:
            from app.services.project.project_risk_service import ProjectRiskService

            service = ProjectRiskService(db)
            results = service.batch_calculate_risks(active_only=True)

            # 统计结果
            success_count = sum(1 for r in results if "error" not in r)
            error_count = sum(1 for r in results if "error" in r)
            upgrade_count = sum(1 for r in results if r.get("is_upgrade", False))

            logger.info(
                f"[{datetime.now()}] 项目风险批量计算完成: "
                f"成功 {success_count} 个, 失败 {error_count} 个, "
                f"风险升级 {upgrade_count} 个"
            )

            return {
                "total": len(results),
                "success": success_count,
                "errors": error_count,
                "upgrades": upgrade_count,
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 项目风险批量计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def create_daily_risk_snapshots() -> Dict[str, Any]:
    """
    为所有活跃项目创建风险快照

    每天执行一次，保存项目风险状态快照，
    用于后续的趋势分析和报表生成。

    Returns:
        执行结果统计
    """
    try:
        with get_db_session() as db:
            from app.models.project import Project
            from app.services.project.project_risk_service import ProjectRiskService

            service = ProjectRiskService(db)

            # 获取所有活跃项目
            projects = db.query(Project).filter(
                Project.is_active,
                not Project.is_archived,
            ).all()

            success_count = 0
            error_count = 0

            for project in projects:
                try:
                    service.create_risk_snapshot(project.id)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"创建项目 {project.id} 风险快照失败: {e}")
                    error_count += 1

            logger.info(
                f"[{datetime.now()}] 风险快照创建完成: "
                f"成功 {success_count} 个, 失败 {error_count} 个"
            )

            return {
                "total": len(projects),
                "success": success_count,
                "errors": error_count,
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 风险快照创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def check_high_risk_projects() -> Dict[str, Any]:
    """
    检查高风险项目并生成预警

    每4小时执行一次，检查风险等级为HIGH或CRITICAL的项目，
    并通过预警系统通知相关人员。

    Returns:
        执行结果统计
    """
    try:
        with get_db_session() as db:
            from app.models.alert import AlertRecord
            from app.models.enums import AlertLevelEnum, AlertStatusEnum
            from app.models.project import Project
            from app.models.project.risk_history import ProjectRiskHistory

            today = datetime.now().date()

            # 获取最近24小时内升级为高风险的项目
            high_risk_upgrades = (
                db.query(ProjectRiskHistory)
                .filter(
                    ProjectRiskHistory.new_risk_level.in_(["HIGH", "CRITICAL"]),
                    ProjectRiskHistory.triggered_at >= datetime.now().replace(hour=0, minute=0, second=0),
                )
                .all()
            )

            alert_count = 0
            for history in high_risk_upgrades:
                # 检查是否已有预警
                existing_query = db.query(AlertRecord).filter(
                    AlertRecord.target_type == "PROJECT",
                    AlertRecord.target_id == history.project_id,
                    AlertRecord.status == "PENDING",
                )
                existing_query = apply_keyword_filter(
                    existing_query,
                    AlertRecord,
                    "风险升级",
                    "alert_title",
                    use_ilike=False,
                )
                existing = existing_query.first()

                if not existing:
                    project = db.query(Project).filter(Project.id == history.project_id).first()
                    if not project:
                        continue

                    alert_no = f"PR{today.strftime('%Y%m%d')}{str(alert_count + 1).zfill(4)}"

                    alert = AlertRecord(
                        alert_no=alert_no,
                        target_type="PROJECT",
                        target_id=project.id,
                        target_no=project.project_code,
                        target_name=project.project_name,
                        project_id=project.id,
                        alert_level=(
                            AlertLevelEnum.CRITICAL.value
                            if history.new_risk_level == "CRITICAL"
                            else AlertLevelEnum.WARNING.value
                        ),
                        alert_title=f"项目风险升级：{project.project_name}",
                        alert_content=(
                            f"项目 {project.project_code} 风险等级从 {history.old_risk_level} "
                            f"升级为 {history.new_risk_level}，请及时关注并采取措施"
                        ),
                        status=AlertStatusEnum.PENDING.value,
                        triggered_at=datetime.now(),
                    )
                    db.add(alert)
                    alert_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 高风险项目预警检查完成: "
                f"检查 {len(high_risk_upgrades)} 个风险升级, "
                f"生成 {alert_count} 个预警"
            )

            return {
                "checked": len(high_risk_upgrades),
                "alerts_created": alert_count,
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 高风险项目预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
