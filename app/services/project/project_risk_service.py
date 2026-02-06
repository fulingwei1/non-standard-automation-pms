# -*- coding: utf-8 -*-
"""
项目风险服务 - 自动风险等级计算与升级

功能：
1. 基于项目数据自动计算风险等级
2. 检测风险升级并记录历史
3. 触发风险通知
4. 提供风险趋势分析数据

创建日期：2026-01-25
更新日期：2026-01-30 - 重构为同步版本
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.pmo import PmoProjectRisk
from app.models.project import Project, ProjectMilestone
from app.models.project.risk_history import ProjectRiskHistory, ProjectRiskSnapshot

logger = logging.getLogger(__name__)


class ProjectRiskService:
    """项目风险服务类

    提供项目风险的自动评估、升级检测和历史记录功能。
    """

    # 风险等级顺序（用于判断升级/降级）
    RISK_LEVEL_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def __init__(self, db: Session):
        self.db = db

    def calculate_project_risk(self, project_id: int) -> Dict[str, Any]:
        """
        计算项目风险等级

        综合以下因素计算风险：
        1. 逾期里程碑数量和比例
        2. 未关闭的PMO风险数量和级别
        3. 进度偏差（如果可用）

        Args:
            project_id: 项目ID

        Returns:
            包含风险等级和详细因子的字典

        Raises:
            ValueError: 如果项目不存在
        """
        # 1. 查询项目
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        today = date.today()

        # 2. 计算里程碑风险因子
        milestone_factors = self._calculate_milestone_factors(project_id, today)

        # 3. 计算PMO风险因子
        pmo_risk_factors = self._calculate_pmo_risk_factors(project_id)

        # 4. 计算进度风险因子
        progress_factors = self._calculate_progress_factors(project)

        # 5. 合并所有因子
        risk_factors = {
            **milestone_factors,
            **pmo_risk_factors,
            **progress_factors,
            "calculated_at": datetime.now().isoformat(),
        }

        # 6. 计算风险等级
        new_risk_level = self._calculate_risk_level(risk_factors)

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "risk_level": new_risk_level,
            "risk_factors": risk_factors,
        }

    def auto_upgrade_risk_level(
        self,
        project_id: int,
        triggered_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        自动升级项目风险等级

        计算风险等级，如果发生变化则记录历史并触发通知。

        Args:
            project_id: 项目ID
            triggered_by: 触发者标识

        Returns:
            包含旧/新风险等级和因子的字典
        """
        # 计算当前风险
        result = self.calculate_project_risk(project_id)

        # 获取之前的风险等级
        last_history = (
            self.db.query(ProjectRiskHistory)
            .filter(ProjectRiskHistory.project_id == project_id)
            .order_by(ProjectRiskHistory.triggered_at.desc())
            .first()
        )

        old_risk_level = last_history.new_risk_level if last_history else "LOW"
        new_risk_level = result["risk_level"]

        # 记录历史
        history = ProjectRiskHistory(
            project_id=project_id,
            old_risk_level=old_risk_level,
            new_risk_level=new_risk_level,
            risk_factors=result["risk_factors"],
            triggered_by=triggered_by,
            triggered_at=datetime.now(),
        )
        self.db.add(history)

        # 检测是否升级
        is_upgrade = self._is_risk_upgrade(old_risk_level, new_risk_level)
        if is_upgrade:
            logger.warning(
                f"项目 {result['project_code']} 风险等级升级: {old_risk_level} -> {new_risk_level}"
            )
            # 获取项目名称用于通知
            project = self.db.query(Project).filter(Project.id == project_id).first()
            project_name = project.project_name if project else result["project_code"]

            # 触发通知服务
            self._send_risk_upgrade_notification(
                project_id=project_id,
                project_code=result["project_code"],
                project_name=project_name,
                old_level=old_risk_level,
                new_level=new_risk_level,
                risk_factors=result["risk_factors"],
            )

        self.db.commit()

        return {
            "project_id": project_id,
            "project_code": result["project_code"],
            "old_risk_level": old_risk_level,
            "new_risk_level": new_risk_level,
            "is_upgrade": is_upgrade,
            "risk_factors": result["risk_factors"],
        }

    def batch_calculate_risks(
        self,
        project_ids: Optional[List[int]] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        批量计算项目风险

        Args:
            project_ids: 项目ID列表，为空则处理所有项目
            active_only: 是否只处理激活项目

        Returns:
            风险计算结果列表
        """
        query = self.db.query(Project)

        if project_ids:
            query = query.filter(Project.id.in_(project_ids))
        if active_only:
            query = query.filter(Project.is_active == True)

        projects = query.all()
        results = []

        for project in projects:
            try:
                result = self.auto_upgrade_risk_level(project.id)
                results.append(result)
            except Exception as e:
                logger.error(f"计算项目 {project.id} 风险失败: {e}")
                results.append({
                    "project_id": project.id,
                    "project_code": project.project_code,
                    "error": str(e),
                })

        return results

    def create_risk_snapshot(self, project_id: int) -> ProjectRiskSnapshot:
        """
        创建项目风险快照

        用于历史趋势分析。

        Args:
            project_id: 项目ID

        Returns:
            创建的快照对象
        """
        result = self.calculate_project_risk(project_id)

        snapshot = ProjectRiskSnapshot(
            project_id=project_id,
            snapshot_date=datetime.now(),
            risk_level=result["risk_level"],
            overdue_milestones_count=result["risk_factors"].get("overdue_milestones_count", 0),
            total_milestones_count=result["risk_factors"].get("total_milestones_count", 0),
            overdue_tasks_count=result["risk_factors"].get("overdue_tasks_count", 0),
            open_risks_count=result["risk_factors"].get("open_risks_count", 0),
            high_risks_count=result["risk_factors"].get("high_risks_count", 0),
            risk_factors=result["risk_factors"],
        )

        self.db.add(snapshot)
        self.db.commit()

        return snapshot

    def get_risk_history(
        self,
        project_id: int,
        limit: int = 50,
    ) -> List[ProjectRiskHistory]:
        """
        获取项目风险历史

        Args:
            project_id: 项目ID
            limit: 返回记录数限制

        Returns:
            风险历史记录列表
        """
        return (
            self.db.query(ProjectRiskHistory)
            .filter(ProjectRiskHistory.project_id == project_id)
            .order_by(ProjectRiskHistory.triggered_at.desc())
            .limit(limit)
            .all()
        )

    def get_risk_trend(
        self,
        project_id: int,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        获取项目风险趋势

        Args:
            project_id: 项目ID
            days: 查询天数

        Returns:
            风险趋势数据列表
        """
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        snapshots = (
            self.db.query(ProjectRiskSnapshot)
            .filter(
                ProjectRiskSnapshot.project_id == project_id,
                ProjectRiskSnapshot.snapshot_date >= start_date,
            )
            .order_by(ProjectRiskSnapshot.snapshot_date)
            .all()
        )

        return [
            {
                "date": s.snapshot_date.isoformat(),
                "risk_level": s.risk_level,
                "overdue_milestones": s.overdue_milestones_count,
                "open_risks": s.open_risks_count,
                "high_risks": s.high_risks_count,
            }
            for s in snapshots
        ]

    # ==================== 私有方法 ====================

    def _calculate_milestone_factors(
        self,
        project_id: int,
        today: date,
    ) -> Dict[str, Any]:
        """计算里程碑相关风险因子"""
        # 查询总里程碑数
        total_count = (
            self.db.query(func.count(ProjectMilestone.id))
            .filter(ProjectMilestone.project_id == project_id)
            .scalar() or 0
        )

        # 查询逾期里程碑
        overdue_milestones = (
            self.db.query(ProjectMilestone)
            .filter(
                and_(
                    ProjectMilestone.project_id == project_id,
                    ProjectMilestone.planned_date < today,
                    ProjectMilestone.status.in_(["NOT_STARTED", "IN_PROGRESS", "PENDING"]),
                )
            )
            .all()
        )

        overdue_count = len(overdue_milestones)
        overdue_ratio = overdue_count / total_count if total_count > 0 else 0

        # 计算最大逾期天数
        max_overdue_days = 0
        for m in overdue_milestones:
            if m.planned_date:
                days = (today - m.planned_date).days
                if days > max_overdue_days:
                    max_overdue_days = days

        return {
            "total_milestones_count": total_count,
            "overdue_milestones_count": overdue_count,
            "overdue_milestone_ratio": round(overdue_ratio, 2),
            "max_overdue_days": max_overdue_days,
        }

    def _calculate_pmo_risk_factors(self, project_id: int) -> Dict[str, Any]:
        """计算PMO风险相关因子"""
        # 查询未关闭的风险
        open_risks = (
            self.db.query(PmoProjectRisk)
            .filter(
                PmoProjectRisk.project_id == project_id,
                PmoProjectRisk.status.notin_(["CLOSED", "RESOLVED"]),
            )
            .all()
        )

        open_count = len(open_risks)
        high_count = sum(1 for r in open_risks if r.risk_level in ("HIGH", "CRITICAL"))
        critical_count = sum(1 for r in open_risks if r.risk_level == "CRITICAL")

        return {
            "open_risks_count": open_count,
            "high_risks_count": high_count,
            "critical_risks_count": critical_count,
        }

    def _calculate_progress_factors(self, project: Project) -> Dict[str, Any]:
        """计算进度相关风险因子"""
        factors = {
            "progress_pct": float(project.progress_pct or 0),
            "schedule_variance": 0,
        }

        # 计算进度偏差（如果有计划结束日期）
        if project.planned_end_date:
            today = date.today()
            total_duration = (project.planned_end_date - (project.planned_start_date or project.contract_date or today)).days
            if total_duration > 0:
                elapsed_days = (today - (project.actual_start_date or project.planned_start_date or today)).days
                expected_progress = min(100, (elapsed_days / total_duration) * 100)
                actual_progress = float(project.progress_pct or 0)
                factors["schedule_variance"] = round(actual_progress - expected_progress, 2)

        return factors

    def _calculate_risk_level(self, factors: Dict[str, Any]) -> str:
        """
        根据风险因子计算风险等级

        规则：
        - CRITICAL: 逾期里程碑>=50% 或 有CRITICAL级别风险
        - HIGH: 逾期里程碑>=30% 或 有HIGH级别风险>=2 或 进度偏差<-20%
        - MEDIUM: 逾期里程碑>=10% 或 有HIGH级别风险>=1 或 进度偏差<-10%
        - LOW: 其他情况
        """
        overdue_ratio = factors.get("overdue_milestone_ratio", 0)
        critical_risks = factors.get("critical_risks_count", 0)
        high_risks = factors.get("high_risks_count", 0)
        schedule_variance = factors.get("schedule_variance", 0)

        # CRITICAL
        if overdue_ratio >= 0.5 or critical_risks > 0:
            return "CRITICAL"

        # HIGH
        if overdue_ratio >= 0.3 or high_risks >= 2 or schedule_variance < -20:
            return "HIGH"

        # MEDIUM
        if overdue_ratio >= 0.1 or high_risks >= 1 or schedule_variance < -10:
            return "MEDIUM"

        return "LOW"

    def _is_risk_upgrade(self, old_level: str, new_level: str) -> bool:
        """判断风险等级是否升级"""
        old_order = self.RISK_LEVEL_ORDER.get(old_level, 0)
        new_order = self.RISK_LEVEL_ORDER.get(new_level, 0)
        return new_order > old_order

    def _send_risk_upgrade_notification(
        self,
        project_id: int,
        project_code: str,
        project_name: str,
        old_level: str,
        new_level: str,
        risk_factors: dict,
    ) -> None:
        """
        发送风险升级通知

        创建预警记录，通知将由定时任务批量发送。

        Args:
            project_id: 项目ID
            project_code: 项目编码
            project_name: 项目名称
            old_level: 原风险等级
            new_level: 新风险等级
            risk_factors: 风险因子
        """
        try:
            from app.models.alert import AlertRecord
            from app.models.enums import AlertLevelEnum, AlertStatusEnum
            from app.utils.scheduled_tasks.base import send_notification_for_alert

            # 确定预警级别
            if new_level == "CRITICAL":
                alert_level = AlertLevelEnum.CRITICAL.value
            elif new_level == "HIGH":
                alert_level = AlertLevelEnum.WARNING.value
            else:
                alert_level = AlertLevelEnum.INFO.value

            # 生成预警编号
            today = datetime.now()
            alert_no = f"RISK{today.strftime('%Y%m%d%H%M%S')}{project_id}"

            # 构建预警内容
            content_parts = [
                f"项目 {project_code} ({project_name}) 风险等级从 {old_level} 升级为 {new_level}。",
            ]

            # 添加风险因子摘要
            if risk_factors:
                if risk_factors.get("overdue_milestones_count", 0) > 0:
                    content_parts.append(
                        f"逾期里程碑: {risk_factors['overdue_milestones_count']}个"
                    )
                if risk_factors.get("high_risks_count", 0) > 0:
                    content_parts.append(
                        f"高风险项: {risk_factors['high_risks_count']}个"
                    )
                if risk_factors.get("schedule_variance", 0) < -10:
                    content_parts.append(
                        f"进度偏差: {risk_factors['schedule_variance']:.1f}%"
                    )

            content_parts.append("请及时关注并采取措施。")

            # 创建预警记录
            alert = AlertRecord(
                alert_no=alert_no,
                target_type="PROJECT",
                target_id=project_id,
                target_no=project_code,
                target_name=project_name,
                project_id=project_id,
                alert_level=alert_level,
                alert_title=f"项目风险升级: {project_name} ({old_level}→{new_level})",
                alert_content=" ".join(content_parts),
                status=AlertStatusEnum.PENDING.value,
                triggered_at=datetime.now(),
            )

            self.db.add(alert)
            self.db.flush()

            # 尝试即时发送通知（失败不影响预警记录）
            send_notification_for_alert(self.db, alert, logger)

            logger.info(
                f"风险升级预警已创建: {alert_no} - {project_code} ({old_level}→{new_level})"
            )

        except Exception as e:
            logger.error(f"创建风险升级预警失败: {e}")
            # 不抛出异常，避免影响主流程
