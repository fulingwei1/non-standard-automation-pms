# -*- coding: utf-8 -*-
"""
投标管理 API endpoints
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_like_filter
from app.core import security
from app.models.business_support import BiddingProject
from app.models.user import User
from app.schemas.business_support import (
    BiddingProjectCreate,
    BiddingProjectResponse,
    BiddingProjectUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


def generate_bidding_no(db: Session) -> str:
    """生成投标编号：BD250101-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m%d")
    prefix = f"BD{month_str}-"

    max_bidding_query = apply_like_filter(
        db.query(BiddingProject),
        BiddingProject,
        f"{prefix}%",
        "bidding_no",
        use_ilike=False,
    )
    max_bidding = max_bidding_query.order_by(desc(BiddingProject.bidding_no)).first()

    if max_bidding:
        try:
            seq = int(max_bidding.bidding_no.split("-")[-1]) + 1
        except (ValueError, TypeError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:03d}"


@router.get("", response_model=ResponseModel[PaginatedResponse[BiddingProjectResponse]], summary="获取投标项目列表")
async def get_bidding_projects(
    pagination: PaginationParams = Depends(get_pagination_query),
    bidding_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
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
        if bidding_status:
            query = query.filter(BiddingProject.status == bidding_status)
        if bid_result:
            query = query.filter(BiddingProject.bid_result == bid_result)
        if customer_id:
            query = query.filter(BiddingProject.customer_id == customer_id)

        # 应用关键词过滤（项目名称/投标编号/客户名称）
        query = apply_keyword_filter(query, BiddingProject, search, ["project_name", "bidding_no", "customer_name"])

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(BiddingProject.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
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
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total)
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取投标项目列表失败: {str(e)}")


@router.post("", response_model=ResponseModel[BiddingProjectResponse], summary="创建投标项目")
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


@router.get("/{bidding_id}", response_model=ResponseModel[BiddingProjectResponse], summary="获取投标项目详情")
async def get_bidding_project(
    bidding_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取投标项目详情"""
    try:
        bidding_project = get_or_404(db, BiddingProject, bidding_id, "投标项目不存在")

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


@router.put("/{bidding_id}", response_model=ResponseModel[BiddingProjectResponse], summary="更新投标项目")
async def update_bidding_project(
    bidding_id: int,
    bidding_data: BiddingProjectUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:update"))
):
    """更新投标项目"""
    try:
        bidding_project = get_or_404(db, BiddingProject, bidding_id, "投标项目不存在")

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
