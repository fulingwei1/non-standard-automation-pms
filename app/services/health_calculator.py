# -*- coding: utf-8 -*-
"""
项目健康度自动计算服务

根据项目状态、里程碑、问题、缺料、预警等多维度指标自动计算项目健康度
健康度等级：
- H1: 正常(绿色) - On Track
- H2: 有风险(黄色) - At Risk
- H3: 阻塞(红色) - Blocked
- H4: 已完结(灰色) - Closed
"""

from typing import Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.project import Project, ProjectMilestone, ProjectStatusLog
from app.models.issue import Issue, IssueTypeEnum
from app.models.alert import AlertRecord, AlertRule
from app.models.shortage import ShortageReport
from app.models.enums import ProjectHealthEnum, IssueStatusEnum, AlertLevelEnum
from app.models.progress import Task


class HealthCalculator:
    """项目健康度计算器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_health(self, project: Project) -> str:
        """
        计算项目健康度
        
        Args:
            project: 项目对象
            
        Returns:
            str: 健康度编码 (H1/H2/H3/H4)
        """
        # H4: 已完结 - 最高优先级
        if self._is_closed(project):
            return ProjectHealthEnum.H4.value
        
        # H3: 阻塞 - 次高优先级
        if self._is_blocked(project):
            return ProjectHealthEnum.H3.value
        
        # H2: 有风险
        if self._has_risks(project):
            return ProjectHealthEnum.H2.value
        
        # H1: 正常
        return ProjectHealthEnum.H1.value
    
    def _is_closed(self, project: Project) -> bool:
        """
        判断项目是否已完结
        
        条件：
        - 状态为 ST30(已结项) 或 ST99(项目取消)
        """
        closed_statuses = ['ST30', 'ST99']
        return project.status in closed_statuses
    
    def _is_blocked(self, project: Project) -> bool:
        """
        判断项目是否阻塞
        
        条件：
        1. 状态为阻塞状态：ST14(缺料阻塞)、ST19(技术阻塞)
        2. 有关键任务阻塞
        3. 有严重阻塞问题未解决
        4. 有严重缺料预警
        """
        # 1. 检查状态
        blocked_statuses = ['ST14', 'ST19']  # 缺料阻塞、技术阻塞
        if project.status in blocked_statuses:
            return True
        
        # 2. 检查关键任务阻塞
        if self._has_blocked_critical_tasks(project):
            return True
        
        # 3. 检查严重阻塞问题
        if self._has_blocking_issues(project):
            return True
        
        # 4. 检查严重缺料预警
        if self._has_critical_shortage_alerts(project):
            return True
        
        return False
    
    def _has_risks(self, project: Project) -> bool:
        """
        判断项目是否有风险
        
        条件：
        1. 状态为整改中：ST22(FAT整改中)、ST26(SAT整改中)
        2. 交期临近（7天内）
        3. 有逾期里程碑
        4. 有缺料预警（非严重）
        5. 有未解决的高优先级问题
        6. 进度偏差超过阈值
        """
        # 1. 检查整改状态
        rectification_statuses = ['ST22', 'ST26']  # FAT整改中、SAT整改中
        if project.status in rectification_statuses:
            return True
        
        # 2. 检查交期临近
        if self._is_deadline_approaching(project, days=7):
            return True
        
        # 3. 检查逾期里程碑
        if self._has_overdue_milestones(project):
            return True
        
        # 4. 检查缺料预警
        if self._has_shortage_warnings(project):
            return True
        
        # 5. 检查高优先级问题
        if self._has_high_priority_issues(project):
            return True
        
        # 6. 检查进度偏差
        if self._has_schedule_variance(project, threshold=10):
            return True
        
        return False
    
    def _has_blocked_critical_tasks(self, project: Project) -> bool:
        """
        检查是否有关键任务阻塞
        
        Returns:
            bool: 如果有关键任务阻塞返回True
        """
        # 查询项目的关键任务，状态为阻塞
        # 注意：Task表中没有is_critical字段，这里先查询阻塞的任务
        blocked_tasks = self.db.query(Task).filter(
            Task.project_id == project.id,
            Task.status == 'BLOCKED'
        ).count()
        
        return blocked_tasks > 0
    
    def _has_blocking_issues(self, project: Project) -> bool:
        """
        检查是否有严重阻塞问题
        
        Returns:
            bool: 如果有严重阻塞问题返回True
        """
        # 查询项目的阻塞类型问题，状态为开放或处理中
        blocking_issues = self.db.query(Issue).filter(
            Issue.project_id == project.id,
            Issue.issue_type == IssueTypeEnum.BLOCKER,
            Issue.status.in_([IssueStatusEnum.OPEN.value, IssueStatusEnum.PROCESSING.value])
        ).count()
        
        return blocking_issues > 0
    
    def _has_critical_shortage_alerts(self, project: Project) -> bool:
        """
        检查是否有严重缺料预警
        
        Returns:
            bool: 如果有严重缺料预警返回True
        """
        # 查询项目的严重级别缺料预警（通过AlertRecord）
        critical_alerts = self.db.query(AlertRecord).join(
            AlertRule, AlertRecord.rule_id == AlertRule.id
        ).filter(
            AlertRecord.project_id == project.id,
            AlertRecord.alert_level == AlertLevelEnum.CRITICAL.value,
            AlertRecord.status == 'PENDING',  # 未处理的预警
            AlertRule.rule_type == 'MATERIAL_SHORTAGE'  # 缺料预警类型
        ).count()
        
        return critical_alerts > 0
    
    def _is_deadline_approaching(self, project: Project, days: int = 7) -> bool:
        """
        检查交期是否临近
        
        Args:
            project: 项目对象
            days: 提前预警天数，默认7天
            
        Returns:
            bool: 如果交期临近返回True
        """
        if not project.planned_end_date:
            return False
        
        today = date.today()
        days_until_deadline = (project.planned_end_date - today).days
        
        # 交期在指定天数内且未完成
        return 0 <= days_until_deadline <= days
    
    def _has_overdue_milestones(self, project: Project) -> bool:
        """
        检查是否有逾期里程碑
        
        Returns:
            bool: 如果有逾期里程碑返回True
        """
        today = date.today()
        
        # 查询项目的逾期里程碑（计划日期已过但未完成）
        overdue_milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id,
            ProjectMilestone.planned_date < today,
            ProjectMilestone.status != 'COMPLETED',
            ProjectMilestone.is_key == True  # 只检查关键里程碑
        ).count()
        
        return overdue_milestones > 0
    
    def _has_shortage_warnings(self, project: Project) -> bool:
        """
        检查是否有缺料预警（非严重）
        
        Returns:
            bool: 如果有缺料预警返回True
        """
        # 查询项目的警告级别缺料预警（通过AlertRecord）
        warning_alerts = self.db.query(AlertRecord).join(
            AlertRule, AlertRecord.rule_id == AlertRule.id
        ).filter(
            AlertRecord.project_id == project.id,
            AlertRecord.alert_level.in_([
                AlertLevelEnum.WARNING.value,
                AlertLevelEnum.URGENT.value
            ]),
            AlertRecord.status == 'PENDING',  # 未处理的预警
            AlertRule.rule_type == 'MATERIAL_SHORTAGE'  # 缺料预警类型
        ).count()
        
        return warning_alerts > 0
    
    def _has_high_priority_issues(self, project: Project) -> bool:
        """
        检查是否有高优先级未解决问题
        
        Returns:
            bool: 如果有高优先级问题返回True
        """
        # 查询项目的高优先级问题，状态为开放或处理中
        high_priority_issues = self.db.query(Issue).filter(
            Issue.project_id == project.id,
            Issue.priority.in_(['HIGH', 'URGENT']),
            Issue.status.in_([IssueStatusEnum.OPEN.value, IssueStatusEnum.PROCESSING.value])
        ).count()
        
        return high_priority_issues > 0
    
    def _has_schedule_variance(self, project: Project, threshold: float = 10.0) -> bool:
        """
        检查进度偏差是否超过阈值
        
        Args:
            project: 项目对象
            threshold: 偏差阈值（百分比），默认10%
            
        Returns:
            bool: 如果进度偏差超过阈值返回True
        """
        if not project.planned_end_date or not project.actual_start_date:
            return False
        
        # 计算计划进度
        today = date.today()
        total_days = (project.planned_end_date - project.planned_start_date).days
        elapsed_days = (today - project.planned_start_date).days
        
        if total_days <= 0:
            return False
        
        planned_progress = (elapsed_days / total_days) * 100

        # 计算偏差 (确保类型一致，progress_pct 可能是 Decimal)
        actual_progress = float(project.progress_pct or 0)
        variance = planned_progress - actual_progress
        
        # 如果实际进度落后计划进度超过阈值，认为有风险
        return variance > threshold
    
    def calculate_and_update(self, project: Project, auto_save: bool = True) -> Dict[str, Any]:
        """
        计算健康度并更新项目
        
        Args:
            project: 项目对象
            auto_save: 是否自动保存到数据库
            
        Returns:
            dict: 计算结果
        """
        old_health = project.health
        new_health = self.calculate_health(project)
        
        result = {
            'project_id': project.id,
            'project_code': project.project_code,
            'old_health': old_health,
            'new_health': new_health,
            'changed': old_health != new_health,
            'calculation_time': datetime.now().isoformat()
        }
        
        # 如果健康度发生变化，更新项目
        if old_health != new_health and auto_save:
            project.health = new_health
            self.db.add(project)
            
            # 记录状态变更历史
            status_log = ProjectStatusLog(
                project_id=project.id,
                old_stage=project.stage,
                new_stage=project.stage,
                old_status=project.status,
                new_status=project.status,
                old_health=old_health,
                new_health=new_health,
                change_type="HEALTH_AUTO_CALCULATED",
                changed_by=None,  # 系统自动计算
                changed_at=datetime.now(),
                remark=f"系统自动计算健康度：{old_health} -> {new_health}"
            )
            self.db.add(status_log)
            self.db.commit()
            self.db.refresh(project)
        
        return result
    
    def batch_calculate(self, project_ids: Optional[list] = None, batch_size: int = 100) -> Dict[str, Any]:
        """
        Issue 5.2: 批量计算项目健康度（性能优化）
        
        Args:
            project_ids: 项目ID列表，如果为None则计算所有活跃项目
            batch_size: 批处理大小（默认100，避免一次性加载过多数据）
            
        Returns:
            dict: 批量计算结果
        """
        # 查询项目（Sprint 5.2: 性能优化 - 只查询必要字段）
        query = self.db.query(Project).filter(
            Project.is_active == True,
            Project.is_archived == False
        )
        
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))
        
        # Sprint 5.2: 性能优化 - 分批处理，避免一次性加载过多数据
        total_count = query.count()
        results = {
            'total': total_count,
            'updated': 0,
            'unchanged': 0,
            'details': []
        }
        
        # 分批处理
        for offset in range(0, total_count, batch_size):
            projects = query.offset(offset).limit(batch_size).all()
            
            for project in projects:
                result = self.calculate_and_update(project, auto_save=False)  # 先不保存，批量提交
                results['details'].append(result)
                
                if result['changed']:
                    results['updated'] += 1
                else:
                    results['unchanged'] += 1
            
            # 每批处理完后提交一次，减少数据库事务开销
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"批量计算健康度提交失败：{str(e)}", exc_info=True)
        
        return results
    
    def get_health_details(self, project: Project) -> Dict[str, Any]:
        """
        获取项目健康度详细信息（用于诊断）
        
        Args:
            project: 项目对象
            
        Returns:
            dict: 健康度详细信息
        """
        return {
            'project_id': project.id,
            'project_code': project.project_code,
            'current_health': project.health,
            'calculated_health': self.calculate_health(project),
            'status': project.status,
            'stage': project.stage,
            'checks': {
                'is_closed': self._is_closed(project),
                'is_blocked': self._is_blocked(project),
                'has_risks': self._has_risks(project),
                'has_blocked_critical_tasks': self._has_blocked_critical_tasks(project),
                'has_blocking_issues': self._has_blocking_issues(project),
                'has_critical_shortage_alerts': self._has_critical_shortage_alerts(project),
                'is_deadline_approaching': self._is_deadline_approaching(project),
                'has_overdue_milestones': self._has_overdue_milestones(project),
                'has_shortage_warnings': self._has_shortage_warnings(project),
                'has_high_priority_issues': self._has_high_priority_issues(project),
                'has_schedule_variance': self._has_schedule_variance(project)
            },
            'statistics': {
                'blocked_tasks': self.db.query(Task).filter(
                    Task.project_id == project.id,
                    Task.status == 'BLOCKED'
                ).count(),
                'blocking_issues': self.db.query(Issue).filter(
                    Issue.project_id == project.id,
                    Issue.issue_type == IssueTypeEnum.BLOCKER,
                    Issue.status.in_([IssueStatusEnum.OPEN.value, IssueStatusEnum.PROCESSING.value])
                ).count(),
                'overdue_milestones': self.db.query(ProjectMilestone).filter(
                    ProjectMilestone.project_id == project.id,
                    ProjectMilestone.planned_date < date.today(),
                    ProjectMilestone.status != 'COMPLETED',
                    ProjectMilestone.is_key == True
                ).count(),
                'active_alerts': self.db.query(AlertRecord).filter(
                    AlertRecord.project_id == project.id,
                    AlertRecord.status == 'PENDING'
                ).count()
            }
        }

