# -*- coding: utf-8 -*-
"""
研发费用报表适配器

将研发费用报表服务适配到统一报表框架
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter


class RdExpenseReportAdapter(BaseReportAdapter):
    """研发费用报表适配器"""
    
    # 报表类型到报表代码的映射
    REPORT_TYPE_MAP = {
        "RD_AUXILIARY_LEDGER": "RD_AUXILIARY_LEDGER",
        "RD_DEDUCTION_DETAIL": "RD_DEDUCTION_DETAIL",
        "RD_HIGH_TECH": "RD_HIGH_TECH",
        "RD_INTENSITY": "RD_INTENSITY",
        "RD_PERSONNEL": "RD_PERSONNEL",
    }
    
    def __init__(self, db: Session, report_type: str = "RD_AUXILIARY_LEDGER"):
        """
        Args:
            db: 数据库会话
            report_type: 报表类型
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
        生成研发费用报表数据
        
        Args:
            params: 报表参数（包含year和可选的project_id）
            user: 当前用户
            
        Returns:
            报表数据字典
        """
        from app.services.rd_report_data_service import (
            build_auxiliary_ledger_data,
            build_deduction_detail_data,
            build_high_tech_data,
            build_intensity_data,
            build_personnel_data,
        )
        
        year = params.get("year")
        if not year:
            raise ValueError("year参数是必需的")
        
        project_id = params.get("project_id")
        
        # 根据报表类型调用不同的构建函数
        if self.report_type == "RD_AUXILIARY_LEDGER":
            return build_auxiliary_ledger_data(self.db, year, project_id)
        elif self.report_type == "RD_DEDUCTION_DETAIL":
            return build_deduction_detail_data(self.db, year, project_id)
        elif self.report_type == "RD_HIGH_TECH":
            return build_high_tech_data(self.db, year)
        elif self.report_type == "RD_INTENSITY":
            # RD_INTENSITY需要start_year和end_year，但build_intensity_data只接受year
            # 暂时使用start_year，如果需要多年度，需要修改build_intensity_data函数
            start_year = params.get("start_year", year)
            end_year = params.get("end_year", year)
            # 如果start_year和end_year相同，使用单年度
            if start_year == end_year:
                return build_intensity_data(self.db, start_year)
            else:
                # 多年度需要特殊处理，暂时返回错误
                raise ValueError("多年度研发投入强度报表暂不支持，请使用单年度")
        elif self.report_type == "RD_PERSONNEL":
            return build_personnel_data(self.db, year)
        else:
            raise ValueError(f"不支持的报表类型: {self.report_type}")
