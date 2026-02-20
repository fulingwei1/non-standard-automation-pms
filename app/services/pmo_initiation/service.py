# -*- coding: utf-8 -*-
"""
PMO 立项管理服务层
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.models.pmo import PmoProjectInitiation
from app.models.project import Customer, Project
from app.models.user import User
from app.schemas.pmo import (
    InitiationApproveRequest,
    InitiationCreate,
    InitiationRejectRequest,
    InitiationUpdate,
)
from app.utils.domain_codes import pmo as pmo_codes


class PmoInitiationService:
    """PMO 立项管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_initiations(
        self,
        offset: int,
        limit: int,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        applicant_id: Optional[int] = None,
    ) -> Tuple[List[PmoProjectInitiation], int]:
        """
        获取立项申请列表

        Args:
            offset: 偏移量
            limit: 每页数量
            keyword: 关键词搜索
            status: 状态筛选
            applicant_id: 申请人ID筛选

        Returns:
            (立项申请列表, 总数)
        """
        query = self.db.query(PmoProjectInitiation)

        # 应用关键词搜索
        query = apply_keyword_filter(
            query, PmoProjectInitiation, keyword, ["application_no", "project_name"]
        )

        # 状态筛选
        if status:
            query = query.filter(PmoProjectInitiation.status == status)

        # 申请人筛选
        if applicant_id:
            query = query.filter(PmoProjectInitiation.applicant_id == applicant_id)

        # 计算总数
        total = query.count()

        # 分页查询
        initiations = apply_pagination(
            query.order_by(desc(PmoProjectInitiation.created_at)), offset, limit
        ).all()

        return initiations, total

    def get_initiation(self, initiation_id: int) -> Optional[PmoProjectInitiation]:
        """
        获取立项申请详情

        Args:
            initiation_id: 立项申请ID

        Returns:
            立项申请对象，不存在返回 None
        """
        return (
            self.db.query(PmoProjectInitiation)
            .filter(PmoProjectInitiation.id == initiation_id)
            .first()
        )

    def create_initiation(
        self, initiation_in: InitiationCreate, current_user: User
    ) -> PmoProjectInitiation:
        """
        创建立项申请

        Args:
            initiation_in: 创建数据
            current_user: 当前用户

        Returns:
            创建的立项申请对象
        """
        initiation = PmoProjectInitiation(
            application_no=pmo_codes.generate_initiation_no(self.db),
            project_name=initiation_in.project_name,
            project_type=initiation_in.project_type,
            project_level=initiation_in.project_level,
            customer_name=initiation_in.customer_name,
            contract_no=initiation_in.contract_no,
            contract_amount=initiation_in.contract_amount,
            required_start_date=initiation_in.required_start_date,
            required_end_date=initiation_in.required_end_date,
            technical_solution_id=initiation_in.technical_solution_id,
            requirement_summary=initiation_in.requirement_summary,
            technical_difficulty=initiation_in.technical_difficulty,
            estimated_hours=initiation_in.estimated_hours,
            resource_requirements=initiation_in.resource_requirements,
            risk_assessment=initiation_in.risk_assessment,
            applicant_id=current_user.id,
            applicant_name=current_user.real_name or current_user.username,
            apply_time=datetime.now(),
            status="DRAFT",
        )

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def update_initiation(
        self, initiation_id: int, initiation_in: InitiationUpdate
    ) -> PmoProjectInitiation:
        """
        更新立项申请

        Args:
            initiation_id: 立项申请ID
            initiation_in: 更新数据

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许修改
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status != "DRAFT":
            raise ValueError("只有草稿状态的申请才能修改")

        update_data = initiation_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(initiation, field, value)

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def submit_initiation(self, initiation_id: int) -> PmoProjectInitiation:
        """
        提交立项评审

        Args:
            initiation_id: 立项申请ID

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许提交
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status != "DRAFT":
            raise ValueError("只有草稿状态的申请才能提交")

        initiation.status = "SUBMITTED"
        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def approve_initiation(
        self,
        initiation_id: int,
        approve_request: InitiationApproveRequest,
        current_user: User,
    ) -> PmoProjectInitiation:
        """
        立项评审通过

        Args:
            initiation_id: 立项申请ID
            approve_request: 审批请求数据
            current_user: 当前用户

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许审批
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status not in ["SUBMITTED", "REVIEWING"]:
            raise ValueError("只有已提交或评审中的申请才能审批")

        # 更新审批信息
        initiation.status = "APPROVED"
        initiation.review_result = approve_request.review_result
        initiation.approved_pm_id = approve_request.approved_pm_id
        initiation.approved_level = approve_request.approved_level
        initiation.approved_at = datetime.now()
        initiation.approved_by = current_user.id

        # 如果指定了项目经理，创建项目
        if approve_request.approved_pm_id:
            project = self._create_project_from_initiation(
                initiation, approve_request.approved_pm_id
            )
            initiation.project_id = project.id

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def reject_initiation(
        self,
        initiation_id: int,
        reject_request: InitiationRejectRequest,
        current_user: User,
    ) -> PmoProjectInitiation:
        """
        立项评审驳回

        Args:
            initiation_id: 立项申请ID
            reject_request: 驳回请求数据
            current_user: 当前用户

        Returns:
            更新后的立项申请对象

        Raises:
            ValueError: 立项申请不存在或状态不允许驳回
        """
        initiation = self.get_initiation(initiation_id)
        if not initiation:
            raise ValueError("立项申请不存在")

        if initiation.status not in ["SUBMITTED", "REVIEWING"]:
            raise ValueError("只有已提交或评审中的申请才能驳回")

        initiation.status = "REJECTED"
        initiation.review_result = reject_request.review_result
        initiation.approved_at = datetime.now()
        initiation.approved_by = current_user.id

        self.db.add(initiation)
        self.db.commit()
        self.db.refresh(initiation)

        return initiation

    def _create_project_from_initiation(
        self, initiation: PmoProjectInitiation, pm_id: int
    ) -> Project:
        """
        从立项申请创建项目（内部方法）

        Args:
            initiation: 立项申请对象
            pm_id: 项目经理ID

        Returns:
            创建的项目对象
        """
        # 生成项目编码
        today = date.today()
        project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:03d}"

        # 检查项目编码是否已存在
        existing = (
            self.db.query(Project).filter(Project.project_code == project_code).first()
        )
        if existing:
            project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:04d}"

        # 查找或创建客户
        customer = (
            self.db.query(Customer)
            .filter(Customer.customer_name == initiation.customer_name)
            .first()
        )
        customer_id = customer.id if customer else None

        # 创建项目
        project = Project(
            project_code=project_code,
            project_name=initiation.project_name,
            customer_id=customer_id,
            customer_name=initiation.customer_name,
            contract_no=initiation.contract_no,
            contract_amount=initiation.contract_amount or Decimal("0"),
            contract_date=initiation.required_start_date,
            planned_start_date=initiation.required_start_date,
            planned_end_date=initiation.required_end_date,
            pm_id=pm_id,
            project_type=initiation.project_type,
            stage="S1",
            status="ST01",
            health="H1",
        )

        # 填充项目经理信息
        pm = self.db.query(User).filter(User.id == pm_id).first()
        if pm:
            project.pm_name = pm.real_name or pm.username

        self.db.add(project)
        self.db.flush()

        # 初始化项目阶段
        from app.utils.project_utils import init_project_stages

        init_project_stages(self.db, project.id)

        return project
