# -*- coding: utf-8 -*-
"""
模板报表适配器

将模板报表服务适配到统一报表框架
模板报表使用数据库中的ReportTemplate配置，需要动态转换为YAML配置
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.report_center import ReportTemplate
from app.models.user import User
from app.services.report_framework.adapters.base import BaseReportAdapter
from app.services.report_framework.config_loader import ConfigLoader
from app.services.report_framework.engine import ReportEngine
from app.services.report_framework.models import ReportConfig


class TemplateReportAdapter(BaseReportAdapter):
    """模板报表适配器"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.config_loader = ConfigLoader("app/report_configs")
    
    def get_report_code(self) -> str:
        """返回报表代码（动态，取决于模板）"""
        return "TEMPLATE_REPORT"
    
    def generate_data(
        self,
        params: Dict[str, Any],
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        生成模板报表数据
        
        Args:
            params: 报表参数（包含template_id）
            user: 当前用户
            
        Returns:
            报表数据字典
        """
        template_id = params.get("template_id")
        if not template_id:
            raise ValueError("template_id参数是必需的")
        
        template = self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"报表模板不存在: {template_id}")
        
        # 使用模板报表服务生成数据
        from app.services.template_report import template_report_service
        
        report_data = template_report_service.generate_from_template(
            self.db,
            template,
            project_id=params.get("project_id"),
            department_id=params.get("department_id"),
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            filters=params.get("filters"),
        )
        
        return report_data
    
    def generate(
        self,
        params: Dict[str, Any],
        format: str = "json",
        user: Optional[User] = None,
        skip_cache: bool = False,
    ) -> Any:
        """
        生成模板报表（使用统一报表框架）
        
        模板报表的特殊之处：
        1. 使用数据库中的ReportTemplate配置
        2. 需要将数据库模板转换为统一报表框架格式
        3. 如果模板对应的报表类型已有YAML配置，优先使用YAML配置
        """
        template_id = params.get("template_id")
        if not template_id:
            raise ValueError("template_id参数是必需的")
        
        template = self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"报表模板不存在: {template_id}")
        
        # 尝试使用对应的YAML配置（如果存在）
        report_type = template.report_type
        yaml_report_code = None
        
        # 映射报表类型到YAML配置代码
        type_to_code = {
            "PROJECT_WEEKLY": "PROJECT_WEEKLY",
            "PROJECT_MONTHLY": "PROJECT_MONTHLY",
            "DEPT_WEEKLY": "DEPT_WEEKLY",
            "DEPT_MONTHLY": "DEPT_MONTHLY",
            "COMPANY_MONTHLY": "COMPANY_MONTHLY",
            "WORKLOAD_ANALYSIS": "WORKLOAD_ANALYSIS",
            "COST_ANALYSIS": "COST_ANALYSIS",
        }
        
        yaml_report_code = type_to_code.get(report_type)
        
        if yaml_report_code:
            try:
                # 尝试使用YAML配置
                result = self.engine.generate(
                    report_code=yaml_report_code,
                    params={
                        "project_id": params.get("project_id"),
                        "department_id": params.get("department_id"),
                        "start_date": params.get("start_date"),
                        "end_date": params.get("end_date"),
                    },
                    format=format,
                    user=user,
                    skip_cache=skip_cache,
                )
                return result
            except Exception:
                # YAML配置不存在或失败，使用适配器方法
                pass
        
        # 使用适配器方法生成数据
        data = self.generate_data(params, user)
        
        # 转换为统一报表框架格式
        return self._convert_to_report_result(data, format)
    
    def _convert_to_report_result(
        self,
        data: Dict[str, Any],
        format: str = "json",
    ) -> Any:
        """
        将模板报表数据转换为统一报表框架格式
        
        Args:
            data: 模板报表数据
            format: 导出格式
            
        Returns:
            报表结果
        """
        from app.services.report_framework.renderers import JsonRenderer
        
        renderer = JsonRenderer()
        sections = []
        
        # 转换数据为sections
        if "summary" in data:
            sections.append({
                "id": "summary",
                "title": "汇总",
                "type": "metrics",
                "items": [
                    {"label": k, "value": str(v)} for k, v in data["summary"].items()
                ],
            })
        
        if "sections" in data:
            for section_id, section_data in data["sections"].items():
                if isinstance(section_data, list):
                    sections.append({
                        "id": section_id,
                        "title": section_id,
                        "type": "table",
                        "data": section_data,
                    })
                elif isinstance(section_data, dict):
                    sections.append({
                        "id": section_id,
                        "title": section_id,
                        "type": "metrics",
                        "items": [
                            {"label": k, "value": str(v)} for k, v in section_data.items()
                        ],
                    })
        
        metadata = {
            "code": data.get("template_code", "TEMPLATE_REPORT"),
            "name": data.get("template_name", "模板报表"),
            "parameters": {},
        }
        
        return renderer.render(sections, metadata)
