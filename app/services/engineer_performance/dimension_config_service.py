# -*- coding: utf-8 -*-
"""
五维权重配置服务
负责绩效评价指标配置的管理
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models.engineer_performance import EngineerDimensionConfig
from app.models.organization import Department, Employee
from app.models.user import User, UserRole
from app.schemas.engineer_performance import DimensionConfigCreate


class DimensionConfigService:
    """五维权重配置服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_config(
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
            dept_config = self._get_department_config(
                job_type, job_level, effective_date, department_id
            )
            if dept_config:
                return dept_config

        # 回退到全局配置
        return self._get_global_config(job_type, job_level, effective_date)

    def _get_department_config(
        self, job_type: str, job_level: Optional[str],
        effective_date: date, department_id: int
    ) -> Optional[EngineerDimensionConfig]:
        """获取部门级别配置"""
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
        return dept_query.filter(
            EngineerDimensionConfig.job_level.is_(None)
        ).order_by(desc(EngineerDimensionConfig.effective_date)).first()

    def _get_global_config(
        self, job_type: str, job_level: Optional[str],
        effective_date: date
    ) -> Optional[EngineerDimensionConfig]:
        """获取全局配置"""
        query = self.db.query(EngineerDimensionConfig).filter(
            EngineerDimensionConfig.job_type == job_type,
            EngineerDimensionConfig.is_global,
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

    def create_config(
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
            self._validate_department_manager_permission(department_id, operator_id)

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

    def _validate_department_manager_permission(
        self, department_id: int, operator_id: int
    ) -> None:
        """验证部门经理权限"""
        operator = self.db.query(User).filter(User.id == operator_id).first()
        if not operator or not operator.employee_id:
            raise ValueError("操作人信息不完整")

        dept = self.db.query(Department).filter(
            Department.id == department_id,
            Department.manager_id == operator.employee_id,
            Department.is_active
        ).first()

        if not dept:
            raise ValueError("无权限为该部门创建配置，只有部门经理可以创建部门级别配置")

    def list_configs(
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

    def get_department_configs(self, manager_id: int) -> Dict[str, Any]:
        """
        获取部门经理管理的部门的评价指标配置

        Args:
            manager_id: 部门经理ID

        Returns:
            部门配置信息
        """
        from app.models.engineer_performance import EngineerProfile

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
            Department.is_active
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
            Employee.is_active
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

        job_type_distribution = self._analyze_job_type_distribution(profiles)

        # 获取部门级别配置和全局配置
        dept_configs = self.list_configs(
            department_id=dept.id,
            include_global=False
        )
        global_configs = self.list_configs(include_global=True)

        configs = self._build_config_list(
            job_type_distribution, dept_configs, global_configs
        )

        return {
            'is_manager': True,
            'department_id': dept.id,
            'department_name': dept.dept_name,
            'configs': configs
        }

    def _analyze_job_type_distribution(
        self, profiles: List
    ) -> Dict[str, Dict]:
        """分析岗位类型分布"""
        distribution = {}
        for profile in profiles:
            job_type = profile.job_type
            if job_type not in distribution:
                distribution[job_type] = {
                    'count': 0,
                    'levels': {}
                }
            distribution[job_type]['count'] += 1
            level = profile.job_level or 'all'
            distribution[job_type]['levels'][level] = \
                distribution[job_type]['levels'].get(level, 0) + 1
        return distribution

    def _build_config_list(
        self, job_type_distribution: Dict,
        dept_configs: List, global_configs: List
    ) -> List[Dict]:
        """构建配置列表"""
        job_type_names = {
            'mechanical': '机械工程师',
            'test': '测试工程师',
            'electrical': '电气工程师',
            'solution': '方案工程师'
        }

        configs = []
        for job_type, dist in job_type_distribution.items():
            dept_config = next(
                (c for c in dept_configs if c.job_type == job_type),
                None
            )
            global_config = next(
                (c for c in global_configs if c.job_type == job_type and c.is_global),
                None
            )

            configs.append({
                'job_type': job_type,
                'job_type_name': job_type_names.get(job_type, job_type),
                'engineer_count': dist['count'],
                'level_distribution': dist['levels'],
                'department_config': self._format_config(dept_config),
                'global_config': self._format_config(global_config)
            })

        return configs

    def _format_config(self, config) -> Optional[Dict]:
        """格式化配置信息"""
        if not config:
            return None

        return {
            'id': config.id,
            'technical_weight': config.technical_weight,
            'execution_weight': config.execution_weight,
            'cost_quality_weight': config.cost_quality_weight,
            'knowledge_weight': config.knowledge_weight,
            'collaboration_weight': config.collaboration_weight,
            'approval_status': getattr(config, 'approval_status', None),
            'effective_date': config.effective_date.isoformat() if config.effective_date else None
        }

    def approve_config(
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
        self._validate_admin_permission(approver_id)

        config.approval_status = 'APPROVED' if approved else 'REJECTED'
        config.approval_reason = approval_reason

        self.db.commit()
        self.db.refresh(config)

        return config

    def _validate_admin_permission(self, approver_id: int) -> None:
        """验证管理员权限"""
        approver = self.db.query(User).filter(User.id == approver_id).first()
        if not approver:
            raise ValueError("审批人不存在")

        # 检查是否是管理员（通过is_superuser或角色判断）
        is_admin = getattr(approver, 'is_superuser', False)
        if not is_admin:
            # 检查是否有管理员角色
            admin_roles = self.db.query(UserRole).filter(
                UserRole.user_id == approver_id
            ).all()

            for user_role in admin_roles:
                if hasattr(user_role, 'role') and user_role.role:
                    role_code = getattr(user_role.role, 'role_code', None)
                    if role_code in ('admin', 'super_admin'):
                        return

            raise ValueError("只有管理员可以审批配置")

    def get_pending_approvals(self) -> List[EngineerDimensionConfig]:
        """获取待审批的部门级别配置"""
        return self.db.query(EngineerDimensionConfig).filter(
            EngineerDimensionConfig.is_global == False,
            EngineerDimensionConfig.approval_status == 'PENDING'
        ).order_by(desc(EngineerDimensionConfig.created_at)).all()
