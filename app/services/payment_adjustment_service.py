# -*- coding: utf-8 -*-
"""
收款计划调整服务
Issue 7.3: 项目进度影响收款计划
实现里程碑状态变化时自动调整收款计划的功能
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.project import ProjectMilestone, ProjectPaymentPlan, Project
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class PaymentAdjustmentService:
    """收款计划调整服务"""

    def __init__(self, db: Session):
        self.db = db

    def adjust_payment_plan_by_milestone(
        self,
        milestone_id: int,
        reason: str = "里程碑延期自动调整",
        adjusted_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        根据里程碑状态变化调整收款计划
        
        Args:
            milestone_id: 里程碑ID
            reason: 调整原因
            adjusted_by: 调整人ID（自动调整时为None）
        
        Returns:
            调整结果字典
        """
        milestone = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.id == milestone_id
        ).first()
        
        if not milestone:
            return {
                "success": False,
                "message": "里程碑不存在",
                "adjusted_plans": []
            }
        
        # 查找关联的收款计划
        payment_plans = self.db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.milestone_id == milestone_id,
            ProjectPaymentPlan.status.in_(["PENDING", "INVOICED"])
        ).all()
        
        if not payment_plans:
            return {
                "success": True,
                "message": "没有需要调整的收款计划",
                "adjusted_plans": []
            }
        
        adjusted_plans = []
        
        for plan in payment_plans:
            # 如果里程碑延期，调整收款计划日期
            if milestone.status == "DELAYED" and milestone.actual_date:
                # 里程碑延期，收款计划也相应延期
                if plan.planned_date and milestone.actual_date > plan.planned_date:
                    old_date = plan.planned_date
                    plan.planned_date = milestone.actual_date
                    
                    # 记录调整历史
                    self._record_adjustment_history(
                        plan.id,
                        "planned_date",
                        str(old_date),
                        str(plan.planned_date),
                        reason,
                        adjusted_by
                    )
                    
                    adjusted_plans.append({
                        "plan_id": plan.id,
                        "payment_name": plan.payment_name,
                        "old_date": str(old_date),
                        "new_date": str(plan.planned_date),
                        "reason": reason
                    })
            
            # 如果里程碑提前完成，可以提前触发开票（需配置）
            elif milestone.status == "COMPLETED" and milestone.actual_date:
                if plan.planned_date and milestone.actual_date < plan.planned_date:
                    # 检查是否允许提前开票（这里简化处理，实际应该从配置读取）
                    allow_early_invoice = True  # 可以从配置读取
                    
                    if allow_early_invoice:
                        old_date = plan.planned_date
                        plan.planned_date = milestone.actual_date
                        
                        # 记录调整历史
                        self._record_adjustment_history(
                            plan.id,
                            "planned_date",
                            str(old_date),
                            str(plan.planned_date),
                            f"里程碑提前完成，允许提前开票: {reason}",
                            adjusted_by
                        )
                        
                        adjusted_plans.append({
                            "plan_id": plan.id,
                            "payment_name": plan.payment_name,
                            "old_date": str(old_date),
                            "new_date": str(plan.planned_date),
                            "reason": f"里程碑提前完成，允许提前开票"
                        })
        
        if adjusted_plans:
            self.db.commit()
            
            # 发送通知
            self._send_adjustment_notifications(milestone, adjusted_plans, reason)
        
        return {
            "success": True,
            "message": f"已调整 {len(adjusted_plans)} 个收款计划",
            "adjusted_plans": adjusted_plans
        }

    def manual_adjust_payment_plan(
        self,
        plan_id: int,
        new_date: date,
        reason: str,
        adjusted_by: int,
    ) -> Dict[str, Any]:
        """
        手动调整收款计划
        
        Args:
            plan_id: 收款计划ID
            new_date: 新的收款日期
            reason: 调整原因
            adjusted_by: 调整人ID
        
        Returns:
            调整结果字典
        """
        plan = self.db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.id == plan_id
        ).first()
        
        if not plan:
            return {
                "success": False,
                "message": "收款计划不存在"
            }
        
        old_date = plan.planned_date
        plan.planned_date = new_date
        
        # 记录调整历史
        self._record_adjustment_history(
            plan.id,
            "planned_date",
            str(old_date) if old_date else None,
            str(new_date),
            reason,
            adjusted_by
        )
        
        self.db.commit()
        
        # 发送通知
        milestone = plan.milestone
        if milestone:
            self._send_adjustment_notifications(
                milestone,
                [{
                    "plan_id": plan.id,
                    "payment_name": plan.payment_name,
                    "old_date": str(old_date) if old_date else None,
                    "new_date": str(new_date),
                    "reason": reason
                }],
                reason
            )
        
        return {
            "success": True,
            "message": "收款计划已调整",
            "plan_id": plan.id,
            "old_date": str(old_date) if old_date else None,
            "new_date": str(new_date)
        }

    def _record_adjustment_history(
        self,
        plan_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: str,
        reason: str,
        adjusted_by: Optional[int],
    ) -> None:
        """
        记录调整历史
        
        注意：这里简化实现，将历史记录存储在收款计划的 remark 字段中
        实际项目中可以创建专门的调整历史表
        """
        plan = self.db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.id == plan_id
        ).first()
        
        if not plan:
            return
        
        # 构建历史记录
        history_entry = {
            "field": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "adjusted_by": adjusted_by,
            "adjusted_at": datetime.now().isoformat()
        }
        
        # 将历史记录追加到备注中（JSON格式）
        import json
        try:
            if plan.remark:
                # 尝试解析现有备注为JSON数组
                try:
                    history_list = json.loads(plan.remark)
                    if not isinstance(history_list, list):
                        history_list = []
                except (json.JSONDecodeError, TypeError):
                    history_list = []
            else:
                history_list = []
            
            history_list.append(history_entry)
            plan.remark = json.dumps(history_list, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"记录调整历史失败: {e}")
            # 如果JSON处理失败，直接追加文本
            history_text = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {field_name}: {old_value} -> {new_value}, 原因: {reason}"
            plan.remark = (plan.remark or "") + history_text

    def _send_adjustment_notifications(
        self,
        milestone: ProjectMilestone,
        adjusted_plans: List[Dict[str, Any]],
        reason: str,
    ) -> None:
        """
        发送调整通知给：收款责任人、销售、财务
        
        Args:
            milestone: 里程碑
            adjusted_plans: 调整的收款计划列表
            reason: 调整原因
        """
        try:
            # 获取项目信息
            project = milestone.project
            if not project:
                return
            
            # 获取合同信息
            contract = None
            if project.contract_id:
                contract = self.db.query(Contract).filter(
                    Contract.id == project.contract_id
                ).first()
            
            # 确定通知对象
            recipient_ids = set()
            
            # 1. 收款责任人（从收款计划中获取）
            for plan_dict in adjusted_plans:
                plan = self.db.query(ProjectPaymentPlan).filter(
                    ProjectPaymentPlan.id == plan_dict["plan_id"]
                ).first()
                if plan and plan.contract:
                    # 合同负责人
                    if plan.contract.owner_id:
                        recipient_ids.add(plan.contract.owner_id)
            
            # 2. 销售（项目负责人或合同负责人）
            if contract and contract.owner_id:
                recipient_ids.add(contract.owner_id)
            if project.pm_id:
                recipient_ids.add(project.pm_id)
            
            # 3. 财务（这里简化处理，实际应该从角色中查找）
            # 通过 UserRole 关联查找财务角色用户
            from app.models.user import UserRole, Role
            finance_role_ids = self.db.query(Role.id).filter(
                Role.role_code.in_(["FINANCE", "财务", "FINANCE_MANAGER", "财务经理"])
            ).all()
            finance_role_ids = [r[0] for r in finance_role_ids]
            if finance_role_ids:
                finance_user_ids = self.db.query(UserRole.user_id).filter(
                    UserRole.role_id.in_(finance_role_ids)
                ).all()
                for uid in finance_user_ids:
                    recipient_ids.add(uid[0])
            
            # 构建通知内容
            plan_names = [p["payment_name"] for p in adjusted_plans]
            notification_content = (
                f"项目 {project.project_code} 的收款计划已调整：\n"
                f"里程碑：{milestone.milestone_name}\n"
                f"调整的收款计划：{', '.join(plan_names)}\n"
                f"调整原因：{reason}\n"
                f"请及时关注收款计划变更。"
            )
            
            # 创建通知记录
            for user_id in recipient_ids:
                notification = Notification(
                    user_id=user_id,
                    title="收款计划调整通知",
                    content=notification_content,
                    notification_type="PAYMENT_ADJUSTMENT",
                    source_type="payment_plan",
                    source_id=adjusted_plans[0]["plan_id"] if adjusted_plans else None,
                    is_read=False,
                )
                self.db.add(notification)
            
            self.db.commit()
            logger.info(f"已发送收款计划调整通知给 {len(recipient_ids)} 个用户")
            
        except Exception as e:
            logger.error(f"发送收款计划调整通知失败: {e}", exc_info=True)
            # 通知失败不影响调整操作

    def get_adjustment_history(
        self,
        plan_id: int,
    ) -> List[Dict[str, Any]]:
        """
        获取收款计划调整历史
        
        Args:
            plan_id: 收款计划ID
        
        Returns:
            调整历史列表
        """
        plan = self.db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.id == plan_id
        ).first()
        
        if not plan or not plan.remark:
            return []
        
        import json
        try:
            # 尝试解析为JSON数组
            history_list = json.loads(plan.remark)
            if isinstance(history_list, list):
                return history_list
        except (json.JSONDecodeError, TypeError):
            pass
        
        # 如果不是JSON格式，返回空列表
        return []
