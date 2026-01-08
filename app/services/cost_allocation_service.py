# -*- coding: utf-8 -*-
"""
项目成本分摊服务
负责将成本分摊到多个机台或项目
"""

from decimal import Decimal
from datetime import date
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.models.project import ProjectCost, Project, Machine
from app.models.budget import ProjectCostAllocationRule
from app.services.revenue_service import RevenueService


class CostAllocationService:
    """成本分摊服务"""
    
    @staticmethod
    def allocate_cost_to_machines(
        db: Session,
        cost_id: int,
        allocation_targets: List[Dict],
        created_by: Optional[int] = None
    ) -> List[ProjectCost]:
        """
        将成本分摊到多个机台
        
        Args:
            db: 数据库会话
            cost_id: 原始成本记录ID
            allocation_targets: 分摊目标列表，格式：[{"machine_id": 1, "amount": 1000}, ...]
            created_by: 创建人ID
        
        Returns:
            创建的分摊成本记录列表
        """
        original_cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
        if not original_cost:
            raise ValueError("成本记录不存在")
        
        if not original_cost.project_id:
            raise ValueError("成本记录未关联项目")
        
        project = db.query(Project).filter(Project.id == original_cost.project_id).first()
        if not project:
            raise ValueError("项目不存在")
        
        # 验证分摊总额
        total_allocated = sum([Decimal(str(target.get("amount", 0))) for target in allocation_targets])
        if abs(total_allocated - original_cost.amount) > Decimal("0.01"):
            raise ValueError(f"分摊总额 {total_allocated} 与原始成本 {original_cost.amount} 不一致")
        
        # 验证机台是否属于该项目
        for target in allocation_targets:
            machine_id = target.get("machine_id")
            if machine_id:
                machine = db.query(Machine).filter(
                    Machine.id == machine_id,
                    Machine.project_id == original_cost.project_id
                ).first()
                if not machine:
                    raise ValueError(f"机台 {machine_id} 不存在或不属于该项目")
        
        # 创建分摊后的成本记录
        allocated_costs = []
        for target in allocation_targets:
            machine_id = target.get("machine_id")
            allocated_amount = Decimal(str(target.get("amount", 0)))
            
            if allocated_amount <= 0:
                continue
            
            # 计算分摊比例
            allocation_rate = (allocated_amount / original_cost.amount * 100) if original_cost.amount > 0 else 0
            
            # 创建分摊后的成本记录
            allocated_cost = ProjectCost(
                project_id=original_cost.project_id,
                machine_id=machine_id,
                cost_type=original_cost.cost_type,
                cost_category=original_cost.cost_category,
                source_module=original_cost.source_module,
                source_type="ALLOCATED",  # 标记为分摊成本
                source_id=original_cost.id,  # 指向原始成本
                source_no=f"{original_cost.source_no or ''}-ALLOC-{machine_id}",
                amount=allocated_amount,
                tax_amount=original_cost.tax_amount * allocation_rate / 100 if original_cost.tax_amount else Decimal("0"),
                cost_date=original_cost.cost_date,
                description=f"成本分摊：{original_cost.description or ''}（分摊到机台{machine_id}）",
                created_by=created_by
            )
            db.add(allocated_cost)
            allocated_costs.append(allocated_cost)
            
            # 更新机台所属项目的实际成本
            if original_cost.project_id:
                project = db.query(Project).filter(Project.id == original_cost.project_id).first()
                if project:
                    project.actual_cost = (project.actual_cost or 0) + float(allocated_amount)
                    db.add(project)
        
        # 标记原始成本为已分摊（可选：删除或保留原始记录）
        # 这里保留原始记录，但可以通过source_type标记
        
        return allocated_costs
    
    @staticmethod
    def allocate_cost_to_projects(
        db: Session,
        cost_id: int,
        allocation_targets: List[Dict],
        created_by: Optional[int] = None
    ) -> List[ProjectCost]:
        """
        将成本分摊到多个项目
        
        Args:
            db: 数据库会话
            cost_id: 原始成本记录ID
            allocation_targets: 分摊目标列表，格式：[{"project_id": 1, "amount": 1000}, ...]
            created_by: 创建人ID
        
        Returns:
            创建的分摊成本记录列表
        """
        original_cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
        if not original_cost:
            raise ValueError("成本记录不存在")
        
        # 验证分摊总额
        total_allocated = sum([Decimal(str(target.get("amount", 0))) for target in allocation_targets])
        if abs(total_allocated - original_cost.amount) > Decimal("0.01"):
            raise ValueError(f"分摊总额 {total_allocated} 与原始成本 {original_cost.amount} 不一致")
        
        # 验证项目是否存在
        for target in allocation_targets:
            project_id = target.get("project_id")
            if project_id:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"项目 {project_id} 不存在")
        
        # 创建分摊后的成本记录
        allocated_costs = []
        for target in allocation_targets:
            project_id = target.get("project_id")
            allocated_amount = Decimal(str(target.get("amount", 0)))
            
            if allocated_amount <= 0:
                continue
            
            # 计算分摊比例
            allocation_rate = (allocated_amount / original_cost.amount * 100) if original_cost.amount > 0 else 0
            
            # 创建分摊后的成本记录
            allocated_cost = ProjectCost(
                project_id=project_id,
                machine_id=original_cost.machine_id,  # 如果有机台，也复制
                cost_type=original_cost.cost_type,
                cost_category=original_cost.cost_category,
                source_module=original_cost.source_module,
                source_type="ALLOCATED",  # 标记为分摊成本
                source_id=original_cost.id,  # 指向原始成本
                source_no=f"{original_cost.source_no or ''}-ALLOC-PJ{project_id}",
                amount=allocated_amount,
                tax_amount=original_cost.tax_amount * allocation_rate / 100 if original_cost.tax_amount else Decimal("0"),
                cost_date=original_cost.cost_date,
                description=f"成本分摊：{original_cost.description or ''}（分摊到项目{project_id}）",
                created_by=created_by
            )
            db.add(allocated_cost)
            allocated_costs.append(allocated_cost)
            
            # 更新项目的实际成本
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.actual_cost = (project.actual_cost or 0) + float(allocated_amount)
                db.add(project)
        
        return allocated_costs
    
    @staticmethod
    def allocate_cost_by_rule(
        db: Session,
        cost_id: int,
        rule_id: int,
        created_by: Optional[int] = None
    ) -> List[ProjectCost]:
        """
        根据分摊规则分摊成本
        
        Args:
            db: 数据库会话
            cost_id: 成本记录ID
            rule_id: 分摊规则ID
            created_by: 创建人ID
        
        Returns:
            创建的分摊成本记录列表
        """
        original_cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
        if not original_cost:
            raise ValueError("成本记录不存在")
        
        rule = db.query(ProjectCostAllocationRule).filter(ProjectCostAllocationRule.id == rule_id).first()
        if not rule:
            raise ValueError("分摊规则不存在")
        
        if not rule.is_active:
            raise ValueError("分摊规则未启用")
        
        # 检查规则适用范围
        if rule.cost_type and rule.cost_type != original_cost.cost_type:
            raise ValueError(f"成本类型 {original_cost.cost_type} 不符合规则适用范围")
        
        if rule.cost_category and rule.cost_category != original_cost.cost_category:
            raise ValueError(f"成本分类 {original_cost.cost_category} 不符合规则适用范围")
        
        # 获取分摊目标
        if rule.allocation_basis == "MACHINE_COUNT":
            # 按机台数量分摊
            if not original_cost.project_id:
                raise ValueError("成本记录未关联项目，无法按机台数量分摊")
            
            machines = db.query(Machine).filter(
                Machine.project_id == original_cost.project_id
            ).all()
            
            if not machines:
                raise ValueError("项目没有机台，无法按机台数量分摊")
            
            # 平均分摊到每个机台
            amount_per_machine = original_cost.amount / len(machines)
            allocation_targets = [
                {"machine_id": machine.id, "amount": amount_per_machine}
                for machine in machines
            ]
            
            return CostAllocationService.allocate_cost_to_machines(
                db, cost_id, allocation_targets, created_by
            )
        
        elif rule.allocation_basis == "REVENUE":
            # 按收入分摊（使用营业收入服务获取准确的收入数据）
            if not rule.project_ids:
                raise ValueError("按收入分摊需要指定项目列表")
            
            projects = db.query(Project).filter(Project.id.in_(rule.project_ids)).all()
            if not projects:
                raise ValueError("指定的项目不存在")
            
            # 从规则公式中读取收入类型（如果配置了）
            revenue_type = "CONTRACT"  # 默认使用合同金额
            if rule.allocation_formula:
                import json
                try:
                    formula = json.loads(rule.allocation_formula)
                    revenue_type = formula.get("revenue_type", "CONTRACT")
                except:
                    pass
            
            # 使用营业收入服务获取各项目的收入
            project_revenues = RevenueService.get_projects_revenue(
                db, rule.project_ids, revenue_type
            )
            
            # 计算总收入
            total_revenue = RevenueService.get_total_revenue(
                db, rule.project_ids, revenue_type
            )
            
            if total_revenue <= 0:
                # 如果总收入为0，则平均分摊
                amount_per_project = original_cost.amount / len(projects)
                allocation_targets = [
                    {"project_id": p.id, "amount": amount_per_project}
                    for p in projects
                ]
            else:
                # 按收入比例分摊
                allocation_targets = []
                for project in projects:
                    revenue = project_revenues.get(project.id, Decimal("0"))
                    rate = float(revenue / total_revenue) if total_revenue > 0 else 0
                    amount = original_cost.amount * Decimal(str(rate))
                    allocation_targets.append({
                        "project_id": project.id,
                        "amount": amount
                    })
            
            return CostAllocationService.allocate_cost_to_projects(
                db, cost_id, allocation_targets, created_by
            )
        
        elif rule.allocation_basis == "MANUAL":
            # 手工分摊，需要从规则公式中读取
            # TODO: 解析allocation_formula JSON
            raise ValueError("手工分摊需要提供allocation_targets参数")
        
        else:
            raise ValueError(f"不支持的分摊依据：{rule.allocation_basis}")


