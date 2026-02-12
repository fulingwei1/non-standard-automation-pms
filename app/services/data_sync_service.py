# -*- coding: utf-8 -*-
"""
项目与销售模块数据同步服务

实现项目与销售模块的数据双向同步，确保合同金额、收款计划等数据一致性
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.project import Customer, Project, ProjectPaymentPlan
from app.models.sales import Contract

logger = logging.getLogger(__name__)


class DataSyncService:
    """数据同步服务"""

    def __init__(self, db: Session):
        self.db = db

    def sync_contract_to_project(self, contract_id: int) -> Dict[str, Any]:
        """
        同步合同数据到项目

        当合同金额、交期等信息变更时，自动更新项目信息

        Args:
            contract_id: 合同ID

        Returns:
            dict: 同步结果
        """
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return {"success": False, "message": "合同不存在"}

        if not contract.project_id:
            return {"success": False, "message": "合同未关联项目"}

        project = self.db.query(Project).filter(Project.id == contract.project_id).first()
        if not project:
            return {"success": False, "message": "项目不存在"}

        updated_fields = []

        # 同步合同金额
        if contract.contract_amount and contract.contract_amount != project.contract_amount:
            project.contract_amount = contract.contract_amount
            updated_fields.append("contract_amount")

        # 同步合同日期
        if contract.signed_date and contract.signed_date != project.contract_date:
            project.contract_date = contract.signed_date
            updated_fields.append("contract_date")

        # 同步交期（如果有）
        # 优先从 Contract 的 delivery_deadline 字段获取（如果存在）
        # 否则从关联的 QuoteVersion 获取 delivery_date
        delivery_date = None
        if hasattr(contract, 'delivery_deadline') and contract.delivery_deadline:
            delivery_date = contract.delivery_deadline
        elif contract.quote_version and hasattr(contract.quote_version, 'delivery_date') and contract.quote_version.delivery_date:
            delivery_date = contract.quote_version.delivery_date
        
        if delivery_date and delivery_date != project.planned_end_date:
            project.planned_end_date = delivery_date
            updated_fields.append("planned_end_date")

        if updated_fields:
            self.db.add(project)
            # 注意：不在这里 commit，由调用方控制事务，确保合同和项目更新在同一事务中
            return {
                "success": True,
                "message": f"已同步字段：{', '.join(updated_fields)}",
                "updated_fields": updated_fields
            }

        return {"success": True, "message": "数据已是最新，无需同步"}

    def sync_payment_plans_from_contract(self, contract_id: int) -> Dict[str, Any]:
        """
        同步收款计划从合同到项目

        当合同收款计划变更时，自动更新项目收款计划

        Args:
            contract_id: 合同ID

        Returns:
            dict: 同步结果
        """
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return {"success": False, "message": "合同不存在"}

        if not contract.project_id:
            return {"success": False, "message": "合同未关联项目"}

        # 查找合同的收款计划（从合同交付物或合同配置中获取）
        # 这里假设收款计划已经通过 _generate_payment_plans_from_contract 生成
        # 如果需要从合同配置同步，可以在这里实现

        existing_plans = self.db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.contract_id == contract_id
        ).all()

        return {
            "success": True,
            "message": f"已找到 {len(existing_plans)} 个收款计划",
            "plan_count": len(existing_plans)
        }

    def sync_project_to_contract(self, project_id: int) -> Dict[str, Any]:
        """
        同步项目数据到合同

        当项目进度、状态更新时，自动更新合同执行状态

        Args:
            project_id: 项目ID

        Returns:
            dict: 同步结果
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"success": False, "message": "项目不存在"}

        # 查找关联的合同
        contracts = self.db.query(Contract).filter(Contract.project_id == project_id).all()
        if not contracts:
            return {"success": False, "message": "项目未关联合同"}

        updated_contracts = []

        for contract in contracts:
            updated = False

            # 更新合同执行状态（如果有相关字段）
            # 这里可以根据项目阶段更新合同状态
            if project.stage == "S9" and project.status == "ST30":
                # 项目已结项，可以更新合同状态为已完成
                if contract.status != "COMPLETED":
                    contract.status = "COMPLETED"
                    updated = True

            if updated:
                self.db.add(contract)
                updated_contracts.append(contract.id)

        if updated_contracts:
            self.db.commit()
            return {
                "success": True,
                "message": f"已更新 {len(updated_contracts)} 个合同",
                "updated_contracts": updated_contracts
            }

        return {"success": True, "message": "数据已是最新，无需同步"}

    def get_sync_status(self, project_id: Optional[int] = None, contract_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取数据同步状态

        Args:
            project_id: 项目ID（可选）
            contract_id: 合同ID（可选）

        Returns:
            dict: 同步状态信息
        """
        if project_id:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "message": "项目不存在"}

            contracts = self.db.query(Contract).filter(Contract.project_id == project_id).all()

            return {
                "success": True,
                "project_id": project_id,
                "contract_count": len(contracts),
                "contracts": [
                    {
                        "contract_id": c.id,
                        "contract_code": c.contract_code,
                        "contract_amount": float(c.contract_amount or 0),
                        "project_amount": float(project.contract_amount or 0),
                        "amount_synced": c.contract_amount == project.contract_amount,
                    }
                    for c in contracts
                ]
            }

        if contract_id:
            contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return {"success": False, "message": "合同不存在"}

            if not contract.project_id:
                return {"success": True, "contract_id": contract_id, "project_id": None, "synced": False}

            project = self.db.query(Project).filter(Project.id == contract.project_id).first()
            if not project:
                return {"success": False, "message": "关联的项目不存在"}

            return {
                "success": True,
                "contract_id": contract_id,
                "project_id": contract.project_id,
                "synced": True,
                "amount_synced": contract.contract_amount == project.contract_amount,
                "date_synced": contract.signed_date == project.contract_date,
            }

        return {"success": False, "message": "请提供 project_id 或 contract_id"}

    def sync_customer_to_projects(self, customer_id: int) -> Dict[str, Any]:
        """
        同步客户信息到所有关联的项目

        当客户信息变更时，自动更新所有关联项目的冗余客户信息字段

        Args:
            customer_id: 客户ID

        Returns:
            dict: 同步结果
        """
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "message": "客户不存在"}

        # 查找所有关联的项目
        projects = self.db.query(Project).filter(Project.customer_id == customer_id).all()
        if not projects:
            return {"success": True, "message": "该客户下没有关联项目", "updated_count": 0}

        updated_projects = []
        updated_fields_list = []

        for project in projects:
            updated_fields = []

            # 同步客户名称
            if customer.customer_name and customer.customer_name != project.customer_name:
                project.customer_name = customer.customer_name
                updated_fields.append("customer_name")

            # 同步客户联系人
            if customer.contact_person and customer.contact_person != project.customer_contact:
                project.customer_contact = customer.contact_person
                updated_fields.append("customer_contact")

            # 同步联系电话
            if customer.contact_phone and customer.contact_phone != project.customer_phone:
                project.customer_phone = customer.contact_phone
                updated_fields.append("customer_phone")

            if updated_fields:
                self.db.add(project)
                updated_projects.append(project.id)
                updated_fields_list.extend(updated_fields)

        if updated_projects:
            # 注意：不在这里 commit，由调用方控制事务
            return {
                "success": True,
                "message": f"已同步 {len(updated_projects)} 个项目的客户信息",
                "updated_count": len(updated_projects),
                "updated_projects": updated_projects,
                "updated_fields": list(set(updated_fields_list))
            }

        return {"success": True, "message": "所有项目的客户信息已是最新", "updated_count": 0}

    def sync_customer_to_contracts(self, customer_id: int) -> Dict[str, Any]:
        """
        同步客户信息到所有关联的合同

        当客户信息变更时，自动更新所有关联合同的冗余客户信息字段（如果有）

        Args:
            customer_id: 客户ID

        Returns:
            dict: 同步结果
        """
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "message": "客户不存在"}

        # 查找所有关联的合同
        contracts = self.db.query(Contract).filter(Contract.customer_id == customer_id).all()
        if not contracts:
            return {"success": True, "message": "该客户下没有关联合同", "updated_count": 0}

        updated_contracts = []
        updated_fields_list = []

        for contract in contracts:
            updated_fields = []

            # 检查合同是否有冗余的客户信息字段
            # 如果合同模型有 customer_name 字段，则同步
            if hasattr(contract, 'customer_name'):
                if customer.customer_name and customer.customer_name != contract.customer_name:
                    contract.customer_name = customer.customer_name
                    updated_fields.append("customer_name")

            # 如果合同模型有 contact_person 字段，则同步
            if hasattr(contract, 'contact_person'):
                if customer.contact_person and customer.contact_person != contract.contact_person:
                    contract.contact_person = customer.contact_person
                    updated_fields.append("contact_person")

            # 如果合同模型有 contact_phone 字段，则同步
            if hasattr(contract, 'contact_phone'):
                if customer.contact_phone and customer.contact_phone != contract.contact_phone:
                    contract.contact_phone = customer.contact_phone
                    updated_fields.append("contact_phone")

            if updated_fields:
                self.db.add(contract)
                updated_contracts.append(contract.id)
                updated_fields_list.extend(updated_fields)

        if updated_contracts:
            # 注意：不在这里 commit，由调用方控制事务
            return {
                "success": True,
                "message": f"已同步 {len(updated_contracts)} 个合同的客户信息",
                "updated_count": len(updated_contracts),
                "updated_contracts": updated_contracts,
                "updated_fields": list(set(updated_fields_list))
            }

        return {"success": True, "message": "所有合同的客户信息已是最新，或合同模型无冗余字段", "updated_count": 0}
