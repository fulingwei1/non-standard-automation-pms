# -*- coding: utf-8 -*-
"""
定时任务调度器
使用 APScheduler 管理所有后台定时任务
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.core.config import settings

logger = logging.getLogger(__name__)

# 配置任务存储和执行器
jobstores = {
    'default': MemoryJobStore()
}

executors = {
    'default': ThreadPoolExecutor(5)
}

job_defaults = {
    'coalesce': True,  # 如果任务堆积，只执行一次
    'max_instances': 1,  # 同一任务最多1个实例
    'misfire_grace_time': 300  # 错过执行时间后5分钟内仍可执行
}

# 创建调度器
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='Asia/Shanghai'
)


def job_listener(event):
    """任务执行监听器"""
    if event.exception:
        logger.error(f"任务 {event.job_id} 执行失败: {event.exception}")
    else:
        logger.info(f"任务 {event.job_id} 执行成功")


def init_scheduler():
    """初始化并启动调度器"""
    from app.utils.scheduled_tasks import (
        calculate_project_health,
        daily_health_snapshot,
        daily_spec_match_check,
        sales_reminder_scan,
        check_overdue_issues,
        check_blocking_issues,
        check_timeout_issues,
        daily_issue_statistics_snapshot,
        check_milestone_alerts,
        check_cost_overrun_alerts,
        check_workload_overload_alerts,
        # P0 预警服务
        generate_shortage_alerts,
        check_task_delay_alerts,
        check_production_plan_alerts,
        check_work_report_timeout,
        calculate_progress_summary,
        daily_kit_check,
        check_delivery_delay,
        check_task_deadline_reminder,
        check_outsourcing_delivery_alerts,
        check_milestone_risk_alerts,
        generate_production_daily_reports,
        generate_shortage_daily_report,
        generate_job_duty_tasks
    )
    
    # 注册事件监听器
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    # 添加定时任务
    
    # 1. 每小时计算项目健康度（整点执行）
    scheduler.add_job(
        calculate_project_health,
        'cron',
        minute=0,
        id='calculate_project_health',
        name='计算项目健康度',
        replace_existing=True
    )
    
    # 2. 每天凌晨2点生成健康度快照
    scheduler.add_job(
        daily_health_snapshot,
        'cron',
        hour=2,
        minute=0,
        id='daily_health_snapshot',
        name='每日健康度快照',
        replace_existing=True
    )
    
    # 3. 每天上午9点执行规格匹配检查
    scheduler.add_job(
        daily_spec_match_check,
        'cron',
        hour=9,
        minute=0,
        id='daily_spec_match_check',
        name='每日规格匹配检查',
        replace_existing=True
    )
    
    # 4. 每小时检查逾期问题（整点执行）
    scheduler.add_job(
        check_overdue_issues,
        'cron',
        minute=0,
        id='check_overdue_issues',
        name='问题逾期预警',
        replace_existing=True
    )
    
    # 5. 每小时检查阻塞问题（整点执行，在健康度计算之后）
    scheduler.add_job(
        check_blocking_issues,
        'cron',
        minute=5,
        id='check_blocking_issues',
        name='阻塞问题预警',
        replace_existing=True
    )
    
    # 6. 每天凌晨1点检查超时问题
    scheduler.add_job(
        check_timeout_issues,
        'cron',
        hour=1,
        minute=0,
        id='check_timeout_issues',
        name='问题超时升级',
        replace_existing=True
    )
    
    # 7. 每天凌晨3点生成问题统计快照
    scheduler.add_job(
        daily_issue_statistics_snapshot,
        'cron',
        hour=3,
        minute=0,
        id='daily_issue_statistics_snapshot',
        name='每日问题统计快照',
        replace_existing=True
    )
    
    # 8. 每天上午8点检查里程碑预警
    scheduler.add_job(
        check_milestone_alerts,
        'cron',
        hour=8,
        minute=0,
        id='check_milestone_alerts',
        name='里程碑预警',
        replace_existing=True
    )
    
    # 9. 每天上午10点检查成本超支预警
    scheduler.add_job(
        check_cost_overrun_alerts,
        'cron',
        hour=10,
        minute=0,
        id='check_cost_overrun_alerts',
        name='成本超支预警',
        replace_existing=True
    )
    
    # 10. 每天上午11点检查负荷超限预警
    scheduler.add_job(
        check_workload_overload_alerts,
        'cron',
        hour=11,
        minute=0,
        id='check_workload_overload_alerts',
        name='负荷超限预警',
        replace_existing=True
    )
    
    # ==================== P0 预警服务 ====================
    
    # 10. 每天上午7点生成缺料预警
    scheduler.add_job(
        generate_shortage_alerts,
        'cron',
        hour=7,
        minute=0,
        id='generate_shortage_alerts',
        name='缺料预警生成',
        replace_existing=True
    )
    
    # 11. 每小时检查任务延期预警（整点执行）
    scheduler.add_job(
        check_task_delay_alerts,
        'cron',
        minute=0,
        id='check_task_delay_alerts',
        name='任务延期预警',
        replace_existing=True
    )
    
    # 12. 每天上午11点检查生产计划预警
    scheduler.add_job(
        check_production_plan_alerts,
        'cron',
        hour=11,
        minute=0,
        id='check_production_plan_alerts',
        name='生产计划预警',
        replace_existing=True
    )
    
    # 13. 每小时检查报工超时提醒（整点执行）
    scheduler.add_job(
        check_work_report_timeout,
        'cron',
        minute=0,
        id='check_work_report_timeout',
        name='报工超时提醒',
        replace_existing=True
    )
    
    # 14. 每小时计算进度汇总（整点执行）
    scheduler.add_job(
        calculate_progress_summary,
        'cron',
        minute=0,
        id='calculate_progress_summary',
        name='进度汇总计算',
        replace_existing=True
    )
    
    # 15. 每天上午6点执行每日齐套检查
    scheduler.add_job(
        daily_kit_check,
        'cron',
        hour=6,
        minute=0,
        id='daily_kit_check',
        name='每日齐套检查',
        replace_existing=True
    )
    
    # 16. 每天下午2点检查到货延迟
    scheduler.add_job(
        check_delivery_delay,
        'cron',
        hour=14,
        minute=0,
        id='check_delivery_delay',
        name='到货延迟检查',
        replace_existing=True
    )
    
    # 17. 每小时检查任务到期提醒（整点执行）
    scheduler.add_job(
        check_task_deadline_reminder,
        'cron',
        minute=0,
        id='check_task_deadline_reminder',
        name='任务到期提醒',
        replace_existing=True
    )
    
    # 18. 每天下午3点检查外协交期预警
    scheduler.add_job(
        check_outsourcing_delivery_alerts,
        'cron',
        hour=15,
        minute=0,
        id='check_outsourcing_delivery_alerts',
        name='外协交期预警',
        replace_existing=True
    )
    
    # 19. 每天上午8点检查里程碑风险预警（与里程碑预警一起执行）
    scheduler.add_job(
        check_milestone_risk_alerts,
        'cron',
        hour=8,
        minute=10,
        id='check_milestone_risk_alerts',
        name='里程碑风险预警',
        replace_existing=True
    )
    
    # 20. 每天凌晨5点生成生产日报
    scheduler.add_job(
        generate_production_daily_reports,
        'cron',
        hour=5,
        minute=0,
        id='generate_production_daily_reports',
        name='生产日报自动生成',
        replace_existing=True
    )
    
    # 21. 每天凌晨5点15分生成缺料日报
    scheduler.add_job(
        generate_shortage_daily_report,
        'cron',
        hour=5,
        minute=15,
        id='generate_shortage_daily_report',
        name='缺料日报自动生成',
        replace_existing=True
    )
    
    # 22. 每天凌晨4点生成岗位职责任务
    scheduler.add_job(
        generate_job_duty_tasks,
        'cron',
        hour=4,
        minute=0,
        id='generate_job_duty_tasks',
        name='岗位职责任务生成',
        replace_existing=True
    )
    
    # 启动调度器
    scheduler.start()
    logger.info("定时任务调度器已启动（包含12个P0预警服务）")
    
    return scheduler


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")


# 注意：应用启动和关闭的钩子在 app/main.py 中定义
