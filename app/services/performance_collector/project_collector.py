# -*- coding: utf-8 -*-
"""
工程师绩效数据采集 - 项目执行数据收集
包含：任务完成情况、项目参与情况
"""

from datetime import date
from typing import Any, Dict


from app.models.progress import Task
from app.models.project import Project, ProjectMember
from app.models.project_evaluation import ProjectEvaluation
from .base import PerformanceDataCollectorBase


class ProjectCollector(PerformanceDataCollectorBase):
    """项目执行数据收集器"""

    def collect_task_completion_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集任务完成情况数据（增强版：包含异常处理）"""
        try:
            tasks = self.db.query(Task).join(
                ProjectMember, Task.project_id == ProjectMember.project_id
            ).filter(
                ProjectMember.user_id == engineer_id,
                Task.owner_id == engineer_id,
                Task.created_at.between(start_date, end_date)
            ).all()

            if not tasks:
                return {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'on_time_tasks': 0,
                    'completion_rate': 0.0,
                    'on_time_rate': 0.0
                }

            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.status == 'COMPLETED')
            on_time_tasks = sum(
                1 for t in tasks
                if t.status == 'COMPLETED' and t.actual_end_date
                and t.due_date and t.actual_end_date <= t.due_date
            )

            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            on_time_rate = (on_time_tasks / completed_tasks * 100) if completed_tasks > 0 else 0.0

            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'on_time_tasks': on_time_tasks,
                'completion_rate': round(completion_rate, 2),
                'on_time_rate': round(on_time_rate, 2)
            }
        except Exception as e:
            # 异常时返回默认值
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'on_time_tasks': 0,
                'completion_rate': 0.0,
                'on_time_rate': 0.0,
                'error': str(e)
            }

    def collect_project_participation_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集项目参与情况数据（增强版：包含异常处理）"""
        try:
            projects = self.db.query(Project).join(
                ProjectMember, Project.id == ProjectMember.project_id
            ).filter(
                ProjectMember.user_id == engineer_id,
                Project.created_at.between(start_date, end_date)
            ).all()

            # 获取项目难度和工作量数据
            project_evaluations = {}
            for project in projects:
                try:
                    evaluation = self.db.query(ProjectEvaluation).filter(
                        ProjectEvaluation.project_id == project.id,
                        ProjectEvaluation.status == 'CONFIRMED'
                    ).first()
                except Exception:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug("查询项目评估数据失败，已忽略", exc_info=True)
                    evaluation = None

                if evaluation:
                    project_evaluations[project.id] = {
                        'difficulty_score': float(evaluation.difficulty_score) if evaluation.difficulty_score else None,
                        'workload_score': float(evaluation.workload_score) if evaluation.workload_score else None
                    }

            return {
                'total_projects': len(projects),
                'project_ids': [p.id for p in projects],
                'project_evaluations': project_evaluations,
                'evaluated_projects': len(project_evaluations)
            }
        except Exception as e:
            return {
                'total_projects': 0,
                'project_ids': [],
                'project_evaluations': {},
                'evaluated_projects': 0,
                'error': str(e)
            }
