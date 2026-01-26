# -*- coding: utf-8 -*-
"""
报表框架使用示例
"""

from typing import Dict, Any
from app.common.reports.base import BaseReportGenerator
from app.common.statistics.base import BaseStatisticsService
from app.models.projects import Project


# ========== 示例1: 简单的报表生成器 ==========

class ProjectReportGenerator(BaseReportGenerator):
    """项目报表生成器"""
    
    def __init__(self, statistics_service: BaseStatisticsService, config: Dict[str, Any]):
        super().__init__(config)
        self.stats = statistics_service
    
    async def generate_data(self) -> Dict[str, Any]:
        """生成项目报表数据"""
        # 获取总数
        total = await self.stats.count_total()
        
        # 按状态统计
        by_status = await self.stats.count_by_status()
        
        # 获取趋势
        trends = await self.stats.get_trend("created_at", days=30)
        
        return {
            "title": "项目报表",
            "description": "项目统计报表",
            "summary": {
                "total": total,
                "by_status": by_status
            },
            "trends": trends,
            "generated_at": "2026-01-23"
        }


# ========== 示例2: 配置驱动的报表 ==========

# 报表配置（可以从YAML文件加载）
PROJECT_REPORT_CONFIG = {
    "name": "项目汇总报表",
    "description": "项目数据汇总报表",
    "template": "templates/reports/project_report.html",
    "fields": [
        {"key": "project_code", "label": "项目编码", "type": "string"},
        {"key": "project_name", "label": "项目名称", "type": "string"},
        {"key": "status", "label": "状态", "type": "enum"},
        {"key": "progress", "label": "进度", "type": "number", "format": "percent"},
        {"key": "total_cost", "label": "总成本", "type": "currency"}
    ],
    "filters": {
        "status": {"type": "select", "options": ["ACTIVE", "COMPLETED", "CANCELLED"]},
        "date_range": {"type": "date_range"}
    }
}


# ========== 使用示例 ==========

async def generate_project_report():
    """生成项目报表"""
    from app.common.statistics.base import BaseStatisticsService
    from app.models.projects import Project
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # 创建统计服务
    stats = BaseStatisticsService(Project, db_session)
    
    # 创建报表生成器
    report = ProjectReportGenerator(stats, PROJECT_REPORT_CONFIG)
    
    # 导出为不同格式
    json_data = await report.export("json")
    pdf_data = await report.export("pdf")
    excel_data = await report.export("excel")
    word_data = await report.export("word")
    
    return {
        "json": json_data,
        "pdf": pdf_data,
        "excel": excel_data,
        "word": word_data
    }


# ========== 示例3: API端点使用 ==========

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/reports/projects")
async def export_project_report(
    format: str = Query("json", regex="^(json|pdf|excel|word)$"),
    db: AsyncSession = Depends(get_db)
):
    """导出项目报表"""
    from app.common.statistics.base import BaseStatisticsService
    from app.models.projects import Project
    
    # 创建统计服务和报表生成器
    stats = BaseStatisticsService(Project, db)
    report = ProjectReportGenerator(stats, PROJECT_REPORT_CONFIG)
    
    # 生成报表
    data = await report.export(format)
    
    # 设置响应头
    content_types = {
        "json": "application/json",
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    
    return Response(
        content=data,
        media_type=content_types[format],
        headers={
            "Content-Disposition": f'attachment; filename="project_report.{format}"'
        }
    )
