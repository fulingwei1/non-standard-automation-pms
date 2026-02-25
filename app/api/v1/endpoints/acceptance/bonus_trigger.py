# -*- coding: utf-8 -*-
"""
验收报告 - 奖金计算触发

包含手动触发验收单关联的奖金计算
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceOrder
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/acceptance-orders/{order_id}/trigger-bonus-calculation", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def trigger_bonus_calculation_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_permission("bonus:trigger")),
) -> Any:
    """
    手动触发验收单关联的奖金计算

    只有正式完成的验收单（已上传客户签署文件）才能触发奖金计算
    """
    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

    # 验证验收单状态
    if not order.is_officially_completed:
        raise HTTPException(status_code=400, detail="只有正式完成的验收单（已上传客户签署文件）才能触发奖金计算")

    if order.overall_result != "PASSED":
        raise HTTPException(status_code=400, detail="只有验收通过的验收单才能触发奖金计算")

    # 获取项目信息
    project = db.query(Project).filter(Project.id == order.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="关联的项目不存在")

    try:
        from app.services.bonus import BonusCalculator
        calculator = BonusCalculator(db)

        # 触发奖金计算
        calculations = calculator.trigger_acceptance_bonus_calculation(project, order)

        db.commit()

        return ResponseModel(
            code=200,
            message="奖金计算触发成功",
            data={
                "order_id": order_id,
                "order_no": order.order_no,
                "project_id": project.id,
                "project_name": project.project_name,
                "calculations_count": len(calculations),
                "calculations": [
                    {
                        "id": calc.id,
                        "calculation_code": calc.calculation_code,
                        "user_id": calc.user_id,
                        "calculated_amount": float(calc.calculated_amount) if calc.calculated_amount else 0,
                        "status": calc.status,
                    }
                    for calc in calculations
                ] if calculations else []
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"奖金计算失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"奖金计算失败: {str(e)}")
