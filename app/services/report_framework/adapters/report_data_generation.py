# -*- coding: utf-8 -*-
"""
报表数据生成服务适配器

将 report_data_generation 服务适配到统一报表框架
保持向后兼容，同时支持统一框架
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter


class ReportDataGenerationAdapter(BaseReportAdapter):
    """报表数据生成服务适配器"""
    
    # 报表类型到报表代码的映射
    REPORT_TYPE_MAP = {
        "PROJECT_WEEKLY": "PROJECT_WEEKLY",
        "PROJECT_MONTHLY": "PROJECT_MONTHLY",
        "DEPT_WEEKLY": "DEPT_WEEKLY",
        "DEPT_MONTHLY": "DEPT_MONTHLY",
        "WORKLOAD_ANALYSIS": "WORKLOAD_ANALYSIS",
        "COST_ANALYSIS": "COST_ANALYSIS",
    }
    
    def __init__(self, db: Session, report_type: str):
        """
        Args:
            db: 数据库会话
            report_type: 报表类型（如 PROJECT_WEEKLY, DEPT_MONTHLY 等）
        """
        super().__init__(db)
        self.report_type = report_type
    
    def get_report_code(self) -> str:
        """返回报表代码"""
        return self.REPORT_TYPE_MAP.get(self.report_type, self.report_type)
    
    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成报表数据（使用 report_data_generation 服务）
        
        Args:
            params: 报表参数
            user: 当前用户
            
        Returns:
            报表数据字典
        """
        from datetime import date, timedelta
        
        from app.services.report_data_generation.router import ReportRouterMixin
        
        # 提取参数
        project_id = params.get("project_id")
        department_id = params.get("department_id")
        
        # 处理日期参数
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        if not start_date:
            start_date = date.today() - timedelta(days=7)
        if not end_date:
            end_date = date.today()
        
        # 使用 report_data_generation 服务生成数据
        report_data = ReportRouterMixin.generate_report_by_type(
            db=self.db,
            report_type=self.report_type,
            project_id=project_id,
            department_id=department_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # 如果有错误，抛出异常
        if "error" in report_data:
            raise ValueError(report_data["error"])
        
        # 添加报表元信息
        report_data["report_type"] = self.report_type
        report_data["title"] = self._get_report_title()
        
        return report_data
    
    def _get_report_title(self) -> str:
        """获取报表标题"""
        titles = {
            "PROJECT_WEEKLY": "项目周报",
            "PROJECT_MONTHLY": "项目月报",
            "DEPT_WEEKLY": "部门周报",
            "DEPT_MONTHLY": "部门月报",
            "WORKLOAD_ANALYSIS": "负荷分析报表",
            "COST_ANALYSIS": "成本分析报表",
        }
        return titles.get(self.report_type, f"{self.report_type}报表")
