# -*- coding: utf-8 -*-
"""
验收报表适配器

将验收报表服务适配到统一报表框架
"""

from typing import Any, Dict, Optional


from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter


class AcceptanceReportAdapter(BaseReportAdapter):
    """验收报表适配器"""
    
    def get_report_code(self) -> str:
        """返回报表代码"""
        return "ACCEPTANCE_REPORT"
    
    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成验收报表数据
        
        Args:
            params: 报表参数（包含order_id和report_type）
            user: 当前用户
            
        Returns:
            报表数据字典
        """
        from app.models.acceptance import AcceptanceIssue, AcceptanceOrder
        from sqlalchemy import func
        
        order_id = params.get("order_id")
        if not order_id:
            raise ValueError("order_id参数是必需的")
        
        order = self.db.query(AcceptanceOrder).filter(
            AcceptanceOrder.id == order_id
        ).first()
        
        if not order:
            raise ValueError(f"验收单不存在: {order_id}")
        
        # 获取项目信息
        project_name = order.project.project_name if hasattr(order, "project") and order.project else None
        machine_name = order.machine.machine_name if hasattr(order, "machine") and order.machine else None
        
        # 获取问题统计
        total_issues = (
            self.db.query(func.count(AcceptanceIssue.id))
            .filter(AcceptanceIssue.order_id == order_id)
            .scalar()
        ) or 0
        
        resolved_issues = (
            self.db.query(func.count(AcceptanceIssue.id))
            .filter(
                AcceptanceIssue.order_id == order_id,
                AcceptanceIssue.status.in_(["RESOLVED", "CLOSED"]),
            )
            .scalar()
        ) or 0
        
        return {
            "title": "验收报告",
            "summary": {
                "验收单号": order.order_no if hasattr(order, "order_no") else f"ORDER-{order_id}",
                "验收类型": order.acceptance_type if hasattr(order, "acceptance_type") else "FAT",
                "验收状态": order.status if hasattr(order, "status") else "PENDING",
                "项目名称": project_name or "N/A",
                "机台名称": machine_name or "N/A",
                "合格率": f"{order.pass_rate or 0}%",
                "总检查项": order.total_items or 0,
                "合格项": order.passed_items or 0,
                "不合格项": order.failed_items or 0,
                "总问题数": total_issues,
                "已解决": resolved_issues,
                "待解决": total_issues - resolved_issues,
            },
            "details": [],
        }
