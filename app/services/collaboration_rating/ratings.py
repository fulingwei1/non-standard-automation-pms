# -*- coding: utf-8 -*-
"""
跨部门协作评价服务 - 评价管理
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.engineer_performance import CollaborationRating, EngineerProfile


class RatingManager:
    """评价管理器"""

    def __init__(self, db, service):
        self.db = db
        self.service = service

    def create_rating_invitations(
        self,
        engineer_id: int,
        period_id: int,
        collaborator_ids: Optional[List[int]] = None
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
        # 使用选择器自动抽取合作人员
        if collaborator_ids is None:
            selector = self.service.selector
            collaborator_ids = selector.auto_select_collaborators(
                engineer_id, period_id
            )

        invitations = []
        for collaborator_id in collaborator_ids:
            # 检查是否已存在评价记录
            existing = self.db.query(CollaborationRating).filter(
                CollaborationRating.period_id == period_id,
                CollaborationRating.rater_id == collaborator_id,
                CollaborationRating.ratee_id == engineer_id
            ).first()

            if existing:
                continue  # 已存在，跳过

            # 创建评价记录（初始状态，等待评价人填写）
            rating = CollaborationRating(
                period_id=period_id,
                rater_id=collaborator_id,
                ratee_id=engineer_id,
                # 评分字段暂时为空，等待评价人填写
            )

            # 获取岗位类型
            rater_profile = self.db.query(EngineerProfile).filter(
                EngineerProfile.user_id == collaborator_id
            ).first()
            ratee_profile = self.db.query(EngineerProfile).filter(
                EngineerProfile.user_id == engineer_id
            ).first()

            if rater_profile:
                rating.rater_job_type = rater_profile.job_type
            if ratee_profile:
                rating.ratee_job_type = ratee_profile.job_type

            self.db.add(rating)
            invitations.append({
                'rater_id': collaborator_id,
                'ratee_id': engineer_id,
                'rating_id': None  # 将在commit后更新
            })

        self.db.commit()

        # 更新rating_id
        for inv in invitations:
            rating = self.db.query(CollaborationRating).filter(
                CollaborationRating.period_id == period_id,
                CollaborationRating.rater_id == inv['rater_id'],
                CollaborationRating.ratee_id == inv['ratee_id']
            ).first()
            if rating:
                inv['rating_id'] = rating.id

        return invitations

    def submit_rating(
        self,
        rating_id: int,
        rater_id: int,
        communication_score: int,
        response_score: int,
        delivery_score: int,
        interface_score: int,
        comment: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> CollaborationRating:
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
        rating = self.db.query(CollaborationRating).filter(
            CollaborationRating.id == rating_id,
            CollaborationRating.rater_id == rater_id
        ).first()

        if not rating:
            raise ValueError("评价记录不存在或无权限")

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
            communication_score * 25 +
            response_score * 25 +
            delivery_score * 25 +
            interface_score * 25
        ) / 5 * 20  # 转换为百分制（5分制转100分制）

        rating.total_score = Decimal(str(round(total_score, 2)))

        self.db.commit()
        self.db.refresh(rating)

        return rating

    def get_pending_ratings(
        self,
        rater_id: int,
        period_id: Optional[int] = None
    ) -> List[CollaborationRating]:
        """
        获取待评价列表

        Args:
            rater_id: 评价人ID
            period_id: 考核周期ID（可选）

        Returns:
            待评价记录列表
        """
        query = self.db.query(CollaborationRating).filter(
            CollaborationRating.rater_id == rater_id,
            CollaborationRating.total_score.is_(None)  # 未完成评价
        )

        if period_id:
            query = query.filter(CollaborationRating.period_id == period_id)

        return query.all()

    def auto_complete_missing_ratings(
        self,
        period_id: int,
        default_score: Decimal = Decimal('75.0')
    ) -> int:
        """
        自动完成缺失的评价（使用默认值）

        Args:
            period_id: 考核周期ID
            default_score: 默认得分（默认75分）

        Returns:
            完成的数量
        """
        pending_ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.period_id == period_id,
            CollaborationRating.total_score.is_(None)
        ).all()

        count = 0
        for rating in pending_ratings:
            # 使用默认值填充
            rating.communication_score = 3  # 中等评分
            rating.response_score = 3
            rating.delivery_score = 3
            rating.interface_score = 3
            rating.total_score = default_score
            count += 1

        self.db.commit()

        return count
