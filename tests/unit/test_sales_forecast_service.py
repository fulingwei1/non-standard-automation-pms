# -*- coding: utf-8 -*-
"""
销售预测服务测试（最小版）
"""

import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from app.models.sales import SalesTarget
from tests.conftest import _get_or_create_user


class TestSalesForecastService:
    """销售预测服务测试"""

    def test_service_creation(self):
        """测试服务创建"""
        from app.services.sales_forecast_service import SalesForecastService
        
        mock_db = MagicMock()
        service = SalesForecastService(mock_db)
        
        assert service is not None
        assert service.db == mock_db

    def test_sales_target_uses_company_yearly_target_from_sales_targets(self, db_session):
        """年度预测目标应读取 sales_targets 真表，而不是 2 亿默认值。"""
        from app.services.sales_forecast_service import SalesForecastService

        creator = _get_or_create_user(
            db_session,
            username="forecast-target-owner",
            password="test123",
            real_name="预测目标创建人",
            department="销售部",
            employee_role="SALES",
        )
        db_session.add(
            SalesTarget(
                target_scope="COMPANY",
                target_type="CONTRACT_AMOUNT",
                target_period="YEARLY",
                period_value="2026",
                target_value=Decimal("12345678.90"),
                status="ACTIVE",
                created_by=creator.id,
            )
        )
        db_session.commit()

        service = SalesForecastService(db_session)

        assert service._get_sales_target(2026, 1, "yearly") == (12345678.9, "CONFIGURED")

    def test_sales_target_sums_quarterly_scope_targets_when_company_target_missing(
        self, db_session
    ):
        """没有公司级目标时，应汇总同周期的有效合同额目标。"""
        from app.services.sales_forecast_service import SalesForecastService

        creator = _get_or_create_user(
            db_session,
            username="forecast-target-team-owner",
            password="test123",
            real_name="预测季度目标创建人",
            department="销售部",
            employee_role="SALES",
        )
        db_session.add_all(
            [
                SalesTarget(
                    target_scope="PERSONAL",
                    user_id=creator.id,
                    target_type="CONTRACT_AMOUNT",
                    target_period="QUARTERLY",
                    period_value="2026-Q2",
                    target_value=Decimal("4000000"),
                    status="ACTIVE",
                    created_by=creator.id,
                ),
                SalesTarget(
                    target_scope="TEAM",
                    target_type="CONTRACT_AMOUNT",
                    target_period="QUARTERLY",
                    period_value="2026-Q2",
                    target_value=Decimal("6000000"),
                    status="ACTIVE",
                    created_by=creator.id,
                ),
                SalesTarget(
                    target_scope="PERSONAL",
                    user_id=creator.id,
                    target_type="CONTRACT_AMOUNT",
                    target_period="QUARTERLY",
                    period_value="2026-Q2",
                    target_value=Decimal("9999999"),
                    status="CANCELLED",
                    created_by=creator.id,
                ),
            ]
        )
        db_session.commit()

        service = SalesForecastService(db_session)

        assert service._get_sales_target(2026, 2, "quarterly") == (10000000.0, "CONFIGURED")

    def test_sales_target_derives_from_real_yearly_target_when_quarter_missing(
        self, db_session
    ):
        """季度目标未配置时，应从当年真实年度目标换算，而不是直接跳到系统默认兜底值。"""
        from app.services.sales_forecast_service import SalesForecastService

        creator = _get_or_create_user(
            db_session,
            username="forecast-target-derive-owner",
            password="test123",
            real_name="预测年度目标创建人",
            department="销售部",
            employee_role="SALES",
        )
        db_session.add(
            SalesTarget(
                target_scope="COMPANY",
                target_type="CONTRACT_AMOUNT",
                target_period="YEARLY",
                period_value="2026",
                target_value=Decimal("400000000"),
                status="ACTIVE",
                created_by=creator.id,
            )
        )
        db_session.commit()

        service = SalesForecastService(db_session)

        # 2026-Q3 没有任何季度目标配置，应从 4 亿真实年度目标换算（叠加季节性因子），
        # 而不是从系统默认的 2 亿年度目标换算。
        value, source = service._get_sales_target(2026, 3, "quarterly")
        assert source == "DERIVED_FROM_YEARLY"
        quarter_factor = sum(
            service.SEASONAL_FACTORS[m] for m in (7, 8, 9)
        ) / 3
        assert value == pytest.approx((400_000_000 / 4) * quarter_factor)

    def test_sales_target_falls_back_when_no_real_data_configured(self, db_session):
        """连年度目标都没配置时，才使用系统默认兜底值，且必须显式标注来源为 FALLBACK。"""
        from app.services.sales_forecast_service import SalesForecastService

        service = SalesForecastService(db_session)

        value, source = service._get_sales_target(2099, 1, "yearly")
        assert source == "FALLBACK"
        assert value == 200_000_000
