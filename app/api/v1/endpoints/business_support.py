# -*- coding: utf-8 -*-
"""
商务支持模块 API endpoints
包含：工作台统计、投标管理、合同审核、回款催收、文件归档
"""

from typing import Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func, and_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Customer, Project
from app.models.sales import Contract, Invoice
from app.models.business_support import (
    BiddingProject, BiddingDocument,
    ContractReview, ContractSealRecord,
    PaymentReminder, DocumentArchive,
    SalesOrder, SalesOrderItem, DeliveryOrder
)
from app.schemas.business_support import (
    BiddingProjectCreate, BiddingProjectUpdate, BiddingProjectResponse,
    BiddingDocumentCreate, BiddingDocumentResponse,
    ContractReviewCreate, ContractReviewUpdate, ContractReviewResponse,
    ContractSealRecordCreate, ContractSealRecordUpdate, ContractSealRecordResponse,
    PaymentReminderCreate, PaymentReminderUpdate, PaymentReminderResponse,
    DocumentArchiveCreate, DocumentArchiveUpdate, DocumentArchiveResponse,
    BusinessSupportDashboardResponse, PerformanceMetricsResponse,
    SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse,
    SalesOrderItemCreate, SalesOrderItemResponse,
    AssignProjectRequest, SendNoticeRequest,
    DeliveryOrderCreate, DeliveryOrderUpdate, DeliveryOrderResponse,
    DeliveryApprovalRequest
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


# ==================== 编码生成函数 ====================


def generate_bidding_no(db: Session) -> str:
    """生成投标编号：BD250101-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m%d")
    prefix = f"BD{month_str}-"
    
    max_bidding = (
        db.query(BiddingProject)
        .filter(BiddingProject.bidding_no.like(f"{prefix}%"))
        .order_by(desc(BiddingProject.bidding_no))
        .first()
    )
    
    if max_bidding:
        try:
            seq = int(max_bidding.bidding_no.split("-")[-1]) + 1
        except (ValueError, TypeError, IndexError):
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


def generate_archive_no(db: Session) -> str:
    """生成归档编号：ARC250101-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m%d")
    prefix = f"ARC{month_str}-"
    
    max_archive = (
        db.query(DocumentArchive)
        .filter(DocumentArchive.archive_no.like(f"{prefix}%"))
        .order_by(desc(DocumentArchive.archive_no))
        .first()
    )
    
    if max_archive:
        try:
            seq = int(max_archive.archive_no.split("-")[-1]) + 1
        except (ValueError, TypeError, IndexError):
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:03d}"


# ==================== 工作台统计 ====================


@router.get("/dashboard", response_model=ResponseModel[BusinessSupportDashboardResponse], summary="获取商务支持工作台统计")
async def get_business_support_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """
    获取商务支持工作台统计数据
    包括：进行中合同数、待回款金额、逾期款项、开票率、投标数、验收率等
    """
    from app.services.business_support_dashboard_service import (
        count_active_contracts,
        calculate_pending_amount,
        calculate_overdue_amount,
        calculate_invoice_rate,
        count_active_bidding,
        calculate_acceptance_rate,
        get_urgent_tasks,
        get_today_todos
    )
    
    try:
        today = date.today()
        
        # 计算各项统计
        active_contracts = count_active_contracts(db)
        pending_amount = calculate_pending_amount(db, today)
        overdue_amount = calculate_overdue_amount(db, today)
        invoice_rate = calculate_invoice_rate(db, today)
        active_bidding = count_active_bidding(db)
        acceptance_rate = calculate_acceptance_rate(db)
        urgent_tasks = get_urgent_tasks(db, current_user.id, today)
        today_todos = get_today_todos(db, current_user.id, today)
        
        dashboard_data = BusinessSupportDashboardResponse(
            active_contracts_count=active_contracts,
            pending_amount=pending_amount,
            overdue_amount=overdue_amount,
            invoice_rate=invoice_rate,
            active_bidding_count=active_bidding,
            acceptance_rate=acceptance_rate,
            urgent_tasks=urgent_tasks,
            today_todos=today_todos
        )
        
        return ResponseModel(
            code=200,
            message="获取工作台统计成功",
            data=dashboard_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作台统计失败: {str(e)}")


# ==================== 投标管理 ====================


@router.get("/bidding", response_model=ResponseModel[PaginatedResponse[BiddingProjectResponse]], summary="获取投标项目列表")
async def get_bidding_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: Optional[str] = Query(None, description="状态筛选"),
    bid_result: Optional[str] = Query(None, description="投标结果筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取投标项目列表"""
    try:
        query = db.query(BiddingProject)
        
        # 筛选条件
        if status:
            query = query.filter(BiddingProject.status == status)
        if bid_result:
            query = query.filter(BiddingProject.bid_result == bid_result)
        if customer_id:
            query = query.filter(BiddingProject.customer_id == customer_id)
        if search:
            query = query.filter(
                or_(
                    BiddingProject.project_name.like(f"%{search}%"),
                    BiddingProject.bidding_no.like(f"%{search}%"),
                    BiddingProject.customer_name.like(f"%{search}%")
                )
            )
        
        # 总数
        total = query.count()
        
        # 分页
        items = (
            query.order_by(desc(BiddingProject.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # 转换为响应格式
        bidding_list = [
            BiddingProjectResponse(
                id=item.id,
                bidding_no=item.bidding_no,
                project_name=item.project_name,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                tender_no=item.tender_no,
                tender_type=item.tender_type,
                tender_platform=item.tender_platform,
                tender_url=item.tender_url,
                publish_date=item.publish_date,
                deadline_date=item.deadline_date,
                bid_opening_date=item.bid_opening_date,
                bid_bond=item.bid_bond,
                bid_bond_status=item.bid_bond_status,
                estimated_amount=item.estimated_amount,
                bid_document_status=item.bid_document_status,
                technical_doc_ready=item.technical_doc_ready,
                commercial_doc_ready=item.commercial_doc_ready,
                qualification_doc_ready=item.qualification_doc_ready,
                submission_method=item.submission_method,
                submission_address=item.submission_address,
                sales_person_id=item.sales_person_id,
                sales_person_name=item.sales_person_name,
                support_person_id=item.support_person_id,
                support_person_name=item.support_person_name,
                bid_result=item.bid_result,
                bid_price=item.bid_price,
                win_price=item.win_price,
                result_date=item.result_date,
                result_remark=item.result_remark,
                status=item.status,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]
        
        return ResponseModel(
            code=200,
            message="获取投标项目列表成功",
            data=PaginatedResponse(
                items=bidding_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取投标项目列表失败: {str(e)}")


@router.post("/bidding", response_model=ResponseModel[BiddingProjectResponse], summary="创建投标项目")
async def create_bidding_project(
    bidding_data: BiddingProjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建投标项目"""
    try:
        # 生成投标编号
        bidding_no = generate_bidding_no(db)
        
        # 创建投标项目
        bidding_project = BiddingProject(
            bidding_no=bidding_no,
            project_name=bidding_data.project_name,
            customer_id=bidding_data.customer_id,
            customer_name=bidding_data.customer_name,
            tender_no=bidding_data.tender_no,
            tender_type=bidding_data.tender_type,
            tender_platform=bidding_data.tender_platform,
            tender_url=bidding_data.tender_url,
            publish_date=bidding_data.publish_date,
            deadline_date=bidding_data.deadline_date,
            bid_opening_date=bidding_data.bid_opening_date,
            bid_bond=bidding_data.bid_bond,
            bid_bond_status=bidding_data.bid_bond_status or "not_required",
            estimated_amount=bidding_data.estimated_amount,
            submission_method=bidding_data.submission_method,
            submission_address=bidding_data.submission_address,
            sales_person_id=bidding_data.sales_person_id,
            sales_person_name=bidding_data.sales_person_name,
            support_person_id=bidding_data.support_person_id or current_user.id,
            support_person_name=bidding_data.support_person_name or current_user.username,
            remark=bidding_data.remark,
            status="draft"
        )
        
        db.add(bidding_project)
        db.commit()
        db.refresh(bidding_project)
        
        return ResponseModel(
            code=200,
            message="创建投标项目成功",
            data=BiddingProjectResponse(
                id=bidding_project.id,
                bidding_no=bidding_project.bidding_no,
                project_name=bidding_project.project_name,
                customer_id=bidding_project.customer_id,
                customer_name=bidding_project.customer_name,
                tender_no=bidding_project.tender_no,
                tender_type=bidding_project.tender_type,
                tender_platform=bidding_project.tender_platform,
                tender_url=bidding_project.tender_url,
                publish_date=bidding_project.publish_date,
                deadline_date=bidding_project.deadline_date,
                bid_opening_date=bidding_project.bid_opening_date,
                bid_bond=bidding_project.bid_bond,
                bid_bond_status=bidding_project.bid_bond_status,
                estimated_amount=bidding_project.estimated_amount,
                bid_document_status=bidding_project.bid_document_status,
                technical_doc_ready=bidding_project.technical_doc_ready,
                commercial_doc_ready=bidding_project.commercial_doc_ready,
                qualification_doc_ready=bidding_project.qualification_doc_ready,
                submission_method=bidding_project.submission_method,
                submission_address=bidding_project.submission_address,
                sales_person_id=bidding_project.sales_person_id,
                sales_person_name=bidding_project.sales_person_name,
                support_person_id=bidding_project.support_person_id,
                support_person_name=bidding_project.support_person_name,
                bid_result=bidding_project.bid_result,
                bid_price=bidding_project.bid_price,
                win_price=bidding_project.win_price,
                result_date=bidding_project.result_date,
                result_remark=bidding_project.result_remark,
                status=bidding_project.status,
                remark=bidding_project.remark,
                created_at=bidding_project.created_at,
                updated_at=bidding_project.updated_at
            )
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建投标项目失败: {str(e)}")


@router.get("/bidding/{bidding_id}", response_model=ResponseModel[BiddingProjectResponse], summary="获取投标项目详情")
async def get_bidding_project(
    bidding_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取投标项目详情"""
    try:
        bidding_project = db.query(BiddingProject).filter(BiddingProject.id == bidding_id).first()
        if not bidding_project:
            raise HTTPException(status_code=404, detail="投标项目不存在")
        
        return ResponseModel(
            code=200,
            message="获取投标项目详情成功",
            data=BiddingProjectResponse(
                id=bidding_project.id,
                bidding_no=bidding_project.bidding_no,
                project_name=bidding_project.project_name,
                customer_id=bidding_project.customer_id,
                customer_name=bidding_project.customer_name,
                tender_no=bidding_project.tender_no,
                tender_type=bidding_project.tender_type,
                tender_platform=bidding_project.tender_platform,
                tender_url=bidding_project.tender_url,
                publish_date=bidding_project.publish_date,
                deadline_date=bidding_project.deadline_date,
                bid_opening_date=bidding_project.bid_opening_date,
                bid_bond=bidding_project.bid_bond,
                bid_bond_status=bidding_project.bid_bond_status,
                estimated_amount=bidding_project.estimated_amount,
                bid_document_status=bidding_project.bid_document_status,
                technical_doc_ready=bidding_project.technical_doc_ready,
                commercial_doc_ready=bidding_project.commercial_doc_ready,
                qualification_doc_ready=bidding_project.qualification_doc_ready,
                submission_method=bidding_project.submission_method,
                submission_address=bidding_project.submission_address,
                sales_person_id=bidding_project.sales_person_id,
                sales_person_name=bidding_project.sales_person_name,
                support_person_id=bidding_project.support_person_id,
                support_person_name=bidding_project.support_person_name,
                bid_result=bidding_project.bid_result,
                bid_price=bidding_project.bid_price,
                win_price=bidding_project.win_price,
                result_date=bidding_project.result_date,
                result_remark=bidding_project.result_remark,
                status=bidding_project.status,
                remark=bidding_project.remark,
                created_at=bidding_project.created_at,
                updated_at=bidding_project.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取投标项目详情失败: {str(e)}")


@router.put("/bidding/{bidding_id}", response_model=ResponseModel[BiddingProjectResponse], summary="更新投标项目")
async def update_bidding_project(
    bidding_id: int,
    bidding_data: BiddingProjectUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:update"))
):
    """更新投标项目"""
    try:
        bidding_project = db.query(BiddingProject).filter(BiddingProject.id == bidding_id).first()
        if not bidding_project:
            raise HTTPException(status_code=404, detail="投标项目不存在")
        
        # 更新字段
        update_data = bidding_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(bidding_project, key, value)
        
        db.commit()
        db.refresh(bidding_project)
        
        return ResponseModel(
            code=200,
            message="更新投标项目成功",
            data=BiddingProjectResponse(
                id=bidding_project.id,
                bidding_no=bidding_project.bidding_no,
                project_name=bidding_project.project_name,
                customer_id=bidding_project.customer_id,
                customer_name=bidding_project.customer_name,
                tender_no=bidding_project.tender_no,
                tender_type=bidding_project.tender_type,
                tender_platform=bidding_project.tender_platform,
                tender_url=bidding_project.tender_url,
                publish_date=bidding_project.publish_date,
                deadline_date=bidding_project.deadline_date,
                bid_opening_date=bidding_project.bid_opening_date,
                bid_bond=bidding_project.bid_bond,
                bid_bond_status=bidding_project.bid_bond_status,
                estimated_amount=bidding_project.estimated_amount,
                bid_document_status=bidding_project.bid_document_status,
                technical_doc_ready=bidding_project.technical_doc_ready,
                commercial_doc_ready=bidding_project.commercial_doc_ready,
                qualification_doc_ready=bidding_project.qualification_doc_ready,
                submission_method=bidding_project.submission_method,
                submission_address=bidding_project.submission_address,
                sales_person_id=bidding_project.sales_person_id,
                sales_person_name=bidding_project.sales_person_name,
                support_person_id=bidding_project.support_person_id,
                support_person_name=bidding_project.support_person_name,
                bid_result=bidding_project.bid_result,
                bid_price=bidding_project.bid_price,
                win_price=bidding_project.win_price,
                result_date=bidding_project.result_date,
                result_remark=bidding_project.result_remark,
                status=bidding_project.status,
                remark=bidding_project.remark,
                created_at=bidding_project.created_at,
                updated_at=bidding_project.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新投标项目失败: {str(e)}")


# ==================== 合同审核 ====================


@router.post("/contracts/{contract_id}/review", response_model=ResponseModel[ContractReviewResponse], summary="创建合同审核")
async def create_contract_review(
    contract_id: int,
    review_data: ContractReviewCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建合同审核记录"""
    try:
        # 检查合同是否存在
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
        
        # 创建审核记录
        contract_review = ContractReview(
            contract_id=contract_id,
            review_type=review_data.review_type,
            review_status="pending",
            reviewer_id=current_user.id,
            review_comment=review_data.review_comment,
            risk_items=review_data.risk_items
        )
        
        db.add(contract_review)
        db.commit()
        db.refresh(contract_review)
        
        return ResponseModel(
            code=200,
            message="创建合同审核成功",
            data=ContractReviewResponse(
                id=contract_review.id,
                contract_id=contract_review.contract_id,
                review_type=contract_review.review_type,
                review_status=contract_review.review_status,
                reviewer_id=contract_review.reviewer_id,
                review_comment=contract_review.review_comment,
                reviewed_at=contract_review.reviewed_at,
                risk_items=contract_review.risk_items,
                created_at=contract_review.created_at,
                updated_at=contract_review.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建合同审核失败: {str(e)}")


@router.put("/contracts/{contract_id}/review/{review_id}", response_model=ResponseModel[ContractReviewResponse], summary="更新合同审核")
async def update_contract_review(
    contract_id: int,
    review_id: int,
    review_data: ContractReviewUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:approve"))
):
    """更新合同审核记录（审批）"""
    try:
        contract_review = (
            db.query(ContractReview)
            .filter(
                ContractReview.id == review_id,
                ContractReview.contract_id == contract_id
            )
            .first()
        )
        if not contract_review:
            raise HTTPException(status_code=404, detail="审核记录不存在")
        
        # 更新审核状态
        update_data = review_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contract_review, key, value)
        
        # 如果审核通过或拒绝，记录审核时间
        if review_data.review_status in ["passed", "rejected"]:
            contract_review.reviewed_at = datetime.now()
        
        db.commit()
        db.refresh(contract_review)
        
        return ResponseModel(
            code=200,
            message="更新合同审核成功",
            data=ContractReviewResponse(
                id=contract_review.id,
                contract_id=contract_review.contract_id,
                review_type=contract_review.review_type,
                review_status=contract_review.review_status,
                reviewer_id=contract_review.reviewer_id,
                review_comment=contract_review.review_comment,
                reviewed_at=contract_review.reviewed_at,
                risk_items=contract_review.risk_items,
                created_at=contract_review.created_at,
                updated_at=contract_review.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新合同审核失败: {str(e)}")


# ==================== 合同盖章邮寄 ====================


@router.post("/contracts/{contract_id}/seal", response_model=ResponseModel[ContractSealRecordResponse], summary="创建合同盖章记录")
async def create_contract_seal_record(
    contract_id: int,
    seal_data: ContractSealRecordCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建合同盖章记录"""
    try:
        # 检查合同是否存在
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合同不存在")
        
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


@router.put("/contracts/{contract_id}/seal/{seal_id}", response_model=ResponseModel[ContractSealRecordResponse], summary="更新合同盖章记录")
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


# ==================== 回款催收 ====================


@router.post("/payment-reminders", response_model=ResponseModel[PaymentReminderResponse], summary="创建回款催收记录")
async def create_payment_reminder(
    reminder_data: PaymentReminderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建回款催收记录"""
    try:
        # 检查合同是否存在
        if reminder_data.contract_id:
            contract = db.query(Contract).filter(Contract.id == reminder_data.contract_id).first()
            if not contract:
                raise HTTPException(status_code=404, detail="合同不存在")
        
        # 创建催收记录
        reminder = PaymentReminder(
            contract_id=reminder_data.contract_id,
            project_id=reminder_data.project_id,
            payment_node=reminder_data.payment_node,
            payment_amount=reminder_data.payment_amount,
            plan_date=reminder_data.plan_date,
            reminder_type=reminder_data.reminder_type,
            reminder_content=reminder_data.reminder_content,
            reminder_date=reminder_data.reminder_date,
            reminder_person_id=current_user.id,
            customer_response=reminder_data.customer_response,
            next_reminder_date=reminder_data.next_reminder_date,
            status="pending",
            remark=reminder_data.remark
        )
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        
        return ResponseModel(
            code=200,
            message="创建回款催收记录成功",
            data=PaymentReminderResponse(
                id=reminder.id,
                contract_id=reminder.contract_id,
                project_id=reminder.project_id,
                payment_node=reminder.payment_node,
                payment_amount=reminder.payment_amount,
                plan_date=reminder.plan_date,
                reminder_type=reminder.reminder_type,
                reminder_content=reminder.reminder_content,
                reminder_date=reminder.reminder_date,
                reminder_person_id=reminder.reminder_person_id,
                customer_response=reminder.customer_response,
                next_reminder_date=reminder.next_reminder_date,
                status=reminder.status,
                remark=reminder.remark,
                created_at=reminder.created_at,
                updated_at=reminder.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建回款催收记录失败: {str(e)}")


@router.get("/payment-reminders", response_model=ResponseModel[PaginatedResponse[PaymentReminderResponse]], summary="获取回款催收记录列表")
async def get_payment_reminders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取回款催收记录列表"""
    try:
        query = db.query(PaymentReminder)
        
        # 筛选条件
        if contract_id:
            query = query.filter(PaymentReminder.contract_id == contract_id)
        if project_id:
            query = query.filter(PaymentReminder.project_id == project_id)
        if status:
            query = query.filter(PaymentReminder.status == status)
        
        # 总数
        total = query.count()
        
        # 分页
        items = (
            query.order_by(desc(PaymentReminder.reminder_date))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # 转换为响应格式
        reminder_list = [
            PaymentReminderResponse(
                id=item.id,
                contract_id=item.contract_id,
                project_id=item.project_id,
                payment_node=item.payment_node,
                payment_amount=item.payment_amount,
                plan_date=item.plan_date,
                reminder_type=item.reminder_type,
                reminder_content=item.reminder_content,
                reminder_date=item.reminder_date,
                reminder_person_id=item.reminder_person_id,
                customer_response=item.customer_response,
                next_reminder_date=item.next_reminder_date,
                status=item.status,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]
        
        return ResponseModel(
            code=200,
            message="获取回款催收记录列表成功",
            data=PaginatedResponse(
                items=reminder_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回款催收记录列表失败: {str(e)}")


# ==================== 文件归档 ====================


@router.post("/archives", response_model=ResponseModel[DocumentArchiveResponse], summary="创建文件归档")
async def create_document_archive(
    archive_data: DocumentArchiveCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建文件归档"""
    try:
        # 生成归档编号
        archive_no = generate_archive_no(db)
        
        # 创建归档记录
        archive = DocumentArchive(
            archive_no=archive_no,
            document_type=archive_data.document_type,
            related_type=archive_data.related_type,
            related_id=archive_data.related_id,
            document_name=archive_data.document_name,
            file_path=archive_data.file_path,
            file_size=archive_data.file_size,
            archive_location=archive_data.archive_location,
            archive_date=archive_data.archive_date,
            archiver_id=current_user.id,
            status="archived",
            remark=archive_data.remark
        )
        
        db.add(archive)
        db.commit()
        db.refresh(archive)
        
        return ResponseModel(
            code=200,
            message="创建文件归档成功",
            data=DocumentArchiveResponse(
                id=archive.id,
                archive_no=archive.archive_no,
                document_type=archive.document_type,
                related_type=archive.related_type,
                related_id=archive.related_id,
                document_name=archive.document_name,
                file_path=archive.file_path,
                file_size=archive.file_size,
                archive_location=archive.archive_location,
                archive_date=archive.archive_date,
                archiver_id=archive.archiver_id,
                status=archive.status,
                remark=archive.remark,
                created_at=archive.created_at,
                updated_at=archive.updated_at
            )
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建文件归档失败: {str(e)}")


@router.get("/archives", response_model=ResponseModel[PaginatedResponse[DocumentArchiveResponse]], summary="获取文件归档列表")
async def get_document_archives(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    document_type: Optional[str] = Query(None, description="文件类型筛选"),
    related_type: Optional[str] = Query(None, description="关联类型筛选"),
    related_id: Optional[int] = Query(None, description="关联ID筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取文件归档列表"""
    try:
        query = db.query(DocumentArchive)
        
        # 筛选条件
        if document_type:
            query = query.filter(DocumentArchive.document_type == document_type)
        if related_type:
            query = query.filter(DocumentArchive.related_type == related_type)
        if related_id:
            query = query.filter(DocumentArchive.related_id == related_id)
        if search:
            query = query.filter(
                or_(
                    DocumentArchive.document_name.like(f"%{search}%"),
                    DocumentArchive.archive_no.like(f"%{search}%")
                )
            )
        
        # 总数
        total = query.count()
        
        # 分页
        items = (
            query.order_by(desc(DocumentArchive.archive_date))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # 转换为响应格式
        archive_list = [
            DocumentArchiveResponse(
                id=item.id,
                archive_no=item.archive_no,
                document_type=item.document_type,
                related_type=item.related_type,
                related_id=item.related_id,
                document_name=item.document_name,
                file_path=item.file_path,
                file_size=item.file_size,
                archive_location=item.archive_location,
                archive_date=item.archive_date,
                archiver_id=item.archiver_id,
                status=item.status,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]
        
        return ResponseModel(
            code=200,
            message="获取文件归档列表成功",
            data=PaginatedResponse(
                items=archive_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件归档列表失败: {str(e)}")


# ==================== 工作台辅助接口 ====================


@router.get("/dashboard/active-contracts", response_model=ResponseModel[List[dict]], summary="获取进行中的合同列表")
async def get_active_contracts(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取进行中的合同列表（用于工作台展示）"""
    try:
        # 查询进行中的合同
        contracts = (
            db.query(Contract)
            .filter(Contract.status.in_(["SIGNED", "EXECUTING"]))
            .order_by(desc(Contract.signed_date))
            .limit(limit)
            .all()
        )
        
        # 使用原生SQL查询回款信息
        from sqlalchemy import text
        contract_list = []
        for contract in contracts:
            # 查询回款计划
            payment_result = None
            if contract.project_id:
                payment_result = db.execute(text("""
                    SELECT 
                        COALESCE(SUM(planned_amount), 0) as total_planned,
                        COALESCE(SUM(actual_amount), 0) as total_actual
                    FROM project_payment_plans
                    WHERE project_id = :project_id
                """), {"project_id": contract.project_id}).fetchone()
            
            total_planned = Decimal(str(payment_result[0])) if payment_result and payment_result[0] else Decimal("0")
            total_actual = Decimal(str(payment_result[1])) if payment_result and payment_result[1] else Decimal("0")
            payment_progress = (total_actual / total_planned * 100) if total_planned > 0 else Decimal("0")
            
            # 查询发票数量
            invoice_count = db.query(Invoice).filter(Invoice.contract_id == contract.id).count()
            
            contract_list.append({
                "id": contract.contract_code,
                "projectId": contract.project.project_code if contract.project else None,
                "projectName": contract.project.project_name if contract.project else None,
                "customerName": contract.customer.customer_name if contract.customer else None,
                "contractAmount": float(contract.contract_amount) if contract.contract_amount else 0,
                "signedDate": contract.signed_date.strftime("%Y-%m-%d") if contract.signed_date else None,
                "paidAmount": float(total_actual),
                "paymentProgress": float(payment_progress),
                "invoiceCount": invoice_count,
                "invoiceStatus": "complete" if invoice_count > 0 else "partial",
                "acceptanceStatus": "in_progress"  # 简化处理，实际应从验收模块查询
            })
        
        return ResponseModel(
            code=200,
            message="获取进行中的合同列表成功",
            data=contract_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进行中的合同列表失败: {str(e)}")


@router.get("/dashboard/active-bidding", response_model=ResponseModel[List[BiddingProjectResponse]], summary="获取进行中的投标列表")
async def get_active_bidding(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取进行中的投标列表（用于工作台展示）"""
    try:
        # 查询进行中的投标
        bidding_projects = (
            db.query(BiddingProject)
            .filter(BiddingProject.status.in_(["draft", "preparing", "submitted"]))
            .order_by(BiddingProject.deadline_date.asc())
            .limit(limit)
            .all()
        )
        
        bidding_list = [
            BiddingProjectResponse(
                id=item.id,
                bidding_no=item.bidding_no,
                project_name=item.project_name,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                tender_no=item.tender_no,
                tender_type=item.tender_type,
                tender_platform=item.tender_platform,
                tender_url=item.tender_url,
                publish_date=item.publish_date,
                deadline_date=item.deadline_date,
                bid_opening_date=item.bid_opening_date,
                bid_bond=item.bid_bond,
                bid_bond_status=item.bid_bond_status,
                estimated_amount=item.estimated_amount,
                bid_document_status=item.bid_document_status,
                technical_doc_ready=item.technical_doc_ready,
                commercial_doc_ready=item.commercial_doc_ready,
                qualification_doc_ready=item.qualification_doc_ready,
                submission_method=item.submission_method,
                submission_address=item.submission_address,
                sales_person_id=item.sales_person_id,
                sales_person_name=item.sales_person_name,
                support_person_id=item.support_person_id,
                support_person_name=item.support_person_name,
                bid_result=item.bid_result,
                bid_price=item.bid_price,
                win_price=item.win_price,
                result_date=item.result_date,
                result_remark=item.result_remark,
                status=item.status,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in bidding_projects
        ]
        
        return ResponseModel(
            code=200,
            message="获取进行中的投标列表成功",
            data=bidding_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进行中的投标列表失败: {str(e)}")


@router.get("/dashboard/performance", response_model=ResponseModel[PerformanceMetricsResponse], summary="获取本月绩效指标")
async def get_performance_metrics(
    month: Optional[str] = Query(None, description="统计月份（YYYY-MM格式），不提供则使用当前月份"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取本月绩效指标（用于工作台右侧展示）"""
    try:
        # 确定统计月份
        if month:
            try:
                year, month_num = map(int, month.split("-"))
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="月份格式错误，应为YYYY-MM")
        else:
            today = date.today()
            year = today.year
            month_num = today.month
        
        month_start = date(year, month_num, 1)
        # 计算下个月第一天，然后减一天得到本月最后一天
        if month_num == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month_num + 1, 1) - timedelta(days=1)
        
        month_str = f"{year}-{month_num:02d}"
        
        # 1. 新签合同数（本月签订的合同）
        new_contracts = (
            db.query(Contract)
            .filter(
                Contract.signed_date >= month_start,
                Contract.signed_date <= month_end,
                Contract.status.in_(["SIGNED", "EXECUTING"])
            )
            .count()
        )
        
        # 2. 回款完成率（本月实际回款/计划回款）
        from sqlalchemy import text
        # 本月计划回款金额
        planned_result = db.execute(text("""
            SELECT COALESCE(SUM(planned_amount), 0) as planned
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
        """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        planned_amount = Decimal(str(planned_result[0])) if planned_result and planned_result[0] else Decimal("0")
        
        # 本月实际回款金额（从回款记录表查询，如果有的话）
        # 这里简化处理，从project_payment_plans表的actual_amount字段计算
        actual_result = db.execute(text("""
            SELECT COALESCE(SUM(actual_amount), 0) as actual
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND actual_amount > 0
        """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        actual_amount = Decimal(str(actual_result[0])) if actual_result and actual_result[0] else Decimal("0")
        
        payment_completion_rate = (actual_amount / planned_amount * 100) if planned_amount > 0 else Decimal("0")
        
        # 3. 开票及时率（按时开票数/应开票数）
        # 应开票数：本月计划回款中需要开票的数量
        # 按时开票数：在计划日期前或当天开票的数量
        # 这里简化处理，使用发票表的issue_date和状态
        total_invoices_needed = db.execute(text("""
            SELECT COUNT(*) as count
            FROM project_payment_plans
            WHERE planned_date >= :start_date
            AND planned_date <= :end_date
            AND status IN ('PENDING', 'PARTIAL', 'INVOICED')
        """), {"start_date": month_start.strftime("%Y-%m-%d"), "end_date": month_end.strftime("%Y-%m-%d")}).fetchone()
        total_needed = total_invoices_needed[0] if total_invoices_needed else 0
        
        # 本月已开票数（在计划日期前或当天开票）
        on_time_invoices = (
            db.query(Invoice)
            .join(Contract, Invoice.contract_id == Contract.id)
            .filter(
                Invoice.issue_date >= month_start,
                Invoice.issue_date <= month_end,
                Invoice.status == "ISSUED"
            )
            .count()
        )
        
        invoice_timeliness_rate = (Decimal(on_time_invoices) / Decimal(total_needed) * 100) if total_needed > 0 else Decimal("0")
        
        # 4. 文件流转数（本月处理的文件数）
        # 包括：文件归档、合同审核、合同盖章、回款催收等
        document_flow_count = (
            db.query(DocumentArchive)
            .filter(
                DocumentArchive.created_at >= datetime.combine(month_start, datetime.min.time()),
                DocumentArchive.created_at <= datetime.combine(month_end, datetime.max.time())
            )
            .count()
        )
        
        # 加上合同审核记录
        document_flow_count += (
            db.query(ContractReview)
            .filter(
                ContractReview.created_at >= datetime.combine(month_start, datetime.min.time()),
                ContractReview.created_at <= datetime.combine(month_end, datetime.max.time())
            )
            .count()
        )
        
        # 加上合同盖章记录
        document_flow_count += (
            db.query(ContractSealRecord)
            .filter(
                ContractSealRecord.created_at >= datetime.combine(month_start, datetime.min.time()),
                ContractSealRecord.created_at <= datetime.combine(month_end, datetime.max.time())
            )
            .count()
        )
        
        # 加上回款催收记录
        document_flow_count += (
            db.query(PaymentReminder)
            .filter(
                PaymentReminder.created_at >= datetime.combine(month_start, datetime.min.time()),
                PaymentReminder.created_at <= datetime.combine(month_end, datetime.max.time())
            )
            .count()
        )
        
        performance_data = PerformanceMetricsResponse(
            new_contracts_count=new_contracts,
            payment_completion_rate=payment_completion_rate,
            invoice_timeliness_rate=invoice_timeliness_rate,
            document_flow_count=document_flow_count,
            month=month_str
        )
        
        return ResponseModel(
            code=200,
            message="获取本月绩效指标成功",
            data=performance_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取本月绩效指标失败: {str(e)}")

