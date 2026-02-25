# -*- coding: utf-8 -*-
"""
奖金分配明细表 - 业务操作（确认、发放）
"""
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.bonus import BonusAllocationSheet, BonusCalculation
from app.models.user import User
from app.schemas.bonus import BonusAllocationSheetConfirm, BonusAllocationSheetResponse
from app.schemas.common import ResponseModel

from ..payment import generate_distribution_code
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.post("/allocation-sheets/{sheet_id}/confirm", response_model=ResponseModel[BonusAllocationSheetResponse], status_code=status.HTTP_200_OK)
def confirm_allocation_sheet(
    *,
    db: Session = Depends(deps.get_db),
    sheet_id: int,
    confirm_in: BonusAllocationSheetConfirm,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认分配明细表（线下确认完成）

    记录财务部、人力资源部、总经理的线下确认状态
    """
    sheet = get_or_404(db, BonusAllocationSheet, sheet_id, "分配明细表不存在")

    if sheet.status == 'DISTRIBUTED':
        raise HTTPException(status_code=400, detail="该明细表已发放，无法修改确认状态")

    sheet.finance_confirmed = confirm_in.finance_confirmed
    sheet.hr_confirmed = confirm_in.hr_confirmed
    sheet.manager_confirmed = confirm_in.manager_confirmed

    # 如果全部确认，更新确认时间
    if confirm_in.finance_confirmed and confirm_in.hr_confirmed and confirm_in.manager_confirmed:
        sheet.confirmed_at = datetime.now()

    db.add(sheet)
    db.commit()
    db.refresh(sheet)

    return ResponseModel(
        code=200,
        message="确认状态更新成功",
        data=BonusAllocationSheetResponse.model_validate(sheet)
    )


@router.post("/allocation-sheets/{sheet_id}/distribute", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def distribute_bonus_from_sheet(
    *,
    db: Session = Depends(deps.get_db),
    sheet_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    同意发放 - 根据分配明细表批量创建发放记录

    只有线下确认完成（财务、人力、总经理都确认）的明细表才能发放
    """
    from app.services.bonus import BonusCalculator
    from app.services.bonus_distribution_service import (
        check_distribution_exists,
        create_calculation_from_team_allocation,
        create_distribution_record,
        validate_sheet_for_distribution,
    )

    sheet = get_or_404(db, BonusAllocationSheet, sheet_id, "分配明细表不存在")

    # 验证明细表
    is_valid, error_msg = validate_sheet_for_distribution(sheet)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    valid_rows = sheet.parse_result['valid_rows']

    # 批量创建发放记录
    distributions = []
    errors = []
    calculator = BonusCalculator(db)

    for row_data in valid_rows:
        try:
            calculation = None
            calculation_id = row_data.get('calculation_id')
            team_allocation_id = row_data.get('team_allocation_id')

            # 如果使用团队奖金分配ID，先创建个人计算记录
            if team_allocation_id:
                try:
                    calculation = create_calculation_from_team_allocation(
                        db, team_allocation_id, row_data['user_id'],
                        Decimal(str(row_data['calculated_amount'])), calculator
                    )
                    calculation_id = calculation.id
                except ValueError as e:
                    errors.append(str(e))
                    continue
            else:
                # 使用已有的计算记录
                calculation = db.query(BonusCalculation).filter(
                    BonusCalculation.id == calculation_id
                ).first()
                if not calculation:
                    errors.append(f"计算记录ID {calculation_id} 不存在")
                    continue

            # 检查是否已发放
            if check_distribution_exists(db, calculation_id, row_data['user_id']):
                errors.append(f"计算记录ID {calculation_id} 对用户ID {row_data['user_id']} 已发放")
                continue

            # 创建发放记录
            distribution = create_distribution_record(
                db, calculation_id, row_data['user_id'], row_data,
                current_user.id, generate_distribution_code
            )
            distributions.append(distribution)

            # 更新计算记录状态
            if calculation:
                calculation.status = 'DISTRIBUTED'

        except Exception as e:
            errors.append(f"处理行数据失败: {str(e)}")
            continue

    if errors and not distributions:
        raise HTTPException(
            status_code=400,
            detail=f"发放失败：{'; '.join(errors[:5])}"  # 只显示前5个错误
        )

    # 更新明细表状态
    sheet.status = 'DISTRIBUTED'
    sheet.distributed_at = datetime.now()
    sheet.distributed_by = current_user.id
    sheet.distribution_count = len(distributions)

    db.commit()

    return ResponseModel(
        code=200,
        message=f"发放成功，共创建 {len(distributions)} 条发放记录" + (f"，{len(errors)} 条失败" if errors else ""),
        data={
            "sheet_id": sheet_id,
            "sheet_code": sheet.sheet_code,
            "distributed_count": len(distributions),
            "error_count": len(errors),
            "errors": errors[:10] if errors else []  # 最多返回10个错误
        }
    )
