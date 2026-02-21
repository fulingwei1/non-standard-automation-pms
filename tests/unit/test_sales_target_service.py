# -*- coding: utf-8 -*-
"""
销售目标服务单元测试

测试策略:
1. 只mock外部依赖(db.query, db.add, db.commit等)
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException

from app.services.sales_target_service import SalesTargetService
from app.models.sales.target_v2 import SalesTargetV2, TargetBreakdownLog
from app.models.sales.team import SalesTeam, SalesTeamMember
from app.schemas.sales_target import (
    SalesTargetV2Create,
    SalesTargetV2Update,
    TargetBreakdownRequest,
    AutoBreakdownRequest,
    TargetBreakdownItem,
)


class TestSalesTargetServiceCreate(unittest.TestCase):
    """测试创建目标方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    def test_create_team_target_success(self):
        """测试成功创建团队目标"""
        target_data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
            sales_target=Decimal('100000'),
            payment_target=Decimal('80000'),
            new_customer_target=10,
        )
        
        # Mock query返回None表示不存在
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.create_target(self.db, target_data, created_by=1)
        
        # 验证save_obj被调用
        self.assertIsNotNone(result)
        self.assertEqual(result.target_type, "team")
        self.assertEqual(result.team_id, 1)
        self.assertEqual(result.sales_target, Decimal('100000'))

    def test_create_personal_target_success(self):
        """测试成功创建个人目标"""
        target_data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="personal",
            user_id=1,
            sales_target=Decimal('50000'),
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(result.target_type, "personal")
        self.assertEqual(result.user_id, 1)

    def test_create_team_target_without_team_id(self):
        """测试创建团队目标但未提供team_id"""
        target_data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=None,
            sales_target=Decimal('100000'),
        )
        
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("必须指定team_id", ctx.exception.detail)

    def test_create_personal_target_without_user_id(self):
        """测试创建个人目标但未提供user_id"""
        target_data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="personal",
            user_id=None,
            sales_target=Decimal('50000'),
        )
        
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("必须指定user_id", ctx.exception.detail)

    def test_create_duplicate_target(self):
        """测试创建重复目标"""
        target_data = SalesTargetV2Create(
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
            sales_target=Decimal('100000'),
        )
        
        # Mock已存在的目标
        existing_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
        )
        self.db.query.return_value.filter.return_value.first.return_value = existing_target
        
        with self.assertRaises(HTTPException) as ctx:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("目标已存在", ctx.exception.detail)


class TestSalesTargetServiceGet(unittest.TestCase):
    """测试获取目标方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    def test_get_target_success(self):
        """测试成功获取目标"""
        mock_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
            sales_target=Decimal('100000'),
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_target
        
        result = self.service.get_target(self.db, 1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.sales_target, Decimal('100000'))

    def test_get_target_not_found(self):
        """测试获取不存在的目标"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_target(self.db, 999)
        
        self.assertIsNone(result)

    def test_get_targets_with_filters(self):
        """测试带过滤条件获取目标列表"""
        mock_targets = [
            SalesTargetV2(id=1, target_type="team", target_year=2024, target_month=1),
            SalesTargetV2(id=2, target_type="team", target_year=2024, target_month=1),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_targets
        
        self.db.query.return_value = mock_query
        
        results = self.service.get_targets(
            self.db,
            target_type="team",
            target_year=2024,
            target_month=1
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, 1)

    def test_get_targets_with_pagination(self):
        """测试分页获取目标列表"""
        mock_targets = [SalesTargetV2(id=i) for i in range(1, 11)]
        
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_targets
        
        self.db.query.return_value = mock_query
        
        results = self.service.get_targets(self.db, skip=10, limit=10)
        
        # 验证分页参数
        mock_query.offset.assert_called_with(10)
        mock_query.limit.assert_called_with(10)

    def test_get_targets_empty_result(self):
        """测试获取空结果"""
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        results = self.service.get_targets(self.db)
        
        self.assertEqual(len(results), 0)


class TestSalesTargetServiceUpdate(unittest.TestCase):
    """测试更新目标方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    @patch('app.services.sales_target_service.get_or_404')
    def test_update_target_success(self, mock_get_or_404):
        """测试成功更新目标"""
        mock_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
            sales_target=Decimal('100000'),
            actual_sales=Decimal('50000'),
            completion_rate=Decimal('0'),
        )
        mock_get_or_404.return_value = mock_target
        
        update_data = SalesTargetV2Update(
            actual_sales=Decimal('60000'),
            sales_target=Decimal('120000'),
        )
        
        result = self.service.update_target(self.db, 1, update_data)
        
        self.assertEqual(result.actual_sales, Decimal('60000'))
        self.assertEqual(result.sales_target, Decimal('120000'))
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()

    @patch('app.services.sales_target_service.get_or_404')
    def test_update_target_recalculate_completion_rate(self, mock_get_or_404):
        """测试更新目标时重新计算完成率"""
        # 创建真实的对象来让业务逻辑执行
        mock_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="team",
            team_id=1,
            sales_target=Decimal('100000'),
            actual_sales=Decimal('0'),
            completion_rate=Decimal('0'),
        )
        mock_get_or_404.return_value = mock_target
        
        update_data = SalesTargetV2Update(
            actual_sales=Decimal('50000'),
        )
        
        result = self.service.update_target(self.db, 1, update_data)
        
        # 验证actual_sales被更新
        self.assertEqual(mock_target.actual_sales, Decimal('50000'))
        # 验证完成率被计算（50000/100000 = 50%）
        self.assertEqual(mock_target.completion_rate, Decimal('50.00'))

    @patch('app.services.sales_target_service.get_or_404')
    def test_update_target_not_found(self, mock_get_or_404):
        """测试更新不存在的目标"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="目标不存在")
        
        update_data = SalesTargetV2Update(actual_sales=Decimal('60000'))
        
        with self.assertRaises(HTTPException) as ctx:
            self.service.update_target(self.db, 999, update_data)
        
        self.assertEqual(ctx.exception.status_code, 404)


class TestSalesTargetServiceDelete(unittest.TestCase):
    """测试删除目标方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    @patch('app.services.sales_target_service.delete_obj')
    @patch('app.services.sales_target_service.get_or_404')
    def test_delete_target_success(self, mock_get_or_404, mock_delete_obj):
        """测试成功删除目标"""
        mock_target = SalesTargetV2(id=1, target_type="team")
        mock_get_or_404.return_value = mock_target
        
        # Mock没有子目标
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        result = self.service.delete_target(self.db, 1)
        
        self.assertTrue(result)
        mock_delete_obj.assert_called_once_with(self.db, mock_target)

    @patch('app.services.sales_target_service.get_or_404')
    def test_delete_target_with_sub_targets(self, mock_get_or_404):
        """测试删除有子目标的目标"""
        mock_target = SalesTargetV2(id=1, target_type="team")
        mock_get_or_404.return_value = mock_target
        
        # Mock有2个子目标
        self.db.query.return_value.filter.return_value.count.return_value = 2
        
        with self.assertRaises(HTTPException) as ctx:
            self.service.delete_target(self.db, 1)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("存在子目标", ctx.exception.detail)


class TestSalesTargetServiceBreakdown(unittest.TestCase):
    """测试目标分解方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    @patch('app.services.sales_target_service.get_or_404')
    def test_breakdown_target_manual(self, mock_get_or_404):
        """测试手动分解目标"""
        parent_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="company",
            sales_target=Decimal('1000000'),
        )
        mock_get_or_404.return_value = parent_target
        
        breakdown_data = TargetBreakdownRequest(
            breakdown_items=[
                TargetBreakdownItem(
                    target_type="team",
                    team_id=1,
                    sales_target=Decimal('400000'),
                ),
                TargetBreakdownItem(
                    target_type="team",
                    team_id=2,
                    sales_target=Decimal('600000'),
                ),
            ]
        )
        
        result = self.service.breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].target_type, "team")
        self.assertEqual(result[0].parent_target_id, 1)
        # 验证db.add被调用3次（2个目标 + 1个日志）
        self.assertEqual(self.db.add.call_count, 3)
        self.db.commit.assert_called_once()

    @patch('app.services.sales_target_service.get_or_404')
    def test_breakdown_target_creates_log(self, mock_get_or_404):
        """测试分解目标时创建日志"""
        parent_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_type="company",
            sales_target=Decimal('1000000'),
        )
        mock_get_or_404.return_value = parent_target
        
        breakdown_data = TargetBreakdownRequest(
            breakdown_items=[
                TargetBreakdownItem(
                    target_type="team",
                    team_id=1,
                    sales_target=Decimal('1000000'),
                ),
            ]
        )
        
        self.service.breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        # 验证日志被创建
        add_calls = self.db.add.call_args_list
        # 最后一个add调用应该是日志
        log_call = add_calls[-1]
        log_obj = log_call[0][0]
        self.assertIsInstance(log_obj, TargetBreakdownLog)
        self.assertEqual(log_obj.parent_target_id, 1)
        self.assertEqual(log_obj.breakdown_type, 'MANUAL')


class TestSalesTargetServiceAutoBreakdown(unittest.TestCase):
    """测试自动分解目标方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_company_to_teams(self, mock_get_or_404):
        """测试公司目标自动分解到团队"""
        # 创建真实对象,让target_type属性正常工作
        parent_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_quarter=None,
            target_type="company",  # 这个很重要,必须是真实对象才能正确读取
            team_id=None,
            user_id=None,
            sales_target=Decimal('1000000'),
            payment_target=Decimal('800000'),
            new_customer_target=100,
            lead_target=500,
            opportunity_target=200,
            deal_target=50,
        )
        mock_get_or_404.return_value = parent_target
        
        # Mock团队数据 
        mock_team1 = MagicMock()
        mock_team1.id = 1
        mock_team2 = MagicMock()
        mock_team2.id = 2
        
        mock_teams = [mock_team1, mock_team2]
        self.db.query.return_value.filter.return_value.all.return_value = mock_teams
        
        breakdown_data = AutoBreakdownRequest(breakdown_method="EQUAL")
        
        result = self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(len(result), 2)
        # 平均分配：1000000 / 2 = 500000
        self.assertEqual(result[0].sales_target, Decimal('500000'))
        self.assertEqual(result[0].target_type, "team")

    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_team_to_members(self, mock_get_or_404):
        """测试团队目标自动分解到成员"""
        # 创建真实对象
        parent_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_quarter=None,
            target_type="team",  # 必须是真实对象
            team_id=1,
            user_id=None,
            sales_target=Decimal('500000'),
            payment_target=Decimal('400000'),
            new_customer_target=50,
            lead_target=250,
            opportunity_target=100,
            deal_target=25,
        )
        mock_get_or_404.return_value = parent_target
        
        # Mock团队成员
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user2 = MagicMock()
        mock_user2.id = 2
        
        mock_members = [
            MagicMock(user=mock_user1, team_id=1, is_active=True),
            MagicMock(user=mock_user2, team_id=1, is_active=True),
        ]
        self.db.query.return_value.filter.return_value.all.return_value = mock_members
        
        breakdown_data = AutoBreakdownRequest(breakdown_method="EQUAL")
        
        result = self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(len(result), 2)
        # 平均分配：500000 / 2 = 250000
        self.assertEqual(result[0].sales_target, Decimal('250000'))
        self.assertEqual(result[0].target_type, "personal")

    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_personal_target_fails(self, mock_get_or_404):
        """测试个人目标无法分解"""
        # 创建真实对象
        parent_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_quarter=None,
            target_type="personal",
            team_id=None,
            user_id=1,
        )
        mock_get_or_404.return_value = parent_target
        
        breakdown_data = AutoBreakdownRequest(breakdown_method="EQUAL")
        
        with self.assertRaises(HTTPException) as ctx:
            self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("无法再分解", ctx.exception.detail)

    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_no_targets(self, mock_get_or_404):
        """测试没有可分解对象"""
        # 创建真实对象
        parent_target = SalesTargetV2(
            id=1,
            target_period="month",
            target_year=2024,
            target_month=1,
            target_quarter=None,
            target_type="company",
            team_id=None,
            user_id=None,
        )
        mock_get_or_404.return_value = parent_target
        
        # Mock空团队列表
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        breakdown_data = AutoBreakdownRequest(breakdown_method="EQUAL")
        
        with self.assertRaises(HTTPException) as ctx:
            self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("没有可分解的对象", ctx.exception.detail)


class TestSalesTargetServiceBreakdownTree(unittest.TestCase):
    """测试获取分解树方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    @patch('app.services.sales_target_service.get_or_404')
    def test_get_breakdown_tree_single_level(self, mock_get_or_404):
        """测试单层分解树"""
        # 创建真实对象而不是Mock,让业务逻辑真正执行
        root_target = SalesTargetV2(
            id=1,
            target_type="company",
            team_id=None,
            user_id=None,
            sales_target=Decimal('1000000'),
            actual_sales=Decimal('500000'),
            completion_rate=Decimal('50.00'),
        )
        mock_get_or_404.return_value = root_target
        
        # 没有子目标
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.get_breakdown_tree(self.db, 1)
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['target_type'], "company")
        self.assertEqual(result['sales_target'], 1000000.0)
        self.assertEqual(len(result['sub_targets']), 0)

    @patch('app.services.sales_target_service.get_or_404')
    def test_get_breakdown_tree_multi_level(self, mock_get_or_404):
        """测试多层分解树"""
        # 创建真实对象
        root_target = SalesTargetV2(
            id=1,
            target_type="company",
            team_id=None,
            user_id=None,
            sales_target=Decimal('1000000'),
            actual_sales=Decimal('500000'),
            completion_rate=Decimal('50.00'),
        )
        mock_get_or_404.return_value = root_target
        
        # Mock子目标（第一次调用返回2个团队目标，后续调用返回空）
        sub_target1 = SalesTargetV2(
            id=2,
            target_type="team",
            team_id=1,
            user_id=None,
            sales_target=Decimal('500000'),
            actual_sales=Decimal('250000'),
            completion_rate=Decimal('50.00'),
        )
        sub_target2 = SalesTargetV2(
            id=3,
            target_type="team",
            team_id=2,
            user_id=None,
            sales_target=Decimal('500000'),
            actual_sales=Decimal('250000'),
            completion_rate=Decimal('50.00'),
        )
        
        # 使用列表记录调用次数
        call_tracker = {'count': 0}
        
        def mock_query_side_effect(*args):
            call_tracker['count'] += 1
            mock_result = MagicMock()
            # 第一次返回2个子目标，后续返回空
            if call_tracker['count'] == 1:
                mock_result.filter.return_value.all.return_value = [sub_target1, sub_target2]
            else:
                mock_result.filter.return_value.all.return_value = []
            return mock_result
        
        self.db.query.side_effect = mock_query_side_effect
        
        result = self.service.get_breakdown_tree(self.db, 1)
        
        self.assertEqual(len(result['sub_targets']), 2)
        self.assertEqual(result['sub_targets'][0]['id'], 2)


class TestSalesTargetServiceRanking(unittest.TestCase):
    """测试排名方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    def test_get_team_ranking(self):
        """测试获取团队排名"""
        mock_targets = [
            SalesTargetV2(
                id=1,
                team_id=1,
                target_type="team",
                sales_target=Decimal('100000'),
                actual_sales=Decimal('90000'),
                completion_rate=Decimal('90.00'),
            ),
            SalesTargetV2(
                id=2,
                team_id=2,
                target_type="team",
                sales_target=Decimal('100000'),
                actual_sales=Decimal('80000'),
                completion_rate=Decimal('80.00'),
            ),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_targets
        
        self.db.query.return_value = mock_query
        
        result = self.service.get_team_ranking(self.db, 2024, 1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['rank'], 1)
        self.assertEqual(result[0]['team_id'], 1)
        self.assertEqual(result[0]['completion_rate'], 90.0)

    def test_get_team_ranking_without_month(self):
        """测试获取年度团队排名"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        result = self.service.get_team_ranking(self.db, 2024)
        
        # 验证没有调用月份过滤
        self.assertEqual(len(result), 0)

    def test_get_personal_ranking(self):
        """测试获取个人排名"""
        mock_targets = [
            SalesTargetV2(
                id=1,
                user_id=1,
                target_type="personal",
                sales_target=Decimal('50000'),
                actual_sales=Decimal('45000'),
                completion_rate=Decimal('90.00'),
            ),
            SalesTargetV2(
                id=2,
                user_id=2,
                target_type="personal",
                sales_target=Decimal('50000'),
                actual_sales=Decimal('40000'),
                completion_rate=Decimal('80.00'),
            ),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_targets
        
        self.db.query.return_value = mock_query
        
        result = self.service.get_personal_ranking(self.db, 2024, 1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['rank'], 1)
        self.assertEqual(result[0]['user_id'], 1)


class TestSalesTargetServiceStatistics(unittest.TestCase):
    """测试统计方法"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    @patch('app.services.sales_target_service.get_or_404')
    def test_get_completion_trend(self, mock_get_or_404):
        """测试获取完成趋势"""
        # 创建真实对象
        mock_target = SalesTargetV2(
            id=1,
            sales_target=Decimal('100000'),
            actual_sales=Decimal('50000'),
            completion_rate=Decimal('50.00'),
        )
        mock_get_or_404.return_value = mock_target
        
        result = self.service.get_completion_trend(self.db, 1)
        
        self.assertEqual(len(result), 1)
        self.assertIn('date', result[0])
        # 验证返回的是Decimal转换后的float
        self.assertEqual(float(result[0]['completion_rate']), 50.0)
        self.assertEqual(float(result[0]['actual_sales']), 50000.0)
        self.assertEqual(float(result[0]['target_sales']), 100000.0)

    def test_get_completion_distribution(self):
        """测试获取完成率分布"""
        mock_targets = [
            SalesTargetV2(completion_rate=Decimal('10.00')),  # 0-20%
            SalesTargetV2(completion_rate=Decimal('30.00')),  # 20-40%
            SalesTargetV2(completion_rate=Decimal('50.00')),  # 40-60%
            SalesTargetV2(completion_rate=Decimal('70.00')),  # 60-80%
            SalesTargetV2(completion_rate=Decimal('90.00')),  # 80-100%
            SalesTargetV2(completion_rate=Decimal('110.00')), # 100%+
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_targets
        
        self.db.query.return_value = mock_query
        
        result = self.service.get_completion_distribution(self.db, 2024, 1)
        
        self.assertEqual(result['period'], '2024-1')
        distribution_dict = {item['range_label']: item['count'] for item in result['distribution']}
        self.assertEqual(distribution_dict['0-20%'], 1)
        self.assertEqual(distribution_dict['20-40%'], 1)
        self.assertEqual(distribution_dict['40-60%'], 1)
        self.assertEqual(distribution_dict['60-80%'], 1)
        self.assertEqual(distribution_dict['80-100%'], 1)
        self.assertEqual(distribution_dict['100%+'], 1)

    def test_get_completion_distribution_without_month(self):
        """测试获取年度完成率分布"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        result = self.service.get_completion_distribution(self.db, 2024)
        
        self.assertEqual(result['period'], '2024-全年')


class TestSalesTargetServiceHelpers(unittest.TestCase):
    """测试辅助方法"""

    def setUp(self):
        self.service = SalesTargetService()

    def test_calculate_completion_rate_normal(self):
        """测试正常计算完成率"""
        target = SalesTargetV2(
            sales_target=Decimal('100000'),
            actual_sales=Decimal('50000'),
        )
        
        result = self.service._calculate_completion_rate(target)
        
        self.assertEqual(result, Decimal('50.00'))

    def test_calculate_completion_rate_over_100(self):
        """测试完成率超过100%"""
        target = SalesTargetV2(
            sales_target=Decimal('100000'),
            actual_sales=Decimal('120000'),
        )
        
        result = self.service._calculate_completion_rate(target)
        
        self.assertEqual(result, Decimal('120.00'))

    def test_calculate_completion_rate_zero_target(self):
        """测试目标为0的完成率"""
        target = SalesTargetV2(
            sales_target=Decimal('0'),
            actual_sales=Decimal('50000'),
        )
        
        result = self.service._calculate_completion_rate(target)
        
        self.assertEqual(result, Decimal('0'))

    def test_calculate_completion_rate_zero_actual(self):
        """测试实际值为0的完成率"""
        target = SalesTargetV2(
            sales_target=Decimal('100000'),
            actual_sales=Decimal('0'),
        )
        
        result = self.service._calculate_completion_rate(target)
        
        self.assertEqual(result, Decimal('0.00'))

    def test_calculate_completion_rate_precision(self):
        """测试完成率精度（保留2位小数）"""
        target = SalesTargetV2(
            sales_target=Decimal('100000'),
            actual_sales=Decimal('33333.33'),
        )
        
        result = self.service._calculate_completion_rate(target)
        
        # 33333.33 / 100000 * 100 = 33.33333... 应该保留为 33.33
        self.assertEqual(result, Decimal('33.33'))


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()

    def test_get_targets_all_filters(self):
        """测试使用所有过滤条件"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        self.service.get_targets(
            self.db,
            skip=0,
            limit=50,
            target_type="team",
            target_period="month",
            target_year=2024,
            target_month=1,
            team_id=1,
            user_id=1,
        )
        
        # 验证所有过滤条件都被应用（6次filter调用）
        self.assertEqual(mock_query.filter.call_count, 6)

    def test_get_completion_distribution_empty_targets(self):
        """测试空目标的完成率分布"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        self.db.query.return_value = mock_query
        
        result = self.service.get_completion_distribution(self.db, 2024, 1)
        
        # 验证所有分布桶为0
        for item in result['distribution']:
            self.assertEqual(item['count'], 0)

    def test_get_completion_distribution_boundary_values(self):
        """测试完成率边界值分布"""
        mock_targets = [
            SalesTargetV2(completion_rate=Decimal('0.00')),   # 边界：0
            SalesTargetV2(completion_rate=Decimal('20.00')),  # 边界：20
            SalesTargetV2(completion_rate=Decimal('40.00')),  # 边界：40
            SalesTargetV2(completion_rate=Decimal('60.00')),  # 边界：60
            SalesTargetV2(completion_rate=Decimal('80.00')),  # 边界：80
            SalesTargetV2(completion_rate=Decimal('100.00')), # 边界：100
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_targets
        
        self.db.query.return_value = mock_query
        
        result = self.service.get_completion_distribution(self.db, 2024)
        
        distribution_dict = {item['range_label']: item['count'] for item in result['distribution']}
        # 边界值应该归入下一个区间
        self.assertEqual(distribution_dict['0-20%'], 1)   # 0
        self.assertEqual(distribution_dict['20-40%'], 1)  # 20
        self.assertEqual(distribution_dict['40-60%'], 1)  # 40
        self.assertEqual(distribution_dict['60-80%'], 1)  # 60
        self.assertEqual(distribution_dict['80-100%'], 1) # 80
        self.assertEqual(distribution_dict['100%+'], 1)   # 100


if __name__ == "__main__":
    unittest.main()
