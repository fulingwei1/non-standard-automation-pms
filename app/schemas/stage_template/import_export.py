# -*- coding: utf-8 -*-
"""
导入导出 Schemas

包含模板导入导出相关的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 导入导出 Schemas ====================

class TemplateExportData(BaseModel):
    """模板导出数据"""
    template_code: str
    template_name: str
    description: Optional[str] = None
    project_type: str
    stages: List[Dict[str, Any]]


class TemplateImportRequest(BaseModel):
    """模板导入请求"""
    data: Dict[str, Any] = Field(..., description="模板数据")
    override_code: Optional[str] = Field(default=None, description="覆盖模板编码")
    override_name: Optional[str] = Field(default=None, description="覆盖模板名称")


