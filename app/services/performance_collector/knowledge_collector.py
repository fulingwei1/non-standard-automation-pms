# -*- coding: utf-8 -*-
"""
工程师绩效数据采集 - 知识贡献数据收集
"""

from datetime import date
from typing import Any, Dict


from app.models.engineer_performance import (
    CodeModule,
    KnowledgeContribution,
    PlcModuleLibrary,
)
from .base import PerformanceDataCollectorBase


class KnowledgeCollector(PerformanceDataCollectorBase):
    """知识贡献数据收集器"""

    def collect_knowledge_contribution_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集知识贡献数据（增强版：包含异常处理）"""
        try:
            contributions = self.db.query(KnowledgeContribution).filter(
                KnowledgeContribution.contributor_id == engineer_id,
                KnowledgeContribution.status == 'approved',
                KnowledgeContribution.created_at.between(start_date, end_date)
            ).all()

            # 统计被引用次数
            total_reuse_count = sum(
                c.reuse_count or 0 for c in contributions
            )

            # 代码模块贡献
            code_modules = self.db.query(CodeModule).filter(
                CodeModule.contributor_id == engineer_id,
                CodeModule.created_at.between(start_date, end_date)
            ).count()

            # PLC模块贡献
            plc_modules = self.db.query(PlcModuleLibrary).filter(
                PlcModuleLibrary.contributor_id == engineer_id,
                PlcModuleLibrary.created_at.between(start_date, end_date)
            ).count()

            return {
                'total_contributions': len(contributions),
                'document_count': sum(1 for c in contributions if c.contribution_type == 'document'),
                'template_count': sum(1 for c in contributions if c.contribution_type == 'template'),
                'module_count': sum(1 for c in contributions if c.contribution_type == 'module'),
                'total_reuse_count': total_reuse_count,
                'code_modules': code_modules,
                'plc_modules': plc_modules
            }
        except Exception as e:
            return {
                'total_contributions': 0,
                'document_count': 0,
                'template_count': 0,
                'module_count': 0,
                'total_reuse_count': 0,
                'code_modules': 0,
                'plc_modules': 0,
                'error': str(e)
            }
