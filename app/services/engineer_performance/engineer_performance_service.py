# -*- coding: utf-8 -*-
"""
工程师绩效评价服务 - 主服务类
整合所有子模块，提供统一的对外接口
"""

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.engineer_performance import EngineerDimensionConfig, EngineerProfile
from app.models.performance import PerformancePeriod, PerformanceResult
from app.models.user import User
from app.schemas.engineer_performance import (
    DimensionConfigCreate,
    EngineerDimensionScore,
    EngineerProfileCreate,
    EngineerProfileUpdate,
)

from .dimension_config_service import DimensionConfigService
from .engperf_scope import EngPerfScopeContext
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
        offset: int = 0,
    ) -> Tuple[List[EngineerProfile], int]:
        """获取工程师列表"""
        return self.profile_service.list_profiles(
            job_type=job_type,
            job_level=job_level,
            department_id=department_id,
            limit=limit,
            offset=offset,
        )

    def get_engineers_by_job_type(self, job_type: str) -> List[EngineerProfile]:
        """按岗位类型获取工程师"""
        return self.profile_service.get_profiles_by_job_type(job_type)

    def count_engineers_by_config(
        self, job_type: str, job_level: Optional[str] = None, department_id: Optional[int] = None
    ) -> int:
        """统计受配置影响的工程师人数"""
        return self.profile_service.count_profiles_by_config(
            job_type=job_type, job_level=job_level, department_id=department_id
        )

    # ==================== 五维权重配置 ====================

    def get_dimension_config(
        self,
        job_type: str,
        job_level: Optional[str] = None,
        effective_date: Optional[date] = None,
        department_id: Optional[int] = None,
    ) -> Optional[EngineerDimensionConfig]:
        """获取五维权重配置（支持部门级别配置）"""
        return self.dimension_config_service.get_config(
            job_type=job_type,
            job_level=job_level,
            effective_date=effective_date,
            department_id=department_id,
        )

    def create_dimension_config(
        self,
        data: DimensionConfigCreate,
        operator_id: int,
        department_id: Optional[int] = None,
        require_approval: bool = True,
    ) -> EngineerDimensionConfig:
        """创建五维权重配置（支持部门级别配置）"""
        return self.dimension_config_service.create_config(
            data=data,
            operator_id=operator_id,
            department_id=department_id,
            require_approval=require_approval,
        )

    def list_dimension_configs(
        self,
        job_type: Optional[str] = None,
        include_expired: bool = False,
        department_id: Optional[int] = None,
        include_global: bool = True,
    ) -> List[EngineerDimensionConfig]:
        """获取五维配置列表（支持按部门筛选）"""
        return self.dimension_config_service.list_configs(
            job_type=job_type,
            include_expired=include_expired,
            department_id=department_id,
            include_global=include_global,
        )

    def get_department_configs(self, manager_id: int) -> Dict[str, Any]:
        """获取部门经理管理的部门的评价指标配置"""
        return self.dimension_config_service.get_department_configs(manager_id)

    def approve_dimension_config(
        self,
        config_id: int,
        approver_id: int,
        approved: bool = True,
        approval_reason: Optional[str] = None,
    ) -> EngineerDimensionConfig:
        """审批部门级别配置"""
        return self.dimension_config_service.approve_config(
            config_id=config_id,
            approver_id=approver_id,
            approved=approved,
            approval_reason=approval_reason,
        )

    def get_pending_approvals(self) -> List[EngineerDimensionConfig]:
        """获取待审批的部门级别配置"""
        return self.dimension_config_service.get_pending_approvals()

    # ==================== 绩效计算 ====================

    def calculate_grade(self, score: Decimal) -> str:
        """根据分数计算等级"""
        return self.performance_calculator.calculate_grade(score)

    def calculate_dimension_score(
        self, engineer_id: int, period_id: int, job_type: str
    ) -> EngineerDimensionScore:
        """计算工程师五维得分"""
        return self.performance_calculator.calculate_dimension_score(
            engineer_id=engineer_id, period_id=period_id, job_type=job_type
        )

    def calculate_total_score(
        self,
        dimension_scores: EngineerDimensionScore,
        config: EngineerDimensionConfig,
        job_type: Optional[str] = None,
    ) -> Decimal:
        """计算加权总分（支持方案工程师的方案成功率维度）"""
        return self.performance_calculator.calculate_total_score(
            dimension_scores=dimension_scores, config=config, job_type=job_type
        )

    def calculate_and_save_result(
        self,
        engineer_id: int,
        period_id: int,
        job_type: Optional[str] = None,
        job_level: Optional[str] = None,
    ) -> PerformanceResult:
        """计算工程师绩效并写回 performance_result。"""
        period = (
            self.db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
        )
        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        user = self.db.query(User).filter(User.id == engineer_id).first()
        if not user:
            raise ValueError(f"工程师用户不存在: {engineer_id}")

        profile = self.get_engineer_profile(engineer_id)
        resolved_job_type = job_type or (profile.job_type if profile else None)
        resolved_job_level = job_level or (profile.job_level if profile else None)
        if not resolved_job_type:
            raise ValueError(f"工程师档案缺少岗位类型: {engineer_id}")

        config = self.get_dimension_config(
            job_type=resolved_job_type,
            job_level=resolved_job_level,
            effective_date=period.end_date,
            department_id=user.department_id,
        )
        if config is None:
            config = self._default_dimension_config()

        dimension_scores = self.calculate_dimension_score(
            engineer_id=engineer_id,
            period_id=period_id,
            job_type=resolved_job_type,
        )
        total_score = self.calculate_total_score(
            dimension_scores=dimension_scores,
            config=config,
            job_type=resolved_job_type,
        )
        level = self.calculate_grade(total_score)

        result = (
            self.db.query(PerformanceResult)
            .filter(
                PerformanceResult.period_id == period_id,
                PerformanceResult.user_id == engineer_id,
            )
            .first()
        )
        if result is None:
            result = PerformanceResult(period_id=period_id, user_id=engineer_id)
            self.db.add(result)

        self._fill_performance_result(
            result=result,
            user=user,
            dimension_scores=dimension_scores,
            total_score=total_score,
            level=level,
            job_type=resolved_job_type,
            job_level=resolved_job_level,
        )

        self.db.flush()
        self._refresh_period_ranks(period_id)
        self.db.commit()
        self.db.refresh(result)
        return result

    def _fill_performance_result(
        self,
        result: PerformanceResult,
        user: User,
        dimension_scores: EngineerDimensionScore,
        total_score: Decimal,
        level: str,
        job_type: str,
        job_level: Optional[str],
    ) -> None:
        result.user_name = user.display_name
        result.department_id = user.department_id
        result.department_name = user.department
        result.total_score = total_score
        result.original_total_score = total_score
        result.level = level
        result.workload_score = dimension_scores.technical_score
        result.task_score = dimension_scores.execution_score
        result.quality_score = dimension_scores.cost_quality_score
        result.growth_score = dimension_scores.knowledge_score
        result.collaboration_score = dimension_scores.collaboration_score
        result.indicator_scores = {
            "technical": float(dimension_scores.technical_score),
            "execution": float(dimension_scores.execution_score),
            "cost_quality": float(dimension_scores.cost_quality_score),
            "knowledge": float(dimension_scores.knowledge_score),
            "collaboration": float(dimension_scores.collaboration_score),
        }
        if dimension_scores.solution_success_score is not None:
            result.indicator_scores["solution_success"] = float(
                dimension_scores.solution_success_score
            )
        result.status = "CALCULATED"
        result.calculated_at = datetime.now()
        result.job_type = job_type
        result.job_level = job_level

    def _refresh_period_ranks(self, period_id: int) -> None:
        results = (
            self.db.query(PerformanceResult)
            .filter(
                PerformanceResult.period_id == period_id,
                PerformanceResult.job_type.isnot(None),
                PerformanceResult.total_score.isnot(None),
            )
            .all()
        )
        ranked = sorted(
            results,
            key=lambda item: (-float(item.total_score or 0), item.user_id or 0),
        )
        for rank, result in enumerate(ranked, start=1):
            result.company_rank = rank
            if result.original_company_rank is None:
                result.original_company_rank = rank

        department_results: Dict[Optional[int], List[PerformanceResult]] = {}
        for result in ranked:
            department_results.setdefault(result.department_id, []).append(result)

        for dept_ranked in department_results.values():
            for rank, result in enumerate(dept_ranked, start=1):
                result.dept_rank = rank
                if result.original_dept_rank is None:
                    result.original_dept_rank = rank

    def _default_dimension_config(self) -> Any:
        return SimpleNamespace(
            technical_weight=30,
            execution_weight=25,
            cost_quality_weight=20,
            knowledge_weight=15,
            collaboration_weight=10,
        )

    # ==================== 排名统计 ====================

    def get_ranking(
        self,
        period_id: int,
        job_type: Optional[str] = None,
        job_level: Optional[str] = None,
        department_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
        scope: Optional[EngPerfScopeContext] = None,
    ) -> Tuple[List[PerformanceResult], int]:
        """获取绩效排名"""
        return self.ranking_service.get_ranking(
            period_id=period_id,
            job_type=job_type,
            job_level=job_level,
            department_id=department_id,
            limit=limit,
            offset=offset,
            scope=scope,
        )

    def get_company_summary(
        self,
        period_id: int,
        scope: Optional[EngPerfScopeContext] = None,
    ) -> Dict[str, Any]:
        """获取公司整体概况"""
        return self.ranking_service.get_company_summary(period_id, scope=scope)

    def get_engineer_trend(self, engineer_id: int, periods: int = 6) -> List[Dict[str, Any]]:
        """获取工程师历史趋势"""
        return self.ranking_service.get_engineer_trend(engineer_id=engineer_id, periods=periods)

    # ==================== 等级划分规则 ====================

    @property
    def GRADE_RULES(self) -> Dict[str, tuple]:
        """等级划分规则"""
        return self.performance_calculator.GRADE_RULES
