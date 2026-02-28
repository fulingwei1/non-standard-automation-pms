# -*- coding: utf-8 -*-
"""
客户验收管理 (FAT/SAT) API
- FAT: Factory Acceptance Test (工厂验收测试)
- SAT: Site Acceptance Test (现场验收测试)
- 检查清单管理
- 问题追踪
- 签收管理
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()

# 表创建标志
_tables_created = False


def _ensure_tables(db: Session):
    """确保表存在（首次请求时创建）"""
    global _tables_created
    if _tables_created:
        return

    try:
        # 创建验收记录表
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS acceptance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL COMMENT '项目 ID',
                acceptance_type TEXT NOT NULL COMMENT '验收类型：FAT/SAT',
                acceptance_code TEXT UNIQUE COMMENT '验收编号',
                title TEXT NOT NULL COMMENT '验收标题',
                status TEXT DEFAULT 'draft' COMMENT '状态：draft/in_progress/passed/failed/signed',
                scheduled_date DATE COMMENT '计划日期',
                actual_date DATE COMMENT '实际日期',
                location TEXT COMMENT '验收地点',
                customer_representative TEXT COMMENT '客户代表',
                our_representative TEXT COMMENT '我方代表',
                overall_result TEXT COMMENT '总体结果：pass/fail/conditional',
                notes TEXT COMMENT '备注',
                sign_date DATE COMMENT '签收日期',
                sign_by TEXT COMMENT '签收人',
                created_by INTEGER COMMENT '创建人 ID',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 创建验收检查清单表
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS acceptance_checklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acceptance_id INTEGER NOT NULL COMMENT '验收 ID',
                item_no INTEGER NOT NULL COMMENT '项目编号',
                category TEXT NOT NULL COMMENT '类别：functional/performance/safety/documentation',
                check_item TEXT NOT NULL COMMENT '检查项',
                expected_result TEXT COMMENT '期望结果',
                actual_result TEXT COMMENT '实际结果',
                status TEXT DEFAULT 'pending' COMMENT '状态：pending/pass/fail/na',
                remarks TEXT COMMENT '备注',
                checked_by TEXT COMMENT '检查人',
                checked_at TIMESTAMP COMMENT '检查时间',
                FOREIGN KEY (acceptance_id) REFERENCES acceptance_records(id)
            )
        """))

        # 创建验收问题表
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS acceptance_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acceptance_id INTEGER NOT NULL COMMENT '验收 ID',
                issue_no INTEGER NOT NULL COMMENT '问题编号',
                severity TEXT NOT NULL COMMENT '严重程度：critical/major/minor',
                description TEXT NOT NULL COMMENT '问题描述',
                root_cause TEXT COMMENT '根本原因',
                solution TEXT COMMENT '解决方案',
                status TEXT DEFAULT 'open' COMMENT '状态：open/fixing/resolved/closed',
                responsible TEXT COMMENT '责任人',
                due_date DATE COMMENT '截止日期',
                resolved_date DATE COMMENT '解决日期',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (acceptance_id) REFERENCES acceptance_records(id)
            )
        """))

        # 创建索引
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_acceptance_project ON acceptance_records(project_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_acceptance_status ON acceptance_records(status)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_checklist_acceptance ON acceptance_checklist(acceptance_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_issues_acceptance ON acceptance_issues(acceptance_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_issues_status ON acceptance_issues(status)"))

        db.commit()
        _tables_created = True
    except Exception as e:
        db.rollback()
        raise e


@router.get("/list", summary="获取验收记录列表")
def list_acceptance_records(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: Optional[int] = Query(None, description="项目 ID"),
    acceptance_type: Optional[str] = Query(None, description="验收类型 FAT/SAT"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取验收记录列表，支持筛选和分页"""
    _ensure_tables(db)

    # 构建 WHERE 条件
    conditions = ["1=1"]
    params = {}

    if project_id:
        conditions.append("project_id = :project_id")
        params["project_id"] = project_id

    if acceptance_type:
        conditions.append("acceptance_type = :acceptance_type")
        params["acceptance_type"] = acceptance_type

    if status:
        conditions.append("status = :status")
        params["status"] = status

    where_clause = " AND ".join(conditions)

    # 获取总数
    count_sql = text(f"SELECT COUNT(*) as total FROM acceptance_records WHERE {where_clause}")
    total = db.execute(count_sql, params).fetchone().total

    # 获取数据
    offset = (page - 1) * page_size
    sql = text(f"""
        SELECT 
            ar.id, ar.project_id, ar.acceptance_type, ar.acceptance_code,
            ar.title, ar.status, ar.scheduled_date, ar.actual_date,
            ar.location, ar.customer_representative, ar.our_representative,
            ar.overall_result, ar.notes, ar.sign_date, ar.sign_by,
            ar.created_by, ar.created_at, ar.updated_at,
            p.project_name, p.project_code
        FROM acceptance_records ar
        LEFT JOIN projects p ON ar.project_id = p.id
        WHERE {where_clause}
        ORDER BY ar.created_at DESC
        LIMIT :limit OFFSET :offset
    """)

    params["limit"] = page_size
    params["offset"] = offset
    rows = db.execute(sql, params).fetchall()

    items = []
    for r in rows:
        items.append({
            "id": r.id,
            "project_id": r.project_id,
            "project_name": r.project_name,
            "project_code": r.project_code,
            "acceptance_type": r.acceptance_type,
            "acceptance_code": r.acceptance_code,
            "title": r.title,
            "status": r.status,
            "scheduled_date": str(r.scheduled_date) if r.scheduled_date else None,
            "actual_date": str(r.actual_date) if r.actual_date else None,
            "location": r.location,
            "customer_representative": r.customer_representative,
            "our_representative": r.our_representative,
            "overall_result": r.overall_result,
            "notes": r.notes,
            "sign_date": str(r.sign_date) if r.sign_date else None,
            "sign_by": r.sign_by,
            "created_by": r.created_by,
            "created_at": str(r.created_at) if r.created_at else None,
            "updated_at": str(r.updated_at) if r.updated_at else None,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/{id}", summary="获取验收记录详情")
def get_acceptance_record(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    id: int,
) -> Any:
    """获取验收记录详情，包含检查清单和问题"""
    _ensure_tables(db)

    # 获取主记录
    sql = text("""
        SELECT 
            ar.id, ar.project_id, ar.acceptance_type, ar.acceptance_code,
            ar.title, ar.status, ar.scheduled_date, ar.actual_date,
            ar.location, ar.customer_representative, ar.our_representative,
            ar.overall_result, ar.notes, ar.sign_date, ar.sign_by,
            ar.created_by, ar.created_at, ar.updated_at,
            p.project_name, p.project_code
        FROM acceptance_records ar
        LEFT JOIN projects p ON ar.project_id = p.id
        WHERE ar.id = :id
    """)
    row = db.execute(sql, {"id": id}).fetchone()

    if not row:
        return {"error": "验收记录不存在"}

    # 获取检查清单
    checklist_sql = text("""
        SELECT id, acceptance_id, item_no, category, check_item, expected_result,
               actual_result, status, remarks, checked_by, 
               strftime('%Y-%m-%d %H:%M:%S', checked_at) as checked_at
        FROM acceptance_checklist
        WHERE acceptance_id = :acceptance_id
        ORDER BY item_no
    """)
    checklist_rows = db.execute(checklist_sql, {"acceptance_id": id}).fetchall()
    checklist = [
        {
            "id": r.id,
            "acceptance_id": r.acceptance_id,
            "item_no": r.item_no,
            "category": r.category,
            "check_item": r.check_item,
            "expected_result": r.expected_result,
            "actual_result": r.actual_result,
            "status": r.status,
            "remarks": r.remarks,
            "checked_by": r.checked_by,
            "checked_at": r.checked_at,
        }
        for r in checklist_rows
    ]

    # 获取问题列表
    issues_sql = text("""
        SELECT id, acceptance_id, issue_no, severity, description, root_cause,
               solution, status, responsible, 
               strftime('%Y-%m-%d', due_date) as due_date,
               strftime('%Y-%m-%d', resolved_date) as resolved_date,
               strftime('%Y-%m-%d %H:%M:%S', created_at) as created_at
        FROM acceptance_issues
        WHERE acceptance_id = :acceptance_id
        ORDER BY 
            CASE severity WHEN 'critical' THEN 1 WHEN 'major' THEN 2 WHEN 'minor' THEN 3 END,
            issue_no
    """)
    issues_rows = db.execute(issues_sql, {"acceptance_id": id}).fetchall()
    issues = [
        {
            "id": r.id,
            "acceptance_id": r.acceptance_id,
            "issue_no": r.issue_no,
            "severity": r.severity,
            "description": r.description,
            "root_cause": r.root_cause,
            "solution": r.solution,
            "status": r.status,
            "responsible": r.responsible,
            "due_date": r.due_date,
            "resolved_date": r.resolved_date,
            "created_at": r.created_at,
        }
        for r in issues_rows
    ]

    # 统计信息
    checklist_stats = {
        "total": len(checklist),
        "passed": sum(1 for c in checklist if c["status"] == "pass"),
        "failed": sum(1 for c in checklist if c["status"] == "fail"),
        "pending": sum(1 for c in checklist if c["status"] == "pending"),
        "na": sum(1 for c in checklist if c["status"] == "na"),
    }

    issues_stats = {
        "total": len(issues),
        "open": sum(1 for i in issues if i["status"] == "open"),
        "fixing": sum(1 for i in issues if i["status"] == "fixing"),
        "resolved": sum(1 for i in issues if i["status"] == "resolved"),
        "closed": sum(1 for i in issues if i["status"] == "closed"),
        "critical": sum(1 for i in issues if i["severity"] == "critical"),
        "major": sum(1 for i in issues if i["severity"] == "major"),
        "minor": sum(1 for i in issues if i["severity"] == "minor"),
    }

    return {
        "id": row.id,
        "project_id": row.project_id,
        "project_name": row.project_name,
        "project_code": row.project_code,
        "acceptance_type": row.acceptance_type,
        "acceptance_code": row.acceptance_code,
        "title": row.title,
        "status": row.status,
        "scheduled_date": str(row.scheduled_date) if row.scheduled_date else None,
        "actual_date": str(row.actual_date) if row.actual_date else None,
        "location": row.location,
        "customer_representative": row.customer_representative,
        "our_representative": row.our_representative,
        "overall_result": row.overall_result,
        "notes": row.notes,
        "sign_date": str(row.sign_date) if row.sign_date else None,
        "sign_by": row.sign_by,
        "created_by": row.created_by,
        "created_at": str(row.created_at) if row.created_at else None,
        "updated_at": str(row.updated_at) if row.updated_at else None,
        "checklist": checklist,
        "checklist_stats": checklist_stats,
        "issues": issues,
        "issues_stats": issues_stats,
    }


@router.post("/", summary="创建验收记录")
def create_acceptance_record(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    data: dict,
) -> Any:
    """创建新的验收记录"""
    _ensure_tables(db)

    # 生成验收编号
    acceptance_type = data.get("acceptance_type", "FAT")
    project_id = data.get("project_id")

    # 获取项目信息
    project_sql = text("SELECT project_code FROM projects WHERE id = :id")
    project = db.execute(project_sql, {"id": project_id}).fetchone()
    project_code = project.project_code if project else "PRJ"

    # 生成编号：PRJ-FAT-001
    count_sql = text("""
        SELECT COUNT(*) as cnt FROM acceptance_records 
        WHERE project_id = :project_id AND acceptance_type = :acceptance_type
    """)
    count = db.execute(count_sql, {"project_id": project_id, "acceptance_type": acceptance_type}).fetchone().cnt
    acceptance_code = f"{project_code}-{acceptance_type}-{str(count + 1).zfill(3)}"

    insert_sql = text("""
        INSERT INTO acceptance_records (
            project_id, acceptance_type, acceptance_code, title, status,
            scheduled_date, location, customer_representative, our_representative,
            notes, created_by, created_at, updated_at
        ) VALUES (
            :project_id, :acceptance_type, :acceptance_code, :title, :status,
            :scheduled_date, :location, :customer_representative, :our_representative,
            :notes, :created_by, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
    """)

    db.execute(insert_sql, {
        "project_id": project_id,
        "acceptance_type": acceptance_type,
        "acceptance_code": acceptance_code,
        "title": data.get("title"),
        "status": data.get("status", "draft"),
        "scheduled_date": data.get("scheduled_date"),
        "location": data.get("location"),
        "customer_representative": data.get("customer_representative"),
        "our_representative": data.get("our_representative"),
        "notes": data.get("notes"),
        "created_by": current_user.id,
    })

    db.commit()

    # 获取新创建的记录 ID
    result = db.execute(text("SELECT last_insert_rowid() as id")).fetchone()
    new_id = result.id

    return {"id": new_id, "acceptance_code": acceptance_code, "message": "创建成功"}


@router.put("/{id}", summary="更新验收记录")
def update_acceptance_record(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    id: int,
    data: dict,
) -> Any:
    """更新验收记录"""
    _ensure_tables(db)

    # 检查记录是否存在
    check_sql = text("SELECT id FROM acceptance_records WHERE id = :id")
    if not db.execute(check_sql, {"id": id}).fetchone():
        return {"error": "验收记录不存在"}

    # 构建更新字段
    update_fields = []
    params = {"id": id}

    allowed_fields = [
        "title", "status", "scheduled_date", "actual_date", "location",
        "customer_representative", "our_representative", "overall_result",
        "notes", "sign_date", "sign_by"
    ]

    for field in allowed_fields:
        if field in data:
            update_fields.append(f"{field} = :{field}")
            params[field] = data[field]

    if not update_fields:
        return {"error": "没有可更新的字段"}

    update_fields.append("updated_at = CURRENT_TIMESTAMP")

    update_sql = text(f"""
        UPDATE acceptance_records 
        SET {", ".join(update_fields)}
        WHERE id = :id
    """)

    db.execute(update_sql, params)
    db.commit()

    return {"message": "更新成功"}


@router.post("/{id}/checklist", summary="添加/更新检查清单")
def add_checklist_items(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    id: int,
    data: dict,
) -> Any:
    """添加或更新检查清单项"""
    _ensure_tables(db)

    # 检查验收记录是否存在
    check_sql = text("SELECT id FROM acceptance_records WHERE id = :id")
    if not db.execute(check_sql, {"id": id}).fetchone():
        return {"error": "验收记录不存在"}

    items = data.get("items", [])
    if not items:
        return {"error": "检查清单项不能为空"}

    inserted_count = 0
    for item in items:
        # 检查是否已存在（根据 item_no）
        existing_sql = text("""
            SELECT id FROM acceptance_checklist 
            WHERE acceptance_id = :acceptance_id AND item_no = :item_no
        """)
        existing = db.execute(existing_sql, {
            "acceptance_id": id,
            "item_no": item.get("item_no"),
        }).fetchone()

        if existing:
            # 更新现有项
            update_sql = text("""
                UPDATE acceptance_checklist 
                SET category = :category, check_item = :check_item,
                    expected_result = :expected_result, actual_result = :actual_result,
                    status = :status, remarks = :remarks,
                    checked_by = :checked_by, checked_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """)
            db.execute(update_sql, {
                "id": existing.id,
                "category": item.get("category"),
                "check_item": item.get("check_item"),
                "expected_result": item.get("expected_result"),
                "actual_result": item.get("actual_result"),
                "status": item.get("status", "pending"),
                "remarks": item.get("remarks"),
                "checked_by": current_user.real_name or current_user.username,
            })
        else:
            # 插入新项
            insert_sql = text("""
                INSERT INTO acceptance_checklist (
                    acceptance_id, item_no, category, check_item, expected_result,
                    actual_result, status, remarks, checked_by, checked_at
                ) VALUES (
                    :acceptance_id, :item_no, :category, :check_item, :expected_result,
                    :actual_result, :status, :remarks, :checked_by, CURRENT_TIMESTAMP
                )
            """)
            db.execute(insert_sql, {
                "acceptance_id": id,
                "item_no": item.get("item_no"),
                "category": item.get("category"),
                "check_item": item.get("check_item"),
                "expected_result": item.get("expected_result"),
                "actual_result": item.get("actual_result"),
                "status": item.get("status", "pending"),
                "remarks": item.get("remarks"),
                "checked_by": current_user.real_name or current_user.username,
            })
            inserted_count += 1

    db.commit()

    return {"message": f"成功处理 {len(items)} 项检查清单", "inserted": inserted_count}


@router.put("/{id}/sign", summary="签收验收记录")
def sign_off_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    id: int,
    data: dict,
) -> Any:
    """签收验收记录"""
    _ensure_tables(db)

    # 检查记录是否存在
    check_sql = text("SELECT id, status FROM acceptance_records WHERE id = :id")
    record = db.execute(check_sql, {"id": id}).fetchone()
    if not record:
        return {"error": "验收记录不存在"}

    # 更新签收信息
    update_sql = text("""
        UPDATE acceptance_records 
        SET status = 'signed', 
            sign_date = :sign_date,
            sign_by = :sign_by,
            overall_result = :overall_result,
            actual_date = :actual_date,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :id
    """)

    db.execute(update_sql, {
        "id": id,
        "sign_date": data.get("sign_date", datetime.now().strftime("%Y-%m-%d")),
        "sign_by": data.get("sign_by", current_user.real_name or current_user.username),
        "overall_result": data.get("overall_result", "pass"),
        "actual_date": data.get("actual_date", datetime.now().strftime("%Y-%m-%d")),
    })

    db.commit()

    return {"message": "签收成功", "status": "signed"}
