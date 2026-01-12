# -*- coding: utf-8 -*-
"""
生产和资源定时任务

包含生产日报自动生成、缺料日报、岗位职责任务生成、负荷超限预警等
"""

import logging
from typing import Optional
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from app.models.base import get_db_session
from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum

logger = logging.getLogger(__name__)


def _calculate_production_daily_stats(db: Session, target_date: date, workshop_id: Optional[int]) -> dict:
    """内部辅助：计算指定日期、车间的生产统计"""
    from sqlalchemy import func
    from app.models.production import WorkOrder, WorkReport, ProductionException, Worker

    # 计划数据
    plan_query = db.query(WorkOrder).filter(
        WorkOrder.plan_start_date <= target_date,
        WorkOrder.plan_end_date >= target_date
    )
    if workshop_id:
        plan_query = plan_query.filter(WorkOrder.workshop_id == workshop_id)
    plan_orders = plan_query.all()
    plan_qty = sum(order.plan_qty or 0 for order in plan_orders)
    plan_hours = sum(float(order.standard_hours or 0) for order in plan_orders)

    # 报工数据
    report_query = db.query(WorkReport).join(WorkOrder, WorkOrder.id == WorkReport.work_order_id).filter(
        func.date(WorkReport.report_time) == target_date
    )
    if workshop_id:
        report_query = report_query.filter(WorkOrder.workshop_id == workshop_id)
    reports = report_query.all()

    completed_qty = sum(report.completed_qty or 0 for report in reports if report.completed_qty)
    qualified_qty = sum(report.qualified_qty or 0 for report in reports if report.qualified_qty)
    defect_qty = sum(report.defect_qty or 0 for report in reports if report.defect_qty)
    total_qty = completed_qty if completed_qty else qualified_qty + defect_qty
    actual_hours = sum(float(report.work_hours or 0) for report in reports if report.work_hours)
    actual_attend = len({report.worker_id for report in reports if report.worker_id})

    # 人员数据
    worker_query = db.query(Worker)
    if workshop_id:
        worker_query = worker_query.filter(Worker.workshop_id == workshop_id)
    workers = worker_query.all()
    should_attend = len([w for w in workers if w.status != 'RESIGNED'])
    leave_count = len([w for w in workers if w.status == 'LEAVE'])

    # 异常数据
    exception_base = db.query(ProductionException)
    if workshop_id:
        exception_base = exception_base.filter(ProductionException.workshop_id == workshop_id)
    new_exception_count = exception_base.filter(
        func.date(ProductionException.report_time) == target_date
    ).count()
    resolved_exception_count = exception_base.filter(
        ProductionException.resolved_at.isnot(None),
        func.date(ProductionException.resolved_at) == target_date
    ).count()

    produced_qty = completed_qty or total_qty
    completion_rate = round((produced_qty / plan_qty) * 100, 2) if plan_qty else 0.0
    efficiency = round((actual_hours / plan_hours) * 100, 2) if plan_hours else 0.0
    overtime_hours = round(max(actual_hours - plan_hours, 0), 2)
    pass_rate = round((qualified_qty / total_qty) * 100, 2) if total_qty else 0.0

    return {
        'plan_qty': int(plan_qty),
        'completed_qty': int(produced_qty),
        'completion_rate': completion_rate,
        'plan_hours': round(plan_hours, 2),
        'actual_hours': round(actual_hours, 2),
        'overtime_hours': overtime_hours,
        'efficiency': efficiency,
        'should_attend': int(should_attend),
        'actual_attend': int(actual_attend),
        'leave_count': int(leave_count),
        'total_qty': int(total_qty),
        'qualified_qty': int(qualified_qty),
        'pass_rate': pass_rate,
        'new_exception_count': int(new_exception_count),
        'resolved_exception_count': int(resolved_exception_count)
    }


def generate_production_daily_reports(target_date: Optional[date] = None):
    """
    P0-11: 生产日报自动生成
    根据上一日生产、报工、异常数据自动生成全厂及各车间日报
    """
    try:
        with get_db_session() as db:
            from app.models.production import ProductionDailyReport, Workshop

            if target_date is None:
                target_date = date.today() - timedelta(days=1)

            workshops = db.query(Workshop).filter(Workshop.is_active == True).all()
            workshop_map = {w.id: w.workshop_name for w in workshops}
            target_workshops = [None] + [w.id for w in workshops]

            generated = 0
            for workshop_id in target_workshops:
                stats = _calculate_production_daily_stats(db, target_date, workshop_id)

                report = db.query(ProductionDailyReport).filter(
                    ProductionDailyReport.report_date == target_date,
                    ProductionDailyReport.workshop_id == workshop_id
                ).first()
                if not report:
                    report = ProductionDailyReport(
                        report_date=target_date,
                        workshop_id=workshop_id
                    )
                    db.add(report)

                workshop_label = '全厂' if workshop_id is None else workshop_map.get(workshop_id, f'车间{workshop_id}')
                stats['summary'] = (
                    f"{workshop_label} {target_date.strftime('%m-%d')} 计划 {stats['plan_qty']} 件，"
                    f"完成 {stats['completed_qty']} 件（{stats['completion_rate']:.1f}%），"
                    f"实工 {stats['actual_hours']:.1f} 小时，效率 {stats['efficiency']:.1f}%，"
                    f"异常 {stats['new_exception_count']} 起。"
                )

                for field, value in stats.items():
                    setattr(report, field, value)

                generated += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 生产日报自动生成: {generated} 条记录, 日期 {target_date}")

            return {
                'generated': generated,
                'date': target_date.isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 生产日报自动生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def generate_shortage_daily_report(target_date: Optional[date] = None):
    """
    P0-12: 缺料日报自动生成
    汇总缺料预警、到货、齐套等指标
    """
    try:
        with get_db_session() as db:
            from app.models.shortage import ShortageDailyReport
            from app.services.shortage_report_service import build_daily_report_data

            if target_date is None:
                target_date = date.today() - timedelta(days=1)

            # 构建日报数据
            report_data = build_daily_report_data(db, target_date)

            # 获取或创建日报记录
            report = db.query(ShortageDailyReport).filter(
                ShortageDailyReport.report_date == target_date
            ).first()
            if not report:
                report = ShortageDailyReport(report_date=target_date)
                db.add(report)

            # 更新日报数据
            report.new_alerts = report_data['new_alerts']
            report.resolved_alerts = report_data['resolved_alerts']
            report.pending_alerts = report_data['pending_alerts']
            report.overdue_alerts = report_data['overdue_alerts']
            report.level1_count = report_data['level_counts']['level1']
            report.level2_count = report_data['level_counts']['level2']
            report.level3_count = report_data['level_counts']['level3']
            report.level4_count = report_data['level_counts']['level4']
            report.new_reports = report_data['new_reports']
            report.resolved_reports = report_data['resolved_reports']
            report.total_work_orders = report_data['total_work_orders']
            report.kit_complete_count = report_data['kit_complete_count']
            report.kit_rate = report_data['kit_rate']
            report.expected_arrivals = report_data['expected_arrivals']
            report.actual_arrivals = report_data['actual_arrivals']
            report.delayed_arrivals = report_data['delayed_arrivals']
            report.on_time_rate = report_data['on_time_rate']
            report.avg_response_minutes = report_data['avg_response_minutes']
            report.avg_resolve_hours = report_data['avg_resolve_hours']
            report.stoppage_count = report_data['stoppage_count']
            report.stoppage_hours = report_data['stoppage_hours']

            db.commit()

            logger.info(f"[{datetime.now()}] 缺料日报自动生成: 日期 {target_date}")

            return {
                'date': target_date.isoformat(),
                'new_alerts': report_data['new_alerts'],
                'new_reports': report_data['new_reports']
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 缺料日报自动生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def generate_job_duty_tasks():
    """
    岗位职责任务生成服务
    每天凌晨4点执行，根据岗位职责模板自动生成任务
    """
    try:
        with get_db_session() as db:
            from app.models.task_center import JobDutyTemplate
            from app.services.job_duty_task_service import (
                should_generate_task,
                find_template_users,
                create_task_from_template,
                check_task_exists
            )
            from app.api.v1.endpoints.task_center import generate_task_code

            today = date.today()
            generated_count = 0

            # 查询所有启用的岗位职责模板
            templates = db.query(JobDutyTemplate).filter(
                JobDutyTemplate.is_active == True,
                JobDutyTemplate.auto_generate == True
            ).all()

            for template in templates:
                # 判断是否需要生成任务
                should_generate, target_date = should_generate_task(template, today)
                if not should_generate:
                    continue

                # 检查是否已经生成过该日期的任务（避免重复生成）
                if check_task_exists(db, template, target_date):
                    continue

                # 查找该岗位的所有用户
                users = find_template_users(db, template)
                if not users:
                    continue

                # 为每个用户生成任务
                for user in users:
                    task = create_task_from_template(
                        db, template, user, target_date, generate_task_code
                    )
                    db.add(task)
                    generated_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 岗位职责任务生成完成: 生成 {generated_count} 个任务")

            return {
                'generated_count': generated_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 岗位职责任务生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_workload_overload_alerts():
    """
    负荷超限预警服务
    每天执行一次，检查负荷超过110%的资源并生成预警
    """
    try:
        with get_db_session() as db:
            from app.models.user import User
            from app.models.progress import Task
            from app.models.pmo import PmoResourceAllocation

            today = date.today()
            # 查询未来30天的负荷
            start_date = today
            end_date = today + timedelta(days=30)

            # 获取所有活跃用户
            users = db.query(User).filter(User.is_active == True).all()

            # 获取或创建预警规则
            overload_rule = db.query(AlertRule).filter(
                AlertRule.rule_code == 'WORKLOAD_OVERLOAD',
                AlertRule.is_enabled == True
            ).first()

            if not overload_rule:
                overload_rule = AlertRule(
                    rule_code='WORKLOAD_OVERLOAD',
                    rule_name='资源负荷超限预警',
                    rule_type=AlertRuleTypeEnum.RESOURCE.value,
                    target_type='USER',
                    condition_type='THRESHOLD',
                    condition_operator='GT',
                    threshold_value='110',
                    alert_level=AlertLevelEnum.WARNING.value,
                    is_enabled=True,
                    is_system=True,
                    description='当用户未来30天负荷超过110%时触发预警'
                )
                db.add(overload_rule)
                db.flush()

            alert_count = 0
            overloaded_users = []

            for user in users:
                # 计算分配工时
                tasks = db.query(Task).filter(
                    Task.owner_id == user.id,
                    Task.plan_start <= end_date,
                    Task.plan_end >= start_date,
                    Task.status != 'CANCELLED'
                ).all()

                assigned_hours = 0.0
                for task in tasks:
                    if task.plan_start and task.plan_end:
                        days = (task.plan_end - task.plan_start).days + 1
                        hours = days * 8.0
                        assigned_hours += hours

                # 获取资源分配
                allocations = db.query(PmoResourceAllocation).filter(
                    PmoResourceAllocation.resource_id == user.id,
                    PmoResourceAllocation.start_date <= end_date,
                    PmoResourceAllocation.end_date >= start_date,
                    PmoResourceAllocation.status != 'CANCELLED'
                ).all()

                for alloc in allocations:
                    if alloc.planned_hours:
                        assigned_hours += float(alloc.planned_hours)

                # 计算标准工时（30天，每月176小时）
                workdays = 22  # 简单估算
                standard_hours = workdays * 8.0

                # 计算分配率
                allocation_rate = (assigned_hours / standard_hours * 100) if standard_hours > 0 else 0.0

                # 如果超过110%，生成预警
                if allocation_rate > 110:
                    existing_alert = db.query(AlertRecord).filter(
                        AlertRecord.target_type == 'USER',
                        AlertRecord.target_id == user.id,
                        AlertRecord.rule_id == overload_rule.id,
                        AlertRecord.status == 'PENDING'
                    ).first()

                    if not existing_alert:
                        alert_no = f'WO{today.strftime("%Y%m%d")}{str(alert_count + 1).zfill(4)}'

                        alert = AlertRecord(
                            alert_no=alert_no,
                            rule_id=overload_rule.id,
                            target_type='USER',
                            target_id=user.id,
                            target_no=str(user.id),
                            target_name=user.real_name or user.username,
                            project_id=None,
                            alert_level=AlertLevelEnum.WARNING.value if allocation_rate <= 150 else AlertLevelEnum.CRITICAL.value,
                            alert_title=f'资源负荷超限：{user.real_name or user.username}',
                            alert_content=f'用户 {user.real_name or user.username} 未来30天负荷达到 {allocation_rate:.1f}%，超过110%阈值（分配工时：{assigned_hours:.1f}小时，标准工时：{standard_hours:.1f}小时）',
                            status=AlertStatusEnum.PENDING.value,
                            triggered_at=datetime.now()
                        )
                        db.add(alert)
                        alert_count += 1
                        overloaded_users.append({
                            'user_id': user.id,
                            'user_name': user.real_name or user.username,
                            'allocation_rate': allocation_rate
                        })

            db.commit()

            logger.info(f"[{datetime.now()}] 负荷超限预警检查完成: 检查 {len(users)} 个用户, 发现 {len(overloaded_users)} 个超负荷用户, 生成 {alert_count} 个预警")

            return {
                'checked_count': len(users),
                'overloaded_count': len(overloaded_users),
                'alert_count': alert_count,
                'overloaded_users': overloaded_users,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 负荷超限预警检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
