# -*- coding: utf-8 -*-
"""
工时报表服务单元测试

策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
from decimal import Decimal

from app.services.report_service import ReportService
from app.models.report import (
    ReportTypeEnum,
    GeneratedByEnum,
    ArchiveStatusEnum,
)


class TestReportServiceGetTemplates(unittest.TestCase):
    """测试获取报表模板"""

    def setUp(self):
        self.db = MagicMock()

    def test_get_active_monthly_templates(self):
        """测试获取启用的月度报表模板"""
        # Mock返回结果
        mock_template1 = MagicMock()
        mock_template1.id = 1
        mock_template1.name = "人员月报"
        mock_template1.enabled = True
        mock_template1.frequency = 'MONTHLY'

        mock_template2 = MagicMock()
        mock_template2.id = 2
        mock_template2.name = "部门月报"
        mock_template2.enabled = True
        mock_template2.frequency = 'MONTHLY'

        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_template1,
            mock_template2,
        ]

        # 调用
        result = ReportService.get_active_monthly_templates(self.db)

        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "人员月报")
        self.assertEqual(result[1].name, "部门月报")

    def test_get_active_monthly_templates_empty(self):
        """测试没有启用的模板"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = ReportService.get_active_monthly_templates(self.db)

        self.assertEqual(len(result), 0)


class TestReportServiceGenerateReport(unittest.TestCase):
    """测试报表生成主入口"""

    def setUp(self):
        self.db = MagicMock()

    def test_generate_report_template_not_found(self):
        """测试模板不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            ReportService.generate_report(self.db, template_id=999, period="2026-01")

        self.assertIn("报表模板不存在", str(context.exception))

    @patch.object(ReportService, '_generate_user_monthly_report')
    def test_generate_report_user_monthly(self, mock_generate):
        """测试生成人员月度报表"""
        # Mock模板
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "人员月报"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        # Mock生成方法返回
        mock_generate.return_value = {
            'summary': [{'user_name': '张三', 'total_hours': 160}],
            'detail': [],
            'year': 2026,
            'month': 1,
        }

        # 调用
        result = ReportService.generate_report(self.db, template_id=1, period="2026-01")

        # 验证
        self.assertEqual(result['period'], "2026-01")
        self.assertEqual(result['generated_by'], GeneratedByEnum.SYSTEM.value)
        self.assertEqual(result['template'], mock_template)
        self.assertIn('summary', result)
        mock_generate.assert_called_once_with(self.db, mock_template, 2026, 1)

    @patch.object(ReportService, '_generate_dept_monthly_report')
    def test_generate_report_dept_monthly(self, mock_generate):
        """测试生成部门月度报表"""
        mock_template = MagicMock()
        mock_template.report_type = ReportTypeEnum.DEPT_MONTHLY.value

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        mock_generate.return_value = {
            'summary': [],
            'detail': [],
            'year': 2026,
            'month': 1,
        }

        result = ReportService.generate_report(self.db, template_id=2, period="2026-01")

        self.assertIn('summary', result)
        mock_generate.assert_called_once()

    @patch.object(ReportService, '_generate_project_monthly_report')
    def test_generate_report_project_monthly(self, mock_generate):
        """测试生成项目月度报表"""
        mock_template = MagicMock()
        mock_template.report_type = ReportTypeEnum.PROJECT_MONTHLY.value

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        mock_generate.return_value = {'summary': [], 'detail': [], 'year': 2026, 'month': 1}

        ReportService.generate_report(self.db, template_id=3, period="2026-01")

        mock_generate.assert_called_once()

    @patch.object(ReportService, '_generate_company_monthly_report')
    def test_generate_report_company_monthly(self, mock_generate):
        """测试生成公司整体报表"""
        mock_template = MagicMock()
        mock_template.report_type = ReportTypeEnum.COMPANY_MONTHLY.value

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        mock_generate.return_value = {'summary': [], 'detail': [], 'year': 2026, 'month': 1}

        ReportService.generate_report(self.db, template_id=4, period="2026-01")

        mock_generate.assert_called_once()

    @patch.object(ReportService, '_generate_overtime_monthly_report')
    def test_generate_report_overtime_monthly(self, mock_generate):
        """测试生成加班统计报表"""
        mock_template = MagicMock()
        mock_template.report_type = ReportTypeEnum.OVERTIME_MONTHLY.value

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        mock_generate.return_value = {'summary': [], 'detail': [], 'year': 2026, 'month': 1}

        ReportService.generate_report(self.db, template_id=5, period="2026-01")

        mock_generate.assert_called_once()

    def test_generate_report_unsupported_type(self):
        """测试不支持的报表类型"""
        mock_template = MagicMock()
        mock_template.report_type = "UNKNOWN_TYPE"

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        with self.assertRaises(ValueError) as context:
            ReportService.generate_report(self.db, template_id=99, period="2026-01")

        self.assertIn("不支持的报表类型", str(context.exception))


class TestReportServiceUserMonthly(unittest.TestCase):
    """测试人员月度报表生成"""

    def setUp(self):
        self.db = MagicMock()
        self.mock_template = MagicMock()
        self.mock_template.config = None

    def test_generate_user_monthly_report(self):
        """测试生成人员月度报表"""
        # Mock工时汇总数据
        mock_row1 = MagicMock()
        mock_row1.user_id = 1
        mock_row1.user_name = "张三"
        mock_row1.department_name = "研发部"
        mock_row1.total_hours = Decimal("168.0")
        mock_row1.normal_hours = Decimal("160.0")
        mock_row1.overtime_hours = Decimal("8.0")
        mock_row1.work_days = 21

        mock_row2 = MagicMock()
        mock_row2.user_id = 2
        mock_row2.user_name = "李四"
        mock_row2.department_name = "研发部"
        mock_row2.total_hours = Decimal("176.0")
        mock_row2.normal_hours = Decimal("160.0")
        mock_row2.overtime_hours = Decimal("16.0")
        mock_row2.work_days = 22

        # Mock明细数据
        mock_ts1 = MagicMock()
        mock_ts1.user_name = "张三"
        mock_ts1.department_name = "研发部"
        mock_ts1.work_date = datetime(2026, 1, 5)
        mock_ts1.project_name = "项目A"
        mock_ts1.task_name = "开发任务1"
        mock_ts1.hours = Decimal("8.0")
        mock_ts1.overtime_type = "NORMAL"
        mock_ts1.work_content = "编码开发"

        # Mock query链式调用
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row1, mock_row2]

        mock_detail_query = MagicMock()
        mock_detail_query.filter.return_value = mock_detail_query
        mock_detail_query.all.return_value = [mock_ts1]

        # 第一次调用返回汇总query，第二次返回明细query
        self.db.query.side_effect = [mock_query, mock_detail_query]

        # 调用
        result = ReportService._generate_user_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        # 验证
        self.assertEqual(result['year'], 2026)
        self.assertEqual(result['month'], 1)
        self.assertEqual(len(result['summary']), 2)
        self.assertEqual(len(result['detail']), 1)

        # 验证汇总数据
        self.assertEqual(result['summary'][0]['user_name'], "张三")
        self.assertEqual(result['summary'][0]['total_hours'], 168.0)
        self.assertEqual(result['summary'][0]['work_days'], 21)
        self.assertEqual(result['summary'][0]['avg_hours_per_day'], 8.0)

        # 验证明细数据
        self.assertEqual(result['detail'][0]['user_name'], "张三")
        self.assertEqual(result['detail'][0]['hours'], 8.0)
        self.assertEqual(result['detail'][0]['work_date'], "2026-01-05")

    def test_generate_user_monthly_report_with_filters(self):
        """测试带部门过滤条件的报表"""
        self.mock_template.config = {
            'filters': {'department_ids': [1, 2]}
        }

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        mock_detail_query = MagicMock()
        mock_detail_query.filter.return_value = mock_detail_query
        mock_detail_query.all.return_value = []

        self.db.query.side_effect = [mock_query, mock_detail_query]

        result = ReportService._generate_user_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(len(result['summary']), 0)
        self.assertEqual(len(result['detail']), 0)

    def test_generate_user_monthly_report_december(self):
        """测试12月的报表（边界情况：跨年）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        mock_detail_query = MagicMock()
        mock_detail_query.filter.return_value = mock_detail_query
        mock_detail_query.all.return_value = []

        self.db.query.side_effect = [mock_query, mock_detail_query]

        result = ReportService._generate_user_monthly_report(
            self.db, self.mock_template, 2025, 12
        )

        self.assertEqual(result['year'], 2025)
        self.assertEqual(result['month'], 12)

    def test_generate_user_monthly_report_zero_work_days(self):
        """测试0工作日情况（避免除零错误）"""
        mock_row = MagicMock()
        mock_row.user_id = 1
        mock_row.user_name = "张三"
        mock_row.department_name = "研发部"
        mock_row.total_hours = Decimal("0")
        mock_row.normal_hours = Decimal("0")
        mock_row.overtime_hours = Decimal("0")
        mock_row.work_days = 0  # 零工作日

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]

        mock_detail_query = MagicMock()
        mock_detail_query.filter.return_value = mock_detail_query
        mock_detail_query.all.return_value = []

        self.db.query.side_effect = [mock_query, mock_detail_query]

        result = ReportService._generate_user_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        # 验证没有除零错误
        self.assertEqual(result['summary'][0]['avg_hours_per_day'], 0)


class TestReportServiceDeptMonthly(unittest.TestCase):
    """测试部门月度报表"""

    def setUp(self):
        self.db = MagicMock()
        self.mock_template = MagicMock()

    def test_generate_dept_monthly_report(self):
        """测试生成部门月度报表"""
        mock_row = MagicMock()
        mock_row.department_id = 1
        mock_row.department_name = "研发部"
        mock_row.user_count = 10
        mock_row.total_hours = Decimal("1600.0")
        mock_row.normal_hours = Decimal("1500.0")
        mock_row.overtime_hours = Decimal("100.0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]

        self.db.query.return_value = mock_query

        result = ReportService._generate_dept_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(len(result['summary']), 1)
        self.assertEqual(result['summary'][0]['department_name'], "研发部")
        self.assertEqual(result['summary'][0]['user_count'], 10)
        self.assertEqual(result['summary'][0]['total_hours'], 1600.0)
        self.assertEqual(result['summary'][0]['avg_hours_per_user'], 160.0)

    def test_generate_dept_monthly_report_zero_users(self):
        """测试0用户的部门（避免除零）"""
        mock_row = MagicMock()
        mock_row.department_id = 1
        mock_row.department_name = "空部门"
        mock_row.user_count = 0
        mock_row.total_hours = Decimal("0")
        mock_row.normal_hours = Decimal("0")
        mock_row.overtime_hours = Decimal("0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]

        self.db.query.return_value = mock_query

        result = ReportService._generate_dept_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(result['summary'][0]['avg_hours_per_user'], 0)


class TestReportServiceProjectMonthly(unittest.TestCase):
    """测试项目月度报表"""

    def setUp(self):
        self.db = MagicMock()
        self.mock_template = MagicMock()

    def test_generate_project_monthly_report(self):
        """测试生成项目月度报表"""
        mock_row1 = MagicMock()
        mock_row1.project_id = 1
        mock_row1.project_name = "项目A"
        mock_row1.user_count = 5
        mock_row1.total_hours = Decimal("400.0")

        mock_row2 = MagicMock()
        mock_row2.project_id = 2
        mock_row2.project_name = "项目B"
        mock_row2.user_count = 3
        mock_row2.total_hours = Decimal("240.0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row1, mock_row2]

        self.db.query.return_value = mock_query

        result = ReportService._generate_project_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(len(result['summary']), 2)
        self.assertEqual(result['summary'][0]['project_name'], "项目A")
        self.assertEqual(result['summary'][0]['total_hours'], 400.0)
        self.assertEqual(result['summary'][0]['avg_hours_per_user'], 80.0)


class TestReportServiceCompanyMonthly(unittest.TestCase):
    """测试公司整体报表"""

    def setUp(self):
        self.db = MagicMock()
        self.mock_template = MagicMock()

    def test_generate_company_monthly_report(self):
        """测试生成公司整体报表"""
        mock_stats = MagicMock()
        mock_stats.total_users = 50
        mock_stats.total_hours = Decimal("8000.0")
        mock_stats.normal_hours = Decimal("7500.0")
        mock_stats.overtime_hours = Decimal("500.0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stats

        self.db.query.return_value = mock_query

        result = ReportService._generate_company_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(len(result['summary']), 1)
        self.assertEqual(result['summary'][0]['total_users'], 50)
        self.assertEqual(result['summary'][0]['total_hours'], 8000.0)
        self.assertEqual(result['summary'][0]['avg_hours_per_user'], 160.0)

    def test_generate_company_monthly_report_zero_users(self):
        """测试0用户情况"""
        mock_stats = MagicMock()
        mock_stats.total_users = 0
        mock_stats.total_hours = Decimal("0")
        mock_stats.normal_hours = Decimal("0")
        mock_stats.overtime_hours = Decimal("0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stats

        self.db.query.return_value = mock_query

        result = ReportService._generate_company_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(result['summary'][0]['avg_hours_per_user'], 0)


class TestReportServiceOvertimeMonthly(unittest.TestCase):
    """测试加班统计报表"""

    def setUp(self):
        self.db = MagicMock()
        self.mock_template = MagicMock()

    def test_generate_overtime_monthly_report(self):
        """测试生成加班统计报表"""
        mock_row = MagicMock()
        mock_row.user_id = 1
        mock_row.user_name = "张三"
        mock_row.department_name = "研发部"
        mock_row.overtime_hours = Decimal("10.0")
        mock_row.weekend_hours = Decimal("16.0")
        mock_row.holiday_hours = Decimal("8.0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]

        self.db.query.return_value = mock_query

        result = ReportService._generate_overtime_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(len(result['summary']), 1)
        self.assertEqual(result['summary'][0]['user_name'], "张三")
        self.assertEqual(result['summary'][0]['overtime_hours'], 10.0)
        self.assertEqual(result['summary'][0]['weekend_hours'], 16.0)
        self.assertEqual(result['summary'][0]['holiday_hours'], 8.0)
        self.assertEqual(result['summary'][0]['total_overtime'], 34.0)

    def test_generate_overtime_monthly_report_null_values(self):
        """测试NULL值情况"""
        mock_row = MagicMock()
        mock_row.user_id = 1
        mock_row.user_name = "李四"
        mock_row.department_name = "测试部"
        mock_row.overtime_hours = None
        mock_row.weekend_hours = Decimal("8.0")
        mock_row.holiday_hours = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]

        self.db.query.return_value = mock_query

        result = ReportService._generate_overtime_monthly_report(
            self.db, self.mock_template, 2026, 1
        )

        self.assertEqual(result['summary'][0]['overtime_hours'], 0.0)
        self.assertEqual(result['summary'][0]['weekend_hours'], 8.0)
        self.assertEqual(result['summary'][0]['holiday_hours'], 0.0)
        self.assertEqual(result['summary'][0]['total_overtime'], 8.0)


class TestReportServiceUtility(unittest.TestCase):
    """测试工具方法"""

    def test_get_last_month_period_january(self):
        """测试1月份获取上月（12月）"""
        with patch('app.services.report_service.datetime') as mock_datetime:
            # Mock datetime.now() 返回值
            mock_now = MagicMock()
            mock_now.year = 2026
            mock_now.month = 1
            mock_datetime.now.return_value = mock_now
            
            # Mock datetime() 构造函数的行为
            def datetime_side_effect(year, month, day=1):
                mock_dt = MagicMock()
                mock_dt.strftime.return_value = f"{year}-{month:02d}"
                return mock_dt
            
            mock_datetime.side_effect = datetime_side_effect
            
            result = ReportService.get_last_month_period()
            
            self.assertEqual(result, "2025-12")

    def test_get_last_month_period_february(self):
        """测试2月份获取上月（1月）"""
        with patch('app.services.report_service.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.year = 2026
            mock_now.month = 2
            mock_datetime.now.return_value = mock_now
            
            def datetime_side_effect(year, month, day=1):
                mock_dt = MagicMock()
                mock_dt.strftime.return_value = f"{year}-{month:02d}"
                return mock_dt
            
            mock_datetime.side_effect = datetime_side_effect
            
            result = ReportService.get_last_month_period()
            
            self.assertEqual(result, "2026-01")

    def test_get_last_month_period_december(self):
        """测试12月份获取上月（11月）"""
        with patch('app.services.report_service.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.year = 2026
            mock_now.month = 12
            mock_datetime.now.return_value = mock_now
            
            def datetime_side_effect(year, month, day=1):
                mock_dt = MagicMock()
                mock_dt.strftime.return_value = f"{year}-{month:02d}"
                return mock_dt
            
            mock_datetime.side_effect = datetime_side_effect
            
            result = ReportService.get_last_month_period()
            
            self.assertEqual(result, "2026-11")


class TestReportServiceArchive(unittest.TestCase):
    """测试报表归档"""

    def setUp(self):
        self.db = MagicMock()

    @patch('app.services.report_service.save_obj')
    @patch('app.services.report_service.datetime')
    def test_archive_report_success(self, mock_datetime, mock_save_obj):
        """测试成功归档报表"""
        mock_datetime.utcnow.return_value = datetime(2026, 2, 1, 10, 0, 0)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "人员月报"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        # 调用
        result = ReportService.archive_report(
            db=self.db,
            template_id=1,
            period="2026-01",
            file_path="/path/to/report.xlsx",
            file_size=10240,
            row_count=100,
        )

        # 验证save_obj被调用
        mock_save_obj.assert_called_once()
        archive = mock_save_obj.call_args[0][1]

        self.assertEqual(archive.template_id, 1)
        self.assertEqual(archive.report_type, ReportTypeEnum.USER_MONTHLY.value)
        self.assertEqual(archive.period, "2026-01")
        self.assertEqual(archive.file_path, "/path/to/report.xlsx")
        self.assertEqual(archive.file_size, 10240)
        self.assertEqual(archive.row_count, 100)
        self.assertEqual(archive.generated_by, GeneratedByEnum.SYSTEM.value)
        self.assertEqual(archive.status, ArchiveStatusEnum.SUCCESS.value)
        self.assertEqual(archive.download_count, 0)

    @patch('app.services.report_service.save_obj')
    def test_archive_report_with_error(self, mock_save_obj):
        """测试归档失败的报表"""
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value

        self.db.query.return_value.filter.return_value.first.return_value = mock_template

        ReportService.archive_report(
            db=self.db,
            template_id=1,
            period="2026-01",
            file_path="/path/to/failed.xlsx",
            file_size=0,
            row_count=0,
            status=ArchiveStatusEnum.FAILED.value,
            error_message="磁盘空间不足",
        )

        archive = mock_save_obj.call_args[0][1]
        self.assertEqual(archive.status, ArchiveStatusEnum.FAILED.value)
        self.assertEqual(archive.error_message, "磁盘空间不足")

    def test_archive_report_template_not_found(self):
        """测试模板不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            ReportService.archive_report(
                db=self.db,
                template_id=999,
                period="2026-01",
                file_path="/path/to/report.xlsx",
                file_size=10240,
                row_count=100,
            )

        self.assertIn("报表模板不存在", str(context.exception))


class TestReportServiceIncrementDownload(unittest.TestCase):
    """测试下载次数增加"""

    def setUp(self):
        self.db = MagicMock()

    def test_increment_download_count(self):
        """测试增加下载次数"""
        mock_archive = MagicMock()
        mock_archive.id = 1
        mock_archive.download_count = 5

        self.db.query.return_value.filter.return_value.first.return_value = mock_archive

        ReportService.increment_download_count(self.db, archive_id=1)

        self.assertEqual(mock_archive.download_count, 6)
        self.db.commit.assert_called_once()

    def test_increment_download_count_not_found(self):
        """测试归档不存在（不应抛出异常）"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        # 应该不抛出异常
        ReportService.increment_download_count(self.db, archive_id=999)

        self.db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
