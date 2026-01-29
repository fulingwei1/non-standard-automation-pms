# -*- coding: utf-8 -*-
"""
Tests for sales_team_service service
Covers: app/services/sales_team_service.py
Coverage Target: 0% → 70%+
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.sales_team_service import SalesTeamService


@pytest.fixture
def sales_team_service(db_session: Session):
    """Create sales team service instance."""
    return SalesTeamService(db_session)


@pytest.mark.unit
class TestSalesTeamServiceInit:
    """测试服务初始化"""

    def test_init_with_session(self, db_session: Session):
        """测试使用 session 初始化服务"""
        service = SalesTeamService(db_session)
        assert service.db is db_session


@pytest.mark.unit
class TestParsePeriodValue:
    """测试周期值解析"""

    def test_parse_monthly_period(self):
        """测试解析月度周期"""
        start, end = SalesTeamService.parse_period_value("2024-01", "MONTHLY")

        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_parse_monthly_period_december(self):
        """测试解析12月份"""
        start, end = SalesTeamService.parse_period_value("2024-12", "MONTHLY")

        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)

    def test_parse_monthly_period_february_leap_year(self):
        """测试解析闰年2月"""
        start, end = SalesTeamService.parse_period_value("2024-02", "MONTHLY")

        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)  # 2024 是闰年

    def test_parse_quarterly_q1(self):
        """测试解析第一季度"""
        start, end = SalesTeamService.parse_period_value("2024-Q1", "QUARTERLY")

        assert start == date(2024, 1, 1)
        assert end == date(2024, 3, 31)

    def test_parse_quarterly_q2(self):
        """测试解析第二季度"""
        start, end = SalesTeamService.parse_period_value("2024-Q2", "QUARTERLY")

        assert start == date(2024, 4, 1)
        assert end == date(2024, 6, 30)

    def test_parse_quarterly_q3(self):
        """测试解析第三季度"""
        start, end = SalesTeamService.parse_period_value("2024-Q3", "QUARTERLY")

        assert start == date(2024, 7, 1)
        assert end == date(2024, 9, 30)

    def test_parse_quarterly_q4(self):
        """测试解析第四季度"""
        start, end = SalesTeamService.parse_period_value("2024-Q4", "QUARTERLY")

        assert start == date(2024, 10, 1)
        assert end == date(2024, 12, 31)

    def test_parse_yearly_period(self):
        """测试解析年度周期"""
        start, end = SalesTeamService.parse_period_value("2024", "YEARLY")

        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_parse_invalid_monthly_format(self):
        """测试解析无效的月度格式"""
        start, end = SalesTeamService.parse_period_value("invalid", "MONTHLY")

        assert start is None
        assert end is None

    def test_parse_unknown_period_type(self):
        """测试解析未知的周期类型"""
        start, end = SalesTeamService.parse_period_value("2024-01", "UNKNOWN")

        assert start is None
        assert end is None


@pytest.mark.unit
class TestCalculateTargetPerformance:
    """测试目标完成率计算"""

    def test_calculate_lead_count_target_empty(
        self, sales_team_service: SalesTeamService
    ):
        """测试线索数量目标 - 空数据库"""
        target = Mock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.period_value = "2024-01"
        target.target_period = "MONTHLY"
        target.user_id = 99999  # 不存在的用户

        actual, rate = sales_team_service.calculate_target_performance(target)

        assert actual == Decimal("0")
        assert rate == 0.0

    def test_calculate_opportunity_count_target_empty(
        self, sales_team_service: SalesTeamService
    ):
        """测试商机数量目标 - 空数据库"""
        target = Mock()
        target.target_type = "OPPORTUNITY_COUNT"
        target.target_value = Decimal("5")
        target.period_value = "2024-01"
        target.target_period = "MONTHLY"
        target.user_id = 99999

        actual, rate = sales_team_service.calculate_target_performance(target)

        assert actual == Decimal("0")
        assert rate == 0.0

    def test_calculate_contract_amount_target_empty(
        self, sales_team_service: SalesTeamService
    ):
        """测试合同金额目标 - 空数据库"""
        target = Mock()
        target.target_type = "CONTRACT_AMOUNT"
        target.target_value = Decimal("100000")
        target.period_value = "2024-01"
        target.target_period = "MONTHLY"
        target.user_id = 99999

        actual, rate = sales_team_service.calculate_target_performance(target)

        assert actual == Decimal("0")
        assert rate == 0.0

    def test_calculate_collection_amount_target_empty(
        self, sales_team_service: SalesTeamService
    ):
        """测试回款金额目标 - 空数据库"""
        target = Mock()
        target.target_type = "COLLECTION_AMOUNT"
        target.target_value = Decimal("50000")
        target.period_value = "2024-01"
        target.target_period = "MONTHLY"
        target.user_id = 99999

        actual, rate = sales_team_service.calculate_target_performance(target)

        assert actual == Decimal("0")
        assert rate == 0.0

    def test_calculate_zero_target_value(
        self, sales_team_service: SalesTeamService
    ):
        """测试目标值为零时的处理"""
        target = Mock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("0")
        target.period_value = "2024-01"
        target.target_period = "MONTHLY"
        target.user_id = 99999

        actual, rate = sales_team_service.calculate_target_performance(target)

        assert actual == Decimal("0")
        assert rate == 0.0

    def test_calculate_unknown_target_type(
        self, sales_team_service: SalesTeamService
    ):
        """测试未知目标类型"""
        target = Mock()
        target.target_type = "UNKNOWN_TYPE"
        target.target_value = Decimal("100")
        target.period_value = "2024-01"
        target.target_period = "MONTHLY"
        target.user_id = 99999

        actual, rate = sales_team_service.calculate_target_performance(target)

        # 未知类型应返回 0
        assert actual == Decimal("0")
        assert rate == 0.0


@pytest.mark.unit
class TestBuildPersonalTargetMap:
    """测试个人目标映射构建"""

    def test_build_personal_target_map_empty_user_ids(
        self, sales_team_service: SalesTeamService
    ):
        """测试空用户 ID 列表"""
        result = sales_team_service.build_personal_target_map([], "2024-01", "2024")

        assert result == {}

    def test_build_personal_target_map_no_period_values(
        self, sales_team_service: SalesTeamService
    ):
        """测试没有周期值"""
        result = sales_team_service.build_personal_target_map([1, 2, 3], None, None)

        assert result == {}

    def test_build_personal_target_map_no_targets(
        self, sales_team_service: SalesTeamService
    ):
        """测试没有目标数据"""
        result = sales_team_service.build_personal_target_map([99999], "2024-01", None)

        assert result == {}


@pytest.mark.unit
class TestGetFollowupStatisticsMap:
    """测试跟进统计映射"""

    def test_get_followup_statistics_empty_user_ids(
        self, sales_team_service: SalesTeamService
    ):
        """测试空用户 ID 列表"""
        result = sales_team_service.get_followup_statistics_map([], None, None)

        assert result == {}

    def test_get_followup_statistics_no_data(
        self, sales_team_service: SalesTeamService
    ):
        """测试无跟进数据"""
        result = sales_team_service.get_followup_statistics_map(
        [99999],
        datetime(2024, 1, 1),
        datetime(2024, 12, 31),
        )

        assert result == {}


@pytest.mark.unit
class TestGetLeadQualityStatsMap:
    """测试线索质量统计映射"""

    def test_get_lead_quality_stats_empty_user_ids(
        self, sales_team_service: SalesTeamService
    ):
        """测试空用户 ID 列表"""
        result = sales_team_service.get_lead_quality_stats_map([], None, None)

        assert result == {}

    def test_get_lead_quality_stats_no_data(
        self, sales_team_service: SalesTeamService
    ):
        """测试无线索数据"""
        result = sales_team_service.get_lead_quality_stats_map(
        [99999],
        datetime(2024, 1, 1),
        datetime(2024, 12, 31),
        )

        assert result == {}


@pytest.mark.unit
class TestGetOpportunityStatsMap:
    """测试商机统计映射"""

    def test_get_opportunity_stats_empty_user_ids(
        self, sales_team_service: SalesTeamService
    ):
        """测试空用户 ID 列表"""
        result = sales_team_service.get_opportunity_stats_map([], None, None)

        assert result == {}

    def test_get_opportunity_stats_no_data(
        self, sales_team_service: SalesTeamService
    ):
        """测试无商机数据"""
        result = sales_team_service.get_opportunity_stats_map(
        [99999],
        datetime(2024, 1, 1),
        datetime(2024, 12, 31),
        )

        assert result == {}


@pytest.mark.unit
class TestGetRecentFollowupsMap:
    """测试最近跟进记录映射"""

    def test_get_recent_followups_map_empty_user_ids(
        self, sales_team_service: SalesTeamService
    ):
        """测试空用户 ID 列表"""
        result = sales_team_service.get_recent_followups_map([])

        assert result == {}

    def test_get_recent_followups_map_with_date_range(
        self, sales_team_service: SalesTeamService
    ):
        """测试带日期范围的最近跟进"""
        result = sales_team_service.get_recent_followups_map(
            [99999],
            start_datetime=datetime(2024, 1, 1),
            end_datetime=datetime(2024, 12, 31),
        )

        assert isinstance(result, dict)


@pytest.mark.unit
class TestGetCustomerDistributionMap:
    """测试客户分布统计映射"""

    def test_get_customer_distribution_map_empty_user_ids(
        self, sales_team_service: SalesTeamService
    ):
        """测试空用户 ID 列表"""
        result = sales_team_service.get_customer_distribution_map(
            [], date(2024, 1, 1), date(2024, 12, 31)
        )

        assert result == {}

    def test_get_customer_distribution_map_no_data(
        self, sales_team_service: SalesTeamService
    ):
        """测试无客户数据"""
        result = sales_team_service.get_customer_distribution_map(
            [99999], date(2024, 1, 1), date(2024, 12, 31)
        )

        assert isinstance(result, dict)


@pytest.mark.unit
@pytest.mark.skip(reason="Method get_team_statistics does not exist in SalesTeamService - tests need redesign")
class TestGetTeamStatistics:
    """测试团队统计 - 方法不存在，跳过"""

    def test_get_team_statistics_empty_user_ids(
        self, sales_team_service: SalesTeamService
    ):
        """测试空用户 ID 列表"""
        result = sales_team_service.get_team_statistics([])

        assert result == {}

    def test_get_team_statistics_no_data(
        self, sales_team_service: SalesTeamService
    ):
        """测试无团队数据"""
        result = sales_team_service.get_team_statistics([99999])

        assert isinstance(result, dict)
