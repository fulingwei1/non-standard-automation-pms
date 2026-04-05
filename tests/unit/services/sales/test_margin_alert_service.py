# -*- coding: utf-8 -*-
"""
margin_alert_service 单元测试

测试毛利率预警服务的核心功能。
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models.sales import (
    MarginAlertConfig,
    MarginAlertLevelEnum,
    MarginAlertRecord,
    MarginAlertStatusEnum,
    Quote,
    QuoteVersion,
)
from app.services.sales.margin_alert_service import MarginAlertService


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return MarginAlertService(mock_db)


@pytest.fixture
def sample_config():
    """示例配置"""
    config = MagicMock(spec=MarginAlertConfig)
    config.id = 1
    config.name = "默认配置"
    config.code = "DEFAULT"
    config.standard_margin = Decimal("25.00")
    config.warning_margin = Decimal("20.00")
    config.alert_margin = Decimal("15.00")
    config.minimum_margin = Decimal("10.00")
    config.is_active = True
    config.is_default = True
    return config


@pytest.fixture
def sample_quote():
    """示例报价"""
    quote = MagicMock(spec=Quote)
    quote.id = 1
    quote.opportunity_id = 10
    quote.customer_id = 100
    quote.customer = MagicMock()
    quote.customer.level = "A"
    return quote


@pytest.fixture
def sample_quote_version():
    """示例报价版本"""
    version = MagicMock(spec=QuoteVersion)
    version.id = 1
    version.total_price = Decimal("100000.00")
    version.cost_total = Decimal("80000.00")  # 20% 毛利率
    return version


# ========== 配置管理测试 ==========

class TestGetApplicableConfig:
    """get_applicable_config 测试"""

    def test_exact_match(self, service, mock_db, sample_config):
        """精确匹配"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = sample_config

        result = service.get_applicable_config(
            customer_level="A",
            project_type="IT",
            industry="金融"
        )

        assert result == sample_config

    def test_customer_level_match(self, service, mock_db, sample_config):
        """客户等级匹配"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        # 精确匹配返回 None，客户等级匹配返回配置
        mock_query.first.side_effect = [None, sample_config]

        result = service.get_applicable_config(customer_level="A")

        assert result == sample_config

    def test_default_config(self, service, mock_db, sample_config):
        """返回默认配置"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # 无参数时直接查询默认配置（只有一次数据库调用）
        mock_query.first.return_value = sample_config

        result = service.get_applicable_config()

        assert result == sample_config

    def test_no_config_found(self, service, mock_db):
        """无配置"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = service.get_applicable_config()

        assert result is None


class TestCreateConfig:
    """create_config 测试"""

    def test_create_basic_config(self, service, mock_db):
        """创建基础配置"""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_config(
            name="测试配置",
            code="TEST001",
            created_by=1,
            standard_margin=25.0,
            warning_margin=20.0,
            alert_margin=15.0,
            minimum_margin=10.0,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_config_with_customer_level(self, service, mock_db):
        """创建带客户等级的配置"""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service.create_config(
            name="A级客户配置",
            code="LEVEL_A",
            created_by=1,
            customer_level="A",
            standard_margin=20.0,  # A 级客户可以有更低的标准
        )

        # 验证添加了配置
        call_args = mock_db.add.call_args
        config = call_args[0][0]
        assert config.customer_level == "A"


class TestListConfigs:
    """list_configs 测试"""

    def test_list_active_configs(self, service, mock_db, sample_config):
        """列出活跃配置"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_config]

        result = service.list_configs(is_active=True)

        assert len(result) == 1
        assert result[0] == sample_config

    def test_list_all_configs(self, service, mock_db, sample_config):
        """列出所有配置"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_config]

        result = service.list_configs(is_active=None)

        assert len(result) == 1


# ========== 预警检查测试 ==========

class TestCheckMarginAlert:
    """check_margin_alert 测试"""

    def test_normal_margin_no_alert(self, service, mock_db, sample_config, sample_quote):
        """正常毛利率无预警"""
        # 设置 30% 毛利率（正常）
        version = MagicMock()
        version.id = 1
        version.total_price = Decimal("100000")
        version.cost_total = Decimal("70000")  # 30% 毛利率
        sample_quote.current_version = version

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_quote

        # Mock get_applicable_config
        with patch.object(service, 'get_applicable_config', return_value=sample_config):
            result = service.check_margin_alert(quote_id=1)

        assert result["alert_required"] is False
        assert result["alert_level"] == MarginAlertLevelEnum.GREEN.value

    def test_warning_margin_yellow_alert(self, service, mock_db, sample_config, sample_quote):
        """警告毛利率触发黄色预警"""
        # 设置 22% 毛利率（警告区间）
        version = MagicMock()
        version.id = 1
        version.total_price = Decimal("100000")
        version.cost_total = Decimal("78000")  # 22% 毛利率
        sample_quote.current_version = version

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_quote

        with patch.object(service, 'get_applicable_config', return_value=sample_config):
            result = service.check_margin_alert(quote_id=1)

        assert result["alert_required"] is True
        assert result["alert_level"] == MarginAlertLevelEnum.YELLOW.value

    def test_low_margin_red_alert(self, service, mock_db, sample_config, sample_quote):
        """低毛利率触发红色预警"""
        # 设置 15% 毛利率（警报区间）
        version = MagicMock()
        version.id = 1
        version.total_price = Decimal("100000")
        version.cost_total = Decimal("85000")  # 15% 毛利率
        sample_quote.current_version = version

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_quote

        with patch.object(service, 'get_applicable_config', return_value=sample_config):
            result = service.check_margin_alert(quote_id=1)

        assert result["alert_required"] is True
        assert result["alert_level"] == MarginAlertLevelEnum.RED.value

    def test_below_minimum_flagged(self, service, mock_db, sample_config, sample_quote):
        """低于最低毛利率标记"""
        # 设置 8% 毛利率（低于最低 10%）
        version = MagicMock()
        version.id = 1
        version.total_price = Decimal("100000")
        version.cost_total = Decimal("92000")  # 8% 毛利率
        sample_quote.current_version = version

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_quote

        with patch.object(service, 'get_applicable_config', return_value=sample_config):
            result = service.check_margin_alert(quote_id=1)

        assert result["below_minimum"] is True

    def test_quote_not_found(self, service, mock_db):
        """报价不存在"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(ValueError, match="报价不存在"):
            service.check_margin_alert(quote_id=999)

    def test_no_config_returns_no_alert(self, service, mock_db, sample_quote):
        """无配置返回无预警"""
        version = MagicMock()
        version.id = 1
        version.total_price = Decimal("100000")
        version.cost_total = Decimal("90000")  # 10% 毛利率
        sample_quote.current_version = version

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_quote

        with patch.object(service, 'get_applicable_config', return_value=None):
            result = service.check_margin_alert(quote_id=1)

        assert result["alert_required"] is False
        assert "无适用的预警配置" in result["message"]


# ========== 预警记录管理测试 ==========

class TestCreateAlertRecord:
    """create_alert_record 测试"""

    def test_create_record_for_low_margin(self, service, mock_db, sample_config, sample_quote):
        """为低毛利创建预警记录"""
        check_result = {
            "quote_id": 1,
            "quote_version_id": 1,
            "alert_required": True,
            "alert_level": MarginAlertLevelEnum.YELLOW.value,
            "gross_margin": 18.0,
            "total_price": 100000,
            "total_cost": 82000,
            "config_id": 1,
            "thresholds": {"standard": 25.0, "warning": 20.0, "alert": 15.0, "minimum": 10.0},
        }

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_quote

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        with patch.object(service, 'check_margin_alert', return_value=check_result):
            result = service.create_alert_record(
                quote_id=1,
                requested_by=1,
                justification="战略客户特批"
            )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_record_not_needed(self, service, mock_db):
        """正常毛利率无需创建记录"""
        check_result = {
            "quote_id": 1,
            "alert_required": False,
        }

        with patch.object(service, 'check_margin_alert', return_value=check_result):
            with pytest.raises(ValueError, match="毛利率正常，无需创建预警记录"):
                service.create_alert_record(
                    quote_id=1,
                    requested_by=1,
                    justification="测试"
                )


class TestApproveAlert:
    """approve_alert 测试"""

    def test_approve_pending_record(self, service, mock_db):
        """审批通过待处理记录"""
        record = MagicMock(spec=MarginAlertRecord)
        record.id = 1
        record.status = MarginAlertStatusEnum.PENDING.value
        record.approval_history = []

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = record

        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.approve_alert(
            record_id=1,
            approved_by=2,
            comment="同意特批",
            valid_days=30
        )

        assert record.status == MarginAlertStatusEnum.APPROVED.value
        assert record.approved_by == 2
        mock_db.commit.assert_called_once()

    def test_approve_nonexistent_record(self, service, mock_db):
        """审批不存在的记录"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with pytest.raises(ValueError, match="预警记录不存在"):
            service.approve_alert(record_id=999, approved_by=1, comment="测试")

    def test_approve_already_processed(self, service, mock_db):
        """审批已处理的记录"""
        record = MagicMock(spec=MarginAlertRecord)
        record.id = 1
        record.status = MarginAlertStatusEnum.APPROVED.value

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = record

        with pytest.raises(ValueError, match="状态不允许审批"):
            service.approve_alert(record_id=1, approved_by=1, comment="测试")


class TestRejectAlert:
    """reject_alert 测试"""

    def test_reject_pending_record(self, service, mock_db):
        """驳回待处理记录"""
        record = MagicMock(spec=MarginAlertRecord)
        record.id = 1
        record.status = MarginAlertStatusEnum.PENDING.value
        record.approval_history = []

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = record

        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.reject_alert(
            record_id=1,
            rejected_by=2,
            comment="毛利率过低，请重新报价"
        )

        assert record.status == MarginAlertStatusEnum.REJECTED.value
        mock_db.commit.assert_called_once()


class TestListPendingAlerts:
    """list_pending_alerts 测试"""

    def test_list_all_pending(self, service, mock_db):
        """列出所有待审批"""
        records = [MagicMock(spec=MarginAlertRecord) for _ in range(3)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = records

        result = service.list_pending_alerts()

        assert len(result) == 3

    def test_list_pending_for_approver(self, service, mock_db):
        """列出指定审批人的待审批"""
        records = [MagicMock(spec=MarginAlertRecord)]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = records

        result = service.list_pending_alerts(approver_id=1)

        assert len(result) == 1


class TestGetQuoteAlertHistory:
    """get_quote_alert_history 测试"""

    def test_get_history(self, service, mock_db):
        """获取报价预警历史"""
        records = [
            MagicMock(spec=MarginAlertRecord),
            MagicMock(spec=MarginAlertRecord),
        ]

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = records

        result = service.get_quote_alert_history(quote_id=1)

        assert len(result) == 2

    def test_empty_history(self, service, mock_db):
        """空历史"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = service.get_quote_alert_history(quote_id=1)

        assert len(result) == 0
