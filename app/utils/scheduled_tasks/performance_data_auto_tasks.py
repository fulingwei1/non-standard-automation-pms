# -*- coding: utf-8 -*-
"""
绩效数据自动同步定时任务
"""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.models.base import get_db_session
from app.services.work_log_auto_generator import WorkLogAutoGenerator
from app.services.design_review_sync_service import DesignReviewSyncService
from app.services.debug_issue_sync_service import DebugIssueSyncService
from app.services.knowledge_auto_identification_service import KnowledgeAutoIdentificationService


def daily_work_log_generation_task():
    """
    每日工作日志自动生成任务
    每天凌晨1点执行，生成昨日工作日志
    """
    with get_db_session() as db:
        generator = WorkLogAutoGenerator(db)
        stats = generator.generate_yesterday_work_logs(auto_submit=False)

        print(f"[工作日志自动生成] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  总用户数: {stats['total_users']}")
        print(f"  生成数量: {stats['generated_count']}")
        print(f"  跳过数量: {stats['skipped_count']}")
        print(f"  错误数量: {stats['error_count']}")

        if stats['errors']:
            print(f"  错误详情:")
            for error in stats['errors'][:5]:  # 只显示前5个错误
                print(f"    - {error['user_name']} ({error['date']}): {error['error']}")

        return stats


def daily_design_review_sync_task():
    """
    每日设计评审自动同步任务
    每天凌晨2点执行，同步昨日完成的技术评审
    """
    with get_db_session() as db:
        sync_service = DesignReviewSyncService(db)
        yesterday = date.today() - timedelta(days=1)

        stats = sync_service.sync_all_completed_reviews(
            start_date=yesterday,
            end_date=yesterday
        )

        print(f"[设计评审自动同步] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  总评审数: {stats['total_reviews']}")
        print(f"  同步数量: {stats['synced_count']}")
        print(f"  跳过数量: {stats['skipped_count']}")
        print(f"  错误数量: {stats['error_count']}")

        if stats['errors']:
            print(f"  错误详情:")
            for error in stats['errors'][:5]:
                print(f"    - {error['review_no']}: {error['error']}")

        return stats


def daily_debug_issue_sync_task():
    """
    每日调试问题自动同步任务
    每天凌晨3点执行，同步昨日创建/解决的问题
    """
    with get_db_session() as db:
        sync_service = DebugIssueSyncService(db)
        yesterday = date.today() - timedelta(days=1)

        stats = sync_service.sync_all_project_issues(
            start_date=yesterday,
            end_date=yesterday
        )

        print(f"[调试问题自动同步] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  总问题数: {stats['total_issues']}")
        print(f"  同步数量: {stats['synced_count']}")
        print(f"  机械调试: {stats['mechanical_debug_count']}")
        print(f"  测试Bug: {stats['test_bug_count']}")
        print(f"  跳过数量: {stats['skipped_count']}")
        print(f"  错误数量: {stats['error_count']}")

        if stats['errors']:
            print(f"  错误详情:")
            for error in stats['errors'][:5]:
                print(f"    - {error['issue_no']}: {error['error']}")

        return stats


def weekly_knowledge_identification_task():
    """
    每周知识贡献自动识别任务
    每周一凌晨4点执行，识别上周的知识贡献
    """
    with get_db_session() as db:
        identification_service = KnowledgeAutoIdentificationService(db)

        # 上周日期范围
        today = date.today()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)

        # 从服务工单识别
        ticket_stats = identification_service.batch_identify_from_service_tickets(
            start_date=last_monday,
            end_date=last_sunday
        )

        # 从知识库识别
        kb_stats = identification_service.batch_identify_from_knowledge_base(
            start_date=last_monday,
            end_date=last_sunday
        )

        print(f"[知识贡献自动识别] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  服务工单:")
        print(f"    总工单数: {ticket_stats['total_tickets']}")
        print(f"    识别数量: {ticket_stats['identified_count']}")
        print(f"  知识库:")
        print(f"    总文章数: {kb_stats['total_articles']}")
        print(f"    识别数量: {kb_stats['identified_count']}")

        return {
            'ticket_stats': ticket_stats,
            'kb_stats': kb_stats
        }


def sync_all_performance_data_task():
    """
    同步所有绩效数据任务（手动触发或定期执行）
    """
    with get_db_session() as db:
        results = {}

        # 1. 生成工作日志（最近7天）
        print("\n[1] 生成工作日志...")
        generator = WorkLogAutoGenerator(db)
        week_ago = date.today() - timedelta(days=7)
        work_log_stats = generator.batch_generate_work_logs(
            start_date=week_ago,
            end_date=date.today(),
            auto_submit=False
        )
        results['work_log'] = work_log_stats

        # 2. 同步设计评审（最近30天）
        print("\n[2] 同步设计评审...")
        design_sync = DesignReviewSyncService(db)
        month_ago = date.today() - timedelta(days=30)
        design_stats = design_sync.sync_all_completed_reviews(
            start_date=month_ago,
            end_date=date.today()
        )
        results['design_review'] = design_stats

        # 3. 同步调试问题（最近30天）
        print("\n[3] 同步调试问题...")
        debug_sync = DebugIssueSyncService(db)
        debug_stats = debug_sync.sync_all_project_issues(
            start_date=month_ago,
            end_date=date.today()
        )
        results['debug_issue'] = debug_stats

        # 4. 识别知识贡献（最近30天）
        print("\n[4] 识别知识贡献...")
        knowledge_service = KnowledgeAutoIdentificationService(db)
        ticket_stats = knowledge_service.batch_identify_from_service_tickets(
            start_date=month_ago,
            end_date=date.today()
        )
        kb_stats = knowledge_service.batch_identify_from_knowledge_base(
            start_date=month_ago,
            end_date=date.today()
        )
        results['knowledge'] = {
            'ticket_stats': ticket_stats,
            'kb_stats': kb_stats
        }

        print("\n[完成] 所有绩效数据同步完成")
        return results
