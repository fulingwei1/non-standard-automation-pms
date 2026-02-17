# -*- coding: utf-8 -*-
"""
知识贡献服务
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.engineer_performance import (
    CodeModule,
    KnowledgeContribution,
    KnowledgeReuseLog,
    PlcModuleLibrary,
)
from app.models.user import User
from app.schemas.engineer_performance import (
    KnowledgeContributionCreate,
    KnowledgeContributionUpdate,
    KnowledgeReuseCreate,
)
from app.utils.db_helpers import save_obj, delete_obj


class KnowledgeContributionService:
    """知识贡献服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 知识贡献管理 ====================

    def create_contribution(
        self,
        data: KnowledgeContributionCreate,
        contributor_id: int
    ) -> KnowledgeContribution:
        """创建知识贡献"""
        contribution = KnowledgeContribution(
            contributor_id=contributor_id,
            contribution_type=data.contribution_type,
            job_type=data.job_type,
            title=data.title,
            description=data.description,
            file_path=data.file_path,
            tags=data.tags,
            status='draft'
        )
        save_obj(self.db, contribution)
        return contribution

    def get_contribution(self, contribution_id: int) -> Optional[KnowledgeContribution]:
        """获取知识贡献详情"""
        return self.db.query(KnowledgeContribution).filter(
            KnowledgeContribution.id == contribution_id
        ).first()

    def update_contribution(
        self,
        contribution_id: int,
        data: KnowledgeContributionUpdate,
        user_id: int
    ) -> Optional[KnowledgeContribution]:
        """更新知识贡献"""
        contribution = self.get_contribution(contribution_id)
        if not contribution:
            return None

        # 检查权限（只有贡献者本人或审核状态时管理员可修改）
        if contribution.contributor_id != user_id and data.status is None:
            raise PermissionError("无权修改他人的贡献")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contribution, key, value)

        contribution.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(contribution)
        return contribution

    def submit_for_review(self, contribution_id: int, user_id: int) -> KnowledgeContribution:
        """提交审核"""
        contribution = self.get_contribution(contribution_id)
        if not contribution:
            raise ValueError("贡献不存在")

        if contribution.contributor_id != user_id:
            raise PermissionError("无权提交他人的贡献")

        if contribution.status != 'draft':
            raise ValueError("只有草稿状态可以提交审核")

        contribution.status = 'pending'
        contribution.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(contribution)
        return contribution

    def approve_contribution(
        self,
        contribution_id: int,
        approver_id: int,
        approved: bool = True
    ) -> KnowledgeContribution:
        """审核知识贡献"""
        contribution = self.get_contribution(contribution_id)
        if not contribution:
            raise ValueError("贡献不存在")

        if contribution.status != 'pending':
            raise ValueError("只有待审核状态可以审核")

        contribution.status = 'approved' if approved else 'rejected'
        contribution.approved_by = approver_id
        contribution.approved_at = datetime.now()
        contribution.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(contribution)
        return contribution

    def list_contributions(
        self,
        contributor_id: Optional[int] = None,
        job_type: Optional[str] = None,
        contribution_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[KnowledgeContribution], int]:
        """获取知识贡献列表"""
        query = self.db.query(KnowledgeContribution)

        if contributor_id:
            query = query.filter(KnowledgeContribution.contributor_id == contributor_id)
        if job_type:
            query = query.filter(KnowledgeContribution.job_type == job_type)
        if contribution_type:
            query = query.filter(KnowledgeContribution.contribution_type == contribution_type)
        if status:
            query = query.filter(KnowledgeContribution.status == status)

        total = query.count()
        items = query.order_by(
            desc(KnowledgeContribution.created_at)
        ).offset(offset).limit(limit).all()

        return items, total

    def delete_contribution(self, contribution_id: int, user_id: int) -> bool:
        """删除知识贡献"""
        contribution = self.get_contribution(contribution_id)
        if not contribution:
            return False

        if contribution.contributor_id != user_id:
            raise PermissionError("无权删除他人的贡献")

        if contribution.status == 'approved':
            raise ValueError("已审核通过的贡献不能删除")

        delete_obj(self.db, contribution)
        return True

    # ==================== 复用记录 ====================

    def record_reuse(
        self,
        data: KnowledgeReuseCreate,
        user_id: int
    ) -> KnowledgeReuseLog:
        """记录知识复用"""
        contribution = self.get_contribution(data.contribution_id)
        if not contribution:
            raise ValueError("贡献不存在")

        if contribution.status != 'approved':
            raise ValueError("只有已审核通过的贡献可以被复用")

        reuse_log = KnowledgeReuseLog(
            contribution_id=data.contribution_id,
            user_id=user_id,
            project_id=data.project_id,
            reuse_type=data.reuse_type,
            rating=data.rating,
            feedback=data.feedback
        )
        self.db.add(reuse_log)

        # 更新复用统计
        contribution.reuse_count = (contribution.reuse_count or 0) + 1
        if data.rating:
            total_rating = (contribution.rating_score or 0) * (contribution.rating_count or 0)
            contribution.rating_count = (contribution.rating_count or 0) + 1
            contribution.rating_score = Decimal(str(
                round((float(total_rating) + data.rating) / contribution.rating_count, 2)
            ))

        self.db.commit()
        self.db.refresh(reuse_log)
        return reuse_log

    def get_reuse_logs(
        self,
        contribution_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[KnowledgeReuseLog], int]:
        """获取复用记录"""
        query = self.db.query(KnowledgeReuseLog).filter(
            KnowledgeReuseLog.contribution_id == contribution_id
        )

        total = query.count()
        items = query.order_by(
            desc(KnowledgeReuseLog.created_at)
        ).offset(offset).limit(limit).all()

        return items, total

    # ==================== 排行统计 ====================

    def get_contribution_ranking(
        self,
        job_type: Optional[str] = None,
        contribution_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取贡献排行"""
        query = self.db.query(
            KnowledgeContribution.contributor_id,
            func.count(KnowledgeContribution.id).label('count'),
            func.sum(KnowledgeContribution.reuse_count).label('total_reuse')
        ).filter(
            KnowledgeContribution.status == 'approved'
        )

        if job_type:
            query = query.filter(KnowledgeContribution.job_type == job_type)
        if contribution_type:
            query = query.filter(KnowledgeContribution.contribution_type == contribution_type)

        results = query.group_by(
            KnowledgeContribution.contributor_id
        ).order_by(
            desc('count'), desc('total_reuse')
        ).limit(limit).all()

        ranking = []
        for i, (contributor_id, count, total_reuse) in enumerate(results, 1):
            user = self.db.query(User).filter(User.id == contributor_id).first()
            ranking.append({
                'rank': i,
                'contributor_id': contributor_id,
                'contributor_name': user.name if user else 'Unknown',
                'contribution_count': count,
                'total_reuse': total_reuse or 0
            })

        return ranking

    def get_contributor_stats(self, user_id: int) -> Dict[str, Any]:
        """获取贡献者统计"""
        contributions = self.db.query(KnowledgeContribution).filter(
            KnowledgeContribution.contributor_id == user_id,
            KnowledgeContribution.status == 'approved'
        ).all()

        if not contributions:
            return {
                'total_contributions': 0,
                'total_reuse': 0,
                'avg_rating': 0,
                'by_type': {}
            }

        # 按类型统计
        by_type = {}
        total_reuse = 0
        total_rating = 0
        rating_count = 0

        for c in contributions:
            ctype = c.contribution_type
            if ctype not in by_type:
                by_type[ctype] = {'count': 0, 'reuse': 0}
            by_type[ctype]['count'] += 1
            by_type[ctype]['reuse'] += c.reuse_count or 0
            total_reuse += c.reuse_count or 0

            if c.rating_score and c.rating_count:
                total_rating += float(c.rating_score) * c.rating_count
                rating_count += c.rating_count

        return {
            'total_contributions': len(contributions),
            'total_reuse': total_reuse,
            'avg_rating': round(total_rating / rating_count, 2) if rating_count > 0 else 0,
            'by_type': by_type
        }

    # ==================== 代码模块库 ====================

    def list_code_modules(
        self,
        category: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[CodeModule], int]:
        """获取代码模块列表"""
        query = self.db.query(CodeModule).filter(
            CodeModule.status == 'active'
        )

        if category:
            query = query.filter(CodeModule.category == category)
        if language:
            query = query.filter(CodeModule.language == language)

        total = query.count()
        items = query.order_by(
            desc(CodeModule.reuse_count), desc(CodeModule.created_at)
        ).offset(offset).limit(limit).all()

        return items, total

    def list_plc_modules(
        self,
        category: Optional[str] = None,
        plc_brand: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[PlcModuleLibrary], int]:
        """获取PLC模块列表"""
        query = self.db.query(PlcModuleLibrary).filter(
            PlcModuleLibrary.status == 'active'
        )

        if category:
            query = query.filter(PlcModuleLibrary.category == category)
        if plc_brand:
            query = query.filter(PlcModuleLibrary.plc_brand == plc_brand)

        total = query.count()
        items = query.order_by(
            desc(PlcModuleLibrary.reuse_count), desc(PlcModuleLibrary.created_at)
        ).offset(offset).limit(limit).all()

        return items, total
