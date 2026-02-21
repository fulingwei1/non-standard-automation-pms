# -*- coding: utf-8 -*-
"""
销售目标服务增强测试
覆盖所有核心方法和边界条件
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException

from app.services.sales_target_service import SalesTargetService
from app.models.sales.target_v2 import SalesTargetV2, TargetBreakdownLog
from app.models.sales.team import SalesTeam, SalesTeamMember
from app.schemas.sales_target import (
    SalesTargetV2Create,
    SalesTargetV2Update,
    TargetBreakdownRequest,
    AutoBreakdownRequest,
)


class TestSalesTargetServiceCreate(unittest.TestCase):
    """测试创建目标功能"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_create_team_target_success(self):
        """测试成功创建团队目标"""
        target_data = SalesTargetV2Create(
            target_type='team',
            target_period='month',
            target_year=2024,
            target_month=1,
            team_id=1,
            sales_target=Decimal('100000'),
            payment_target=Decimal('80000'),
            new_customer_target=10,
            lead_target=50,
            opportunity_target=30,
            deal_target=20
        )
        
        # Mock查询不存在
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.sales_target_service.save_obj') as mock_save:
            result = self.service.create_target(self.db, target_data, created_by=1)
            
            mock_save.assert_called_once()
            self.assertIsInstance(result, SalesTargetV2)
            self.assertEqual(result.target_type, 'team')
            self.assertEqual(result.team_id, 1)
    
    def test_create_personal_target_success(self):
        """测试成功创建个人目标"""
        target_data = SalesTargetV2Create(
            target_type='personal',
            target_period='month',
            target_year=2024,
            target_month=1,
            user_id=1,
            sales_target=Decimal('50000'),
            payment_target=Decimal('40000'),
            new_customer_target=5,
            lead_target=25,
            opportunity_target=15,
            deal_target=10
        )
        
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.sales_target_service.save_obj') as mock_save:
            result = self.service.create_target(self.db, target_data, created_by=1)
            
            mock_save.assert_called_once()
            self.assertEqual(result.target_type, 'personal')
            self.assertEqual(result.user_id, 1)
    
    def test_create_team_target_without_team_id(self):
        """测试创建团队目标但未指定team_id"""
        target_data = SalesTargetV2Create(
            target_type='team',
            target_period='month',
            target_year=2024,
            sales_target=Decimal('100000')
        )
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("team_id", str(context.exception.detail))
    
    def test_create_personal_target_without_user_id(self):
        """测试创建个人目标但未指定user_id"""
        target_data = SalesTargetV2Create(
            target_type='personal',
            target_period='month',
            target_year=2024,
            sales_target=Decimal('50000')
        )
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("user_id", str(context.exception.detail))
    
    def test_create_duplicate_target(self):
        """测试创建重复的目标"""
        target_data = SalesTargetV2Create(
            target_type='team',
            target_period='month',
            target_year=2024,
            target_month=1,
            team_id=1,
            sales_target=Decimal('100000')
        )
        
        # Mock已存在的目标
        existing_target = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = existing_target
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("已存在", str(context.exception.detail))


class TestSalesTargetServiceRead(unittest.TestCase):
    """测试读取目标功能"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_get_target_exists(self):
        """测试获取存在的目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_target
        
        result = self.service.get_target(self.db, 1)
        
        self.assertEqual(result.id, 1)
    
    def test_get_target_not_exists(self):
        """测试获取不存在的目标"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_target(self.db, 999)
        
        self.assertIsNone(result)
    
    def test_get_targets_no_filters(self):
        """测试获取目标列表（无过滤）"""
        mock_targets = [MagicMock(spec=SalesTargetV2) for _ in range(5)]
        query_mock = self.db.query.return_value
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db)
        
        self.assertEqual(len(result), 5)
    
    def test_get_targets_with_type_filter(self):
        """测试按类型过滤目标"""
        mock_targets = [MagicMock(spec=SalesTargetV2)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db, target_type='team')
        
        self.assertEqual(len(result), 1)
    
    def test_get_targets_with_period_filter(self):
        """测试按周期过滤目标"""
        mock_targets = [MagicMock(spec=SalesTargetV2)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db, target_period='month')
        
        self.assertEqual(len(result), 1)
    
    def test_get_targets_with_year_filter(self):
        """测试按年份过滤目标"""
        mock_targets = [MagicMock(spec=SalesTargetV2)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db, target_year=2024)
        
        self.assertEqual(len(result), 1)
    
    def test_get_targets_with_month_filter(self):
        """测试按月份过滤目标"""
        mock_targets = [MagicMock(spec=SalesTargetV2)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db, target_month=1)
        
        self.assertEqual(len(result), 1)
    
    def test_get_targets_with_team_filter(self):
        """测试按团队过滤目标"""
        mock_targets = [MagicMock(spec=SalesTargetV2)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db, team_id=1)
        
        self.assertEqual(len(result), 1)
    
    def test_get_targets_with_user_filter(self):
        """测试按用户过滤目标"""
        mock_targets = [MagicMock(spec=SalesTargetV2)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db, user_id=1)
        
        self.assertEqual(len(result), 1)
    
    def test_get_targets_with_pagination(self):
        """测试分页参数"""
        mock_targets = [MagicMock(spec=SalesTargetV2) for _ in range(10)]
        query_mock = self.db.query.return_value
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(self.db, skip=10, limit=10)
        
        self.assertEqual(len(result), 10)


class TestSalesTargetServiceUpdate(unittest.TestCase):
    """测试更新目标功能"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_update_target_success(self, mock_get_or_404):
        """测试成功更新目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('50000')
        mock_get_or_404.return_value = mock_target
        
        update_data = SalesTargetV2Update(
            sales_target=Decimal('120000')
        )
        
        with patch.object(self.service, '_calculate_completion_rate', return_value=Decimal('41.67')):
            result = self.service.update_target(self.db, 1, update_data)
            
            self.assertEqual(result.sales_target, Decimal('120000'))
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(mock_target)
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_update_target_not_found(self, mock_get_or_404):
        """测试更新不存在的目标"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="目标不存在")
        
        update_data = SalesTargetV2Update(sales_target=Decimal('120000'))
        
        with self.assertRaises(HTTPException) as context:
            self.service.update_target(self.db, 999, update_data)
        
        self.assertEqual(context.exception.status_code, 404)
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_update_target_partial_update(self, mock_get_or_404):
        """测试部分字段更新"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('50000')
        mock_target.new_customer_target = 10
        mock_get_or_404.return_value = mock_target
        
        update_data = SalesTargetV2Update(new_customer_target=15)
        
        with patch.object(self.service, '_calculate_completion_rate', return_value=Decimal('50.00')):
            result = self.service.update_target(self.db, 1, update_data)
            
            self.assertEqual(result.new_customer_target, 15)


class TestSalesTargetServiceDelete(unittest.TestCase):
    """测试删除目标功能"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    @patch('app.services.sales_target_service.get_or_404')
    @patch('app.services.sales_target_service.delete_obj')
    def test_delete_target_success(self, mock_delete_obj, mock_get_or_404):
        """测试成功删除目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_get_or_404.return_value = mock_target
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        result = self.service.delete_target(self.db, 1)
        
        self.assertTrue(result)
        mock_delete_obj.assert_called_once_with(self.db, mock_target)
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_delete_target_with_sub_targets(self, mock_get_or_404):
        """测试删除有子目标的目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_get_or_404.return_value = mock_target
        self.db.query.return_value.filter.return_value.count.return_value = 3
        
        with self.assertRaises(HTTPException) as context:
            self.service.delete_target(self.db, 1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("子目标", str(context.exception.detail))
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_delete_target_not_found(self, mock_get_or_404):
        """测试删除不存在的目标"""
        mock_get_or_404.side_effect = HTTPException(status_code=404, detail="目标不存在")
        
        with self.assertRaises(HTTPException) as context:
            self.service.delete_target(self.db, 999)
        
        self.assertEqual(context.exception.status_code, 404)


class TestSalesTargetServiceBreakdown(unittest.TestCase):
    """测试目标分解功能"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_manual_breakdown_success(self, mock_get_or_404):
        """测试手动分解目标成功"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.id = 1
        mock_parent.target_period = 'month'
        mock_parent.target_year = 2024
        mock_parent.target_month = 1
        mock_get_or_404.return_value = mock_parent
        
        from app.schemas.sales_target import TargetBreakdownItem
        breakdown_data = TargetBreakdownRequest(
            breakdown_items=[
                TargetBreakdownItem(
                    target_type='personal',
                    user_id=1,
                    sales_target=Decimal('50000'),
                    payment_target=Decimal('40000'),
                    new_customer_target=5,
                    lead_target=25,
                    opportunity_target=15,
                    deal_target=10
                )
            ]
        )
        
        result = self.service.breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(len(result), 1)
        self.db.commit.assert_called_once()
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_manual_breakdown_multiple_items(self, mock_get_or_404):
        """测试手动分解多个子目标"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.id = 1
        mock_parent.target_period = 'month'
        mock_parent.target_year = 2024
        mock_parent.target_month = 1
        mock_get_or_404.return_value = mock_parent
        
        from app.schemas.sales_target import TargetBreakdownItem
        breakdown_data = TargetBreakdownRequest(
            breakdown_items=[
                TargetBreakdownItem(
                    target_type='personal',
                    user_id=i,
                    sales_target=Decimal('30000'),
                    payment_target=Decimal('24000'),
                    new_customer_target=3,
                    lead_target=15,
                    opportunity_target=10,
                    deal_target=6
                ) for i in range(1, 4)
            ]
        )
        
        result = self.service.breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(len(result), 3)
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_company_to_teams(self, mock_get_or_404):
        """测试自动分解公司目标到团队"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.id = 1
        mock_parent.target_type = 'company'
        mock_parent.target_period = 'month'
        mock_parent.target_year = 2024
        mock_parent.target_month = 1
        mock_parent.sales_target = Decimal('300000')
        mock_parent.payment_target = Decimal('240000')
        mock_parent.new_customer_target = 30
        mock_parent.lead_target = 150
        mock_parent.opportunity_target = 90
        mock_parent.deal_target = 60
        mock_get_or_404.return_value = mock_parent
        
        # Mock团队查询
        mock_teams = [MagicMock(id=i) for i in range(1, 4)]
        self.db.query.return_value.filter.return_value.all.return_value = mock_teams
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        result = self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(len(result), 3)
        self.db.commit.assert_called_once()
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_team_to_personal(self, mock_get_or_404):
        """测试自动分解团队目标到个人"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.id = 1
        mock_parent.target_type = 'team'
        mock_parent.team_id = 1
        mock_parent.target_period = 'month'
        mock_parent.target_year = 2024
        mock_parent.target_month = 1
        mock_parent.sales_target = Decimal('100000')
        mock_parent.payment_target = Decimal('80000')
        mock_parent.new_customer_target = 10
        mock_parent.lead_target = 50
        mock_parent.opportunity_target = 30
        mock_parent.deal_target = 20
        mock_get_or_404.return_value = mock_parent
        
        # Mock团队成员查询
        mock_members = [MagicMock(user=MagicMock(id=i)) for i in range(1, 3)]
        self.db.query.return_value.filter.return_value.all.return_value = mock_members
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        result = self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(len(result), 2)
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_personal_target_fails(self, mock_get_or_404):
        """测试个人目标无法自动分解"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.target_type = 'personal'
        mock_get_or_404.return_value = mock_parent
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        with self.assertRaises(HTTPException) as context:
            self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("无法再分解", str(context.exception.detail))
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_auto_breakdown_no_targets(self, mock_get_or_404):
        """测试没有可分解对象"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.target_type = 'company'
        mock_get_or_404.return_value = mock_parent
        
        # Mock空团队列表
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        with self.assertRaises(HTTPException) as context:
            self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("没有可分解的对象", str(context.exception.detail))


class TestSalesTargetServiceBreakdownTree(unittest.TestCase):
    """测试目标分解树功能"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_get_breakdown_tree_no_children(self, mock_get_or_404):
        """测试获取没有子目标的分解树"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.id = 1
        mock_target.target_type = 'personal'
        mock_target.team_id = None
        mock_target.user_id = 1
        mock_target.sales_target = Decimal('50000')
        mock_target.actual_sales = Decimal('25000')
        mock_target.completion_rate = Decimal('50.00')
        mock_get_or_404.return_value = mock_target
        
        # Mock没有子目标
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.get_breakdown_tree(self.db, 1)
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(len(result['sub_targets']), 0)
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_get_breakdown_tree_with_children(self, mock_get_or_404):
        """测试获取有子目标的分解树"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.id = 1
        mock_parent.target_type = 'team'
        mock_parent.team_id = 1
        mock_parent.user_id = None
        mock_parent.sales_target = Decimal('100000')
        mock_parent.actual_sales = Decimal('50000')
        mock_parent.completion_rate = Decimal('50.00')
        
        mock_child = MagicMock(spec=SalesTargetV2)
        mock_child.id = 2
        mock_child.target_type = 'personal'
        mock_child.team_id = None
        mock_child.user_id = 1
        mock_child.sales_target = Decimal('50000')
        mock_child.actual_sales = Decimal('25000')
        mock_child.completion_rate = Decimal('50.00')
        
        mock_get_or_404.return_value = mock_parent
        
        # 第一次查询返回一个子目标，第二次返回空
        self.db.query.return_value.filter.return_value.all.side_effect = [
            [mock_child],
            []
        ]
        
        result = self.service.get_breakdown_tree(self.db, 1)
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(len(result['sub_targets']), 1)
        self.assertEqual(result['sub_targets'][0]['id'], 2)


class TestSalesTargetServiceStatistics(unittest.TestCase):
    """测试统计分析功能"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_get_team_ranking(self):
        """测试获取团队排名"""
        mock_targets = [
            MagicMock(
                team_id=i,
                sales_target=Decimal('100000'),
                actual_sales=Decimal(str(100000 - i * 10000)),
                completion_rate=Decimal(str(100 - i * 10))
            )
            for i in range(1, 4)
        ]
        
        query_mock = self.db.query.return_value.filter.return_value
        query_mock.order_by.return_value.all.return_value = mock_targets
        
        result = self.service.get_team_ranking(self.db, 2024)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['rank'], 1)
        self.assertEqual(result[0]['team_id'], 1)
    
    def test_get_team_ranking_with_month(self):
        """测试获取指定月份的团队排名"""
        mock_targets = [
            MagicMock(
                team_id=1,
                sales_target=Decimal('100000'),
                actual_sales=Decimal('90000'),
                completion_rate=Decimal('90.00')
            )
        ]
        
        query_mock = self.db.query.return_value.filter.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = mock_targets
        
        result = self.service.get_team_ranking(self.db, 2024, target_month=1)
        
        self.assertEqual(len(result), 1)
    
    def test_get_personal_ranking(self):
        """测试获取个人排名"""
        mock_targets = [
            MagicMock(
                user_id=i,
                sales_target=Decimal('50000'),
                actual_sales=Decimal(str(50000 - i * 5000)),
                completion_rate=Decimal(str(100 - i * 10))
            )
            for i in range(1, 4)
        ]
        
        query_mock = self.db.query.return_value.filter.return_value
        query_mock.order_by.return_value.all.return_value = mock_targets
        
        result = self.service.get_personal_ranking(self.db, 2024)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['rank'], 1)
        self.assertEqual(result[0]['user_id'], 1)
    
    def test_get_personal_ranking_with_month(self):
        """测试获取指定月份的个人排名"""
        mock_targets = [
            MagicMock(
                user_id=1,
                sales_target=Decimal('50000'),
                actual_sales=Decimal('45000'),
                completion_rate=Decimal('90.00')
            )
        ]
        
        query_mock = self.db.query.return_value.filter.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = mock_targets
        
        result = self.service.get_personal_ranking(self.db, 2024, target_month=1)
        
        self.assertEqual(len(result), 1)
    
    @patch('app.services.sales_target_service.get_or_404')
    def test_get_completion_trend(self, mock_get_or_404):
        """测试获取完成趋势"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.completion_rate = Decimal('75.50')
        mock_target.actual_sales = Decimal('75500')
        mock_target.sales_target = Decimal('100000')
        mock_get_or_404.return_value = mock_target
        
        result = self.service.get_completion_trend(self.db, 1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['completion_rate'], 75.50)
    
    def test_get_completion_distribution_all_ranges(self):
        """测试完成率分布（所有区间）"""
        mock_targets = [
            MagicMock(completion_rate=Decimal('10.00')),  # 0-20%
            MagicMock(completion_rate=Decimal('30.00')),  # 20-40%
            MagicMock(completion_rate=Decimal('50.00')),  # 40-60%
            MagicMock(completion_rate=Decimal('70.00')),  # 60-80%
            MagicMock(completion_rate=Decimal('90.00')),  # 80-100%
            MagicMock(completion_rate=Decimal('110.00')),  # 100%+
        ]
        
        query_mock = self.db.query.return_value.filter.return_value
        query_mock.all.return_value = mock_targets
        
        result = self.service.get_completion_distribution(self.db, 2024)
        
        distribution_dict = {item['range_label']: item['count'] for item in result['distribution']}
        self.assertEqual(distribution_dict['0-20%'], 1)
        self.assertEqual(distribution_dict['20-40%'], 1)
        self.assertEqual(distribution_dict['40-60%'], 1)
        self.assertEqual(distribution_dict['60-80%'], 1)
        self.assertEqual(distribution_dict['80-100%'], 1)
        self.assertEqual(distribution_dict['100%+'], 1)
    
    def test_get_completion_distribution_with_month(self):
        """测试指定月份的完成率分布"""
        mock_targets = [
            MagicMock(completion_rate=Decimal('50.00')),
            MagicMock(completion_rate=Decimal('75.00')),
        ]
        
        query_mock = self.db.query.return_value.filter.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = mock_targets
        
        result = self.service.get_completion_distribution(self.db, 2024, target_month=1)
        
        self.assertIn('2024-1', result['period'])


class TestSalesTargetServiceHelpers(unittest.TestCase):
    """测试辅助方法"""
    
    def test_calculate_completion_rate_normal(self):
        """测试正常计算完成率"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('75000')
        
        result = SalesTargetService._calculate_completion_rate(mock_target)
        
        self.assertEqual(result, Decimal('75.00'))
    
    def test_calculate_completion_rate_zero_target(self):
        """测试目标为0时的完成率"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('0')
        mock_target.actual_sales = Decimal('50000')
        
        result = SalesTargetService._calculate_completion_rate(mock_target)
        
        self.assertEqual(result, Decimal('0'))
    
    def test_calculate_completion_rate_over_100(self):
        """测试完成率超过100%"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('150000')
        
        result = SalesTargetService._calculate_completion_rate(mock_target)
        
        self.assertEqual(result, Decimal('150.00'))
    
    def test_calculate_completion_rate_precision(self):
        """测试完成率计算精度"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('300000')
        mock_target.actual_sales = Decimal('100000')
        
        result = SalesTargetService._calculate_completion_rate(mock_target)
        
        self.assertEqual(result, Decimal('33.33'))


if __name__ == '__main__':
    unittest.main()
