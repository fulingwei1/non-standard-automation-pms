# -*- coding: utf-8 -*-
"""
踩坑服务
提供踩坑记录的CRUD和搜索功能
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter, apply_pagination, apply_like_filter
from app.models.pitfall import Pitfall


class PitfallService:
    """踩坑服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_pitfall_no(self) -> str:
        """
        生成踩坑编号
        格式: PFyymmdd001
        """
        today = datetime.now()
        prefix = f"PF{today.strftime('%y%m%d')}"

        # 查询今天最后一条记录
        last_pitfall_query = self.db.query(Pitfall)
        last_pitfall_query = apply_like_filter(
            last_pitfall_query,
            Pitfall,
            f"{prefix}%",
            "pitfall_no",
            use_ilike=False,
        )
        last_pitfall = last_pitfall_query.order_by(desc(Pitfall.pitfall_no)).first()

        if last_pitfall:
            # 提取序号并+1
            last_no = int(last_pitfall.pitfall_no[-3:])
            new_no = last_no + 1
        else:
            new_no = 1

        return f"{prefix}{new_no:03d}"

    def create_pitfall(
        self,
        title: str,
        description: str,
        created_by: int,
        solution: Optional[str] = None,
        stage: Optional[str] = None,
        equipment_type: Optional[str] = None,
        problem_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        root_cause: Optional[str] = None,
        impact: Optional[str] = None,
        prevention: Optional[str] = None,
        cost_impact: Optional[float] = None,
        schedule_impact: Optional[int] = None,
        source_type: Optional[str] = None,
        source_project_id: Optional[int] = None,
        source_ecn_id: Optional[int] = None,
        source_issue_id: Optional[int] = None,
        is_sensitive: bool = False,
        sensitive_reason: Optional[str] = None,
        visible_to: Optional[List[int]] = None,
    ) -> Pitfall:
        """创建踩坑记录"""
        pitfall = Pitfall(
            pitfall_no=self.generate_pitfall_no(),
            title=title,
            description=description,
            solution=solution,
            stage=stage,
            equipment_type=equipment_type,
            problem_type=problem_type,
            tags=tags,
            root_cause=root_cause,
            impact=impact,
            prevention=prevention,
            cost_impact=cost_impact,
            schedule_impact=schedule_impact,
            source_type=source_type or "REALTIME",
            source_project_id=source_project_id,
            source_ecn_id=source_ecn_id,
            source_issue_id=source_issue_id,
            is_sensitive=is_sensitive,
            sensitive_reason=sensitive_reason,
            visible_to=visible_to,
            created_by=created_by,
            status="DRAFT",
        )

        self.db.add(pitfall)
        self.db.commit()
        self.db.refresh(pitfall)

        return pitfall

    def get_pitfall(
        self, pitfall_id: int, user_id: int, is_admin: bool = False
    ) -> Optional[Pitfall]:
        """
        获取踩坑记录
        敏感记录需要权限检查
        """
        pitfall = self.db.query(Pitfall).filter(Pitfall.id == pitfall_id).first()

        if not pitfall:
            return None

        # 敏感记录权限检查
        if pitfall.is_sensitive and not is_admin:
            if pitfall.created_by != user_id:
                if pitfall.visible_to and user_id not in pitfall.visible_to:
                    return None

        return pitfall

    def list_pitfalls(
        self,
        user_id: int,
        keyword: Optional[str] = None,
        stage: Optional[str] = None,
        equipment_type: Optional[str] = None,
        problem_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        verified_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Pitfall], int]:
        """
        获取踩坑列表
        支持多维度筛选
        """
        query = self.db.query(Pitfall)

        # 状态筛选（默认只显示已发布）
        if status:
            query = query.filter(Pitfall.status == status)
        else:
            query = query.filter(Pitfall.status == "PUBLISHED")

        # 关键词搜索
        query = apply_keyword_filter(query, Pitfall, keyword, ["title", "description", "solution"])

        # 多维度筛选
        if stage:
            query = query.filter(Pitfall.stage == stage)
        if equipment_type:
            query = query.filter(Pitfall.equipment_type == equipment_type)
        if problem_type:
            query = query.filter(Pitfall.problem_type == problem_type)
        if verified_only:
            query = query.filter(Pitfall.verified == True)

        # 排除无权限的敏感记录
        query = query.filter(
            or_(
                Pitfall.is_sensitive == False,
                Pitfall.created_by == user_id,
            )
        )

        total = query.count()
        pitfalls = (
            apply_pagination(query.order_by(desc(Pitfall.created_at)), skip, limit).all()
        )

        return pitfalls, total

    def publish_pitfall(self, pitfall_id: int, user_id: int) -> Optional[Pitfall]:
        """发布踩坑记录"""
        pitfall = self.get_pitfall(pitfall_id, user_id)
        if not pitfall:
            return None

        if pitfall.created_by != user_id:
            return None

        pitfall.status = "PUBLISHED"
        self.db.commit()
        self.db.refresh(pitfall)

        return pitfall

    def verify_pitfall(self, pitfall_id: int) -> Optional[Pitfall]:
        """验证踩坑记录（增加验证次数）"""
        pitfall = self.db.query(Pitfall).filter(Pitfall.id == pitfall_id).first()
        if pitfall:
            pitfall.verified = True
            pitfall.verify_count = (pitfall.verify_count or 0) + 1
            self.db.commit()
            self.db.refresh(pitfall)
        return pitfall
