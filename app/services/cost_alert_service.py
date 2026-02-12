# -*- coding: utf-8 -*-
"""
成本预警服务
负责在成本归集时实时检查预算执行情况，并生成预警
"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.project import Project


class CostAlertService:
    """成本预警服务"""

    @staticmethod
    def check_budget_execution(
        db: Session,
        project_id: int,
        trigger_source: Optional[str] = None,
        source_id: Optional[int] = None
    ) -> Optional[AlertRecord]:
        """
        检查项目预算执行情况并生成预警

        Args:
            db: 数据库会话
            project_id: 项目ID
            trigger_source: 触发来源（PURCHASE/OUTSOURCING/ECN/BOM/TIMESHEET）
            source_id: 触发来源ID

        Returns:
            创建的预警记录（如果有）
        """
        from app.services.budget_execution_check_service import (
            create_alert_record,
            determine_alert_level,
            find_existing_alert,
            get_actual_cost,
            get_or_create_alert_rule,
            get_project_budget,
        )

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # 获取预算和实际成本
        budget_amount = get_project_budget(db, project_id, project)

        if budget_amount <= 0:
            return None

        actual_cost = get_actual_cost(db, project_id, project)

        # 计算执行率和超支比例
        execution_rate = (actual_cost / budget_amount * 100) if budget_amount > 0 else 0
        overrun_ratio = ((actual_cost - budget_amount) / budget_amount * 100) if budget_amount > 0 else 0

        # 获取或创建预警规则
        alert_rule = get_or_create_alert_rule(db)

        # 判断预警级别
        alert_level, alert_title, alert_content = determine_alert_level(
            execution_rate, overrun_ratio, project.project_name, project.project_code,
            budget_amount, actual_cost
        )

        if not alert_level:
            return None

        # 检查是否已存在相同级别的预警
        existing_alert = find_existing_alert(db, project_id, alert_rule, alert_level)

        if existing_alert:
            existing_alert.alert_content = alert_content
            existing_alert.triggered_at = datetime.now()
            db.add(existing_alert)
            return existing_alert

        # 创建预警记录
        return create_alert_record(
            db, project, project_id, alert_rule, alert_level,
            alert_title, alert_content, budget_amount, actual_cost,
            trigger_source, source_id
        )

    @staticmethod
    def check_all_projects_budget(
        db: Session,
        project_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        批量检查项目预算执行情况

        Args:
            db: 数据库会话
            project_ids: 项目ID列表（如果为None，检查所有活跃项目）

        Returns:
            检查结果统计
        """
        if project_ids:
            projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
        else:
            projects = db.query(Project).filter(Project.is_active).all()

        alert_count = 0
        checked_projects = []

        for project in projects:
            alert = CostAlertService.check_budget_execution(db, project.id)
            if alert:
                alert_count += 1
                checked_projects.append({
                    'project_id': project.id,
                    'project_code': project.project_code,
                    'alert_id': alert.id,
                    'alert_level': alert.alert_level
                })

        return {
            'checked_count': len(projects),
            'alert_count': alert_count,
            'projects': checked_projects
        }






