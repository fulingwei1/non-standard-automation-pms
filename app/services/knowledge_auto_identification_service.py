# -*- coding: utf-8 -*-
"""
知识贡献自动识别服务
从代码仓库、文档系统、服务工单自动识别知识贡献
"""

from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.models.engineer_performance import (
    CodeModule,
    KnowledgeContribution,
)
from app.models.service import KnowledgeBase, ServiceTicket
from app.services.knowledge_extraction_service import auto_extract_knowledge_from_ticket
from app.utils.db_helpers import save_obj


class KnowledgeAutoIdentificationService:
    """知识贡献自动识别服务"""

    def __init__(self, db: Session):
        self.db = db

    def identify_from_service_ticket(
        self,
        ticket_id: int,
        auto_publish: bool = True
    ) -> Optional[KnowledgeContribution]:
        """
        从服务工单自动识别知识贡献

        Args:
            ticket_id: 服务工单ID
            auto_publish: 是否自动发布

        Returns:
            创建的知识贡献记录
        """
        # 获取工单
        ticket = self.db.query(ServiceTicket).filter(
            ServiceTicket.id == ticket_id
        ).first()

        if not ticket:
            return None

        # 只处理已关闭且有解决方案的工单
        if ticket.status != 'CLOSED' or not ticket.solution:
            return None

        # 检查是否已创建知识贡献
        existing = None
        if ticket.ticket_no:
            existing_query = self.db.query(KnowledgeContribution)
            existing_query = apply_keyword_filter(
                existing_query,
                KnowledgeContribution,
                ticket.ticket_no,
                "title",
                use_ilike=False,
            )
            existing = existing_query.first()

        if existing:
            return existing

        # 使用现有的知识提取服务创建知识库文章
        knowledge_article = auto_extract_knowledge_from_ticket(
            db=self.db,
            ticket=ticket,
            auto_publish=auto_publish
        )

        if not knowledge_article:
            return None

        # 确定贡献类型
        contribution_type = 'troubleshooting'  # 故障排查案例

        # 确定岗位类型（从工单问题类型推断）
        job_type = None
        if ticket.problem_type == 'MECHANICAL':
            job_type = 'MECHANICAL'
        elif ticket.problem_type == 'ELECTRICAL':
            job_type = 'ELECTRICAL'
        elif ticket.problem_type == 'SOFTWARE':
            job_type = 'TEST'

        # 创建知识贡献记录
        contribution = KnowledgeContribution(
            contributor_id=ticket.resolver_id or ticket.assignee_id,
            contribution_type=contribution_type,
            job_type=job_type,
            title=f"故障排查：{ticket.problem_type} - {ticket.ticket_no}",
            description=f"从服务工单 {ticket.ticket_no} 提取的故障排查案例",
            file_path=None,  # 可以关联到知识库文章
            tags=[ticket.problem_type, ticket.urgency, 'auto_extracted'],
            status='approved' if auto_publish else 'draft',
            approved_by=ticket.resolver_id if auto_publish else None,
            approved_at=datetime.now() if auto_publish else None
        )

        save_obj(self.db, contribution)

        return contribution

    def identify_from_knowledge_base(
        self,
        article_id: int,
        contributor_id: Optional[int] = None
    ) -> Optional[KnowledgeContribution]:
        """
        从知识库文章识别知识贡献

        Args:
            article_id: 知识库文章ID
            contributor_id: 贡献者ID（如果未提供，使用文章创建人）

        Returns:
            创建的知识贡献记录
        """
        # 获取知识库文章
        article = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id == article_id
        ).first()

        if not article:
            return None

        # 检查是否已创建知识贡献
        existing = self.db.query(KnowledgeContribution).filter(
            KnowledgeContribution.title == article.title
        ).first()

        if existing:
            return existing

        # 确定贡献者
        if not contributor_id:
            contributor_id = article.created_by

        if not contributor_id:
            return None

        # 确定贡献类型（从分类推断）
        contribution_type_map = {
            '软件问题': 'technical_solution',
            '机械问题': 'technical_solution',
            '电气问题': 'technical_solution',
            '操作问题': 'process_standard',
            '其他问题': 'other'
        }
        contribution_type = contribution_type_map.get(article.category, 'other')

        # 创建知识贡献记录
        contribution = KnowledgeContribution(
            contributor_id=contributor_id,
            contribution_type=contribution_type,
            job_type=None,  # 可以从文章内容推断
            title=article.title,
            description=article.content[:200] if article.content else None,  # 截取前200字
            file_path=None,
            tags=['knowledge_base', 'auto_identified'],
            status='approved',  # 知识库文章已审核通过
            approved_by=article.approved_by,
            approved_at=article.approved_at
        )

        save_obj(self.db, contribution)

        return contribution

    def identify_code_module(
        self,
        module_name: str,
        author_id: int,
        file_path: str,
        description: str,
        project_id: Optional[int] = None
    ) -> Optional[CodeModule]:
        """
        识别代码模块（从Git提交记录）

        Args:
            module_name: 模块名称
            author_id: 作者ID
            file_path: 文件路径
            description: 描述
            project_id: 关联项目ID

        Returns:
            创建的代码模块记录
        """
        # 检查是否已存在
        existing = self.db.query(CodeModule).filter(
            CodeModule.module_name == module_name,
            CodeModule.author_id == author_id
        ).first()

        if existing:
            return existing

        # 创建代码模块记录
        code_module = CodeModule(
            module_name=module_name,
            author_id=author_id,
            file_path=file_path,
            description=description,
            project_id=project_id,
            language='python',  # 默认Python，可以从文件路径推断
            version='1.0.0',
            status='active'
        )

        save_obj(self.db, code_module)

        return code_module

    def batch_identify_from_service_tickets(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        批量从服务工单识别知识贡献

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            识别统计信息
        """
        stats = {
            'total_tickets': 0,
            'identified_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'errors': []
        }

        # 查询已关闭且有解决方案的工单
        query = self.db.query(ServiceTicket).filter(
            ServiceTicket.status == 'CLOSED',
            ServiceTicket.solution.isnot(None)
        )

        if start_date:
            query = query.filter(ServiceTicket.resolved_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(ServiceTicket.resolved_time <= datetime.combine(end_date, datetime.max.time()))

        tickets = query.all()
        stats['total_tickets'] = len(tickets)

        for ticket in tickets:
            try:
                contribution = self.identify_from_service_ticket(ticket.id)
                if contribution:
                    stats['identified_count'] += 1
                else:
                    stats['skipped_count'] += 1
            except Exception as e:
                stats['error_count'] += 1
                stats['errors'].append({
                    'ticket_id': ticket.id,
                    'ticket_no': ticket.ticket_no,
                    'error': str(e)
                })

        return stats

    def batch_identify_from_knowledge_base(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        批量从知识库识别知识贡献

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            识别统计信息
        """
        stats = {
            'total_articles': 0,
            'identified_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'errors': []
        }

        # 查询知识库文章
        query = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.status == 'PUBLISHED'
        )

        if start_date:
            query = query.filter(KnowledgeBase.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(KnowledgeBase.created_at <= datetime.combine(end_date, datetime.max.time()))

        articles = query.all()
        stats['total_articles'] = len(articles)

        for article in articles:
            try:
                contribution = self.identify_from_knowledge_base(article.id)
                if contribution:
                    stats['identified_count'] += 1
                else:
                    stats['skipped_count'] += 1
            except Exception as e:
                stats['error_count'] += 1
                stats['errors'].append({
                    'article_id': article.id,
                    'article_no': article.article_no,
                    'error': str(e)
                })

        return stats
