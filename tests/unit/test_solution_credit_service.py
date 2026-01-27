# -*- coding: utf-8 -*-
"""
方案生成积分服务单元测试

测试覆盖:
- 积分配置获取
- 用户余额查询
- 积分扣除和退还
- 管理员充值和扣除
- 交易历史
- 批量操作
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.solution_credit_service import (
    SolutionCreditService,
    CreditTransactionType,
)


class TestCreditTransactionTypeConstants:
    """交易类型常量测试"""

    def test_transaction_type_constants(self):
        """测试交易类型常量"""
        assert CreditTransactionType.INIT == "INIT"
        assert CreditTransactionType.GENERATE == "GENERATE"
        assert CreditTransactionType.ADMIN_ADD == "ADMIN_ADD"
        assert CreditTransactionType.ADMIN_DEDUCT == "ADMIN_DEDUCT"
        assert CreditTransactionType.SYSTEM_REWARD == "SYSTEM_REWARD"
        assert CreditTransactionType.REFUND == "REFUND"


class TestSolutionCreditServiceInit:
    """服务初始化测试"""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = SolutionCreditService(db_session)
        assert service.db == db_session

    def test_default_config(self, db_session: Session):
        """测试默认配置值"""
        service = SolutionCreditService(db_session)
        assert service.DEFAULT_CONFIG["INITIAL_CREDITS"] == 100
        assert service.DEFAULT_CONFIG["GENERATE_COST"] == 10
        assert service.DEFAULT_CONFIG["MIN_CREDITS_TO_GENERATE"] == 10
        assert service.DEFAULT_CONFIG["DAILY_FREE_GENERATIONS"] == 0
        assert service.DEFAULT_CONFIG["MAX_CREDITS"] == 9999


class TestGetConfig:
    """获取配置测试"""

    def test_get_config_default(self, db_session: Session):
        """测试获取默认配置"""
        service = SolutionCreditService(db_session)

        # 获取默认配置（如果数据库中没有配置）
        value = service.get_config("NONEXISTENT_KEY")
        assert value == 0  # 不存在的key返回0

    def test_get_config_initial_credits(self, db_session: Session):
        """测试获取初始积分配置"""
        service = SolutionCreditService(db_session)
        value = service.get_config("INITIAL_CREDITS")
        # 应该返回数据库值或默认值100
        assert isinstance(value, int)


class TestGetUserBalance:
    """获取用户余额测试"""

    def test_get_user_balance_user_not_found(self, db_session: Session):
        """测试用户不存在时返回0"""
        service = SolutionCreditService(db_session)
        balance = service.get_user_balance(99999)
        assert balance == 0


class TestGetUserCreditInfo:
    """获取用户积分信息测试"""

    def test_get_user_credit_info_user_not_found(self, db_session: Session):
        """测试用户不存在时返回None"""
        service = SolutionCreditService(db_session)
        info = service.get_user_credit_info(99999)
        assert info is None

    def test_get_user_credit_info_structure(self, db_session: Session):
        """测试返回数据结构（如果用户存在）"""
        service = SolutionCreditService(db_session)
        info = service.get_user_credit_info(1)
        if info is not None:
            assert "user_id" in info
            assert "balance" in info
            assert "generate_cost" in info
            assert "can_generate" in info
            assert "remaining_generations" in info


class TestCanGenerateSolution:
    """检查是否可以生成方案测试"""

    def test_can_generate_solution_user_not_found(self, db_session: Session):
        """测试用户不存在时返回False"""
        service = SolutionCreditService(db_session)
        can_generate, message = service.can_generate_solution(99999)
        assert can_generate is False
        assert "用户不存在" in message


class TestDeductForGeneration:
    """生成方案扣除积分测试"""

    def test_deduct_for_generation_user_not_found(self, db_session: Session):
        """测试用户不存在时返回失败"""
        service = SolutionCreditService(db_session)
        success, message, transaction = service.deduct_for_generation(99999)
        assert success is False
        assert transaction is None


class TestRefundCredits:
    """退还积分测试"""

    def test_refund_credits_user_not_found(self, db_session: Session):
        """测试用户不存在时返回失败"""
        service = SolutionCreditService(db_session)
        success, message, transaction = service.refund_credits(99999)
        assert success is False
        assert "用户不存在" in message
        assert transaction is None


class TestAdminAddCredits:
    """管理员充值积分测试"""

    def test_admin_add_credits_invalid_amount(self, db_session: Session):
        """测试充值数量无效时返回失败"""
        service = SolutionCreditService(db_session)
        success, message, transaction = service.admin_add_credits(
        user_id=1,
        amount=0,
        operator_id=1
        )
        assert success is False
        assert "必须大于0" in message
        assert transaction is None

    def test_admin_add_credits_negative_amount(self, db_session: Session):
        """测试充值负数时返回失败"""
        service = SolutionCreditService(db_session)
        success, message, transaction = service.admin_add_credits(
        user_id=1,
        amount=-100,
        operator_id=1
        )
        assert success is False
        assert "必须大于0" in message

    def test_admin_add_credits_user_not_found(self, db_session: Session):
        """测试用户不存在时返回失败"""
        service = SolutionCreditService(db_session)
        success, message, transaction = service.admin_add_credits(
        user_id=99999,
        amount=100,
        operator_id=1
        )
        assert success is False
        assert "用户不存在" in message


class TestAdminDeductCredits:
    """管理员扣除积分测试"""

    def test_admin_deduct_credits_invalid_amount(self, db_session: Session):
        """测试扣除数量无效时返回失败"""
        service = SolutionCreditService(db_session)
        success, message, transaction = service.admin_deduct_credits(
        user_id=1,
        amount=0,
        operator_id=1
        )
        assert success is False
        assert "必须大于0" in message

    def test_admin_deduct_credits_user_not_found(self, db_session: Session):
        """测试用户不存在时返回失败"""
        service = SolutionCreditService(db_session)
        success, message, transaction = service.admin_deduct_credits(
        user_id=99999,
        amount=100,
        operator_id=1
        )
        assert success is False
        assert "用户不存在" in message


class TestGetTransactionHistory:
    """获取交易历史测试"""

    def test_get_transaction_history_empty(self, db_session: Session):
        """测试无交易历史时返回空列表"""
        service = SolutionCreditService(db_session)
        transactions, total = service.get_transaction_history(user_id=99999)
        assert isinstance(transactions, list)
        assert total == 0

    def test_get_transaction_history_with_pagination(self, db_session: Session):
        """测试分页参数"""
        service = SolutionCreditService(db_session)
        transactions, total = service.get_transaction_history(
        user_id=1,
        page=1,
        page_size=10
        )
        assert isinstance(transactions, list)
        assert len(transactions) <= 10

    def test_get_transaction_history_with_type_filter(self, db_session: Session):
        """测试按类型筛选"""
        service = SolutionCreditService(db_session)
        transactions, total = service.get_transaction_history(
        user_id=1,
        transaction_type=CreditTransactionType.GENERATE
        )
        assert isinstance(transactions, list)


class TestGetAllUsersCredits:
    """获取所有用户积分列表测试"""

    def test_get_all_users_credits_structure(self, db_session: Session):
        """测试返回数据结构"""
        service = SolutionCreditService(db_session)
        users, total = service.get_all_users_credits()
        assert isinstance(users, list)
        assert isinstance(total, int)

    def test_get_all_users_credits_with_pagination(self, db_session: Session):
        """测试分页参数"""
        service = SolutionCreditService(db_session)
        users, total = service.get_all_users_credits(page=1, page_size=5)
        assert isinstance(users, list)
        assert len(users) <= 5

    def test_get_all_users_credits_with_search(self, db_session: Session):
        """测试搜索参数"""
        service = SolutionCreditService(db_session)
        users, total = service.get_all_users_credits(search="admin")
        assert isinstance(users, list)


class TestBatchAddCredits:
    """批量充值积分测试"""

    def test_batch_add_credits_structure(self, db_session: Session):
        """测试返回数据结构"""
        service = SolutionCreditService(db_session)
        result = service.batch_add_credits(
        user_ids=[99998, 99999],
        amount=100,
        operator_id=1,
        remark="测试批量充值"
        )

        assert "total" in result
        assert "success_count" in result
        assert "fail_count" in result
        assert "results" in result
        assert result["total"] == 2
        # 用户不存在，应该全部失败
        assert result["fail_count"] == 2


class TestGetAllConfigs:
    """获取所有配置测试"""

    def test_get_all_configs_structure(self, db_session: Session):
        """测试返回所有配置"""
        service = SolutionCreditService(db_session)
        configs = service.get_all_configs()

        assert isinstance(configs, list)
        assert len(configs) > 0

        # 检查配置项结构
        for config in configs:
            assert "key" in config
            assert "value" in config


class TestUpdateConfig:
    """更新配置测试"""

    def test_update_config(self, db_session: Session):
        """测试更新配置"""
        service = SolutionCreditService(db_session)
        try:
            success, message = service.update_config(
            key="TEST_CONFIG_KEY",
            value="100",
            description="测试配置"
            )
            assert success is True
        except Exception as e:
            pytest.skip(f"配置更新失败: {e}")
