# -*- coding: utf-8 -*-
"""
坑点预警服务
新项目创建时自动推送类似项目的历史坑点、同类产品常见风险、同客户特殊要求
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.knowledge_base import (
    KnowledgeAlert,
    KnowledgeEntry,
    KnowledgeStatusEnum,
    KnowledgeTypeEnum,
)
from app.models.project.core import Project


class PitfallAlertService:
    """坑点预警服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_alerts(
        self, target_project_id: int, *, max_alerts: int = 20
    ) -> Dict[str, Any]:
        """
        为新项目生成坑点预警

        匹配维度（按优先级）：
        1. 同客户的历史坑点 — 匹配分 0.95
        2. 同产品类别的常见风险 — 匹配分 0.85
        3. 同项目类型的经验教训 — 匹配分 0.75
        4. 同行业的通用知识 — 匹配分 0.60
        """
        project = self.db.query(Project).filter(Project.id == target_project_id).first()
        if not project:
            raise ValueError(f"项目 {target_project_id} 不存在")

        # 清理旧预警（避免重复生成）
        self.db.query(KnowledgeAlert).filter(
            KnowledgeAlert.target_project_id == target_project_id
        ).delete(synchronize_session=False)

        # 只匹配已发布的知识
        base_q = self.db.query(KnowledgeEntry).filter(
            KnowledgeEntry.status == KnowledgeStatusEnum.PUBLISHED,
            # 排除来自同一项目的知识
            or_(
                KnowledgeEntry.source_project_id != project.id,
                KnowledgeEntry.source_project_id.is_(None),
            ),
        )

        candidates: List[Dict[str, Any]] = []

        # 1. 同客户
        if project.customer_id:
            rows = (
                base_q.filter(KnowledgeEntry.customer_id == project.customer_id)
                .limit(max_alerts)
                .all()
            )
            for r in rows:
                candidates.append(
                    {"entry": r, "score": 0.95, "reason": f"同客户（customer_id={project.customer_id}）历史经验"}
                )

        # 2. 同产品类别
        if project.product_category:
            rows = (
                base_q.filter(KnowledgeEntry.product_category == project.product_category)
                .limit(max_alerts)
                .all()
            )
            for r in rows:
                if not any(c["entry"].id == r.id for c in candidates):
                    candidates.append(
                        {"entry": r, "score": 0.85, "reason": f"同产品类别（{project.product_category}）"}
                    )

        # 3. 同项目类型
        if project.project_type:
            rows = (
                base_q.filter(KnowledgeEntry.project_type == project.project_type)
                .limit(max_alerts)
                .all()
            )
            for r in rows:
                if not any(c["entry"].id == r.id for c in candidates):
                    candidates.append(
                        {"entry": r, "score": 0.75, "reason": f"同项目类型（{project.project_type}）"}
                    )

        # 4. 同行业
        if project.industry:
            rows = (
                base_q.filter(KnowledgeEntry.industry == project.industry)
                .limit(max_alerts)
                .all()
            )
            for r in rows:
                if not any(c["entry"].id == r.id for c in candidates):
                    candidates.append(
                        {"entry": r, "score": 0.60, "reason": f"同行业（{project.industry}）"}
                    )

        # 按匹配分降序，取 top N
        candidates.sort(key=lambda c: c["score"], reverse=True)
        candidates = candidates[:max_alerts]

        # 写入预警记录
        alerts: List[KnowledgeAlert] = []
        for c in candidates:
            alert = KnowledgeAlert(
                target_project_id=target_project_id,
                knowledge_entry_id=c["entry"].id,
                match_reason=c["reason"],
                match_score=c["score"],
            )
            alerts.append(alert)

        self.db.add_all(alerts)
        self.db.flush()

        return {
            "target_project_id": target_project_id,
            "alerts_generated": len(alerts),
            "alerts": alerts,
        }

    def get_project_alerts(
        self,
        project_id: int,
        *,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取项目的预警列表"""
        q = (
            self.db.query(KnowledgeAlert)
            .filter(KnowledgeAlert.target_project_id == project_id)
        )
        if unread_only:
            q = q.filter(KnowledgeAlert.is_read.is_(False))

        total = q.count()
        alerts = (
            q.order_by(KnowledgeAlert.match_score.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {"total": total, "items": alerts}

    def mark_read(self, alert_id: int) -> KnowledgeAlert:
        """标记预警已读"""
        alert = self.db.query(KnowledgeAlert).filter(KnowledgeAlert.id == alert_id).first()
        if not alert:
            raise ValueError(f"预警 {alert_id} 不存在")
        alert.is_read = True
        self.db.flush()
        return alert

    def submit_feedback(
        self, alert_id: int, *, is_adopted: bool, feedback: Optional[str] = None
    ) -> KnowledgeAlert:
        """提交预警反馈"""
        alert = self.db.query(KnowledgeAlert).filter(KnowledgeAlert.id == alert_id).first()
        if not alert:
            raise ValueError(f"预警 {alert_id} 不存在")
        alert.is_adopted = is_adopted
        alert.feedback = feedback
        alert.is_read = True

        # 如果采纳，增加引用计数
        if is_adopted:
            entry = (
                self.db.query(KnowledgeEntry)
                .filter(KnowledgeEntry.id == alert.knowledge_entry_id)
                .first()
            )
            if entry:
                entry.cite_count = (entry.cite_count or 0) + 1

        self.db.flush()
        return alert
