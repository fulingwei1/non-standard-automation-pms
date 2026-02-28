# -*- coding: utf-8 -*-
"""
ECN 工程变更→BOM 联动 API

提供 ECN 变更通知的 CRUD 操作，以及与 BOM 的联动功能
"""

import json
import logging
import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)

router = APIRouter()

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "app.db"


def get_db_connection():
    """获取 SQLite 数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    """Lazy init - 初始化 ECN 相关表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建 ECN 记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ecn_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ecn_no VARCHAR(50) UNIQUE NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            change_type VARCHAR(20) NOT NULL,
            affected_projects JSON,
            status VARCHAR(20) DEFAULT 'draft',
            created_by INTEGER,
            priority VARCHAR(20) DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建 ECN BOM 变更表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ecn_bom_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ecn_id INTEGER NOT NULL,
            bom_id INTEGER,
            project_id INTEGER,
            material_code VARCHAR(100),
            change_action VARCHAR(20) NOT NULL,
            old_value JSON,
            new_value JSON,
            cost_impact DECIMAL(14,2) DEFAULT 0,
            applied_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ecn_id) REFERENCES ecn_records(id)
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ecn_records_status ON ecn_records(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ecn_records_change_type ON ecn_records(change_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ecn_bom_changes_ecn_id ON ecn_bom_changes(ecn_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ecn_bom_changes_project_id ON ecn_bom_changes(project_id)")
    
    conn.commit()
    conn.close()


def generate_ecn_no(db_conn) -> str:
    """生成 ECN 编号"""
    cursor = db_conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"ECN{today}"
    
    cursor.execute("SELECT ecn_no FROM ecn_records WHERE ecn_no LIKE ? ORDER BY ecn_no DESC LIMIT 1", (f"{prefix}%",))
    row = cursor.fetchone()
    
    if row:
        last_no = row["ecn_no"]
        try:
            seq = int(last_no[-4:]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    
    return f"{prefix}{seq:04d}"


# 初始化表（lazy init）
init_tables()


@router.post("/ecn/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_ecn(
    ecn_no: Optional[str] = Query(None, description="ECN 编号（可选，不提供则自动生成）"),
    title: str = Query(..., description="ECN 标题"),
    description: Optional[str] = Query(None, description="变更描述"),
    change_type: str = Query(..., description="变更类型：材料替换/设计变更/工艺优化"),
    affected_projects: str = Query(..., description="受影响项目 ID 列表（JSON 数组）"),
    priority: str = Query("medium", description="优先级：low/medium/high/urgent"),
    created_by: Optional[int] = Query(None, description="创建人 ID"),
):
    """
    创建 ECN 工程变更通知
    
    - **ecn_no**: ECN 编号（可选，不提供则自动生成）
    - **title**: ECN 标题
    - **description**: 变更描述
    - **change_type**: 变更类型（材料替换/设计变更/工艺优化）
    - **affected_projects**: 受影响项目 ID 列表（JSON 数组字符串）
    - **status**: 状态（draft/reviewing/approved/implemented/closed）
    - **created_by**: 创建人 ID
    - **priority**: 优先级（low/medium/high/urgent）
    """
    # 验证 change_type
    valid_change_types = ["材料替换", "设计变更", "工艺优化"]
    if change_type not in valid_change_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的变更类型，必须是：{', '.join(valid_change_types)}"
        )
    
    # 验证 priority
    valid_priorities = ["low", "medium", "high", "urgent"]
    if priority not in valid_priorities:
        raise HTTPException(
            status_code=400,
            detail=f"无效的优先级，必须是：{', '.join(valid_priorities)}"
        )
    
    # 解析 affected_projects
    try:
        affected_projects_list = json.loads(affected_projects)
        if not isinstance(affected_projects_list, list):
            raise ValueError("必须是数组")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"affected_projects 格式错误：{str(e)}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 生成或使用提供的 ECN 编号
        if ecn_no:
            # 检查是否已存在
            cursor.execute("SELECT id FROM ecn_records WHERE ecn_no = ?", (ecn_no,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="ECN 编号已存在")
        else:
            ecn_no = generate_ecn_no(conn)
        
        # 插入记录
        cursor.execute("""
            INSERT INTO ecn_records (
                ecn_no, title, description, change_type, affected_projects,
                status, created_by, priority
            ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?)
        """, (
            ecn_no, title, description, change_type,
            json.dumps(affected_projects_list), created_by, priority
        ))
        
        conn.commit()
        ecn_id = cursor.lastrowid
        
        # 返回创建的记录
        cursor.execute("SELECT * FROM ecn_records WHERE id = ?", (ecn_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "ecn_no": row["ecn_no"],
            "title": row["title"],
            "description": row["description"],
            "change_type": row["change_type"],
            "affected_projects": json.loads(row["affected_projects"]),
            "status": row["status"],
            "created_by": row["created_by"],
            "priority": row["priority"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    finally:
        conn.close()


@router.get("/ecn/", response_model=dict, status_code=status.HTTP_200_OK)
def list_ecn(
    status: Optional[str] = Query(None, description="状态筛选：draft/reviewing/approved/implemented/closed"),
    change_type: Optional[str] = Query(None, description="变更类型筛选：材料替换/设计变更/工艺优化"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    获取 ECN 列表
    
    - **status**: 状态筛选
    - **change_type**: 变更类型筛选
    - **page**: 页码
    - **page_size**: 每页数量
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 构建查询
        conditions = []
        params = []
        
        if status:
            valid_statuses = ["draft", "reviewing", "approved", "implemented", "closed"]
            if status in valid_statuses:
                conditions.append("status = ?")
                params.append(status)
        
        if change_type:
            conditions.append("change_type = ?")
            params.append(change_type)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 查询总数
        cursor.execute(f"SELECT COUNT(*) as total FROM ecn_records WHERE {where_clause}", params)
        total = cursor.fetchone()["total"]
        
        # 分页查询
        offset = (page - 1) * page_size
        cursor.execute(f"""
            SELECT * FROM ecn_records
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row["id"],
                "ecn_no": row["ecn_no"],
                "title": row["title"],
                "description": row["description"],
                "change_type": row["change_type"],
                "affected_projects": json.loads(row["affected_projects"]),
                "affected_projects_count": len(json.loads(row["affected_projects"])),
                "status": row["status"],
                "created_by": row["created_by"],
                "priority": row["priority"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    finally:
        conn.close()


@router.get("/ecn/{ecn_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_ecn(ecn_id: int):
    """
    获取 ECN 详情
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM ecn_records WHERE id = ?", (ecn_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="ECN 不存在")
        
        # 查询关联的 BOM 变更
        cursor.execute("""
            SELECT * FROM ecn_bom_changes WHERE ecn_id = ? ORDER BY created_at DESC
        """, (ecn_id,))
        bom_changes = []
        for change_row in cursor.fetchall():
            bom_changes.append({
                "id": change_row["id"],
                "bom_id": change_row["bom_id"],
                "project_id": change_row["project_id"],
                "material_code": change_row["material_code"],
                "change_action": change_row["change_action"],
                "old_value": json.loads(change_row["old_value"]) if change_row["old_value"] else None,
                "new_value": json.loads(change_row["new_value"]) if change_row["new_value"] else None,
                "cost_impact": float(change_row["cost_impact"]) if change_row["cost_impact"] else 0,
                "applied_at": change_row["applied_at"],
                "created_at": change_row["created_at"]
            })
        
        return {
            "id": row["id"],
            "ecn_no": row["ecn_no"],
            "title": row["title"],
            "description": row["description"],
            "change_type": row["change_type"],
            "affected_projects": json.loads(row["affected_projects"]),
            "status": row["status"],
            "created_by": row["created_by"],
            "priority": row["priority"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "bom_changes": bom_changes
        }
    finally:
        conn.close()


@router.put("/ecn/{ecn_id}", response_model=dict, status_code=status.HTTP_200_OK)
def update_ecn(
    ecn_id: int,
    title: Optional[str] = Query(None, description="ECN 标题"),
    description: Optional[str] = Query(None, description="变更描述"),
    change_type: Optional[str] = Query(None, description="变更类型"),
    affected_projects: Optional[str] = Query(None, description="受影响项目 ID 列表"),
    status: Optional[str] = Query(None, description="状态"),
    priority: Optional[str] = Query(None, description="优先级"),
):
    """
    更新 ECN
    
    只能更新草稿状态的 ECN
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查 ECN 是否存在
        cursor.execute("SELECT * FROM ecn_records WHERE id = ?", (ecn_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="ECN 不存在")
        
        if row["status"] != "draft":
            raise HTTPException(status_code=400, detail="只能更新草稿状态的 ECN")
        
        # 构建更新字段
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if change_type is not None:
            valid_change_types = ["材料替换", "设计变更", "工艺优化"]
            if change_type not in valid_change_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的变更类型，必须是：{', '.join(valid_change_types)}"
                )
            updates.append("change_type = ?")
            params.append(change_type)
        
        if affected_projects is not None:
            try:
                affected_list = json.loads(affected_projects)
                if not isinstance(affected_list, list):
                    raise ValueError("必须是数组")
                updates.append("affected_projects = ?")
                params.append(json.dumps(affected_list))
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(status_code=400, detail=f"affected_projects 格式错误：{str(e)}")
        
        if status is not None:
            valid_statuses = ["draft", "reviewing", "approved", "implemented", "closed"]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的状态，必须是：{', '.join(valid_statuses)}"
                )
            updates.append("status = ?")
            params.append(status)
        
        if priority is not None:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if priority not in valid_priorities:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的优先级，必须是：{', '.join(valid_priorities)}"
                )
            updates.append("priority = ?")
            params.append(priority)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(ecn_id)
            
            cursor.execute(f"""
                UPDATE ecn_records SET {', '.join(updates)} WHERE id = ?
            """, params)
            
            conn.commit()
        
        # 返回更新后的记录
        cursor.execute("SELECT * FROM ecn_records WHERE id = ?", (ecn_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "ecn_no": row["ecn_no"],
            "title": row["title"],
            "description": row["description"],
            "change_type": row["change_type"],
            "affected_projects": json.loads(row["affected_projects"]),
            "status": row["status"],
            "created_by": row["created_by"],
            "priority": row["priority"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    finally:
        conn.close()


@router.post("/ecn/{ecn_id}/apply-to-bom", response_model=dict, status_code=status.HTTP_200_OK)
def apply_ecn_to_bom(ecn_id: int):
    """
    将 ECN 变更应用到 BOM
    
    自动更新受影响的 BOM 项
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查 ECN 是否存在
        cursor.execute("SELECT * FROM ecn_records WHERE id = ?", (ecn_id,))
        ecn_row = cursor.fetchone()
        
        if not ecn_row:
            raise HTTPException(status_code=404, detail="ECN 不存在")
        
        if ecn_row["status"] != "approved":
            raise HTTPException(status_code=400, detail="只能应用已批准的 ECN")
        
        affected_projects = json.loads(ecn_row["affected_projects"])
        change_type = ecn_row["change_type"]
        
        # 模拟 BOM 更新逻辑（实际项目中需要查询真实的 BOM 表）
        # 这里创建 BOM 变更记录
        updated_count = 0
        bom_changes = []
        
        for project_id in affected_projects:
            # 模拟：查询该项目的 BOM 项
            # 在实际项目中，这里应该查询 bom_items 表
            # 这里我们创建示例变更记录
            
            # 根据变更类型模拟不同的 BOM 更新
            if change_type == "材料替换":
                # 模拟材料替换：更新物料编码
                cursor.execute("""
                    INSERT INTO ecn_bom_changes (
                        ecn_id, project_id, bom_id, material_code,
                        change_action, old_value, new_value, cost_impact, applied_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    ecn_id, project_id, None, f"MATERIAL-{project_id}-001",
                    "REPLACE",
                    json.dumps({"material_code": "OLD-MAT-001", "name": "旧物料"}),
                    json.dumps({"material_code": "NEW-MAT-001", "name": "新物料"}),
                    0,
                ))
                updated_count += 1
                bom_changes.append({
                    "project_id": project_id,
                    "material_code": f"MATERIAL-{project_id}-001",
                    "action": "REPLACE"
                })
            
            elif change_type == "设计变更":
                # 模拟设计变更：更新规格参数
                cursor.execute("""
                    INSERT INTO ecn_bom_changes (
                        ecn_id, project_id, bom_id, material_code,
                        change_action, old_value, new_value, cost_impact, applied_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    ecn_id, project_id, None, f"SPEC-{project_id}-001",
                    "UPDATE",
                    json.dumps({"spec": "V1.0", "tolerance": "±0.1"}),
                    json.dumps({"spec": "V2.0", "tolerance": "±0.05"}),
                    0,
                ))
                updated_count += 1
                bom_changes.append({
                    "project_id": project_id,
                    "material_code": f"SPEC-{project_id}-001",
                    "action": "UPDATE"
                })
            
            elif change_type == "工艺优化":
                # 模拟工艺优化：更新工艺参数
                cursor.execute("""
                    INSERT INTO ecn_bom_changes (
                        ecn_id, project_id, bom_id, material_code,
                        change_action, old_value, new_value, cost_impact, applied_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    ecn_id, project_id, None, f"PROCESS-{project_id}-001",
                    "OPTIMIZE",
                    json.dumps({"process": "焊接", "temp": "200°C"}),
                    json.dumps({"process": "激光焊接", "temp": "250°C"}),
                    0,
                ))
                updated_count += 1
                bom_changes.append({
                    "project_id": project_id,
                    "material_code": f"PROCESS-{project_id}-001",
                    "action": "OPTIMIZE"
                })
        
        conn.commit()
        
        # 更新 ECN 状态为 implemented
        cursor.execute("""
            UPDATE ecn_records SET status = 'implemented', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ecn_id,))
        conn.commit()
        
        return {
            "success": True,
            "ecn_id": ecn_id,
            "ecn_no": ecn_row["ecn_no"],
            "updated_bom_count": updated_count,
            "affected_projects": affected_projects,
            "bom_changes": bom_changes,
            "message": f"成功应用 ECN 到 {updated_count} 个 BOM 项"
        }
    finally:
        conn.close()


@router.get("/ecn/{ecn_id}/impact", response_model=dict, status_code=status.HTTP_200_OK)
def get_ecn_impact(ecn_id: int):
    """
    获取 ECN 变更影响分析
    
    返回受影响项目数、BOM 项数、预估成本影响
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查 ECN 是否存在
        cursor.execute("SELECT * FROM ecn_records WHERE id = ?", (ecn_id,))
        ecn_row = cursor.fetchone()
        
        if not ecn_row:
            raise HTTPException(status_code=404, detail="ECN 不存在")
        
        affected_projects = json.loads(ecn_row["affected_projects"])
        affected_projects_count = len(affected_projects)
        
        # 查询已应用的 BOM 变更数
        cursor.execute("""
            SELECT COUNT(*) as count, SUM(cost_impact) as total_cost
            FROM ecn_bom_changes WHERE ecn_id = ?
        """, (ecn_id,))
        bom_row = cursor.fetchone()
        
        bom_changes_count = bom_row["count"] or 0
        total_cost_impact = float(bom_row["total_cost"] or 0)
        
        # 预估成本影响（根据变更类型和优先级估算）
        priority_multiplier = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.0,
            "urgent": 3.0
        }.get(ecn_row["priority"], 1.0)
        
        change_type_base_cost = {
            "材料替换": 5000,
            "设计变更": 10000,
            "工艺优化": 3000
        }.get(ecn_row["change_type"], 5000)
        
        estimated_cost = change_type_base_cost * affected_projects_count * priority_multiplier
        
        # 影响分析详情
        impact_details = {
            "projects": [],
            "bom_items": [],
            "cost_breakdown": {}
        }
        
        # 获取每个项目的影响
        for project_id in affected_projects:
            cursor.execute("""
                SELECT COUNT(*) as count FROM ecn_bom_changes
                WHERE ecn_id = ? AND project_id = ?
            """, (ecn_id, project_id))
            proj_row = cursor.fetchone()
            impact_details["projects"].append({
                "project_id": project_id,
                "bom_changes_count": proj_row["count"] or 0
            })
        
        # 获取 BOM 变更明细
        cursor.execute("""
            SELECT * FROM ecn_bom_changes WHERE ecn_id = ?
        """, (ecn_id,))
        for change_row in cursor.fetchall():
            impact_details["bom_items"].append({
                "id": change_row["id"],
                "project_id": change_row["project_id"],
                "material_code": change_row["material_code"],
                "change_action": change_row["change_action"],
                "cost_impact": float(change_row["cost_impact"]) if change_row["cost_impact"] else 0
            })
        
        # 按变更类型统计成本
        impact_details["cost_breakdown"] = {
            "material_replacement": estimated_cost * 0.5 if ecn_row["change_type"] == "材料替换" else 0,
            "design_change": estimated_cost * 0.7 if ecn_row["change_type"] == "设计变更" else 0,
            "process_optimization": estimated_cost * 0.3 if ecn_row["change_type"] == "工艺优化" else 0,
            "labor": estimated_cost * 0.2,
            "overhead": estimated_cost * 0.1
        }
        
        return {
            "ecn_id": ecn_id,
            "ecn_no": ecn_row["ecn_no"],
            "title": ecn_row["title"],
            "change_type": ecn_row["change_type"],
            "priority": ecn_row["priority"],
            "status": ecn_row["status"],
            "impact_summary": {
                "affected_projects_count": affected_projects_count,
                "affected_bom_items_count": bom_changes_count,
                "actual_cost_impact": total_cost_impact,
                "estimated_cost_impact": estimated_cost
            },
            "impact_details": impact_details,
            "recommendations": [
                f"建议优先处理优先级为 {ecn_row['priority']} 的变更",
                f"变更类型为'{ecn_row['change_type']}',需关注相关质量控制",
                f"影响 {affected_projects_count} 个项目，建议分批实施"
            ] if ecn_row["status"] == "draft" else []
        }
    finally:
        conn.close()
