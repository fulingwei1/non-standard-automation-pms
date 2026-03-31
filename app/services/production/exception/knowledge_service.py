# -*- coding: utf-8 -*-
"""
异常知识库服务
"""
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_pagination
from app.models.production import ExceptionKnowledge
from app.models.user import User
from app.schemas.production.exception_enhancement import (
    KnowledgeListResponse,
    KnowledgeResponse,
)
from app.utils.db_helpers import save_obj


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db

    def create_knowledge(self, request, creator_id: int) -> KnowledgeResponse:
        """添加知识库条目"""
        knowledge = ExceptionKnowledge(
            title=request.title,
            exception_type=request.exception_type,
            exception_level=request.exception_level,
            symptom_description=request.symptom_description,
            solution=request.solution,
            solution_steps=request.solution_steps,
            prevention_measures=request.prevention_measures,
            keywords=request.keywords,
            source_exception_id=request.source_exception_id,
            attachments=request.attachments,
            creator_id=creator_id,
        )

        save_obj(self.db, knowledge)

        return self.build_knowledge_response(knowledge)

    def search_knowledge(
        self,
        keyword: Optional[str],
        exception_type: Optional[str],
        exception_level: Optional[str],
        is_approved: Optional[bool],
        offset: int,
        limit: int,
        page: int,
        page_size: int,
    ) -> KnowledgeListResponse:
        """知识库搜索（支持关键词、异常类型匹配）"""
        from sqlalchemy import or_

        query = self.db.query(ExceptionKnowledge)

        # 关键词搜索（标题、症状、解决方案、关键词）
        if keyword:
            keyword_filter = or_(
                ExceptionKnowledge.title.contains(keyword),
                ExceptionKnowledge.symptom_description.contains(keyword),
                ExceptionKnowledge.solution.contains(keyword),
                ExceptionKnowledge.keywords.contains(keyword),
            )
            query = query.filter(keyword_filter)

        # 异常类型过滤
        if exception_type:
            query = query.filter(ExceptionKnowledge.exception_type == exception_type)

        # 异常级别过滤
        if exception_level:
            query = query.filter(ExceptionKnowledge.exception_level == exception_level)

        # 审核状态过滤
        if is_approved is not None:
            query = query.filter(ExceptionKnowledge.is_approved == is_approved)

        # 按引用次数和创建时间排序
        query = query.order_by(
            desc(ExceptionKnowledge.reference_count), desc(ExceptionKnowledge.created_at)
        )

        # 分页
        total = query.count()
        items = apply_pagination(query, offset, limit).all()

        return KnowledgeListResponse(
            items=[self.build_knowledge_response(k) for k in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def build_knowledge_response(self, knowledge: ExceptionKnowledge) -> KnowledgeResponse:
        """构建知识库响应"""
        creator_name = None
        if knowledge.creator_id:
            creator = self.db.query(User).filter(User.id == knowledge.creator_id).first()
            if creator:
                creator_name = creator.username

        approver_name = None
        if knowledge.approver_id:
            approver = self.db.query(User).filter(User.id == knowledge.approver_id).first()
            if approver:
                approver_name = approver.username

        return KnowledgeResponse(
            id=knowledge.id,
            title=knowledge.title,
            exception_type=knowledge.exception_type,
            exception_level=knowledge.exception_level,
            symptom_description=knowledge.symptom_description,
            solution=knowledge.solution,
            solution_steps=knowledge.solution_steps,
            prevention_measures=knowledge.prevention_measures,
            keywords=knowledge.keywords,
            source_exception_id=knowledge.source_exception_id,
            reference_count=knowledge.reference_count,
            success_count=knowledge.success_count,
            last_referenced_at=knowledge.last_referenced_at,
            is_approved=knowledge.is_approved,
            approver_name=approver_name,
            approved_at=knowledge.approved_at,
            creator_name=creator_name,
            attachments=knowledge.attachments,
            remark=knowledge.remark,
            created_at=knowledge.created_at,
            updated_at=knowledge.updated_at,
        )
