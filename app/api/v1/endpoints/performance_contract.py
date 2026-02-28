# -*- coding: utf-8 -*-
"""
绩效合约管理 API 端点

绩效合约体系：
- L1: 公司↔高管 — 年度经营目标合约
- L2: 高管↔部门经理 — 部门目标合约
- L3: 部门经理↔员工 — 个人绩效合约
"""

import sqlite3
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.common import ResponseModel, PageResponse

router = APIRouter()

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "../../../../data/app.db")


def get_db_connection():
    """获取 SQLite 数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    """Lazy init - 初始化数据表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建绩效合约表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_no TEXT UNIQUE NOT NULL,
            contract_type TEXT NOT NULL CHECK(contract_type IN ('L1', 'L2', 'L3')),
            year INTEGER NOT NULL,
            quarter INTEGER,
            signer_id INTEGER,
            signer_name TEXT NOT NULL,
            signer_title TEXT,
            counterpart_id INTEGER,
            counterpart_name TEXT NOT NULL,
            counterpart_title TEXT,
            department_id INTEGER,
            department_name TEXT,
            strategy_id INTEGER,
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'pending_review', 'pending_sign', 'active', 'completed', 'terminated')),
            total_weight REAL DEFAULT 0,
            sign_date DATE,
            effective_date DATE,
            expiry_date DATE,
            signer_signature DATETIME,
            counterpart_signature DATETIME,
            remarks TEXT,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建绩效合约指标条目表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_contract_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,
            category TEXT NOT NULL CHECK(category IN ('业绩指标', '管理指标', '能力指标', '态度指标')),
            indicator_name TEXT NOT NULL,
            indicator_description TEXT,
            weight REAL NOT NULL,
            unit TEXT,
            target_value TEXT,
            challenge_value TEXT,
            baseline_value TEXT,
            scoring_rule TEXT,
            data_source TEXT,
            evaluation_method TEXT,
            actual_value TEXT,
            score REAL,
            evaluator_comment TEXT,
            source_type TEXT CHECK(source_type IN ('kpi', 'work', 'custom')),
            source_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES performance_contracts(id) ON DELETE CASCADE
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contract_type ON performance_contracts(contract_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contract_status ON performance_contracts(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contract_year ON performance_contracts(year)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contract_signer ON performance_contracts(signer_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_item_contract ON performance_contract_items(contract_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_item_source ON performance_contract_items(source_type, source_id)
    """)
    
    conn.commit()
    conn.close()


# 确保表存在
init_tables()


def generate_contract_no(contract_type: str, year: int) -> str:
    """生成合约编号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PC-{contract_type}-{year}-{timestamp}"


def calculate_total_weight(contract_id: int) -> float:
    """计算合约总权重"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(weight), 0) as total FROM performance_contract_items WHERE contract_id = ?",
        (contract_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return float(result['total']) if result else 0.0


# ============================================
# 合约 CRUD
# ============================================

@router.post("", response_model=ResponseModel)
def create_contract(
    contract_no: str = Query(..., description="合约编号"),
    contract_type: str = Query(..., description="合约类型 (L1/L2/L3)"),
    year: int = Query(..., description="年度"),
    quarter: Optional[int] = Query(None, description="季度 (可选)"),
    signer_id: Optional[int] = Query(None, description="签约人 ID"),
    signer_name: str = Query(..., description="签约人姓名"),
    signer_title: Optional[str] = Query(None, description="签约人职位"),
    counterpart_id: Optional[int] = Query(None, description="对方/上级 ID"),
    counterpart_name: str = Query(..., description="对方/上级姓名"),
    counterpart_title: Optional[str] = Query(None, description="对方/上级职位"),
    department_id: Optional[int] = Query(None, description="部门 ID"),
    department_name: Optional[str] = Query(None, description="部门名称"),
    strategy_id: Optional[int] = Query(None, description="关联战略 ID"),
    status: str = Query("draft", description="状态"),
    sign_date: Optional[str] = Query(None, description="签署日期"),
    effective_date: Optional[str] = Query(None, description="生效日期"),
    expiry_date: Optional[str] = Query(None, description="到期日期"),
    remarks: Optional[str] = Query(None, description="备注"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """创建绩效合约"""
    if contract_type not in ['L1', 'L2', 'L3']:
        raise HTTPException(status_code=400, detail="合约类型必须是 L1/L2/L3")
    
    if status not in ['draft', 'pending_review', 'pending_sign', 'active', 'completed', 'terminated']:
        raise HTTPException(status_code=400, detail="状态无效")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查合约编号是否已存在
        cursor.execute("SELECT id FROM performance_contracts WHERE contract_no = ?", (contract_no,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="合约编号已存在")
        
        cursor.execute("""
            INSERT INTO performance_contracts (
                contract_no, contract_type, year, quarter,
                signer_id, signer_name, signer_title,
                counterpart_id, counterpart_name, counterpart_title,
                department_id, department_name,
                strategy_id, status,
                sign_date, effective_date, expiry_date,
                remarks, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_no, contract_type, year, quarter,
            signer_id, signer_name, signer_title,
            counterpart_id, counterpart_name, counterpart_title,
            department_id, department_name,
            strategy_id, status,
            sign_date, effective_date, expiry_date,
            remarks, current_user.id
        ))
        
        contract_id = cursor.lastrowid
        conn.commit()
        
        # 获取创建的合约
        cursor.execute("SELECT * FROM performance_contracts WHERE id = ?", (contract_id,))
        contract = dict(cursor.fetchone())
        
        return ResponseModel(
            code=200,
            message="创建成功",
            data=contract
        )
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")
    finally:
        conn.close()


@router.get("", response_model=ResponseModel)
def list_contracts(
    contract_type: Optional[str] = Query(None, description="合约类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    year: Optional[int] = Query(None, description="年度筛选"),
    signer_id: Optional[int] = Query(None, description="签约人 ID 筛选"),
    department_id: Optional[int] = Query(None, description="部门 ID 筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """获取绩效合约列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建查询条件
    conditions = []
    params = []
    
    if contract_type:
        conditions.append("contract_type = ?")
        params.append(contract_type)
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    if year:
        conditions.append("year = ?")
        params.append(year)
    
    if signer_id:
        conditions.append("signer_id = ?")
        params.append(signer_id)
    
    if department_id:
        conditions.append("department_id = ?")
        params.append(department_id)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # 查询合约列表
    cursor.execute(f"""
        SELECT * FROM performance_contracts
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, skip])
    
    contracts = [dict(row) for row in cursor.fetchall()]
    
    # 查询总数
    cursor.execute(f"""
        SELECT COUNT(*) as count FROM performance_contracts
        WHERE {where_clause}
    """, params)
    total = cursor.fetchone()['count']
    
    conn.close()
    
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": contracts,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.get("/{contract_id}", response_model=ResponseModel)
def get_contract(
    contract_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """获取绩效合约详情（含指标条目）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取合约
    cursor.execute("SELECT * FROM performance_contracts WHERE id = ?", (contract_id,))
    contract = cursor.fetchone()
    
    if not contract:
        conn.close()
        raise HTTPException(status_code=404, detail="合约不存在")
    
    contract_data = dict(contract)
    
    # 获取指标条目
    cursor.execute("""
        SELECT * FROM performance_contract_items
        WHERE contract_id = ?
        ORDER BY sort_order, id
    """, (contract_id,))
    
    items = [dict(row) for row in cursor.fetchall()]
    contract_data['items'] = items
    
    conn.close()
    
    return ResponseModel(
        code=200,
        message="查询成功",
        data=contract_data
    )


@router.put("/{contract_id}", response_model=ResponseModel)
def update_contract(
    contract_id: int,
    contract_no: Optional[str] = Query(None, description="合约编号"),
    contract_type: Optional[str] = Query(None, description="合约类型"),
    year: Optional[int] = Query(None, description="年度"),
    quarter: Optional[int] = Query(None, description="季度"),
    signer_id: Optional[int] = Query(None, description="签约人 ID"),
    signer_name: Optional[str] = Query(None, description="签约人姓名"),
    signer_title: Optional[str] = Query(None, description="签约人职位"),
    counterpart_id: Optional[int] = Query(None, description="对方 ID"),
    counterpart_name: Optional[str] = Query(None, description="对方姓名"),
    counterpart_title: Optional[str] = Query(None, description="对方职位"),
    department_id: Optional[int] = Query(None, description="部门 ID"),
    department_name: Optional[str] = Query(None, description="部门名称"),
    strategy_id: Optional[int] = Query(None, description="战略 ID"),
    status: Optional[str] = Query(None, description="状态"),
    sign_date: Optional[str] = Query(None, description="签署日期"),
    effective_date: Optional[str] = Query(None, description="生效日期"),
    expiry_date: Optional[str] = Query(None, description="到期日期"),
    remarks: Optional[str] = Query(None, description="备注"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """更新绩效合约"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查合约是否存在
    cursor.execute("SELECT id FROM performance_contracts WHERE id = ?", (contract_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="合约不存在")
    
    # 构建更新字段
    updates = []
    params = []
    
    field_mappings = {
        'contract_no': contract_no,
        'contract_type': contract_type,
        'year': year,
        'quarter': quarter,
        'signer_id': signer_id,
        'signer_name': signer_name,
        'signer_title': signer_title,
        'counterpart_id': counterpart_id,
        'counterpart_name': counterpart_name,
        'counterpart_title': counterpart_title,
        'department_id': department_id,
        'department_name': department_name,
        'strategy_id': strategy_id,
        'status': status,
        'sign_date': sign_date,
        'effective_date': effective_date,
        'expiry_date': expiry_date,
        'remarks': remarks,
    }
    
    for field, value in field_mappings.items():
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    
    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="没有要更新的字段")
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(contract_id)
    
    try:
        cursor.execute(f"""
            UPDATE performance_contracts
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        
        # 返回更新后的合约
        cursor.execute("SELECT * FROM performance_contracts WHERE id = ?", (contract_id,))
        contract = dict(cursor.fetchone())
        
        return ResponseModel(
            code=200,
            message="更新成功",
            data=contract
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败：{str(e)}")
    finally:
        conn.close()


# ============================================
# 指标条目管理
# ============================================

@router.post("/{contract_id}/items", response_model=ResponseModel)
def add_contract_item(
    contract_id: int,
    sort_order: int = Query(0, description="排序"),
    category: str = Query(..., description="指标类别"),
    indicator_name: str = Query(..., description="指标名称"),
    indicator_description: Optional[str] = Query(None, description="指标描述"),
    weight: float = Query(..., description="权重"),
    unit: Optional[str] = Query(None, description="单位"),
    target_value: Optional[str] = Query(None, description="目标值"),
    challenge_value: Optional[str] = Query(None, description="挑战值"),
    baseline_value: Optional[str] = Query(None, description="底线值"),
    scoring_rule: Optional[str] = Query(None, description="评分规则"),
    data_source: Optional[str] = Query(None, description="数据来源"),
    evaluation_method: Optional[str] = Query(None, description="评估方式"),
    source_type: Optional[str] = Query(None, description="来源类型"),
    source_id: Optional[int] = Query(None, description="来源 ID"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """添加合约指标条目"""
    if category not in ['业绩指标', '管理指标', '能力指标', '态度指标']:
        raise HTTPException(status_code=400, detail="指标类别无效")
    
    if source_type and source_type not in ['kpi', 'work', 'custom']:
        raise HTTPException(status_code=400, detail="来源类型无效")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查合约是否存在
    cursor.execute("SELECT id FROM performance_contracts WHERE id = ?", (contract_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="合约不存在")
    
    try:
        cursor.execute("""
            INSERT INTO performance_contract_items (
                contract_id, sort_order, category, indicator_name,
                indicator_description, weight, unit,
                target_value, challenge_value, baseline_value,
                scoring_rule, data_source, evaluation_method,
                source_type, source_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_id, sort_order, category, indicator_name,
            indicator_description, weight, unit,
            target_value, challenge_value, baseline_value,
            scoring_rule, data_source, evaluation_method,
            source_type, source_id
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        
        # 更新合约总权重
        total_weight = calculate_total_weight(contract_id)
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (total_weight, contract_id)
        )
        conn.commit()
        
        # 返回创建的条目
        cursor.execute("SELECT * FROM performance_contract_items WHERE id = ?", (item_id,))
        item = dict(cursor.fetchone())
        
        return ResponseModel(
            code=200,
            message="添加成功",
            data=item
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"添加失败：{str(e)}")
    finally:
        conn.close()


@router.put("/{contract_id}/items/{item_id}", response_model=ResponseModel)
def update_contract_item(
    contract_id: int,
    item_id: int,
    sort_order: Optional[int] = Query(None, description="排序"),
    category: Optional[str] = Query(None, description="指标类别"),
    indicator_name: Optional[str] = Query(None, description="指标名称"),
    indicator_description: Optional[str] = Query(None, description="指标描述"),
    weight: Optional[float] = Query(None, description="权重"),
    unit: Optional[str] = Query(None, description="单位"),
    target_value: Optional[str] = Query(None, description="目标值"),
    challenge_value: Optional[str] = Query(None, description="挑战值"),
    baseline_value: Optional[str] = Query(None, description="底线值"),
    scoring_rule: Optional[str] = Query(None, description="评分规则"),
    data_source: Optional[str] = Query(None, description="数据来源"),
    evaluation_method: Optional[str] = Query(None, description="评估方式"),
    actual_value: Optional[str] = Query(None, description="实际值"),
    score: Optional[float] = Query(None, description="得分"),
    evaluator_comment: Optional[str] = Query(None, description="评估意见"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """更新合约指标条目"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查条目是否存在且属于该合约
    cursor.execute(
        "SELECT * FROM performance_contract_items WHERE id = ? AND contract_id = ?",
        (item_id, contract_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="指标条目不存在或不属于该合约")
    
    # 构建更新字段
    updates = []
    params = []
    
    field_mappings = {
        'sort_order': sort_order,
        'category': category,
        'indicator_name': indicator_name,
        'indicator_description': indicator_description,
        'weight': weight,
        'unit': unit,
        'target_value': target_value,
        'challenge_value': challenge_value,
        'baseline_value': baseline_value,
        'scoring_rule': scoring_rule,
        'data_source': data_source,
        'evaluation_method': evaluation_method,
        'actual_value': actual_value,
        'score': score,
        'evaluator_comment': evaluator_comment,
    }
    
    for field, value in field_mappings.items():
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    
    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="没有要更新的字段")
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(item_id)
    
    try:
        cursor.execute(f"""
            UPDATE performance_contract_items
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        
        # 如果更新了 weight，重新计算总权重
        if weight is not None:
            total_weight = calculate_total_weight(contract_id)
            cursor.execute(
                "UPDATE performance_contracts SET total_weight = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (total_weight, contract_id)
            )
        
        conn.commit()
        
        # 返回更新后的条目
        cursor.execute("SELECT * FROM performance_contract_items WHERE id = ?", (item_id,))
        item = dict(cursor.fetchone())
        
        return ResponseModel(
            code=200,
            message="更新成功",
            data=item
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败：{str(e)}")
    finally:
        conn.close()


@router.delete("/{contract_id}/items/{item_id}", response_model=ResponseModel)
def delete_contract_item(
    contract_id: int,
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """删除合约指标条目"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查条目是否存在且属于该合约
    cursor.execute(
        "SELECT id FROM performance_contract_items WHERE id = ? AND contract_id = ?",
        (item_id, contract_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="指标条目不存在或不属于该合约")
    
    try:
        cursor.execute("DELETE FROM performance_contract_items WHERE id = ?", (item_id,))
        
        # 重新计算总权重
        total_weight = calculate_total_weight(contract_id)
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (total_weight, contract_id)
        )
        
        conn.commit()
        
        return ResponseModel(
            code=200,
            message="删除成功"
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")
    finally:
        conn.close()


# ============================================
# 合约流程操作
# ============================================

@router.post("/{contract_id}/submit", response_model=ResponseModel)
def submit_contract(
    contract_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """提交合约审批"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM performance_contracts WHERE id = ?", (contract_id,))
    contract = cursor.fetchone()
    
    if not contract:
        conn.close()
        raise HTTPException(status_code=404, detail="合约不存在")
    
    if contract['status'] != 'draft':
        conn.close()
        raise HTTPException(status_code=400, detail="只有草稿状态的合约可以提交")
    
    # 检查权重是否为 100
    if abs(contract['total_weight'] - 100.0) > 0.01:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"权重总和必须为 100，当前为{contract['total_weight']}"
        )
    
    try:
        cursor.execute("""
            UPDATE performance_contracts
            SET status = 'pending_review', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (contract_id,))
        conn.commit()
        
        return ResponseModel(
            code=200,
            message="提交成功"
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"提交失败：{str(e)}")
    finally:
        conn.close()


@router.post("/{contract_id}/sign", response_model=ResponseModel)
def sign_contract(
    contract_id: int,
    sign_as: str = Query(..., description="签署身份 (signer/counterpart)"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """签署合约"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM performance_contracts WHERE id = ?", (contract_id,))
    contract = cursor.fetchone()
    
    if not contract:
        conn.close()
        raise HTTPException(status_code=404, detail="合约不存在")
    
    if contract['status'] not in ['pending_sign', 'active']:
        conn.close()
        raise HTTPException(status_code=400, detail="合约状态不允许签署")
    
    try:
        if sign_as == 'signer':
            cursor.execute("""
                UPDATE performance_contracts
                SET signer_signature = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (contract_id,))
        elif sign_as == 'counterpart':
            cursor.execute("""
                UPDATE performance_contracts
                SET counterpart_signature = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (contract_id,))
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="签署身份必须是 signer 或 counterpart")
        
        # 检查双方是否都已签署
        cursor.execute("SELECT signer_signature, counterpart_signature FROM performance_contracts WHERE id = ?", (contract_id,))
        updated = cursor.fetchone()
        
        if updated['signer_signature'] and updated['counterpart_signature']:
            # 双方都签署，状态改为 active
            cursor.execute("""
                UPDATE performance_contracts
                SET status = 'active', sign_date = DATE('now')
                WHERE id = ?
            """, (contract_id,))
        
        conn.commit()
        
        return ResponseModel(
            code=200,
            message="签署成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"签署失败：{str(e)}")
    finally:
        conn.close()


@router.post("/{contract_id}/evaluate", response_model=ResponseModel)
def evaluate_contract(
    contract_id: int,
    evaluations: List[Dict[str, Any]],
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """批量评分（更新指标条目的实际值和得分）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM performance_contracts WHERE id = ?", (contract_id,))
    contract = cursor.fetchone()
    
    if not contract:
        conn.close()
        raise HTTPException(status_code=404, detail="合约不存在")
    
    try:
        for eval_item in evaluations:
            item_id = eval_item.get('item_id')
            actual_value = eval_item.get('actual_value')
            score = eval_item.get('score')
            comment = eval_item.get('evaluator_comment')
            
            if not item_id:
                continue
            
            updates = []
            params = []
            
            if actual_value is not None:
                updates.append("actual_value = ?")
                params.append(str(actual_value))
            
            if score is not None:
                updates.append("score = ?")
                params.append(score)
            
            if comment is not None:
                updates.append("evaluator_comment = ?")
                params.append(comment)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(item_id)
                
                cursor.execute(f"""
                    UPDATE performance_contract_items
                    SET {', '.join(updates)}
                    WHERE id = ? AND contract_id = ?
                """, params + [contract_id])
        
        conn.commit()
        
        return ResponseModel(
            code=200,
            message="评分成功"
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"评分失败：{str(e)}")
    finally:
        conn.close()


# ============================================
# Dashboard 总览
# ============================================

@router.get("/dashboard", response_model=ResponseModel)
def get_dashboard(
    year: Optional[int] = Query(None, description="年度筛选"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """获取绩效合约总览"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建年度筛选条件
    year_condition = "AND year = ?" if year else ""
    year_params = [year] if year else []
    
    # 各类型合约数量
    cursor.execute(f"""
        SELECT contract_type, status, COUNT(*) as count
        FROM performance_contracts
        WHERE 1=1 {year_condition}
        GROUP BY contract_type, status
    """, year_params)
    
    type_status_counts = {}
    for row in cursor.fetchall():
        contract_type = row['contract_type']
        status = row['status']
        count = row['count']
        
        if contract_type not in type_status_counts:
            type_status_counts[contract_type] = {}
        type_status_counts[contract_type][status] = count
    
    # 总计
    cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending_sign' THEN 1 ELSE 0 END) as pending_sign,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            AVG(total_weight) as avg_weight
        FROM performance_contracts
        WHERE 1=1 {year_condition}
    """, year_params)
    
    summary = dict(cursor.fetchone())
    
    # 平均得分（仅计算已评分的条目）
    cursor.execute(f"""
        SELECT AVG(score) as avg_score
        FROM performance_contract_items
        WHERE score IS NOT NULL
        AND contract_id IN (
            SELECT id FROM performance_contracts WHERE 1=1 {year_condition}
        )
    """, year_params)
    
    avg_score_result = cursor.fetchone()
    avg_score = avg_score_result['avg_score'] if avg_score_result else 0
    
    # 签署进度
    cursor.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN signer_signature IS NOT NULL THEN 1 ELSE 0 END) as signer_signed,
            SUM(CASE WHEN counterpart_signature IS NOT NULL THEN 1 ELSE 0 END) as counterpart_signed,
            SUM(CASE WHEN signer_signature IS NOT NULL AND counterpart_signature IS NOT NULL THEN 1 ELSE 0 END) as fully_signed
        FROM performance_contracts
        WHERE status IN ('pending_sign', 'active') {year_condition}
    """, year_params)
    
    signing_progress = dict(cursor.fetchone())
    
    conn.close()
    
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "summary": summary,
            "avg_score": avg_score,
            "type_status_breakdown": type_status_counts,
            "signing_progress": signing_progress
        }
    )


@router.post("/{contract_id}/generate-from-strategy", response_model=ResponseModel)
def generate_from_strategy(
    contract_id: int,
    strategy_id: int,
    include_kpis: bool = Query(True, description="是否包含 KPI"),
    include_annual_works: bool = Query(True, description="是否包含年度工作"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """从战略分解自动生成合约条目"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查合约是否存在
    cursor.execute("SELECT * FROM performance_contracts WHERE id = ?", (contract_id,))
    contract = cursor.fetchone()
    
    if not contract:
        conn.close()
        raise HTTPException(status_code=404, detail="合约不存在")
    
    try:
        items_created = []
        sort_order = 0
        
        # 获取战略关联的 KPI
        if include_kpis:
            cursor.execute("""
                SELECT k.*, c.name as csf_name
                FROM strategy_kpis k
                LEFT JOIN strategy_csfs c ON k.csf_id = c.id
                WHERE k.strategy_id = ? AND k.is_deleted = 0
            """, (strategy_id,))
            
            for kpi in cursor.fetchall():
                sort_order += 1
                cursor.execute("""
                    INSERT INTO performance_contract_items (
                        contract_id, sort_order, category, indicator_name,
                        indicator_description, weight, unit,
                        target_value, challenge_value, baseline_value,
                        scoring_rule, data_source, evaluation_method,
                        source_type, source_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_id, sort_order, '业绩指标', kpi['name'],
                    kpi.get('description'), 0, kpi.get('unit'),
                    str(kpi.get('target_value')), str(kpi.get('challenge_value')),
                    str(kpi.get('baseline_value')), kpi.get('scoring_rule'),
                    kpi.get('data_source'), '系统采集',
                    'kpi', kpi['id']
                ))
                
                items_created.append({
                    'type': 'kpi',
                    'id': kpi['id'],
                    'name': kpi['name']
                })
        
        # 获取战略关联的年度重点工作
        if include_annual_works:
            cursor.execute("""
                SELECT * FROM strategy_annual_works
                WHERE strategy_id = ?
            """, (strategy_id,))
            
            for work in cursor.fetchall():
                sort_order += 1
                cursor.execute("""
                    INSERT INTO performance_contract_items (
                        contract_id, sort_order, category, indicator_name,
                        indicator_description, weight, unit,
                        target_value, challenge_value, baseline_value,
                        scoring_rule, data_source, evaluation_method,
                        source_type, source_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract_id, sort_order, '管理指标', work['name'],
                    work.get('description'), 0, '进度%',
                    '100%', None, None, '按进度评分',
                    '项目管理系统', '进度同步',
                    'work', work['id']
                ))
                
                items_created.append({
                    'type': 'annual_work',
                    'id': work['id'],
                    'name': work['name']
                })
        
        # 更新合约的 strategy_id
        cursor.execute(
            "UPDATE performance_contracts SET strategy_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (strategy_id, contract_id)
        )
        
        # 重新计算总权重
        total_weight = calculate_total_weight(contract_id)
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = ? WHERE id = ?",
            (total_weight, contract_id)
        )
        
        conn.commit()
        
        return ResponseModel(
            code=200,
            message=f"生成成功，共创建{len(items_created)}个指标条目",
            data={
                "items_created": items_created,
                "total_items": sort_order,
                "total_weight": total_weight
            }
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")
    finally:
        conn.close()
