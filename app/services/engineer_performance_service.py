# -*- coding: utf-8 -*-
"""
工程师绩效评价服务
核心业务逻辑：绩效计算、排名、统计
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.engineer_performance import (
    EngineerProfile, EngineerDimensionConfig, CollaborationRating,
    KnowledgeContribution, DesignReview, MechanicalDebugIssue,
    TestBugRecord, CodeModule, PlcProgramVersion, PlcModuleLibrary
)
from app.models.performance import PerformancePeriod, PerformanceResult
from app.models.user import User
from app.schemas.engineer_performance import (
    EngineerProfileCreate, EngineerProfileUpdate,
    DimensionConfigCreate, DimensionConfigUpdate,
    EngineerDimensionScore, EngineerPerformanceSummary
)


class EngineerPerformanceService:
    """工程师绩效服务"""

    # 等级划分规则
    GRADE_RULES = {
        'S': (85, 100),   # 优秀
        'A': (70, 84),    # 良好
        'B': (60, 69),    # 合格
        'C': (40, 59),    # 待改进
        'D': (0, 39),     # 不合格
    }

    def __init__(self, db: Session):
        self.db = db

    # ==================== 工程师档案管理 ====================

    def get_engineer_profile(self, user_id: int) -> Optional[EngineerProfile]:
        """获取工程师档案"""
        return self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == user_id
        ).first()

    def get_engineer_profile_by_id(self, profile_id: int) -> Optional[EngineerProfile]:
        """通过ID获取工程师档案"""
        return self.db.query(EngineerProfile).filter(
            EngineerProfile.id == profile_id
        ).first()

    def create_engineer_profile(self, data: EngineerProfileCreate) -> EngineerProfile:
        """创建工程师档案"""
        profile = EngineerProfile(
            user_id=data.user_id,
            job_type=data.job_type,
            job_level=data.job_level or 'junior',
            skills=data.skills,
            certifications=data.certifications,
            job_start_date=data.job_start_date,
            level_start_date=data.level_start_date
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_engineer_profile(
        self, user_id: int, data: EngineerProfileUpdate
    ) -> Optional[EngineerProfile]:
        """更新工程师档案"""
        profile = self.get_engineer_profile(user_id)
        if not profile:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)

        profile.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_engineers(
        self,
        job_type: Optional[str] = None,
        job_level: Optional[str] = None,
        department_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[EngineerProfile], int]:
        """获取工程师列表"""
        query = self.db.query(EngineerProfile).join(
            User, EngineerProfile.user_id == User.id
        )

        if job_type:
            query = query.filter(EngineerProfile.job_type == job_type)
        if job_level:
            query = query.filter(EngineerProfile.job_level == job_level)
        if department_id:
            query = query.filter(User.department_id == department_id)

        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    def get_engineers_by_job_type(self, job_type: str) -> List[EngineerProfile]:
        """按岗位类型获取工程师"""
        return self.db.query(EngineerProfile).filter(
            EngineerProfile.job_type == job_type
        ).all()

    def count_engineers_by_config(
        self, job_type: str, job_level: Optional[str] = None
    ) -> int:
        """统计受配置影响的工程师人数"""
        query = self.db.query(EngineerProfile).filter(
            EngineerProfile.job_type == job_type
        )
        if job_level:
            query = query.filter(EngineerProfile.job_level == job_level)
        return query.count()

    # ==================== 五维权重配置 ====================

    def get_dimension_config(
        self,
        job_type: str,
        job_level: Optional[str] = None,
        effective_date: Optional[date] = None
    ) -> Optional[EngineerDimensionConfig]:
        """获取五维权重配置"""
        if effective_date is None:
            effective_date = date.today()

        # 优先匹配精确的岗位+级别配置
        query = self.db.query(EngineerDimensionConfig).filter(
            EngineerDimensionConfig.job_type == job_type,
            EngineerDimensionConfig.effective_date <= effective_date,
            or_(
                EngineerDimensionConfig.expired_date.is_(None),
                EngineerDimensionConfig.expired_date > effective_date
            )
        )

        if job_level:
            # 先尝试匹配精确级别
            config = query.filter(
                EngineerDimensionConfig.job_level == job_level
            ).order_by(desc(EngineerDimensionConfig.effective_date)).first()

            if config:
                return config

        # 回退到通用配置（job_level 为 None）
        return query.filter(
            EngineerDimensionConfig.job_level.is_(None)
        ).order_by(desc(EngineerDimensionConfig.effective_date)).first()

    def create_dimension_config(
        self, data: DimensionConfigCreate, operator_id: int
    ) -> EngineerDimensionConfig:
        """创建五维权重配置"""
        # 验证权重总和为100
        total_weight = (
            data.technical_weight + data.execution_weight +
            data.cost_quality_weight + data.knowledge_weight +
            data.collaboration_weight
        )
        if total_weight != 100:
            raise ValueError(f"权重总和必须为100，当前为{total_weight}")

        config = EngineerDimensionConfig(
            job_type=data.job_type,
            job_level=data.job_level,
            technical_weight=data.technical_weight,
            execution_weight=data.execution_weight,
            cost_quality_weight=data.cost_quality_weight,
            knowledge_weight=data.knowledge_weight,
            collaboration_weight=data.collaboration_weight,
            effective_date=data.effective_date,
            config_name=data.config_name,
            description=data.description,
            operator_id=operator_id
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def list_dimension_configs(
        self,
        job_type: Optional[str] = None,
        include_expired: bool = False
    ) -> List[EngineerDimensionConfig]:
        """获取五维配置列表"""
        query = self.db.query(EngineerDimensionConfig)

        if job_type:
            query = query.filter(EngineerDimensionConfig.job_type == job_type)

        if not include_expired:
            today = date.today()
            query = query.filter(
                or_(
                    EngineerDimensionConfig.expired_date.is_(None),
                    EngineerDimensionConfig.expired_date > today
                )
            )

        return query.order_by(
            EngineerDimensionConfig.job_type,
            EngineerDimensionConfig.job_level,
            desc(EngineerDimensionConfig.effective_date)
        ).all()

    # ==================== 绩效计算 ====================

    def calculate_grade(self, score: Decimal) -> str:
        """根据分数计算等级"""
        score_int = int(score)
        for grade, (min_score, max_score) in self.GRADE_RULES.items():
            if min_score <= score_int <= max_score:
                return grade
        return 'D'

    def calculate_dimension_score(
        self,
        engineer_id: int,
        period_id: int,
        job_type: str
    ) -> EngineerDimensionScore:
        """计算工程师五维得分"""
        # 获取考核周期
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        # 根据岗位类型调用不同的计算方法
        if job_type == 'mechanical':
            return self._calculate_mechanical_score(engineer_id, period)
        elif job_type == 'test':
            return self._calculate_test_score(engineer_id, period)
        elif job_type == 'electrical':
            return self._calculate_electrical_score(engineer_id, period)
        else:
            raise ValueError(f"未知的岗位类型: {job_type}")

    def _calculate_mechanical_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算机械工程师五维得分"""
        # 技术能力：设计一次通过率、ECN责任率、调试问题密度
        design_reviews = self.db.query(DesignReview).filter(
            DesignReview.designer_id == engineer_id,
            DesignReview.review_date.between(period.start_date, period.end_date)
        ).all()

        if design_reviews:
            first_pass_count = sum(1 for r in design_reviews if r.is_first_pass)
            first_pass_rate = first_pass_count / len(design_reviews) * 100
        else:
            first_pass_rate = 85  # 默认值

        # 调试问题数量
        debug_issues = self.db.query(MechanicalDebugIssue).filter(
            MechanicalDebugIssue.responsible_id == engineer_id,
            MechanicalDebugIssue.found_date.between(period.start_date, period.end_date)
        ).count()

        # 技术得分计算
        technical_score = min(first_pass_rate / 85 * 100, 120)
        if debug_issues > 0:
            technical_score = max(technical_score - debug_issues * 5, 0)

        # 项目执行：简化计算
        execution_score = Decimal('80')

        # 成本/质量：简化计算
        cost_quality_score = Decimal('75')

        # 知识沉淀
        contributions = self.db.query(KnowledgeContribution).filter(
            KnowledgeContribution.contributor_id == engineer_id,
            KnowledgeContribution.job_type == 'mechanical',
            KnowledgeContribution.status == 'approved',
            KnowledgeContribution.created_at.between(period.start_date, period.end_date)
        ).count()

        knowledge_score = min(50 + contributions * 10, 100)

        # 团队协作
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)

        return EngineerDimensionScore(
            technical_score=Decimal(str(round(technical_score, 2))),
            execution_score=execution_score,
            cost_quality_score=cost_quality_score,
            knowledge_score=Decimal(str(knowledge_score)),
            collaboration_score=collaboration_avg
        )

    def _calculate_test_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算测试工程师五维得分"""
        # Bug修复统计
        bugs = self.db.query(TestBugRecord).filter(
            TestBugRecord.assignee_id == engineer_id,
            TestBugRecord.found_time.between(period.start_date, period.end_date)
        ).all()

        if bugs:
            resolved_bugs = [b for b in bugs if b.status in ('resolved', 'closed')]
            resolve_rate = len(resolved_bugs) / len(bugs) * 100 if bugs else 100

            # 平均修复时长
            fix_times = [b.fix_duration_hours for b in resolved_bugs if b.fix_duration_hours]
            avg_fix_time = sum(fix_times) / len(fix_times) if fix_times else 4
        else:
            resolve_rate = 100
            avg_fix_time = 4

        # 技术得分
        technical_score = min(resolve_rate, 100)
        if avg_fix_time < 4:
            technical_score = min(technical_score + 10, 120)
        elif avg_fix_time > 8:
            technical_score = max(technical_score - 10, 0)

        # 代码模块贡献
        modules = self.db.query(CodeModule).filter(
            CodeModule.contributor_id == engineer_id,
            CodeModule.created_at.between(period.start_date, period.end_date)
        ).count()

        knowledge_score = min(50 + modules * 15, 100)

        # 团队协作
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)

        return EngineerDimensionScore(
            technical_score=Decimal(str(round(technical_score, 2))),
            execution_score=Decimal('80'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal(str(knowledge_score)),
            collaboration_score=collaboration_avg
        )

    def _calculate_electrical_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算电气工程师五维得分"""
        # PLC程序调试统计
        plc_programs = self.db.query(PlcProgramVersion).filter(
            PlcProgramVersion.programmer_id == engineer_id,
            PlcProgramVersion.first_debug_date.between(period.start_date, period.end_date)
        ).all()

        if plc_programs:
            first_pass_count = sum(1 for p in plc_programs if p.is_first_pass)
            first_pass_rate = first_pass_count / len(plc_programs) * 100
        else:
            first_pass_rate = 80

        technical_score = min(first_pass_rate / 80 * 100, 120)

        # PLC模块贡献
        modules = self.db.query(PlcModuleLibrary).filter(
            PlcModuleLibrary.contributor_id == engineer_id,
            PlcModuleLibrary.created_at.between(period.start_date, period.end_date)
        ).count()

        knowledge_score = min(50 + modules * 15, 100)

        # 团队协作
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)

        return EngineerDimensionScore(
            technical_score=Decimal(str(round(technical_score, 2))),
            execution_score=Decimal('80'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal(str(knowledge_score)),
            collaboration_score=collaboration_avg
        )

    def _get_collaboration_avg(self, engineer_id: int, period_id: int) -> Decimal:
        """获取协作评价平均分"""
        ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.ratee_id == engineer_id,
            CollaborationRating.period_id == period_id
        ).all()

        if not ratings:
            return Decimal('75')

        total = sum(
            (r.communication_score or 0) + (r.response_score or 0) +
            (r.delivery_score or 0) + (r.interface_score or 0)
            for r in ratings
        )
        avg = total / (len(ratings) * 4) * 20  # 转换为百分制
        return Decimal(str(round(avg, 2)))

    def calculate_total_score(
        self,
        dimension_scores: EngineerDimensionScore,
        config: EngineerDimensionConfig
    ) -> Decimal:
        """计算加权总分"""
        total = (
            dimension_scores.technical_score * config.technical_weight / 100 +
            dimension_scores.execution_score * config.execution_weight / 100 +
            dimension_scores.cost_quality_score * config.cost_quality_weight / 100 +
            dimension_scores.knowledge_score * config.knowledge_weight / 100 +
            dimension_scores.collaboration_score * config.collaboration_weight / 100
        )
        return Decimal(str(round(total, 2)))

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
        query = self.db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period_id,
            PerformanceResult.job_type.isnot(None)
        )

        if job_type:
            query = query.filter(PerformanceResult.job_type == job_type)
        if job_level:
            query = query.filter(PerformanceResult.job_level == job_level)
        if department_id:
            query = query.filter(PerformanceResult.department_id == department_id)

        total = query.count()
        items = query.order_by(
            desc(PerformanceResult.total_score)
        ).offset(offset).limit(limit).all()

        return items, total

    def get_company_summary(self, period_id: int) -> Dict[str, Any]:
        """获取公司整体概况"""
        results = self.db.query(PerformanceResult).filter(
            PerformanceResult.period_id == period_id,
            PerformanceResult.job_type.isnot(None)
        ).all()

        if not results:
            return {}

        # 按岗位类型统计
        by_job_type = {}
        for job_type in ['mechanical', 'test', 'electrical']:
            type_results = [r for r in results if r.job_type == job_type]
            if type_results:
                scores = [float(r.total_score or 0) for r in type_results]
                by_job_type[job_type] = {
                    'count': len(type_results),
                    'avg_score': round(sum(scores) / len(scores), 2),
                    'max_score': max(scores),
                    'min_score': min(scores)
                }

        # 等级分布
        level_distribution = {}
        for result in results:
            level = result.level or 'D'
            level_distribution[level] = level_distribution.get(level, 0) + 1

        # 总体统计
        all_scores = [float(r.total_score or 0) for r in results]

        return {
            'total_engineers': len(results),
            'by_job_type': by_job_type,
            'level_distribution': level_distribution,
            'avg_score': round(sum(all_scores) / len(all_scores), 2),
            'max_score': max(all_scores),
            'min_score': min(all_scores)
        }

    def get_engineer_trend(
        self, engineer_id: int, periods: int = 6
    ) -> List[Dict[str, Any]]:
        """获取工程师历史趋势"""
        results = self.db.query(PerformanceResult).join(
            PerformancePeriod, PerformanceResult.period_id == PerformancePeriod.id
        ).filter(
            PerformanceResult.user_id == engineer_id
        ).order_by(
            desc(PerformancePeriod.start_date)
        ).limit(periods).all()

        trends = []
        for r in reversed(results):
            trends.append({
                'period_id': r.period_id,
                'period_name': r.period.period_name if r.period else '',
                'total_score': float(r.total_score or 0),
                'level': r.level,
                'rank': r.company_rank
            })
        return trends
