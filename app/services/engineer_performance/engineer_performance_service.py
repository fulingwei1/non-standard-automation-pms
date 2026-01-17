# -*- coding: utf-8 -*-
"""
工程师绩效评价服务 - 主服务类
整合所有子模块，提供统一的对外接口
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.engineer_performance import EngineerDimensionConfig, EngineerProfile
from app.models.performance import PerformancePeriod, PerformanceResult
from app.schemas.engineer_performance import (
    DimensionConfigCreate,
    EngineerDimensionScore,
    EngineerPerformanceSummary,
    EngineerProfileCreate,
    EngineerProfileUpdate,
)

from .dimension_config_service import DimensionConfigService
from .performance_calculator import PerformanceCalculator
from .profile_service import ProfileService
from .ranking_service import RankingService


class EngineerPerformanceService:
    """
    工程师绩效服务 - 主服务类

    整合所有子模块功能，提供完整的绩效管理服务
    """

    def __init__(self, db: Session):
        self.db = db
        self.profile_service = ProfileService(db)
        self.dimension_config_service = DimensionConfigService(db)
        self.performance_calculator = PerformanceCalculator(db)
        self.ranking_service = RankingService(db)

    # ==================== 工程师档案管理 ====================

    def get_engineer_profile(self, user_id: int) -> Optional[EngineerProfile]:
        """获取工程师档案"""
        return self.profile_service.get_profile(user_id)

    def get_engineer_profile_by_id(self, profile_id: int) -> Optional[EngineerProfile]:
        """通过ID获取工程师档案"""
        return self.profile_service.get_profile_by_id(profile_id)

    def create_engineer_profile(self, data: EngineerProfileCreate) -> EngineerProfile:
        """创建工程师档案"""
        return self.profile_service.create_profile(data)

    def update_engineer_profile(
        self, user_id: int, data: EngineerProfileUpdate
    ) -> Optional[EngineerProfile]:
        """更新工程师档案"""
        return self.profile_service.update_profile(user_id, data)

    def list_engineers(
        self,
        job_type: Optional[str] = None,
        job_level: Optional[str] = None,
        department_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[EngineerProfile], int]:
        """获取工程师列表"""
        return self.profile_service.list_profiles(
            job_type=job_type,
            job_level=job_level,
            department_id=department_id,
            limit=limit,
            offset=offset
        )

    def get_engineers_by_job_type(self, job_type: str) -> List[EngineerProfile]:
        """按岗位类型获取工程师"""
        return self.profile_service.get_profiles_by_job_type(job_type)

    def count_engineers_by_config(
        self, job_type: str, job_level: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> int:
        """统计受配置影响的工程师人数"""
        return self.profile_service.count_profiles_by_config(
            job_type=job_type,
            job_level=job_level,
            department_id=department_id
        )

    # ==================== 五维权重配置 ====================

    def get_dimension_config(
        self,
        job_type: str,
        job_level: Optional[str] = None,
        effective_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> Optional[EngineerDimensionConfig]:
        """获取五维权重配置（支持部门级别配置）"""
        return self.dimension_config_service.get_config(
            job_type=job_type,
            job_level=job_level,
            effective_date=effective_date,
            department_id=department_id
        )

    def create_dimension_config(
        self, data: DimensionConfigCreate, operator_id: int,
        department_id: Optional[int] = None, require_approval: bool = True
    ) -> EngineerDimensionConfig:
        """创建五维权重配置（支持部门级别配置）"""
        return self.dimension_config_service.create_config(
            data=data,
            operator_id=operator_id,
            department_id=department_id,
            require_approval=require_approval
        )

    def list_dimension_configs(
        self,
        job_type: Optional[str] = None,
        include_expired: bool = False,
        department_id: Optional[int] = None,
        include_global: bool = True
    ) -> List[EngineerDimensionConfig]:
        """获取五维配置列表（支持按部门筛选）"""
        return self.dimension_config_service.list_configs(
            job_type=job_type,
            include_expired=include_expired,
            department_id=department_id,
            include_global=include_global
        )

    def get_department_configs(self, manager_id: int) -> Dict[str, Any]:
        """获取部门经理管理的部门的评价指标配置"""
        return self.dimension_config_service.get_department_configs(manager_id)

    def approve_dimension_config(
        self,
        config_id: int,
        approver_id: int,
        approved: bool = True,
        approval_reason: Optional[str] = None
    ) -> EngineerDimensionConfig:
        """审批部门级别配置"""
        return self.dimension_config_service.approve_config(
            config_id=config_id,
            approver_id=approver_id,
            approved=approved,
            approval_reason=approval_reason
        )

    def get_pending_approvals(self) -> List[EngineerDimensionConfig]:
        """获取待审批的部门级别配置"""
        return self.dimension_config_service.get_pending_approvals()

    # ==================== 绩效计算 ====================

    def calculate_grade(self, score: Decimal) -> str:
        """根据分数计算等级"""
        return self.performance_calculator.calculate_grade(score)

    def calculate_dimension_score(
        self,
        engineer_id: int,
        period_id: int,
        job_type: str
    ) -> EngineerDimensionScore:
        """计算工程师五维得分"""
        return self.performance_calculator.calculate_dimension_score(
            engineer_id=engineer_id,
            period_id=period_id,
            job_type=job_type
        )

    def calculate_total_score(
        self,
        dimension_scores: EngineerDimensionScore,
        config: EngineerDimensionConfig,
        job_type: Optional[str] = None
    ) -> Decimal:
        """计算加权总分（支持方案工程师的方案成功率维度）"""
        return self.performance_calculator.calculate_total_score(
            dimension_scores=dimension_scores,
            config=config,
            job_type=job_type
        )

    # ==================== 排名统计 ====================

    def get_ranking(
        self,
        period_id: int,
        job_type: Optional[str] = None,
        job_level: Optional[str] = None,
        department_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[PerformanceResult], int]:
        """获取绩效排名"""
        return self.ranking_service.get_ranking(
            period_id=period_id,
            job_type=job_type,
            job_level=job_level,
            department_id=department_id,
            limit=limit,
            offset=offset
        )

    def get_company_summary(self, period_id: int) -> Dict[str, Any]:
        """获取公司整体概况"""
        return self.ranking_service.get_company_summary(period_id)

    def get_engineer_trend(
        self, engineer_id: int, periods: int = 6
    ) -> List[Dict[str, Any]]:
        """获取工程师历史趋势"""
        return self.ranking_service.get_engineer_trend(
            engineer_id=engineer_id,
            periods=periods
        )

    # ==================== 等级划分规则 ====================

    @property
    def GRADE_RULES(self) -> Dict[str, tuple]:
        """等级划分规则"""
        return self.performance_calculator.GRADE_RULES
