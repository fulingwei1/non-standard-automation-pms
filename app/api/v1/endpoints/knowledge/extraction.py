# -*- coding: utf-8 -*-
"""
经验教训自动提取 API
项目结项时调用，自动从风险/问题/变更/进度日志中提取知识
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.knowledge_base import ExtractionRequest
from app.services.knowledge.extraction_service import KnowledgeExtractionService

router = APIRouter()


@router.post("/extract", response_model=ResponseModel)
def extract_knowledge(
    req: ExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    项目结项时一键提取经验知识

    自动从以下数据中提取知识：
    - 风险记录 → 已发生风险 + 应对措施
    - 问题记录 → 典型问题 + 解决方案
    - 变更单 → 高频变更类型 + 原因分析
    - 进度日志 → 关键节点延误原因
    """
    service = KnowledgeExtractionService(db)

    result = service.extract_all(
        project_id=req.project_id,
        extract_risks=req.extract_risks,
        extract_issues=req.extract_issues,
        extract_ecns=req.extract_ecns,
        extract_logs=req.extract_logs,
        auto_publish=req.auto_publish,
        created_by=current_user.id,
    )

    db.commit()

    entries_data = [
        {
            "id": e.id,
            "entry_code": e.entry_code,
            "knowledge_type": e.knowledge_type.value if hasattr(e.knowledge_type, "value") else str(e.knowledge_type),
            "title": e.title,
            "summary": e.summary,
            "status": e.status.value if hasattr(e.status, "value") else str(e.status),
        }
        for e in result["entries"]
    ]

    return ResponseModel(
        code=200,
        message=f"成功提取 {result['total_extracted']} 条知识",
        data={
            "project_id": result["project_id"],
            "total_extracted": result["total_extracted"],
            "risk_entries": result["risk_entries"],
            "issue_entries": result["issue_entries"],
            "change_entries": result["change_entries"],
            "delay_entries": result["delay_entries"],
            "entries": entries_data,
        },
    )
