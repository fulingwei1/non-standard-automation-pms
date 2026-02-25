# -*- coding: utf-8 -*-
"""
AI进度排期优化器
自动生成甘特图、优化关键路径、处理约束条件
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import Project
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation

logger = logging.getLogger(__name__)


class AIScheduleOptimizer:
    """AI进度排期优化器"""
    
    def __init__(self, db: Session):
        """
        初始化排期优化器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def optimize_schedule(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        优化项目进度排期
        
        Args:
            project_id: 项目ID
            start_date: 项目开始日期（None表示今天）
            constraints: 约束条件
            
        Returns:
            排期结果字典，包含甘特图数据、关键路径等
        """
        # 获取项目
        project = self.db.query(Project).get(project_id)
        if not project:
            logger.error(f"项目不存在: {project_id}")
            return {}
        
        # 获取所有WBS任务
        wbs_tasks = self.db.query(AIWbsSuggestion).filter(
            AIWbsSuggestion.project_id == project_id,
            AIWbsSuggestion.is_active == True
        ).order_by(AIWbsSuggestion.wbs_code).all()
        
        if not wbs_tasks:
            logger.warning(f"项目{project_id}没有WBS任务")
            return {}
        
        # 设置开始日期
        if not start_date:
            start_date = date.today()
        
        # 1. 执行关键路径法(CPM)计算
        cpm_result = self._calculate_cpm(wbs_tasks, start_date)
        
        # 2. 生成甘特图数据
        gantt_data = self._generate_gantt_data(
            wbs_tasks, cpm_result, start_date
        )
        
        # 3. 识别关键路径
        critical_path = self._identify_critical_path(wbs_tasks, cpm_result)
        
        # 4. 分析资源负载
        resource_load = self._analyze_resource_load(project_id, cpm_result)
        
        # 5. 检测冲突
        conflicts = self._detect_conflicts(wbs_tasks, cpm_result, resource_load)
        
        # 6. 生成优化建议
        recommendations = self._generate_recommendations(
            wbs_tasks, critical_path, conflicts, resource_load
        )
        
        return {
            "project_id": project_id,
            "start_date": start_date.isoformat(),
            "total_duration_days": cpm_result.get('total_duration', 0),
            "end_date": cpm_result.get('end_date'),
            "gantt_data": gantt_data,
            "critical_path": critical_path,
            "critical_path_length": len(critical_path),
            "resource_load": resource_load,
            "conflicts": conflicts,
            "recommendations": recommendations,
            "optimization_summary": {
                "total_tasks": len(wbs_tasks),
                "critical_tasks": len(critical_path),
                "conflicts_found": len(conflicts),
                "resource_utilization": self._calculate_resource_utilization(resource_load)
            }
        }
    
    def _calculate_cpm(
        self,
        tasks: List[AIWbsSuggestion],
        start_date: date
    ) -> Dict[str, Any]:
        """
        关键路径法(CPM)计算
        
        Returns:
            包含ES, EF, LS, LF, 浮动时间等信息
        """
        task_dict = {task.id: task for task in tasks}
        
        # 初始化
        es_dict = {}  # Earliest Start
        ef_dict = {}  # Earliest Finish
        ls_dict = {}  # Latest Start
        lf_dict = {}  # Latest Finish
        slack_dict = {}  # 浮动时间
        
        # 按拓扑排序（按WBS层级和序号）
        sorted_tasks = sorted(tasks, key=lambda t: (t.wbs_level, t.wbs_code))
        
        # 正向计算 ES 和 EF
        for task in sorted_tasks:
            duration = task.estimated_duration_days or 0
            
            # 获取前置任务
            predecessors = self._get_predecessors(task, task_dict)
            
            if not predecessors:
                # 无前置任务，从开始日期开始
                es_dict[task.id] = 0
            else:
                # 取所有前置任务的最晚结束时间
                max_ef = max(ef_dict.get(p.id, 0) for p in predecessors)
                es_dict[task.id] = max_ef
            
            ef_dict[task.id] = es_dict[task.id] + duration
        
        # 项目总工期
        total_duration = max(ef_dict.values()) if ef_dict else 0
        end_date = start_date + timedelta(days=int(total_duration))
        
        # 反向计算 LS 和 LF
        for task in reversed(sorted_tasks):
            duration = task.estimated_duration_days or 0
            
            # 获取后继任务
            successors = self._get_successors(task, task_dict)
            
            if not successors:
                # 无后继任务，LF = 项目结束时间
                lf_dict[task.id] = total_duration
            else:
                # 取所有后继任务的最早开始时间
                min_ls = min(ls_dict.get(s.id, total_duration) for s in successors)
                lf_dict[task.id] = min_ls
            
            ls_dict[task.id] = lf_dict[task.id] - duration
            
            # 计算浮动时间（总时差）
            slack_dict[task.id] = ls_dict[task.id] - es_dict[task.id]
        
        return {
            'es': es_dict,
            'ef': ef_dict,
            'ls': ls_dict,
            'lf': lf_dict,
            'slack': slack_dict,
            'total_duration': total_duration,
            'end_date': end_date.isoformat()
        }
    
    def _get_predecessors(
        self,
        task: AIWbsSuggestion,
        task_dict: Dict[int, AIWbsSuggestion]
    ) -> List[AIWbsSuggestion]:
        """获取前置任务"""
        
        predecessors = []
        
        if task.dependencies:
            try:
                deps = json.loads(task.dependencies)
                for dep in deps:
                    dep_id = dep.get('task_id')
                    if dep_id and dep_id in task_dict:
                        predecessors.append(task_dict[dep_id])
            except:
                pass
        
        return predecessors
    
    def _get_successors(
        self,
        task: AIWbsSuggestion,
        task_dict: Dict[int, AIWbsSuggestion]
    ) -> List[AIWbsSuggestion]:
        """获取后继任务"""
        
        successors = []
        
        for other_task in task_dict.values():
            if other_task.dependencies:
                try:
                    deps = json.loads(other_task.dependencies)
                    for dep in deps:
                        if dep.get('task_id') == task.id:
                            successors.append(other_task)
                            break
                except:
                    pass
        
        return successors
    
    def _generate_gantt_data(
        self,
        tasks: List[AIWbsSuggestion],
        cpm_result: Dict,
        start_date: date
    ) -> List[Dict]:
        """生成甘特图数据"""
        
        gantt_data = []
        es_dict = cpm_result.get('es', {})
        ef_dict = cpm_result.get('ef', {})
        slack_dict = cpm_result.get('slack', {})
        
        for task in tasks:
            es = es_dict.get(task.id, 0)
            ef = ef_dict.get(task.id, 0)
            slack = slack_dict.get(task.id, 0)
            
            task_start = start_date + timedelta(days=int(es))
            task_end = start_date + timedelta(days=int(ef))
            
            gantt_data.append({
                "task_id": task.id,
                "task_name": task.task_name,
                "wbs_code": task.wbs_code,
                "level": task.wbs_level,
                "parent_id": task.parent_wbs_id,
                "start_date": task_start.isoformat(),
                "end_date": task_end.isoformat(),
                "duration_days": task.estimated_duration_days,
                "es": es,
                "ef": ef,
                "slack": slack,
                "is_critical": slack == 0,
                "progress": 0,  # 初始进度为0
                "assignees": [],  # 稍后填充
            })
        
        return gantt_data
    
    def _identify_critical_path(
        self,
        tasks: List[AIWbsSuggestion],
        cpm_result: Dict
    ) -> List[Dict]:
        """识别关键路径"""
        
        slack_dict = cpm_result.get('slack', {})
        
        # 关键路径上的任务：浮动时间为0
        critical_tasks = [
            {
                "task_id": task.id,
                "task_name": task.task_name,
                "wbs_code": task.wbs_code,
                "duration_days": task.estimated_duration_days
            }
            for task in tasks
            if slack_dict.get(task.id, 0) == 0
        ]
        
        return critical_tasks
    
    def _analyze_resource_load(
        self,
        project_id: int,
        cpm_result: Dict
    ) -> Dict[int, Dict]:
        """分析资源负载"""
        
        # 获取所有资源分配
        allocations = self.db.query(AIResourceAllocation).filter(
            AIResourceAllocation.project_id == project_id,
            AIResourceAllocation.is_active == True
        ).all()
        
        resource_load = {}
        
        for alloc in allocations:
            user_id = alloc.user_id
            
            if user_id not in resource_load:
                resource_load[user_id] = {
                    "user_id": user_id,
                    "total_hours": 0,
                    "task_count": 0,
                    "tasks": []
                }
            
            resource_load[user_id]["total_hours"] += alloc.allocated_hours or 0
            resource_load[user_id]["task_count"] += 1
            resource_load[user_id]["tasks"].append({
                "wbs_id": alloc.wbs_suggestion_id,
                "hours": alloc.allocated_hours,
                "match_score": alloc.overall_match_score
            })
        
        return resource_load
    
    def _detect_conflicts(
        self,
        tasks: List[AIWbsSuggestion],
        cpm_result: Dict,
        resource_load: Dict
    ) -> List[Dict]:
        """检测冲突"""
        
        conflicts = []
        
        # 1. 检测资源过载
        for user_id, load in resource_load.items():
            # 假设每人每月工作160小时
            if load["total_hours"] > 160 * 3:  # 3个月
                conflicts.append({
                    "type": "RESOURCE_OVERLOAD",
                    "severity": "HIGH",
                    "user_id": user_id,
                    "description": f"用户{user_id}工作负载过高：{load['total_hours']}小时",
                    "recommendation": "考虑增加人手或延长工期"
                })
        
        # 2. 检测关键路径风险
        slack_dict = cpm_result.get('slack', {})
        critical_tasks = [t for t in tasks if slack_dict.get(t.id, 0) == 0]
        
        if len(critical_tasks) > len(tasks) * 0.5:
            conflicts.append({
                "type": "TOO_MANY_CRITICAL_TASKS",
                "severity": "MEDIUM",
                "description": f"关键路径任务过多（{len(critical_tasks)}/{len(tasks)}）",
                "recommendation": "考虑并行化部分任务或增加缓冲时间"
            })
        
        # 3. 检测任务工期异常
        for task in tasks:
            if task.estimated_duration_days and task.estimated_duration_days > 60:
                conflicts.append({
                    "type": "TASK_TOO_LONG",
                    "severity": "LOW",
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "description": f"任务工期过长：{task.estimated_duration_days}天",
                    "recommendation": "建议进一步分解任务"
                })
        
        return conflicts
    
    def _generate_recommendations(
        self,
        tasks: List[AIWbsSuggestion],
        critical_path: List[Dict],
        conflicts: List[Dict],
        resource_load: Dict
    ) -> List[Dict]:
        """生成优化建议"""
        
        recommendations = []
        
        # 1. 关键路径优化建议
        if critical_path:
            recommendations.append({
                "category": "CRITICAL_PATH",
                "priority": "HIGH",
                "title": "关注关键路径任务",
                "description": f"项目有{len(critical_path)}个关键任务，任何延期都会影响项目工期",
                "actions": [
                    "为关键任务分配最优秀的人员",
                    "增加关键任务的监控频率",
                    "为关键任务预留应急资源"
                ]
            })
        
        # 2. 资源平衡建议
        avg_load = sum(r["total_hours"] for r in resource_load.values()) / len(resource_load) if resource_load else 0
        max_load = max((r["total_hours"] for r in resource_load.values()), default=0)
        
        if max_load > avg_load * 2:
            recommendations.append({
                "category": "RESOURCE_BALANCE",
                "priority": "MEDIUM",
                "title": "资源分配不均衡",
                "description": "部分成员工作负载显著高于平均水平",
                "actions": [
                    "重新分配任务，平衡工作负载",
                    "考虑增加人手支援高负载成员"
                ]
            })
        
        # 3. 风险管理建议
        high_risk_tasks = [t for t in tasks if t.risk_level in ['HIGH', 'CRITICAL']]
        if high_risk_tasks:
            recommendations.append({
                "category": "RISK_MANAGEMENT",
                "priority": "HIGH",
                "title": "高风险任务需特别关注",
                "description": f"发现{len(high_risk_tasks)}个高风险任务",
                "actions": [
                    "制定详细的风险应对计划",
                    "为高风险任务增加缓冲时间",
                    "建立风险监控机制"
                ]
            })
        
        return recommendations
    
    def _calculate_resource_utilization(self, resource_load: Dict) -> float:
        """计算资源利用率"""
        
        if not resource_load:
            return 0.0
        
        # 简化计算：总工时 / (人数 * 标准工时)
        total_hours = sum(r["total_hours"] for r in resource_load.values())
        resource_count = len(resource_load)
        standard_hours = 160 * 3  # 3个月，每月160小时
        
        utilization = (total_hours / (resource_count * standard_hours)) * 100 if resource_count > 0 else 0
        
        return min(utilization, 100.0)
