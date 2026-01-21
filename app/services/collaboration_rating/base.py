# -*- coding: utf-8 -*-
"""
跨部门协作评价服务 - 基础类
"""
from sqlalchemy.orm import Session

from .ratings import RatingManager
from .selector import CollaboratorSelector
from .statistics import RatingStatistics


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
        # 初始化子模块
        self.selector = CollaboratorSelector(db, self)
        self.ratings = RatingManager(db, self)
        self.statistics = RatingStatistics(db, self)

    # 向后兼容：将子模块方法暴露为服务类方法
    def auto_select_collaborators(self, *args, **kwargs):
        return self.selector.auto_select_collaborators(*args, **kwargs)

    def _get_collaborators_from_projects(self, *args, **kwargs):
        return self.selector._get_collaborators_from_projects(*args, **kwargs)

    def _get_target_job_types(self, *args, **kwargs):
        return self.selector._get_target_job_types(*args, **kwargs)

    def create_rating_invitations(self, *args, **kwargs):
        return self.ratings.create_rating_invitations(*args, **kwargs)

    def submit_rating(self, *args, **kwargs):
        return self.ratings.submit_rating(*args, **kwargs)

    def get_pending_ratings(self, *args, **kwargs):
        return self.ratings.get_pending_ratings(*args, **kwargs)

    def auto_complete_missing_ratings(self, *args, **kwargs):
        return self.ratings.auto_complete_missing_ratings(*args, **kwargs)

    def get_average_collaboration_score(self, *args, **kwargs):
        return self.statistics.get_average_collaboration_score(*args, **kwargs)

    def get_rating_statistics(self, *args, **kwargs):
        return self.statistics.get_rating_statistics(*args, **kwargs)

    def get_collaboration_trend(self, *args, **kwargs):
        return self.statistics.get_collaboration_trend(*args, **kwargs)

    def analyze_rating_quality(self, *args, **kwargs):
        return self.statistics.analyze_rating_quality(*args, **kwargs)
