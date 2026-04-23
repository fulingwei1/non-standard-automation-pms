# -*- coding: utf-8 -*-
"""
跨部门协作评价服务 - 评价管理
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.engineer_performance import CollaborationRating, EngineerProfile


class RatingManager:
    """评价管理器"""

    def __init__(self, db, service=None):
        self.db = db
        self.service = service

    def create_rating_invitations(
        self,
        engineer_id: Optional[int] = None,
        period_id: Optional[int] = None,
        collaborator_ids: Optional[List[int]] = None,
        project_id: Optional[int] = None,
        assessment_period: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        创建评价邀请

        Args:
            engineer_id: 被评价工程师ID
            period_id: 考核周期ID
            collaborator_ids: 合作人员ID列表（如果为None则自动抽取）

        Returns:
            评价邀请列表
        """
        if engineer_id is None or period_id is None:
            return []

        try:
            # 使用选择器自动抽取合作人员
            if collaborator_ids is None:
                selector = getattr(self.service, "selector", None)
                if selector is None:
                    return []
                collaborator_ids = selector.auto_select_collaborators(engineer_id, period_id)

            invitations = []
            for collaborator_id in collaborator_ids:
                existing = (
                    self.db.query(CollaborationRating)
                    .filter(
                        CollaborationRating.period_id == period_id,
                        CollaborationRating.rater_id == collaborator_id,
                        CollaborationRating.ratee_id == engineer_id,
                    )
                    .first()
                )

                if existing:
                    continue

                rating = CollaborationRating(
                    period_id=period_id,
                    rater_id=collaborator_id,
                    ratee_id=engineer_id,
                )

                rater_profile = (
                    self.db.query(EngineerProfile)
                    .filter(EngineerProfile.user_id == collaborator_id)
                    .first()
                )
                ratee_profile = (
                    self.db.query(EngineerProfile)
                    .filter(EngineerProfile.user_id == engineer_id)
                    .first()
                )

                if rater_profile:
                    rating.rater_job_type = rater_profile.job_type
                if ratee_profile:
                    rating.ratee_job_type = ratee_profile.job_type

                self.db.add(rating)
                invitations.append(
                    {"rater_id": collaborator_id, "ratee_id": engineer_id, "rating_id": None}
                )

            self.db.commit()

            for inv in invitations:
                rating = (
                    self.db.query(CollaborationRating)
                    .filter(
                        CollaborationRating.period_id == period_id,
                        CollaborationRating.rater_id == inv["rater_id"],
                        CollaborationRating.ratee_id == inv["ratee_id"],
                    )
                    .first()
                )
                if rating:
                    inv["rating_id"] = rating.id

            return invitations
        except Exception:
            return []

    def submit_rating(
        self,
        rating_id: int,
        rater_id: Optional[int] = None,
        communication_score: int = 0,
        response_score: Optional[int] = None,
        delivery_score: Optional[int] = None,
        interface_score: Optional[int] = None,
        comment: Optional[str] = None,
        project_id: Optional[int] = None,
        response_speed_score: Optional[int] = None,
        delivery_quality_score: Optional[int] = None,
        interface_compliance_score: Optional[int] = None,
    ) -> Optional[CollaborationRating]:
        """
        提交评价

        Args:
            rating_id: 评价记录ID
            rater_id: 评价人ID（用于验证）
            communication_score: 沟通配合得分（1-5）
            response_score: 响应速度得分（1-5）
            delivery_score: 交付质量得分（1-5）
            interface_score: 接口规范得分（1-5）
            comment: 评价备注
            project_id: 关联项目ID

        Returns:
            更新后的评价记录
        """
        response_score = response_score if response_score is not None else response_speed_score or 0
        delivery_score = (
            delivery_score if delivery_score is not None else delivery_quality_score or 0
        )
        interface_score = (
            interface_score
            if interface_score is not None
            else interface_compliance_score or 0
        )

        try:
            query = self.db.query(CollaborationRating).filter(CollaborationRating.id == rating_id)
            if rater_id is not None:
                query = query.filter(CollaborationRating.rater_id == rater_id)
            rating = query.first()
        except Exception:
            return False

        if not rating:
            return False

        # 验证分数范围
        scores = [communication_score, response_score, delivery_score, interface_score]
        if not all(1 <= s <= 5 for s in scores):
            raise ValueError("评分必须在1-5之间")

        # 更新评分
        rating.communication_score = communication_score
        rating.response_score = response_score
        rating.delivery_score = delivery_score
        rating.interface_score = interface_score
        rating.comment = comment
        rating.project_id = project_id

        # 计算总分（转换为百分制）
        total_score = (
            (
                communication_score * 25
                + response_score * 25
                + delivery_score * 25
                + interface_score * 25
            )
            / 5
            * 20
        )  # 转换为百分制（5分制转100分制）

        rating.total_score = Decimal(str(round(total_score, 2)))

        try:
            self.db.commit()
            self.db.refresh(rating)
        except Exception:
            return rating

        return rating

    def get_pending_ratings(
        self, rater_id: Optional[int] = None, period_id: Optional[int] = None, user_id: Optional[int] = None
    ) -> List[CollaborationRating]:
        """
        获取待评价列表

        Args:
            rater_id: 评价人ID
            period_id: 考核周期ID（可选）

        Returns:
            待评价记录列表
        """
        rater_id = rater_id if rater_id is not None else user_id
        if rater_id is None:
            return []

        try:
            query = self.db.query(CollaborationRating).filter(
                CollaborationRating.rater_id == rater_id,
                CollaborationRating.total_score.is_(None),
            )

            if period_id:
                query = query.filter(CollaborationRating.period_id == period_id)

            return query.all()
        except Exception:
            return []

    def auto_complete_missing_ratings(
        self,
        period_id: Optional[int] = None,
        default_score: Decimal = Decimal("75.0"),
        assessment_period: Optional[str] = None,
    ) -> int:
        """
        自动完成缺失的评价（使用默认值）

        Args:
            period_id: 考核周期ID
            default_score: 默认得分（默认75分）

        Returns:
            完成的数量
        """
        if period_id is None:
            return 0

        if not isinstance(default_score, Decimal):
            default_score = Decimal(str(default_score))

        try:
            pending_ratings = (
                self.db.query(CollaborationRating)
                .filter(
                    CollaborationRating.period_id == period_id,
                    CollaborationRating.total_score.is_(None),
                )
                .all()
            )
        except Exception:
            return 0

        count = 0
        for rating in pending_ratings:
            # 使用默认值填充
            rating.communication_score = 3  # 中等评分
            rating.response_score = 3
            rating.delivery_score = 3
            rating.interface_score = 3
            rating.total_score = default_score
            count += 1

        try:
            self.db.commit()
        except Exception:
            return count

        return count
