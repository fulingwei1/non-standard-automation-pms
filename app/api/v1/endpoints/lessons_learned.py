# -*- coding: utf-8 -*-
"""
经验教训库 API
- 项目复盘经验教训管理
- 支持分类、标签、影响程度筛选
- 统计分析
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()

# 创建经验教训表的 SQL（在模块级别定义）
CREATE_TABLE_SQL = text("""
CREATE TABLE IF NOT EXISTS lessons_learned (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50), -- technical/management/quality/cost/schedule/customer
    lesson_type VARCHAR(20), -- success/failure/improvement
    description TEXT NOT NULL,
    root_cause TEXT,
    action_taken TEXT,
    recommendation TEXT,
    impact_level VARCHAR(20), -- high/medium/low
    applicable_to VARCHAR(200),
    tags VARCHAR(500),
    submitted_by INTEGER,
    reviewed BOOLEAN DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
""")


_table_created = False

def _ensure_table(db: Session):
    global _table_created
    if not _table_created:
        try:
            db.execute(CREATE_TABLE_SQL)
            db.commit()
        except Exception:
            db.rollback()
        _table_created = True


@router.get("/list", summary="经验教训列表")
def list_lessons(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    category: Optional[str] = Query(None, description="分类：technical/management/quality/cost/schedule/customer"),
    lesson_type: Optional[str] = Query(None, description="类型：success/failure/improvement"),
    project_id: Optional[int] = Query(None, description="项目 ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """
    获取经验教训列表，支持筛选和分页
    """
    _ensure_table(db)
    # 构建 WHERE 条件
    where_clauses = ["1=1"]
    params = {"offset": (page - 1) * page_size, "limit": page_size}
    
    if category:
        where_clauses.append("ll.category = :category")
        params["category"] = category
    
    if lesson_type:
        where_clauses.append("ll.lesson_type = :lesson_type")
        params["lesson_type"] = lesson_type
    
    if project_id:
        where_clauses.append("ll.project_id = :project_id")
        params["project_id"] = project_id
    
    if keyword:
        where_clauses.append("(ll.title LIKE :keyword OR ll.description LIKE :keyword)")
        params["keyword"] = f"%{keyword}%"
    
    where_clause = " AND ".join(where_clauses)
    
    # 查询列表
    list_sql = text(f"""
        SELECT 
            ll.id,
            ll.project_id,
            ll.title,
            ll.category,
            ll.lesson_type,
            ll.description,
            ll.root_cause,
            ll.action_taken,
            ll.recommendation,
            ll.impact_level,
            ll.applicable_to,
            ll.tags,
            ll.submitted_by,
            ll.reviewed,
            ll.created_at,
            ll.updated_at,
            p.project_name
        FROM lessons_learned ll
        LEFT JOIN projects p ON ll.project_id = p.id
        WHERE {where_clause}
        ORDER BY ll.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    
    rows = db.execute(list_sql, params).fetchall()
    
    # 查询总数
    count_sql = text(f"""
        SELECT COUNT(*) as total
        FROM lessons_learned ll
        WHERE {where_clause}
    """)
    total = db.execute(count_sql, {k: v for k, v in params.items() if k not in ["offset", "limit"]}).fetchone().total
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "project_name": r.project_name,
                "title": r.title,
                "category": r.category,
                "lesson_type": r.lesson_type,
                "description": r.description,
                "root_cause": r.root_cause,
                "action_taken": r.action_taken,
                "recommendation": r.recommendation,
                "impact_level": r.impact_level,
                "applicable_to": r.applicable_to,
                "tags": r.tags,
                "submitted_by": r.submitted_by,
                "reviewed": bool(r.reviewed),
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in rows
        ],
    }


@router.get("/stats", summary="经验教训统计")
def get_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取经验教训统计数据
    - 按分类统计
    - 按类型统计
    - 按项目统计
    """
    _ensure_table(db)
    total_sql = text("SELECT COUNT(*) as total FROM lessons_learned")
    total = db.execute(total_sql).fetchone().total

    category_sql = text("""
        SELECT category, COUNT(*) as count
        FROM lessons_learned
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    """)
    by_category = [
        {"category": r.category, "count": r.count}
        for r in db.execute(category_sql).fetchall()
    ]

    type_sql = text("""
        SELECT lesson_type, COUNT(*) as count
        FROM lessons_learned
        WHERE lesson_type IS NOT NULL
        GROUP BY lesson_type
        ORDER BY count DESC
    """)
    by_type = [
        {"lesson_type": r.lesson_type, "count": r.count}
        for r in db.execute(type_sql).fetchall()
    ]

    project_sql = text("""
        SELECT p.id, p.project_name, COUNT(ll.id) as count
        FROM lessons_learned ll
        JOIN projects p ON ll.project_id = p.id
        GROUP BY p.id, p.project_name
        ORDER BY count DESC
        LIMIT 20
    """)
    by_project = [
        {"project_id": r.id, "project_name": r.project_name, "count": r.count}
        for r in db.execute(project_sql).fetchall()
    ]

    impact_sql = text("""
        SELECT impact_level, COUNT(*) as count
        FROM lessons_learned
        WHERE impact_level IS NOT NULL
        GROUP BY impact_level
        ORDER BY
            CASE impact_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END
    """)
    by_impact = [
        {"impact_level": r.impact_level, "count": r.count}
        for r in db.execute(impact_sql).fetchall()
    ]

    return {
        "total": total,
        "by_category": by_category,
        "by_type": by_type,
        "by_project": by_project,
        "by_impact": by_impact,
    }


@router.get("/search", summary="搜索经验教训")
def search_lessons(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    q: str = Query(..., description="搜索关键词"),
) -> Any:
    """
    搜索经验教训（标题、描述、建议）
    """
    _ensure_table(db)
    keyword = f"%{q}%"
    sql = text("""
        SELECT
            ll.id, ll.project_id, ll.title, ll.category, ll.lesson_type,
            ll.description, ll.root_cause, ll.action_taken, ll.recommendation,
            ll.impact_level, ll.applicable_to, ll.tags, ll.submitted_by,
            ll.reviewed, ll.created_at, ll.updated_at, p.project_name
        FROM lessons_learned ll
        LEFT JOIN projects p ON ll.project_id = p.id
        WHERE ll.title LIKE :keyword
           OR ll.description LIKE :keyword
           OR ll.recommendation LIKE :keyword
        ORDER BY ll.created_at DESC
        LIMIT 50
    """)
    rows = db.execute(sql, {"keyword": keyword}).fetchall()
    return {
        "total": len(rows),
        "keyword": q,
        "items": [
            {
                "id": r.id, "project_id": r.project_id, "project_name": r.project_name,
                "title": r.title, "category": r.category, "lesson_type": r.lesson_type,
                "description": r.description, "root_cause": r.root_cause,
                "action_taken": r.action_taken, "recommendation": r.recommendation,
                "impact_level": r.impact_level, "applicable_to": r.applicable_to,
                "tags": r.tags, "submitted_by": r.submitted_by, "reviewed": bool(r.reviewed),
                "created_at": r.created_at, "updated_at": r.updated_at,
            }
            for r in rows
        ],
    }


@router.get("/{id}", summary="经验教训详情")
def get_lesson(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    id: int,
) -> Any:
    """
    获取单个经验教训详情
    """
    _ensure_table(db)
    sql = text("""
        SELECT
            ll.id, ll.project_id, ll.title, ll.category, ll.lesson_type,
            ll.description, ll.root_cause, ll.action_taken, ll.recommendation,
            ll.impact_level, ll.applicable_to, ll.tags, ll.submitted_by,
            ll.reviewed, ll.created_at, ll.updated_at, p.project_name
        FROM lessons_learned ll
        LEFT JOIN projects p ON ll.project_id = p.id
        WHERE ll.id = :id
    """)
    row = db.execute(sql, {"id": id}).fetchone()
    if not row:
        return {"error": "经验教训不存在"}
    return {
        "id": row.id, "project_id": row.project_id, "project_name": row.project_name,
        "title": row.title, "category": row.category, "lesson_type": row.lesson_type,
        "description": row.description, "root_cause": row.root_cause,
        "action_taken": row.action_taken, "recommendation": row.recommendation,
        "impact_level": row.impact_level, "applicable_to": row.applicable_to,
        "tags": row.tags, "submitted_by": row.submitted_by, "reviewed": bool(row.reviewed),
        "created_at": row.created_at, "updated_at": row.updated_at,
    }


@router.post("/", summary="创建经验教训")
def create_lesson(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    lesson: dict,
) -> Any:
    """
    创建新的经验教训
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sql = text("""
        INSERT INTO lessons_learned (
            project_id, title, category, lesson_type, description,
            root_cause, action_taken, recommendation, impact_level,
            applicable_to, tags, submitted_by, reviewed, created_at, updated_at
        ) VALUES (
            :project_id, :title, :category, :lesson_type, :description,
            :root_cause, :action_taken, :recommendation, :impact_level,
            :applicable_to, :tags, :submitted_by, :reviewed, :now, :now
        )
    """)
    
    params = {
        "project_id": lesson.get("project_id"),
        "title": lesson.get("title"),
        "category": lesson.get("category"),
        "lesson_type": lesson.get("lesson_type"),
        "description": lesson.get("description"),
        "root_cause": lesson.get("root_cause"),
        "action_taken": lesson.get("action_taken"),
        "recommendation": lesson.get("recommendation"),
        "impact_level": lesson.get("impact_level"),
        "applicable_to": lesson.get("applicable_to"),
        "tags": lesson.get("tags"),
        "submitted_by": current_user.id,
        "reviewed": lesson.get("reviewed", False),
        "now": now,
    }
    
    db.execute(sql, params)
    db.commit()
    
    # 获取新插入的 ID
    result = db.execute(text("SELECT last_insert_rowid() as id")).fetchone()
    new_id = result.id
    
    return {
        "id": new_id,
        "message": "经验教训创建成功",
    }


@router.put("/{id}", summary="更新经验教训")
def update_lesson(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    id: int,
    lesson: dict,
) -> Any:
    """
    更新经验教训
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构建动态更新字段
    update_fields = []
    params = {"id": id, "now": now}
    
    field_mapping = {
        "project_id": "project_id",
        "title": "title",
        "category": "category",
        "lesson_type": "lesson_type",
        "description": "description",
        "root_cause": "root_cause",
        "action_taken": "action_taken",
        "recommendation": "recommendation",
        "impact_level": "impact_level",
        "applicable_to": "applicable_to",
        "tags": "tags",
        "reviewed": "reviewed",
    }
    
    for key, column in field_mapping.items():
        if key in lesson:
            update_fields.append(f"{column} = :{key}")
            params[key] = lesson[key]
    
    if not update_fields:
        return {"error": "没有要更新的字段"}
    
    update_fields.append("updated_at = :now")
    
    sql = text(f"""
        UPDATE lessons_learned
        SET {", ".join(update_fields)}
        WHERE id = :id
    """)
    
    db.execute(sql, params)
    db.commit()
    
    return {
        "id": id,
        "message": "经验教训更新成功",
    }
