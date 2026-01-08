# -*- coding: utf-8 -*-
"""
成本复盘报告生成服务
在项目结项时自动生成成本分析报告
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.project import Project, ProjectCost
from app.models.project_review import ProjectReview
from app.models.budget import ProjectBudget
from app.models.ecn import Ecn


class CostReviewService:
    """成本复盘服务"""
    
    @staticmethod
    def generate_cost_review_report(
        db: Session,
        project_id: int,
        reviewer_id: int,
        review_date: Optional[date] = None
    ) -> ProjectReview:
        """
        自动生成项目成本复盘报告
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            reviewer_id: 复盘负责人ID
            review_date: 复盘日期（默认今天）
        
        Returns:
            创建的复盘报告对象
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")
        
        # 检查项目是否已结项
        if project.stage != "S9" and project.status != "ST30":
            raise ValueError("项目未结项，无法生成成本复盘报告")
        
        # 检查是否已有复盘报告
        existing = db.query(ProjectReview).filter(
            ProjectReview.project_id == project_id,
            ProjectReview.review_type == "POST_MORTEM"
        ).first()
        
        if existing:
            raise ValueError("该项目已存在结项复盘报告")
        
        # 生成复盘编号
        review_no = CostReviewService._generate_review_no(db)
        
        # 计算项目周期
        plan_duration = None
        actual_duration = None
        schedule_variance = None
        
        if project.planned_start_date and project.planned_end_date:
            plan_duration = (project.planned_end_date - project.planned_start_date).days
        
        if project.actual_start_date:
            if project.actual_end_date:
                actual_duration = (project.actual_end_date - project.actual_start_date).days
            else:
                actual_duration = (date.today() - project.actual_start_date).days
        
        if plan_duration and actual_duration:
            schedule_variance = actual_duration - plan_duration
        
        # 获取预算和实际成本
        budget = (
            db.query(ProjectBudget)
            .filter(
                ProjectBudget.project_id == project_id,
                ProjectBudget.is_active == True,
                ProjectBudget.status == "APPROVED"
            )
            .order_by(ProjectBudget.version.desc())
            .first()
        )
        
        budget_amount = Decimal(str(budget.total_amount)) if budget else (project.budget_amount or Decimal("0"))
        
        # 计算实际成本
        costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
        actual_cost = sum([c.amount or Decimal("0") for c in costs])
        
        if project.actual_cost:
            actual_cost = Decimal(str(project.actual_cost))
        
        cost_variance = actual_cost - budget_amount
        
        # 统计变更次数
        ecn_count = db.query(Ecn).filter(
            Ecn.project_id == project_id,
            Ecn.status == "APPROVED"
        ).count()
        
        # 按成本类型统计
        cost_by_type = {}
        for cost in costs:
            cost_type = cost.cost_type or "其他"
            if cost_type not in cost_by_type:
                cost_by_type[cost_type] = Decimal("0")
            cost_by_type[cost_type] += cost.amount or Decimal("0")
        
        # 按成本分类统计
        cost_by_category = {}
        for cost in costs:
            category = cost.cost_category or "其他"
            if category not in cost_by_category:
                cost_by_category[category] = Decimal("0")
            cost_by_category[category] += cost.amount or Decimal("0")
        
        # 生成成本分析总结
        cost_summary = CostReviewService._generate_cost_summary(
            budget_amount, actual_cost, cost_variance,
            cost_by_type, cost_by_category, ecn_count
        )
        
        # 获取复盘负责人信息
        from app.models.user import User
        reviewer = db.query(User).filter(User.id == reviewer_id).first()
        reviewer_name = reviewer.real_name or reviewer.username if reviewer else "系统"
        
        # 创建复盘报告
        review = ProjectReview(
            review_no=review_no,
            project_id=project_id,
            project_code=project.project_code,
            review_date=review_date or date.today(),
            review_type="POST_MORTEM",
            plan_duration=plan_duration,
            actual_duration=actual_duration,
            schedule_variance=schedule_variance,
            budget_amount=budget_amount,
            actual_cost=actual_cost,
            cost_variance=cost_variance,
            change_count=ecn_count,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            conclusion=cost_summary,
            status="DRAFT"
        )
        
        db.add(review)
        db.flush()
        
        return review
    
    @staticmethod
    def _generate_review_no(db: Session) -> str:
        """生成复盘编号：REV-yymmdd-xxx"""
        today = datetime.now().strftime("%y%m%d")
        max_review = (
            db.query(ProjectReview)
            .filter(ProjectReview.review_no.like(f"REV-{today}-%"))
            .order_by(ProjectReview.review_no.desc())
            .first()
        )
        
        if max_review:
            seq = int(max_review.review_no.split("-")[-1]) + 1
        else:
            seq = 1
        
        return f"REV-{today}-{seq:03d}"
    
    @staticmethod
    def _generate_cost_summary(
        budget_amount: Decimal,
        actual_cost: Decimal,
        cost_variance: Decimal,
        cost_by_type: Dict[str, Decimal],
        cost_by_category: Dict[str, Decimal],
        ecn_count: int
    ) -> str:
        """生成成本分析总结"""
        summary_parts = []
        
        # 总体情况
        variance_pct = (cost_variance / budget_amount * 100) if budget_amount > 0 else 0
        if variance_pct > 10:
            summary_parts.append(f"项目实际成本{actual_cost:.2f}元，超出预算{cost_variance:.2f}元（{variance_pct:.1f}%），存在严重超支。")
        elif variance_pct > 5:
            summary_parts.append(f"项目实际成本{actual_cost:.2f}元，超出预算{cost_variance:.2f}元（{variance_pct:.1f}%），需要关注。")
        elif variance_pct < -5:
            summary_parts.append(f"项目实际成本{actual_cost:.2f}元，低于预算{abs(cost_variance):.2f}元（{abs(variance_pct):.1f}%），成本控制良好。")
        else:
            summary_parts.append(f"项目实际成本{actual_cost:.2f}元，与预算基本一致（偏差{variance_pct:.1f}%）。")
        
        # 成本构成
        if cost_by_type:
            summary_parts.append("\n成本构成：")
            for cost_type, amount in sorted(cost_by_type.items(), key=lambda x: x[1], reverse=True):
                pct = (amount / actual_cost * 100) if actual_cost > 0 else 0
                summary_parts.append(f"  - {cost_type}：{amount:.2f}元（{pct:.1f}%）")
        
        # 变更影响
        if ecn_count > 0:
            summary_parts.append(f"\n项目共发生{ecn_count}次工程变更，变更成本已单独核算。")
        
        return "\n".join(summary_parts)






