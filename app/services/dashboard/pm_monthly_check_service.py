# -*- coding: utf-8 -*-
"""
PM 月度自检服务（对应手册 Sheet8）

实时聚合，不入库。返回：
1. 在管项目利润健康度表（batch_margin_analysis）
2. 8项关键动作自检（4项系统自动判定 + 4项靠PM手填）

每项动作 status:
  - auto_passed: 系统判定通过
  - auto_failed: 系统判定不通过（有风险，需关注）
  - manual: 系统无法判定，PM 自填
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.change_request import ChangeRequest
from app.models.project import Project

logger = logging.getLogger(__name__)


class PmMonthlyCheckService:
    """PM 月度自检"""

    def __init__(self, db: Session):
        self.db = db
        self._today = date.today()

    def get_check(
        self,
        pm_id: Optional[int] = None,
        target_margin: float = 25.0,
    ) -> Dict[str, Any]:
        """
        生成 PM 月度自检表。

        Args:
            pm_id: 指定 PM（None 则所有 PM 的项目汇总，按 pm_id 分组）
            target_margin: 无等级项目的默认目标毛利率
        """
        from app.services.profit_analysis_service import ProfitAnalysisService

        # 1. 在管项目利润健康度表
        analyses = ProfitAnalysisService(self.db).batch_margin_analysis()
        if pm_id:
            analyses = [a for a in analyses if self._is_pm_project(a["project_id"], pm_id)]

        health_table = [
            {
                "project_id": a.get("project_id"),
                "project_code": a.get("project_code"),
                "project_name": a.get("project_name"),
                "project_level": a.get("project_level"),
                "contract_amount": a.get("contract_amount"),
                "current_margin_rate": a.get("current_margin_rate"),
                "target_margin_rate": a.get("target_margin_rate"),
                "margin_gap": a.get("margin_gap"),
                "health": a.get("health"),
                "risk_point": self._project_risk_point(a),
            }
            for a in analyses
        ]

        # 按健康度排序：critical 在前
        health_order = {"critical": 0, "warning": 1, "healthy": 2}
        health_table.sort(
            key=lambda x: health_order.get(x.get("health", "healthy"), 3)
        )

        # 2. 8项关键动作自检
        project_ids = [a["project_id"] for a in analyses]
        actions = self._check_actions(project_ids, pm_id)

        # 3. 汇总
        summary = {
            "total_projects": len(health_table),
            "healthy": sum(1 for h in health_table if h["health"] == "healthy"),
            "warning": sum(1 for h in health_table if h["health"] == "warning"),
            "critical": sum(1 for h in health_table if h["health"] == "critical"),
            "auto_failed_actions": sum(1 for a in actions if a["status"] == "auto_failed"),
        }

        return {
            "period": {
                "year": self._today.year,
                "month": self._today.month,
            },
            "pm_id": pm_id,
            "summary": summary,
            "health_table": health_table,
            "actions": actions,
            "generated_at": self._today.isoformat(),
        }

    # ================================================================
    # 项目风险点摘要
    # ================================================================

    def _project_risk_point(self, analysis: Dict) -> str:
        """从毛利率分析提取一句话风险点。"""
        health = analysis.get("health", "healthy")
        gap = analysis.get("margin_gap", 0)
        if health == "critical":
            return f"毛利率 {analysis.get('current_margin_rate')}% 严重低于目标（gap {gap}%）"
        elif health == "warning":
            return f"毛利率 {analysis.get('current_margin_rate')}% 低于目标（gap {gap}%）"
        return "正常"

    # ================================================================
    # 8项关键动作自检
    # ================================================================

    def _check_actions(
        self, project_ids: List[int], pm_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """8项动作：4项自动判定 + 4项PM手填。"""
        return [
            self._action_new_project_budget(),
            self._action_design_review_participation(project_ids),
            self._action_weekly_tracking_update(),
            self._action_unregistered_changes(project_ids),
            self._action_overbudget_projects(),
            self._action_delayed_projects(project_ids),
            self._action_completed_reviews(project_ids),
            self._action_lessons_to_capture(),
        ]

    # --- 动作1: 新项目48h内立项预算（无法自动判，靠 PM 自填）---
    def _action_new_project_budget(self) -> Dict:
        return {
            "id": 1,
            "name": "所有新项目是否在48h内完成立项预算表？",
            "status": "manual",
            "detail": "系统无法自动判定（无立项预算填写时间记录），请PM自查",
        }

    # --- 动作2: 参与所有设计评审（部分可判：查项目有无评审记录）---
    def _action_design_review_participation(
        self, project_ids: List[int]
    ) -> Dict:
        if not project_ids:
            return {
                "id": 2,
                "name": "是否参与了所有在管项目的设计评审？",
                "status": "manual",
                "detail": "无在管项目",
            }
        from app.models.technical_review import TechnicalReview

        # 查有评审记录的项目数
        reviewed_count = (
            self.db.query(TechnicalReview.project_id)
            .filter(TechnicalReview.project_id.in_(project_ids))
            .distinct()
            .count()
        )
        unreviewed = len(project_ids) - reviewed_count
        if unreviewed == 0:
            return {
                "id": 2,
                "name": "是否参与了所有在管项目的设计评审？",
                "status": "auto_passed",
                "detail": f"所有 {len(project_ids)} 个在管项目都有评审记录",
            }
        return {
            "id": 2,
            "name": "是否参与了所有在管项目的设计评审？",
            "status": "auto_failed",
            "detail": f"{unreviewed} 个在管项目无评审记录（共 {len(project_ids)} 个）",
        }

    # --- 动作3: 每周更新执行跟踪（无法自动判）---
    def _action_weekly_tracking_update(self) -> Dict:
        return {
            "id": 3,
            "name": "是否每周更新了项目执行跟踪表？",
            "status": "manual",
            "detail": "请PM自查工时/成本记录的最后更新时间",
        }

    # --- 动作4: 变更未登记/客户变更未追费（能判：查未关闭变更）---
    def _action_unregistered_changes(
        self, project_ids: List[int]
    ) -> Dict:
        if not project_ids:
            return {
                "id": 4,
                "name": "是否有变更未登记？是否有客户变更未追费？",
                "status": "auto_passed",
                "detail": "无在管项目",
            }
        # 未关闭的变更（PENDING/APPROVED 状态）
        open_changes = (
            self.db.query(ChangeRequest)
            .filter(
                ChangeRequest.project_id.in_(project_ids),
                ChangeRequest.status.in_(["PENDING", "APPROVED", "REVIEW"]),
            )
            .count()
        )
        if open_changes == 0:
            return {
                "id": 4,
                "name": "是否有变更未登记？是否有客户变更未追费？",
                "status": "auto_passed",
                "detail": "无未关闭的变更",
            }
        return {
            "id": 4,
            "name": "是否有变更未登记？是否有客户变更未追费？",
            "status": "auto_failed",
            "detail": f"{open_changes} 个变更未关闭，请确认是否已追费",
        }

    # --- 动作5: 超预算项目已上报（能判：health=critical）---
    def _action_overbudget_projects(self) -> Dict:
        from app.services.profit_analysis_service import ProfitAnalysisService

        analyses = ProfitAnalysisService(self.db).batch_margin_analysis()
        critical = [a for a in analyses if a.get("health") == "critical"]
        if not critical:
            return {
                "id": 5,
                "name": "是否有超预算项目？是否已上报并制定应对方案？",
                "status": "auto_passed",
                "detail": "无严重超预算（critical）项目",
            }
        codes = ", ".join(a["project_code"] for a in critical[:5])
        return {
            "id": 5,
            "name": "是否有超预算项目？是否已上报并制定应对方案？",
            "status": "auto_failed",
            "detail": f"{len(critical)} 个项目毛利 critical：{codes}",
        }

    # --- 动作6: 延期项目影响回款（能判：在途超期）---
    def _action_delayed_projects(
        self, project_ids: List[int]
    ) -> Dict:
        if not project_ids:
            return {
                "id": 6,
                "name": "是否有延期项目？是否影响回款？",
                "status": "auto_passed",
                "detail": "无在管项目",
            }
        delayed = (
            self.db.query(Project)
            .filter(
                Project.id.in_(project_ids),
                Project.stage != "S9",
                Project.planned_end_date.isnot(None),
                Project.planned_end_date < self._today,
            )
            .count()
        )
        if delayed == 0:
            return {
                "id": 6,
                "name": "是否有延期项目？是否影响回款？",
                "status": "auto_passed",
                "detail": "无延期项目",
            }
        return {
            "id": 6,
            "name": "是否有延期项目？是否影响回款？",
            "status": "auto_failed",
            "detail": f"{delayed} 个在管项目已过计划交付日",
        }

    # --- 动作7: 结项项目完成复盘（能判：S9项目有无ProjectReview）---
    def _action_completed_reviews(
        self, project_ids: List[int]
    ) -> Dict:
        if not project_ids:
            return {
                "id": 7,
                "name": "是否完成了结项项目的复盘表？",
                "status": "auto_passed",
                "detail": "无在管项目",
            }
        from app.models.project_review import ProjectReview

        # 本月结项的项目（S9）
        completed = (
            self.db.query(Project)
            .filter(Project.id.in_(project_ids), Project.stage == "S9")
            .all()
        )
        if not completed:
            return {
                "id": 7,
                "name": "是否完成了结项项目的复盘表？",
                "status": "auto_passed",
                "detail": "本月无结项项目",
            }
        completed_ids = {p.id for p in completed}
        reviewed_ids = {
            r.project_id
            for r in self.db.query(ProjectReview)
            .filter(ProjectReview.project_id.in_(completed_ids))
            .all()
        }
        unreviewed = completed_ids - reviewed_ids
        if not unreviewed:
            return {
                "id": 7,
                "name": "是否完成了结项项目的复盘表？",
                "status": "auto_passed",
                "detail": f"所有 {len(completed)} 个结项项目都有复盘记录",
            }
        return {
            "id": 7,
            "name": "是否完成了结项项目的复盘表？",
            "status": "auto_failed",
            "detail": f"{len(unreviewed)} 个结项项目缺复盘记录",
        }

    # --- 动作8: 值得沉淀的模块/经验（无法自动判）---
    def _action_lessons_to_capture(self) -> Dict:
        return {
            "id": 8,
            "name": "本月是否有值得沉淀的模块/方案/经验？",
            "status": "manual",
            "detail": "请PM自查并录入知识库",
        }

    # ================================================================
    # 辅助：判断项目是否属于某 PM
    # ================================================================

    def _is_pm_project(self, project_id: int, pm_id: int) -> bool:
        p = self.db.query(Project).filter(Project.id == project_id).first()
        return p is not None and p.pm_id == pm_id
