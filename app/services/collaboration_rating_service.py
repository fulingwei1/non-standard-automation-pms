# -*- coding: utf-8 -*-
"""
跨部门协作评价服务
实现自动匿名抽取5个合作人员进行评价
"""

import secrets
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.models.engineer_performance import CollaborationRating, EngineerProfile
from app.models.organization import Department
from app.models.performance import PerformancePeriod
from app.models.project import Project, ProjectMember
from app.models.user import User


class CollaborationRatingService:
    """跨部门协作评价服务"""

    # 岗位类型映射（用于识别跨部门合作）
    JOB_TYPE_DEPARTMENT_MAP = {
        'mechanical': '机械部',
        'test': '测试部',
        'electrical': '电气部',
        'solution': '售前部'  # 方案工程师
    }

    def __init__(self, db: Session):
        self.db = db

    def auto_select_collaborators(
        self,
        engineer_id: int,
        period_id: int,
        target_count: int = 5
    ) -> List[int]:
        """
        自动匿名抽取合作人员

        Args:
            engineer_id: 被评价工程师ID
            period_id: 考核周期ID
            target_count: 目标抽取数量（默认5人）

        Returns:
            合作人员ID列表（已匿名处理，不包含被评价人）
        """
        # 获取考核周期
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        # 获取工程师档案
        profile = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == engineer_id
        ).first()

        if not profile:
            raise ValueError(f"工程师档案不存在: {engineer_id}")

        engineer_job_type = profile.job_type

        # 获取工程师在考核周期内参与的项目
        projects = self.db.query(Project).join(
            ProjectMember, Project.id == ProjectMember.project_id
        ).filter(
            ProjectMember.user_id == engineer_id,
            Project.created_at.between(period.start_date, period.end_date)
        ).all()

        if not projects:
            return []

        project_ids = [p.id for p in projects]

        # 获取所有合作人员（同项目但不同岗位）
        collaborators = self._get_collaborators_from_projects(
            engineer_id, engineer_job_type, project_ids
        )

        if not collaborators:
            return []

        # 去重
        unique_collaborators = list(set(collaborators))

        # 随机抽取（如果数量不足则全部抽取）
        if len(unique_collaborators) <= target_count:
            selected = unique_collaborators
        else:
            selected = secrets.SystemRandom().sample(unique_collaborators, target_count)

        return selected

    def _get_collaborators_from_projects(
        self,
        engineer_id: int,
        engineer_job_type: str,
        project_ids: List[int]
    ) -> List[int]:
        """
        从项目中获取合作人员

        根据岗位类型识别跨部门合作：
        - 机械工程师：抽取电气、测试工程师
        - 电气工程师：抽取机械、测试工程师
        - 测试工程师：抽取机械、电气工程师
        """
        # 获取所有项目成员
        all_members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id.in_(project_ids),
            ProjectMember.user_id != engineer_id
        ).all()

        # 获取这些成员的岗位类型
        user_ids = [m.user_id for m in all_members]
        profiles = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id.in_(user_ids)
        ).all()

        # 构建用户ID到岗位类型的映射
        user_job_type_map = {p.user_id: p.job_type for p in profiles}

        # 根据岗位类型筛选合作人员
        target_job_types = self._get_target_job_types(engineer_job_type)

        collaborators = []
        for member in all_members:
            job_type = user_job_type_map.get(member.user_id)
            if job_type and job_type in target_job_types:
                collaborators.append(member.user_id)

        return collaborators

    def _get_target_job_types(self, engineer_job_type: str) -> List[str]:
        """根据工程师岗位类型获取目标合作岗位类型"""
        if engineer_job_type == 'mechanical':
            return ['electrical', 'test']
        elif engineer_job_type == 'electrical':
            return ['mechanical', 'test']
        elif engineer_job_type == 'test':
            return ['mechanical', 'electrical']
        elif engineer_job_type == 'solution':
            # 方案工程师可以与所有岗位合作
            return ['mechanical', 'electrical', 'test']
        else:
            # 默认返回所有岗位
            return ['mechanical', 'electrical', 'test']

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
        if collaborator_ids is None:
            collaborator_ids = self.auto_select_collaborators(
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

    def get_average_collaboration_score(
        self,
        engineer_id: int,
        period_id: int
    ) -> Decimal:
        """
        获取平均协作得分

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID

        Returns:
            平均得分（如果无评价则返回默认值75）
        """
        ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.ratee_id == engineer_id,
            CollaborationRating.period_id == period_id,
            CollaborationRating.total_score.isnot(None)
        ).all()

        if not ratings:
            return Decimal('75.0')  # 默认值

        total = sum(r.total_score for r in ratings)
        avg = total / len(ratings)

        return Decimal(str(round(avg, 2)))

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

    def get_rating_statistics(
        self,
        period_id: int
    ) -> Dict[str, Any]:
        """
        获取评价统计信息

        Args:
            period_id: 考核周期ID

        Returns:
            评价统计信息
        """
        # 获取所有评价记录
        all_ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.period_id == period_id
        ).all()

        total_ratings = len(all_ratings)
        completed_ratings = sum(1 for r in all_ratings if r.total_score is not None)
        pending_ratings = total_ratings - completed_ratings

        completion_rate = (completed_ratings / total_ratings * 100) if total_ratings > 0 else 0.0

        # 计算平均得分
        completed = [r for r in all_ratings if r.total_score is not None]
        avg_score = sum(float(r.total_score) for r in completed) / len(completed) if completed else 0.0

        # 按岗位类型统计
        job_type_stats = {}
        for rating in completed:
            ratee_job_type = rating.ratee_job_type or 'unknown'
            if ratee_job_type not in job_type_stats:
                job_type_stats[ratee_job_type] = {
                    'count': 0,
                    'total_score': 0.0,
                    'avg_score': 0.0
                }
            job_type_stats[ratee_job_type]['count'] += 1
            job_type_stats[ratee_job_type]['total_score'] += float(rating.total_score)

        for job_type in job_type_stats:
            stats = job_type_stats[job_type]
            stats['avg_score'] = round(stats['total_score'] / stats['count'], 2) if stats['count'] > 0 else 0.0

        return {
            'period_id': period_id,
            'total_ratings': total_ratings,
            'completed_ratings': completed_ratings,
            'pending_ratings': pending_ratings,
            'completion_rate': round(completion_rate, 2),
            'average_score': round(avg_score, 2),
            'job_type_statistics': job_type_stats
        }

    def get_collaboration_trend(
        self,
        engineer_id: int,
        periods: int = 6
    ) -> Dict[str, Any]:
        """
        获取跨部门协作趋势

        Args:
            engineer_id: 工程师ID
            periods: 历史周期数

        Returns:
            协作趋势数据
        """
        # 获取最近的几个周期
        recent_periods = self.db.query(PerformancePeriod).order_by(
            desc(PerformancePeriod.start_date)
        ).limit(periods).all()

        trend_data = []
        for period in reversed(recent_periods):  # 从最早到最新
            avg_score = self.get_average_collaboration_score(engineer_id, period.id)
            ratings = self.db.query(CollaborationRating).filter(
                CollaborationRating.ratee_id == engineer_id,
                CollaborationRating.period_id == period.id,
                CollaborationRating.total_score.isnot(None)
            ).count()

            trend_data.append({
                'period_id': period.id,
                'period_name': period.period_name,
                'start_date': period.start_date.isoformat(),
                'end_date': period.end_date.isoformat(),
                'average_score': float(avg_score),
                'rating_count': ratings
            })

        return {
            'engineer_id': engineer_id,
            'trend_data': trend_data,
            'periods_count': len(trend_data)
        }

    def analyze_rating_quality(
        self,
        period_id: int
    ) -> Dict[str, Any]:
        """
        分析评价质量

        Args:
            period_id: 考核周期ID

        Returns:
            评价质量分析
        """
        ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.period_id == period_id,
            CollaborationRating.total_score.isnot(None)
        ).all()

        if not ratings:
            return {
                'total_ratings': 0,
                'quality_analysis': {},
                'recommendations': []
            }

        # 分析评分分布
        scores = [float(r.total_score) for r in ratings]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0

        # 计算标准差
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 0.0
        std_dev = variance ** 0.5

        # 分析各维度得分
        dimension_scores = {
            'communication': [r.communication_score for r in ratings if r.communication_score],
            'response': [r.response_score for r in ratings if r.response_score],
            'delivery': [r.delivery_score for r in ratings if r.delivery_score],
            'interface': [r.interface_score for r in ratings if r.interface_score]
        }

        dimension_analysis = {}
        for dim, scores_list in dimension_scores.items():
            if scores_list:
                dimension_analysis[dim] = {
                    'average': round(sum(scores_list) / len(scores_list), 2),
                    'min': min(scores_list),
                    'max': max(scores_list)
                }

        # 生成建议
        recommendations = []
        if std_dev > 15:  # 标准差过大，评价差异大
            recommendations.append('评价得分差异较大，建议统一评价标准')
        if avg_score < 70:
            recommendations.append('平均得分较低，建议加强跨部门协作培训')
        if len([s for s in scores if s < 60]) > len(scores) * 0.2:  # 超过20%得分低于60
            recommendations.append('存在较多低分评价，建议分析具体原因并改进')

        return {
            'total_ratings': len(ratings),
            'quality_analysis': {
                'average_score': round(avg_score, 2),
                'min_score': round(min_score, 2),
                'max_score': round(max_score, 2),
                'std_deviation': round(std_dev, 2),
                'dimension_analysis': dimension_analysis
            },
            'recommendations': recommendations
        }
