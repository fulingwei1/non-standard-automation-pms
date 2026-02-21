# -*- coding: utf-8 -*-
"""
方案生成积分服务增强测试

测试覆盖目标: 70%+
测试用例数量: 25-35个
Mock策略: 使用 unittest.mock.MagicMock 和 patch Mock所有数据库操作
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, call

from app.services.solution_credit_service import (
    SolutionCreditService,
    CreditTransactionType
)
from app.models.user import SolutionCreditConfig, SolutionCreditTransaction, User


class TestSolutionCreditService(unittest.TestCase):
    """方案生成积分服务测试类"""

    def setUp(self):
        """测试前置准备"""
        self.mock_db = MagicMock()
        self.service = SolutionCreditService(self.mock_db)

    def tearDown(self):
        """测试后置清理"""
        self.mock_db.reset_mock()

    # ==================== get_config 测试 ====================
    
    def test_get_config_from_database(self):
        """测试从数据库获取配置"""
        # 准备 mock 配置对象
        mock_config = MagicMock()
        mock_config.config_value = "100"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_config
        
        # 执行测试
        result = self.service.get_config("INITIAL_CREDITS")
        
        # 验证结果
        self.assertEqual(result, 100)
        self.mock_db.query.assert_called_once_with(SolutionCreditConfig)

    def test_get_config_use_default_when_not_in_db(self):
        """测试当数据库无配置时使用默认值"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        result = self.service.get_config("GENERATE_COST")
        
        # 验证返回默认值
        self.assertEqual(result, 10)

    def test_get_config_unknown_key_returns_zero(self):
        """测试未知配置键返回0"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        result = self.service.get_config("UNKNOWN_KEY")
        
        # 验证返回0
        self.assertEqual(result, 0)

    # ==================== get_user_balance 测试 ====================

    def test_get_user_balance_success(self):
        """测试成功获取用户余额"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 500
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_user
        
        # 执行测试
        result = self.service.get_user_balance(1)
        
        # 验证结果
        self.assertEqual(result, 500)

    def test_get_user_balance_user_not_found(self):
        """测试用户不存在时返回0"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        result = self.service.get_user_balance(999)
        
        # 验证返回0
        self.assertEqual(result, 0)

    def test_get_user_balance_none_credits(self):
        """测试用户积分为None时返回0"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = None
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_user
        
        # 执行测试
        result = self.service.get_user_balance(1)
        
        # 验证返回0
        self.assertEqual(result, 0)

    # ==================== get_user_credit_info 测试 ====================

    def test_get_user_credit_info_success(self):
        """测试成功获取用户完整积分信息"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.solution_credits = 100
        mock_user.credits_updated_at = datetime(2024, 1, 1)
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "10"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config]
        
        # 执行测试
        result = self.service.get_user_credit_info(1)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result["user_id"], 1)
        self.assertEqual(result["balance"], 100)
        self.assertEqual(result["generate_cost"], 10)
        self.assertTrue(result["can_generate"])
        self.assertEqual(result["remaining_generations"], 10)

    def test_get_user_credit_info_user_not_found(self):
        """测试用户不存在时返回None"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        result = self.service.get_user_credit_info(999)
        
        # 验证返回None
        self.assertIsNone(result)

    def test_get_user_credit_info_zero_generate_cost(self):
        """测试生成成本为0时的处理"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 100
        mock_user.credits_updated_at = datetime(2024, 1, 1)
        
        # Mock 配置返回0
        mock_config = MagicMock()
        mock_config.config_value = "0"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config]
        
        # 执行测试
        result = self.service.get_user_credit_info(1)
        
        # 验证剩余生成次数为0
        self.assertEqual(result["remaining_generations"], 0)

    # ==================== can_generate_solution 测试 ====================

    def test_can_generate_solution_success(self):
        """测试可以生成方案"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 100
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "10"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config, mock_config]
        
        # 执行测试
        can_generate, message = self.service.can_generate_solution(1)
        
        # 验证结果
        self.assertTrue(can_generate)
        self.assertIn("可以生成", message)

    def test_can_generate_solution_user_not_found(self):
        """测试用户不存在"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        can_generate, message = self.service.can_generate_solution(999)
        
        # 验证结果
        self.assertFalse(can_generate)
        self.assertEqual(message, "用户不存在")

    def test_can_generate_solution_insufficient_credits(self):
        """测试积分不足"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 5
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "10"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config, mock_config]
        
        # 执行测试
        can_generate, message = self.service.can_generate_solution(1)
        
        # 验证结果
        self.assertFalse(can_generate)
        self.assertIn("积分不足", message)

    # ==================== deduct_for_generation 测试 ====================

    @patch('app.services.solution_credit_service.save_obj')
    @patch('app.services.solution_credit_service.datetime')
    def test_deduct_for_generation_success(self, mock_datetime, mock_save_obj):
        """测试成功扣除积分"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.solution_credits = 100
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "10"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [
            mock_user,  # can_generate_solution 第一次查询
            mock_config,  # get_config MIN_CREDITS
            mock_config,  # get_config GENERATE_COST
            mock_user,  # deduct_for_generation 查询用户
            mock_config,  # get_config GENERATE_COST
        ]
        
        # 执行测试
        success, message, transaction = self.service.deduct_for_generation(
            user_id=1,
            related_type="solution",
            related_id=123,
            remark="测试扣除"
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn("扣除 10 积分", message)
        self.assertIsNotNone(transaction)
        self.assertEqual(mock_user.solution_credits, 90)
        self.assertEqual(mock_user.credits_updated_at, mock_now)
        mock_save_obj.assert_called_once()

    def test_deduct_for_generation_insufficient_credits(self):
        """测试扣除时积分不足"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 5
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "10"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config, mock_config]
        
        # 执行测试
        success, message, transaction = self.service.deduct_for_generation(1)
        
        # 验证结果
        self.assertFalse(success)
        self.assertIn("积分不足", message)
        self.assertIsNone(transaction)

    # ==================== refund_credits 测试 ====================

    @patch('app.services.solution_credit_service.save_obj')
    @patch('app.services.solution_credit_service.datetime')
    def test_refund_credits_success(self, mock_datetime, mock_save_obj):
        """测试成功退还积分"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 90
        
        # Mock 配置
        mock_config_generate = MagicMock()
        mock_config_generate.config_value = "10"
        mock_config_max = MagicMock()
        mock_config_max.config_value = "9999"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [
            mock_user,
            mock_config_generate,
            mock_config_max
        ]
        
        # 执行测试
        success, message, transaction = self.service.refund_credits(
            user_id=1,
            remark="生成失败退还"
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn("退还 10 积分", message)
        self.assertEqual(mock_user.solution_credits, 100)
        mock_save_obj.assert_called_once()

    def test_refund_credits_user_not_found(self):
        """测试退还积分时用户不存在"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        success, message, transaction = self.service.refund_credits(999)
        
        # 验证结果
        self.assertFalse(success)
        self.assertEqual(message, "用户不存在")
        self.assertIsNone(transaction)

    @patch('app.services.solution_credit_service.save_obj')
    def test_refund_credits_at_max_limit(self, mock_save_obj):
        """测试已达积分上限时退还"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 9999
        
        # Mock 配置
        mock_config_max = MagicMock()
        mock_config_max.config_value = "9999"
        mock_config_generate = MagicMock()
        mock_config_generate.config_value = "10"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [
            mock_user,
            mock_config_generate,
            mock_config_max
        ]
        
        # 执行测试
        success, message, transaction = self.service.refund_credits(1)
        
        # 验证结果
        self.assertFalse(success)
        self.assertIn("已达到积分上限", message)
        self.assertIsNone(transaction)

    @patch('app.services.solution_credit_service.save_obj')
    @patch('app.services.solution_credit_service.datetime')
    def test_refund_credits_custom_amount(self, mock_datetime, mock_save_obj):
        """测试自定义退还数量"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 50
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "9999"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config]
        
        # 执行测试
        success, message, transaction = self.service.refund_credits(
            user_id=1,
            amount=20
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn("退还 20 积分", message)
        self.assertEqual(mock_user.solution_credits, 70)

    # ==================== admin_add_credits 测试 ====================

    @patch('app.services.solution_credit_service.save_obj')
    @patch('app.services.solution_credit_service.datetime')
    def test_admin_add_credits_success(self, mock_datetime, mock_save_obj):
        """测试管理员成功充值"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 50
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "9999"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config]
        
        # 执行测试
        success, message, transaction = self.service.admin_add_credits(
            user_id=1,
            amount=100,
            operator_id=2,
            remark="测试充值"
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn("充值成功", message)
        self.assertEqual(mock_user.solution_credits, 150)
        mock_save_obj.assert_called_once()

    def test_admin_add_credits_invalid_amount(self):
        """测试充值数量无效（<=0）"""
        # 执行测试
        success, message, transaction = self.service.admin_add_credits(
            user_id=1,
            amount=0,
            operator_id=2
        )
        
        # 验证结果
        self.assertFalse(success)
        self.assertEqual(message, "充值数量必须大于0")
        self.assertIsNone(transaction)

    def test_admin_add_credits_user_not_found(self):
        """测试充值时用户不存在"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        success, message, transaction = self.service.admin_add_credits(
            user_id=999,
            amount=100,
            operator_id=2
        )
        
        # 验证结果
        self.assertFalse(success)
        self.assertEqual(message, "用户不存在")
        self.assertIsNone(transaction)

    @patch('app.services.solution_credit_service.save_obj')
    def test_admin_add_credits_exceed_max_limit(self, mock_save_obj):
        """测试充值超过上限"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 9990
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "9999"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [mock_user, mock_config]
        
        # 执行测试 - 尝试充值100，但只能充值9（达到9999上限）
        success, message, transaction = self.service.admin_add_credits(
            user_id=1,
            amount=100,
            operator_id=2
        )
        
        # 验证结果 - 应该成功但只充值实际可充值的数量
        self.assertTrue(success)
        self.assertIn("增加 9 积分", message)
        self.assertEqual(mock_user.solution_credits, 9999)

    # ==================== admin_deduct_credits 测试 ====================

    @patch('app.services.solution_credit_service.save_obj')
    @patch('app.services.solution_credit_service.datetime')
    def test_admin_deduct_credits_success(self, mock_datetime, mock_save_obj):
        """测试管理员成功扣除积分"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 150
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_user
        
        # 执行测试
        success, message, transaction = self.service.admin_deduct_credits(
            user_id=1,
            amount=50,
            operator_id=2,
            remark="测试扣除"
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn("扣除成功", message)
        self.assertEqual(mock_user.solution_credits, 100)
        mock_save_obj.assert_called_once()

    def test_admin_deduct_credits_invalid_amount(self):
        """测试扣除数量无效（<=0）"""
        # 执行测试
        success, message, transaction = self.service.admin_deduct_credits(
            user_id=1,
            amount=-10,
            operator_id=2
        )
        
        # 验证结果
        self.assertFalse(success)
        self.assertEqual(message, "扣除数量必须大于0")

    def test_admin_deduct_credits_user_not_found(self):
        """测试扣除时用户不存在"""
        # Mock 数据库返回 None
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        success, message, transaction = self.service.admin_deduct_credits(
            user_id=999,
            amount=50,
            operator_id=2
        )
        
        # 验证结果
        self.assertFalse(success)
        self.assertEqual(message, "用户不存在")

    @patch('app.services.solution_credit_service.save_obj')
    def test_admin_deduct_credits_zero_balance(self, mock_save_obj):
        """测试用户积分已为0时扣除"""
        # 准备 mock 用户
        mock_user = MagicMock()
        mock_user.solution_credits = 0
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_user
        
        # 执行测试
        success, message, transaction = self.service.admin_deduct_credits(
            user_id=1,
            amount=50,
            operator_id=2
        )
        
        # 验证结果
        self.assertFalse(success)
        self.assertEqual(message, "用户积分已为0")

    # ==================== get_transaction_history 测试 ====================

    @patch('app.services.solution_credit_service.get_pagination_params')
    @patch('app.services.solution_credit_service.apply_pagination')
    def test_get_transaction_history_success(self, mock_apply_pagination, mock_get_pagination):
        """测试成功获取交易历史"""
        # Mock pagination
        mock_pagination = MagicMock()
        mock_pagination.offset = 0
        mock_pagination.limit = 20
        mock_get_pagination.return_value = mock_pagination
        
        # 准备 mock 交易记录
        mock_transactions = [MagicMock(), MagicMock()]
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.count.return_value = 2
        mock_filter.order_by.return_value = mock_filter
        mock_apply_pagination.return_value = mock_filter
        mock_filter.all.return_value = mock_transactions
        
        # 执行测试
        transactions, total = self.service.get_transaction_history(
            user_id=1,
            page=1,
            page_size=20
        )
        
        # 验证结果
        self.assertEqual(len(transactions), 2)
        self.assertEqual(total, 2)

    @patch('app.services.solution_credit_service.get_pagination_params')
    @patch('app.services.solution_credit_service.apply_pagination')
    def test_get_transaction_history_with_type_filter(self, mock_apply_pagination, mock_get_pagination):
        """测试按类型过滤交易历史"""
        # Mock pagination
        mock_pagination = MagicMock()
        mock_pagination.offset = 0
        mock_pagination.limit = 20
        mock_get_pagination.return_value = mock_pagination
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.filter.return_value = mock_filter
        mock_filter.count.return_value = 1
        mock_filter.order_by.return_value = mock_filter
        mock_apply_pagination.return_value = mock_filter
        mock_filter.all.return_value = [MagicMock()]
        
        # 执行测试
        transactions, total = self.service.get_transaction_history(
            user_id=1,
            transaction_type=CreditTransactionType.GENERATE
        )
        
        # 验证调用了两次 filter（user_id 和 transaction_type）
        self.assertEqual(mock_filter.filter.call_count, 1)

    # ==================== get_all_users_credits 测试 ====================

    @patch('app.services.solution_credit_service.get_pagination_params')
    @patch('app.services.solution_credit_service.apply_pagination')
    @patch('app.services.solution_credit_service.apply_keyword_filter')
    def test_get_all_users_credits_success(self, mock_keyword_filter, mock_apply_pagination, mock_get_pagination):
        """测试成功获取所有用户积分列表"""
        # Mock pagination
        mock_pagination = MagicMock()
        mock_pagination.offset = 0
        mock_pagination.limit = 20
        mock_get_pagination.return_value = mock_pagination
        
        # 准备 mock 用户
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.username = "user1"
        mock_user1.real_name = "用户1"
        mock_user1.employee_no = "E001"
        mock_user1.department = "技术部"
        mock_user1.solution_credits = 100
        mock_user1.credits_updated_at = datetime(2024, 1, 1)
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "10"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_keyword_filter.return_value = mock_filter
        mock_filter.count.return_value = 1
        mock_apply_pagination.return_value = mock_filter
        mock_filter.all.return_value = [mock_user1]
        
        # Mock 第二次查询（get_config）
        mock_query.filter.return_value.first.return_value = mock_config
        
        # 执行测试
        users, total = self.service.get_all_users_credits()
        
        # 验证结果
        self.assertEqual(len(users), 1)
        self.assertEqual(total, 1)
        self.assertEqual(users[0]["user_id"], 1)
        self.assertEqual(users[0]["balance"], 100)
        self.assertEqual(users[0]["remaining_generations"], 10)

    # ==================== batch_add_credits 测试 ====================

    @patch('app.services.solution_credit_service.save_obj')
    @patch('app.services.solution_credit_service.datetime')
    def test_batch_add_credits_all_success(self, mock_datetime, mock_save_obj):
        """测试批量充值全部成功"""
        # Mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # 准备 mock 用户
        mock_user1 = MagicMock()
        mock_user1.solution_credits = 50
        mock_user2 = MagicMock()
        mock_user2.solution_credits = 60
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "9999"
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [
            mock_user1, mock_config,
            mock_user2, mock_config
        ]
        
        # 执行测试
        result = self.service.batch_add_credits(
            user_ids=[1, 2],
            amount=50,
            operator_id=3,
            remark="批量充值"
        )
        
        # 验证结果
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["fail_count"], 0)

    def test_batch_add_credits_partial_failure(self):
        """测试批量充值部分失败"""
        # 准备 mock 用户
        mock_user1 = MagicMock()
        mock_user1.solution_credits = 50
        
        # Mock 配置
        mock_config = MagicMock()
        mock_config.config_value = "9999"
        
        # Mock 数据库查询 - 第一个成功，第二个用户不存在
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.side_effect = [
            mock_user1, mock_config,
            None
        ]
        
        # 执行测试
        result = self.service.batch_add_credits(
            user_ids=[1, 999],
            amount=50,
            operator_id=3
        )
        
        # 验证结果
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["fail_count"], 1)

    # ==================== update_config 测试 ====================

    def test_update_config_existing_key(self):
        """测试更新已存在的配置"""
        # 准备 mock 配置
        mock_config = MagicMock()
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_config
        
        # 执行测试
        success, message = self.service.update_config(
            key="GENERATE_COST",
            value="20",
            description="生成成本"
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn("已更新", message)
        self.assertEqual(mock_config.config_value, "20")
        self.assertEqual(mock_config.description, "生成成本")
        self.mock_db.commit.assert_called_once()

    def test_update_config_new_key(self):
        """测试创建新配置"""
        # Mock 数据库返回 None（配置不存在）
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        # 执行测试
        success, message = self.service.update_config(
            key="NEW_CONFIG",
            value="100"
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn("已更新", message)
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    # ==================== get_all_configs 测试 ====================

    def test_get_all_configs_success(self):
        """测试成功获取所有配置"""
        # 准备 mock 配置
        mock_config1 = MagicMock()
        mock_config1.config_key = "INITIAL_CREDITS"
        mock_config1.config_value = "200"
        mock_config1.description = "初始积分"
        mock_config1.is_active = True
        
        # Mock 数据库查询
        mock_query = self.mock_db.query.return_value
        mock_query.all.return_value = [mock_config1]
        
        # 执行测试
        result = self.service.get_all_configs()
        
        # 验证结果
        self.assertEqual(len(result), 5)  # DEFAULT_CONFIG 有5个键
        # 验证第一个配置（从数据库获取的）
        initial_credits_config = next(c for c in result if c["key"] == "INITIAL_CREDITS")
        self.assertEqual(initial_credits_config["value"], "200")
        self.assertTrue(initial_credits_config["is_active"])


if __name__ == "__main__":
    unittest.main()
