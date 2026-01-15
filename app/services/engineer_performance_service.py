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
        self, job_type: str, job_level: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> int:
        """
        统计受配置影响的工程师人数
        
        Args:
            job_type: 岗位类型
            job_level: 职级（可选）
            department_id: 部门ID（如果指定则只统计该部门的工程师）
        """
        query = self.db.query(EngineerProfile).filter(
            EngineerProfile.job_type == job_type
        )
        if job_level:
            query = query.filter(EngineerProfile.job_level == job_level)
        
        if department_id:
            from app.models.user import User
            from app.models.organization import Employee
            
            # 获取部门内的员工
            employees = self.db.query(Employee).filter(
                Employee.department_id == department_id,
                Employee.is_active == True
            ).all()
            
            employee_ids = [e.id for e in employees]
            user_ids = [
                u.id for u in self.db.query(User).filter(
                    User.employee_id.in_(employee_ids)
                ).all()
            ]
            
            query = query.filter(EngineerProfile.user_id.in_(user_ids))
        
        return query.count()

    # ==================== 五维权重配置 ====================

    def get_dimension_config(
        self,
        job_type: str,
        job_level: Optional[str] = None,
        effective_date: Optional[date] = None,
        department_id: Optional[int] = None
    ) -> Optional[EngineerDimensionConfig]:
        """
        获取五维权重配置（支持部门级别配置）
        
        优先级：部门级别配置 > 全局配置
        """
        if effective_date is None:
            effective_date = date.today()

        # 如果指定了部门，优先查找部门级别配置
        if department_id:
            dept_query = self.db.query(EngineerDimensionConfig).filter(
                EngineerDimensionConfig.job_type == job_type,
                EngineerDimensionConfig.department_id == department_id,
                EngineerDimensionConfig.is_global == False,
                EngineerDimensionConfig.approval_status == 'APPROVED',
                EngineerDimensionConfig.effective_date <= effective_date,
                or_(
                    EngineerDimensionConfig.expired_date.is_(None),
                    EngineerDimensionConfig.expired_date > effective_date
                )
            )
            
            if job_level:
                dept_config = dept_query.filter(
                    EngineerDimensionConfig.job_level == job_level
                ).order_by(desc(EngineerDimensionConfig.effective_date)).first()
                if dept_config:
                    return dept_config
            
            # 部门级别通用配置
            dept_config = dept_query.filter(
                EngineerDimensionConfig.job_level.is_(None)
            ).order_by(desc(EngineerDimensionConfig.effective_date)).first()
            if dept_config:
                return dept_config

        # 回退到全局配置
        query = self.db.query(EngineerDimensionConfig).filter(
            EngineerDimensionConfig.job_type == job_type,
            EngineerDimensionConfig.is_global == True,
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
        self, data: DimensionConfigCreate, operator_id: int,
        department_id: Optional[int] = None, require_approval: bool = True
    ) -> EngineerDimensionConfig:
        """
        创建五维权重配置（支持部门级别配置）
        
        Args:
            data: 配置数据
            operator_id: 操作人ID
            department_id: 部门ID（如果指定则创建部门级别配置）
            require_approval: 是否需要审批（部门级别配置默认需要审批）
        """
        # 验证权重总和为100
        total_weight = (
            data.technical_weight + data.execution_weight +
            data.cost_quality_weight + data.knowledge_weight +
            data.collaboration_weight
        )
        if total_weight != 100:
            raise ValueError(f"权重总和必须为100，当前为{total_weight}")

        # 如果是部门级别配置，需要验证部门经理权限
        if department_id:
            from app.models.organization import Department
            
            operator = self.db.query(User).filter(User.id == operator_id).first()
            if not operator or not operator.employee_id:
                raise ValueError("操作人信息不完整")
            
            dept = self.db.query(Department).filter(
                Department.id == department_id,
                Department.manager_id == operator.employee_id,
                Department.is_active == True
            ).first()
            
            if not dept:
                raise ValueError("无权限为该部门创建配置，只有部门经理可以创建部门级别配置")

        config = EngineerDimensionConfig(
            job_type=data.job_type,
            job_level=data.job_level,
            department_id=department_id,
            is_global=(department_id is None),
            technical_weight=data.technical_weight,
            execution_weight=data.execution_weight,
            cost_quality_weight=data.cost_quality_weight,
            knowledge_weight=data.knowledge_weight,
            collaboration_weight=data.collaboration_weight,
            effective_date=data.effective_date,
            config_name=data.config_name,
            description=data.description,
            operator_id=operator_id,
            approval_status='APPROVED' if not require_approval or department_id is None else 'PENDING'
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def list_dimension_configs(
        self,
        job_type: Optional[str] = None,
        include_expired: bool = False,
        department_id: Optional[int] = None,
        include_global: bool = True
    ) -> List[EngineerDimensionConfig]:
        """
        获取五维配置列表（支持按部门筛选）
        
        Args:
            job_type: 岗位类型
            include_expired: 是否包含已过期配置
            department_id: 部门ID（如果指定则只返回该部门的配置）
            include_global: 是否包含全局配置
        """
        query = self.db.query(EngineerDimensionConfig)

        if job_type:
            query = query.filter(EngineerDimensionConfig.job_type == job_type)
        
        if department_id:
            query = query.filter(EngineerDimensionConfig.department_id == department_id)
        elif not include_global:
            query = query.filter(EngineerDimensionConfig.is_global == False)

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

    def get_department_configs(
        self,
        manager_id: int
    ) -> Dict[str, Any]:
        """
        获取部门经理管理的部门的评价指标配置
        
        Args:
            manager_id: 部门经理ID
            
        Returns:
            部门配置信息
        """
        from app.models.user import User
        from app.models.organization import Department, Employee
        
        manager = self.db.query(User).filter(User.id == manager_id).first()
        if not manager or not manager.employee_id:
            return {
                'is_manager': False,
                'department_id': None,
                'configs': []
            }
        
        # 获取部门经理管理的部门
        dept = self.db.query(Department).filter(
            Department.manager_id == manager.employee_id,
            Department.is_active == True
        ).first()
        
        if not dept:
            return {
                'is_manager': False,
                'department_id': None,
                'configs': []
            }
        
        # 获取部门内所有工程师的岗位类型
        employees = self.db.query(Employee).filter(
            Employee.department_id == dept.id,
            Employee.is_active == True
        ).all()
        
        employee_ids = [e.id for e in employees]
        user_ids = [
            u.id for u in self.db.query(User).filter(
                User.employee_id.in_(employee_ids)
            ).all()
        ]
        
        # 获取部门内工程师的岗位类型分布
        profiles = self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id.in_(user_ids)
        ).all()
        
        job_type_distribution = {}
        for profile in profiles:
            job_type = profile.job_type
            if job_type not in job_type_distribution:
                job_type_distribution[job_type] = {
                    'count': 0,
                    'levels': {}
                }
            job_type_distribution[job_type]['count'] += 1
            level = profile.job_level or 'all'
            job_type_distribution[job_type]['levels'][level] = \
                job_type_distribution[job_type]['levels'].get(level, 0) + 1
        
        # 获取部门级别配置
        dept_configs = self.list_dimension_configs(
            department_id=dept.id,
            include_global=False
        )
        
        # 获取全局配置（作为参考）
        global_configs = self.list_dimension_configs(
            include_global=True
        )
        
        configs = []
        for job_type, dist in job_type_distribution.items():
            # 查找部门级别配置
            dept_config = next(
                (c for c in dept_configs if c.job_type == job_type),
                None
            )
            
            # 查找全局配置
            global_config = next(
                (c for c in global_configs if c.job_type == job_type and c.is_global),
                None
            )
            
            configs.append({
                'job_type': job_type,
                'job_type_name': {
                    'mechanical': '机械工程师',
                    'test': '测试工程师',
                    'electrical': '电气工程师',
                    'solution': '方案工程师'
                }.get(job_type, job_type),
                'engineer_count': dist['count'],
                'level_distribution': dist['levels'],
                'department_config': {
                    'id': dept_config.id if dept_config else None,
                    'technical_weight': dept_config.technical_weight if dept_config else None,
                    'execution_weight': dept_config.execution_weight if dept_config else None,
                    'cost_quality_weight': dept_config.cost_quality_weight if dept_config else None,
                    'knowledge_weight': dept_config.knowledge_weight if dept_config else None,
                    'collaboration_weight': dept_config.collaboration_weight if dept_config else None,
                    'approval_status': dept_config.approval_status if dept_config else None,
                    'effective_date': dept_config.effective_date.isoformat() if dept_config and dept_config.effective_date else None
                } if dept_config else None,
                'global_config': {
                    'id': global_config.id if global_config else None,
                    'technical_weight': global_config.technical_weight if global_config else None,
                    'execution_weight': global_config.execution_weight if global_config else None,
                    'cost_quality_weight': global_config.cost_quality_weight if global_config else None,
                    'knowledge_weight': global_config.knowledge_weight if global_config else None,
                    'collaboration_weight': global_config.collaboration_weight if global_config else None
                } if global_config else None
            })
        
        return {
            'is_manager': True,
            'department_id': dept.id,
            'department_name': dept.dept_name,
            'configs': configs
        }

    def approve_dimension_config(
        self,
        config_id: int,
        approver_id: int,
        approved: bool = True,
        approval_reason: Optional[str] = None
    ) -> EngineerDimensionConfig:
        """
        审批部门级别配置
        
        Args:
            config_id: 配置ID
            approver_id: 审批人ID（需要管理员权限）
            approved: 是否批准
            approval_reason: 审批理由
        """
        config = self.db.query(EngineerDimensionConfig).filter(
            EngineerDimensionConfig.id == config_id
        ).first()
        
        if not config:
            raise ValueError(f"配置不存在: {config_id}")
        
        if config.is_global:
            raise ValueError("全局配置无需审批")
        
        if config.approval_status != 'PENDING':
            raise ValueError(f"配置状态为{config.approval_status}，无法审批")
        
        # 验证审批人权限（需要管理员）
        approver = self.db.query(User).filter(User.id == approver_id).first()
        if not approver:
            raise ValueError("审批人不存在")
        
        # 检查是否是管理员（通过is_superuser或角色判断）
        is_admin = getattr(approver, 'is_superuser', False)
        if not is_admin:
            # 检查是否有管理员角色
            from app.models.user import UserRole
            admin_roles = self.db.query(UserRole).join(
                'role', UserRole.user_id == approver_id
            ).filter(
                or_(
                    UserRole.role.has(role_code='admin'),
                    UserRole.role.has(role_code='super_admin')
                )
            ).first()
            if not admin_roles:
                raise ValueError("只有管理员可以审批配置")
        
        config.approval_status = 'APPROVED' if approved else 'REJECTED'
        config.approval_reason = approval_reason
        
        self.db.commit()
        self.db.refresh(config)
        
        return config

    def get_pending_approvals(
        self
    ) -> List[EngineerDimensionConfig]:
        """获取待审批的部门级别配置"""
        return self.db.query(EngineerDimensionConfig).filter(
            EngineerDimensionConfig.is_global == False,
            EngineerDimensionConfig.approval_status == 'PENDING'
        ).order_by(desc(EngineerDimensionConfig.created_at)).all()

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
        elif job_type == 'solution':
            return self._calculate_solution_score(engineer_id, period)
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
        config: EngineerDimensionConfig,
        job_type: Optional[str] = None
    ) -> Decimal:
        """计算加权总分（支持方案工程师的方案成功率维度）"""
        # 如果是方案工程师，使用特殊权重
        if job_type == 'solution' and dimension_scores.solution_success_score is not None:
            # 方案工程师权重：技术能力25% + 方案成功率30% + 项目执行20% + 知识沉淀15% + 团队协作10%
            total = (
                dimension_scores.technical_score * 25 / 100 +
                dimension_scores.solution_success_score * 30 / 100 +
                dimension_scores.execution_score * 20 / 100 +
                dimension_scores.knowledge_score * 15 / 100 +
                dimension_scores.collaboration_score * 10 / 100
            )
        else:
            # 其他工程师使用配置的权重
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

    def _calculate_solution_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算方案工程师得分（六维：技术能力+方案成功率+项目执行+成本/质量+知识沉淀+团队协作）"""
        from app.models.presale import PresaleSolution, PresaleSupportTicket
        from app.models.sales import Contract
        
        # 1. 方案成功率维度（30%权重）
        solutions = self.db.query(PresaleSolution).filter(
            PresaleSolution.author_id == engineer_id,
            PresaleSolution.created_at.between(period.start_date, period.end_date)
        ).all()
        
        if not solutions:
            win_rate_score = Decimal('60.0')  # 默认值
            approval_rate_score = Decimal('60.0')
            quality_score = Decimal('60.0')
        else:
            # 方案中标率（支持高价值方案加权、低价值方案降权）
            won_solutions = []
            high_value_won = 0  # 高价值方案中标数（>200万）
            low_value_won = 0   # 低价值方案中标数（<50万）
            normal_value_won = 0  # 正常价值方案中标数
            
            for solution in solutions:
                # 检查是否关联了合同（中标）
                contract_amount = Decimal('0')
                if solution.opportunity_id:
                    contract = self.db.query(Contract).filter(
                        Contract.opportunity_id == solution.opportunity_id,
                        Contract.status == 'SIGNED'
                    ).first()
                    if contract:
                        won_solutions.append(solution)
                        contract_amount = contract.contract_amount or Decimal('0')
                        
                        # 分类统计
                        if contract_amount > Decimal('2000000'):  # >200万
                            high_value_won += 1
                        elif contract_amount < Decimal('500000'):  # <50万
                            low_value_won += 1
                        else:
                            normal_value_won += 1
            
            # 计算加权中标率
            total_won = len(won_solutions)
            if total_won > 0:
                # 高价值方案权重×1.2，低价值方案权重×0.8
                weighted_won = high_value_won * Decimal('1.2') + low_value_won * Decimal('0.8') + normal_value_won
                weighted_win_rate = (weighted_won / len(solutions) * 100) if solutions else 0
            else:
                weighted_win_rate = 0
            
            win_rate = total_won / len(solutions) * 100 if solutions else 0
            win_rate_score = min(Decimal(str(weighted_win_rate)) / 40 * 100, 120)  # 目标40%，使用加权值
            
            # 方案通过率
            approved_solutions = [s for s in solutions if s.review_status == 'APPROVED']
            approval_rate = len(approved_solutions) / len(solutions) * 100 if solutions else 0
            approval_rate_score = min(Decimal(str(approval_rate)) / 80 * 100, 120)  # 目标80%
            
            # 方案质量评分（从工单满意度获取，支持高质量方案补偿）
            ticket_ids = [s.ticket_id for s in solutions if s.ticket_id]
            high_quality_unwon = 0  # 高质量但未中标的方案数
            if ticket_ids:
                tickets = self.db.query(PresaleSupportTicket).filter(
                    PresaleSupportTicket.id.in_(ticket_ids),
                    PresaleSupportTicket.satisfaction_score.isnot(None)
                ).all()
                if tickets:
                    satisfaction_scores = []
                    for ticket in tickets:
                        score = ticket.satisfaction_score
                        satisfaction_scores.append(score)
                        
                        # 检查是否高质量但未中标（质量评分≥4.5但未中标）
                        if score >= 4.5:
                            # 检查对应的方案是否中标
                            solution = next((s for s in solutions if s.ticket_id == ticket.id), None)
                            if solution and solution not in won_solutions:
                                high_quality_unwon += 1
                    
                    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
                    quality_score = Decimal(str(avg_satisfaction)) / 5 * 100  # 5分制转百分制
                else:
                    quality_score = Decimal('75.0')
            else:
                quality_score = Decimal('75.0')
            
            # 高质量方案补偿（未中标但质量评分≥4.5，给予50%基础分补偿）
            if high_quality_unwon > 0:
                compensation = Decimal(str(high_quality_unwon)) * Decimal('0.5') * Decimal('10')  # 每个补偿5分
                quality_score = min(quality_score + compensation, 100)
        
        solution_success_score = (
            win_rate_score * Decimal('0.5') +
            approval_rate_score * Decimal('0.3') +
            quality_score * Decimal('0.2')
        )
        
        # 2. 技术能力维度（25%权重）
        # 方案技术可行性（从交付项目的ECN记录统计）
        # 简化计算，使用方案通过率作为技术能力指标
        technical_score = approval_rate_score
        
        # 3. 项目执行维度（20%权重）
        # 方案交付及时率
        on_time_solutions = sum(
            1 for s in solutions
            if s.ticket_id and s.created_at
        )
        delivery_rate = on_time_solutions / len(solutions) * 100 if solutions else 90
        execution_score = Decimal(str(min(delivery_rate / 90 * 100, 120)))  # 目标90%
        
        # 4. 成本/质量维度（使用cost_quality_score，但方案工程师权重较低）
        cost_quality_score = Decimal('75.0')  # 简化计算
        
        # 5. 知识沉淀维度（15%权重）
        # 方案模板贡献
        from app.models.presale import PresaleSolutionTemplate
        templates = self.db.query(PresaleSolutionTemplate).filter(
            PresaleSolutionTemplate.created_by == engineer_id,
            PresaleSolutionTemplate.created_at.between(period.start_date, period.end_date)
        ).count()
        
        knowledge_score = min(Decimal('50') + Decimal(str(templates)) * Decimal('15'), 100)
        
        # 6. 团队协作维度（10%权重）
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)
        
        return EngineerDimensionScore(
            technical_score=technical_score,
            execution_score=execution_score,
            cost_quality_score=cost_quality_score,
            knowledge_score=knowledge_score,
            collaboration_score=collaboration_avg,
            solution_success_score=solution_success_score
        )
