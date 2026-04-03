# -*- coding: utf-8 -*-
"""
知识检索服务
支持按项目类型/产品/客户、风险类型、问题类型等多维检索
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.knowledge_base import (
    KnowledgeEntry,
    KnowledgeStatusEnum,
)


class KnowledgeSearchService:
    """知识检索服务"""

    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        *,
        keyword: Optional[str] = None,
        knowledge_type: Optional[str] = None,
        source_type: Optional[str] = None,
        project_type: Optional[str] = None,
        product_category: Optional[str] = None,
        industry: Optional[str] = None,
        customer_id: Optional[int] = None,
        risk_type: Optional[str] = None,
        issue_category: Optional[str] = None,
        change_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        多维度知识检索

        支持：
        - 关键词搜索（标题、摘要、问题描述、解决方案）
        - 按项目类型/产品/客户检索经验
        - 按风险类型检索应对措施
        - 按问题类型检索解决方案
        - 按变更类型检索变更经验
        - 标签筛选

        Returns:
            {"total": N, "items": [...], "page": N, "page_size": N}
        """
        q = self.db.query(KnowledgeEntry)

        # 默认只看已发布
        if status:
            q = q.filter(KnowledgeEntry.status == status)
        else:
            q = q.filter(KnowledgeEntry.status == KnowledgeStatusEnum.PUBLISHED)

        # 关键词：搜标题、摘要、问题描述、解决方案
        if keyword:
            like_pattern = f"%{keyword}%"
            q = q.filter(
                or_(
                    KnowledgeEntry.title.ilike(like_pattern),
                    KnowledgeEntry.summary.ilike(like_pattern),
                    KnowledgeEntry.problem_description.ilike(like_pattern),
                    KnowledgeEntry.solution.ilike(like_pattern),
                    KnowledgeEntry.root_cause.ilike(like_pattern),
                )
            )

        # 精确筛选
        if knowledge_type:
            q = q.filter(KnowledgeEntry.knowledge_type == knowledge_type)
        if source_type:
            q = q.filter(KnowledgeEntry.source_type == source_type)
        if project_type:
            q = q.filter(KnowledgeEntry.project_type == project_type)
        if product_category:
            q = q.filter(KnowledgeEntry.product_category == product_category)
        if industry:
            q = q.filter(KnowledgeEntry.industry == industry)
        if customer_id:
            q = q.filter(KnowledgeEntry.customer_id == customer_id)
        if risk_type:
            q = q.filter(KnowledgeEntry.risk_type == risk_type)
        if issue_category:
            q = q.filter(KnowledgeEntry.issue_category == issue_category)
        if change_type:
            q = q.filter(KnowledgeEntry.change_type == change_type)

        # 标签筛选（JSON 数组包含任一标签即匹配）
        if tags:
            tag_conditions = []
            for tag in tags:
                # SQLite JSON 兼容写法；MySQL/PG 可用 JSON_CONTAINS
                tag_conditions.append(KnowledgeEntry.tags.ilike(f"%{tag}%"))
            q = q.filter(or_(*tag_conditions))

        # 排序：引用次数 + 有用性 + 创建时间
        q = q.order_by(
            KnowledgeEntry.cite_count.desc(),
            KnowledgeEntry.usefulness_score.desc(),
            KnowledgeEntry.created_at.desc(),
        )

        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "items": items,
            "page": page,
            "page_size": page_size,
        }

    def get_by_id(self, entry_id: int, *, increment_view: bool = True) -> Optional[KnowledgeEntry]:
        """获取单条知识详情，自动增加查看次数"""
        entry = self.db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
        if entry and increment_view:
            entry.view_count = (entry.view_count or 0) + 1
            self.db.flush()
        return entry

    def vote(self, entry_id: int, score: float) -> KnowledgeEntry:
        """
        投票/评分

        score: 0-5 的评分
        usefulness_score 使用增量平均算法
        """
        entry = self.db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
        if not entry:
            raise ValueError(f"知识条目 {entry_id} 不存在")

        old_count = entry.vote_count or 0
        old_score = entry.usefulness_score or 0.0

        new_count = old_count + 1
        new_score = (old_score * old_count + score) / new_count

        entry.vote_count = new_count
        entry.usefulness_score = round(new_score, 2)
        self.db.flush()
        return entry

    def get_statistics(self) -> Dict[str, Any]:
        """知识库统计概览"""
        from sqlalchemy import func

        total = self.db.query(func.count(KnowledgeEntry.id)).scalar() or 0
        published = (
            self.db.query(func.count(KnowledgeEntry.id))
            .filter(KnowledgeEntry.status == KnowledgeStatusEnum.PUBLISHED)
            .scalar()
            or 0
        )

        # 按类型统计
        type_stats = (
            self.db.query(
                KnowledgeEntry.knowledge_type,
                func.count(KnowledgeEntry.id),
            )
            .filter(KnowledgeEntry.status == KnowledgeStatusEnum.PUBLISHED)
            .group_by(KnowledgeEntry.knowledge_type)
            .all()
        )

        # 按来源统计
        source_stats = (
            self.db.query(
                KnowledgeEntry.source_type,
                func.count(KnowledgeEntry.id),
            )
            .filter(KnowledgeEntry.status == KnowledgeStatusEnum.PUBLISHED)
            .group_by(KnowledgeEntry.source_type)
            .all()
        )

        # 热门标签 top 10
        # 简化实现：直接从最近 100 条记录中提取标签频率
        recent = (
            self.db.query(KnowledgeEntry.tags)
            .filter(
                KnowledgeEntry.status == KnowledgeStatusEnum.PUBLISHED,
                KnowledgeEntry.tags.isnot(None),
            )
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(100)
            .all()
        )
        tag_freq: Dict[str, int] = {}
        for (tags_json,) in recent:
            if isinstance(tags_json, list):
                for t in tags_json:
                    tag_freq[t] = tag_freq.get(t, 0) + 1
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total": total,
            "published": published,
            "by_type": {str(k): v for k, v in type_stats},
            "by_source": {str(k): v for k, v in source_stats},
            "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
        }
