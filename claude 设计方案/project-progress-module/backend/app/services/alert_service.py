"""
预警服务 - 进度预警规则引擎
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    Project, WbsTask, TaskAssignment, ProgressAlert, 
    WorkloadSnapshot
)


class AlertRule:
    """预警规则基类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check(self) -> List[ProgressAlert]:
        raise NotImplementedError
    
    def create_alert(
        self,
        project_id: int,
        task_id: Optional[int],
        alert_type: str,
        alert_level: str,
        title: str,
        content: str,
        trigger_value: str,
        threshold_value: str,
        notify_users: List[int]
    ) -> ProgressAlert:
        alert = ProgressAlert(
            project_id=project_id,
            task_id=task_id,
            alert_type=alert_type,
            alert_level=alert_level,
            alert_title=title,
            alert_content=content,
            trigger_value=trigger_value,
            threshold_value=threshold_value,
            notify_users=",".join(map(str, notify_users)),
            status="待处理"
        )
        self.db.add(alert)
        return alert


class TaskOverdueRule(AlertRule):
    """任务逾期预警"""
    
    def check(self) -> List[ProgressAlert]:
        alerts = []
        today = date.today()
        
        overdue_tasks = self.db.query(WbsTask).filter(
            WbsTask.is_deleted == 0,
            WbsTask.status.notin_(['已完成', '取消']),
            WbsTask.plan_end_date < today
        ).all()
        
        for task in overdue_tasks:
            existing = self.db.query(ProgressAlert).filter(
                ProgressAlert.task_id == task.task_id,
                ProgressAlert.alert_type == "任务逾期",
                ProgressAlert.status == "待处理"
            ).first()
            
            if existing:
                continue
            
            overdue_days = (today - task.plan_end_date).days
            level = "红" if overdue_days >= 7 else ("橙" if overdue_days >= 3 else "黄")
            
            project = self.db.query(Project).filter(
                Project.project_id == task.project_id
            ).first()
            
            notify_users = [u for u in [task.owner_id, project.pm_id if project else None] if u]
            
            alert = self.create_alert(
                project_id=task.project_id,
                task_id=task.task_id,
                alert_type="任务逾期",
                alert_level=level,
                title=f"任务【{task.task_name}】已逾期{overdue_days}天",
                content=f"计划完成日期{task.plan_end_date}，负责人：{task.owner_name}",
                trigger_value=str(overdue_days),
                threshold_value="0",
                notify_users=notify_users
            )
            alerts.append(alert)
        
        return alerts


class ProgressDelayRule(AlertRule):
    """进度滞后预警（SPI < 0.9）"""
    
    def check(self) -> List[ProgressAlert]:
        alerts = []
        
        projects = self.db.query(Project).filter(
            Project.is_deleted == 0,
            Project.status.notin_(['已完成', '已取消']),
            Project.spi < 0.9
        ).all()
        
        for project in projects:
            existing = self.db.query(ProgressAlert).filter(
                ProgressAlert.project_id == project.project_id,
                ProgressAlert.alert_type == "进度滞后",
                ProgressAlert.status == "待处理"
            ).first()
            
            if existing:
                continue
            
            spi = float(project.spi or 1)
            level = "红" if spi < 0.8 else ("橙" if spi < 0.85 else "黄")
            
            notify_users = [u for u in [project.pm_id, project.te_id] if u]
            
            alert = self.create_alert(
                project_id=project.project_id,
                task_id=None,
                alert_type="进度滞后",
                alert_level=level,
                title=f"项目【{project.project_name}】进度滞后，SPI={spi:.2f}",
                content=f"实际进度{project.progress_rate}%，计划进度{project.plan_progress_rate}%",
                trigger_value=f"{spi:.2f}",
                threshold_value="0.9",
                notify_users=notify_users
            )
            alerts.append(alert)
        
        return alerts


class AlertService:
    """预警服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rules = [
            TaskOverdueRule(db),
            ProgressDelayRule(db),
        ]
    
    def run_all_rules(self) -> Dict[str, int]:
        result = {}
        for rule in self.rules:
            rule_name = rule.__class__.__name__
            try:
                alerts = rule.check()
                result[rule_name] = len(alerts)
            except Exception as e:
                result[rule_name] = f"Error: {str(e)}"
        self.db.commit()
        return result
    
    def get_alerts(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        query = self.db.query(ProgressAlert)
        
        if project_id:
            query = query.filter(ProgressAlert.project_id == project_id)
        if status:
            query = query.filter(ProgressAlert.status == status)
        
        total = query.count()
        alerts = query.order_by(
            ProgressAlert.created_time.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "list": [
                {
                    "alert_id": a.alert_id,
                    "project_id": a.project_id,
                    "alert_type": a.alert_type,
                    "alert_level": a.alert_level,
                    "alert_title": a.alert_title,
                    "status": a.status,
                    "created_time": str(a.created_time)
                }
                for a in alerts
            ],
            "total": total
        }
    
    def handle_alert(self, alert_id: int, handle_user_id: int, handle_remark: str) -> bool:
        alert = self.db.query(ProgressAlert).filter(
            ProgressAlert.alert_id == alert_id
        ).first()
        
        if not alert:
            return False
        
        alert.status = "已处理"
        alert.handle_user_id = handle_user_id
        alert.handle_time = datetime.now()
        alert.handle_remark = handle_remark
        
        self.db.commit()
        return True
