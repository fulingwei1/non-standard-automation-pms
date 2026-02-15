# -*- coding: utf-8 -*-
"""
AI WBS分解器
智能分解工作任务并识别依赖关系
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Project, TaskUnified
from app.models.ai_planning import AIWbsSuggestion, AIProjectPlanTemplate
from .glm_service import GLMService

logger = logging.getLogger(__name__)


class AIWbsDecomposer:
    """AI WBS分解器"""
    
    def __init__(self, db: Session, glm_service: Optional[GLMService] = None):
        """
        初始化WBS分解器
        
        Args:
            db: 数据库会话
            glm_service: GLM AI服务实例
        """
        self.db = db
        self.glm_service = glm_service or GLMService()
    
    async def decompose_project(
        self,
        project_id: int,
        template_id: Optional[int] = None,
        max_level: int = 3
    ) -> List[AIWbsSuggestion]:
        """
        分解整个项目
        
        Args:
            project_id: 项目ID
            template_id: 模板ID
            max_level: 最大分解层级
            
        Returns:
            WBS建议列表
        """
        project = self.db.query(Project).get(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return []
        
        # 获取模板
        template = None
        if template_id:
            template = self.db.query(AIProjectPlanTemplate).get(template_id)
        
        # 生成一级任务（阶段）
        level_1_tasks = self._generate_level_1_tasks(project, template)
        
        all_suggestions = []
        
        # 递归分解每个一级任务
        for task in level_1_tasks:
            self.db.add(task)
            self.db.flush()
            all_suggestions.append(task)
            
            if max_level > 1:
                subtasks = await self._decompose_task(
                    task, project, level=2, max_level=max_level
                )
                all_suggestions.extend(subtasks)
        
        # 识别依赖关系
        self._identify_dependencies(all_suggestions)
        
        # 计算关键路径
        self._calculate_critical_path(all_suggestions)
        
        return all_suggestions
    
    def _generate_level_1_tasks(
        self,
        project: Project,
        template: Optional[AIProjectPlanTemplate]
    ) -> List[AIWbsSuggestion]:
        """生成一级任务（项目阶段）"""
        
        tasks = []
        
        if template and template.phases:
            # 从模板生成
            phases = json.loads(template.phases)
            for i, phase in enumerate(phases, 1):
                suggestion = AIWbsSuggestion(
                    suggestion_code=f"WBS_{project.id}_L1_{i:02d}",
                    project_id=project.id,
                    template_id=template.id if template else None,
                    ai_model_version=template.ai_model_version if template else "RULE_ENGINE",
                    generation_time=datetime.now(),
                    confidence_score=90.0,
                    wbs_level=1,
                    parent_wbs_id=None,
                    wbs_code=f"{i}",
                    sequence=i,
                    task_name=phase['name'],
                    task_description=f"{phase['name']}阶段",
                    task_type="PHASE",
                    category="项目阶段",
                    estimated_duration_days=phase['duration_days'],
                    complexity="MEDIUM",
                    deliverables=json.dumps(phase.get('deliverables', []), ensure_ascii=False),
                    status='SUGGESTED',
                )
                tasks.append(suggestion)
        else:
            # 使用默认阶段
            default_phases = [
                {"name": "需求分析", "duration_days": 15, "deliverables": ["需求文档"]},
                {"name": "设计阶段", "duration_days": 20, "deliverables": ["设计方案"]},
                {"name": "开发实施", "duration_days": 40, "deliverables": ["代码"]},
                {"name": "测试验收", "duration_days": 15, "deliverables": ["测试报告"]},
            ]
            
            for i, phase in enumerate(default_phases, 1):
                suggestion = AIWbsSuggestion(
                    suggestion_code=f"WBS_{project.id}_L1_{i:02d}",
                    project_id=project.id,
                    generation_time=datetime.now(),
                    confidence_score=75.0,
                    wbs_level=1,
                    wbs_code=f"{i}",
                    sequence=i,
                    task_name=phase['name'],
                    task_description=f"{phase['name']}阶段",
                    task_type="PHASE",
                    estimated_duration_days=phase['duration_days'],
                    complexity="MEDIUM",
                    deliverables=json.dumps(phase.get('deliverables', []), ensure_ascii=False),
                    status='SUGGESTED',
                )
                tasks.append(suggestion)
        
        return tasks
    
    async def _decompose_task(
        self,
        parent_task: AIWbsSuggestion,
        project: Project,
        level: int,
        max_level: int
    ) -> List[AIWbsSuggestion]:
        """递归分解任务"""
        
        if level > max_level:
            return []
        
        # 查找参考任务
        reference_tasks = self._find_reference_tasks(
            parent_task.task_name,
            parent_task.task_type,
            project.project_type
        )
        
        # 使用AI分解
        subtasks_data = self.glm_service.decompose_wbs(
            task_name=parent_task.task_name,
            task_description=parent_task.task_description or "",
            task_type=parent_task.task_type or "GENERAL",
            estimated_duration=parent_task.estimated_duration_days,
            reference_tasks=[self._task_to_dict(t) for t in reference_tasks]
        )
        
        if not subtasks_data:
            # 使用规则引擎生成备用分解
            subtasks_data = self._generate_fallback_subtasks(parent_task)
        
        all_suggestions = []
        
        for i, subtask_data in enumerate(subtasks_data, 1):
            suggestion = self._create_suggestion_from_data(
                subtask_data,
                project=project,
                parent_task=parent_task,
                level=level,
                sequence=i
            )
            
            self.db.add(suggestion)
            self.db.flush()
            all_suggestions.append(suggestion)
            
            # 如果还可以继续分解
            if level < max_level and suggestion.complexity in ['COMPLEX', 'CRITICAL']:
                sub_suggestions = await self._decompose_task(
                    suggestion, project, level + 1, max_level
                )
                all_suggestions.extend(sub_suggestions)
        
        return all_suggestions
    
    def _find_reference_tasks(
        self,
        task_name: str,
        task_type: str,
        project_type: str,
        limit: int = 5
    ) -> List[TaskUnified]:
        """查找参考任务"""
        
        # 简单的关键词匹配
        query = self.db.query(TaskUnified).filter(
            TaskUnified.task_type == task_type,
            TaskUnified.status == 'COMPLETED'
        )
        
        # TODO: 实现更智能的相似度匹配
        return query.limit(limit).all()
    
    def _task_to_dict(self, task: TaskUnified) -> Dict:
        """将任务对象转换为字典"""
        return {
            'id': task.id,
            'name': task.title,
            'type': task.task_type,
            'effort_hours': float(task.actual_hours) if task.actual_hours else None,
        }
    
    def _generate_fallback_subtasks(self, parent_task: AIWbsSuggestion) -> List[Dict]:
        """生成备用子任务（基于规则）"""
        
        logger.info(f"为任务 '{parent_task.task_name}' 生成备用子任务")
        
        # 根据任务类型生成标准子任务
        task_name_lower = parent_task.task_name.lower()
        
        if '需求' in task_name_lower or 'requirement' in task_name_lower:
            return [
                {
                    "task_name": "需求调研",
                    "task_description": "收集用户需求",
                    "task_type": "ANALYSIS",
                    "estimated_duration_days": 5,
                    "estimated_effort_hours": 40,
                    "complexity": "MEDIUM",
                    "required_skills": [{"skill": "需求分析", "level": "Middle"}],
                    "deliverables": [{"name": "需求调研报告", "type": "文档"}],
                    "risk_level": "LOW"
                },
                {
                    "task_name": "需求分析",
                    "task_description": "分析整理需求",
                    "task_type": "ANALYSIS",
                    "estimated_duration_days": 7,
                    "estimated_effort_hours": 56,
                    "complexity": "MEDIUM",
                    "required_skills": [{"skill": "需求分析", "level": "Senior"}],
                    "deliverables": [{"name": "需求规格说明书", "type": "文档"}],
                    "risk_level": "MEDIUM"
                },
                {
                    "task_name": "需求评审",
                    "task_description": "需求评审会议",
                    "task_type": "REVIEW",
                    "estimated_duration_days": 3,
                    "estimated_effort_hours": 24,
                    "complexity": "SIMPLE",
                    "required_skills": [{"skill": "项目管理", "level": "Middle"}],
                    "deliverables": [{"name": "评审报告", "type": "文档"}],
                    "risk_level": "LOW"
                }
            ]
        elif '设计' in task_name_lower or 'design' in task_name_lower:
            return [
                {
                    "task_name": "概要设计",
                    "task_description": "系统架构设计",
                    "task_type": "DESIGN",
                    "estimated_duration_days": 7,
                    "estimated_effort_hours": 56,
                    "complexity": "COMPLEX",
                    "required_skills": [{"skill": "系统架构", "level": "Senior"}],
                    "deliverables": [{"name": "概要设计文档", "type": "文档"}],
                    "risk_level": "MEDIUM"
                },
                {
                    "task_name": "详细设计",
                    "task_description": "模块详细设计",
                    "task_type": "DESIGN",
                    "estimated_duration_days": 10,
                    "estimated_effort_hours": 80,
                    "complexity": "MEDIUM",
                    "required_skills": [{"skill": "软件设计", "level": "Middle"}],
                    "deliverables": [{"name": "详细设计文档", "type": "文档"}],
                    "risk_level": "MEDIUM"
                },
                {
                    "task_name": "设计评审",
                    "task_description": "设计方案评审",
                    "task_type": "REVIEW",
                    "estimated_duration_days": 3,
                    "estimated_effort_hours": 24,
                    "complexity": "SIMPLE",
                    "required_skills": [{"skill": "技术评审", "level": "Senior"}],
                    "deliverables": [{"name": "评审记录", "type": "文档"}],
                    "risk_level": "LOW"
                }
            ]
        else:
            # 通用分解
            duration = parent_task.estimated_duration_days or 10
            return [
                {
                    "task_name": f"{parent_task.task_name} - 准备",
                    "task_description": "任务准备阶段",
                    "task_type": parent_task.task_type,
                    "estimated_duration_days": int(duration * 0.2),
                    "estimated_effort_hours": int(duration * 0.2 * 8),
                    "complexity": "SIMPLE",
                    "required_skills": [],
                    "deliverables": [],
                    "risk_level": "LOW"
                },
                {
                    "task_name": f"{parent_task.task_name} - 执行",
                    "task_description": "任务执行阶段",
                    "task_type": parent_task.task_type,
                    "estimated_duration_days": int(duration * 0.6),
                    "estimated_effort_hours": int(duration * 0.6 * 8),
                    "complexity": "MEDIUM",
                    "required_skills": [],
                    "deliverables": [],
                    "risk_level": "MEDIUM"
                },
                {
                    "task_name": f"{parent_task.task_name} - 验收",
                    "task_description": "任务验收阶段",
                    "task_type": parent_task.task_type,
                    "estimated_duration_days": int(duration * 0.2),
                    "estimated_effort_hours": int(duration * 0.2 * 8),
                    "complexity": "SIMPLE",
                    "required_skills": [],
                    "deliverables": [],
                    "risk_level": "LOW"
                }
            ]
    
    def _create_suggestion_from_data(
        self,
        data: Dict,
        project: Project,
        parent_task: AIWbsSuggestion,
        level: int,
        sequence: int
    ) -> AIWbsSuggestion:
        """从数据创建WBS建议对象"""
        
        wbs_code = f"{parent_task.wbs_code}.{sequence}"
        
        return AIWbsSuggestion(
            suggestion_code=f"WBS_{project.id}_L{level}_{parent_task.id}_{sequence:02d}",
            project_id=project.id,
            template_id=parent_task.template_id,
            ai_model_version=self.glm_service.model if self.glm_service.is_available() else "RULE_ENGINE",
            generation_time=datetime.now(),
            confidence_score=data.get('confidence_score', 80.0),
            wbs_level=level,
            parent_wbs_id=parent_task.id,
            wbs_code=wbs_code,
            sequence=sequence,
            task_name=data['task_name'],
            task_description=data.get('task_description'),
            task_type=data.get('task_type', 'GENERAL'),
            category=data.get('category'),
            estimated_duration_days=data.get('estimated_duration_days'),
            estimated_effort_hours=data.get('estimated_effort_hours'),
            complexity=data.get('complexity', 'MEDIUM'),
            dependencies=json.dumps(data.get('dependencies', []), ensure_ascii=False),
            required_skills=json.dumps(data.get('required_skills', []), ensure_ascii=False),
            deliverables=json.dumps(data.get('deliverables', []), ensure_ascii=False),
            risk_level=data.get('risk_level', 'MEDIUM'),
            status='SUGGESTED',
        )
    
    def _identify_dependencies(self, suggestions: List[AIWbsSuggestion]):
        """识别任务依赖关系"""
        
        # 默认依赖规则：同层级任务按顺序执行（FS关系）
        level_tasks = {}
        for suggestion in suggestions:
            level = suggestion.wbs_level
            if level not in level_tasks:
                level_tasks[level] = []
            level_tasks[level].append(suggestion)
        
        # 为每层的任务设置依赖
        for level, tasks in level_tasks.items():
            # 按父任务和序号排序
            tasks.sort(key=lambda t: (t.parent_wbs_id or 0, t.sequence or 0))
            
            for i in range(1, len(tasks)):
                prev_task = tasks[i-1]
                current_task = tasks[i]
                
                # 只在同一父任务下设置依赖
                if current_task.parent_wbs_id == prev_task.parent_wbs_id:
                    dependencies = [{"task_id": prev_task.id, "type": "FS"}]
                    current_task.dependencies = json.dumps(dependencies, ensure_ascii=False)
                    current_task.dependency_type = "FS"
    
    def _calculate_critical_path(self, suggestions: List[AIWbsSuggestion]):
        """计算关键路径"""
        
        # 简化版关键路径算法：找出最长的任务链
        # TODO: 实现完整的CPM算法
        
        max_duration = 0
        critical_tasks = []
        
        for suggestion in suggestions:
            if suggestion.wbs_level == 1:  # 从一级任务开始
                duration = self._calculate_task_duration(suggestion, suggestions)
                if duration > max_duration:
                    max_duration = duration
                    critical_tasks = self._get_task_chain(suggestion, suggestions)
        
        # 标记关键路径上的任务
        for task in critical_tasks:
            task.is_critical_path = True
    
    def _calculate_task_duration(
        self,
        task: AIWbsSuggestion,
        all_tasks: List[AIWbsSuggestion]
    ) -> float:
        """递归计算任务总工期"""
        
        # 获取子任务
        subtasks = [t for t in all_tasks if t.parent_wbs_id == task.id]
        
        if not subtasks:
            return task.estimated_duration_days or 0
        
        # 如果有子任务，返回子任务的总和
        return sum(self._calculate_task_duration(st, all_tasks) for st in subtasks)
    
    def _get_task_chain(
        self,
        task: AIWbsSuggestion,
        all_tasks: List[AIWbsSuggestion]
    ) -> List[AIWbsSuggestion]:
        """获取任务链"""
        
        chain = [task]
        subtasks = [t for t in all_tasks if t.parent_wbs_id == task.id]
        
        if subtasks:
            # 递归获取子任务链
            for subtask in subtasks:
                chain.extend(self._get_task_chain(subtask, all_tasks))
        
        return chain
