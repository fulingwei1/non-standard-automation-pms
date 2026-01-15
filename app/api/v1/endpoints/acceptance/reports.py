# -*- coding: utf-8 -*-
"""
验收报告与签字管理端点

包含：签字管理、报告生成、报告下载、客户签署文件上传、奖金计算触发
"""

import os
import logging
from typing import Any, List
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Response, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.acceptance import (
    AcceptanceOrder, AcceptanceSignature, AcceptanceReport
)
from app.schemas.acceptance import (
    AcceptanceOrderResponse,
    AcceptanceSignatureCreate, AcceptanceSignatureResponse,
    AcceptanceReportGenerateRequest, AcceptanceReportResponse
)
from app.schemas.common import ResponseModel

# Import for returning order response
from .orders import read_acceptance_order

router = APIRouter()


# ==================== 验收签字 ====================

@router.get("/acceptance-orders/{order_id}/signatures", response_model=List[AcceptanceSignatureResponse], status_code=status.HTTP_200_OK)
def read_acceptance_signatures(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收签字列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    signatures = db.query(AcceptanceSignature).filter(AcceptanceSignature.order_id == order_id).order_by(AcceptanceSignature.signed_at).all()

    items = []
    for sig in signatures:
        items.append(AcceptanceSignatureResponse(
            id=sig.id,
            order_id=sig.order_id,
            signer_type=sig.signer_type,
            signer_role=sig.signer_role,
            signer_name=sig.signer_name,
            signer_company=sig.signer_company,
            signed_at=sig.signed_at,
            ip_address=sig.ip_address,
            created_at=sig.created_at,
            updated_at=sig.updated_at
        ))

    return items


@router.post("/acceptance-orders/{order_id}/signatures", response_model=AcceptanceSignatureResponse, status_code=status.HTTP_201_CREATED)
def add_acceptance_signature(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    order_id: int,
    signature_in: AcceptanceSignatureCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加签字
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只能为已完成状态的验收单添加签字")

    if signature_in.order_id != order_id:
        raise HTTPException(status_code=400, detail="签字所属验收单ID不匹配")

    signature = AcceptanceSignature(
        order_id=order_id,
        signer_type=signature_in.signer_type,
        signer_role=signature_in.signer_role,
        signer_name=signature_in.signer_name,
        signer_company=signature_in.signer_company,
        signature_data=signature_in.signature_data,
        signed_at=datetime.now(),
        ip_address=request.client.host if request and request.client else None
    )

    # 如果是QA签字，更新验收单
    if signature_in.signer_type == "QA":
        order.qa_signer_id = current_user.id
        order.qa_signed_at = datetime.now()
        db.add(order)

    # 如果是客户签字，更新验收单
    if signature_in.signer_type == "CUSTOMER":
        order.customer_signer = signature_in.signer_name
        order.customer_signed_at = datetime.now()
        order.customer_signature = signature_in.signature_data
        db.add(order)

    db.add(signature)
    db.commit()
    db.refresh(signature)

    return AcceptanceSignatureResponse(
        id=signature.id,
        order_id=signature.order_id,
        signer_type=signature.signer_type,
        signer_role=signature.signer_role,
        signer_name=signature.signer_name,
        signer_company=signature.signer_company,
        signed_at=signature.signed_at,
        ip_address=signature.ip_address,
        created_at=signature.created_at,
        updated_at=signature.updated_at
    )


# ==================== 验收报告 ====================

def generate_report_no(db: Session, report_type: str) -> str:
    """生成报告编号：RPT-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RPT-{today}-"
    max_report = (
        db.query(AcceptanceReport)
        .filter(AcceptanceReport.report_no.like(f"{prefix}%"))
        .order_by(desc(AcceptanceReport.report_no))
        .first()
    )
    if max_report:
        seq = int(max_report.report_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_pdf_report(
    order: AcceptanceOrder,
    db: Session,
    report_no: str,
    version: int,
    current_user: User,
    include_signatures: bool = True
) -> bytes:
    """
    生成PDF格式的验收报告

    Args:
        order: 验收单对象
        db: 数据库会话
        report_no: 报告编号
        version: 报告版本号
        current_user: 当前用户
        include_signatures: 是否包含签字信息

    Returns:
        PDF文件的字节内容
    """
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PDF生成功能不可用，请安装reportlab库：pip install reportlab"
        )

    from app.services.pdf_styles import get_pdf_styles
    from app.services.pdf_content_builders import (
        build_basic_info_section,
        build_statistics_section,
        build_conclusion_section,
        build_issues_section,
        build_signatures_section,
        build_footer_section
    )

    # 创建PDF缓冲区
    buffer = BytesIO()

    # 创建PDF文档
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # 获取样式
    styles = get_pdf_styles()

    # 获取项目和设备信息
    project = db.query(Project).filter(Project.id == order.project_id).first()
    machine = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()

    # 构建PDF内容
    story = []

    # 基本信息部分
    story.extend(build_basic_info_section(order, project, machine, report_no, version, styles))

    # 验收项目统计部分
    story.extend(build_statistics_section(order, db, styles))

    # 验收结论部分
    story.extend(build_conclusion_section(order, styles))

    # 验收问题部分
    story.extend(build_issues_section(order, db, styles))

    # 签字信息部分
    if include_signatures:
        story.extend(build_signatures_section(order, db, styles))

    # 页脚部分
    story.extend(build_footer_section(current_user, styles))

    # 构建PDF
    doc.build(story)

    # 获取PDF字节
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


@router.post("/acceptance-orders/{order_id}/report", response_model=AcceptanceReportResponse, status_code=status.HTTP_201_CREATED)
def generate_acceptance_report(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    report_in: AcceptanceReportGenerateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成验收报告
    """
    from app.services.acceptance_report_service import (
        generate_report_no,
        get_report_version,
        build_report_content,
        save_report_file
    )

    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只有已完成的验收单才能生成报告")

    # 生成报告编号和版本
    report_no = generate_report_no(db, report_in.report_type)
    version = get_report_version(db, order_id, report_in.report_type)

    # 构建报告内容
    report_content = build_report_content(db, order, report_no, version, current_user)

    # 保存报告文件
    file_rel_path, file_size, file_hash = save_report_file(
        report_content, report_no, report_in.report_type,
        report_in.include_signatures, order, db, current_user
    )

    # 创建报告记录
    report = AcceptanceReport(
        order_id=order_id,
        report_no=report_no,
        report_type=report_in.report_type,
        version=version,
        report_content=report_content,
        file_path=file_rel_path,
        file_size=file_size,
        file_hash=file_hash,
        generated_at=datetime.now(),
        generated_by=current_user.id
    )

    db.add(report)

    # 更新验收单的报告文件路径（如果有最新报告）
    if not order.report_file_path or report_in.report_type == "FINAL":
        order.report_file_path = file_rel_path
        db.add(order)

    db.commit()
    db.refresh(report)

    return AcceptanceReportResponse(
        id=report.id,
        order_id=report.order_id,
        report_no=report.report_no,
        report_type=report.report_type,
        version=report.version,
        report_content=report.report_content,
        file_path=report.file_path,
        file_size=report.file_size,
        file_hash=report.file_hash,
        generated_at=report.generated_at,
        generated_by=report.generated_by,
        generated_by_name=current_user.real_name or current_user.username,
        created_at=report.created_at,
        updated_at=report.updated_at
    )


@router.get("/acceptance-reports/{report_id}/download", response_class=FileResponse)
def download_acceptance_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载验收报告（支持PDF和文本格式）
    """
    report = db.query(AcceptanceReport).filter(AcceptanceReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="验收报告不存在")

    if not report.file_path:
        raise HTTPException(status_code=404, detail="报告文件不存在")

    # 安全检查：解析为规范路径，防止路径遍历攻击
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    file_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, report.file_path))

    if not file_path.startswith(upload_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        # 如果文件不存在，返回报告内容作为文本
        content = report.report_content or "报告内容为空"
        return Response(
            content=content.encode('utf-8'),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={report.report_no}.txt"
            }
        )

    filename = os.path.basename(file_path)
    # 根据文件扩展名设置媒体类型
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".txt"):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@router.get("/acceptance-orders/{order_id}/report", response_model=List[AcceptanceReportResponse], status_code=status.HTTP_200_OK)
def read_acceptance_reports(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收单的所有报告列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    reports = db.query(AcceptanceReport).filter(
        AcceptanceReport.order_id == order_id
    ).order_by(desc(AcceptanceReport.version)).all()

    items = []
    for report in reports:
        generated_by_name = None
        if report.generated_by:
            user = db.query(User).filter(User.id == report.generated_by).first()
            generated_by_name = user.real_name or user.username if user else None

        items.append(AcceptanceReportResponse(
            id=report.id,
            order_id=report.order_id,
            report_no=report.report_no,
            report_type=report.report_type,
            version=report.version,
            report_content=report.report_content,
            file_path=report.file_path,
            file_size=report.file_size,
            file_hash=report.file_hash,
            generated_at=report.generated_at,
            generated_by=report.generated_by,
            generated_by_name=generated_by_name,
            created_at=report.created_at,
            updated_at=report.updated_at
        ))

    return items


# ==================== 客户签署验收单上传 ====================

@router.post("/acceptance-orders/{order_id}/upload-signed-document", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
async def upload_customer_signed_document(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    file: UploadFile = File(..., description="客户签署的验收单文件"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上传客户签署的验收单文件

    上传后，验收单将被标记为正式完成（is_officially_completed=True）
    只有状态为COMPLETED且验收结果为PASSED的验收单才能上传签署文件
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    # 验证验收单状态
    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只有已完成状态的验收单才能上传客户签署文件")

    if order.overall_result != "PASSED":
        raise HTTPException(status_code=400, detail="只有验收通过的验收单才能上传客户签署文件")

    # 验证项目关联
    project = db.query(Project).filter(Project.id == order.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="关联的项目不存在")

    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, "acceptance_signed_documents")
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名
    import uuid
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    unique_filename = f"{order.order_no}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    # 保存文件
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 计算相对路径（相对于UPLOAD_DIR）
    relative_path = os.path.relpath(file_path, settings.UPLOAD_DIR)

    # 更新验收单
    order.customer_signed_file_path = relative_path
    order.is_officially_completed = True
    order.officially_completed_at = datetime.now()

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)


@router.get("/acceptance-orders/{order_id}/download-signed-document", response_class=FileResponse)
def download_customer_signed_document(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载客户签署的验收单文件
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if not order.customer_signed_file_path:
        raise HTTPException(status_code=404, detail="客户签署文件不存在")

    # 安全检查：解析为规范路径，防止路径遍历攻击
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    file_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, order.customer_signed_file_path))

    if not file_path.startswith(upload_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    filename = os.path.basename(file_path)
    media_type = "application/pdf" if filename.endswith(".pdf") else "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


# ==================== 手动触发奖金计算 ====================

@router.post("/acceptance-orders/{order_id}/trigger-bonus-calculation", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def trigger_bonus_calculation_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    手动触发验收单关联的奖金计算

    只有正式完成的验收单（已上传客户签署文件）才能触发奖金计算
    """
    logger = logging.getLogger(__name__)

    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

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
        from app.services.bonus_calculator import BonusCalculator
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
