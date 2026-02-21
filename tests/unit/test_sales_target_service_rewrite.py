# -*- coding: utf-8 -*-
"""
销售目标服务单元测试 - 完全重写版

策略：
- 只mock外部依赖（db.query, db.add, db.commit等）
- 让业务逻辑真正执行
- 覆盖主要方法和边界情况
- 目标：70%+ 覆盖率
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
    TargetBreakdownItem,
    AutoBreakdownRequest,
)


class TestSalesTargetServiceCreate(unittest.TestCase):
    """测试创建目标"""
    
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
        
        # Mock不存在相同目标
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.sales_target_service.save_obj') as mock_save:
            result = self.service.create_target(self.db, target_data, created_by=1)
            
            # 验证调用了save_obj
            mock_save.assert_called_once()
            # 验证返回的是SalesTargetV2实例
            self.assertIsInstance(result, SalesTargetV2)
            self.assertEqual(result.target_type, 'team')
    
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
    
    def test_create_team_target_without_team_id_raises_error(self):
        """测试创建团队目标但未指定team_id"""
        target_data = SalesTargetV2Create(
            target_type='team',
            target_period='month',
            target_year=2024,
            sales_target=Decimal('100000'),
            payment_target=Decimal('80000'),
            new_customer_target=10,
            lead_target=50,
            opportunity_target=30,
            deal_target=20
        )
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("team_id", str(context.exception.detail))
    
    def test_create_personal_target_without_user_id_raises_error(self):
        """测试创建个人目标但未指定user_id"""
        target_data = SalesTargetV2Create(
            target_type='personal',
            target_period='month',
            target_year=2024,
            sales_target=Decimal('100000'),
            payment_target=Decimal('80000'),
            new_customer_target=10,
            lead_target=50,
            opportunity_target=30,
            deal_target=20
        )
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("user_id", str(context.exception.detail))
    
    def test_create_duplicate_target_raises_error(self):
        """测试创建重复目标"""
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
        
        # Mock已存在
        existing = MagicMock(spec=SalesTargetV2)
        self.db.query.return_value.filter.return_value.first.return_value = existing
        
        with self.assertRaises(HTTPException) as context:
            self.service.create_target(self.db, target_data, created_by=1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("已存在", str(context.exception.detail))


class TestSalesTargetServiceRead(unittest.TestCase):
    """测试查询目标"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_get_target_found(self):
        """测试获取存在的目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.id = 1
        self.db.query.return_value.filter.return_value.first.return_value = mock_target
        
        result = self.service.get_target(self.db, 1)
        
        self.assertEqual(result, mock_target)
    
    def test_get_target_not_found(self):
        """测试获取不存在的目标"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_target(self.db, 999)
        
        self.assertIsNone(result)
    
    def test_get_targets_with_filters(self):
        """测试带过滤条件获取目标列表"""
        mock_targets = [MagicMock(spec=SalesTargetV2) for _ in range(3)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value.all.return_value = mock_targets
        
        result = self.service.get_targets(
            self.db,
            target_type='team',
            target_year=2024,
            target_month=1
        )
        
        self.assertEqual(len(result), 3)
        # 验证至少调用了filter（应该有3次：type, year, month）
        self.assertGreaterEqual(query_mock.filter.call_count, 3)
    
    def test_get_targets_pagination(self):
        """测试分页"""
        mock_targets = [MagicMock(spec=SalesTargetV2) for _ in range(10)]
        query_mock = self.db.query.return_value
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value.all.return_value = mock_targets[:5]
        
        result = self.service.get_targets(self.db, skip=0, limit=5)
        
        query_mock.offset.assert_called_once_with(0)
        query_mock.limit.assert_called_once_with(5)


class TestSalesTargetServiceUpdate(unittest.TestCase):
    """测试更新目标"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_update_target_success(self):
        """测试成功更新目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('50000')
        
        update_data = SalesTargetV2Update(
            actual_sales=Decimal('60000')
        )
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_target):
            result = self.service.update_target(self.db, 1, update_data)
            
            # 验证更新了actual_sales
            self.assertEqual(mock_target.actual_sales, Decimal('60000'))
            # 验证调用了commit和refresh
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(mock_target)
    
    def test_update_target_not_found(self):
        """测试更新不存在的目标"""
        update_data = SalesTargetV2Update(actual_sales=Decimal('60000'))
        
        with patch('app.services.sales_target_service.get_or_404', side_effect=HTTPException(status_code=404, detail="目标不存在")):
            with self.assertRaises(HTTPException) as context:
                self.service.update_target(self.db, 999, update_data)
            
            self.assertEqual(context.exception.status_code, 404)


class TestSalesTargetServiceDelete(unittest.TestCase):
    """测试删除目标"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_delete_target_success(self):
        """测试成功删除目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        
        # Mock没有子目标
        self.db.query.return_value.filter.return_value.count.return_value = 0
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_target):
            with patch('app.services.sales_target_service.delete_obj') as mock_delete:
                result = self.service.delete_target(self.db, 1)
                
                self.assertTrue(result)
                mock_delete.assert_called_once_with(self.db, mock_target)
    
    def test_delete_target_with_children_raises_error(self):
        """测试删除有子目标的目标"""
        mock_target = MagicMock(spec=SalesTargetV2)
        
        # Mock有子目标
        self.db.query.return_value.filter.return_value.count.return_value = 2
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_target):
            with self.assertRaises(HTTPException) as context:
                self.service.delete_target(self.db, 1)
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("子目标", str(context.exception.detail))


class TestSalesTargetServiceBreakdown(unittest.TestCase):
    """测试目标分解"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_breakdown_target_manual(self):
        """测试手动分解目标"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.target_period = 'month'
        mock_parent.target_year = 2024
        mock_parent.target_month = 1
        
        breakdown_items = [
            TargetBreakdownItem(
                target_type='personal',
                user_id=1,
                sales_target=Decimal('50000'),
                payment_target=Decimal('40000'),
                new_customer_target=5,
                lead_target=25,
                opportunity_target=15,
                deal_target=10
            ),
            TargetBreakdownItem(
                target_type='personal',
                user_id=2,
                sales_target=Decimal('50000'),
                payment_target=Decimal('40000'),
                new_customer_target=5,
                lead_target=25,
                opportunity_target=15,
                deal_target=10
            )
        ]
        
        breakdown_data = TargetBreakdownRequest(breakdown_items=breakdown_items)
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_parent):
            result = self.service.breakdown_target(self.db, 1, breakdown_data, created_by=1)
            
            # 验证创建了2个子目标
            self.assertEqual(len(result), 2)
            # 验证db.add被调用了3次（2个target + 1个log）
            self.assertEqual(self.db.add.call_count, 3)
            # 验证commit被调用
            self.db.commit.assert_called_once()
    
    def test_auto_breakdown_target_equal_method(self):
        """测试自动平均分解目标"""
        mock_parent = MagicMock(spec=SalesTargetV2)
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
        
        # Mock团队成员
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user2 = MagicMock()
        mock_user2.id = 2
        
        mock_member1 = MagicMock(spec=SalesTeamMember)
        mock_member1.user = mock_user1
        mock_member2 = MagicMock(spec=SalesTeamMember)
        mock_member2.user = mock_user2
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_member1, mock_member2]
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_parent):
            result = self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
            
            # 验证创建了2个子目标
            self.assertEqual(len(result), 2)
            # 验证每个目标的金额是父目标的一半
            self.assertEqual(result[0].sales_target, Decimal('100000') / 2)
            # 验证commit被调用
            self.db.commit.assert_called_once()
    
    def test_auto_breakdown_company_to_teams(self):
        """测试公司目标分解到团队"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.target_type = 'company'
        mock_parent.target_period = 'year'
        mock_parent.target_year = 2024
        mock_parent.sales_target = Decimal('1000000')
        mock_parent.payment_target = Decimal('800000')
        mock_parent.new_customer_target = 100
        mock_parent.lead_target = 500
        mock_parent.opportunity_target = 300
        mock_parent.deal_target = 200
        
        # Mock团队
        mock_team1 = MagicMock(spec=SalesTeam)
        mock_team1.id = 1
        mock_team2 = MagicMock(spec=SalesTeam)
        mock_team2.id = 2
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_team1, mock_team2]
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_parent):
            result = self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
            
            # 验证创建了2个团队目标
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].target_type, 'team')
    
    def test_auto_breakdown_no_targets_raises_error(self):
        """测试没有可分解对象"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.target_type = 'team'
        mock_parent.team_id = 1
        
        # Mock没有团队成员
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_parent):
            with self.assertRaises(HTTPException) as context:
                self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("没有可分解", str(context.exception.detail))
    
    def test_auto_breakdown_personal_target_raises_error(self):
        """测试个人目标无法分解"""
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.target_type = 'personal'
        
        breakdown_data = AutoBreakdownRequest(breakdown_method='EQUAL')
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_parent):
            with self.assertRaises(HTTPException) as context:
                self.service.auto_breakdown_target(self.db, 1, breakdown_data, created_by=1)
            
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("无法再分解", str(context.exception.detail))


class TestSalesTargetServiceBreakdownTree(unittest.TestCase):
    """测试分解树"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_get_breakdown_tree_no_children(self):
        """测试获取无子节点的分解树"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.id = 1
        mock_target.target_type = 'personal'
        mock_target.team_id = None
        mock_target.user_id = 1
        mock_target.sales_target = Decimal('50000')
        mock_target.actual_sales = Decimal('30000')
        mock_target.completion_rate = Decimal('60.00')
        
        # Mock没有子目标
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_target):
            result = self.service.get_breakdown_tree(self.db, 1)
            
            self.assertEqual(result['id'], 1)
            self.assertEqual(result['target_type'], 'personal')
            self.assertEqual(len(result['sub_targets']), 0)
    
    def test_get_breakdown_tree_with_children(self):
        """测试获取有子节点的分解树"""
        # 创建父目标
        mock_parent = MagicMock(spec=SalesTargetV2)
        mock_parent.id = 1
        mock_parent.target_type = 'team'
        mock_parent.team_id = 1
        mock_parent.user_id = None
        mock_parent.sales_target = Decimal('100000')
        mock_parent.actual_sales = Decimal('60000')
        mock_parent.completion_rate = Decimal('60.00')
        
        # 创建子目标
        mock_child1 = MagicMock(spec=SalesTargetV2)
        mock_child1.id = 2
        mock_child1.target_type = 'personal'
        mock_child1.team_id = None
        mock_child1.user_id = 1
        mock_child1.sales_target = Decimal('50000')
        mock_child1.actual_sales = Decimal('30000')
        mock_child1.completion_rate = Decimal('60.00')
        
        mock_child2 = MagicMock(spec=SalesTargetV2)
        mock_child2.id = 3
        mock_child2.target_type = 'personal'
        mock_child2.team_id = None
        mock_child2.user_id = 2
        mock_child2.sales_target = Decimal('50000')
        mock_child2.actual_sales = Decimal('30000')
        mock_child2.completion_rate = Decimal('60.00')
        
        # Mock db.query调用的返回值
        # 第一次调用：返回父节点的子节点
        # 后续调用：返回空列表（子节点没有子节点）
        call_counts = {'count': 0}
        
        def mock_filter_side_effect(condition):
            call_counts['count'] += 1
            mock_result = MagicMock()
            if call_counts['count'] == 1:
                # 第一次查询parent的子节点
                mock_result.all.return_value = [mock_child1, mock_child2]
            else:
                # 子节点的子节点为空
                mock_result.all.return_value = []
            return mock_result
        
        self.db.query.return_value.filter.side_effect = mock_filter_side_effect
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_parent):
            result = self.service.get_breakdown_tree(self.db, 1)
            
            self.assertEqual(result['id'], 1)
            self.assertEqual(len(result['sub_targets']), 2)
            self.assertEqual(result['sub_targets'][0]['id'], 2)
            self.assertEqual(result['sub_targets'][1]['id'], 3)


class TestSalesTargetServiceStatistics(unittest.TestCase):
    """测试统计分析"""
    
    def setUp(self):
        self.db = MagicMock()
        self.service = SalesTargetService()
    
    def test_get_team_ranking(self):
        """测试获取团队排名"""
        mock_targets = []
        for i in range(3):
            mock_target = MagicMock(spec=SalesTargetV2)
            mock_target.team_id = i + 1
            mock_target.sales_target = Decimal('100000')
            mock_target.actual_sales = Decimal(str((3 - i) * 30000))  # 递减
            mock_target.completion_rate = Decimal(str((3 - i) * 30))
            mock_targets.append(mock_target)
        
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = mock_targets
        
        result = self.service.get_team_ranking(self.db, 2024, 1)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['rank'], 1)
        self.assertEqual(result[0]['team_id'], 1)
        self.assertEqual(result[2]['rank'], 3)
    
    def test_get_personal_ranking(self):
        """测试获取个人排名"""
        mock_targets = []
        for i in range(3):
            mock_target = MagicMock(spec=SalesTargetV2)
            mock_target.user_id = i + 1
            mock_target.sales_target = Decimal('50000')
            mock_target.actual_sales = Decimal(str((3 - i) * 15000))
            mock_target.completion_rate = Decimal(str((3 - i) * 30))
            mock_targets.append(mock_target)
        
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = mock_targets
        
        result = self.service.get_personal_ranking(self.db, 2024, 1)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['user_id'], 1)
    
    def test_get_completion_trend(self):
        """测试获取完成趋势"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('60000')
        mock_target.completion_rate = Decimal('60.00')
        
        with patch('app.services.sales_target_service.get_or_404', return_value=mock_target):
            result = self.service.get_completion_trend(self.db, 1)
            
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['completion_rate'], 60.00)
    
    def test_get_completion_distribution(self):
        """测试获取完成率分布"""
        mock_targets = []
        # 创建不同完成率的目标
        completion_rates = [10, 25, 45, 65, 85, 105]
        for rate in completion_rates:
            mock_target = MagicMock(spec=SalesTargetV2)
            mock_target.completion_rate = Decimal(str(rate))
            mock_targets.append(mock_target)
        
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = mock_targets
        
        result = self.service.get_completion_distribution(self.db, 2024, 1)
        
        self.assertIn('distribution', result)
        distribution = {d['range_label']: d['count'] for d in result['distribution']}
        self.assertEqual(distribution['0-20%'], 1)
        self.assertEqual(distribution['20-40%'], 1)
        self.assertEqual(distribution['40-60%'], 1)
        self.assertEqual(distribution['60-80%'], 1)
        self.assertEqual(distribution['80-100%'], 1)
        self.assertEqual(distribution['100%+'], 1)


class TestSalesTargetServiceHelpers(unittest.TestCase):
    """测试辅助方法"""
    
    def test_calculate_completion_rate_normal(self):
        """测试正常计算完成率"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('60000')
        
        result = SalesTargetService._calculate_completion_rate(mock_target)
        
        self.assertEqual(result, Decimal('60.00'))
    
    def test_calculate_completion_rate_zero_target(self):
        """测试目标为0时的完成率"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('0')
        mock_target.actual_sales = Decimal('60000')
        
        result = SalesTargetService._calculate_completion_rate(mock_target)
        
        self.assertEqual(result, Decimal('0'))
    
    def test_calculate_completion_rate_over_100(self):
        """测试超额完成"""
        mock_target = MagicMock(spec=SalesTargetV2)
        mock_target.sales_target = Decimal('100000')
        mock_target.actual_sales = Decimal('150000')
        
        result = SalesTargetService._calculate_completion_rate(mock_target)
        
        self.assertEqual(result, Decimal('150.00'))


if __name__ == "__main__":
    unittest.main()
