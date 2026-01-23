# -*- coding: utf-8 -*-
"""
报表生成基类
所有报表都基于此基类实现
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
import json

from app.common.reports.renderers import PDFRenderer, ExcelRenderer, WordRenderer


class BaseReportGenerator(ABC):
    """报表生成基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: 报表配置
                - name: 报表名称
                - description: 报表描述
                - template: 模板路径（可选）
                - fields: 字段配置列表
                - filters: 筛选配置
        """
        self.config = config
        self.name = config.get("name", "报表")
        self.description = config.get("description", "")
        self.template = config.get("template")
        self.fields = config.get("fields", [])
        self.filters = config.get("filters", {})
    
    @abstractmethod
    async def generate_data(self) -> Dict[str, Any]:
        """
        生成报表数据
        
        子类必须实现此方法
        
        Returns:
            报表数据字典
        """
        pass
    
    async def export(
        self,
        format: str = "json",  # json, pdf, excel, word
        output_path: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        导出报表
        
        Args:
            format: 导出格式
            output_path: 输出路径（可选）
            **kwargs: 其他参数
        
        Returns:
            报表文件字节流
        """
        # 生成数据
        data = await self.generate_data()
        
        # 根据格式导出
        if format == "json":
            return self._export_json(data)
        elif format == "pdf":
            return self._export_pdf(data, **kwargs)
        elif format == "excel":
            return self._export_excel(data, **kwargs)
        elif format == "word":
            return self._export_word(data, **kwargs)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _export_json(self, data: Dict[str, Any]) -> bytes:
        """导出为JSON"""
        return json.dumps(
            {
                "report_name": self.name,
                "description": self.description,
                "generated_at": datetime.now().isoformat(),
                "data": data
            },
            ensure_ascii=False,
            indent=2
        ).encode('utf-8')
    
    def _export_pdf(self, data: Dict[str, Any], **kwargs) -> bytes:
        """导出为PDF"""
        renderer = PDFRenderer(self.template)
        return renderer.render(data, **kwargs)
    
    def _export_excel(self, data: Dict[str, Any], **kwargs) -> bytes:
        """导出为Excel"""
        renderer = ExcelRenderer(self.template)
        return renderer.render(data, **kwargs)
    
    def _export_word(self, data: Dict[str, Any], **kwargs) -> bytes:
        """导出为Word"""
        renderer = WordRenderer(self.template)
        return renderer.render(data, **kwargs)
    
    def get_config(self) -> Dict[str, Any]:
        """获取报表配置"""
        return self.config
    
    def validate_config(self) -> List[str]:
        """
        验证配置
        
        Returns:
            错误列表（空列表表示配置正确）
        """
        errors = []
        
        if not self.name:
            errors.append("报表名称不能为空")
        
        if not self.fields:
            errors.append("字段配置不能为空")
        
        return errors
