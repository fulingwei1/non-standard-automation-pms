# -*- coding: utf-8 -*-
"""
项目管理定时任务模块
包含项目健康检查、进度汇总、规格匹配等任务
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import ProjectHealthSnapshot
from app.models.base import get_db_session
from app.models.material import BomHeader, BomItem
from app.models.project import Project, ProjectCost, ProjectMilestone
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.technical_spec import SpecMatchRecord, TechnicalSpecRequirement
from app.utils.spec_match_service import SpecMatchService

# 模块级 logger
logger = logging.getLogger(__name__)


def daily_spec_match_check():
    """
    每日规格匹配检查
    每天上午9点执行，检查所有活跃项目的采购订单和BOM
    """
    service = SpecMatchService()

    with get_db_session() as db:
        try:
            # 查询所有活跃项目
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status != 'completed'
            ).all()

            total_checked = 0
            total_mismatched = 0

            for project in projects:
                # 检查采购订单规格匹配
                purchase_orders = db.query(PurchaseOrder).filter(
                    PurchaseOrder.project_id == project.id,
                    PurchaseOrder.status.in_(['pending', 'approved'])
                ).all()

                for po in purchase_orders:
                    # 检查订单项
                    items = db.query(PurchaseOrderItem).filter(
                        PurchaseOrderItem.purchase_order_id == po.id
                    ).all()

                    for item in items:
                        if not item.technical_spec_id:
                            continue

                        # 检查规格匹配
                        spec_requirement = db.query(TechnicalSpecRequirement).filter(
                            TechnicalSpecRequirement.id == item.technical_spec_id
                        ).first()

                        if not spec_requirement:
                            continue

                        # 创建匹配记录
                        match_result = service.check_spec_match(
                            item.description,
                            spec_requirement
                        )

                        # 记录匹配结果
                        existing_record = db.query(SpecMatchRecord).filter(
                            SpecMatchRecord.purchase_order_item_id == item.id,
                            SpecMatchRecord.check_date == datetime.now().date()
                        ).first()

                        if existing_record:
                            existing_record.match_score = match_result['score']
                            existing_record.match_status = match_result['status']
                            existing_record.match_details = match_result['details']
                        else:
                            record = SpecMatchRecord(
                                purchase_order_item_id=item.id,
                                spec_requirement_id=spec_requirement.id,
                                check_date=datetime.now().date(),
                                match_score=match_result['score'],
                                match_status=match_result['status'],
                                match_details=match_result['details']
                            )
                            db.add(record)

                        total_checked += 1
                        if match_result['status'] != 'matched':
                            total_mismatched += 1

            # 检查BOM规格匹配
            for project in projects:
                bom_headers = db.query(BomHeader).filter(
                    BomHeader.project_id == project.id,
                    BomHeader.is_active == True
                ).all()

                for bom in bom_headers:
                    bom_items = db.query(BomItem).filter(
                        BomItem.bom_id == bom.id
                    ).all()

                    for item in bom_items:
                        if not item.technical_spec_id:
                            continue

                        # 类似采购订单的规格匹配检查
                        spec_requirement = db.query(TechnicalSpecRequirement).filter(
                            TechnicalSpecRequirement.id == item.technical_spec_id
                        ).first()

                        if not spec_requirement:
                            continue

                        match_result = service.check_spec_match(
                            item.item_name,
                            spec_requirement
                        )

                        # 记录匹配结果
                        existing_record = db.query(SpecMatchRecord).filter(
                            SpecMatchRecord.bom_item_id == item.id,
                            SpecMatchRecord.check_date == datetime.now().date()
                        ).first()

                        if existing_record:
                            existing_record.match_score = match_result['score']
                            existing_record.match_status = match_result['status']
                            existing_record.match_details = match_result['details']
                        else:
                            record = SpecMatchRecord(
                                bom_item_id=item.id,
                                spec_requirement_id=spec_requirement.id,
                                check_date=datetime.now().date(),
                                match_score=match_result['score'],
                                match_status=match_result['status'],
                                match_details=match_result['details']
                            )
                            db.add(record)

                        total_checked += 1
                        if match_result['status'] != 'matched':
                            total_mismatched += 1

            db.commit()

            logger.info(f"规格匹配检查完成: 检查 {total_checked} 项, 发现 {total_mismatched} 项不匹配")

            return {
                'checked': total_checked,
                'mismatched': total_mismatched,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"规格匹配检查失败: {str(e)}")
            db.rollback()
            raise


def calculate_project_health():
    """
    计算项目健康度
    每小时执行一次，自动计算所有活跃项目的健康度
    """
    try:
        from app.services.health_calculator import HealthCalculator

        with get_db_session() as db:
            calculator = HealthCalculator(db)
            result = calculator.batch_calculate()

            logger.info(f"健康度计算完成: 总计 {result['total']} 个项目,  更新 {result['updated']} 个, 未变化 {result['unchanged']} 个")

            return result
    except Exception as e:
        logger.error(f"健康度计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def daily_health_snapshot():
    """
    每日健康度快照
    每天凌晨2点执行，生成所有项目的健康度快照
    """
    try:
        from app.services.health_calculator import HealthCalculator

        with get_db_session() as db:
            calculator = HealthCalculator(db)

            # 获取所有活跃项目
            projects = db.query(Project).filter(
                Project.is_active == True
            ).all()

            snapshot_count = 0

            for project in projects:
                # 计算当前健康度
                health_data = calculator.calculate_project_health(project.id)

                if health_data:
                    # 创建快照记录
                    snapshot = ProjectHealthSnapshot(
                        project_id=project.id,
                        snapshot_date=datetime.now().date(),
                        health_score=health_data.get('health_score', 0),
                        progress_score=health_data.get('progress_score', 0),
                        quality_score=health_data.get('quality_score', 0),
                        cost_score=health_data.get('cost_score', 0),
                        risk_score=health_data.get('risk_score', 0),
                        overall_status=health_data.get('overall_status', 'normal'),
                        risk_factors=health_data.get('risk_factors', []),
                        recommendations=health_data.get('recommendations', [])
                    )

                    db.add(snapshot)
                    snapshot_count += 1

            db.commit()

            logger.info(f"健康度快照生成完成: 生成 {snapshot_count} 个项目快照")

            return {
                'snapshot_count': snapshot_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"健康度快照生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def calculate_progress_summary():
    """
    进度汇总计算服务
    每小时执行一次，自动计算项目进度汇总
    """
    try:
        with get_db_session() as db:
            from app.models.progress import MilestoneProgress, TaskProgress

            # 获取所有活跃项目
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status != 'completed'
            ).all()

            updated_count = 0

            for project in projects:
                # 计算任务进度
                task_progress_summary = db.query(
                    func.avg(TaskProgress.completion_rate).label('avg_completion'),
                    func.count(TaskProgress.id).label('total_tasks'),
                    func.sum(func.case([(TaskProgress.status == 'completed', 1)], else_=0)).label('completed_tasks')
                ).filter(TaskProgress.project_id == project.id).first()

                # 计算里程碑进度
                milestone_progress_summary = db.query(
                    func.avg(MilestoneProgress.completion_rate).label('avg_completion'),
                    func.count(MilestoneProgress.id).label('total_milestones'),
                    func.sum(func.case([(MilestoneProgress.status == 'completed', 1)], else_=0)).label('completed_milestones')
                ).filter(MilestoneProgress.project_id == project.id).first()

                # 更新项目的进度汇总
                if task_progress_summary.total_tasks > 0 or milestone_progress_summary.total_milestones > 0:
                    task_completion_rate = (task_progress_summary.completed_tasks / task_progress_summary.total_tasks * 100) if task_progress_summary.total_tasks > 0 else 0
                    milestone_completion_rate = (milestone_progress_summary.completed_milestones / milestone_progress_summary.total_milestones * 100) if milestone_progress_summary.total_milestones > 0 else 0

                    # 综合进度计算（任务权重60%，里程碑权重40%）
                    overall_progress = (task_completion_rate * 0.6) + (milestone_completion_rate * 0.4)

                    # 更新项目进度
                    project.progress_percentage = round(overall_progress, 2)
                    project.last_progress_update = datetime.now()

                    updated_count += 1

            db.commit()

            logger.info(f"项目进度汇总计算完成: 更新 {updated_count} 个项目")

            return {
                'updated_projects': updated_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"项目进度汇总计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_project_deadline_alerts():
    """
    项目截止日期预警检查
    每天早上8点执行，检查即将到期的项目
    """
    try:
        with get_db_session() as db:
            from app.models.alert import AlertRecord

            # 查询7天内到期的活跃项目
            upcoming_deadline = datetime.now() + timedelta(days=7)

            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status != 'completed',
                Project.end_date <= upcoming_deadline,
                Project.end_date >= datetime.now().date()
            ).all()

            alert_count = 0

            for project in projects:
                days_remaining = (project.end_date - datetime.now().date()).days

                # 检查是否已存在相同预警
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.source_type == 'project',
                    AlertRecord.source_id == project.id,
                    AlertRecord.alert_type == 'deadline_warning',
                    AlertRecord.status == 'active'
                ).first()

                if existing_alert:
                    continue

                # 创建预警记录
                urgency = 'high' if days_remaining <= 3 else 'medium'

                alert = AlertRecord(
                    source_type='project',
                    source_id=project.id,
                    alert_type='deadline_warning',
                    alert_title=f'项目截止日期预警',
                    alert_content=f'项目 "{project.name}" 将在 {days_remaining} 天后截止（{project.end_date}），当前进度 {project.progress_percentage}%。',
                    alert_level=urgency,
                    alert_status='active',
                    created_time=datetime.now(),
                    project_id=project.id
                )

                db.add(alert)
                alert_count += 1

            db.commit()

            logger.info(f"项目截止日期预警检查完成: 发现 {len(projects)} 个即将到期项目, 生成 {alert_count} 个预警")

            return {
                'upcoming_projects': len(projects),
                'alerts_created': alert_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"项目截止日期预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_project_cost_overrun():
    """
    项目成本超支检查
    每天执行一次，检查项目成本是否超支
    """
    try:
        with get_db_session() as db:
            from app.models.alert import AlertRecord

            # 获取所有活跃项目
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status != 'completed'
            ).all()

            alert_count = 0

            for project in projects:
                # 计算实际成本
                actual_cost = db.query(func.sum(ProjectCost.amount)).filter(
                    ProjectCost.project_id == project.id
                ).scalar() or 0

                # 检查是否超支
                if project.budget and actual_cost > project.budget:
                    overrun_amount = actual_cost - project.budget
                    overrun_percentage = (overrun_amount / project.budget) * 100

                    # 检查是否已存在相同预警
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.source_type == 'project',
                        AlertRecord.source_id == project.id,
                        AlertRecord.alert_type == 'cost_overrun',
                        AlertRecord.status == 'active'
                    ).first()

                    if existing_alert:
                        continue

                    # 创建成本超支预警
                    urgency = 'critical' if overrun_percentage > 20 else 'high'

                    alert = AlertRecord(
                        source_type='project',
                        source_id=project.id,
                        alert_type='cost_overrun',
                        alert_title=f'项目成本超支预警',
                        alert_content=f'项目 "{project.name}" 成本已超支 {overrun_percentage:.1f}%（超支金额：{overrun_amount:,.2f}），预算 {project.budget:,.2f}，实际成本 {actual_cost:,.2f}。',
                        alert_level=urgency,
                        alert_status='active',
                        created_time=datetime.now(),
                        project_id=project.id
                    )

                    db.add(alert)
                    alert_count += 1

            db.commit()

            logger.info(f"项目成本超支检查完成: 发现 {alert_count} 个成本超支项目")

            return {
                'overrun_projects': alert_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"项目成本超支检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# 导出所有任务函数
__all__ = [
    'daily_spec_match_check',
    'calculate_project_health',
    'daily_health_snapshot',
    'calculate_progress_summary',
    'check_project_deadline_alerts',
    'check_project_cost_overrun',
]
