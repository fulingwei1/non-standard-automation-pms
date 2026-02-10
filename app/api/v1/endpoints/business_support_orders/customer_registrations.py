# -*- coding: utf-8 -*-
"""
商务支持模块 - 客户供应商入驻管理 API endpoints
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.models.business_support import CustomerSupplierRegistration
from app.models.project import Customer
from app.models.user import User
from app.schemas.business_support import (
    CustomerSupplierRegistrationCreate,
    CustomerSupplierRegistrationResponse,
    CustomerSupplierRegistrationUpdate,
    SupplierRegistrationReviewRequest,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import (
    _serialize_attachments,
    _to_registration_response,
    generate_registration_no,
)

router = APIRouter()


# ==================== 客户供应商入驻 ====================


@router.get("/customer-registrations", response_model=ResponseModel[PaginatedResponse[CustomerSupplierRegistrationResponse]], summary="获取客户供应商入驻列表")
async def get_customer_registrations(
    pagination: PaginationParams = Depends(get_pagination_query),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    registration_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    platform_name: Optional[str] = Query(None, description="平台名称筛选"),
    keyword: Optional[str] = Query(None, description="搜索入驻编号/客户"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """分页获取客户供应商入驻记录"""
    try:
        query = db.query(CustomerSupplierRegistration)
        if customer_id:
            query = query.filter(CustomerSupplierRegistration.customer_id == customer_id)
        if registration_status:
            query = query.filter(CustomerSupplierRegistration.registration_status == registration_status)
        if platform_name:
            query = query.filter(CustomerSupplierRegistration.platform_name == platform_name)

        # 应用关键词过滤（入驻编号/客户名称）
        query = apply_keyword_filter(query, CustomerSupplierRegistration, keyword, ["registration_no", "customer_name"])

        total = query.count()
        items = (
            query.order_by(desc(CustomerSupplierRegistration.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        responses = [_to_registration_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取客户供应商入驻列表成功",
            data=PaginatedResponse(
                items=responses,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total)
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取客户供应商入驻列表失败: {str(exc)}")


@router.post("/customer-registrations", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="创建客户供应商入驻申请")
async def create_customer_registration(
    registration_in: CustomerSupplierRegistrationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建客户供应商入驻申请"""
    try:
        customer = db.query(Customer).filter(Customer.id == registration_in.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")

        registration = CustomerSupplierRegistration(
            registration_no=generate_registration_no(db),
            customer_id=customer.id,
            customer_name=registration_in.customer_name or customer.customer_name,
            platform_name=registration_in.platform_name,
            platform_url=registration_in.platform_url,
            registration_status="PENDING",
            application_date=registration_in.application_date or date.today(),
            contact_person=registration_in.contact_person,
            contact_phone=registration_in.contact_phone,
            contact_email=registration_in.contact_email,
            required_docs=_serialize_attachments(registration_in.required_docs),
            remark=registration_in.remark,
            external_sync_status="pending"
        )
        db.add(registration)
        db.commit()
        db.refresh(registration)

        return ResponseModel(
            code=200,
            message="创建客户供应商入驻申请成功",
            data=_to_registration_response(registration)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建客户供应商入驻申请失败: {str(exc)}")


@router.get("/customer-registrations/{registration_id}", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="获取入驻详情")
async def get_customer_registration(
    registration_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取客户供应商入驻详情"""
    record = db.query(CustomerSupplierRegistration).filter(
        CustomerSupplierRegistration.id == registration_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="入驻记录不存在")
    return ResponseModel(
        code=200,
        message="获取客户供应商入驻详情成功",
        data=_to_registration_response(record)
    )


@router.put("/customer-registrations/{registration_id}", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="更新入驻记录")
async def update_customer_registration(
    registration_id: int,
    registration_in: CustomerSupplierRegistrationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新客户供应商入驻记录"""
    try:
        record = db.query(CustomerSupplierRegistration).filter(
            CustomerSupplierRegistration.id == registration_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="入驻记录不存在")

        update_data = registration_in.model_dump(exclude_unset=True)
        if "required_docs" in update_data:
            record.required_docs = _serialize_attachments(update_data.pop("required_docs"))
        for field, value in update_data.items():
            setattr(record, field, value)

        db.add(record)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            code=200,
            message="更新入驻记录成功",
            data=_to_registration_response(record)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新入驻记录失败: {str(exc)}")


@router.post("/customer-registrations/{registration_id}/approve", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="审批客户入驻申请")
async def approve_customer_registration(
    registration_id: int,
    review_in: SupplierRegistrationReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """审批通过客户供应商入驻申请"""
    try:
        record = db.query(CustomerSupplierRegistration).filter(
            CustomerSupplierRegistration.id == registration_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="入驻记录不存在")
        if record.registration_status == "APPROVED":
            raise HTTPException(status_code=400, detail="申请已审批通过")

        record.registration_status = "APPROVED"
        record.approved_date = date.today()
        record.reviewer_id = current_user.id
        record.review_comment = review_in.review_comment
        record.external_sync_status = "pending"

        db.add(record)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            code=200,
            message="审批客户供应商入驻成功",
            data=_to_registration_response(record)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审批客户供应商入驻失败: {str(exc)}")


@router.post("/customer-registrations/{registration_id}/reject", response_model=ResponseModel[CustomerSupplierRegistrationResponse], summary="驳回客户入驻申请")
async def reject_customer_registration(
    registration_id: int,
    review_in: SupplierRegistrationReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """驳回客户供应商入驻申请"""
    try:
        record = db.query(CustomerSupplierRegistration).filter(
            CustomerSupplierRegistration.id == registration_id
        ).first()
        if not record:
            raise HTTPException(status_code=404, detail="入驻记录不存在")
        if record.registration_status == "APPROVED":
            raise HTTPException(status_code=400, detail="审批通过的申请不可驳回")

        record.registration_status = "REJECTED"
        record.reviewer_id = current_user.id
        record.review_comment = review_in.review_comment
        record.approved_date = None

        db.add(record)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            code=200,
            message="驳回客户供应商入驻成功",
            data=_to_registration_response(record)
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"驳回客户供应商入驻失败: {str(exc)}")
