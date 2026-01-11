# -*- coding: utf-8 -*-
"""
奖金发放服务

提取奖金发放的业务逻辑
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.bonus import (
    BonusAllocationSheet, BonusCalculation, BonusDistribution,
    TeamBonusAllocation, BonusRule
)
from app.services.bonus_calculator import BonusCalculator


def validate_sheet_for_distribution(
    sheet: BonusAllocationSheet
) -> Tuple[bool, Optional[str]]:
    """
    验证明细表是否可以发放
    
    Args:
        sheet: 奖金分配明细表
    
    Returns:
        (是否有效, 错误消息)
    """
    if sheet.status == 'DISTRIBUTED':
        return False, "该明细表已发放"
    
    # 检查线下确认状态
    if not (sheet.finance_confirmed and sheet.hr_confirmed and sheet.manager_confirmed):
        return False, "线下确认未完成，无法发放。请先完成财务部、人力资源部、总经理的确认"
    
    if not sheet.parse_result or 'valid_rows' not in sheet.parse_result:
        return False, "明细表数据无效，请重新上传"
    
    valid_rows = sheet.parse_result['valid_rows']
    if not valid_rows:
        return False, "明细表中没有有效数据"
    
    return True, None


def create_calculation_from_team_allocation(
    db: Session,
    team_allocation_id: int,
    user_id: int,
    calculated_amount: Decimal,
    calculator: BonusCalculator
) -> BonusCalculation:
    """
    从团队奖金分配创建个人计算记录
    
    Args:
        db: 数据库会话
        team_allocation_id: 团队奖金分配ID
        user_id: 用户ID
        calculated_amount: 计算金额
        calculator: 奖金计算器
    
    Returns:
        创建的计算记录
    """
    allocation = db.query(TeamBonusAllocation).filter(
        TeamBonusAllocation.id == team_allocation_id
    ).first()
    
    if not allocation:
        raise ValueError(f"团队奖金分配ID {team_allocation_id} 不存在")
    
    # 获取分配明细中的规则信息
    allocation_detail = allocation.allocation_detail or {}
    rule_id = allocation_detail.get('rule_id')
    
    if not rule_id:
        raise ValueError(f"团队奖金分配ID {team_allocation_id} 缺少规则ID")
    
    rule = db.query(BonusRule).filter(BonusRule.id == rule_id).first()
    if not rule:
        raise ValueError(f"规则ID {rule_id} 不存在")
    
    # 创建个人计算记录
    calculation = BonusCalculation(
        calculation_code=calculator.generate_calculation_code(),
        rule_id=rule_id,
        project_id=allocation.project_id,
        user_id=user_id,
        calculated_amount=calculated_amount,
        calculation_detail={
            "from_team_allocation": True,
            "team_allocation_id": team_allocation_id,
            "allocation_detail": allocation_detail
        },
        calculation_basis={
            "type": "from_team_allocation",
            "team_allocation_id": team_allocation_id,
            "user_id": user_id
        },
        status='APPROVED'  # 从Excel导入的视为已审批
    )
    
    db.add(calculation)
    db.flush()  # 获取calculation.id
    
    return calculation


def create_distribution_record(
    db: Session,
    calculation_id: int,
    user_id: int,
    row_data: Dict[str, Any],
    current_user_id: int,
    generate_distribution_code_func
) -> BonusDistribution:
    """
    创建发放记录
    
    Args:
        db: 数据库会话
        calculation_id: 计算记录ID
        user_id: 用户ID
        row_data: 行数据
        current_user_id: 当前用户ID
        generate_distribution_code_func: 发放编号生成函数
    
    Returns:
        创建的发放记录
    """
    distribution = BonusDistribution(
        distribution_code=generate_distribution_code_func(),
        calculation_id=calculation_id,
        user_id=user_id,
        distributed_amount=Decimal(str(row_data['distributed_amount'])),
        distribution_date=datetime.strptime(row_data['distribution_date'], '%Y-%m-%d').date(),
        payment_method=row_data.get('payment_method'),
        voucher_no=row_data.get('voucher_no'),
        payment_account=row_data.get('payment_account'),
        payment_remark=row_data.get('payment_remark'),
        status='PAID',  # 直接标记为已发放
        paid_by=current_user_id,
        paid_at=datetime.now()
    )
    
    db.add(distribution)
    return distribution


def check_distribution_exists(
    db: Session,
    calculation_id: int,
    user_id: int
) -> bool:
    """
    检查是否已发放
    
    Args:
        db: 数据库会话
        calculation_id: 计算记录ID
        user_id: 用户ID
    
    Returns:
        是否已发放
    """
    existing = db.query(BonusDistribution).filter(
        BonusDistribution.calculation_id == calculation_id,
        BonusDistribution.user_id == user_id,
        BonusDistribution.status == 'PAID'
    ).first()
    
    return existing is not None
