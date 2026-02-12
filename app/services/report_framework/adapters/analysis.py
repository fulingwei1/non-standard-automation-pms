# -*- coding: utf-8 -*-
"""
分析报表适配器

将分析报表数据生成器适配到统一报表框架
"""

from datetime import date
from typing import Any, Dict, Optional


from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter
from app.services.report_framework.generators import AnalysisReportGenerator


class WorkloadAnalysisAdapter(BaseReportAdapter):
    """负荷分析报表适配器"""

    def get_report_code(self) -> str:
        """返回报表代码"""
        return "WORKLOAD_ANALYSIS"

    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成负荷分析报表数据

        Args:
            params: 报表参数（department_id可选, start_date, end_date）
            user: 当前用户

        Returns:
            报表数据字典
        """
        department_id = params.get("department_id")

        # 处理日期参数
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        if end_date and isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        if start_date and isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        # 使用统一生成器
        data = AnalysisReportGenerator.generate_workload_analysis(
            self.db, department_id, start_date, end_date
        )

        # 添加报表元信息
        data["title"] = "负荷分析报告"
        data["report_type"] = self.get_report_code()

        return data


class CostAnalysisAdapter(BaseReportAdapter):
    """成本分析报表适配器"""

    def get_report_code(self) -> str:
        """返回报表代码"""
        return "COST_ANALYSIS"

    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成成本分析报表数据

        Args:
            params: 报表参数（project_id可选, start_date, end_date）
            user: 当前用户

        Returns:
            报表数据字典
        """
        project_id = params.get("project_id")

        # 处理日期参数
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        if end_date and isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        if start_date and isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        # 使用统一生成器
        data = AnalysisReportGenerator.generate_cost_analysis(
            self.db, project_id, start_date, end_date
        )

        # 添加报表元信息
        data["title"] = "成本分析报告"
        data["report_type"] = self.get_report_code()

        return data
