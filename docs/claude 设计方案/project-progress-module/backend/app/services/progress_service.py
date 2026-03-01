"""
进度计算服务 - 核心业务逻辑
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Project, WbsTask, TaskLog


class ProgressService:
    """进度计算服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_task_progress(
        self, 
        task_id: int, 
        new_progress: float,
        operator_id: int,
        operator_name: str,
        remark: str = None
    ) -> Dict[str, Any]:
        """
        更新任务进度，并级联更新父任务和项目进度
        
        Args:
            task_id: 任务ID
            new_progress: 新进度值(0-100)
            operator_id: 操作人ID
            operator_name: 操作人姓名
            remark: 备注
            
        Returns:
            dict: 包含任务进度和项目进度的结果
        """
        # 1. 获取任务
        task = self.db.query(WbsTask).filter(
            WbsTask.task_id == task_id,
            WbsTask.is_deleted == 0
        ).first()
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 2. 校验进度值
        if new_progress < 0 or new_progress > 100:
            raise ValueError("进度值必须在0-100之间")
        
        old_progress = float(task.progress_rate or 0)
        
        # 3. 更新任务进度
        task.progress_rate = Decimal(str(new_progress))
        
        # 如果进度100%，更新状态和实际结束日期
        if new_progress >= 100:
            task.status = '已完成'
            if not task.actual_end_date:
                task.actual_end_date = date.today()
        elif new_progress > 0 and task.status == '未开始':
            task.status = '进行中'
            if not task.actual_start_date:
                task.actual_start_date = date.today()
        
        # 4. 记录变更日志
        log = TaskLog(
            task_id=task_id,
            project_id=task.project_id,
            action='progress_update',
            field_name='progress_rate',
            old_value=str(old_progress),
            new_value=str(new_progress),
            remark=remark,
            operator_id=operator_id,
            operator_name=operator_name
        )
        self.db.add(log)
        
        # 5. 递归更新父任务进度
        if task.parent_id:
            self._update_parent_progress(task.parent_id)
        
        # 6. 更新项目进度
        project_progress = self._update_project_progress(task.project_id)
        
        # 7. 提交事务
        self.db.commit()
        
        return {
            'task_id': task_id,
            'task_progress': new_progress,
            'project_id': task.project_id,
            'project_progress': float(project_progress)
        }
    
    def _update_parent_progress(self, parent_id: int) -> None:
        """递归更新父任务进度（加权平均）"""
        # 获取所有子任务
        children = self.db.query(WbsTask).filter(
            WbsTask.parent_id == parent_id,
            WbsTask.is_deleted == 0
        ).all()
        
        if not children:
            return
        
        # 计算加权平均进度
        total_weight = sum(float(child.weight or 1) for child in children)
        if total_weight == 0:
            return
        
        weighted_progress = sum(
            float(child.progress_rate or 0) * float(child.weight or 1)
            for child in children
        )
        parent_progress = weighted_progress / total_weight
        
        # 更新父任务
        parent = self.db.query(WbsTask).filter(
            WbsTask.task_id == parent_id
        ).first()
        
        if parent:
            parent.progress_rate = Decimal(str(round(parent_progress, 2)))
            
            # 更新状态
            if parent_progress >= 100:
                parent.status = '已完成'
            elif parent_progress > 0:
                parent.status = '进行中'
            
            # 递归向上更新
            if parent.parent_id:
                self._update_parent_progress(parent.parent_id)
    
    def _update_project_progress(self, project_id: int) -> Decimal:
        """更新项目整体进度"""
        # 获取所有一级任务（阶段）
        phases = self.db.query(WbsTask).filter(
            WbsTask.project_id == project_id,
            WbsTask.level == 1,
            WbsTask.is_deleted == 0
        ).all()
        
        if not phases:
            return Decimal('0.00')
        
        # 计算加权平均进度
        total_weight = sum(float(phase.weight or 1) for phase in phases)
        if total_weight == 0:
            return Decimal('0.00')
        
        weighted_progress = sum(
            float(phase.progress_rate or 0) * float(phase.weight or 1)
            for phase in phases
        )
        project_progress = Decimal(str(round(weighted_progress / total_weight, 2)))
        
        # 更新项目
        project = self.db.query(Project).filter(
            Project.project_id == project_id
        ).first()
        
        if project:
            project.progress_rate = project_progress
            
            # 计划进度（按时间比例）
            plan_progress = self._calculate_plan_progress(project)
            project.plan_progress_rate = plan_progress
            
            # 计算SPI
            if plan_progress > 0:
                spi = float(project_progress) / float(plan_progress)
                project.spi = Decimal(str(round(spi, 2)))
                
                # 根据SPI设置健康状态
                if spi >= 0.95:
                    project.health_status = '绿'
                elif spi >= 0.85:
                    project.health_status = '黄'
                else:
                    project.health_status = '红'
            
            # 更新当前阶段
            current_phase = self._get_current_phase(project_id)
            if current_phase:
                project.current_phase = current_phase
        
        return project_progress
    
    def _calculate_plan_progress(self, project: Project) -> Decimal:
        """计算计划进度（按时间比例）"""
        today = date.today()
        
        if today <= project.plan_start_date:
            return Decimal('0.00')
        elif today >= project.plan_end_date:
            return Decimal('100.00')
        else:
            total_days = (project.plan_end_date - project.plan_start_date).days
            elapsed_days = (today - project.plan_start_date).days
            if total_days > 0:
                return Decimal(str(round(elapsed_days / total_days * 100, 2)))
            return Decimal('0.00')
    
    def _get_current_phase(self, project_id: int) -> Optional[str]:
        """获取当前阶段"""
        # 找到第一个未完成的阶段
        phase = self.db.query(WbsTask).filter(
            WbsTask.project_id == project_id,
            WbsTask.level == 1,
            WbsTask.is_deleted == 0,
            WbsTask.progress_rate < 100
        ).order_by(WbsTask.sort_order).first()
        
        if phase:
            return phase.task_name
        return None
    
    def update_progress_by_timesheet(
        self,
        task_id: int,
        hours: float,
        operator_id: int,
        operator_name: str
    ) -> Dict[str, Any]:
        """
        根据工时填报更新任务进度（工时法）
        
        Args:
            task_id: 任务ID
            hours: 填报工时
            operator_id: 操作人ID
            operator_name: 操作人姓名
        """
        task = self.db.query(WbsTask).filter(
            WbsTask.task_id == task_id,
            WbsTask.is_deleted == 0
        ).first()
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 累加实际工时
        task.actual_manhours = (task.actual_manhours or 0) + Decimal(str(hours))
        
        # 计算新进度（工时法）
        if task.plan_manhours and task.plan_manhours > 0:
            new_progress = float(task.actual_manhours) / float(task.plan_manhours) * 100
            new_progress = min(new_progress, 100)  # 最大100%
        else:
            new_progress = 0
        
        # 更新进度
        return self.update_task_progress(
            task_id=task_id,
            new_progress=new_progress,
            operator_id=operator_id,
            operator_name=operator_name,
            remark=f"工时填报触发，本次填报{hours}小时"
        )
    
    def batch_update_progress(
        self,
        updates: List[Dict[str, Any]],
        operator_id: int,
        operator_name: str
    ) -> List[Dict[str, Any]]:
        """
        批量更新进度
        
        Args:
            updates: [{"task_id": 1, "progress_rate": 50}, ...]
            operator_id: 操作人ID
            operator_name: 操作人姓名
        """
        results = []
        for item in updates:
            try:
                result = self.update_task_progress(
                    task_id=item['task_id'],
                    new_progress=item['progress_rate'],
                    operator_id=operator_id,
                    operator_name=operator_name
                )
                results.append({**result, 'success': True})
            except Exception as e:
                results.append({
                    'task_id': item['task_id'],
                    'success': False,
                    'error': str(e)
                })
        return results
    
    def get_project_progress_summary(self, project_id: int) -> Dict[str, Any]:
        """获取项目进度汇总"""
        project = self.db.query(Project).filter(
            Project.project_id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 任务统计
        task_stats = self.db.query(
            WbsTask.status,
            func.count(WbsTask.task_id).label('count')
        ).filter(
            WbsTask.project_id == project_id,
            WbsTask.is_deleted == 0,
            WbsTask.level > 1  # 排除阶段
        ).group_by(WbsTask.status).all()
        
        status_count = {s.status: s.count for s in task_stats}
        
        # 阶段进度
        phases = self.db.query(WbsTask).filter(
            WbsTask.project_id == project_id,
            WbsTask.level == 1,
            WbsTask.is_deleted == 0
        ).order_by(WbsTask.sort_order).all()
        
        phase_progress = [
            {
                'phase': p.task_name,
                'progress': float(p.progress_rate or 0),
                'status': p.status
            }
            for p in phases
        ]
        
        return {
            'project_id': project_id,
            'project_name': project.project_name,
            'progress_rate': float(project.progress_rate or 0),
            'plan_progress_rate': float(project.plan_progress_rate or 0),
            'spi': float(project.spi or 1),
            'health_status': project.health_status,
            'current_phase': project.current_phase,
            'status': project.status,
            'plan_start_date': str(project.plan_start_date),
            'plan_end_date': str(project.plan_end_date),
            'task_status_count': status_count,
            'phase_progress': phase_progress
        }
