# -*- coding: utf-8 -*-
"""
验收单跟踪 - 辅助函数

包含响应构建等辅助函数
"""

from app.models.business_support import AcceptanceTracking
from app.schemas.business_support import AcceptanceTrackingResponse


def build_tracking_response(tracking: AcceptanceTracking) -> AcceptanceTrackingResponse:
    """构建验收单跟踪响应对象"""
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

    return AcceptanceTrackingResponse(
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
