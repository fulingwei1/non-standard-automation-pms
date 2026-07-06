# -*- coding: utf-8 -*-
"""文档导出 API。"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from urllib.parse import quote
import io

from app.api import deps
from app.core import security
from app.models.user import User
from app.modules.presale.models.presale_proposal import PresaleProposal
from app.modules.presale.models.audit_pack import AuditPackRequest

router = APIRouter(prefix="/export", tags=["文档导出"])


@router.get("/proposal/{proposal_id}/docx", summary="导出方案为 Word 文档")
def export_proposal_docx(
    proposal_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """把售前方案导出为 Word 文档，销售可编辑后发给客户。"""
    proposal = db.query(PresaleProposal).filter(PresaleProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(404, "方案不存在")

    from app.services.presale.docx_exporter import export_proposal_to_docx

    docx_bytes = export_proposal_to_docx(
        solution=proposal.current_solution or {},
        requirement_text=proposal.requirement_text or "",
        customer_name=proposal.title or "",
    )
    filename = quote(f"技术方案_{proposal.title[:20]}.docx")
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/audit-pack/{pack_id}/docx", summary="导出验厂资料为 Word 文档")
def export_audit_pack_docx(
    pack_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """把验厂资料包导出为 Word 文档。"""
    pack = db.query(AuditPackRequest).filter(AuditPackRequest.id == pack_id).first()
    if not pack:
        raise HTTPException(404, "验厂资料不存在")
    if not pack.generated_html:
        raise HTTPException(400, "资料包尚未生成")

    from app.services.presale.docx_exporter import export_audit_pack_to_docx

    docx_bytes = export_audit_pack_to_docx(
        html_content=pack.generated_html,
        customer_name=pack.customer_name or "",
    )
    filename = quote(f"验厂资料_{pack.customer_name[:20]}.docx")
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
