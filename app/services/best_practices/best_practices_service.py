# -*- coding: utf-8 -*-
"""
最佳实践业务逻辑服务
"""

from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.pagination import PaginationParams


class BestPracticesService:
    """最佳实践服务类"""

    def __init__(self, db: Session):
        """初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db

    def get_popular_practices(
        self,
        pagination: PaginationParams,
        category: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取热门最佳实践（按复用次数排序）
        
        Args:
            pagination: 分页参数
            category: 分类筛选
            
        Returns:
            (实践列表, 总数)
        """
        # 构建查询
        query = """
            SELECT
                bp.*,
                p.project_code,
                p.project_name as project_name
            FROM project_best_practices bp
            LEFT JOIN projects p ON bp.project_id = p.id
            WHERE bp.status = 'ACTIVE' AND bp.is_reusable = 1
        """
        params = {}

        if category:
            query += " AND bp.category = :category"
            params["category"] = category

        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) as subq"
        total = self.db.execute(text(count_query), params).scalar() or 0

        # 分页查询（按复用次数降序）
        query += " ORDER BY bp.reuse_count DESC, bp.created_at DESC"
        query += " LIMIT :page_size OFFSET :offset"
        params["page_size"] = pagination.limit
        params["offset"] = pagination.offset

        result = self.db.execute(text(query), params)
        rows = result.fetchall()

        # 转换为字典列表
        items = [self._row_to_dict(row) for row in rows]

        return items, total

    def get_practices(
        self,
        pagination: PaginationParams,
        project_id: Optional[int] = None,
        category: Optional[str] = None,
        validation_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取最佳实践列表
        
        Args:
            pagination: 分页参数
            project_id: 项目ID筛选
            category: 分类筛选
            validation_status: 验证状态筛选
            search: 搜索关键词
            
        Returns:
            (实践列表, 总数)
        """
        query = """
            SELECT
                bp.*,
                p.project_code,
                p.project_name as project_name
            FROM project_best_practices bp
            LEFT JOIN projects p ON bp.project_id = p.id
            WHERE bp.status = 'ACTIVE'
        """
        params = {}

        if project_id:
            query += " AND bp.project_id = :project_id"
            params["project_id"] = project_id

        if category:
            query += " AND bp.category = :category"
            params["category"] = category

        if validation_status:
            query += " AND bp.validation_status = :validation_status"
            params["validation_status"] = validation_status

        if search:
            query += " AND (bp.title LIKE :search OR bp.description LIKE :search)"
            params["search"] = f"%{search}%"

        # 获取总数
        count_query = f"SELECT COUNT(*) FROM ({query}) as subq"
        total = self.db.execute(text(count_query), params).scalar() or 0

        # 分页查询
        query += " ORDER BY bp.created_at DESC"
        query += " LIMIT :page_size OFFSET :offset"
        params["page_size"] = pagination.limit
        params["offset"] = pagination.offset

        result = self.db.execute(text(query), params)
        rows = result.fetchall()

        items = [self._row_to_dict(row) for row in rows]

        return items, total

    def get_practice_by_id(self, practice_id: int) -> Optional[Dict[str, Any]]:
        """获取最佳实践详情
        
        Args:
            practice_id: 实践ID
            
        Returns:
            实践信息字典，不存在时返回 None
        """
        query = """
            SELECT
                bp.*,
                p.project_code,
                p.project_name as project_name
            FROM project_best_practices bp
            LEFT JOIN projects p ON bp.project_id = p.id
            WHERE bp.id = :practice_id
        """

        result = self.db.execute(text(query), {"practice_id": practice_id})
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def apply_practice(
        self, practice_id: int, target_project_id: int, notes: Optional[str] = None
    ) -> bool:
        """应用最佳实践到目标项目
        
        Args:
            practice_id: 实践ID
            target_project_id: 目标项目ID
            notes: 应用备注
            
        Returns:
            成功返回 True，失败抛出异常
            
        Raises:
            ValueError: 实践或项目不存在
        """
        # 检查最佳实践是否存在
        check_query = (
            "SELECT id, reuse_count FROM project_best_practices WHERE id = :practice_id"
        )
        result = self.db.execute(text(check_query), {"practice_id": practice_id})
        practice = result.fetchone()

        if not practice:
            raise ValueError("最佳实践不存在")

        # 检查目标项目是否存在
        project_check = "SELECT id FROM projects WHERE id = :project_id"
        project_result = self.db.execute(
            text(project_check), {"project_id": target_project_id}
        )
        if not project_result.fetchone():
            raise ValueError("目标项目不存在")

        # 更新复用次数
        update_query = """
            UPDATE project_best_practices
            SET reuse_count = reuse_count + 1,
                last_reused_at = :now,
                updated_at = :now
            WHERE id = :practice_id
        """
        self.db.execute(
            text(update_query), {"practice_id": practice_id, "now": datetime.now()}
        )
        self.db.commit()

        return True

    def create_practice(
        self,
        review_id: int,
        project_id: int,
        title: str,
        description: str,
        context: Optional[str] = None,
        implementation: Optional[str] = None,
        benefits: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        is_reusable: bool = True,
        applicable_project_types: Optional[str] = None,
        applicable_stages: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建最佳实践
        
        Args:
            review_id: 评审ID
            project_id: 项目ID
            title: 标题
            description: 描述
            context: 上下文
            implementation: 实施方法
            benefits: 收益
            category: 分类
            tags: 标签
            is_reusable: 是否可复用
            applicable_project_types: 适用项目类型
            applicable_stages: 适用阶段
            
        Returns:
            创建的实践信息字典
        """
        insert_query = """
            INSERT INTO project_best_practices (
                review_id, project_id, title, description, context,
                implementation, benefits, category, tags, is_reusable,
                applicable_project_types, applicable_stages, created_at, updated_at
            ) VALUES (
                :review_id, :project_id, :title, :description, :context,
                :implementation, :benefits, :category, :tags, :is_reusable,
                :applicable_project_types, :applicable_stages, :now, :now
            )
        """

        now = datetime.now()
        result = self.db.execute(
            text(insert_query),
            {
                "review_id": review_id,
                "project_id": project_id,
                "title": title,
                "description": description,
                "context": context,
                "implementation": implementation,
                "benefits": benefits,
                "category": category,
                "tags": tags,
                "is_reusable": is_reusable,
                "applicable_project_types": applicable_project_types,
                "applicable_stages": applicable_stages,
                "now": now,
            },
        )
        self.db.commit()

        # 返回新创建的记录
        new_id = result.lastrowid
        return {
            "id": new_id,
            "review_id": review_id,
            "project_id": project_id,
            "title": title,
            "description": description,
            "context": context,
            "implementation": implementation,
            "benefits": benefits,
            "category": category,
            "tags": tags,
            "is_reusable": is_reusable,
            "applicable_project_types": applicable_project_types,
            "applicable_stages": applicable_stages,
            "validation_status": "PENDING",
            "reuse_count": 0,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        }

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典
        
        Args:
            row: 数据库行对象
            
        Returns:
            字典格式的数据
        """
        return {
            "id": row.id,
            "review_id": row.review_id,
            "project_id": row.project_id,
            "title": row.title,
            "description": row.description,
            "context": row.context,
            "implementation": row.implementation,
            "benefits": row.benefits,
            "category": row.category,
            "tags": row.tags,
            "is_reusable": bool(row.is_reusable),
            "applicable_project_types": row.applicable_project_types,
            "applicable_stages": row.applicable_stages,
            "validation_status": row.validation_status or "PENDING",
            "reuse_count": row.reuse_count or 0,
            "status": row.status or "ACTIVE",
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "project_code": row.project_code,
            "project_name": row.project_name,
        }
