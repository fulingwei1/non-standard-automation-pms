# -*- coding: utf-8 -*-
"""
设计评审自动同步服务
从技术评审系统自动同步设计评审记录
"""

from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.engineer_performance import DesignReview
from app.models.project import Project
from app.models.technical_review import TechnicalReview
from app.models.user import User


class DesignReviewSyncService:
    """设计评审自动同步服务"""

    def __init__(self, db: Session):
        self.db = db

    def sync_from_technical_review(
        self,
        technical_review_id: int,
        force_update: bool = False
    ) -> Optional[DesignReview]:
        """
        从技术评审同步设计评审记录

        Args:
            technical_review_id: 技术评审ID
            force_update: 是否强制更新（即使已存在）

        Returns:
            同步的设计评审记录
        """
        # 获取技术评审
        tech_review = self.db.query(TechnicalReview).filter(
            TechnicalReview.id == technical_review_id
        ).first()

        if not tech_review:
            return None

        # 只同步已完成的评审
        if tech_review.status != 'COMPLETED':
            return None

        # 检查是否已同步
        existing_review = self.db.query(DesignReview).filter(
            DesignReview.project_id == tech_review.project_id,
            DesignReview.review_date == (tech_review.actual_date.date() if tech_review.actual_date else tech_review.scheduled_date.date())
        ).first()

        if existing_review and not force_update:
            # 已存在且不强制更新
            return existing_review

        # 确定设计者（通常是汇报人）
        designer_id = tech_review.presenter_id
        if not designer_id:
            return None

        # 确定评审人（通常是主持人）
        reviewer_id = tech_review.host_id

        # 确定评审结果
        review_result = None
        is_first_pass = False

        if tech_review.conclusion == 'PASS':
            review_result = 'PASSED'
            is_first_pass = True
        elif tech_review.conclusion == 'PASS_WITH_CONDITION':
            review_result = 'PASSED_WITH_CONDITION'
            is_first_pass = False
        elif tech_review.conclusion == 'REJECT':
            review_result = 'REJECTED'
            is_first_pass = False
        else:
            # 其他状态不同步
            return None

        # 获取项目信息
        project = self.db.query(Project).filter(
            Project.id == tech_review.project_id
        ).first()

        if not project:
            return None

        # 生成设计名称
        design_name = f"{tech_review.review_name}（{tech_review.review_type}）"

        # 创建或更新设计评审记录
        if existing_review:
            design_review = existing_review
            design_review.design_name = design_name
            design_review.design_type = tech_review.review_type
            design_review.review_date = tech_review.actual_date.date() if tech_review.actual_date else tech_review.scheduled_date.date()
            design_review.reviewer_id = reviewer_id
            design_review.result = review_result
            design_review.is_first_pass = is_first_pass
            design_review.issues_found = (
                tech_review.issue_count_a +
                tech_review.issue_count_b +
                tech_review.issue_count_c +
                tech_review.issue_count_d
            )
            design_review.review_comments = tech_review.conclusion_summary
            design_review.updated_at = datetime.now()
        else:
            design_review = DesignReview(
                project_id=tech_review.project_id,
                designer_id=designer_id,
                design_name=design_name,
                design_type=tech_review.review_type,
                design_code=tech_review.review_no,
                review_date=tech_review.actual_date.date() if tech_review.actual_date else tech_review.scheduled_date.date(),
                reviewer_id=reviewer_id,
                result=review_result,
                is_first_pass=is_first_pass,
                issues_found=(
                    tech_review.issue_count_a +
                    tech_review.issue_count_b +
                    tech_review.issue_count_c +
                    tech_review.issue_count_d
                ),
                review_comments=tech_review.conclusion_summary
            )
            self.db.add(design_review)

        self.db.commit()
        self.db.refresh(design_review)

        return design_review

    def sync_all_completed_reviews(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        同步所有已完成的技术评审

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            同步统计信息
        """
        stats = {
            'total_reviews': 0,
            'synced_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'errors': []
        }

        # 查询已完成的评审
        query = self.db.query(TechnicalReview).filter(
            TechnicalReview.status == 'COMPLETED',
            TechnicalReview.conclusion.in_(['PASS', 'PASS_WITH_CONDITION', 'REJECT'])
        )

        if start_date:
            query = query.filter(TechnicalReview.actual_date >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(TechnicalReview.actual_date <= datetime.combine(end_date, datetime.max.time()))

        reviews = query.all()
        stats['total_reviews'] = len(reviews)

        for review in reviews:
            try:
                design_review = self.sync_from_technical_review(review.id)
                if design_review:
                    stats['synced_count'] += 1
                else:
                    stats['skipped_count'] += 1
            except Exception as e:
                stats['error_count'] += 1
                stats['errors'].append({
                    'review_id': review.id,
                    'review_no': review.review_no,
                    'error': str(e)
                })

        return stats
