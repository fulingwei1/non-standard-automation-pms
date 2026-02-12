# -*- coding: utf-8 -*-
"""
工时报表适配器

将工时报表服务适配到统一报表框架
"""

from typing import Any, Dict, Optional


from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter


class TimesheetReportAdapter(BaseReportAdapter):
    """工时报表适配器"""
    
    def get_report_code(self) -> str:
        """返回报表代码"""
        # 根据参数动态返回报表代码
        return "TIMESHEET_WEEKLY"  # 默认周报
    
    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成工时报表数据
        
        Args:
            params: 报表参数
            user: 当前用户
            
        Returns:
            报表数据字典
        """
        # 这个适配器主要用于向后兼容
        # 实际数据生成应该通过YAML配置中的服务调用
        return {
            "title": "工时报表",
            "summary": {},
            "details": [],
        }
