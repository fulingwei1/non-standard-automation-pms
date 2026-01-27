# -*- coding: utf-8 -*-
"""
销售团队数据聚合服务测试
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.sales import SalesTarget
from app.services.sales_team_service import SalesTeamService


@pytest.fixture
def sales_team_service(db_session: Session):
    return SalesTeamService(db_session)


@pytest.fixture
def test_sales_user(db_session: Session):
    from tests.conftest import _get_or_create_user

    user = _get_or_create_user(
        db_session,
        username="sales_test_user",
        password="test123",
        real_name="销售测试用户",
        department="销售部",
        employee_role="SALES",
    )

    db_session.flush()
    return user


class TestSalesTeamService:
    def test_init(self, db_session: Session):
        service = SalesTeamService(db_session)
        assert service.db is db_session

    def test_parse_period_value_monthly(self, sales_team_service):
        from app.services.sales_team_service import SalesTeamService

        start, end = SalesTeamService.parse_period_value("2024-01", "MONTHLY")
        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_parse_period_value_quarterly(self, sales_team_service):
        from app.services.sales_team_service import SalesTeamService

        start, end = SalesTeamService.parse_period_value("2024-Q1", "QUARTERLY")
        assert start == date(2024, 1, 1)
        assert end == date(2024, 3, 31)

    def test_parse_period_value_yearly(self, sales_team_service):
        from app.services.sales_team_service import SalesTeamService

        start, end = SalesTeamService.parse_period_value("2024", "YEARLY")
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_calculate_target_performance_lead_count(
        self, sales_team_service, test_sales_user
    ):
        target = SalesTarget(
        target_scope="PERSONAL",
        user_id=test_sales_user.id,
        target_type="LEAD_COUNT",
        target_value=Decimal("100"),
        target_period="MONTHLY",
        period_value="2024-01",
        status="ACTIVE",
        created_by=test_sales_user.id,
        )
        sales_team_service.db.add(target)
        sales_team_service.db.commit()

        actual_value, completion_rate = sales_team_service.calculate_target_performance(
        target
        )

        assert isinstance(actual_value, Decimal)
        assert isinstance(completion_rate, float)
        assert completion_rate >= 0

    def test_calculate_target_performance_opportunity_count(
        self, sales_team_service, test_sales_user
    ):
        target = SalesTarget(
        target_scope="PERSONAL",
        user_id=test_sales_user.id,
        target_type="OPPORTUNITY_COUNT",
        target_value=Decimal("50"),
        target_period="MONTHLY",
        period_value="2024-01",
        status="ACTIVE",
        created_by=test_sales_user.id,
        )
        sales_team_service.db.add(target)
        sales_team_service.db.commit()

        actual_value, completion_rate = sales_team_service.calculate_target_performance(
        target
        )

        assert isinstance(actual_value, Decimal)
        assert isinstance(completion_rate, float)
        assert completion_rate >= 0

    def test_calculate_target_performance_contract_amount(
        self, sales_team_service, test_sales_user
    ):
        target = SalesTarget(
        target_scope="PERSONAL",
        user_id=test_sales_user.id,
        target_type="CONTRACT_AMOUNT",
        target_value=Decimal("1000000"),
        target_period="MONTHLY",
        period_value="2024-01",
        status="ACTIVE",
        created_by=test_sales_user.id,
        )
        sales_team_service.db.add(target)
        sales_team_service.db.commit()

        actual_value, completion_rate = sales_team_service.calculate_target_performance(
        target
        )

        assert isinstance(actual_value, Decimal)
        assert isinstance(completion_rate, float)
        assert completion_rate >= 0

    def test_calculate_target_performance_zero_target_value(
        self, sales_team_service, test_sales_user
    ):
        target = SalesTarget(
        target_scope="PERSONAL",
        user_id=test_sales_user.id,
        target_type="LEAD_COUNT",
        target_value=Decimal("0"),
        target_period="MONTHLY",
        period_value="2024-01",
        status="ACTIVE",
        created_by=test_sales_user.id,
        )
        sales_team_service.db.add(target)
        sales_team_service.db.commit()

        actual_value, completion_rate = sales_team_service.calculate_target_performance(
        target
        )

        assert completion_rate == 0.0
        assert isinstance(actual_value, Decimal)

    def test_calculate_target_performance_collection_amount(
        self, sales_team_service, test_sales_user
    ):
        target = SalesTarget(
        target_scope="PERSONAL",
        user_id=test_sales_user.id,
        target_type="COLLECTION_AMOUNT",
        target_value=Decimal("500000"),
        target_period="MONTHLY",
        period_value="2024-01",
        status="ACTIVE",
        created_by=test_sales_user.id,
        )
        sales_team_service.db.add(target)
        sales_team_service.db.commit()

        actual_value, completion_rate = sales_team_service.calculate_target_performance(
        target
        )

        assert isinstance(actual_value, Decimal)
        assert isinstance(completion_rate, float)
        assert completion_rate >= 0

    def test_build_personal_target_map_empty_user_ids(self, sales_team_service):
        result = sales_team_service.build_personal_target_map([], "2024-01", None)
        assert result == {}

    def test_build_personal_target_map_empty_period_values(self, sales_team_service):
        result = sales_team_service.build_personal_target_map([1, 2], None, None)
        assert result == {}

    def test_build_personal_target_map_success(
        self, sales_team_service, test_sales_user
    ):
        target = SalesTarget(
        target_scope="PERSONAL",
        user_id=test_sales_user.id,
        target_type="CONTRACT_AMOUNT",
        target_value=Decimal("1000000"),
        target_period="MONTHLY",
        period_value="2024-01",
        status="ACTIVE",
        created_by=test_sales_user.id,
        )
        sales_team_service.db.add(target)
        sales_team_service.db.commit()

        result = sales_team_service.build_personal_target_map(
        [test_sales_user.id], "2024-01", None
        )

        assert test_sales_user.id in result
        assert "monthly" in result[test_sales_user.id]  # 注意：返回的是小写 "monthly"

    def test_get_followup_statistics_map_empty_user_ids(self, sales_team_service):
        """测试空用户ID列表的跟进统计"""
        result = sales_team_service.get_followup_statistics_map([], None, None)
        assert result == {}

    def test_get_followup_statistics_map_success(self, sales_team_service, test_sales_user):
        """测试获取跟进统计"""
        result = sales_team_service.get_followup_statistics_map(
        [test_sales_user.id],
        None,
        None
        )
        assert isinstance(result, dict)

    def test_get_recent_followups_map_empty_user_ids(self, sales_team_service):
        """测试空用户ID列表的最近跟进（使用 get_recent_followups_map）"""
        result = sales_team_service.get_recent_followups_map([])
        assert result == {}

    def test_get_recent_followups_map_success(self, sales_team_service, test_sales_user):
        """测试获取最近跟进（使用 get_recent_followups_map）"""
        result = sales_team_service.get_recent_followups_map([test_sales_user.id])
        assert isinstance(result, dict)

    def test_get_recent_followups_map_with_date_range(self, sales_team_service, test_sales_user):
        """测试带日期范围的最近跟进（使用 get_recent_followups_map）"""
        from datetime import datetime, timedelta
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        result = sales_team_service.get_recent_followups_map(
        [test_sales_user.id],
        start_datetime=start,
        end_datetime=end
        )
        assert isinstance(result, dict)

    def test_get_customer_distribution_map_empty_user_ids(self, sales_team_service):
        """测试空用户ID列表的客户分布"""
        from datetime import date
        result = sales_team_service.get_customer_distribution_map([], None, None)
        assert result == {}

    def test_get_customer_distribution_map_success(
        self, sales_team_service, test_sales_user
    ):
        """测试获取客户分布"""
        from datetime import date
        result = sales_team_service.get_customer_distribution_map(
        [test_sales_user.id],
        date(2024, 1, 1),
        date(2024, 12, 31)
        )
        assert isinstance(result, dict)

    def test_get_lead_quality_stats_map_empty_user_ids(self, sales_team_service):
        """测试空用户ID列表的线索质量统计"""
        from datetime import datetime
        result = sales_team_service.get_lead_quality_stats_map([], None, None)
        assert result == {}

    def test_get_lead_quality_stats_map_success(
        self, sales_team_service, test_sales_user
    ):
        """测试获取线索质量统计"""
        from datetime import datetime
        result = sales_team_service.get_lead_quality_stats_map(
        [test_sales_user.id],
        None,
        None
        )
        assert isinstance(result, dict)

    def test_get_opportunity_stats_map_empty_user_ids(self, sales_team_service):
        """测试空用户ID列表的商机统计"""
        from datetime import datetime
        result = sales_team_service.get_opportunity_stats_map([], None, None)
        assert result == {}

    def test_get_opportunity_stats_map_success(
        self, sales_team_service, test_sales_user
    ):
        """测试获取商机统计"""
        from datetime import datetime
        result = sales_team_service.get_opportunity_stats_map(
        [test_sales_user.id],
        None,
        None
        )
        assert isinstance(result, dict)

    def test_get_recent_followups_map_empty_user_ids(self, sales_team_service):
        """测试空用户ID列表的最近跟进"""
        result = sales_team_service.get_recent_followups_map([])
        assert result == {}

    def test_get_recent_followups_map_success(
        self, sales_team_service, test_sales_user
    ):
        """测试获取最近跟进"""
        result = sales_team_service.get_recent_followups_map([test_sales_user.id])
        assert isinstance(result, dict)

    def test_get_recent_followups_map_with_date_range(
        self, sales_team_service, test_sales_user
    ):
        """测试带日期范围的最近跟进"""
        from datetime import datetime, timedelta
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        result = sales_team_service.get_recent_followups_map(
        [test_sales_user.id],
        start_datetime=start,
        end_datetime=end
        )
        assert isinstance(result, dict)

    def test_invalid_target_type(self, sales_team_service, test_sales_user):
        target = SalesTarget(
        target_scope="PERSONAL",  # 必填字段
        user_id=test_sales_user.id,
        target_type="INVALID_TYPE",
        target_value=Decimal("100"),
        target_period="MONTHLY",
        period_value="2024-01",
        status="ACTIVE",
        created_by=test_sales_user.id,  # 必填字段
        )
        sales_team_service.db.add(target)
        sales_team_service.db.commit()

        actual_value, completion_rate = sales_team_service.calculate_target_performance(
        target
        )

        assert actual_value == Decimal("0")
        assert completion_rate == 0.0
