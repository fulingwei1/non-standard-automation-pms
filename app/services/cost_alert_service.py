# -*- coding: utf-8 -*-
"""
成本预警服务
负责在成本归集时实时检查预算执行情况，并生成预警
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost
from app.models.alert import AlertRule, AlertRecord, AlertNotification
from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum
from app.models.budget import ProjectBudget


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
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # 获取项目预算
        budget = (
            db.query(ProjectBudget)
            .filter(
                ProjectBudget.project_id == project_id,
                ProjectBudget.is_active == True,
                ProjectBudget.status == "APPROVED"
            )
            .order_by(ProjectBudget.version.desc())
            .first()
        )
        
        budget_amount = float(budget.total_amount) if budget else float(project.budget_amount or 0)
        
        if budget_amount <= 0:
            # 没有预算，不检查
            return None
        
        # 获取实际成本
        costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
        actual_cost = sum([float(c.amount or 0) for c in costs])
        
        if project.actual_cost:
            actual_cost = float(project.actual_cost)
        
        # 计算执行率和超支比例
        execution_rate = (actual_cost / budget_amount * 100) if budget_amount > 0 else 0
        overrun_ratio = ((actual_cost - budget_amount) / budget_amount * 100) if budget_amount > 0 else 0
        
        # 获取或创建成本预警规则
        alert_rule = db.query(AlertRule).filter(
            AlertRule.rule_code == 'COST_OVERRUN',
            AlertRule.is_enabled == True
        ).first()
        
        if not alert_rule:
            # 创建默认规则
            alert_rule = AlertRule(
                rule_code='COST_OVERRUN',
                rule_name='成本超支预警',
                rule_type=AlertRuleTypeEnum.COST_OVERRUN.value,
                target_type='PROJECT',
                condition_type='THRESHOLD',
                condition_operator='GT',
                threshold_value='5',
                alert_level=AlertLevelEnum.WARNING.value,
                is_enabled=True,
                is_system=True,
                description='当项目成本超支超过5%时触发预警'
            )
            db.add(alert_rule)
            db.flush()
        
        # 判断预警级别
        alert_level = None
        alert_title = None
        alert_content = None
        
        if execution_rate >= 100:
            # 已超支
            if overrun_ratio >= 20:
                alert_level = AlertLevelEnum.URGENT.value
                alert_title = f'项目成本严重超支：{project.project_name}'
                alert_content = f'项目 {project.project_code} 成本严重超支 {overrun_ratio:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，超支：{actual_cost - budget_amount:,.2f}）'
            elif overrun_ratio >= 10:
                alert_level = AlertLevelEnum.CRITICAL.value
                alert_title = f'项目成本超支：{project.project_name}'
                alert_content = f'项目 {project.project_code} 成本超支 {overrun_ratio:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，超支：{actual_cost - budget_amount:,.2f}）'
            elif overrun_ratio >= 5:
                alert_level = AlertLevelEnum.WARNING.value
                alert_title = f'项目成本超支：{project.project_name}'
                alert_content = f'项目 {project.project_code} 成本超支 {overrun_ratio:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，超支：{actual_cost - budget_amount:,.2f}）'
        elif execution_rate >= 90:
            # 接近预算
            alert_level = AlertLevelEnum.WARNING.value
            alert_title = f'项目成本接近预算：{project.project_name}'
            alert_content = f'项目 {project.project_code} 成本执行率 {execution_rate:.2f}%，接近预算（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}，剩余：{budget_amount - actual_cost:,.2f}）'
        elif execution_rate >= 80:
            # 注意
            alert_level = AlertLevelEnum.INFO.value
            alert_title = f'项目成本执行率较高：{project.project_name}'
            alert_content = f'项目 {project.project_code} 成本执行率 {execution_rate:.2f}%（预算：{budget_amount:,.2f}，实际：{actual_cost:,.2f}）'
        
        if not alert_level:
            return None
        
        # 检查是否已存在相同级别的预警
        existing_alert = db.query(AlertRecord).filter(
            AlertRecord.target_type == 'PROJECT',
            AlertRecord.target_id == project_id,
            AlertRecord.rule_id == alert_rule.id,
            AlertRecord.alert_level == alert_level,
            AlertRecord.status == AlertStatusEnum.PENDING.value
        ).first()
        
        if existing_alert:
            # 如果已存在相同级别的预警，更新内容
            existing_alert.alert_content = alert_content
            existing_alert.triggered_at = datetime.now()
            db.add(existing_alert)
            return existing_alert
        
        # 生成预警编号
        today = date.today()
        max_alert = (
            db.query(AlertRecord)
            .filter(AlertRecord.alert_no.like(f'CO{today.strftime("%Y%m%d")}%'))
            .order_by(AlertRecord.alert_no.desc())
            .first()
        )
        
        if max_alert:
            seq = int(max_alert.alert_no[-4:]) + 1
        else:
            seq = 1
        
        alert_no = f'CO{today.strftime("%Y%m%d")}{str(seq).zfill(4)}'
        
        # 创建预警记录
        alert = AlertRecord(
            alert_no=alert_no,
            rule_id=alert_rule.id,
            target_type='PROJECT',
            target_id=project_id,
            target_no=project.project_code,
            target_name=project.project_name,
            project_id=project_id,
            alert_level=alert_level,
            alert_title=alert_title,
            alert_content=alert_content,
            status=AlertStatusEnum.PENDING.value,
            triggered_at=datetime.now(),
            source_module=trigger_source or 'COST',
            source_id=source_id
        )
        db.add(alert)
        db.flush()
        
        # 发送通知（可选）
        # TODO: 实现通知发送逻辑
        
        return alert
    
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
            projects = db.query(Project).filter(Project.is_active == True).all()
        
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






