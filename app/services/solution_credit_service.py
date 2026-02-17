# -*- coding: utf-8 -*-
"""
方案生成积分服务

提供积分查询、扣除、充值等功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.models.user import SolutionCreditConfig, SolutionCreditTransaction, User
from app.utils.db_helpers import save_obj


class CreditTransactionType:
    """积分交易类型"""
    INIT = "INIT"                    # 初始化积分
    GENERATE = "GENERATE"            # 生成方案扣除
    ADMIN_ADD = "ADMIN_ADD"          # 管理员充值
    ADMIN_DEDUCT = "ADMIN_DEDUCT"    # 管理员扣除
    SYSTEM_REWARD = "SYSTEM_REWARD"  # 系统奖励
    REFUND = "REFUND"                # 退还


class SolutionCreditService:
    """方案生成积分服务类"""

    # 默认配置值（当数据库中没有配置时使用）
    DEFAULT_CONFIG = {
        "INITIAL_CREDITS": 100,
        "GENERATE_COST": 10,
        "MIN_CREDITS_TO_GENERATE": 10,
        "DAILY_FREE_GENERATIONS": 0,
        "MAX_CREDITS": 9999,
    }

    def __init__(self, db: Session):
        self.db = db

    def get_config(self, key: str) -> int:
        """获取配置值"""
        config = self.db.query(SolutionCreditConfig).filter(
            SolutionCreditConfig.config_key == key,
            SolutionCreditConfig.is_active
        ).first()

        if config:
            return int(config.config_value)
        return self.DEFAULT_CONFIG.get(key, 0)

    def get_user_balance(self, user_id: int) -> int:
        """获取用户当前积分余额"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0
        return user.solution_credits or 0

    def get_user_credit_info(self, user_id: int) -> Dict[str, Any]:
        """获取用户完整积分信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        generate_cost = self.get_config("GENERATE_COST")
        balance = user.solution_credits or 0

        return {
            "user_id": user_id,
            "balance": balance,
            "generate_cost": generate_cost,
            "can_generate": balance >= generate_cost,
            "remaining_generations": balance // generate_cost if generate_cost > 0 else 0,
            "last_updated": user.credits_updated_at,
        }

    def can_generate_solution(self, user_id: int) -> Tuple[bool, str]:
        """
        检查用户是否可以生成方案

        Returns:
            Tuple[bool, str]: (是否可以生成, 原因说明)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在"

        balance = user.solution_credits or 0
        min_credits = self.get_config("MIN_CREDITS_TO_GENERATE")
        generate_cost = self.get_config("GENERATE_COST")

        if balance < min_credits:
            return False, f"积分不足，当前余额 {balance}，生成方案需要 {generate_cost} 积分"

        return True, f"可以生成，当前余额 {balance} 积分"

    def deduct_for_generation(
        self,
        user_id: int,
        related_type: str = None,
        related_id: int = None,
        remark: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[bool, str, Optional[SolutionCreditTransaction]]:
        """
        生成方案时扣除积分

        Returns:
            Tuple[bool, str, Optional[SolutionCreditTransaction]]:
                (是否成功, 消息, 交易记录)
        """
        # 先检查是否可以生成
        can_generate, message = self.can_generate_solution(user_id)
        if not can_generate:
            return False, message, None

        user = self.db.query(User).filter(User.id == user_id).first()
        generate_cost = self.get_config("GENERATE_COST")
        balance_before = user.solution_credits
        balance_after = balance_before - generate_cost

        # 创建交易记录
        transaction = SolutionCreditTransaction(
            user_id=user_id,
            transaction_type=CreditTransactionType.GENERATE,
            amount=-generate_cost,
            balance_before=balance_before,
            balance_after=balance_after,
            related_type=related_type,
            related_id=related_id,
            remark=remark or "生成测试方案",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 更新用户余额
        user.solution_credits = balance_after
        user.credits_updated_at = datetime.now()

        save_obj(self.db, transaction)

        return True, f"扣除 {generate_cost} 积分，剩余 {balance_after} 积分", transaction

    def refund_credits(
        self,
        user_id: int,
        amount: int = None,
        related_type: str = None,
        related_id: int = None,
        remark: str = None,
    ) -> Tuple[bool, str, Optional[SolutionCreditTransaction]]:
        """
        退还积分（生成失败时调用）

        Args:
            amount: 退还数量，默认为生成消耗的积分数
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在", None

        if amount is None:
            amount = self.get_config("GENERATE_COST")

        max_credits = self.get_config("MAX_CREDITS")
        balance_before = user.solution_credits
        balance_after = min(balance_before + amount, max_credits)
        actual_amount = balance_after - balance_before

        if actual_amount <= 0:
            return False, "已达到积分上限，无法退还", None

        # 创建交易记录
        transaction = SolutionCreditTransaction(
            user_id=user_id,
            transaction_type=CreditTransactionType.REFUND,
            amount=actual_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            related_type=related_type,
            related_id=related_id,
            remark=remark or "方案生成失败退还",
        )

        # 更新用户余额
        user.solution_credits = balance_after
        user.credits_updated_at = datetime.now()

        save_obj(self.db, transaction)

        return True, f"退还 {actual_amount} 积分，当前余额 {balance_after} 积分", transaction

    def admin_add_credits(
        self,
        user_id: int,
        amount: int,
        operator_id: int,
        remark: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[bool, str, Optional[SolutionCreditTransaction]]:
        """
        管理员充值积分

        Args:
            user_id: 目标用户ID
            amount: 充值数量（正数）
            operator_id: 操作人（管理员）ID
            remark: 充值备注
        """
        if amount <= 0:
            return False, "充值数量必须大于0", None

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在", None

        max_credits = self.get_config("MAX_CREDITS")
        balance_before = user.solution_credits or 0
        balance_after = min(balance_before + amount, max_credits)
        actual_amount = balance_after - balance_before

        if actual_amount <= 0:
            return False, f"用户已达积分上限 {max_credits}", None

        # 创建交易记录
        transaction = SolutionCreditTransaction(
            user_id=user_id,
            transaction_type=CreditTransactionType.ADMIN_ADD,
            amount=actual_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            operator_id=operator_id,
            remark=remark or "管理员充值",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 更新用户余额
        user.solution_credits = balance_after
        user.credits_updated_at = datetime.now()

        save_obj(self.db, transaction)

        return True, f"充值成功，增加 {actual_amount} 积分，当前余额 {balance_after} 积分", transaction

    def admin_deduct_credits(
        self,
        user_id: int,
        amount: int,
        operator_id: int,
        remark: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[bool, str, Optional[SolutionCreditTransaction]]:
        """
        管理员扣除积分

        Args:
            user_id: 目标用户ID
            amount: 扣除数量（正数）
            operator_id: 操作人（管理员）ID
            remark: 扣除原因
        """
        if amount <= 0:
            return False, "扣除数量必须大于0", None

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户不存在", None

        balance_before = user.solution_credits or 0
        balance_after = max(balance_before - amount, 0)
        actual_amount = balance_before - balance_after

        if actual_amount <= 0:
            return False, "用户积分已为0", None

        # 创建交易记录
        transaction = SolutionCreditTransaction(
            user_id=user_id,
            transaction_type=CreditTransactionType.ADMIN_DEDUCT,
            amount=-actual_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            operator_id=operator_id,
            remark=remark or "管理员扣除",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 更新用户余额
        user.solution_credits = balance_after
        user.credits_updated_at = datetime.now()

        save_obj(self.db, transaction)

        return True, f"扣除成功，减少 {actual_amount} 积分，当前余额 {balance_after} 积分", transaction

    def get_transaction_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        transaction_type: str = None
    ) -> Tuple[List[SolutionCreditTransaction], int]:
        """
        获取用户积分交易历史

        Returns:
            Tuple[List[SolutionCreditTransaction], int]: (交易记录列表, 总数)
        """
        query = self.db.query(SolutionCreditTransaction).filter(
            SolutionCreditTransaction.user_id == user_id
        )

        if transaction_type:
            query = query.filter(SolutionCreditTransaction.transaction_type == transaction_type)

        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = query.order_by(desc(SolutionCreditTransaction.created_at))
        query = apply_pagination(query, pagination.offset, pagination.limit)
        transactions = query.all()

        return transactions, total

    def get_all_users_credits(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取所有用户积分列表（管理员用）

        Returns:
            Tuple[List[Dict], int]: (用户积分列表, 总数)
        """
        query = self.db.query(User).filter(User.is_active)

        query = apply_keyword_filter(query, User, search, ["username", "real_name", "employee_no"])

        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        users = query.all()

        generate_cost = self.get_config("GENERATE_COST")
        result = []
        for user in users:
            balance = user.solution_credits or 0
            result.append({
                "user_id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "employee_no": user.employee_no,
                "department": user.department,
                "balance": balance,
                "remaining_generations": balance // generate_cost if generate_cost > 0 else 0,
                "last_updated": user.credits_updated_at,
            })

        return result, total

    def batch_add_credits(
        self,
        user_ids: List[int],
        amount: int,
        operator_id: int,
        remark: str = None
    ) -> Dict[str, Any]:
        """
        批量充值积分

        Returns:
            Dict: 充值结果统计
        """
        success_count = 0
        fail_count = 0
        results = []

        for user_id in user_ids:
            success, message, _ = self.admin_add_credits(
                user_id=user_id,
                amount=amount,
                operator_id=operator_id,
                remark=remark
            )
            if success:
                success_count += 1
            else:
                fail_count += 1
            results.append({
                "user_id": user_id,
                "success": success,
                "message": message
            })

        return {
            "total": len(user_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }

    def update_config(
        self,
        key: str,
        value: str,
        description: str = None
    ) -> Tuple[bool, str]:
        """更新积分配置"""
        config = self.db.query(SolutionCreditConfig).filter(
            SolutionCreditConfig.config_key == key
        ).first()

        if config:
            config.config_value = value
            if description:
                config.description = description
            config.updated_at = datetime.now()
        else:
            config = SolutionCreditConfig(
                config_key=key,
                config_value=value,
                description=description
            )
            self.db.add(config)

        self.db.commit()
        return True, f"配置 {key} 已更新为 {value}"

    def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有积分配置"""
        configs = self.db.query(SolutionCreditConfig).all()

        result = []
        for key, default_value in self.DEFAULT_CONFIG.items():
            config = next((c for c in configs if c.config_key == key), None)
            result.append({
                "key": key,
                "value": config.config_value if config else str(default_value),
                "description": config.description if config else "",
                "is_active": config.is_active if config else True,
            })

        return result
