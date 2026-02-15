"""
AI报价单自动生成API路由
Team 5: AI Quotation Generator API
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.base import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.presale_ai_quotation import (
    QuotationGenerateRequest, QuotationResponse, QuotationUpdateRequest,
    QuotationApprovalRequest, QuotationApprovalResponse, QuotationEmailRequest,
    ThreeTierQuotationRequest, ThreeTierQuotationResponse, QuotationHistoryResponse,
    QuotationVersionResponse
)
from app.services.presale_ai_quotation_service import AIQuotationGeneratorService
from app.services.quotation_pdf_service import QuotationPDFService


router = APIRouter(prefix="/api/v1/presale/ai", tags=["AI报价单生成"])


@router.post("/generate-quotation", response_model=QuotationResponse, summary="生成报价单")
async def generate_quotation(
    request: QuotationGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成AI报价单
    
    - **presale_ticket_id**: 售前工单ID
    - **customer_id**: 客户ID（可选）
    - **quotation_type**: 报价单类型（basic/standard/premium）
    - **items**: 报价项清单
    - **tax_rate**: 税率（默认0.13）
    - **discount_rate**: 折扣率（默认0）
    - **validity_days**: 有效期天数（默认30）
    - **payment_terms**: 付款条款（可选，不提供则AI生成）
    """
    try:
        service = AIQuotationGeneratorService(db)
        quotation = service.generate_quotation(request, current_user.id)
        return quotation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成报价单失败: {str(e)}"
        )


@router.post("/generate-three-tier-quotations", response_model=ThreeTierQuotationResponse, summary="生成三档报价方案")
async def generate_three_tier_quotations(
    request: ThreeTierQuotationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成三档报价方案（基础版、标准版、高级版）
    
    - **presale_ticket_id**: 售前工单ID
    - **customer_id**: 客户ID（可选）
    - **base_requirements**: 基础需求描述
    - **budget_range**: 预算范围（可选）
    - **priority_features**: 优先功能列表（可选）
    
    返回三档方案及智能推荐
    """
    try:
        service = AIQuotationGeneratorService(db)
        basic, standard, premium = service.generate_three_tier_quotations(request, current_user.id)
        
        # 生成对比和推荐
        comparison = {
            "price_range": {
                "basic": float(basic.total),
                "standard": float(standard.total),
                "premium": float(premium.total)
            },
            "features_count": {
                "basic": len(basic.items),
                "standard": len(standard.items),
                "premium": len(premium.items)
            },
            "discount": {
                "basic": float(basic.discount),
                "standard": float(standard.discount),
                "premium": float(premium.discount)
            }
        }
        
        # 智能推荐逻辑
        recommendation = "standard"
        if request.budget_range:
            avg_budget = (request.budget_range.get("min", 0) + request.budget_range.get("max", 999999)) / 2
            if avg_budget < float(standard.total):
                recommendation = "basic"
            elif avg_budget > float(standard.total) * 1.5:
                recommendation = "premium"
        
        return {
            "basic": basic,
            "standard": standard,
            "premium": premium,
            "recommendation": recommendation,
            "comparison": comparison
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成三档方案失败: {str(e)}"
        )


@router.get("/quotation/{quotation_id}", response_model=QuotationResponse, summary="获取报价单")
async def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定报价单详情
    """
    service = AIQuotationGeneratorService(db)
    quotation = service.get_quotation(quotation_id)
    
    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"报价单 {quotation_id} 不存在"
        )
    
    return quotation


@router.put("/quotation/{quotation_id}", response_model=QuotationResponse, summary="更新报价单")
async def update_quotation(
    quotation_id: int,
    request: QuotationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新报价单
    
    - 支持更新报价项、税率、折扣、有效期、付款条款、状态等
    - 每次更新会自动创建新版本快照
    """
    try:
        service = AIQuotationGeneratorService(db)
        quotation = service.update_quotation(quotation_id, request, current_user.id)
        return quotation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新报价单失败: {str(e)}"
        )


@router.post("/export-quotation-pdf/{quotation_id}", summary="导出报价单PDF")
async def export_quotation_pdf(
    quotation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出报价单为PDF
    
    返回PDF文件URL
    """
    try:
        quotation_service = AIQuotationGeneratorService(db)
        quotation = quotation_service.get_quotation(quotation_id)
        
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报价单 {quotation_id} 不存在"
            )
        
        # 生成PDF
        pdf_service = QuotationPDFService()
        pdf_path = pdf_service.generate_pdf(quotation)
        
        # 更新报价单PDF URL
        quotation.pdf_url = pdf_path
        db.commit()
        
        return {
            "quotation_id": quotation_id,
            "pdf_url": pdf_path,
            "message": "PDF生成成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出PDF失败: {str(e)}"
        )


@router.post("/send-quotation-email/{quotation_id}", summary="发送报价单邮件")
async def send_quotation_email(
    quotation_id: int,
    request: QuotationEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送报价单邮件
    
    - **to_email**: 收件人邮箱
    - **cc_emails**: 抄送邮箱列表（可选）
    - **subject**: 邮件主题（可选）
    - **message**: 邮件正文（可选）
    - **include_pdf**: 是否包含PDF附件（默认true）
    """
    try:
        quotation_service = AIQuotationGeneratorService(db)
        quotation = quotation_service.get_quotation(quotation_id)
        
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报价单 {quotation_id} 不存在"
            )
        
        # 如果需要PDF但还没有生成，先生成PDF
        if request.include_pdf and not quotation.pdf_url:
            pdf_service = QuotationPDFService()
            pdf_path = pdf_service.generate_pdf(quotation)
            quotation.pdf_url = pdf_path
            db.commit()
        
        # 异步发送邮件（这里暂时返回成功，实际应该调用邮件服务）
        background_tasks.add_task(
            _send_email_task,
            to_email=request.to_email,
            cc_emails=request.cc_emails or [],
            subject=request.subject or f"报价单 - {quotation.quotation_number}",
            message=request.message or "请查收附件中的报价单。",
            pdf_path=quotation.pdf_url if request.include_pdf else None
        )
        
        # 更新报价单状态为已发送
        quotation.status = "sent"
        db.commit()
        
        return {
            "quotation_id": quotation_id,
            "to_email": request.to_email,
            "message": "邮件发送成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送邮件失败: {str(e)}"
        )


@router.get("/quotation-history/{ticket_id}", response_model=QuotationHistoryResponse, summary="获取报价单版本历史")
async def get_quotation_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定工单的所有报价单及版本历史
    """
    try:
        service = AIQuotationGeneratorService(db)
        quotations = service.get_quotation_history(ticket_id)
        
        if not quotations:
            return {
                "quotation_id": None,
                "current_version": 0,
                "versions": [],
                "total_versions": 0
            }
        
        # 获取最新报价单的所有版本
        latest_quotation = quotations[0]
        versions = service.get_quotation_versions(latest_quotation.id)
        
        return {
            "quotation_id": latest_quotation.id,
            "current_version": latest_quotation.version,
            "versions": versions,
            "total_versions": len(versions)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史失败: {str(e)}"
        )


@router.post("/approve-quotation/{quotation_id}", response_model=QuotationApprovalResponse, summary="审批报价单")
async def approve_quotation(
    quotation_id: int,
    request: QuotationApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    审批报价单
    
    - **status**: 审批状态 (approved/rejected)
    - **comments**: 审批意见（可选）
    """
    try:
        service = AIQuotationGeneratorService(db)
        approval = service.approve_quotation(
            quotation_id=quotation_id,
            approver_id=current_user.id,
            status=request.status,
            comments=request.comments
        )
        return approval
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"审批失败: {str(e)}"
        )


# ========== 辅助函数 ==========

async def _send_email_task(
    to_email: str, 
    cc_emails: List[str], 
    subject: str, 
    message: str, 
    pdf_path: str = None
):
    """
    异步发送邮件任务
    TODO: 集成实际的邮件服务（如SendGrid, AWS SES等）
    """
    # 这里应该调用实际的邮件服务
    print(f"发送邮件到 {to_email}")
    print(f"主题: {subject}")
    print(f"内容: {message}")
    if pdf_path:
        print(f"附件: {pdf_path}")
    # 实际实现：
    # email_service = EmailService()
    # await email_service.send_email(to_email, cc_emails, subject, message, pdf_path)
