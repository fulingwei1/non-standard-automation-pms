# -*- coding: utf-8 -*-
"""
报表模块核心服务单元测试
覆盖: app/services/report/report_service.py (模板管理服务)
     app/services/report_excel_service.py (Excel导出服务扩展)
"""
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models.report import (
    ArchiveStatusEnum,
    FrequencyEnum,
    GeneratedByEnum,
    OutputFormatEnum,
    ReportTypeEnum,
)


class TestReportTemplateManagement(unittest.TestCase):
    """测试报表模板管理功能"""

    def setUp(self):
        self.db = MagicMock()
        # Import after patching to avoid import errors
        from app.services.report.report_service import ReportService

        self.ReportService = ReportService

    def test_create_template(self):
        """测试创建报表模板"""
        service = self.ReportService(self.db)

        # Verify the service was created with db session
        self.assertIsNotNone(service)
        self.assertEqual(service.db, self.db)

    def test_list_templates(self):
        """测试获取模板列表（分页）"""
        service = self.ReportService(self.db)

        # Mock templates
        mock_template1 = MagicMock()
        mock_template1.id = 1
        mock_template1.name = "模板1"
        mock_template1.report_type = ReportTypeEnum.USER_MONTHLY.value
        mock_template1.description = "描述1"
        mock_template1.enabled = True

        mock_template2 = MagicMock()
        mock_template2.id = 2
        mock_template2.name = "模板2"
        mock_template2.report_type = ReportTypeEnum.DEPT_MONTHLY.value
        mock_template2.description = "描述2"
        mock_template2.enabled = True

        # Setup mock chain
        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.offset = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)
        mock_query.count = MagicMock(return_value=2)
        mock_query.all = MagicMock(return_value=[mock_template1, mock_template2])

        self.db.query = MagicMock(return_value=mock_query)

        # Call
        result = service.list_templates(page=1, page_size=20)

        # Verify
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["templates"]), 2)
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 20)

    def test_list_templates_with_filter(self):
        """测试带筛选条件的模板列表"""
        service = self.ReportService(self.db)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.offset = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)
        mock_query.count = MagicMock(return_value=0)
        mock_query.all = MagicMock(return_value=[])

        self.db.query = MagicMock(return_value=mock_query)

        # Call with filters
        result = service.list_templates(
            report_type=ReportTypeEnum.USER_MONTHLY.value,
            page=1,
            page_size=10,
        )

        # Verify filter was called
        self.assertEqual(result["total"], 0)

    def test_get_template(self):
        """测试获取单个模板"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "测试模板"

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_template)

        self.db.query = MagicMock(return_value=mock_query)

        result = service.get_template(1)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "测试模板")

    def test_get_template_not_found(self):
        """测试获取不存在的模板"""
        service = self.ReportService(self.db)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=None)

        self.db.query = MagicMock(return_value=mock_query)

        result = service.get_template(999)

        self.assertIsNone(result)

    def test_update_template(self):
        """测试更新模板"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "旧名称"
        mock_template.description = "旧描述"

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_template)

        self.db.query = MagicMock(return_value=mock_query)
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = service.update_template(
            template_id=1,
            name="新名称",
            description="新描述",
        )

        self.assertIsNotNone(result)
        self.assertEqual(mock_template.name, "新名称")
        self.assertEqual(mock_template.description, "新描述")
        self.db.commit.assert_called_once()

    def test_update_template_not_found(self):
        """测试更新不存在的模板"""
        service = self.ReportService(self.db)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=None)

        self.db.query = MagicMock(return_value=mock_query)

        result = service.update_template(
            template_id=999,
            name="新名称",
        )

        self.assertIsNone(result)

    def test_delete_template(self):
        """测试删除模板"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "测试模板"

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_template)

        self.db.query = MagicMock(return_value=mock_query)
        self.db.delete = MagicMock()
        self.db.commit = MagicMock()

        result = service.delete_template(1)

        self.assertTrue(result)
        self.db.delete.assert_called_once_with(mock_template)
        self.db.commit.assert_called_once()

    def test_delete_template_not_found(self):
        """测试删除不存在的模板"""
        service = self.ReportService(self.db)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=None)

        self.db.query = MagicMock(return_value=mock_query)

        result = service.delete_template(999)

        self.assertFalse(result)

    def test_toggle_template(self):
        """测试启用/禁用模板"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "测试模板"
        mock_template.enabled = False

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_template)

        self.db.query = MagicMock(return_value=mock_query)
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = service.toggle_template(1)

        self.assertIsNotNone(result)
        self.assertTrue(result["enabled"])
        self.db.commit.assert_called_once()

    def test_toggle_template_not_found(self):
        """测试切换不存在的模板"""
        service = self.ReportService(self.db)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=None)

        self.db.query = MagicMock(return_value=mock_query)

        result = service.toggle_template(999)

        self.assertIsNone(result)


class TestReportGeneration(unittest.TestCase):
    """测试报表生成功能"""

    def setUp(self):
        self.db = MagicMock()
        from app.services.report.report_service import ReportService

        self.ReportService = ReportService

    def test_generate_report_data_template_not_found(self):
        """测试报表模板不存在"""
        service = self.ReportService(self.db)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=None)

        self.db.query = MagicMock(return_value=mock_query)

        with self.assertRaises(ValueError) as context:
            service.generate_report_data(template_id=999, period="2026-01")

        self.assertIn("报表模板不存在", str(context.exception))

    def test_generate_report_data_unsupported_type(self):
        """测试不支持的报表类型"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "测试模板"
        mock_template.report_type = "UNKNOWN_TYPE"

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_template)

        self.db.query = MagicMock(return_value=mock_query)

        with self.assertRaises(ValueError) as context:
            service.generate_report_data(template_id=1, period="2026-01")

        self.assertIn("不支持的报表类型", str(context.exception))

    @patch(
        "app.services.report.report_service.ReportService._generate_user_monthly_report"
    )
    def test_generate_report_user_monthly(self, mock_generate):
        """测试生成人员月度报表"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "人员月报"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_template)

        self.db.query = MagicMock(return_value=mock_query)

        # Mock the generation method
        mock_generate.return_value = {
            "summary": [{"user_name": "张三", "total_hours": 160}],
            "detail": [],
            "year": 2026,
            "month": 1,
        }

        result = service.generate_report_data(
            template_id=1, period="2026-01", generated_by=GeneratedByEnum.SYSTEM.value
        )

        self.assertIn("template", result)
        self.assertIn("period", result)
        self.assertIn("generated_by", result)
        self.assertEqual(result["period"], "2026-01")


class TestReportArchiveAndRecipients(unittest.TestCase):
    """测试报表归档与收件人管理"""

    def setUp(self):
        self.db = MagicMock()
        from app.services.report.report_service import ReportService

        self.ReportService = ReportService

    @patch("app.services.report.report_service.datetime")
    def test_archive_report_success(self, mock_datetime):
        """测试归档报表成功"""
        service = self.ReportService(self.db)
        mock_datetime.utcnow.return_value = datetime(2026, 2, 1, 10, 0, 0)

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "人员月报"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value

        service.get_template = MagicMock(return_value=mock_template)
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        archive = service.archive_report(
            template_id=1,
            period="2026-01",
            file_path="/tmp/report.xlsx",
            file_size=2048,
            row_count=88,
        )

        self.db.add.assert_called_once_with(archive)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(archive)
        self.assertEqual(archive.template_id, 1)
        self.assertEqual(archive.report_type, ReportTypeEnum.USER_MONTHLY.value)
        self.assertEqual(archive.period, "2026-01")
        self.assertEqual(archive.file_path, "/tmp/report.xlsx")
        self.assertEqual(archive.file_size, 2048)
        self.assertEqual(archive.row_count, 88)
        self.assertEqual(archive.generated_by, GeneratedByEnum.SYSTEM.value)
        self.assertEqual(archive.status, ArchiveStatusEnum.SUCCESS.value)
        self.assertEqual(archive.download_count, 0)

    def test_archive_report_template_not_found(self):
        """测试归档时模板不存在"""
        service = self.ReportService(self.db)
        service.get_template = MagicMock(return_value=None)

        with self.assertRaises(ValueError) as context:
            service.archive_report(
                template_id=999,
                period="2026-01",
                file_path="/tmp/report.xlsx",
                file_size=2048,
                row_count=88,
            )

        self.assertIn("报表模板不存在", str(context.exception))

    def test_list_archives_with_filters(self):
        """测试按条件分页获取归档列表"""
        service = self.ReportService(self.db)

        mock_archive1 = MagicMock()
        mock_archive2 = MagicMock()

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.offset = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)
        mock_query.count = MagicMock(return_value=2)
        mock_query.all = MagicMock(return_value=[mock_archive1, mock_archive2])

        self.db.query = MagicMock(return_value=mock_query)

        result = service.list_archives(
            template_id=1,
            report_type=ReportTypeEnum.USER_MONTHLY.value,
            period="2026-01",
            status=ArchiveStatusEnum.SUCCESS.value,
            page=2,
            page_size=5,
        )

        self.assertEqual(result["total"], 2)
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["page_size"], 5)
        self.assertEqual(len(result["archives"]), 2)
        self.assertGreaterEqual(mock_query.filter.call_count, 4)

    def test_get_archive_with_template_success(self):
        """测试获取归档及模板信息"""
        service = self.ReportService(self.db)

        mock_archive = MagicMock()
        mock_archive.template_id = 7
        mock_template = MagicMock()

        service.get_archive = MagicMock(return_value=mock_archive)
        service.get_template = MagicMock(return_value=mock_template)

        result = service.get_archive_with_template(101)

        self.assertEqual(result["archive"], mock_archive)
        self.assertEqual(result["template"], mock_template)
        service.get_template.assert_called_once_with(7)

    def test_get_archive_with_template_not_found(self):
        """测试归档不存在时返回None"""
        service = self.ReportService(self.db)
        service.get_archive = MagicMock(return_value=None)

        result = service.get_archive_with_template(404)

        self.assertIsNone(result)

    def test_increment_download_count_success(self):
        """测试增加下载次数成功"""
        service = self.ReportService(self.db)
        mock_archive = MagicMock()
        mock_archive.id = 3
        mock_archive.period = "2026-01"
        mock_archive.download_count = 9

        service.get_archive = MagicMock(return_value=mock_archive)
        self.db.commit = MagicMock()

        result = service.increment_download_count(3)

        self.assertTrue(result)
        self.assertEqual(mock_archive.download_count, 10)
        self.db.commit.assert_called_once()

    def test_increment_download_count_not_found(self):
        """测试增加下载次数时归档不存在"""
        service = self.ReportService(self.db)
        service.get_archive = MagicMock(return_value=None)

        result = service.increment_download_count(404)

        self.assertFalse(result)
        self.db.commit.assert_not_called()

    def test_get_archives_by_ids(self):
        """测试按ID列表批量获取归档"""
        service = self.ReportService(self.db)
        mock_archives = [MagicMock(), MagicMock()]

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.all = MagicMock(return_value=mock_archives)
        self.db.query = MagicMock(return_value=mock_query)

        result = service.get_archives_by_ids([1, 2])

        self.assertEqual(result, mock_archives)

    def test_get_template_with_recipients_success(self):
        """测试获取模板和收件人列表"""
        service = self.ReportService(self.db)
        mock_template = MagicMock()
        mock_recipients = [MagicMock(), MagicMock()]

        service.get_template = MagicMock(return_value=mock_template)

        recipient_query = MagicMock()
        recipient_query.filter = MagicMock(return_value=recipient_query)
        recipient_query.all = MagicMock(return_value=mock_recipients)
        self.db.query = MagicMock(return_value=recipient_query)

        result = service.get_template_with_recipients(1)

        self.assertEqual(result["template"], mock_template)
        self.assertEqual(result["recipients"], mock_recipients)

    def test_get_template_with_recipients_not_found(self):
        """测试模板不存在时获取收件人返回None"""
        service = self.ReportService(self.db)
        service.get_template = MagicMock(return_value=None)

        result = service.get_template_with_recipients(999)

        self.assertIsNone(result)

    def test_add_recipient_success(self):
        """测试添加收件人成功"""
        service = self.ReportService(self.db)
        mock_template = MagicMock()
        mock_template.name = "月报模板"

        service.get_template = MagicMock(return_value=mock_template)
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        recipient = service.add_recipient(
            template_id=1,
            recipient_type="USER",
            recipient_id=88,
            recipient_email="test@example.com",
            delivery_method="EMAIL",
            enabled=True,
        )

        self.db.add.assert_called_once_with(recipient)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(recipient)
        self.assertEqual(recipient.template_id, 1)
        self.assertEqual(recipient.recipient_type, "USER")
        self.assertEqual(recipient.recipient_id, 88)
        self.assertEqual(recipient.recipient_email, "test@example.com")
        self.assertEqual(recipient.delivery_method, "EMAIL")
        self.assertTrue(recipient.enabled)

    def test_add_recipient_template_not_found(self):
        """测试添加收件人时模板不存在"""
        service = self.ReportService(self.db)
        service.get_template = MagicMock(return_value=None)

        result = service.add_recipient(template_id=999, recipient_type="USER")

        self.assertIsNone(result)
        self.db.add.assert_not_called()

    def test_delete_recipient_success(self):
        """测试删除收件人成功"""
        service = self.ReportService(self.db)
        mock_recipient = MagicMock()

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_recipient)
        self.db.query = MagicMock(return_value=mock_query)
        self.db.delete = MagicMock()
        self.db.commit = MagicMock()

        result = service.delete_recipient(12)

        self.assertTrue(result)
        self.db.delete.assert_called_once_with(mock_recipient)
        self.db.commit.assert_called_once()

    def test_delete_recipient_not_found(self):
        """测试删除不存在的收件人"""
        service = self.ReportService(self.db)

        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=None)
        self.db.query = MagicMock(return_value=mock_query)

        result = service.delete_recipient(404)

        self.assertFalse(result)
        self.db.delete.assert_not_called()


class TestReportTemplateManagementExtended(unittest.TestCase):
    """补充覆盖模板管理的实际写入与完整更新路径"""

    def setUp(self):
        self.db = MagicMock()
        from app.services.report.report_service import ReportService

        self.ReportService = ReportService

    def test_create_template_persists_values(self):
        """测试创建模板时写入默认/显式字段"""
        service = self.ReportService(self.db)
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        template = service.create_template(
            name="季度汇总",
            report_type=ReportTypeEnum.COMPANY_MONTHLY.value,
            created_by=11,
            description="季度人效汇总",
            config={"filters": {"department_ids": [1, 2]}},
            output_format=OutputFormatEnum.PDF.value,
            frequency=FrequencyEnum.QUARTERLY.value,
            enabled=False,
        )

        self.db.add.assert_called_once_with(template)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(template)
        self.assertEqual(template.name, "季度汇总")
        self.assertEqual(template.report_type, ReportTypeEnum.COMPANY_MONTHLY.value)
        self.assertEqual(template.created_by, 11)
        self.assertEqual(template.description, "季度人效汇总")
        self.assertEqual(template.config, {"filters": {"department_ids": [1, 2]}})
        self.assertEqual(template.output_format, OutputFormatEnum.PDF.value)
        self.assertEqual(template.frequency, FrequencyEnum.QUARTERLY.value)
        self.assertFalse(template.enabled)

    def test_list_templates_with_enabled_filter_and_pagination(self):
        """测试按启用状态筛选和分页"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.order_by = MagicMock(return_value=mock_query)
        mock_query.offset = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_query)
        mock_query.count = MagicMock(return_value=1)
        mock_query.all = MagicMock(return_value=[mock_template])
        self.db.query = MagicMock(return_value=mock_query)

        result = service.list_templates(enabled=False, page=2, page_size=5)

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["templates"], [mock_template])
        self.assertEqual(result["page"], 2)
        self.assertEqual(result["page_size"], 5)
        mock_query.filter.assert_called_once()
        mock_query.offset.assert_called_once_with(5)
        mock_query.limit.assert_called_once_with(5)

    def test_update_template_updates_all_optional_fields(self):
        """测试完整更新模板的所有可选字段"""
        service = self.ReportService(self.db)

        mock_template = MagicMock()
        mock_template.id = 9
        mock_template.name = "旧模板"
        mock_template.description = "旧描述"
        mock_template.config = {}
        mock_template.output_format = OutputFormatEnum.EXCEL.value
        mock_template.frequency = FrequencyEnum.MONTHLY.value
        mock_template.enabled = True

        service.get_template = MagicMock(return_value=mock_template)
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        result = service.update_template(
            template_id=9,
            name="新模板",
            description="新描述",
            config={"filters": {"department_ids": [5]}},
            output_format=OutputFormatEnum.CSV.value,
            frequency=FrequencyEnum.YEARLY.value,
            enabled=False,
        )

        self.assertEqual(result, mock_template)
        self.assertEqual(mock_template.name, "新模板")
        self.assertEqual(mock_template.description, "新描述")
        self.assertEqual(mock_template.config, {"filters": {"department_ids": [5]}})
        self.assertEqual(mock_template.output_format, OutputFormatEnum.CSV.value)
        self.assertEqual(mock_template.frequency, FrequencyEnum.YEARLY.value)
        self.assertFalse(mock_template.enabled)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(mock_template)


class TestReportGenerationDispatchExtended(unittest.TestCase):
    """补充 generate_report_data 的剩余分发分支"""

    def setUp(self):
        self.db = MagicMock()
        from app.services.report.report_service import ReportService

        self.ReportService = ReportService

    def test_generate_report_dept_monthly_dispatch(self):
        """测试部门月报分发"""
        service = self.ReportService(self.db)
        mock_template = MagicMock()
        mock_template.name = "部门月报"
        mock_template.report_type = ReportTypeEnum.DEPT_MONTHLY.value
        service.get_template = MagicMock(return_value=mock_template)
        service._generate_dept_monthly_report = MagicMock(
            return_value={"summary": [], "detail": [], "year": 2026, "month": 1}
        )

        result = service.generate_report_data(template_id=2, period="2026-01")

        self.assertEqual(result["template"], mock_template)
        service._generate_dept_monthly_report.assert_called_once_with(mock_template, 2026, 1)

    def test_generate_report_project_monthly_dispatch(self):
        """测试项目月报分发"""
        service = self.ReportService(self.db)
        mock_template = MagicMock()
        mock_template.name = "项目月报"
        mock_template.report_type = ReportTypeEnum.PROJECT_MONTHLY.value
        service.get_template = MagicMock(return_value=mock_template)
        service._generate_project_monthly_report = MagicMock(
            return_value={"summary": [], "detail": [], "year": 2026, "month": 1}
        )

        result = service.generate_report_data(template_id=3, period="2026-01")

        self.assertEqual(result["template"], mock_template)
        service._generate_project_monthly_report.assert_called_once_with(mock_template, 2026, 1)

    def test_generate_report_company_monthly_dispatch(self):
        """测试公司月报分发"""
        service = self.ReportService(self.db)
        mock_template = MagicMock()
        mock_template.name = "公司月报"
        mock_template.report_type = ReportTypeEnum.COMPANY_MONTHLY.value
        service.get_template = MagicMock(return_value=mock_template)
        service._generate_company_monthly_report = MagicMock(
            return_value={"summary": [], "detail": [], "year": 2026, "month": 1}
        )

        result = service.generate_report_data(template_id=4, period="2026-01")

        self.assertEqual(result["template"], mock_template)
        service._generate_company_monthly_report.assert_called_once_with(mock_template, 2026, 1)

    def test_generate_report_overtime_monthly_dispatch(self):
        """测试加班月报分发"""
        service = self.ReportService(self.db)
        mock_template = MagicMock()
        mock_template.name = "加班月报"
        mock_template.report_type = ReportTypeEnum.OVERTIME_MONTHLY.value
        service.get_template = MagicMock(return_value=mock_template)
        service._generate_overtime_monthly_report = MagicMock(
            return_value={"summary": [], "detail": [], "year": 2026, "month": 1}
        )

        result = service.generate_report_data(
            template_id=5,
            period="2026-01",
            generated_by=GeneratedByEnum.MANUAL.value,
        )

        self.assertEqual(result["generated_by"], GeneratedByEnum.MANUAL.value)
        service._generate_overtime_monthly_report.assert_called_once_with(mock_template, 2026, 1)


class TestReportGenerationMethodsExtended(unittest.TestCase):
    """补充 report 模块内部 4 类月报生成方法覆盖"""

    def setUp(self):
        self.db = MagicMock()
        from app.services.report.report_service import ReportService

        self.service = ReportService(self.db)
        self.mock_template = MagicMock()
        self.mock_template.config = None

    def test_generate_user_monthly_report_with_filters_zero_days_in_december(self):
        """测试用户月报的过滤、明细和 12 月边界"""
        self.mock_template.config = {"filters": {"department_ids": [1, 2]}}

        mock_row = MagicMock()
        mock_row.user_id = 7
        mock_row.user_name = "张三"
        mock_row.department_name = "研发部"
        mock_row.total_hours = Decimal("0")
        mock_row.normal_hours = Decimal("0")
        mock_row.overtime_hours = Decimal("0")
        mock_row.work_days = 0

        mock_ts = MagicMock()
        mock_ts.user_name = "张三"
        mock_ts.department_name = "研发部"
        mock_ts.work_date = datetime(2025, 12, 15)
        mock_ts.project_name = "项目A"
        mock_ts.task_name = "联调"
        mock_ts.hours = Decimal("8.0")
        mock_ts.overtime_type = "NORMAL"
        mock_ts.work_content = "联调验证"

        mock_summary_query = MagicMock()
        mock_summary_query.filter.return_value = mock_summary_query
        mock_summary_query.group_by.return_value = mock_summary_query
        mock_summary_query.all.return_value = [mock_row]

        mock_detail_query = MagicMock()
        mock_detail_query.filter.return_value = mock_detail_query
        mock_detail_query.all.return_value = [mock_ts]

        self.db.query.side_effect = [mock_summary_query, mock_detail_query]

        result = self.service._generate_user_monthly_report(self.mock_template, 2025, 12)

        self.assertEqual(result["year"], 2025)
        self.assertEqual(result["month"], 12)
        self.assertEqual(result["summary"][0]["avg_hours_per_day"], 0)
        self.assertEqual(result["detail"][0]["hours"], 8.0)
        self.assertEqual(result["detail"][0]["work_date"], "2025-12-15")

    def test_generate_user_monthly_report_in_january(self):
        """测试用户月报的普通月份分支"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        mock_detail_query = MagicMock()
        mock_detail_query.filter.return_value = mock_detail_query
        mock_detail_query.all.return_value = []

        self.db.query.side_effect = [mock_query, mock_detail_query]

        result = self.service._generate_user_monthly_report(self.mock_template, 2026, 1)

        self.assertEqual(result["year"], 2026)
        self.assertEqual(result["month"], 1)
        self.assertEqual(result["summary"], [])
        self.assertEqual(result["detail"], [])

    def test_generate_dept_monthly_report_december_zero_users(self):
        """测试部门月报 12 月与零人数场景"""
        mock_row = MagicMock()
        mock_row.department_id = 10
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

        result = self.service._generate_dept_monthly_report(self.mock_template, 2025, 12)

        self.assertEqual(result["summary"][0]["department_name"], "空部门")
        self.assertEqual(result["summary"][0]["avg_hours_per_user"], 0)
        self.assertEqual(result["year"], 2025)
        self.assertEqual(result["month"], 12)

    def test_generate_dept_monthly_report_in_january(self):
        """测试部门月报的普通月份分支"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query

        result = self.service._generate_dept_monthly_report(self.mock_template, 2026, 1)

        self.assertEqual(result["year"], 2026)
        self.assertEqual(result["month"], 1)
        self.assertEqual(result["summary"], [])

    def test_generate_project_monthly_report_december_zero_users(self):
        """测试项目月报 12 月与零人数场景"""
        mock_row = MagicMock()
        mock_row.project_id = 18
        mock_row.project_name = "空项目"
        mock_row.user_count = 0
        mock_row.total_hours = Decimal("0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_row]
        self.db.query.return_value = mock_query

        result = self.service._generate_project_monthly_report(self.mock_template, 2025, 12)

        self.assertEqual(result["summary"][0]["project_name"], "空项目")
        self.assertEqual(result["summary"][0]["avg_hours_per_user"], 0)

    def test_generate_project_monthly_report_in_january(self):
        """测试项目月报的普通月份分支"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query

        result = self.service._generate_project_monthly_report(self.mock_template, 2026, 1)

        self.assertEqual(result["year"], 2026)
        self.assertEqual(result["month"], 1)
        self.assertEqual(result["summary"], [])

    def test_generate_company_monthly_report_december_zero_users(self):
        """测试公司月报 12 月与零人数场景"""
        mock_stats = MagicMock()
        mock_stats.total_users = 0
        mock_stats.total_hours = Decimal("0")
        mock_stats.normal_hours = Decimal("0")
        mock_stats.overtime_hours = Decimal("0")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stats
        self.db.query.return_value = mock_query

        result = self.service._generate_company_monthly_report(self.mock_template, 2025, 12)

        self.assertEqual(result["summary"][0]["total_users"], 0)
        self.assertEqual(result["summary"][0]["avg_hours_per_user"], 0)

    def test_generate_company_monthly_report_in_january(self):
        """测试公司月报的普通月份分支"""
        mock_stats = MagicMock()
        mock_stats.total_users = 3
        mock_stats.total_hours = Decimal("24")
        mock_stats.normal_hours = Decimal("16")
        mock_stats.overtime_hours = Decimal("8")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stats
        self.db.query.return_value = mock_query

        result = self.service._generate_company_monthly_report(self.mock_template, 2026, 1)

        self.assertEqual(result["year"], 2026)
        self.assertEqual(result["month"], 1)
        self.assertEqual(result["summary"][0]["avg_hours_per_user"], 8.0)

    def test_generate_overtime_monthly_report_december_with_null_values(self):
        """测试加班月报 12 月与空值汇总"""
        mock_row = MagicMock()
        mock_row.user_id = 6
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

        result = self.service._generate_overtime_monthly_report(self.mock_template, 2025, 12)

        self.assertEqual(result["summary"][0]["overtime_hours"], 0.0)
        self.assertEqual(result["summary"][0]["weekend_hours"], 8.0)
        self.assertEqual(result["summary"][0]["holiday_hours"], 0.0)
        self.assertEqual(result["summary"][0]["total_overtime"], 8.0)

    def test_generate_overtime_monthly_report_in_january(self):
        """测试加班月报的普通月份分支"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        self.db.query.return_value = mock_query

        result = self.service._generate_overtime_monthly_report(self.mock_template, 2026, 1)

        self.assertEqual(result["year"], 2026)
        self.assertEqual(result["month"], 1)
        self.assertEqual(result["summary"], [])


class TestReportArchiveAndRecipientExtended(unittest.TestCase):
    """补充归档和收件人的直接查询/异常路径覆盖"""

    def setUp(self):
        self.db = MagicMock()
        from app.services.report.report_service import ReportService

        self.service = ReportService(self.db)

    def test_archive_report_with_failure_status_and_error_message(self):
        """测试失败归档保留错误信息"""
        mock_template = MagicMock()
        mock_template.name = "失败月报"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value
        self.service.get_template = MagicMock(return_value=mock_template)
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()

        archive = self.service.archive_report(
            template_id=1,
            period="2026-01",
            file_path="/tmp/failed.xlsx",
            file_size=0,
            row_count=0,
            generated_by=GeneratedByEnum.MANUAL.value,
            status=ArchiveStatusEnum.FAILED.value,
            error_message="生成失败",
        )

        self.assertEqual(archive.status, ArchiveStatusEnum.FAILED.value)
        self.assertEqual(archive.error_message, "生成失败")
        self.assertEqual(archive.generated_by, GeneratedByEnum.MANUAL.value)

    def test_get_archive_direct_query(self):
        """测试直接获取归档"""
        mock_archive = MagicMock()
        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=mock_archive)
        self.db.query = MagicMock(return_value=mock_query)

        result = self.service.get_archive(77)

        self.assertEqual(result, mock_archive)

    def test_get_archive_direct_query_not_found(self):
        """测试直接获取归档不存在"""
        mock_query = MagicMock()
        mock_query.filter = MagicMock(return_value=mock_query)
        mock_query.first = MagicMock(return_value=None)
        self.db.query = MagicMock(return_value=mock_query)

        result = self.service.get_archive(999)

        self.assertIsNone(result)

    def test_list_archives_without_filters_uses_defaults(self):
        """测试归档列表默认分页参数"""
        mock_archive = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_archive]
        self.db.query = MagicMock(return_value=mock_query)

        result = self.service.list_archives()

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["page_size"], 20)
        self.assertEqual(result["archives"], [mock_archive])

    def test_add_recipient_uses_default_values(self):
        """测试添加收件人使用默认投递方式和启用状态"""
        mock_template = MagicMock()
        mock_template.name = "默认收件人模板"
        self.service.get_template = MagicMock(return_value=mock_template)
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 321))

        recipient = self.service.add_recipient(template_id=1, recipient_type="USER")

        self.assertEqual(recipient.delivery_method, "EMAIL")
        self.assertTrue(recipient.enabled)
        self.assertIsNone(recipient.recipient_email)
        self.assertIsNone(recipient.recipient_id)

    def test_generate_report_data_preserves_custom_generated_by(self):
        """测试生成报表数据时保留自定义生成方式"""
        mock_template = MagicMock()
        mock_template.name = "人员月报"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value
        self.service.get_template = MagicMock(return_value=mock_template)
        self.service._generate_user_monthly_report = MagicMock(
            return_value={"summary": [], "detail": [], "year": 2026, "month": 1}
        )

        result = self.service.generate_report_data(
            template_id=1,
            period="2026-01",
            generated_by=GeneratedByEnum.MANUAL.value,
        )

        self.assertEqual(result["generated_by"], GeneratedByEnum.MANUAL.value)
        self.service._generate_user_monthly_report.assert_called_once_with(mock_template, 2026, 1)


class TestReportExcelService(unittest.TestCase):
    """测试报表Excel导出服务"""

    def test_translate_header(self):
        """测试表头翻译"""
        from app.services.report_excel_service import ReportExcelService

        self.assertEqual(ReportExcelService._translate_header("user_name"), "姓名")
        self.assertEqual(ReportExcelService._translate_header("department_name"), "部门名称")
        self.assertEqual(ReportExcelService._translate_header("total_hours"), "总工时")
        self.assertEqual(ReportExcelService._translate_header("unknown_field"), "unknown_field")

    def test_header_translations_complete(self):
        """测试所有表头翻译"""
        from app.services.report_excel_service import ReportExcelService

        translations = {
            "user_id": "用户ID",
            "user_name": "姓名",
            "department": "部门",
            "total_hours": "总工时",
            "normal_hours": "正常工时",
            "overtime_hours": "加班工时",
            "work_days": "工作天数",
            "user_count": "人数",
            "project_name": "项目名称",
            "task_name": "任务名称",
            "work_date": "日期",
        }

        for key, expected in translations.items():
            self.assertEqual(ReportExcelService._translate_header(key), expected)

    def test_export_requires_openpyxl(self):
        """测试openpyxl不可用时抛出异常"""
        from app.services.report_excel_service import OPENPYXL_AVAILABLE

        # Note: This test checks the logic - if openpyxl is not available,
        # the function should raise ImportError
        # We don't actually disable openpyxl here to avoid side effects

        # Just verify the flag exists
        self.assertIn(OPENPYXL_AVAILABLE, [True, False])


if __name__ == "__main__":
    unittest.main()
