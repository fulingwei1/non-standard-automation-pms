# -*- coding: utf-8 -*-
"""
销售目标服务单元测试
覆盖: app/services/sales_target_service.py
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


# ─── create_target ─────────────────────────────────────────────────────────────

class TestCreateTarget:
    def test_team_target_without_team_id_raises(self, mock_db):
        """团队目标未指定 team_id 应报错"""
        from app.services.sales_target_service import SalesTargetService
        from app.schemas.sales_target import SalesTargetV2Create
        from fastapi import HTTPException

        data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            # team_id missing
            sales_target=Decimal("100000"),
            payment_target=Decimal("80000"),
            new_customer_target=5,
            lead_target=20,
            opportunity_target=10,
            deal_target=3,
        )
        with pytest.raises(HTTPException) as exc_info:
            SalesTargetService.create_target(mock_db, data, created_by=1)
        assert exc_info.value.status_code == 400
        assert "team_id" in exc_info.value.detail

    def test_personal_target_without_user_id_raises(self, mock_db):
        """个人目标未指定 user_id 应报错"""
        from app.services.sales_target_service import SalesTargetService
        from app.schemas.sales_target import SalesTargetV2Create
        from fastapi import HTTPException

        data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="personal",
            # user_id missing
            sales_target=Decimal("50000"),
            payment_target=Decimal("40000"),
            new_customer_target=2,
            lead_target=10,
            opportunity_target=5,
            deal_target=1,
        )
        with pytest.raises(HTTPException) as exc_info:
            SalesTargetService.create_target(mock_db, data, created_by=1)
        assert exc_info.value.status_code == 400

    def test_duplicate_target_raises(self, mock_db):
        """重复目标应报错"""
        from app.services.sales_target_service import SalesTargetService
        from app.schemas.sales_target import SalesTargetV2Create
        from fastapi import HTTPException

        data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
            sales_target=Decimal("100000"),
            payment_target=Decimal("80000"),
            new_customer_target=5,
            lead_target=20,
            opportunity_target=10,
            deal_target=3,
        )
        # existing target found
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            SalesTargetService.create_target(mock_db, data, created_by=1)
        assert exc_info.value.status_code == 400
        assert "已存在" in exc_info.value.detail

    def test_create_target_success(self, mock_db):
        """正常创建目标"""
        from app.services.sales_target_service import SalesTargetService
        from app.schemas.sales_target import SalesTargetV2Create

        data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
            sales_target=Decimal("100000"),
            payment_target=Decimal("80000"),
            new_customer_target=5,
            lead_target=20,
            opportunity_target=10,
            deal_target=3,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = None  # no existing

        with patch("app.services.sales_target_service.SalesTargetV2") as MockTarget, \
             patch("app.services.sales_target_service.save_obj"):
            mock_target = MagicMock()
            MockTarget.return_value = mock_target
            result = SalesTargetService.create_target(mock_db, data, created_by=1)
        assert result == mock_target


# ─── get_target / get_targets ──────────────────────────────────────────────────

class TestGetTargets:
    def test_get_target_by_id(self, mock_db):
        """根据ID获取目标"""
        from app.services.sales_target_service import SalesTargetService
        mock_target = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_target
        result = SalesTargetService.get_target(mock_db, 1)
        assert result == mock_target

    def test_get_target_not_found(self, mock_db):
        """目标不存在返回 None"""
        from app.services.sales_target_service import SalesTargetService
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = SalesTargetService.get_target(mock_db, 999)
        assert result is None

    def test_get_targets_with_filters(self, mock_db):
        """带过滤条件查询目标列表"""
        from app.services.sales_target_service import SalesTargetService
        mock_targets = [MagicMock(), MagicMock()]
        # chain: filter.filter.filter...order_by.offset.limit.all
        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = mock_targets

        result = SalesTargetService.get_targets(
            mock_db,
            target_type="team",
            target_year=2024,
            target_month=1,
        )
        assert result == mock_targets


# ─── delete_target ─────────────────────────────────────────────────────────────

class TestDeleteTarget:
    def test_delete_with_sub_targets_raises(self, mock_db):
        """有子目标时应拒绝删除"""
        from app.services.sales_target_service import SalesTargetService
        from fastapi import HTTPException

        mock_target = MagicMock()
        with patch("app.services.sales_target_service.get_or_404", return_value=mock_target):
            mock_db.query.return_value.filter.return_value.count.return_value = 2
            with pytest.raises(HTTPException) as exc_info:
                SalesTargetService.delete_target(mock_db, 1)
            assert exc_info.value.status_code == 400

    def test_delete_success(self, mock_db):
        """正常删除目标"""
        from app.services.sales_target_service import SalesTargetService

        mock_target = MagicMock()
        with patch("app.services.sales_target_service.get_or_404", return_value=mock_target), \
             patch("app.services.sales_target_service.delete_obj") as mock_del:
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            result = SalesTargetService.delete_target(mock_db, 1)
        assert result is True
        mock_del.assert_called_once_with(mock_db, mock_target)


# ─── _calculate_completion_rate ────────────────────────────────────────────────

class TestCalculateCompletionRate:
    def test_zero_target_returns_zero(self):
        """目标为0时完成率为0"""
        from app.services.sales_target_service import SalesTargetService
        target = MagicMock()
        target.sales_target = Decimal("0")
        target.actual_sales = Decimal("50000")
        result = SalesTargetService._calculate_completion_rate(target)
        assert result == Decimal("0")

    def test_normal_completion_rate(self):
        """正常计算完成率"""
        from app.services.sales_target_service import SalesTargetService
        target = MagicMock()
        target.sales_target = Decimal("100000")
        target.actual_sales = Decimal("80000")
        result = SalesTargetService._calculate_completion_rate(target)
        assert result == Decimal("80.00")

    def test_over_completion(self):
        """超额完成时完成率超过100"""
        from app.services.sales_target_service import SalesTargetService
        target = MagicMock()
        target.sales_target = Decimal("100000")
        target.actual_sales = Decimal("120000")
        result = SalesTargetService._calculate_completion_rate(target)
        assert result == Decimal("120.00")


# ─── get_team_ranking / get_personal_ranking ───────────────────────────────────

class TestRanking:
    def test_get_team_ranking(self, mock_db):
        """获取团队排名"""
        from app.services.sales_target_service import SalesTargetService

        t1 = MagicMock()
        t1.team_id = 1
        t1.sales_target = Decimal("100000")
        t1.actual_sales = Decimal("90000")
        t1.completion_rate = Decimal("90.00")

        t2 = MagicMock()
        t2.team_id = 2
        t2.sales_target = Decimal("100000")
        t2.actual_sales = Decimal("80000")
        t2.completion_rate = Decimal("80.00")

        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = [t1, t2]

        result = SalesTargetService.get_team_ranking(mock_db, 2024)
        assert result[0]["rank"] == 1
        assert result[0]["team_id"] == 1
        assert result[1]["rank"] == 2

    def test_get_personal_ranking_with_month(self, mock_db):
        """按月获取个人排名"""
        from app.services.sales_target_service import SalesTargetService

        t1 = MagicMock()
        t1.user_id = 5
        t1.sales_target = Decimal("50000")
        t1.actual_sales = Decimal("55000")
        t1.completion_rate = Decimal("110.00")

        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = [t1]

        result = SalesTargetService.get_personal_ranking(mock_db, 2024, target_month=1)
        assert len(result) == 1
        assert result[0]["user_id"] == 5


# ─── get_completion_distribution ──────────────────────────────────────────────

class TestCompletionDistribution:
    def test_distribution_categorizes_correctly(self, mock_db):
        """完成率分布应正确分组"""
        from app.services.sales_target_service import SalesTargetService

        targets = []
        for rate in [10, 30, 50, 70, 90, 110]:
            t = MagicMock()
            t.completion_rate = Decimal(str(rate))
            targets.append(t)

        q = mock_db.query.return_value
        q.filter.return_value = q
        q.all.return_value = targets

        result = SalesTargetService.get_completion_distribution(mock_db, 2024)
        dist = {item["range_label"]: item["count"] for item in result["distribution"]}
        assert dist["0-20%"] == 1
        assert dist["20-40%"] == 1
        assert dist["40-60%"] == 1
        assert dist["60-80%"] == 1
        assert dist["80-100%"] == 1
        assert dist["100%+"] == 1

    def test_empty_distribution(self, mock_db):
        """空数据时所有分组为0"""
        from app.services.sales_target_service import SalesTargetService

        q = mock_db.query.return_value
        q.filter.return_value = q
        q.all.return_value = []

        result = SalesTargetService.get_completion_distribution(mock_db, 2024, target_month=3)
        dist = {item["range_label"]: item["count"] for item in result["distribution"]}
        assert all(v == 0 for v in dist.values())
