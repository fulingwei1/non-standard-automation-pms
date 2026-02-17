# -*- coding: utf-8 -*-
"""
合同盖章邮寄 API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.business_support import ContractSealRecord
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import (
    ContractSealRecordCreate,
    ContractSealRecordResponse,
    ContractSealRecordUpdate,
)
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.post("/{contract_id}/seal", response_model=ResponseModel[ContractSealRecordResponse], summary="创建合同盖章记录")
async def create_contract_seal_record(
    contract_id: int,
    seal_data: ContractSealRecordCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建合同盖章记录"""
    try:
        # 检查合同是否存在
        contract = get_or_404(db, Contract, contract_id, "合同不存在")

        # 创建盖章记录
        seal_record = ContractSealRecord(
            contract_id=contract_id,
            seal_status="pending",
            seal_date=seal_data.seal_date,
            seal_operator_id=current_user.id,
            send_date=seal_data.send_date,
            tracking_no=seal_data.tracking_no,
            courier_company=seal_data.courier_company,
            remark=seal_data.remark
        )

        db.add(seal_record)
        db.commit()
        db.refresh(seal_record)

        return ResponseModel(
            code=200,
            message="创建合同盖章记录成功",
            data=ContractSealRecordResponse(
                id=seal_record.id,
                contract_id=seal_record.contract_id,
                seal_status=seal_record.seal_status,
                seal_date=seal_record.seal_date,
                seal_operator_id=seal_record.seal_operator_id,
                send_date=seal_record.send_date,
                tracking_no=seal_record.tracking_no,
                courier_company=seal_record.courier_company,
                receive_date=seal_record.receive_date,
                archive_date=seal_record.archive_date,
                archive_location=seal_record.archive_location,
                remark=seal_record.remark,
                created_at=seal_record.created_at,
                updated_at=seal_record.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建合同盖章记录失败: {str(e)}")


@router.put("/{contract_id}/seal/{seal_id}", response_model=ResponseModel[ContractSealRecordResponse], summary="更新合同盖章记录")
async def update_contract_seal_record(
    contract_id: int,
    seal_id: int,
    seal_data: ContractSealRecordUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:update"))
):
    """更新合同盖章记录"""
    try:
        seal_record = (
            db.query(ContractSealRecord)
            .filter(
                ContractSealRecord.id == seal_id,
                ContractSealRecord.contract_id == contract_id
            )
            .first()
        )
        if not seal_record:
            raise HTTPException(status_code=404, detail="盖章记录不存在")

        # 更新字段
        update_data = seal_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(seal_record, key, value)

        db.commit()
        db.refresh(seal_record)

        return ResponseModel(
            code=200,
            message="更新合同盖章记录成功",
            data=ContractSealRecordResponse(
                id=seal_record.id,
                contract_id=seal_record.contract_id,
                seal_status=seal_record.seal_status,
                seal_date=seal_record.seal_date,
                seal_operator_id=seal_record.seal_operator_id,
                send_date=seal_record.send_date,
                tracking_no=seal_record.tracking_no,
                courier_company=seal_record.courier_company,
                receive_date=seal_record.receive_date,
                archive_date=seal_record.archive_date,
                archive_location=seal_record.archive_location,
                remark=seal_record.remark,
                created_at=seal_record.created_at,
                updated_at=seal_record.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新合同盖章记录失败: {str(e)}")
