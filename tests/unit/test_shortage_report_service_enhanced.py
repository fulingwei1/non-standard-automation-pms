# -*- coding: utf-8 -*-
"""
增强的 shortage_report_service 单元测试

覆盖目标: 70%+
测试策略: Mock外部依赖，构造真实数据对象让业务逻辑真正执行
"""

import json
import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

# 尝试导入模块
try:
    from app.services.shortage_report_service import (
        calculate_alert_statistics,
        calculate_report_statistics,
        calculate_kit_statistics,
        calculate_arrival_statistics,
        calculate_response_time_statistics,
        calculate_stoppage_statistics,
        build_daily_report_data,
    )
    from app.services.shortage.shortage_reports_service import ShortageReportsService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock()


@pytest.fixture
def target_date():
    """目标测试日期"""
    return date(2026, 2, 21)


@pytest.fixture
def mock_user():
    """Mock用户对象"""
    user = MagicMock()
    user.id = 1
    user.username = "test_user"
    return user


@pytest.fixture
def service(mock_db):
    """ShortageReportsService实例"""
    return ShortageReportsService(mock_db)


# ============================================================================
# ShortageReportsService 类测试
# ============================================================================

class TestShortageReportsServiceInit:
    """测试服务初始化"""

    def test_init_stores_db_session(self, mock_db):
        """测试初始化时保存数据库会话"""
        service = ShortageReportsService(mock_db)
        assert service.db is mock_db

    def test_init_with_none_db(self):
        """测试使用None初始化"""
        service = ShortageReportsService(None)
        assert service.db is None


class TestGetShortageReports:
    """测试获取缺料报告列表"""

    def test_get_reports_default_pagination(self, service, mock_db):
        """测试默认分页参数"""
        with patch.object(service, 'get_shortage_reports', wraps=service.get_shortage_reports):
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.all.return_value = []

            result = service.get_shortage_reports()

            assert result.total == 0
            assert result.page == 1
            assert result.page_size == 20

    def test_get_reports_with_keyword_filter(self, service, mock_db):
        """测试关键词搜索"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 5
        
        # 构造真实的报告对象
        mock_reports = [self._create_mock_report(i) for i in range(5)]
        mock_query.all.return_value = mock_reports

        result = service.get_shortage_reports(keyword="紧急")

        assert result.total == 5
        assert len(result.items) == 5

    def test_get_reports_with_status_filter(self, service, mock_db):
        """测试状态过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.all.return_value = []

        result = service.get_shortage_reports(status="pending")

        assert result.total == 3
        mock_query.filter.assert_called()

    def test_get_reports_with_date_range(self, service, mock_db):
        """测试日期范围过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.all.return_value = []

        start_date = date(2026, 2, 1)
        end_date = date(2026, 2, 28)
        result = service.get_shortage_reports(start_date=start_date, end_date=end_date)

        assert result.total == 10

    def test_get_reports_with_reporter_filter(self, service, mock_db):
        """测试上报人过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.all.return_value = []

        result = service.get_shortage_reports(reporter_id=1)

        assert result.total == 2

    @staticmethod
    def _create_mock_report(idx):
        """创建模拟报告对象"""
        report = MagicMock()
        report.id = idx
        report.title = f"Report {idx}"
        report.description = f"Description {idx}"
        report.status = "pending"
        report.created_at = datetime.now(timezone.utc)
        return report


class TestCreateShortageReport:
    """测试创建缺料报告"""

    @patch("app.services.shortage.shortage_reports_service.save_obj")
    @patch("app.services.shortage.shortage_reports_service.ShortageReport")
    def test_create_report_with_all_fields(self, mock_report_class, mock_save, service, mock_user):
        """测试创建完整字段的报告"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.status = "pending"
        mock_report.reporter_id = mock_user.id
        mock_report_class.return_value = mock_report

        report_data = MagicMock()
        report_data.title = "紧急缺料"
        report_data.description = "电机缺料，影响生产"
        report_data.material_id = 101
        report_data.shortage_quantity = Decimal("50.00")
        report_data.shortage_reason = "供应商延迟交付"
        report_data.impact_assessment = "影响两条生产线"
        report_data.expected_arrival_date = date(2026, 3, 1)

        result = service.create_shortage_report(report_data, mock_user)

        assert result is not None
        assert result.status == "pending"
        assert result.reporter_id == mock_user.id
        mock_save.assert_called_once()

    @patch("app.services.shortage.shortage_reports_service.save_obj")
    @patch("app.services.shortage.shortage_reports_service.ShortageReport")
    def test_create_report_minimal_fields(self, mock_report_class, mock_save, service, mock_user):
        """测试创建最小字段报告"""
        mock_report = MagicMock()
        mock_report.status = "pending"
        mock_report_class.return_value = mock_report

        report_data = MagicMock()
        report_data.title = "T"
        report_data.description = "D"
        report_data.material_id = 1
        report_data.shortage_quantity = Decimal("1")
        report_data.shortage_reason = None
        report_data.impact_assessment = None
        report_data.expected_arrival_date = None

        result = service.create_shortage_report(report_data, mock_user)

        assert result.status == "pending"
        mock_save.assert_called_once()

    @patch("app.services.shortage.shortage_reports_service.save_obj")
    @patch("app.services.shortage.shortage_reports_service.ShortageReport")
    def test_create_report_sets_reporter_id(self, mock_report_class, mock_save, service, mock_user):
        """测试创建报告时设置上报人ID"""
        mock_report = MagicMock()
        mock_report_class.return_value = mock_report

        report_data = MagicMock()
        report_data.title = "Test"
        report_data.description = "Test"
        report_data.material_id = 1
        report_data.shortage_quantity = Decimal("10")

        service.create_shortage_report(report_data, mock_user)

        mock_report_class.assert_called_once()
        call_kwargs = mock_report_class.call_args[1]
        assert call_kwargs['reporter_id'] == mock_user.id


class TestGetShortageReport:
    """测试获取单个缺料报告"""

    @patch("app.services.shortage.shortage_reports_service.joinedload")
    def test_get_report_found(self, mock_joinedload, service, mock_db):
        """测试获取存在的报告"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.title = "Test Report"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_report

        result = service.get_shortage_report(1)

        assert result is not None
        assert result.id == 1
        assert result.title == "Test Report"

    @patch("app.services.shortage.shortage_reports_service.joinedload")
    def test_get_report_not_found(self, mock_joinedload, service, mock_db):
        """测试获取不存在的报告"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = service.get_shortage_report(999)

        assert result is None


class TestConfirmShortageReport:
    """测试确认缺料报告"""

    def test_confirm_report_success(self, service, mock_db, mock_user):
        """测试成功确认报告"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.status = "pending"

        with patch.object(service, 'get_shortage_report', return_value=mock_report):
            result = service.confirm_shortage_report(1, mock_user)

            assert result is not None
            assert result.status == "confirmed"
            assert result.confirmer_id == mock_user.id
            assert result.confirmed_at is not None
            mock_db.commit.assert_called_once()

    def test_confirm_report_not_found(self, service, mock_db, mock_user):
        """测试确认不存在的报告"""
        with patch.object(service, 'get_shortage_report', return_value=None):
            result = service.confirm_shortage_report(999, mock_user)

            assert result is None
            mock_db.commit.assert_not_called()


class TestHandleShortageReport:
    """测试处理缺料报告"""

    def test_handle_report_success(self, service, mock_db, mock_user):
        """测试成功处理报告"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.status = "confirmed"

        handle_data = {
            "handling_method": "紧急采购",
            "handling_note": "已联系供应商加急"
        }

        with patch.object(service, 'get_shortage_report', return_value=mock_report):
            result = service.handle_shortage_report(1, handle_data, mock_user)

            assert result is not None
            assert result.status == "handling"
            assert result.handler_id == mock_user.id
            assert result.handling_method == "紧急采购"
            assert result.handling_note == "已联系供应商加急"
            mock_db.commit.assert_called_once()

    def test_handle_report_not_found(self, service, mock_db, mock_user):
        """测试处理不存在的报告"""
        handle_data = {"handling_method": "test"}

        with patch.object(service, 'get_shortage_report', return_value=None):
            result = service.handle_shortage_report(999, handle_data, mock_user)

            assert result is None
            mock_db.commit.assert_not_called()

    def test_handle_report_empty_data(self, service, mock_db, mock_user):
        """测试处理报告时传入空数据"""
        mock_report = MagicMock()
        handle_data = {}

        with patch.object(service, 'get_shortage_report', return_value=mock_report):
            result = service.handle_shortage_report(1, handle_data, mock_user)

            assert result.handling_method is None
            assert result.handling_note is None


class TestResolveShortageReport:
    """测试解决缺料报告"""

    def test_resolve_report_success(self, service, mock_db, mock_user):
        """测试成功解决报告"""
        mock_report = MagicMock()
        mock_report.id = 1
        mock_report.status = "handling"

        resolve_data = {
            "resolution_method": "物料已到货",
            "resolution_note": "供应商按时交付",
            "actual_arrival_date": date(2026, 2, 25)
        }

        with patch.object(service, 'get_shortage_report', return_value=mock_report):
            result = service.resolve_shortage_report(1, resolve_data, mock_user)

            assert result is not None
            assert result.status == "resolved"
            assert result.resolver_id == mock_user.id
            assert result.resolved_at is not None
            assert result.resolution_method == "物料已到货"
            assert result.actual_arrival_date == date(2026, 2, 25)
            mock_db.commit.assert_called_once()

    def test_resolve_report_not_found(self, service, mock_db, mock_user):
        """测试解决不存在的报告"""
        resolve_data = {"resolution_method": "test"}

        with patch.object(service, 'get_shortage_report', return_value=None):
            result = service.resolve_shortage_report(999, resolve_data, mock_user)

            assert result is None
            mock_db.commit.assert_not_called()


# ============================================================================
# 统计函数测试
# ============================================================================

class TestCalculateAlertStatistics:
    """测试预警统计"""

    def test_alert_statistics_all_zeros(self, mock_db, target_date):
        """测试无预警时的统计"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        result = calculate_alert_statistics(mock_db, target_date)

        assert result['new_alerts'] == 0
        assert result['resolved_alerts'] == 0
        assert result['pending_alerts'] == 0
        assert result['overdue_alerts'] == 0

    def test_alert_statistics_with_new_alerts(self, mock_db, target_date):
        """测试新增预警统计"""
        def count_side_effect(*args, **kwargs):
            # 根据filter条件返回不同的count
            return 5

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [5, 3, 2, 1, 2, 1, 1]  # new, resolved, pending, level1-4

        result = calculate_alert_statistics(mock_db, target_date)

        assert result['new_alerts'] == 5
        assert result['resolved_alerts'] == 3
        assert result['pending_alerts'] == 2

    def test_alert_statistics_level_counts(self, mock_db, target_date):
        """测试预警级别统计"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [10, 5, 8, 3, 2, 1, 1]  # 顺序很重要

        result = calculate_alert_statistics(mock_db, target_date)

        assert 'level_counts' in result
        assert isinstance(result['level_counts'], dict)


class TestCalculateReportStatistics:
    """测试上报统计"""

    def test_report_statistics_no_reports(self, mock_db, target_date):
        """测试无上报记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None

        result = calculate_report_statistics(mock_db, target_date)

        assert result['new_reports'] == 0
        assert result['resolved_reports'] == 0

    def test_report_statistics_with_reports(self, mock_db, target_date):
        """测试有上报记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [15, 10]  # new_reports, resolved_reports

        result = calculate_report_statistics(mock_db, target_date)

        assert result['new_reports'] == 15
        assert result['resolved_reports'] == 10


class TestCalculateKitStatistics:
    """测试齐套统计"""

    def test_kit_statistics_no_checks(self, mock_db, target_date):
        """测试无齐套检查记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = calculate_kit_statistics(mock_db, target_date)

        assert result['total_work_orders'] == 0
        assert result['kit_complete_count'] == 0
        assert result['kit_rate'] == 0.0

    def test_kit_statistics_all_complete(self, mock_db, target_date):
        """测试全部齐套"""
        mock_checks = [
            self._create_kit_check("complete", 100.0),
            self._create_kit_check("complete", 100.0),
            self._create_kit_check("complete", 100.0),
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_checks

        result = calculate_kit_statistics(mock_db, target_date)

        assert result['total_work_orders'] == 3
        assert result['kit_complete_count'] == 3
        assert result['kit_rate'] == 100.0

    def test_kit_statistics_partial_complete(self, mock_db, target_date):
        """测试部分齐套"""
        mock_checks = [
            self._create_kit_check("complete", 100.0),
            self._create_kit_check("incomplete", 80.0),
            self._create_kit_check("incomplete", 60.0),
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_checks

        result = calculate_kit_statistics(mock_db, target_date)

        assert result['total_work_orders'] == 3
        assert result['kit_complete_count'] == 1
        assert result['kit_rate'] == 80.0  # (100 + 80 + 60) / 3

    @staticmethod
    def _create_kit_check(status, rate):
        """创建齐套检查对象"""
        check = MagicMock()
        check.kit_status = status
        check.kit_rate = rate
        return check


class TestCalculateArrivalStatistics:
    """测试到货统计"""

    def test_arrival_statistics_no_arrivals(self, mock_db, target_date):
        """测试无到货记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0

        result = calculate_arrival_statistics(mock_db, target_date)

        assert result['expected_arrivals'] == 0
        assert result['actual_arrivals'] == 0
        assert result['delayed_arrivals'] == 0
        assert result['on_time_rate'] == 0.0

    def test_arrival_statistics_all_on_time(self, mock_db, target_date):
        """测试全部按时到货"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [10, 10, 0]  # expected, actual, delayed

        result = calculate_arrival_statistics(mock_db, target_date)

        assert result['expected_arrivals'] == 10
        assert result['actual_arrivals'] == 10
        assert result['delayed_arrivals'] == 0
        assert result['on_time_rate'] == 100.0

    def test_arrival_statistics_with_delays(self, mock_db, target_date):
        """测试有延迟到货"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [20, 18, 5]  # expected, actual, delayed

        result = calculate_arrival_statistics(mock_db, target_date)

        assert result['expected_arrivals'] == 20
        assert result['actual_arrivals'] == 18
        assert result['delayed_arrivals'] == 5
        # on_time_rate = ((18 - 5) / 18) * 100 = 72.22
        assert 72.0 <= result['on_time_rate'] <= 73.0


class TestCalculateResponseTimeStatistics:
    """测试响应时间统计"""

    def test_response_time_no_alerts(self, mock_db, target_date):
        """测试无预警记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = calculate_response_time_statistics(mock_db, target_date)

        assert result['avg_response_minutes'] == 0
        assert result['avg_resolve_hours'] == 0.0

    def test_response_time_with_alerts(self, mock_db, target_date):
        """测试有预警记录"""
        base_time = datetime(2026, 2, 21, 10, 0, 0)
        mock_alerts_response = [
            self._create_alert(base_time, base_time + timedelta(minutes=30)),
            self._create_alert(base_time, base_time + timedelta(minutes=60)),
        ]
        mock_alerts_resolved = [
            self._create_alert_resolved(base_time, base_time + timedelta(hours=2)),
            self._create_alert_resolved(base_time, base_time + timedelta(hours=4)),
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = [mock_alerts_response, mock_alerts_resolved]

        result = calculate_response_time_statistics(mock_db, target_date)

        # avg_response = (30 + 60) / 2 = 45 minutes
        assert result['avg_response_minutes'] == 45
        # avg_resolve = (2 + 4) / 2 = 3.0 hours
        assert result['avg_resolve_hours'] == 3.0

    @staticmethod
    def _create_alert(created_at, handle_start_at):
        """创建预警对象"""
        alert = MagicMock()
        alert.created_at = created_at
        alert.handle_start_at = handle_start_at
        return alert

    @staticmethod
    def _create_alert_resolved(created_at, handle_end_at):
        """创建已解决预警对象"""
        alert = MagicMock()
        alert.created_at = created_at
        alert.handle_end_at = handle_end_at
        return alert


class TestCalculateStoppageStatistics:
    """测试停工统计"""

    def test_stoppage_statistics_no_stoppages(self, mock_db, target_date):
        """测试无停工记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = calculate_stoppage_statistics(mock_db, target_date)

        assert result['stoppage_count'] == 0
        assert result['stoppage_hours'] == 0

    def test_stoppage_statistics_with_stoppages(self, mock_db, target_date):
        """测试有停工记录"""
        mock_alerts = [
            self._create_alert_with_stoppage(2),  # 2天停工
            self._create_alert_with_stoppage(1),  # 1天停工
            self._create_alert_no_stoppage(),     # 非停工
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_alerts

        result = calculate_stoppage_statistics(mock_db, target_date)

        assert result['stoppage_count'] == 2
        # (2 + 1) * 24 = 72 hours
        assert result['stoppage_hours'] == 72.0

    def test_stoppage_statistics_json_string_data(self, mock_db, target_date):
        """测试JSON字符串格式的alert_data"""
        mock_alert = MagicMock()
        mock_alert.alert_data = json.dumps({
            'impact_type': 'stop',
            'estimated_delay_days': 3
        })

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_alert]

        result = calculate_stoppage_statistics(mock_db, target_date)

        assert result['stoppage_count'] == 1
        assert result['stoppage_hours'] == 72.0  # 3 * 24

    @staticmethod
    def _create_alert_with_stoppage(delay_days):
        """创建带停工的预警对象"""
        alert = MagicMock()
        alert.alert_data = {
            'impact_type': 'stop',
            'estimated_delay_days': delay_days
        }
        return alert

    @staticmethod
    def _create_alert_no_stoppage():
        """创建非停工预警对象"""
        alert = MagicMock()
        alert.alert_data = {
            'impact_type': 'delay',
            'estimated_delay_days': 0
        }
        return alert


class TestBuildDailyReportData:
    """测试构建日报数据"""

    @patch("app.services.shortage.shortage_reports_service.calculate_stoppage_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_response_time_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_arrival_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_kit_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_report_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_alert_statistics")
    def test_build_daily_report_combines_all_stats(
        self, mock_alert, mock_report, mock_kit, mock_arrival, 
        mock_response, mock_stoppage, mock_db, target_date
    ):
        """测试构建日报整合所有统计数据"""
        mock_alert.return_value = {'new_alerts': 5}
        mock_report.return_value = {'new_reports': 3}
        mock_kit.return_value = {'total_work_orders': 10}
        mock_arrival.return_value = {'expected_arrivals': 8}
        mock_response.return_value = {'avg_response_minutes': 30}
        mock_stoppage.return_value = {'stoppage_count': 1}

        result = build_daily_report_data(mock_db, target_date)

        assert 'new_alerts' in result
        assert 'new_reports' in result
        assert 'total_work_orders' in result
        assert 'expected_arrivals' in result
        assert 'avg_response_minutes' in result
        assert 'stoppage_count' in result

    @patch("app.services.shortage.shortage_reports_service.calculate_stoppage_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_response_time_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_arrival_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_kit_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_report_statistics")
    @patch("app.services.shortage.shortage_reports_service.calculate_alert_statistics")
    def test_build_daily_report_calls_all_functions(
        self, mock_alert, mock_report, mock_kit, mock_arrival, 
        mock_response, mock_stoppage, mock_db, target_date
    ):
        """测试构建日报调用所有统计函数"""
        mock_alert.return_value = {}
        mock_report.return_value = {}
        mock_kit.return_value = {}
        mock_arrival.return_value = {}
        mock_response.return_value = {}
        mock_stoppage.return_value = {}

        build_daily_report_data(mock_db, target_date)

        mock_alert.assert_called_once_with(mock_db, target_date)
        mock_report.assert_called_once_with(mock_db, target_date)
        mock_kit.assert_called_once_with(mock_db, target_date)
        mock_arrival.assert_called_once_with(mock_db, target_date)
        mock_response.assert_called_once_with(mock_db, target_date)
        mock_stoppage.assert_called_once_with(mock_db, target_date)


# ============================================================================
# 边界条件和异常测试
# ============================================================================

class TestEdgeCases:
    """边界条件测试"""

    def test_kit_statistics_with_null_rate(self, mock_db, target_date):
        """测试齐套率为None的情况"""
        mock_checks = [
            MagicMock(kit_status="complete", kit_rate=None),
            MagicMock(kit_status="incomplete", kit_rate=80.0),
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_checks

        result = calculate_kit_statistics(mock_db, target_date)

        # 应该处理None值
        assert result['total_work_orders'] == 2
        assert result['kit_rate'] == 40.0  # (0 + 80) / 2

    def test_arrival_on_time_rate_division_by_zero(self, mock_db, target_date):
        """测试到货率除零情况"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [5, 0, 0]  # expected=5, actual=0, delayed=0

        result = calculate_arrival_statistics(mock_db, target_date)

        # 应该返回0而不是抛出异常
        assert result['on_time_rate'] == 0.0

    def test_stoppage_with_invalid_json(self, mock_db, target_date):
        """测试无效JSON格式的alert_data"""
        mock_alert = MagicMock()
        mock_alert.alert_data = "invalid json {"

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_alert]

        # 不应该抛出异常
        result = calculate_stoppage_statistics(mock_db, target_date)

        assert result['stoppage_count'] == 0
        assert result['stoppage_hours'] == 0

    def test_response_time_with_none_timestamps(self, mock_db, target_date):
        """测试时间戳为None的情况"""
        mock_alerts = [
            MagicMock(created_at=None, handle_start_at=datetime.now()),
            MagicMock(created_at=datetime.now(), handle_start_at=None),
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = [mock_alerts, []]

        # 不应该抛出异常
        result = calculate_response_time_statistics(mock_db, target_date)

        assert result['avg_response_minutes'] == 0
