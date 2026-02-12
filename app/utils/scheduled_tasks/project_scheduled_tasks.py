# -*- coding: utf-8 -*-
"""
项目管理定时任务模块
包含项目健康检查、进度汇总、规格匹配等任务
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import case, func

from app.models.alert import ProjectHealthSnapshot
from app.models.base import get_db_session
from app.models.material import BomHeader, BomItem
from app.models.project import Project, ProjectCost
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
                Project.is_active,
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
                    BomHeader.is_latest
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
                Project.is_active
            ).all()

            snapshot_count = 0

            for project in projects:
                # 计算并更新健康度
                health_result = calculator.calculate_and_update(project)

                if health_result:
                    # 创建快照记录
                    new_health = health_result.get('new_health', 'H1')
                    snapshot = ProjectHealthSnapshot(
                        project_id=project.id,
                        snapshot_date=datetime.now().date(),
                        overall_health=new_health,
                        schedule_health=new_health,
                        cost_health=new_health,
                        quality_health=new_health,
                        resource_health=new_health,
                        health_score=100 if new_health == 'H1' else
                                     70 if new_health == 'H2' else
                                     30 if new_health == 'H3' else 0,
                        open_alerts=0,
                        open_exceptions=0,
                        blocking_issues=0,
                        schedule_variance=0,
                        milestone_on_track=0,
                        milestone_delayed=0,
                        cost_variance=0,
                        budget_used_pct=0
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
            from app.models.progress import Task
            from app.models.project.financial import ProjectMilestone

            # 获取所有活跃项目
            projects = db.query(Project).filter(
                Project.is_active,
                Project.status != 'completed'
            ).all()

            updated_count = 0

            for project in projects:
                # 计算任务进度（使用 Task 模型）
                task_progress_summary = db.query(
                    func.avg(Task.progress_percent).label('avg_completion'),
                    func.count(Task.id).label('total_tasks'),
                    func.sum(case((Task.status == 'DONE', 1), else_=0)).label('completed_tasks')
                ).filter(Task.project_id == project.id).first()

                # 计算里程碑进度（使用 ProjectMilestone 模型）
                milestone_progress_summary = db.query(
                    func.count(ProjectMilestone.id).label('total_milestones'),
                    func.sum(case((ProjectMilestone.status == 'COMPLETED', 1), else_=0)).label('completed_milestones')
                ).filter(ProjectMilestone.project_id == project.id).first()

                total_tasks = task_progress_summary.total_tasks or 0
                total_milestones = milestone_progress_summary.total_milestones or 0

                # 更新项目的进度汇总
                if total_tasks > 0 or total_milestones > 0:
                    completed_tasks = task_progress_summary.completed_tasks or 0
                    completed_milestones = milestone_progress_summary.completed_milestones or 0

                    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    milestone_completion_rate = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0

                    # 综合进度计算（任务权重60%，里程碑权重40%）
                    overall_progress = (task_completion_rate * 0.6) + (milestone_completion_rate * 0.4)

                    # 更新项目进度
                    project.progress_pct = round(overall_progress, 2)

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
                Project.is_active,
                Project.status != 'completed',
                Project.planned_end_date <= upcoming_deadline,
                Project.planned_end_date >= datetime.now().date()
            ).all()

            alert_count = 0

            for project in projects:
                days_remaining = (project.planned_end_date - datetime.now().date()).days

                # 检查是否已存在相同预警（使用target_type和target_id）
                existing_alert = db.query(AlertRecord).filter(
                    AlertRecord.target_type == 'project',
                    AlertRecord.target_id == project.id,
                    AlertRecord.alert_title.contains('截止日期'),
                    AlertRecord.status == 'PENDING'
                ).first()

                if existing_alert:
                    continue

                # 创建预警记录
                urgency = 'CRITICAL' if days_remaining <= 3 else 'HIGH'

                alert = AlertRecord(
                    alert_no=f"ALT-DL-{project.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    rule_id=1,  # 使用默认规则ID
                    target_type='project',
                    target_id=project.id,
                    target_no=project.project_code,
                    target_name=project.project_name,
                    alert_title='项目截止日期预警',
                    alert_content=f'项目 "{project.project_name}" 将在 {days_remaining} 天后截止（{project.planned_end_date}），当前进度 {project.progress_pct or 0}%。',
                    alert_level=urgency,
                    status='PENDING',
                    triggered_at=datetime.now(),
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
                Project.is_active,
                Project.status != 'completed'
            ).all()

            alert_count = 0

            for project in projects:
                # 计算实际成本
                actual_cost = db.query(func.sum(ProjectCost.amount)).filter(
                    ProjectCost.project_id == project.id
                ).scalar() or 0

                # 检查是否超支
                if project.budget_amount and actual_cost > project.budget_amount:
                    overrun_amount = actual_cost - project.budget_amount
                    overrun_percentage = (overrun_amount / project.budget_amount) * 100

                    # 检查是否已存在相同预警（使用target_type和target_id）
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'project',
                        AlertRecord.target_id == project.id,
                        AlertRecord.alert_title.contains('成本超支'),
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if existing_alert:
                        continue

                    # 创建成本超支预警
                    urgency = 'CRITICAL' if overrun_percentage > 20 else 'HIGH'

                    alert = AlertRecord(
                        alert_no=f"ALT-CO-{project.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        rule_id=1,  # 使用默认规则ID
                        target_type='project',
                        target_id=project.id,
                        target_no=project.project_code,
                        target_name=project.project_name,
                        alert_title='项目成本超支预警',
                        alert_content=f'项目 "{project.project_name}" 成本已超支 {overrun_percentage:.1f}%（超支金额：{overrun_amount:,.2f}），预算 {project.budget_amount:,.2f}，实际成本 {actual_cost:,.2f}。',
                        alert_level=urgency,
                        status='PENDING',
                        triggered_at=datetime.now(),
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
