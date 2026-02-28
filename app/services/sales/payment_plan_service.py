# -*- coding: utf-8 -*-
"""
收款计划服务

将原来157行的复杂函数拆分为多个小函数，提高可维护性和可测试性
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.models.project import Project, ProjectMilestone, ProjectPaymentPlan
from app.models.sales import Contract


class PaymentPlanService:
    """收款计划服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_payment_plans_from_contract(self, contract: Contract) -> List[ProjectPaymentPlan]:
        """
        根据合同自动生成收款计划

        默认规则：
        - 预付款：30%（合同签订后）
        - 发货款：40%（发货里程碑）
        - 验收款：25%（验收里程碑）
        - 质保款：5%（质保结束）
        """
        if not self._validate_contract(contract):
            return []

        payment_configs = self._get_payment_configurations()
        plans = []

        for config in payment_configs:
            plan = self._create_payment_plan(contract, config)
            if plan:
                plans.append(plan)

        self.db.flush()
        return plans

    def _validate_contract(self, contract: Contract) -> bool:
        """验证合同是否有效"""
        if not contract.project_id:
            return False

        # 检查项目是否存在
        project = self.db.query(Project).filter(Project.id == contract.project_id).first()
        if not project:
            return False

        # 检查合同金额
        contract_amount = float(contract.contract_amount or 0)
        if contract_amount <= 0:
            return False

        # 检查是否已有收款计划
        existing_plans = self.db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.contract_id == contract.id
        ).count()
        return existing_plans == 0

    def _get_payment_configurations(self) -> List[Dict[str, Any]]:
        """获取收款计划配置"""
        return [
            {
                "payment_no": 1,
                "payment_name": "预付款",
                "payment_type": "ADVANCE",
                "payment_ratio": 30.0,
                "trigger_milestone": "合同签订",
                "trigger_condition": "合同签订后"
            },
            {
                "payment_no": 2,
                "payment_name": "发货款",
                "payment_type": "DELIVERY",
                "payment_ratio": 40.0,
                "trigger_milestone": "发货",
                "trigger_condition": "设备发货后"
            },
            {
                "payment_no": 3,
                "payment_name": "验收款",
                "payment_type": "ACCEPTANCE",
                "payment_ratio": 25.0,
                "trigger_milestone": "终验通过",
                "trigger_condition": "终验通过后"
            },
            {
                "payment_no": 4,
                "payment_name": "质保款",
                "payment_type": "WARRANTY",
                "payment_ratio": 5.0,
                "trigger_milestone": "质保结束",
                "trigger_condition": "质保期结束后"
            }
        ]

    def _create_payment_plan(self, contract: Contract, config: Dict[str, Any]) -> Optional[ProjectPaymentPlan]:
        """创建单个收款计划"""
        if not contract.project_id:
            return None

        project = self.db.query(Project).filter(Project.id == contract.project_id).first()
        if not project:
            return None

        # 计算计划金额
        contract_amount = float(contract.contract_amount or 0)
        planned_amount = contract_amount * config["payment_ratio"] / 100

        # 计算计划收款日期
        planned_date = self._calculate_planned_date(contract, project, config["payment_no"])

        # 查找关联里程碑
        milestone_id = self._find_milestone_id(contract.project_id, config["payment_no"])

        return ProjectPaymentPlan(
            project_id=contract.project_id,
            contract_id=contract.id,
            payment_no=config["payment_no"],
            payment_name=config["payment_name"],
            payment_type=config["payment_type"],
            payment_ratio=config["payment_ratio"],
            planned_amount=planned_amount,
            planned_date=planned_date,
            milestone_id=milestone_id,
            trigger_milestone=config["trigger_milestone"],
            trigger_condition=config["trigger_condition"],
            status="PENDING"
        )

    def _calculate_planned_date(self, contract: Contract, project: Project, payment_no: int) -> Optional[datetime]:
        """计算计划收款日期"""
        if payment_no == 1:
            # 预付款：合同签订后7天
            return contract.signing_date + timedelta(days=7) if contract.signing_date else None
        elif payment_no == 2:
            # 发货款：预计项目中期
            if project.planned_end_date and project.planned_start_date:
                days = (project.planned_end_date - project.planned_start_date).days
                return project.planned_start_date + timedelta(days=int(days * 0.6)) if days > 0 else None
        elif payment_no == 3:
            # 验收款：项目结束前
            return project.planned_end_date
        elif payment_no == 4:
            # 质保款：项目结束后1年
            if project.planned_end_date:
                return project.planned_end_date + timedelta(days=365)

        return None

    def _find_milestone_id(self, project_id: int, payment_no: int) -> Optional[int]:
        """根据付款阶段查找对应的里程碑ID"""
        if payment_no == 1:
            return self._find_advance_payment_milestone(project_id)
        elif payment_no == 2:
            return self._find_delivery_payment_milestone(project_id)
        elif payment_no == 3:
            return self._find_acceptance_payment_milestone(project_id)
        elif payment_no == 4:
            return self._find_warranty_payment_milestone(project_id)
        return None

    def _find_advance_payment_milestone(self, project_id: int) -> Optional[int]:
        """查找预付款里程碑"""
        keyword_query = apply_keyword_filter(
            self.db.query(ProjectMilestone.id),
            ProjectMilestone,
            ["合同", "签订", "立项"],
            "milestone_name",
            use_ilike=False,
        )
        milestone = self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.project_id == project_id,
                or_(
                    ProjectMilestone.id.in_(keyword_query),
                    ProjectMilestone.milestone_type == "GATE"
                )
            )
        ).order_by(ProjectMilestone.planned_date.asc()).first()

        return milestone.id if milestone else None

    def _find_delivery_payment_milestone(self, project_id: int) -> Optional[int]:
        """查找发货款里程碑"""
        keyword_query = apply_keyword_filter(
            self.db.query(ProjectMilestone.id),
            ProjectMilestone,
            ["发货", "发运", "包装"],
            "milestone_name",
            use_ilike=False,
        )
        milestone = self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.project_id == project_id,
                or_(
                    ProjectMilestone.id.in_(keyword_query),
                    ProjectMilestone.milestone_type == "DELIVERY"
                )
            )
        ).order_by(ProjectMilestone.planned_date.asc()).first()

        return milestone.id if milestone else None

    def _find_acceptance_payment_milestone(self, project_id: int) -> Optional[int]:
        """查找验收款里程碑"""
        keyword_query = apply_keyword_filter(
            self.db.query(ProjectMilestone.id),
            ProjectMilestone,
            ["验收", "终验", "FAT", "SAT"],
            "milestone_name",
            use_ilike=False,
        )
        milestone = self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.project_id == project_id,
                or_(
                    ProjectMilestone.id.in_(keyword_query),
                    ProjectMilestone.milestone_type == "GATE"
                )
            )
        ).order_by(ProjectMilestone.planned_date.desc()).first()  # 取最晚的验收里程碑

        return milestone.id if milestone else None

    def _find_warranty_payment_milestone(self, project_id: int) -> Optional[int]:
        """查找质保款里程碑"""
        keyword_query = apply_keyword_filter(
            self.db.query(ProjectMilestone.id),
            ProjectMilestone,
            ["质保", "结项", "完成"],
            "milestone_name",
            use_ilike=False,
        )
        milestone = self.db.query(ProjectMilestone).filter(
            and_(
                ProjectMilestone.project_id == project_id,
                or_(
                    ProjectMilestone.id.in_(keyword_query)
                )
            )
        ).order_by(ProjectMilestone.planned_date.desc()).first()

        return milestone.id if milestone else None
