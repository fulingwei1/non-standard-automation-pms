# -*- coding: utf-8 -*-
"""
AlertPdfService 增强测试 - 提升覆盖率到60%+
目标：补充PDF生成、数据格式化、统计表格等核心功能测试
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from app.services import alert_pdf_service
from app.models.alert import AlertRecord, AlertRule
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def mock_alert():
    """创建 Mock 告警记录"""
    def _create_alert(**kwargs):
        alert = MagicMock(spec=AlertRecord)
        alert.id = kwargs.get('id', 1)
        alert.alert_no = kwargs.get('alert_no', 'ALT20240101001')
        alert.alert_level = kwargs.get('alert_level', 'WARNING')
        alert.alert_title = kwargs.get('alert_title', '测试告警')
        alert.status = kwargs.get('status', 'PENDING')
        alert.triggered_at = kwargs.get('triggered_at', datetime(2024, 1, 1, 10, 0, 0))
        alert.project_id = kwargs.get('project_id')
        alert.handler_id = kwargs.get('handler_id')
        alert.acknowledged_by = kwargs.get('acknowledged_by')
        
        # Mock project
        if alert.project_id:
            project = MagicMock()
            project.project_name = kwargs.get('project_name', '测试项目')
            alert.project = project
        else:
            alert.project = None
        
        # Mock rule
        rule = MagicMock(spec=AlertRule)
        rule.rule_type = kwargs.get('rule_type', 'project_delay')
        alert.rule = rule
        
        return alert
    return _create_alert


class TestBuildAlertQuery:
    """测试构建预警查询"""

    def test_build_query_no_filters(self, mock_db):
        """测试无过滤条件"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        result = alert_pdf_service.build_alert_query(mock_db)
        
        mock_db.query.assert_called_once()
        assert result == mock_query

    def test_build_query_with_project_id(self, mock_db):
        """测试项目ID过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        result = alert_pdf_service.build_alert_query(mock_db, project_id=10)
        
        assert mock_query.filter.called

    def test_build_query_with_alert_level(self, mock_db):
        """测试告警级别过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        result = alert_pdf_service.build_alert_query(mock_db, alert_level="CRITICAL")
        
        assert mock_query.filter.called

    def test_build_query_with_status(self, mock_db):
        """测试状态过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        result = alert_pdf_service.build_alert_query(mock_db, status="PENDING")
        
        assert mock_query.filter.called

    def test_build_query_with_rule_type(self, mock_db):
        """测试规则类型过滤（需要JOIN）"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        result = alert_pdf_service.build_alert_query(mock_db, rule_type="project_delay")
        
        assert mock_query.join.called
        assert mock_query.filter.called

    def test_build_query_with_date_range(self, mock_db):
        """测试日期范围过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        result = alert_pdf_service.build_alert_query(
            mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # Should filter twice for start and end date
        assert mock_query.filter.call_count >= 3  # triggered_at.isnot(None) + start + end

    def test_build_query_with_all_filters(self, mock_db):
        """测试所有过滤条件"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        result = alert_pdf_service.build_alert_query(
            mock_db,
            project_id=10,
            alert_level="HIGH",
            status="PENDING",
            rule_type="cost_overrun",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert mock_query.filter.call_count >= 5
        assert mock_query.join.called


class TestCalculateAlertStatistics:
    """测试计算预警统计信息"""

    def test_calculate_statistics_empty_list(self, mock_alert):
        """测试空列表"""
        result = alert_pdf_service.calculate_alert_statistics([])
        
        assert result['total'] == 0
        assert result['by_level'] == {}
        assert result['by_status'] == {}
        assert result['by_type'] == {}

    def test_calculate_statistics_single_alert(self, mock_alert):
        """测试单个告警"""
        alert = mock_alert(alert_level='WARNING', status='PENDING', rule_type='project_delay')
        
        result = alert_pdf_service.calculate_alert_statistics([alert])
        
        assert result['total'] == 1
        assert result['by_level']['WARNING'] == 1
        assert result['by_status']['PENDING'] == 1
        assert result['by_type']['project_delay'] == 1

    def test_calculate_statistics_multiple_alerts(self, mock_alert):
        """测试多个告警"""
        alerts = [
            mock_alert(alert_level='CRITICAL', status='PENDING'),
            mock_alert(alert_level='CRITICAL', status='ACKNOWLEDGED'),
            mock_alert(alert_level='WARNING', status='PENDING'),
            mock_alert(alert_level='WARNING', status='RESOLVED'),
        ]
        
        result = alert_pdf_service.calculate_alert_statistics(alerts)
        
        assert result['total'] == 4
        assert result['by_level']['CRITICAL'] == 2
        assert result['by_level']['WARNING'] == 2
        assert result['by_status']['PENDING'] == 2
        assert result['by_status']['ACKNOWLEDGED'] == 1
        assert result['by_status']['RESOLVED'] == 1

    def test_calculate_statistics_alert_without_rule(self, mock_alert):
        """测试无规则的告警"""
        alert = mock_alert()
        alert.rule = None
        
        result = alert_pdf_service.calculate_alert_statistics([alert])
        
        assert result['by_type']['UNKNOWN'] == 1

    def test_calculate_statistics_mixed_levels(self, mock_alert):
        """测试混合级别"""
        alerts = [
            mock_alert(alert_level='CRITICAL'),
            mock_alert(alert_level='HIGH'),
            mock_alert(alert_level='MEDIUM'),
            mock_alert(alert_level='LOW'),
            mock_alert(alert_level='CRITICAL'),
        ]
        
        result = alert_pdf_service.calculate_alert_statistics(alerts)
        
        assert result['total'] == 5
        assert result['by_level']['CRITICAL'] == 2
        assert result['by_level']['HIGH'] == 1
        assert result['by_level']['MEDIUM'] == 1
        assert result['by_level']['LOW'] == 1


class TestGetPdfStyles:
    """测试获取PDF样式"""

    @patch('app.services.alert_pdf_service.get_pdf_styles')
    def test_get_pdf_styles_from_core(self):
        """测试从核心样式获取"""
        with patch('app.services.pdf_styles.get_pdf_styles') as mock_core_styles:
            mock_core_styles.return_value = {
                "title": "title_style",
                "heading": "heading_style",
                "normal": "normal_style"
            }
            
            result = alert_pdf_service.get_pdf_styles()
            
            assert result[0] == "title_style"
            assert result[1] == "heading_style"
            assert result[2] == "normal_style"

    def test_get_pdf_styles_fallback(self):
        """测试回退到默认样式"""
        with patch('app.services.pdf_styles.get_pdf_styles', side_effect=ImportError):
            with patch('app.services.alert_pdf_service.getSampleStyleSheet') as mock_get_styles:
                mock_styles = MagicMock()
                mock_styles.__getitem__ = MagicMock(side_effect=lambda x: f"style_{x}")
                mock_get_styles.return_value = mock_styles
                
                result = alert_pdf_service.get_pdf_styles()
                
                assert result is not None
                assert len(result) == 4  # title, heading, normal, styles

    def test_get_pdf_styles_missing_reportlab(self):
        """测试缺少reportlab库"""
        with patch('app.services.pdf_styles.get_pdf_styles', side_effect=ImportError):
            with patch('app.services.alert_pdf_service.getSampleStyleSheet', side_effect=ImportError):
                with pytest.raises(ImportError) as exc_info:
                    alert_pdf_service.get_pdf_styles()
                
                assert "reportlab" in str(exc_info.value)


class TestBuildSummaryTable:
    """测试构建统计摘要表格"""

    def test_build_summary_table_basic(self):
        """测试基本摘要表格"""
        statistics = {
            'total': 10,
            'by_level': {'WARNING': 5, 'CRITICAL': 3, 'HIGH': 2},
            'by_status': {'PENDING': 4, 'ACKNOWLEDGED': 3, 'RESOLVED': 3},
            'by_type': {}
        }
        
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                result = alert_pdf_service.build_summary_table(statistics)
                
                mock_table.assert_called_once()
                # Verify table data includes statistics
                call_args = mock_table.call_args[0][0]
                assert any('总预警数' in row for row in call_args if isinstance(row, list))

    def test_build_summary_table_empty_statistics(self):
        """测试空统计"""
        statistics = {
            'total': 0,
            'by_level': {},
            'by_status': {},
            'by_type': {}
        }
        
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                result = alert_pdf_service.build_summary_table(statistics)
                
                mock_table.assert_called_once()

    def test_build_summary_table_missing_reportlab(self):
        """测试缺少reportlab库"""
        with patch('app.services.alert_pdf_service.Table', side_effect=ImportError):
            with pytest.raises(ImportError):
                alert_pdf_service.build_summary_table({'total': 0})


class TestBuildAlertListTables:
    """测试构建预警列表表格"""

    def test_build_alert_list_tables_empty(self, mock_db):
        """测试空列表"""
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                result = alert_pdf_service.build_alert_list_tables(mock_db, [])
                
                assert result == []

    def test_build_alert_list_tables_single_page(self, mock_db, mock_alert):
        """测试单页数据"""
        alerts = [mock_alert(id=i, alert_title=f'告警{i}') for i in range(10)]
        
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                result = alert_pdf_service.build_alert_list_tables(mock_db, alerts, page_size=20)
                
                assert len(result) == 1  # Only one table
                mock_table.assert_called_once()

    def test_build_alert_list_tables_multiple_pages(self, mock_db, mock_alert):
        """测试多页数据"""
        alerts = [mock_alert(id=i) for i in range(50)]
        
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                with patch('app.services.alert_pdf_service.PageBreak'):
                    result = alert_pdf_service.build_alert_list_tables(mock_db, alerts, page_size=20)
                    
                    # Should have multiple tables with page breaks
                    assert len(result) > 1

    def test_build_alert_list_tables_with_handler(self, mock_db, mock_alert):
        """测试有处理人的告警"""
        alert = mock_alert(handler_id=1)
        
        mock_user = MagicMock(spec=User)
        mock_user.username = "test_handler"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                result = alert_pdf_service.build_alert_list_tables(mock_db, [alert])
                
                # Verify handler info is included
                call_args = mock_table.call_args[0][0]
                assert len(call_args) > 1  # Header + data row

    def test_build_alert_list_tables_with_acknowledged_by(self, mock_db, mock_alert):
        """测试有确认人的告警"""
        alert = mock_alert(acknowledged_by=2)
        
        mock_user = MagicMock(spec=User)
        mock_user.username = "test_acknowledger"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                result = alert_pdf_service.build_alert_list_tables(mock_db, [alert])
                
                mock_table.assert_called_once()

    def test_build_alert_list_tables_long_title(self, mock_db, mock_alert):
        """测试长标题截断"""
        long_title = "这是一个非常非常非常非常长的告警标题，应该被截断"
        alert = mock_alert(alert_title=long_title)
        
        with patch('app.services.alert_pdf_service.Table') as mock_table:
            with patch('app.services.alert_pdf_service.TableStyle'):
                result = alert_pdf_service.build_alert_list_tables(mock_db, [alert])
                
                # Verify title is truncated
                call_args = mock_table.call_args[0][0]
                data_row = call_args[1]  # First data row after header
                assert len(data_row[2]) <= 33  # 30 chars + "..."


class TestBuildPdfContent:
    """测试构建PDF内容"""

    @patch('app.services.alert_pdf_service.build_alert_list_tables')
    @patch('app.services.alert_pdf_service.build_summary_table')
    @patch('app.services.alert_pdf_service.calculate_alert_statistics')
    def test_build_pdf_content_basic(self, mock_calc_stats, mock_build_summary,
                                     mock_build_list, mock_db, mock_alert):
        """测试基本PDF内容构建"""
        alerts = [mock_alert()]
        mock_calc_stats.return_value = {'total': 1}
        mock_build_summary.return_value = MagicMock()
        mock_build_list.return_value = [MagicMock()]
        
        title_style = MagicMock()
        heading_style = MagicMock()
        normal_style = MagicMock()
        
        with patch('app.services.alert_pdf_service.Paragraph') as mock_paragraph:
            with patch('app.services.alert_pdf_service.Spacer'):
                result = alert_pdf_service.build_pdf_content(
                    mock_db,
                    alerts,
                    title_style,
                    heading_style,
                    normal_style
                )
                
                assert result is not None
                assert isinstance(result, list)
                # Should include title, summary, and alert list
                mock_paragraph.assert_called()

    @patch('app.services.alert_pdf_service.build_alert_list_tables')
    @patch('app.services.alert_pdf_service.build_summary_table')
    @patch('app.services.alert_pdf_service.calculate_alert_statistics')
    def test_build_pdf_content_empty_alerts(self, mock_calc_stats, mock_build_summary,
                                           mock_build_list, mock_db):
        """测试无告警的PDF内容"""
        mock_calc_stats.return_value = {'total': 0}
        mock_build_summary.return_value = MagicMock()
        mock_build_list.return_value = []
        
        title_style = MagicMock()
        heading_style = MagicMock()
        normal_style = MagicMock()
        
        with patch('app.services.alert_pdf_service.Paragraph'):
            with patch('app.services.alert_pdf_service.Spacer'):
                result = alert_pdf_service.build_pdf_content(
                    mock_db,
                    [],
                    title_style,
                    heading_style,
                    normal_style
                )
                
                assert result is not None

    def test_build_pdf_content_missing_reportlab(self, mock_db, mock_alert):
        """测试缺少reportlab库"""
        with patch('app.services.alert_pdf_service.Paragraph', side_effect=ImportError):
            with pytest.raises(ImportError):
                alert_pdf_service.build_pdf_content(
                    mock_db,
                    [mock_alert()],
                    MagicMock(),
                    MagicMock(),
                    MagicMock()
                )


class TestIntegration:
    """集成测试"""

    def test_full_query_and_statistics_workflow(self, mock_db, mock_alert):
        """测试完整查询和统计流程"""
        # Setup query
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        
        # Setup alerts
        alerts = [
            mock_alert(id=1, alert_level='CRITICAL', status='PENDING'),
            mock_alert(id=2, alert_level='WARNING', status='RESOLVED'),
        ]
        mock_query.all.return_value = alerts
        
        # Build query
        query = alert_pdf_service.build_alert_query(
            mock_db,
            project_id=1,
            alert_level='CRITICAL'
        )
        
        # Calculate statistics
        stats = alert_pdf_service.calculate_alert_statistics(alerts)
        
        assert stats['total'] == 2
        assert stats['by_level']['CRITICAL'] == 1
        assert stats['by_level']['WARNING'] == 1
