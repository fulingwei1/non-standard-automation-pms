# -*- coding: utf-8 -*-
"""
报表服务单元测试 (覆盖率目标: 56%)
使用 unittest.mock.MagicMock 模拟数据库会话
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.report.report_service import ReportService
from app.models.report import (
    ReportTypeEnum,
    OutputFormatEnum,
    FrequencyEnum,
    GeneratedByEnum,
    ArchiveStatusEnum,
)


class TestReportService(unittest.TestCase):
    """报表服务测试类"""
    
    def setUp(self):
        """每个测试前的初始化"""
        self.mock_db = MagicMock()
        self.service = ReportService(self.mock_db)
    
    def tearDown(self):
        """每个测试后的清理"""
        self.mock_db.reset_mock()
    
    # ==================== 模板管理测试 ====================
    
    def test_create_template_success(self):
        """测试创建报表模板成功"""
        # Arrange
        template_name = "月度工时报表"
        report_type = ReportTypeEnum.USER_MONTHLY.value
        created_by = 1
        
        # Mock database operations
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = template_name
        mock_template.report_type = report_type
        
        self.mock_db.add = MagicMock()
        self.mock_db.commit = MagicMock()
        self.mock_db.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))
        
        # Act
        with patch('app.services.report.report_service.ReportTemplate', return_value=mock_template):
            result = self.service.create_template(
                name=template_name,
                report_type=report_type,
                created_by=created_by,
            )
        
        # Assert
        self.assertEqual(result.name, template_name)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_list_templates_with_filters(self):
        """测试获取报表模板列表（带筛选条件）"""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        mock_template1 = MagicMock()
        mock_template1.id = 1
        mock_template1.name = "模板1"
        
        mock_template2 = MagicMock()
        mock_template2.id = 2
        mock_template2.name = "模板2"
        
        mock_query.all.return_value = [mock_template1, mock_template2]
        
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.service.list_templates(
            report_type=ReportTypeEnum.USER_MONTHLY.value,
            enabled=True,
            page=1,
            page_size=20,
        )
        
        # Assert
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['templates']), 2)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['page_size'], 20)
    
    def test_get_template_exists(self):
        """测试获取存在的报表模板"""
        # Arrange
        template_id = 1
        mock_template = MagicMock()
        mock_template.id = template_id
        mock_template.name = "测试模板"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_template
        
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.service.get_template(template_id)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, template_id)
    
    def test_get_template_not_exists(self):
        """测试获取不存在的报表模板"""
        # Arrange
        template_id = 999
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.service.get_template(template_id)
        
        # Assert
        self.assertIsNone(result)
    
    def test_update_template_success(self):
        """测试更新报表模板成功"""
        # Arrange
        template_id = 1
        new_name = "更新后的模板"
        
        mock_template = MagicMock()
        mock_template.id = template_id
        mock_template.name = "原模板"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_template
        
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit = MagicMock()
        self.mock_db.refresh = MagicMock()
        
        # Act
        result = self.service.update_template(
            template_id=template_id,
            name=new_name,
        )
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.name, new_name)
        self.mock_db.commit.assert_called_once()
    
    def test_delete_template_success(self):
        """测试删除报表模板成功"""
        # Arrange
        template_id = 1
        mock_template = MagicMock()
        mock_template.id = template_id
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_template
        
        self.mock_db.query.return_value = mock_query
        self.mock_db.delete = MagicMock()
        self.mock_db.commit = MagicMock()
        
        # Act
        result = self.service.delete_template(template_id)
        
        # Assert
        self.assertTrue(result)
        self.mock_db.delete.assert_called_once_with(mock_template)
        self.mock_db.commit.assert_called_once()
    
    def test_toggle_template_enable_to_disable(self):
        """测试切换模板状态（启用→禁用）"""
        # Arrange
        template_id = 1
        mock_template = MagicMock()
        mock_template.id = template_id
        mock_template.enabled = True
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_template
        
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit = MagicMock()
        self.mock_db.refresh = MagicMock()
        
        # Act
        result = self.service.toggle_template(template_id)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertFalse(result['enabled'])
        self.assertFalse(result['template'].enabled)
    
    # ==================== 报表归档测试 ====================
    
    def test_archive_report_success(self):
        """测试归档报表成功"""
        # Arrange
        template_id = 1
        period = "2026-01"
        file_path = "/path/to/report.xlsx"
        file_size = 1024
        row_count = 100
        
        mock_template = MagicMock()
        mock_template.id = template_id
        mock_template.name = "测试模板"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value
        
        mock_archive = MagicMock()
        mock_archive.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_template
        
        self.mock_db.query.return_value = mock_query
        self.mock_db.add = MagicMock()
        self.mock_db.commit = MagicMock()
        self.mock_db.refresh = MagicMock()
        
        # Act
        with patch('app.services.report.report_service.ReportArchive', return_value=mock_archive):
            result = self.service.archive_report(
                template_id=template_id,
                period=period,
                file_path=file_path,
                file_size=file_size,
                row_count=row_count,
            )
        
        # Assert
        self.assertIsNotNone(result)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_list_archives_with_pagination(self):
        """测试获取报表归档列表（分页）"""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        mock_archive1 = MagicMock()
        mock_archive1.id = 1
        
        mock_archive2 = MagicMock()
        mock_archive2.id = 2
        
        mock_query.all.return_value = [mock_archive1, mock_archive2]
        
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.service.list_archives(
            template_id=1,
            page=1,
            page_size=2,
        )
        
        # Assert
        self.assertEqual(result['total'], 3)
        self.assertEqual(len(result['archives']), 2)
    
    def test_increment_download_count_success(self):
        """测试增加下载次数成功"""
        # Arrange
        archive_id = 1
        mock_archive = MagicMock()
        mock_archive.id = archive_id
        mock_archive.download_count = 5
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_archive
        
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit = MagicMock()
        
        # Act
        result = self.service.increment_download_count(archive_id)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_archive.download_count, 6)
        self.mock_db.commit.assert_called_once()
    
    # ==================== 收件人管理测试 ====================
    
    def test_add_recipient_success(self):
        """测试添加收件人成功"""
        # Arrange
        template_id = 1
        recipient_type = "USER"
        recipient_email = "test@example.com"
        
        mock_template = MagicMock()
        mock_template.id = template_id
        mock_template.name = "测试模板"
        
        mock_recipient = MagicMock()
        mock_recipient.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_template
        
        self.mock_db.query.return_value = mock_query
        self.mock_db.add = MagicMock()
        self.mock_db.commit = MagicMock()
        self.mock_db.refresh = MagicMock()
        
        # Act
        with patch('app.services.report.report_service.ReportRecipient', return_value=mock_recipient):
            result = self.service.add_recipient(
                template_id=template_id,
                recipient_type=recipient_type,
                recipient_email=recipient_email,
            )
        
        # Assert
        self.assertIsNotNone(result)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_delete_recipient_success(self):
        """测试删除收件人成功"""
        # Arrange
        recipient_id = 1
        mock_recipient = MagicMock()
        mock_recipient.id = recipient_id
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_recipient
        
        self.mock_db.query.return_value = mock_query
        self.mock_db.delete = MagicMock()
        self.mock_db.commit = MagicMock()
        
        # Act
        result = self.service.delete_recipient(recipient_id)
        
        # Assert
        self.assertTrue(result)
        self.mock_db.delete.assert_called_once_with(mock_recipient)
        self.mock_db.commit.assert_called_once()
    
    # ==================== 报表生成测试 ====================
    
    def test_generate_report_data_user_monthly(self):
        """测试生成人员月度报表数据"""
        # Arrange
        template_id = 1
        period = "2026-01"
        
        mock_template = MagicMock()
        mock_template.id = template_id
        mock_template.name = "人员月度工时报表"
        mock_template.report_type = ReportTypeEnum.USER_MONTHLY.value
        mock_template.config = {}
        
        # Mock query results
        mock_summary_row = MagicMock()
        mock_summary_row.user_id = 1
        mock_summary_row.user_name = "张三"
        mock_summary_row.department_name = "技术部"
        mock_summary_row.total_hours = 160.0
        mock_summary_row.normal_hours = 150.0
        mock_summary_row.overtime_hours = 10.0
        mock_summary_row.work_days = 20
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_template
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [mock_summary_row]
        
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.service.generate_report_data(
            template_id=template_id,
            period=period,
        )
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result['period'], period)
        self.assertEqual(result['template'].id, template_id)
        self.assertIn('summary', result)
        self.assertIn('detail', result)
    
    def test_generate_report_data_template_not_found(self):
        """测试生成报表数据时模板不存在"""
        # Arrange
        template_id = 999
        period = "2026-01"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        self.mock_db.query.return_value = mock_query
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.generate_report_data(
                template_id=template_id,
                period=period,
            )
        
        self.assertIn("报表模板不存在", str(context.exception))


if __name__ == '__main__':
    unittest.main()
