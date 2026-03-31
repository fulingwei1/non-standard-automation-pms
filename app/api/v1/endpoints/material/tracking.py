# -*- coding: utf-8 -*-
"""
物料进度跟踪 Phase 1 — BOM→采购联动

端点:
- POST /material/bom-to-purchase-request  BOM物料需求转采购申请
- GET  /material/purchase-order-tracking   采购订单进度跟踪
- POST /material/goods-received-notify     物料到货自动通知项目
"""

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.schemas.response import error_response, success_response
from app.dependencies import get_db
from app.models.inventory_tracking import MaterialStock
from app.models.material import BomHeader, BomItem, Material
from app.models.notification import Notification
from app.models.project import Project, ProjectStatusLog
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _decimal(v: Any, default: str = "0") -> Decimal:
    if v is None:
        return Decimal(default)
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal(default)


def _generate_request_no(db: Session) -> str:
    """生成采购申请编号 PR-YYYYMMDD-NNN"""
    from app.common.query_filters import apply_like_filter

    today = datetime.now().strftime("%Y%m%d")
    like_pattern = f"PR-{today}-%"
    q = db.query(PurchaseRequest.request_no)
    q = apply_like_filter(q, PurchaseRequest, like_pattern, "request_no", use_ilike=False)
    max_no = q.order_by(PurchaseRequest.request_no.desc()).first()
    if max_no and max_no[0]:
        try:
            seq = int(max_no[0].split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"PR-{today}-{seq:03d}"


def _get_available_stock(db: Session, material_id: int) -> Decimal:
    """查询某物料的总可用库存"""
    row = (
        db.query(func.coalesce(func.sum(MaterialStock.available_quantity), 0))
        .filter(MaterialStock.material_id == material_id)
        .scalar()
    )
    return _decimal(row)


# ---------------------------------------------------------------------------
# 1. BOM 物料需求转采购申请
# ---------------------------------------------------------------------------

@router.post("/bom-to-purchase-request")
def bom_to_purchase_request(
    project_id: int = Query(..., description="项目ID"),
    bom_ids: Optional[List[int]] = Query(None, description="指定BOM ID列表，为空则取项目全部已批准BOM"),
    group_by: Optional[str] = Query(None, description="分组方式: supplier / category"),
    db: Session = Depends(get_db),
):
    """
    根据项目 BOM 自动生成采购申请

    - 合并相同物料需求（多 BOM 汇总）
    - 扣减现有库存，计算净需求
    - 可按物料分类/供应商分组
    """

    # 1. 查询 BOM
    bom_query = db.query(BomHeader).filter(BomHeader.project_id == project_id)
    if bom_ids:
        bom_query = bom_query.filter(BomHeader.id.in_(bom_ids))
    else:
        # 默认只取已批准 & 最新版本
        bom_query = bom_query.filter(
            BomHeader.status == "APPROVED",
            BomHeader.is_latest.is_(True),
        )
    boms = bom_query.all()

    if not boms:
        return error_response("未找到符合条件的BOM", code=404)

    bom_id_list = [b.id for b in boms]

    # 2. 汇总 BOM 行项（只取需采购的）
    items = (
        db.query(BomItem)
        .filter(
            BomItem.bom_id.in_(bom_id_list),
            BomItem.source_type == "PURCHASE",
        )
        .all()
    )

    if not items:
        return error_response("BOM中没有需要采购的物料行", code=404)

    # 3. 按 material_id 合并需求
    merged: Dict[int, Dict[str, Any]] = {}
    for it in items:
        mid = it.material_id or 0
        if mid not in merged:
            merged[mid] = {
                "material_id": it.material_id,
                "material_code": it.material_code,
                "material_name": it.material_name,
                "specification": it.specification,
                "unit": it.unit,
                "supplier_id": it.supplier_id,
                "category_id": None,
                "total_qty": Decimal("0"),
                "purchased_qty": Decimal("0"),
                "unit_price": _decimal(it.unit_price),
                "required_date": it.required_date,
                "bom_item_ids": [],
            }
        merged[mid]["total_qty"] += _decimal(it.quantity)
        merged[mid]["purchased_qty"] += _decimal(it.purchased_qty)
        merged[mid]["bom_item_ids"].append(it.id)
        # 取最早需求日期
        if it.required_date and (
            merged[mid]["required_date"] is None or it.required_date < merged[mid]["required_date"]
        ):
            merged[mid]["required_date"] = it.required_date

    # 4. 补充物料分类信息
    material_ids = [mid for mid in merged if mid]
    if material_ids:
        materials = db.query(Material).filter(Material.id.in_(material_ids)).all()
        mat_map = {m.id: m for m in materials}
        for mid, info in merged.items():
            mat = mat_map.get(mid)
            if mat:
                info["category_id"] = mat.category_id
                # 如果 BOM 行没有供应商，取物料默认供应商
                if not info["supplier_id"] and mat.default_supplier_id:
                    info["supplier_id"] = mat.default_supplier_id

    # 5. 扣减库存，计算净需求
    request_lines: List[Dict[str, Any]] = []
    for mid, info in merged.items():
        gross = info["total_qty"] - info["purchased_qty"]
        if gross <= 0:
            continue
        stock = _get_available_stock(db, mid) if mid else Decimal("0")
        net = gross - stock
        if net <= 0:
            continue
        info["gross_qty"] = float(gross)
        info["available_stock"] = float(stock)
        info["net_qty"] = float(net)
        info["amount"] = float(net * info["unit_price"])
        request_lines.append(info)

    if not request_lines:
        return success_response(
            data={"message": "所有物料库存充足或已采购，无需生成采购申请", "items": []},
            message="无净需求",
        )

    # 6. 分组逻辑
    groups: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    if group_by == "supplier":
        for line in request_lines:
            groups[line.get("supplier_id")].append(line)
    elif group_by == "category":
        for line in request_lines:
            groups[line.get("category_id")].append(line)
    else:
        groups[None] = request_lines

    # 7. 生成采购申请
    created_requests = []
    for group_key, lines in groups.items():
        req = PurchaseRequest(
            request_no=_generate_request_no(db),
            project_id=project_id,
            request_type="NORMAL",
            source_type="BOM",
            request_reason=f"BOM自动生成 - 项目{project_id}",
            required_date=min((l["required_date"] for l in lines if l.get("required_date")), default=None),
            total_amount=sum(Decimal(str(l["amount"])) for l in lines),
            status="DRAFT",
        )
        if group_by == "supplier" and group_key:
            req.supplier_id = group_key

        db.add(req)
        db.flush()  # 获取 req.id

        for idx, line in enumerate(lines, 1):
            pri = PurchaseRequestItem(
                request_id=req.id,
                bom_item_id=line["bom_item_ids"][0] if line["bom_item_ids"] else None,
                material_id=line["material_id"],
                material_code=line["material_code"],
                material_name=line["material_name"],
                specification=line.get("specification"),
                unit=line.get("unit", "件"),
                quantity=Decimal(str(line["net_qty"])),
                unit_price=line["unit_price"],
                amount=Decimal(str(line["amount"])),
                required_date=line.get("required_date"),
            )
            db.add(pri)

        created_requests.append({
            "request_id": req.id,
            "request_no": req.request_no,
            "group_key": group_key,
            "item_count": len(lines),
            "total_amount": float(req.total_amount or 0),
            "items": [
                {
                    "material_code": l["material_code"],
                    "material_name": l["material_name"],
                    "gross_qty": l["gross_qty"],
                    "available_stock": l["available_stock"],
                    "net_qty": l["net_qty"],
                    "unit_price": float(l["unit_price"]),
                    "amount": l["amount"],
                }
                for l in lines
            ],
        })

    db.commit()

    return success_response(
        data={
            "project_id": project_id,
            "bom_count": len(boms),
            "bom_ids": bom_id_list,
            "group_by": group_by,
            "requests_created": len(created_requests),
            "requests": created_requests,
        },
        message=f"成功生成 {len(created_requests)} 个采购申请",
    )


# ---------------------------------------------------------------------------
# 2. 采购订单进度跟踪
# ---------------------------------------------------------------------------

@router.get("/purchase-order-tracking")
def purchase_order_tracking(
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    supplier_id: Optional[int] = Query(None, description="供应商ID筛选"),
    material_code: Optional[str] = Query(None, description="物料编码筛选"),
    status: Optional[str] = Query(None, description="订单状态筛选"),
    overdue_only: bool = Query(False, description="仅显示延期订单"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    采购订单进度跟踪

    - 订单状态跟踪（已下单/生产中/发货中/已到货）
    - 预计到货日期 vs 实际到货
    - 延期预警
    - 按项目/物料/供应商筛选
    """

    today = date.today()

    # 基础查询
    q = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.vendor),
    )

    if project_id is not None:
        q = q.filter(PurchaseOrder.project_id == project_id)
    if supplier_id is not None:
        q = q.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        q = q.filter(PurchaseOrder.status == status)

    # 如果按物料编码筛选，需 join order items
    if material_code:
        q = q.join(PurchaseOrderItem, PurchaseOrderItem.order_id == PurchaseOrder.id).filter(
            PurchaseOrderItem.material_code.contains(material_code)
        )

    # 延期筛选：promised_date 已过但未完成收货
    if overdue_only:
        q = q.filter(
            PurchaseOrder.promised_date < today,
            PurchaseOrder.status.notin_(["COMPLETED", "CANCELLED", "CLOSED"]),
        )

    total = q.count()
    orders = q.order_by(PurchaseOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 构建跟踪数据
    result_items = []
    for order in orders:
        # 查询该订单的收货汇总
        receipt_stats = (
            db.query(
                func.count(GoodsReceipt.id).label("receipt_count"),
                func.max(GoodsReceipt.receipt_date).label("last_receipt_date"),
            )
            .filter(GoodsReceipt.order_id == order.id)
            .first()
        )

        # 查询行项收货进度
        item_rows = (
            db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.order_id == order.id)
            .all()
        )

        total_qty = sum(_decimal(i.quantity) for i in item_rows)
        received_qty = sum(_decimal(i.received_qty) for i in item_rows)
        qualified_qty = sum(_decimal(i.qualified_qty) for i in item_rows)

        receive_rate = float(received_qty / total_qty * 100) if total_qty else 0
        is_overdue = bool(
            order.promised_date
            and order.promised_date < today
            and order.status not in ("COMPLETED", "CANCELLED", "CLOSED")
        )
        overdue_days = (today - order.promised_date).days if is_overdue else 0

        result_items.append({
            "order_id": order.id,
            "order_no": order.order_no,
            "order_title": order.order_title,
            "supplier_id": order.supplier_id,
            "supplier_name": order.vendor.vendor_name if order.vendor else None,
            "project_id": order.project_id,
            "status": order.status,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "required_date": order.required_date.isoformat() if order.required_date else None,
            "promised_date": order.promised_date.isoformat() if order.promised_date else None,
            "total_amount": float(order.total_amount or 0),
            # 收货进度
            "total_qty": float(total_qty),
            "received_qty": float(received_qty),
            "qualified_qty": float(qualified_qty),
            "receive_rate": round(receive_rate, 1),
            "receipt_count": receipt_stats.receipt_count if receipt_stats else 0,
            "last_receipt_date": (
                receipt_stats.last_receipt_date.isoformat()
                if receipt_stats and receipt_stats.last_receipt_date
                else None
            ),
            # 延期预警
            "is_overdue": is_overdue,
            "overdue_days": overdue_days,
            # 行项明细
            "items": [
                {
                    "item_id": i.id,
                    "material_code": i.material_code,
                    "material_name": i.material_name,
                    "specification": i.specification,
                    "quantity": float(i.quantity or 0),
                    "received_qty": float(i.received_qty or 0),
                    "qualified_qty": float(i.qualified_qty or 0),
                    "status": i.status,
                    "required_date": i.required_date.isoformat() if i.required_date else None,
                    "promised_date": i.promised_date.isoformat() if i.promised_date else None,
                }
                for i in item_rows
            ],
        })

    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return success_response(
        data={
            "items": result_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
            "summary": {
                "total_orders": total,
                "overdue_count": sum(1 for r in result_items if r["is_overdue"]),
            },
        },
        message="查询成功",
    )


# ---------------------------------------------------------------------------
# 3. 物料到货自动通知项目
# ---------------------------------------------------------------------------

@router.post("/goods-received-notify")
def goods_received_notify(
    receipt_id: int = Query(..., description="收货单 ID"),
    db: Session = Depends(get_db),
):
    """
    物料入库自动触发通知并同步项目齐套率

    功能:
    - 更新 BomItem 到货数量和齐套状态
    - 重算项目齐套率/物料状态/缺料项数
    - 齐套率变化时记录项目状态日志
    - 齐套率 < 90% 自动标记项目健康度为警告 (H2)
    - 通知项目经理/采购员/计划员
    """

    # 1. 查询收货单
    receipt = (
        db.query(GoodsReceipt)
        .options(joinedload(GoodsReceipt.order))
        .filter(GoodsReceipt.id == receipt_id)
        .first()
    )
    if not receipt:
        return error_response("收货单不存在", code=404)

    order = receipt.order
    if not order:
        return error_response("关联采购订单不存在", code=404)

    # 2. 查询收货明细
    receipt_items = db.query(GoodsReceiptItem).filter(GoodsReceiptItem.receipt_id == receipt_id).all()
    if not receipt_items:
        return error_response("收货单无明细行", code=404)

    # 3. 更新 BomItem 到货数量 & 实际到货日期
    updated_bom_count = 0
    for ri in receipt_items:
        if not ri.order_item_id:
            continue
        oi = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == ri.order_item_id).first()
        if not oi or not oi.bom_item_id:
            continue
        bom_item = db.query(BomItem).filter(BomItem.id == oi.bom_item_id).first()
        if not bom_item:
            continue
        bom_item.received_qty = _decimal(bom_item.received_qty) + _decimal(ri.qualified_qty)
        bom_item.actual_arrival_date = date.today()
        updated_bom_count += 1

    # 4. 计算项目物料齐套率（如果有项目）
    kitting_info = None
    project = None
    old_kitting_rate = 0
    old_health = None
    
    if order.project_id:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        if project:
            old_kitting_rate = float(project.kitting_rate or 0)
            old_health = project.health
            
            project_bom_items = (
                db.query(BomItem)
                .join(BomHeader, BomItem.bom_id == BomHeader.id)
                .filter(
                    BomHeader.project_id == order.project_id,
                    BomItem.source_type == "PURCHASE",
                )
                .all()
            )
            total_lines = len(project_bom_items)
            complete_lines = sum(
                1 for b in project_bom_items if _decimal(b.received_qty) >= _decimal(b.quantity)
            )
            kitting_rate = round(complete_lines / total_lines * 100, 1) if total_lines else 0
            
            # 判断是否有采购中的物料
            has_purchased = (
                db.query(BomItem.id)
                .join(BomHeader, BomItem.bom_id == BomHeader.id)
                .filter(
                    BomHeader.project_id == order.project_id,
                    BomItem.purchased_qty > 0,
                )
                .first()
                is not None
            )
            
            # 更新项目齐套率相关字段
            project.kitting_rate = kitting_rate
            project.shortage_items_count = total_lines - complete_lines
            
            # 推导物料状态
            if kitting_rate >= 100:
                project.material_status = "COMPLETE"
            elif kitting_rate >= 95:
                project.material_status = "PARTIAL_ARRIVAL"
            elif kitting_rate >= 90:
                project.material_status = "IN_PROGRESS"
            elif kitting_rate > 0:
                project.material_status = "IN_PROGRESS"
            else:
                project.material_status = "PENDING"
            
            # 齐套率 < 90% → 项目健康度警告
            new_health = old_health
            if kitting_rate < 90 and project.health == "H1":
                project.health = "H2"
                new_health = "H2"
            elif kitting_rate >= 100 and project.health == "H2":
                project.health = "H1"
                new_health = "H1"
            
            # 齐套率变化时记录日志
            rate_changed = abs(kitting_rate - old_kitting_rate) > 0.05
            health_changed = new_health != old_health
            if rate_changed or health_changed:
                log = ProjectStatusLog(
                    project_id=project.id,
                    old_health=old_health,
                    new_health=new_health,
                    change_type="HEALTH_CHANGE" if health_changed else "STATUS_CHANGE",
                    change_reason=f"物料到货更新齐套率：{old_kitting_rate}% → {kitting_rate}%",
                    change_note=f"收货单：{receipt.receipt_no}",
                    changed_at=datetime.now(),
                )
                db.add(log)
            
            kitting_info = {
                "project_id": order.project_id,
                "total_material_lines": total_lines,
                "complete_lines": complete_lines,
                "kitting_rate": kitting_rate,
                "is_complete": kitting_rate >= 100,
                "old_kitting_rate": old_kitting_rate,
                "old_health": old_health,
                "new_health": new_health,
            }

    # 5. 生成通知记录
    notify_users = set()
    # 采购订单创建人
    if order.created_by:
        notify_users.add(order.created_by)
    # 来源采购申请的申请人
    if order.source_request_id:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == order.source_request_id).first()
        if pr and pr.requested_by:
            notify_users.add(pr.requested_by)
        if pr and pr.created_by:
            notify_users.add(pr.created_by)
    # 项目经理
    if project and project.pm_id:
        notify_users.add(project.pm_id)

    material_summary = ", ".join(
        f"{ri.material_name}×{float(ri.received_qty or 0)}" for ri in receipt_items[:5]
    )
    if len(receipt_items) > 5:
        material_summary += f" 等{len(receipt_items)}项"

    notifications_created = []
    for uid in notify_users:
        notif = Notification(
            user_id=uid,
            notification_type="GOODS_RECEIVED",
            source_type="goods_receipt",
            source_id=receipt_id,
            title=f"物料到货通知 - {receipt.receipt_no}",
            content=(
                f"收货单 {receipt.receipt_no} 已入库。"
                f"订单：{order.order_no}。"
                f"物料：{material_summary}。"
                + (f"项目齐套率：{kitting_info['kitting_rate']}%" if kitting_info else "")
            ),
            priority="HIGH" if (kitting_info and kitting_info["is_complete"]) else "NORMAL",
            extra_data={
                "receipt_id": receipt_id,
                "receipt_no": receipt.receipt_no,
                "order_id": order.id,
                "order_no": order.order_no,
                "project_id": order.project_id,
                "kitting_info": kitting_info,
            },
        )
        db.add(notif)
        notifications_created.append(uid)

    db.commit()

    return success_response(
        data={
            "receipt_id": receipt_id,
            "receipt_no": receipt.receipt_no,
            "order_no": order.order_no,
            "items_processed": len(receipt_items),
            "bom_items_updated": updated_bom_count,
            "kitting_info": kitting_info,
            "notifications_sent": len(notifications_created),
        },
        message=f"物料到货已处理：{len(receipt_items)}项物料，更新{updated_bom_count}个 BOM 行",
    )

