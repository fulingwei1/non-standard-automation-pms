# -*- coding: utf-8 -*-
"""
销售目标服务单元测试 (F组)

测试 SalesTargetService 的核心方法：
- create_target
- get_target / get_targets
- update_target
- delete_target
- breakdown_target
- auto_breakdown_target
- get_breakdown_tree
- get_team_ranking / get_personal_ranking
- get_completion_trend
- get_completion_distribution
- _calculate_completion_rate
"""
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.sales_target_service import SalesTargetService


@pytest.fixture
def db():
    return MagicMock()


# ============================================================
# create_target 测试
# ============================================================

class TestCreateTarget:
    def test_team_target_missing_team_id(self, db):
        target_data = MagicMock(target_type='team', team_id=None, user_id=None)
        with pytest.raises(HTTPException) as exc:
            SalesTargetService.create_target(db, target_data, created_by=1)
        assert exc.value.status_code == 400

    def test_personal_target_missing_user_id(self, db):
        target_data = MagicMock(target_type='personal', team_id=None, user_id=None)
        with pytest.raises(HTTPException) as exc:
            SalesTargetService.create_target(db, target_data, created_by=1)
        assert exc.value.status_code == 400

    def test_duplicate_target(self, db):
        target_data = MagicMock(
            target_type='team', team_id=1, user_id=None,
            target_period='MONTHLY', target_year=2025
        )
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        with pytest.raises(HTTPException) as exc:
            SalesTargetService.create_target(db, target_data, created_by=1)
        assert exc.value.status_code == 400
        assert "已存在" in exc.value.detail

    def test_create_success(self, db):
        target_data = MagicMock(
            target_type='team', team_id=1, user_id=None,
            target_period='MONTHLY', target_year=2025,
            model_dump=lambda: {
                'target_type': 'team', 'team_id': 1, 'user_id': None,
                'target_period': 'MONTHLY', 'target_year': 2025,
                'sales_target': Decimal('100000'), 'payment_target': Decimal('90000'),
                'new_customer_target': 2, 'lead_target': 5, 'opportunity_target': 3,
                'deal_target': 1, 'target_month': 1, 'target_quarter': None,
                'actual_sales': Decimal('0'), 'completion_rate': Decimal('0')
            }
        )
        db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.services.sales_target_service.save_obj') as mock_save:
            with patch('app.services.sales_target_service.SalesTargetV2') as MockTarget:
                MockTarget.return_value = MagicMock()
                result = SalesTargetService.create_target(db, target_data, created_by=1)
        assert MockTarget.called


# ============================================================
# get_target 测试
# ============================================================

class TestGetTarget:
    def test_get_existing_target(self, db):
        target = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = target
        result = SalesTargetService.get_target(db, 1)
        assert result == target

    def test_get_nonexistent_target(self, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = SalesTargetService.get_target(db, 999)
        assert result is None


# ============================================================
# get_targets 测试
# ============================================================

class TestGetTargets:
    def test_get_all_targets(self, db):
        targets = [MagicMock(), MagicMock()]
        db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = targets
        result = SalesTargetService.get_targets(db)
        assert len(result) == 2

    def test_get_targets_with_filters(self, db):
        targets = [MagicMock()]
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = targets
        db.query.return_value = mock_q

        result = SalesTargetService.get_targets(
            db,
            target_type='team',
            target_year=2025,
            target_month=1,
            team_id=1
        )
        assert len(result) == 1


# ============================================================
# update_target 测试
# ============================================================

class TestUpdateTarget:
    def test_update_nonexistent(self, db):
        with patch('app.services.sales_target_service.get_or_404') as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="目标不存在")
            target_data = MagicMock(model_dump=lambda exclude_unset=True: {})
            with pytest.raises(HTTPException):
                SalesTargetService.update_target(db, 999, target_data)

    def test_update_success(self, db):
        target = MagicMock(
            sales_target=Decimal("100000"),
            actual_sales=Decimal("50000"),
            completion_rate=Decimal("50")
        )
        update_data = MagicMock()
        update_data.model_dump.return_value = {'sales_target': Decimal("120000")}

        with patch('app.services.sales_target_service.get_or_404', return_value=target):
            result = SalesTargetService.update_target(db, 1, update_data)
        assert target.sales_target == Decimal("120000")
        assert db.commit.called


# ============================================================
# delete_target 测试
# ============================================================

class TestDeleteTarget:
    def test_delete_with_sub_targets(self, db):
        target = MagicMock()
        with patch('app.services.sales_target_service.get_or_404', return_value=target):
            db.query.return_value.filter.return_value.count.return_value = 2
            with pytest.raises(HTTPException) as exc:
                SalesTargetService.delete_target(db, 1)
            assert exc.value.status_code == 400

    def test_delete_success(self, db):
        target = MagicMock()
        with patch('app.services.sales_target_service.get_or_404', return_value=target):
            db.query.return_value.filter.return_value.count.return_value = 0
            with patch('app.services.sales_target_service.delete_obj') as mock_del:
                result = SalesTargetService.delete_target(db, 1)
        assert result is True
        assert mock_del.called


# ============================================================
# breakdown_target 测试
# ============================================================

class TestBreakdownTarget:
    def test_breakdown_manual(self, db):
        parent_target = MagicMock(
            target_period='MONTHLY', target_year=2025,
            target_month=1, target_quarter=None
        )
        breakdown_item = MagicMock(
            target_type='team', team_id=1, user_id=None,
            sales_target=Decimal("50000"), payment_target=Decimal("45000"),
            new_customer_target=1, lead_target=3, opportunity_target=2,
            deal_target=1
        )
        breakdown_data = MagicMock(breakdown_items=[breakdown_item])

        with patch('app.services.sales_target_service.get_or_404', return_value=parent_target):
            with patch('app.services.sales_target_service.SalesTargetV2') as MockTarget:
                with patch('app.services.sales_target_service.TargetBreakdownLog') as MockLog:
                    MockTarget.return_value = MagicMock()
                    MockLog.return_value = MagicMock()
                    result = SalesTargetService.breakdown_target(db, 1, breakdown_data, created_by=1)
        assert db.commit.called


# ============================================================
# get_team_ranking 测试
# ============================================================

class TestGetTeamRanking:
    def test_get_ranking_annual(self, db):
        target1 = MagicMock(team_id=1, sales_target=Decimal("100000"), actual_sales=Decimal("95000"), completion_rate=Decimal("95"))
        target2 = MagicMock(team_id=2, sales_target=Decimal("80000"), actual_sales=Decimal("60000"), completion_rate=Decimal("75"))
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = [target1, target2]
        db.query.return_value = mock_q

        result = SalesTargetService.get_team_ranking(db, 2025)
        assert len(result) == 2
        assert result[0]['rank'] == 1
        assert result[1]['rank'] == 2

    def test_get_ranking_monthly(self, db):
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = []
        db.query.return_value = mock_q

        result = SalesTargetService.get_team_ranking(db, 2025, target_month=1)
        assert result == []


# ============================================================
# get_personal_ranking 测试
# ============================================================

class TestGetPersonalRanking:
    def test_get_ranking(self, db):
        target = MagicMock(user_id=1, sales_target=Decimal("50000"), actual_sales=Decimal("45000"), completion_rate=Decimal("90"))
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value.all.return_value = [target]
        db.query.return_value = mock_q

        result = SalesTargetService.get_personal_ranking(db, 2025)
        assert len(result) == 1
        assert result[0]['user_id'] == target.user_id


# ============================================================
# get_completion_trend 测试
# ============================================================

class TestGetCompletionTrend:
    def test_completion_trend(self, db):
        target = MagicMock(completion_rate=Decimal("75"), actual_sales=Decimal("75000"), sales_target=Decimal("100000"))
        with patch('app.services.sales_target_service.get_or_404', return_value=target):
            result = SalesTargetService.get_completion_trend(db, 1)
        assert len(result) == 1
        assert result[0]['completion_rate'] == float(target.completion_rate)


# ============================================================
# get_completion_distribution 测试
# ============================================================

class TestGetCompletionDistribution:
    def test_distribution_various_rates(self, db):
        targets = [
            MagicMock(completion_rate=Decimal("10")),
            MagicMock(completion_rate=Decimal("30")),
            MagicMock(completion_rate=Decimal("50")),
            MagicMock(completion_rate=Decimal("70")),
            MagicMock(completion_rate=Decimal("90")),
            MagicMock(completion_rate=Decimal("110")),
        ]
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = targets
        db.query.return_value = mock_q

        result = SalesTargetService.get_completion_distribution(db, 2025)
        distribution = {d['range_label']: d['count'] for d in result['distribution']}
        assert distribution['0-20%'] == 1
        assert distribution['20-40%'] == 1
        assert distribution['100%+'] == 1

    def test_empty_distribution(self, db):
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        result = SalesTargetService.get_completion_distribution(db, 2025)
        assert result['distribution'] is not None


# ============================================================
# _calculate_completion_rate 测试
# ============================================================

class TestCalculateCompletionRate:
    def test_zero_target(self):
        target = MagicMock(sales_target=Decimal("0"), actual_sales=Decimal("50000"))
        result = SalesTargetService._calculate_completion_rate(target)
        assert result == Decimal("0")

    def test_normal_calculation(self):
        target = MagicMock(sales_target=Decimal("100000"), actual_sales=Decimal("75000"))
        result = SalesTargetService._calculate_completion_rate(target)
        assert result == Decimal("75.00")

    def test_overachievement(self):
        target = MagicMock(sales_target=Decimal("100000"), actual_sales=Decimal("120000"))
        result = SalesTargetService._calculate_completion_rate(target)
        assert result == Decimal("120.00")
