# -*- coding: utf-8 -*-
"""
工程师绩效数据采集 - 数据聚合和报告生成
"""

from datetime import date, datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from .base import PerformanceDataCollectorBase
from .bom_collector import BomCollector
from .design_collector import DesignCollector
from .ecn_collector import EcnCollector
from .knowledge_collector import KnowledgeCollector
from .project_collector import ProjectCollector
from .work_log_collector import WorkLogCollector


class PerformanceDataAggregator(PerformanceDataCollectorBase):
    """绩效数据聚合器"""

    def __init__(self, db: Session):
        super().__init__(db)
        # 初始化各个收集器
        self.work_log_collector = WorkLogCollector(db)
        self.project_collector = ProjectCollector(db)
        self.ecn_collector = EcnCollector(db)
        self.bom_collector = BomCollector(db)
        self.design_collector = DesignCollector(db)
        self.knowledge_collector = KnowledgeCollector(db)

    def collect_all_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        采集所有绩效数据（增强版：包含统计和监控信息）

        Returns:
            包含所有维度数据和采集统计的字典
        """
        collection_stats = {
            'start_time': datetime.now().isoformat(),
            'success_count': 0,
            'failure_count': 0,
            'missing_data_sources': [],
            'errors': []
        }

        data = {}

        # 采集各个数据源
        data_sources = {
            'self_evaluation': lambda: self.work_log_collector.extract_self_evaluation_from_work_logs(
                engineer_id, start_date, end_date
            ),
            'task_completion': lambda: self.project_collector.collect_task_completion_data(
                engineer_id, start_date, end_date
            ),
            'project_participation': lambda: self.project_collector.collect_project_participation_data(
                engineer_id, start_date, end_date
            ),
            'ecn_responsibility': lambda: self.ecn_collector.collect_ecn_responsibility_data(
                engineer_id, start_date, end_date
            ),
            'bom_data': lambda: self.bom_collector.collect_bom_data(
                engineer_id, start_date, end_date
            ),
            'design_review': lambda: self.design_collector.collect_design_review_data(
                engineer_id, start_date, end_date
            ),
            'debug_issue': lambda: self.design_collector.collect_debug_issue_data(
                engineer_id, start_date, end_date
            ),
            'knowledge_contribution': lambda: self.knowledge_collector.collect_knowledge_contribution_data(
                engineer_id, start_date, end_date
            )
        }

        for source_name, collect_func in data_sources.items():
            try:
                result = collect_func()
                data[source_name] = result
                collection_stats['success_count'] += 1

                # 检查数据是否为空或缺失
                if not result or (isinstance(result, dict) and not any(result.values())):
                    collection_stats['missing_data_sources'].append(source_name)
            except Exception as e:
                collection_stats['failure_count'] += 1
                collection_stats['errors'].append({
                    'source': source_name,
                    'error': str(e)
                })
                # 提供默认值
                data[source_name] = {}

        collection_stats['end_time'] = datetime.now().isoformat()
        collection_stats['total_sources'] = len(data_sources)
        collection_stats['success_rate'] = round(
            (collection_stats['success_count'] / len(data_sources) * 100), 2
        ) if data_sources else 0.0

        return {
            'data': data,
            'statistics': collection_stats,
            'engineer_id': engineer_id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

    def generate_collection_report(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成数据采集报告

        Returns:
            包含采集结果、统计信息、缺失数据分析和建议的报告
        """
        collection_result = self.collect_all_data(engineer_id, start_date, end_date)
        stats = collection_result.get('statistics', {})
        data = collection_result.get('data', {})

        # 分析缺失数据原因
        missing_analysis = []
        suggestions = []

        # 检查工作日志
        self_eval = data.get('self_evaluation', {})
        if self_eval.get('total_logs', 0) == 0:
            missing_analysis.append({
                'source': '工作日志',
                'reason': '考核周期内无工作日志记录',
                'impact': '无法提取自我评价数据'
            })
            suggestions.append('建议工程师及时填写工作日志')

        # 检查项目参与
        project_data = data.get('project_participation', {})
        if project_data.get('total_projects', 0) == 0:
            missing_analysis.append({
                'source': '项目参与',
                'reason': '考核周期内未参与任何项目',
                'impact': '无法计算项目执行相关指标'
            })
            suggestions.append('检查项目成员分配是否正确')

        # 检查任务完成情况
        task_data = data.get('task_completion', {})
        if task_data.get('total_tasks', 0) == 0:
            missing_analysis.append({
                'source': '任务完成',
                'reason': '考核周期内无任务记录',
                'impact': '无法计算任务完成率'
            })
            suggestions.append('检查任务分配和记录是否完整')

        # 检查设计评审（针对机械工程师）
        design_review = data.get('design_review', {})
        if design_review.get('total_reviews', 0) == 0:
            missing_analysis.append({
                'source': '设计评审',
                'reason': '考核周期内无设计评审记录',
                'impact': '无法计算设计一次通过率'
            })
            suggestions.append('确保设计评审流程完整执行')

        # 计算数据完整性得分
        total_sources = len(data)
        available_sources = sum(1 for d in data.values() if d)
        completeness_score = round((available_sources / total_sources * 100), 2) if total_sources > 0 else 0.0

        return {
            'engineer_id': engineer_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'collection_statistics': stats,
            'data_completeness': {
                'score': completeness_score,
                'total_sources': total_sources,
                'available_sources': available_sources,
                'missing_sources': total_sources - available_sources
            },
            'missing_data_analysis': missing_analysis,
            'suggestions': suggestions,
            'generated_at': datetime.now().isoformat()
        }
