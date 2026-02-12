# -*- coding: utf-8 -*-
"""
合同服务 - 实现合同→项目自动生成功能
从合同创建项目，自动关联付款节点到里程碑

功能说明：
1. 从合同创建项目
2. 将合同中的付款节点自动关联到项目里程碑
3. 同步合同金额到项目
4. 同步SOW/验收标准到项目
"""

from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import Column, Date, Integer, Numeric, String
from sqlalchemy.orm import relationship, selectinload

from app.models.base import Base
from app.models.project import (
    Project,
    ProjectMilestone,
    Customer,
)
from app.models.sales.contracts import Contract


class ContractService:
    """合同服务类"""

    @staticmethod
    async def create_project_from_contract(
        db: AsyncSession, contract_id: int
    ) -> Dict[str, Any]:
        """
        从合同创建项目，自动绑定付款节点到里程碑

        Args:
            db: 数据库会话
            contract_id: 合同ID

        Returns:
            包含项目ID、收款计划数量等的字典

        Raises:
            ValueError: 如果合同不存在
        """

        # 1. 查询合同（包含客户信息）
        result = await db.execute(
            select(Contract, Customer)
            .where(Contract.id == contract_id)
            .options(selectinload(Customer))
        )
        contract_data = result.first()

        if not contract_data:
            raise ValueError(f"合同不存在: {contract_id}")

        contract = contract_data[0]
        customer = contract_data[1]

        # 2. 查询合同中的付款节点
        payment_nodes = contract.payment_nodes or []
        if payment_nodes:
            if isinstance(payment_nodes, list):
                payment_nodes = payment_nodes
            elif isinstance(payment_nodes, str):
                import json

                payment_nodes = json.loads(payment_nodes)

        # 3. 检查是否有项目ID，如果合同已关联项目则返回
        if contract.project_id:
            return {
                "success": False,
                "message": "该合同已关联项目ID "
                + str(contract.project_id)
                + "，无需重复创建项目",
                "project_id": contract.project_id,
            }

        # 4. 创建项目
        project = Project(
            code=await ProjectService.generate_code(),  # 假设这个方法存在
            name=f"{contract.contract_code}-{customer.name}",
            customer_id=customer.id,
            contract_id=contract.id,
            amount=contract.contract_amount,
            sow_text=contract.sow_text or "",
            acceptance_criteria=contract.acceptance_criteria or [],
            stage="S1",  # 需求进入
            status="ST01",  # 未启动
            health_status="H1",  # 正常
        )

        db.add(project)
        await db.flush()

        # 5. 如果有付款节点，创建收款计划和里程碑并关联
        created_payment_plans = 0
        created_milestones = 0

        if payment_nodes:
            milestone_seq = 1

            for idx, node in enumerate(payment_nodes, 1):
                # 计算里程碑序号
                milestone_seq = idx + 1

                # 创建收款计划
                payment_plan = ProjectPaymentPlan(
                    project_id=project.id,
                    contract_id=contract.id,
                    node_name=node.get("name", f"付款节点{milestone_seq}"),
                    percentage=node.get("percentage", 0),
                    amount=project.amount * node.get("percentage", 0) / 100,
                    due_date=node.get("due_date"),
                    milestone_id=None,  # 稍后关联
                    status="PENDING",
                )

                db.add(payment_plan)
                created_payment_plans += 1

                # 创建对应的里程碑（简化逻辑）
                milestone = ProjectMilestone(
                    project_id=project.id,
                    name=f"M{milestone_seq}",
                    description=node.get("description", f"付款里程碑{milestone_seq}"),
                    planned_date=node.get("due_date"),
                    sequence=milestone_seq,
                    status="NOT_STARTED",
                )

                db.add(milestone)
                created_milestones += 1

                # 关联收款计划与里程碑
                payment_plan.milestone_id = milestone.id
                db.flush()
                created_milestones += 1

        await db.commit()

        return {
            "success": True,
            "message": "项目创建成功，付款节点已关联到里程碑",
            "project_id": project.id,
            "payment_plans_count": created_payment_plans,
            "milestones_count": created_milestones,
        }


class ProjectPaymentPlan(Base):
    """项目收款计划模型（新创建）"""

    __tablename__ = "project_payment_plans"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    project_id = Column(Integer, nullable=False, index=True, comment="项目ID")
    contract_id = Column(Integer, nullable=True, comment="合同ID")
    node_name = Column(String(100), comment="节点名称")
    percentage = Column(Numeric(5, 2), comment="百分比")
    amount = Column(Numeric(14, 2), comment="金额")
    due_date = Column(Date, comment="到期日期")
    milestone_id = Column(
        Integer, nullable=True, index=True, comment="里程碑ID（里程碑表）"
    )
    status = Column(String(20), default="PENDING", comment="状态：PENDING/PAID")

    # 关系
    project = relationship(
        "Project", back_populates="payment_plans", cascade="all, delete-orphan"
    )
    contract = relationship("Contract", back_populates="payment_plans")
    milestone = relationship("ProjectMilestone", foreign_keys="[milestone_id]")


class ProjectService:
    """项目服务（假设存在）"""

    @staticmethod
    async def generate_code() -> str:
        """生成项目编码"""
        from app.utils.number_generator import generate_project_code

        return await generate_project_code()
