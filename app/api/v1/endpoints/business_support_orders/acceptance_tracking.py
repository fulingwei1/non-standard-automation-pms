# -*- coding: utf-8 -*-
"""
商务支持模块 - 验收单跟踪 API endpoints
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.acceptance import AcceptanceOrder
from app.models.business_support import AcceptanceTracking, AcceptanceTrackingRecord
from app.models.sales import Contract
from app.schemas.business_support import (
    AcceptanceTrackingCreate, AcceptanceTrackingUpdate, AcceptanceTrackingResponse,
    ConditionCheckRequest, ReminderRequest
)
from app.schemas.common import PaginatedResponse, ResponseModel
from .utils import _send_department_notification

router = APIRouter()


# ==================== 验收单跟踪 ====================


@router.get("/acceptance-tracking", response_model=ResponseModel[PaginatedResponse[AcceptanceTrackingResponse]], summary="获取验收单跟踪列表")
async def get_acceptance_tracking(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    tracking_status: Optional[str] = Query(None, description="跟踪状态筛选"),
    condition_check_status: Optional[str] = Query(None, description="验收条件检查状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取验收单跟踪列表（商务支持角度）"""
    try:
        query = db.query(AcceptanceTracking)

        # 筛选条件
        if project_id:
            query = query.filter(AcceptanceTracking.project_id == project_id)
        if customer_id:
            query = query.filter(AcceptanceTracking.customer_id == customer_id)
        if tracking_status:
            query = query.filter(AcceptanceTracking.tracking_status == tracking_status)
        if condition_check_status:
            query = query.filter(AcceptanceTracking.condition_check_status == condition_check_status)
        if search:
            query = query.filter(
                or_(
                    AcceptanceTracking.acceptance_order_no.like(f"%{search}%"),
                    AcceptanceTracking.customer_name.like(f"%{search}%"),
                    AcceptanceTracking.project_code.like(f"%{search}%")
                )
            )

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(AcceptanceTracking.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 转换为响应格式
        tracking_list = []
        for item in items:
            # 查询跟踪记录
            records_data = [
                {
                    "id": r.id,
                    "tracking_id": r.tracking_id,
                    "record_type": r.record_type,
                    "record_content": r.record_content,
                    "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                    "operator_id": r.operator_id,
                    "operator_name": r.operator_name,
                    "result": r.result,
                    "remark": r.remark,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                    "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
                }
                for r in item.tracking_records
            ]

            tracking_list.append(AcceptanceTrackingResponse(
                id=item.id,
                acceptance_order_id=item.acceptance_order_id,
                acceptance_order_no=item.acceptance_order_no,
                project_id=item.project_id,
                project_code=item.project_code,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                condition_check_status=item.condition_check_status,
                condition_check_result=item.condition_check_result,
                condition_check_date=item.condition_check_date,
                condition_checker_id=item.condition_checker_id,
                tracking_status=item.tracking_status,
                reminder_count=item.reminder_count,
                last_reminder_date=item.last_reminder_date,
                last_reminder_by=item.last_reminder_by,
                received_date=item.received_date,
                signed_file_id=item.signed_file_id,
                report_status=item.report_status,
                report_generated_date=item.report_generated_date,
                report_signed_date=item.report_signed_date,
                report_archived_date=item.report_archived_date,
                warranty_start_date=item.warranty_start_date,
                warranty_end_date=item.warranty_end_date,
                warranty_status=item.warranty_status,
                warranty_expiry_reminded=item.warranty_expiry_reminded,
                contract_id=item.contract_id,
                contract_no=item.contract_no,
                sales_person_id=item.sales_person_id,
                sales_person_name=item.sales_person_name,
                support_person_id=item.support_person_id,
                remark=item.remark,
                tracking_records=records_data,
                created_at=item.created_at,
                updated_at=item.updated_at
            ))

        return ResponseModel(
            code=200,
            message="获取验收单跟踪列表成功",
            data=PaginatedResponse(
                items=tracking_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验收单跟踪列表失败: {str(e)}")


@router.post("/acceptance-tracking", response_model=ResponseModel[AcceptanceTrackingResponse], summary="创建验收单跟踪记录")
async def create_acceptance_tracking(
    tracking_data: AcceptanceTrackingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建验收单跟踪记录"""
    try:
        # 检查验收单是否存在
        acceptance_order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == tracking_data.acceptance_order_id).first()
        if not acceptance_order:
            raise HTTPException(status_code=404, detail="验收单不存在")

        # 检查是否已有跟踪记录
        existing = db.query(AcceptanceTracking).filter(
            AcceptanceTracking.acceptance_order_id == tracking_data.acceptance_order_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该验收单已有跟踪记录")

        # 获取项目信息
        project = db.query(Project).filter(Project.id == acceptance_order.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取客户信息（从项目获取）
        customer = project.customer if hasattr(project, 'customer') else None
        if not customer:
            # 尝试从合同获取
            if tracking_data.contract_id:
                contract = db.query(Contract).filter(Contract.id == tracking_data.contract_id).first()
                if contract:
                    customer = contract.customer

        if not customer:
            raise HTTPException(status_code=404, detail="无法获取客户信息")

        # 获取业务员信息
        sales_person_id = tracking_data.sales_person_id
        sales_person_name = None
        if sales_person_id:
            sales_person = db.query(User).filter(User.id == sales_person_id).first()
            if sales_person:
                sales_person_name = sales_person.username

        # 获取合同信息
        contract_no = None
        if tracking_data.contract_id:
            contract = db.query(Contract).filter(Contract.id == tracking_data.contract_id).first()
            if contract:
                contract_no = contract.contract_code

        # 创建跟踪记录
        tracking = AcceptanceTracking(
            acceptance_order_id=tracking_data.acceptance_order_id,
            acceptance_order_no=acceptance_order.order_no,
            project_id=acceptance_order.project_id,
            project_code=project.project_code,
            customer_id=customer.id,
            customer_name=customer.customer_name,
            contract_id=tracking_data.contract_id,
            contract_no=contract_no,
            sales_person_id=sales_person_id,
            sales_person_name=sales_person_name,
            support_person_id=current_user.id,
            condition_check_status="pending",
            tracking_status="pending",
            report_status="pending",
            warranty_status="not_started",
            remark=tracking_data.remark
        )

        db.add(tracking)
        db.commit()
        db.refresh(tracking)

        return ResponseModel(
            code=200,
            message="创建验收单跟踪记录成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=[],
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建验收单跟踪记录失败: {str(e)}")


@router.get("/acceptance-tracking/{tracking_id}", response_model=ResponseModel[AcceptanceTrackingResponse], summary="获取验收单跟踪详情")
async def get_acceptance_tracking_detail(
    tracking_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取验收单跟踪详情"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]

        return ResponseModel(
            code=200,
            message="获取验收单跟踪详情成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取验收单跟踪详情失败: {str(e)}")


@router.post("/acceptance-tracking/{tracking_id}/check-condition", response_model=ResponseModel[AcceptanceTrackingResponse], summary="验收条件检查")
async def check_acceptance_condition(
    tracking_id: int,
    check_data: ConditionCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """验收条件检查"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        # 更新验收条件检查状态
        tracking.condition_check_status = check_data.condition_check_status
        tracking.condition_check_result = check_data.condition_check_result
        tracking.condition_check_date = datetime.now()
        tracking.condition_checker_id = current_user.id

        # 创建跟踪记录
        record = AcceptanceTrackingRecord(
            tracking_id=tracking_id,
            record_type="condition_check",
            record_content=f"验收条件检查：{check_data.condition_check_status} - {check_data.condition_check_result}",
            record_date=datetime.now(),
            operator_id=current_user.id,
            operator_name=current_user.username,
            result="success" if check_data.condition_check_status == "met" else "pending",
            remark=check_data.remark
        )
        db.add(record)

        db.commit()
        db.refresh(tracking)

        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]

        return ResponseModel(
            code=200,
            message="验收条件检查成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"验收条件检查失败: {str(e)}")


@router.post("/acceptance-tracking/{tracking_id}/remind", response_model=ResponseModel[AcceptanceTrackingResponse], summary="催签验收单")
async def remind_acceptance_signature(
    tracking_id: int,
    reminder_data: ReminderRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """催签验收单"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        # 更新催签信息
        tracking.reminder_count = (tracking.reminder_count or 0) + 1
        tracking.last_reminder_date = datetime.now()
        tracking.last_reminder_by = current_user.id
        tracking.tracking_status = "reminded"

        # 创建跟踪记录
        record = AcceptanceTrackingRecord(
            tracking_id=tracking_id,
            record_type="reminder",
            record_content=reminder_data.reminder_content or f"第{tracking.reminder_count}次催签验收单",
            record_date=datetime.now(),
            operator_id=current_user.id,
            operator_name=current_user.username,
            result="success",
            remark=reminder_data.remark
        )
        db.add(record)

        db.commit()
        db.refresh(tracking)

        # 实际发送催签通知（邮件、短信、系统消息等）
        # 获取验收单信息
        acceptance_order = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.id == tracking.acceptance_order_id
        ).first()

        if acceptance_order:
            # 获取项目信息
            project = None
            if acceptance_order.project_id:
                project = db.query(Project).filter(
                    Project.id == acceptance_order.project_id
                ).first()

            # 通知项目经理和销售人员
            notified_users = set()

            # 通知项目经理
            if project and project.pm_id:
                title = f"验收单催签提醒：{acceptance_order.order_no}"
                content = f"验收单 {acceptance_order.order_no} 需要催签。\n\n项目名称：{project.project_name if project else ''}\n验收类型：{acceptance_order.acceptance_type}\n客户名称：{acceptance_order.customer_name}\n计划验收日期：{acceptance_order.plan_accept_date.strftime('%Y-%m-%d') if acceptance_order.plan_accept_date else '未设置'}\n已催签{tracking.reminder_count or 0}次\n\n请及时跟进。"

                _send_department_notification(
                    db=db,
                    user_id=project.pm_id,
                    notification_type="ACCEPTANCE_REMINDER",
                    title=title,
                    content=content,
                    source_type="ACCEPTANCE_TRACKING",
                    source_id=tracking.id,
                    priority="HIGH",
                    extra_data={
                        "order_no": acceptance_order.order_no,
                        "reminder_count": tracking.reminder_count
                    }
                )
                notified_users.add(project.pm_id)

            # 通知销售人员
            if acceptance_order.sales_id and acceptance_order.sales_id not in notified_users:
                _send_department_notification(
                    db=db,
                    user_id=acceptance_order.sales_id,
                    notification_type="ACCEPTANCE_REMINDER",
                    title=f"验收单催签提醒：{acceptance_order.order_no}",
                    content=f"验收单 {acceptance_order.order_no} 需要催签，已催签{tracking.reminder_count or 0}次。",
                    source_type="ACCEPTANCE_TRACKING",
                    source_id=tracking.id,
                    priority="HIGH"
                )
                notified_users.add(acceptance_order.sales_id)

        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]

        return ResponseModel(
            code=200,
            message="催签成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"催签失败: {str(e)}")


@router.put("/acceptance-tracking/{tracking_id}", response_model=ResponseModel[AcceptanceTrackingResponse], summary="更新验收单跟踪记录")
async def update_acceptance_tracking(
    tracking_id: int,
    tracking_data: AcceptanceTrackingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新验收单跟踪记录"""
    try:
        tracking = db.query(AcceptanceTracking).filter(AcceptanceTracking.id == tracking_id).first()
        if not tracking:
            raise HTTPException(status_code=404, detail="验收单跟踪记录不存在")

        # 更新字段
        update_data = tracking_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tracking, key, value)

        db.commit()
        db.refresh(tracking)

        # 查询跟踪记录
        records_data = [
            {
                "id": r.id,
                "tracking_id": r.tracking_id,
                "record_type": r.record_type,
                "record_content": r.record_content,
                "record_date": r.record_date.strftime("%Y-%m-%d %H:%M:%S") if r.record_date else None,
                "operator_id": r.operator_id,
                "operator_name": r.operator_name,
                "result": r.result,
                "remark": r.remark,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
            }
            for r in tracking.tracking_records
        ]

        return ResponseModel(
            code=200,
            message="更新验收单跟踪记录成功",
            data=AcceptanceTrackingResponse(
                id=tracking.id,
                acceptance_order_id=tracking.acceptance_order_id,
                acceptance_order_no=tracking.acceptance_order_no,
                project_id=tracking.project_id,
                project_code=tracking.project_code,
                customer_id=tracking.customer_id,
                customer_name=tracking.customer_name,
                condition_check_status=tracking.condition_check_status,
                condition_check_result=tracking.condition_check_result,
                condition_check_date=tracking.condition_check_date,
                condition_checker_id=tracking.condition_checker_id,
                tracking_status=tracking.tracking_status,
                reminder_count=tracking.reminder_count,
                last_reminder_date=tracking.last_reminder_date,
                last_reminder_by=tracking.last_reminder_by,
                received_date=tracking.received_date,
                signed_file_id=tracking.signed_file_id,
                report_status=tracking.report_status,
                report_generated_date=tracking.report_generated_date,
                report_signed_date=tracking.report_signed_date,
                report_archived_date=tracking.report_archived_date,
                warranty_start_date=tracking.warranty_start_date,
                warranty_end_date=tracking.warranty_end_date,
                warranty_status=tracking.warranty_status,
                warranty_expiry_reminded=tracking.warranty_expiry_reminded,
                contract_id=tracking.contract_id,
                contract_no=tracking.contract_no,
                sales_person_id=tracking.sales_person_id,
                sales_person_name=tracking.sales_person_name,
                support_person_id=tracking.support_person_id,
                remark=tracking.remark,
                tracking_records=records_data,
                created_at=tracking.created_at,
                updated_at=tracking.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新验收单跟踪记录失败: {str(e)}")
