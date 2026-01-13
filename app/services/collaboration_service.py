# -*- coding: utf-8 -*-
"""
跨部门协作评价服务
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models.engineer_performance import (
    EngineerProfile, CollaborationRating
)
from app.models.performance import PerformancePeriod
from app.models.user import User
from app.schemas.engineer_performance import CollaborationRatingCreate


class CollaborationService:
    """跨部门协作服务"""

    # 定义可互评的岗位关系
    VALID_RATING_PAIRS = [
        ('mechanical', 'test'),
        ('mechanical', 'electrical'),
        ('test', 'electrical'),
        ('test', 'mechanical'),
        ('electrical', 'mechanical'),
        ('electrical', 'test'),
    ]

    def __init__(self, db: Session):
        self.db = db

    def create_rating(
        self,
        data: CollaborationRatingCreate,
        rater_id: int
    ) -> CollaborationRating:
        """创建跨部门评价"""
        # 获取评价人档案
        rater_profile = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == rater_id
        ).first()

        # 获取被评价人档案
        ratee_profile = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == data.ratee_id
        ).first()

        if not rater_profile or not ratee_profile:
            raise ValueError("评价人或被评价人不是工程师")

        # 验证是否可以互评
        pair = (rater_profile.job_type, ratee_profile.job_type)
        if pair not in self.VALID_RATING_PAIRS:
            raise ValueError(f"相同岗位类型不能互评: {pair}")

        # 检查是否已评价
        existing = self.db.query(CollaborationRating).filter(
            CollaborationRating.period_id == data.period_id,
            CollaborationRating.rater_id == rater_id,
            CollaborationRating.ratee_id == data.ratee_id
        ).first()

        if existing:
            raise ValueError("本周期已对该工程师进行过评价")

        # 计算总分
        total_score = (
            data.communication_score + data.response_score +
            data.delivery_score + data.interface_score
        ) / 4 * 20  # 转换为百分制

        rating = CollaborationRating(
            period_id=data.period_id,
            rater_id=rater_id,
            ratee_id=data.ratee_id,
            rater_job_type=rater_profile.job_type,
            ratee_job_type=ratee_profile.job_type,
            communication_score=data.communication_score,
            response_score=data.response_score,
            delivery_score=data.delivery_score,
            interface_score=data.interface_score,
            total_score=Decimal(str(round(total_score, 2))),
            comment=data.comment,
            project_id=data.project_id
        )

        self.db.add(rating)
        self.db.commit()
        self.db.refresh(rating)
        return rating

    def get_rating(self, rating_id: int) -> Optional[CollaborationRating]:
        """获取单个评价"""
        return self.db.query(CollaborationRating).filter(
            CollaborationRating.id == rating_id
        ).first()

    def get_ratings_received(
        self,
        user_id: int,
        period_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[CollaborationRating], int]:
        """获取收到的评价"""
        query = self.db.query(CollaborationRating).filter(
            CollaborationRating.ratee_id == user_id
        )

        if period_id:
            query = query.filter(CollaborationRating.period_id == period_id)

        total = query.count()
        items = query.order_by(
            desc(CollaborationRating.created_at)
        ).offset(offset).limit(limit).all()

        return items, total

    def get_ratings_given(
        self,
        user_id: int,
        period_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[CollaborationRating], int]:
        """获取给出的评价"""
        query = self.db.query(CollaborationRating).filter(
            CollaborationRating.rater_id == user_id
        )

        if period_id:
            query = query.filter(CollaborationRating.period_id == period_id)

        total = query.count()
        items = query.order_by(
            desc(CollaborationRating.created_at)
        ).offset(offset).limit(limit).all()

        return items, total

    def get_collaboration_matrix(self, period_id: int) -> Dict[str, Any]:
        """获取协作评价矩阵"""
        ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.period_id == period_id
        ).all()

        # 构建矩阵：rater_job_type -> ratee_job_type -> avg_score
        matrix = {}
        counts = {}

        for rating in ratings:
            rater_type = rating.rater_job_type
            ratee_type = rating.ratee_job_type

            if rater_type not in matrix:
                matrix[rater_type] = {}
                counts[rater_type] = {}

            if ratee_type not in matrix[rater_type]:
                matrix[rater_type][ratee_type] = 0
                counts[rater_type][ratee_type] = 0

            matrix[rater_type][ratee_type] += float(rating.total_score or 0)
            counts[rater_type][ratee_type] += 1

        # 计算平均分
        for rater_type in matrix:
            for ratee_type in matrix[rater_type]:
                count = counts[rater_type][ratee_type]
                if count > 0:
                    matrix[rater_type][ratee_type] = round(
                        matrix[rater_type][ratee_type] / count, 2
                    )

        return {
            'period_id': period_id,
            'matrix': matrix,
            'details': [
                {
                    'rater_type': r.rater_job_type,
                    'ratee_type': r.ratee_job_type,
                    'avg_score': float(r.total_score or 0)
                }
                for r in ratings[:50]  # 限制详情数量
            ]
        }

    def get_pending_ratings(
        self,
        user_id: int,
        period_id: int
    ) -> List[Dict[str, Any]]:
        """获取待评价的工程师列表"""
        # 获取评价人档案
        rater_profile = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == user_id
        ).first()

        if not rater_profile:
            return []

        # 获取可评价的岗位类型
        valid_ratee_types = [
            pair[1] for pair in self.VALID_RATING_PAIRS
            if pair[0] == rater_profile.job_type
        ]

        # 获取已评价的用户
        rated_users = self.db.query(CollaborationRating.ratee_id).filter(
            CollaborationRating.period_id == period_id,
            CollaborationRating.rater_id == user_id
        ).all()
        rated_user_ids = [r[0] for r in rated_users]

        # 获取待评价的工程师
        pending = self.db.query(EngineerProfile, User).join(
            User, EngineerProfile.user_id == User.id
        ).filter(
            EngineerProfile.job_type.in_(valid_ratee_types),
            EngineerProfile.user_id.notin_(rated_user_ids) if rated_user_ids else True
        ).all()

        return [
            {
                'user_id': profile.user_id,
                'user_name': user.name,
                'job_type': profile.job_type,
                'job_level': profile.job_level,
                'department': user.department_name if hasattr(user, 'department_name') else None
            }
            for profile, user in pending
        ]

    def get_collaboration_stats(
        self,
        user_id: int,
        period_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取协作统计"""
        query = self.db.query(CollaborationRating).filter(
            CollaborationRating.ratee_id == user_id
        )

        if period_id:
            query = query.filter(CollaborationRating.period_id == period_id)

        ratings = query.all()

        if not ratings:
            return {
                'total_ratings': 0,
                'avg_score': 0,
                'by_dimension': {}
            }

        # 各维度平均分
        comm_scores = [r.communication_score for r in ratings if r.communication_score]
        resp_scores = [r.response_score for r in ratings if r.response_score]
        deliv_scores = [r.delivery_score for r in ratings if r.delivery_score]
        iface_scores = [r.interface_score for r in ratings if r.interface_score]

        return {
            'total_ratings': len(ratings),
            'avg_score': round(
                sum(float(r.total_score or 0) for r in ratings) / len(ratings), 2
            ),
            'by_dimension': {
                'communication': round(sum(comm_scores) / len(comm_scores), 2) if comm_scores else 0,
                'response': round(sum(resp_scores) / len(resp_scores), 2) if resp_scores else 0,
                'delivery': round(sum(deliv_scores) / len(deliv_scores), 2) if deliv_scores else 0,
                'interface': round(sum(iface_scores) / len(iface_scores), 2) if iface_scores else 0,
            },
            'by_rater_type': self._group_by_rater_type(ratings)
        }

    def _group_by_rater_type(
        self, ratings: List[CollaborationRating]
    ) -> Dict[str, Dict[str, Any]]:
        """按评价人岗位类型分组统计"""
        grouped = {}
        for rating in ratings:
            rater_type = rating.rater_job_type
            if rater_type not in grouped:
                grouped[rater_type] = {'count': 0, 'total_score': 0}
            grouped[rater_type]['count'] += 1
            grouped[rater_type]['total_score'] += float(rating.total_score or 0)

        for rater_type in grouped:
            count = grouped[rater_type]['count']
            grouped[rater_type]['avg_score'] = round(
                grouped[rater_type]['total_score'] / count, 2
            ) if count > 0 else 0
            del grouped[rater_type]['total_score']

        return grouped
