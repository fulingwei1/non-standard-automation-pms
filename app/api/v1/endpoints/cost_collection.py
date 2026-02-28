# -*- coding: utf-8 -*-
"""
成本自动归集 API
- 从采购订单自动归集材料成本到项目
- 从工单自动归集人工/加工成本到项目
- 归集日志和状态追踪
- 支持手动触发和自动归集
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()


def _collect_from_purchase_orders(db: Session, project_id: Optional[int] = None) -> dict:
    """从采购订单归集材料成本"""
    where_clause = "AND po.project_id = :pid" if project_id else ""
    params = {"pid": project_id} if project_id else {}

    # Find POs with project_id that haven't been collected yet
    sql = text(f"""
        SELECT po.id, po.order_no, po.project_id, po.total_amount, po.order_date,
               po.order_title, po.status
        FROM purchase_orders po
        WHERE po.project_id IS NOT NULL
          AND po.status IN ('RECEIVED', 'COMPLETED', 'SHIPPED')
          AND po.total_amount > 0
          AND NOT EXISTS (
            SELECT 1 FROM project_costs pc 
            WHERE pc.source_type = 'purchase_order' 
              AND pc.source_id = po.id
          )
          {where_clause}
    """)
    rows = db.execute(sql, params).fetchall()

    collected = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for po in rows:
        db.execute(text("""
            INSERT INTO project_costs 
            (project_id, cost_type, cost_category, source_module, source_type, source_id, 
             source_no, amount, cost_date, description, created_at, updated_at)
            VALUES (:project_id, 'material', 'purchase', 'procurement', 'purchase_order', :source_id,
                    :source_no, :amount, :cost_date, :desc, :now, :now)
        """), {
            "project_id": po.project_id,
            "source_id": po.id,
            "source_no": po.order_no,
            "amount": float(po.total_amount),
            "cost_date": po.order_date or now[:10],
            "desc": f"采购订单 {po.order_no}: {po.order_title or ''}",
            "now": now,
        })
        collected.append({
            "source": f"PO#{po.order_no}",
            "project_id": po.project_id,
            "amount": float(po.total_amount),
            "type": "material",
        })

    return {"source": "purchase_orders", "collected": len(collected), "items": collected}


def _collect_from_work_orders(db: Session, project_id: Optional[int] = None) -> dict:
    """从工单归集人工/加工成本"""
    where_clause = "AND wo.project_id = :pid" if project_id else ""
    params = {"pid": project_id} if project_id else {}

    sql = text(f"""
        SELECT wo.id, wo.work_order_no, wo.project_id, wo.task_type, wo.task_name,
               wo.status, wo.actual_hours, wo.standard_hours
        FROM work_order wo
        WHERE wo.project_id IS NOT NULL
          AND wo.status IN ('COMPLETED', 'IN_PROGRESS')
          AND NOT EXISTS (
            SELECT 1 FROM project_costs pc 
            WHERE pc.source_type = 'work_order'
              AND pc.source_id = wo.id
          )
          {where_clause}
    """)
    rows = db.execute(sql, params).fetchall()

    collected = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for wo in rows:
        # Estimate cost from hours (200 yuan/hour)
        hours = float(wo.actual_hours or wo.standard_hours or 0)
        if hours <= 0:
            continue  # Skip if no hours data
        total = hours * 200

        # Map task_type to cost_type
        cost_type = "labor"
        if wo.task_type in ("OUTSOURCE", "SUBCONTRACT"):
            cost_type = "outsource"

        db.execute(text("""
            INSERT INTO project_costs 
            (project_id, cost_type, cost_category, source_module, source_type, source_id,
             source_no, amount, cost_date, description, created_at, updated_at)
            VALUES (:project_id, :cost_type, :category, 'production', 'work_order', :source_id,
                    :source_no, :amount, :now_date, :desc, :now, :now)
        """), {
            "project_id": wo.project_id,
            "cost_type": cost_type,
            "category": wo.task_type or "production",
            "source_id": wo.id,
            "source_no": wo.work_order_no,
            "amount": total,
            "now_date": now[:10],
            "desc": f"工单 {wo.work_order_no}: {wo.task_name or ''}",
            "now": now,
        })
        collected.append({
            "source": f"WO#{wo.work_order_no}",
            "project_id": wo.project_id,
            "amount": total,
            "type": cost_type,
        })

    return {"source": "work_orders", "collected": len(collected), "items": collected}


@router.post("/collect", summary="执行成本归集")
def run_cost_collection(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: Optional[int] = Query(None, description="指定项目ID（空=全部）"),
) -> Any:
    """
    手动触发成本归集：
    1. 扫描所有有project_id的采购订单→归集为material成本
    2. 扫描所有有project_id的工单→归集为labor/outsource成本
    3. 跳过已归集的（通过source_type+source_id去重）
    """
    results = []

    po_result = _collect_from_purchase_orders(db, project_id)
    results.append(po_result)

    wo_result = _collect_from_work_orders(db, project_id)
    results.append(wo_result)

    db.commit()

    total = sum(r["collected"] for r in results)
    total_amount = sum(item["amount"] for r in results for item in r["items"])

    return {
        "message": f"成本归集完成：{total}条记录，合计¥{total_amount:,.2f}",
        "total_collected": total,
        "total_amount": round(total_amount, 2),
        "details": results,
    }


@router.get("/status", summary="归集状态概览")
def get_collection_status(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """查看各来源的归集状态。"""

    # PO stats
    po_sql = text("""
        SELECT 
            COUNT(*) as total_po,
            SUM(CASE WHEN EXISTS(SELECT 1 FROM project_costs pc WHERE pc.source_type='purchase_order' AND pc.source_id=po.id) THEN 1 ELSE 0 END) as collected,
            SUM(CASE WHEN NOT EXISTS(SELECT 1 FROM project_costs pc WHERE pc.source_type='purchase_order' AND pc.source_id=po.id) 
                      AND po.status IN ('RECEIVED','COMPLETED','SHIPPED') AND po.total_amount > 0 THEN 1 ELSE 0 END) as pending
        FROM purchase_orders po
        WHERE po.project_id IS NOT NULL
    """)
    po = db.execute(po_sql).fetchone()

    # WO stats
    wo_sql = text("""
        SELECT 
            COUNT(*) as total_wo,
            SUM(CASE WHEN EXISTS(SELECT 1 FROM project_costs pc WHERE pc.source_type='work_order' AND pc.source_id=wo.id) THEN 1 ELSE 0 END) as collected,
            SUM(CASE WHEN NOT EXISTS(SELECT 1 FROM project_costs pc WHERE pc.source_type='work_order' AND pc.source_id=wo.id)
                      AND wo.status IN ('COMPLETED','IN_PROGRESS') THEN 1 ELSE 0 END) as pending
        FROM work_order wo
        WHERE wo.project_id IS NOT NULL
    """)
    wo = db.execute(wo_sql).fetchone()

    # Recent collections
    recent_sql = text("""
        SELECT pc.source_type, pc.source_no, pc.amount, pc.cost_type, pc.created_at, p.project_name
        FROM project_costs pc
        JOIN projects p ON pc.project_id = p.id
        WHERE pc.source_type IN ('purchase_order', 'work_order')
        ORDER BY pc.created_at DESC LIMIT 10
    """)
    recent = [
        {
            "source_type": r.source_type,
            "source_no": r.source_no,
            "amount": float(r.amount),
            "cost_type": r.cost_type,
            "project_name": r.project_name,
            "collected_at": r.created_at,
        }
        for r in db.execute(recent_sql).fetchall()
    ]

    return {
        "purchase_orders": {
            "total": po.total_po,
            "collected": po.collected,
            "pending": po.pending,
        },
        "work_orders": {
            "total": wo.total_wo,
            "collected": wo.collected,
            "pending": wo.pending,
        },
        "recent_collections": recent,
    }


@router.get("/by-project", summary="按项目查看归集明细")
def get_collection_by_project(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """按项目汇总已归集的成本和来源。"""
    sql = text("""
        SELECT 
            p.id, p.project_name, p.project_code, p.contract_amount,
            COUNT(pc.id) as cost_records,
            SUM(pc.amount) as total_cost,
            SUM(CASE WHEN pc.source_type='purchase_order' THEN pc.amount ELSE 0 END) as po_cost,
            SUM(CASE WHEN pc.source_type='work_order' THEN pc.amount ELSE 0 END) as wo_cost,
            SUM(CASE WHEN pc.source_type IS NULL OR pc.source_type NOT IN ('purchase_order','work_order') THEN pc.amount ELSE 0 END) as manual_cost
        FROM projects p
        LEFT JOIN project_costs pc ON pc.project_id = p.id
        WHERE p.is_active = 1
        GROUP BY p.id
        HAVING cost_records > 0
        ORDER BY total_cost DESC
    """)
    rows = db.execute(sql).fetchall()

    return {
        "projects": [
            {
                "project_id": r.id,
                "project_name": r.project_name,
                "project_code": r.project_code,
                "contract_amount": float(r.contract_amount or 0),
                "total_cost": float(r.total_cost or 0),
                "po_cost": float(r.po_cost or 0),
                "wo_cost": float(r.wo_cost or 0),
                "manual_cost": float(r.manual_cost or 0),
                "cost_records": r.cost_records,
                "margin": round((float(r.contract_amount or 0) - float(r.total_cost or 0)) / float(r.contract_amount) * 100, 2) if r.contract_amount else 0,
            }
            for r in rows
        ]
    }
