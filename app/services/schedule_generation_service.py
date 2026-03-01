# -*- coding: utf-8 -*-
"""
AI 智能排程服务

基于历史项目数据自动生成项目计划
支持正常强度和高强度两种模式
"""

from typing import Any, Dict, List, Optional
from datetime import date, timedelta
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.project_schedule import ProjectSchedulePlan, ScheduleTask
from app.models.project import Project
from app.models.user import User
from app.models.engineer_capacity import EngineerCapacity


class ScheduleGenerationService:
    """AI 智能排程服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_schedule(
        self,
        project_id: int,
        mode: str = 'NORMAL',
        team_members: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        生成项目进度计划
        
        Args:
            project_id: 项目 ID
            mode: 计划模式 NORMAL/INTENSIVE
            team_members: 团队成员列表（可选，不填则基于项目估算）
        
        Returns:
            项目计划数据
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}
        
        # 1. 分析历史类似项目
        historical_data = self._analyze_historical_projects(project)
        
        # 2. 确定项目阶段和任务
        phases_tasks = self._determine_phases_and_tasks(project, mode)
        
        # 3. 计算效率系数
        efficiency_factors = self._calculate_efficiency_factors(team_members)
        
        # 4. 生成任务时间表
        scheduled_tasks = self._schedule_tasks(
            phases_tasks,
            historical_data,
            efficiency_factors,
            mode,
        )
        
        # 5. 计算关键路径和总工期
        critical_path = self._calculate_critical_path(scheduled_tasks)
        
        # 6. 生成计划
        schedule_plan = self._create_schedule_plan(
            project,
            scheduled_tasks,
            critical_path,
            efficiency_factors,
            mode,
        )
        
        return schedule_plan
    
    def _analyze_historical_projects(self, project: Project) -> Dict[str, Any]:
        """分析历史类似项目数据"""
        
        # 查询类似项目的工期数据
        similar_projects = self.db.query(Project)\
            .filter(
                Project.product_category == project.product_category,
                Project.industry == project.industry,
                Project.id != project.id,
                Project.status.in_(['COMPLETED', 'DELIVERED']),
            )\
            .limit(10)\
            .all()
        
        if not similar_projects:
            # 无历史数据，使用默认值
            return self._get_default_historical_data()
        
        # 统计工期
        durations = []
        for p in similar_projects:
            if p.planned_start_date and p.planned_end_date:
                duration = (p.planned_end_date - p.planned_start_date).days
                if 0 < duration < 365:
                    durations.append(duration)
        
        if not durations:
            return self._get_default_historical_data()
        
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        # 按阶段统计（5 个部门环节）
        phase_durations = {
            'engineering': avg_duration * 0.25,    # 工程技术部 25%
            'procurement': avg_duration * 0.20,    # 采购 20%
            'production': avg_duration * 0.30,     # 生产 30%
            'shipping': avg_duration * 0.10,       # 发货 10%
            'acceptance': avg_duration * 0.15,     # 验收 15%
        }
        
        return {
            'sample_count': len(durations),
            'avg_duration': round(avg_duration, 0),
            'min_duration': min_duration,
            'max_duration': max_duration,
            'phase_durations': phase_durations,
            'confidence': 'HIGH' if len(durations) >= 5 else 'MEDIUM' if len(durations) >= 3 else 'LOW',
        }
    
    def _get_default_historical_data(self) -> Dict[str, Any]:
        """默认历史数据（无历史项目时）"""
        return {
            'sample_count': 0,
            'avg_duration': 60,  # 默认 60 天
            'min_duration': 45,
            'max_duration': 90,
            'phase_durations': {
                'design': 15,
                'procurement': 12,
                'assembly': 18,
                'debug': 9,
                'delivery': 6,
            },
            'confidence': 'LOW',
        }
    
    def _determine_phases_and_tasks(
        self,
        project: Project,
        mode: str,
    ) -> Dict[str, List[Dict]]:
        """确定项目阶段和任务"""
        
        product_category = project.product_category or ''
        
        # 基础阶段定义（公司实际 5 个部门环节）
        phases = {
            'engineering': {
                'name': '工程技术部',
                'department': '工程技术部',
                'tasks': [
                    {'name': '需求分析与技术方案', 'duration_factor': 0.25},
                    {'name': '机械/电气/软件设计', 'duration_factor': 0.35},
                    {'name': '设计评审与优化', 'duration_factor': 0.25},
                    {'name': 'BOM 清单输出', 'duration_factor': 0.15},
                ],
            },
            'procurement': {
                'name': '采购',
                'department': '采购部',
                'tasks': [
                    {'name': '供应商询价比价', 'duration_factor': 0.25},
                    {'name': '采购下单与合同', 'duration_factor': 0.20},
                    {'name': '物料跟催与到货', 'duration_factor': 0.35},
                    {'name': '来料检验入库', 'duration_factor': 0.20},
                ],
            },
            'production': {
                'name': '生产',
                'department': '生产部',
                'tasks': [
                    {'name': '机械装配', 'duration_factor': 0.35},
                    {'name': '电气装配与接线', 'duration_factor': 0.35},
                    {'name': '单机调试', 'duration_factor': 0.20},
                    {'name': '厂内联调测试', 'duration_factor': 0.10},
                ],
            },
            'shipping': {
                'name': '发货',
                'department': '物流部',
                'tasks': [
                    {'name': '包装与防护', 'duration_factor': 0.30},
                    {'name': '物流安排与装车', 'duration_factor': 0.25},
                    {'name': '运输与跟踪', 'duration_factor': 0.30},
                    {'name': '现场卸货与就位', 'duration_factor': 0.15},
                ],
            },
            'acceptance': {
                'name': '验收',
                'department': '项目部',
                'tasks': [
                    {'name': '现场安装调试', 'duration_factor': 0.30},
                    {'name': '客户培训', 'duration_factor': 0.25},
                    {'name': 'FAT/SAT 验收测试', 'duration_factor': 0.30},
                    {'name': '验收报告与归档', 'duration_factor': 0.15},
                ],
            },
        }
        
        # 根据模式调整工期
        duration_multiplier = 1.0 if mode == 'NORMAL' else 0.7  # 高强度模式缩短 30%
        
        # 应用 multiplier
        for phase_key, phase in phases.items():
            for task in phase['tasks']:
                task['adjusted_duration_factor'] = task['duration_factor'] * duration_multiplier
        
        return phases
    
    def _calculate_efficiency_factors(
        self,
        team_members: Optional[List[Dict]],
    ) -> Dict[str, float]:
        """计算效率系数"""
        
        if not team_members:
            return {
                'team_efficiency': 1.0,
                'ai_boost': 1.0,
                'multi_project_factor': 1.0,
                'overall_factor': 1.0,
            }
        
        # 计算团队平均效率
        ai_boosts = []
        multi_project_efficiencies = []
        
        for member in team_members:
            capacity = member.get('capacity')
            if capacity:
                ai_boosts.append(getattr(capacity, 'ai_efficiency_boost', 1.0))
                multi_project_efficiencies.append(
                    getattr(capacity, 'multi_project_efficiency', 1.0)
                )
        
        avg_ai_boost = sum(ai_boosts) / len(ai_boosts) if ai_boosts else 1.0
        avg_multi_project = sum(multi_project_efficiencies) / len(multi_project_efficiencies) if multi_project_efficiencies else 1.0
        
        # 整体效率系数
        overall = avg_ai_boost * avg_multi_project
        
        return {
            'team_efficiency': round(avg_multi_project, 2),
            'ai_boost': round(avg_ai_boost, 2),
            'multi_project_factor': round(avg_multi_project, 2),
            'overall_factor': round(overall, 2),
        }
    
    def _schedule_tasks(
        self,
        phases_tasks: Dict,
        historical_data: Dict,
        efficiency_factors: Dict,
        mode: str,
    ) -> List[Dict]:
        """生成任务时间表"""
        
        tasks = []
        current_day = 0
        
        for phase_key, phase in phases_tasks.items():
            phase_duration = historical_data['phase_durations'].get(phase_key, 10)
            
            # 应用效率调整
            if mode == 'INTENSIVE':
                phase_duration *= 0.7  # 高强度缩短 30%
            
            phase_duration /= efficiency_factors['overall_factor']
            phase_duration = max(1, int(phase_duration))
            
            # 分配任务工期
            total_factor = sum(t['adjusted_duration_factor'] for t in phase['tasks'])
            
            for task in phase['tasks']:
                task_duration = int(phase_duration * task['adjusted_duration_factor'] / total_factor)
                task_duration = max(1, task_duration)
                
                tasks.append({
                    'phase': phase_key,
                    'phase_name': phase['name'],
                    'task_name': task['name'],
                    'base_duration': task_duration,
                    'duration': task_duration,
                    'start_day': current_day,
                    'end_day': current_day + task_duration - 1,
                    'predecessors': [],  # 后续计算
                })
                
                current_day += task_duration
            
            # 阶段间留 1 天缓冲
            current_day += 1
        
        # 计算依赖关系
        for i, task in enumerate(tasks):
            if i > 0:
                # 简单 FS 依赖
                task['predecessors'] = [tasks[i-1]['task_name']]
        
        return tasks
    
    def _calculate_critical_path(self, tasks: List[Dict]) -> Dict[str, Any]:
        """计算关键路径"""
        
        if not tasks:
            return {'total_days': 0, 'critical_tasks': []}
        
        # 简单计算：最后一个任务的结束日期
        total_days = max(t['end_day'] for t in tasks) + 1
        
        # 关键任务（所有任务都在关键路径上，简化处理）
        critical_tasks = [t['task_name'] for t in tasks]
        
        return {
            'total_days': total_days,
            'critical_tasks': critical_tasks,
        }
    
    def _create_schedule_plan(
        self,
        project: Project,
        scheduled_tasks: List[Dict],
        critical_path: Dict,
        efficiency_factors: Dict,
        mode: str,
    ) -> Dict[str, Any]:
        """创建计划方案"""
        
        from datetime import timedelta
        
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=critical_path['total_days'])
        
        # 模式名称
        mode_names = {
            'NORMAL': '正常强度',
            'INTENSIVE': '高强度（加速）',
        }
        
        # 按阶段分组
        phases_summary = {}
        for task in scheduled_tasks:
            phase = task['phase']
            if phase not in phases_summary:
                phases_summary[phase] = {
                    'name': task['phase_name'],
                    'tasks': [],
                    'duration': 0,
                }
            phases_summary[phase]['tasks'].append(task)
            phases_summary[phase]['duration'] += task['duration']
        
        return {
            'project_id': project.id,
            'project_name': project.project_name,
            'schedule_mode': mode,
            'mode_name': mode_names.get(mode, mode),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_days': critical_path['total_days'],
            'working_days': critical_path['total_days'],  # 简化
            'team_efficiency_factor': efficiency_factors.get('team_efficiency', 1.0),
            'ai_boost_factor': efficiency_factors.get('ai_boost', 1.0),
            'overall_efficiency': efficiency_factors.get('overall_factor', 1.0),
            'phases': phases_summary,
            'tasks': scheduled_tasks,
            'critical_path': critical_path,
            'buffer_days': int(critical_path['total_days'] * 0.1),  # 10% 缓冲
        }
    
    def save_schedule_plan(
        self,
        schedule_data: Dict[str, Any],
        created_by: int,
    ) -> ProjectSchedulePlan:
        """保存计划方案"""
        from datetime import datetime
        
        plan = ProjectSchedulePlan(
            plan_no=f"PSP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_id=schedule_data['project_id'],
            project_name=schedule_data['project_name'],
            schedule_mode=schedule_data['schedule_mode'],
            mode_name=schedule_data['mode_name'],
            start_date=date.fromisoformat(schedule_data['start_date']),
            end_date=date.fromisoformat(schedule_data['end_date']),
            total_days=schedule_data['total_days'],
            team_efficiency_factor=schedule_data.get('team_efficiency_factor', 1.0),
            ai_boost_factor=schedule_data.get('ai_boost_factor', 1.0),
            phases=json.dumps(schedule_data['phases']),
            tasks=json.dumps(schedule_data['tasks']),
            status='DRAFT',
            created_by=created_by,
        )
        
        self.db.add(plan)
        self.db.flush()
        
        # 添加任务
        for idx, task_data in enumerate(schedule_data['tasks'], 1):
            task = ScheduleTask(
                schedule_plan_id=plan.id,
                task_no=f"T{idx:03d}",
                task_name=task_data['task_name'],
                task_type=task_data.get('phase', 'GENERAL').upper(),
                phase=task_data['phase'],
                planned_start_date=date.today() + timedelta(days=task_data['start_day']),
                planned_end_date=date.today() + timedelta(days=task_data['end_day']),
                duration_days=task_data['duration'],
                base_duration=task_data.get('base_duration', task_data['duration']),
            )
            self.db.add(task)
        
        self.db.commit()
        self.db.refresh(plan)
        
        return plan
