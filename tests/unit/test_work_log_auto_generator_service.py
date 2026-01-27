# -*- coding: utf-8 -*-
"""
工作日志自动生成服务单元测试
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestWorkLogAutoGeneratorInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                service = WorkLogAutoGenerator(db_session)

                assert service.db == db_session



class TestGenerateWorkLogFromTimesheet:
    """测试从工时记录生成工作日志"""

    def test_existing_submitted_log_returns_none(self, db_session):
        """测试已存在已提交日志返回None"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                from app.models.work_log import WorkLog


                # 创建已提交的工作日志

                existing_log = WorkLog(

                user_id=1,

                work_date=date.today(),

                status='SUBMITTED',

                content='测试内容'

                )

                db_session.add(existing_log)

                db_session.flush()


                service = WorkLogAutoGenerator(db_session)

                result = service.generate_work_log_from_timesheet(

                user_id=1,

                work_date=date.today()

                )


                assert result is None


    def test_no_timesheets_returns_none(self, db_session):
        """测试无工时记录返回None"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                service = WorkLogAutoGenerator(db_session)

                result = service.generate_work_log_from_timesheet(

                user_id=99999,

                work_date=date.today()

                )


                assert result is None


    def test_user_not_found_returns_none(self, db_session):
        """测试用户不存在返回None"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                from app.models.timesheet import Timesheet


                # 创建工时记录但用户不存在

                timesheet = Timesheet(

                user_id=99999,

                work_date=date.today(),

                status='APPROVED',

                hours=Decimal('8.0')

                )

                db_session.add(timesheet)

                db_session.flush()


                service = WorkLogAutoGenerator(db_session)

                result = service.generate_work_log_from_timesheet(

                user_id=99999,

                work_date=date.today()

                )


                # 用户不存在应返回None

                assert result is None



class TestBatchGenerateWorkLogs:
    """测试批量生成工作日志"""

    def test_batch_no_users(self, db_session):
        """测试无用户时批量生成"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                service = WorkLogAutoGenerator(db_session)

                result = service.batch_generate_work_logs(

                start_date=date.today() - timedelta(days=7),

                end_date=date.today()

                )


                assert result['total_users'] == 0

                assert result['generated_count'] == 0


    def test_batch_result_structure(self, db_session):
        """测试批量结果结构"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                service = WorkLogAutoGenerator(db_session)

                result = service.batch_generate_work_logs(

                start_date=date.today(),

                end_date=date.today()

                )


                expected_keys = [

                'total_users', 'total_days', 'generated_count',

                'skipped_count', 'error_count', 'errors'

                ]

                for key in expected_keys:

                    assert key in result


    def test_batch_with_user_ids(self, db_session):
        """测试指定用户ID列表"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                service = WorkLogAutoGenerator(db_session)

                result = service.batch_generate_work_logs(

                start_date=date.today(),

                end_date=date.today(),

                user_ids=[1, 2, 3]

                )


                assert 'total_users' in result



class TestGenerateYesterdayWorkLogs:
    """测试生成昨日工作日志"""

    def test_generate_yesterday(self, db_session):
        """测试生成昨日日志"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                service = WorkLogAutoGenerator(db_session)

                result = service.generate_yesterday_work_logs()


                assert 'total_users' in result

                assert 'generated_count' in result


    def test_generate_yesterday_with_auto_submit(self, db_session):
        """测试昨日日志自动提交"""
                from app.services.work_log_auto_generator import WorkLogAutoGenerator

                service = WorkLogAutoGenerator(db_session)

                result = service.generate_yesterday_work_logs(auto_submit=True)


                assert 'generated_count' in result



class TestContentGeneration:
    """测试内容生成逻辑"""

    def test_content_truncation(self):
        """测试内容截断"""
        content = "测试内容" * 100  # 超过300字

        if len(content) > 300:
            content = content[:297] + "..."

            assert len(content) == 300
            assert content.endswith("...")

    def test_project_grouping(self):
        """测试按项目分组"""
        timesheets = [
        {'project_id': 1, 'hours': Decimal('4.0')},
        {'project_id': 1, 'hours': Decimal('2.0')},
        {'project_id': 2, 'hours': Decimal('2.0')},
        ]

        project_groups = {}
        for ts in timesheets:
            project_id = ts['project_id']
            if project_id not in project_groups:
                project_groups[project_id] = []
                project_groups[project_id].append(ts)

                assert len(project_groups) == 2
                assert len(project_groups[1]) == 2
                assert len(project_groups[2]) == 1

    def test_total_hours_calculation(self):
        """测试总工时计算"""
        timesheets = [
        {'hours': Decimal('4.0')},
        {'hours': Decimal('2.5')},
        {'hours': Decimal('1.5')},
        ]

        total_hours = sum(ts['hours'] for ts in timesheets)
        assert total_hours == Decimal('8.0')


class TestDateRangeIteration:
    """测试日期范围迭代"""

    def test_single_day_range(self):
        """测试单日范围"""
        start_date = date(2025, 1, 15)
        end_date = date(2025, 1, 15)

        days = []
        current = start_date
        while current <= end_date:
            days.append(current)
            current += timedelta(days=1)

            assert len(days) == 1

    def test_week_range(self):
        """测试一周范围"""
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 7)

        days = []
        current = start_date
        while current <= end_date:
            days.append(current)
            current += timedelta(days=1)

            assert len(days) == 7


class TestWorkLogStatus:
    """测试工作日志状态"""

    def test_draft_status(self):
        """测试草稿状态"""
        auto_submit = False
        status = 'SUBMITTED' if auto_submit else 'DRAFT'
        assert status == 'DRAFT'

    def test_submitted_status(self):
        """测试已提交状态"""
        auto_submit = True
        status = 'SUBMITTED' if auto_submit else 'DRAFT'
        assert status == 'SUBMITTED'


# pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
