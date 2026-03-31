# -*- coding: utf-8 -*-
"""
异常处理增强服务（Facade）

Delegates to focused sub-services:
  - EscalationService  — escalation and flow tracking
  - KnowledgeService   — knowledge base CRUD and search
  - StatisticsService  — statistics and recurrence analysis
  - PDCAService        — PDCA lifecycle management
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.production import ExceptionHandlingFlow
from app.schemas.production.exception_enhancement import (
    ExceptionEscalateResponse,
    ExceptionStatisticsResponse,
    FlowTrackingResponse,
    KnowledgeListResponse,
    KnowledgeResponse,
    PDCAResponse,
    RecurrenceAnalysisResponse,
)

from .escalation_service import EscalationService
from .knowledge_service import KnowledgeService
from .pdca_service import PDCAService
from .statistics_service import StatisticsService


class ExceptionEnhancementService:
    def __init__(self, db: Session):
        self.db = db
        self._escalation = EscalationService(db)
        self._knowledge = KnowledgeService(db)
        self._statistics = StatisticsService(db)
        self._pdca = PDCAService(db)

    # ==================== 异常升级 ====================

    def escalate_exception(
        self,
        exception_id: int,
        escalation_level: str,
        reason: str,
        escalated_to_id: Optional[int],
    ) -> ExceptionEscalateResponse:
        """异常升级"""
        return self._escalation.escalate_exception(
            exception_id, escalation_level, reason, escalated_to_id
        )

    # ==================== 处理流程跟踪 ====================

    def get_exception_flow(self, exception_id: int) -> FlowTrackingResponse:
        """获取异常处理流程跟踪"""
        return self._escalation.get_exception_flow(exception_id)

    def calculate_flow_duration(self, flow: ExceptionHandlingFlow):
        """计算流程时长"""
        return self._escalation.calculate_flow_duration(flow)

    # ==================== 异常知识库 ====================

    def create_knowledge(self, request, creator_id: int) -> KnowledgeResponse:
        """添加知识库条目"""
        return self._knowledge.create_knowledge(request, creator_id)

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
        return self._knowledge.search_knowledge(
            keyword, exception_type, exception_level, is_approved, offset, limit, page, page_size
        )

    def build_knowledge_response(self, knowledge) -> KnowledgeResponse:
        """构建知识库响应"""
        return self._knowledge.build_knowledge_response(knowledge)

    # ==================== 异常统计分析 ====================

    def get_exception_statistics(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> ExceptionStatisticsResponse:
        """异常统计分析"""
        return self._statistics.get_exception_statistics(start_date, end_date)

    # ==================== 重复异常分析 ====================

    def analyze_recurrence(
        self,
        exception_type: Optional[str],
        days: int,
    ) -> List[RecurrenceAnalysisResponse]:
        """重复异常分析"""
        return self._statistics.analyze_recurrence(exception_type, days)

    def find_similar_exceptions(self, exceptions: list) -> List[dict]:
        """查找相似异常（Jaccard相似度算法）"""
        return self._statistics.find_similar_exceptions(exceptions)

    def analyze_time_trend(self, exceptions: list, days: int) -> List[dict]:
        """分析时间趋势"""
        return self._statistics.analyze_time_trend(exceptions, days)

    def extract_common_root_causes(self, exception_ids: List[int]) -> List[str]:
        """提取常见根因"""
        return self._statistics.extract_common_root_causes(exception_ids)

    # ==================== PDCA管理 ====================

    def create_pdca(self, request, current_user_id: int) -> PDCAResponse:
        """创建PDCA记录"""
        return self._pdca.create_pdca(request, current_user_id)

    def advance_pdca_stage(self, pdca_id: int, request) -> PDCAResponse:
        """推进PDCA阶段"""
        return self._pdca.advance_pdca_stage(pdca_id, request)

    def build_pdca_response(self, pdca) -> PDCAResponse:
        """构建PDCA响应"""
        return self._pdca.build_pdca_response(pdca)
