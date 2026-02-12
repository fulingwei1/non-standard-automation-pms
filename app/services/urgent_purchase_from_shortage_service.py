# -*- coding: utf-8 -*-
"""
缺料预警自动触发紧急采购服务
当缺料预警级别为紧急（level3/level4 或 CRITICAL/URGENT）时，自动创建采购申请

使用统一的 AlertRecord 表，通过 target_type='SHORTAGE' 筛选缺料预警
缺料特定字段存储在 alert_data JSON 中
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.material import Material, MaterialSupplier
from app.models.purchase import PurchaseRequest, PurchaseRequestItem

logger = logging.getLogger(__name__)


def get_material_supplier(
    db: Session,
    material_id: int,
    project_id: Optional[int] = None
) -> Optional[int]:
    """
    获取物料的供应商ID

    优先级：
    1. 物料的首选供应商（is_preferred=True）
    2. 物料的默认供应商（default_supplier_id）
    3. 物料供应商关联表中的第一个活跃供应商

    Args:
        db: 数据库会话
        material_id: 物料ID
        project_id: 项目ID（可选，用于项目特定的供应商选择）

    Returns:
        供应商ID，如果找不到则返回None
    """
    # 1. 查找首选供应商
    preferred_supplier = (
        db.query(MaterialSupplier)
        .filter(
            MaterialSupplier.material_id == material_id,
            MaterialSupplier.is_preferred,
            MaterialSupplier.is_active
        )
        .first()
    )
    if preferred_supplier:
        return preferred_supplier.supplier_id

    # 2. 查找物料的默认供应商
    material = db.query(Material).filter(Material.id == material_id).first()
    if material and material.default_supplier_id:
        return material.default_supplier_id

    # 3. 查找物料供应商关联表中的第一个活跃供应商
    material_supplier = (
        db.query(MaterialSupplier)
        .filter(
            MaterialSupplier.material_id == material_id,
            MaterialSupplier.is_active
        )
        .first()
    )
    if material_supplier:
        return material_supplier.supplier_id

    return None


def get_material_price(
    db: Session,
    material_id: int,
    supplier_id: Optional[int] = None
) -> Decimal:
    """
    获取物料价格

    Args:
        db: 数据库会话
        material_id: 物料ID
        supplier_id: 供应商ID（可选）

    Returns:
        物料价格，如果找不到则返回0
    """
    # 如果指定了供应商，优先使用供应商价格
    if supplier_id:
        material_supplier = (
            db.query(MaterialSupplier)
            .filter(
                MaterialSupplier.material_id == material_id,
                MaterialSupplier.supplier_id == supplier_id,
                MaterialSupplier.is_active
            )
            .first()
        )
        if material_supplier and material_supplier.price:
            return material_supplier.price

    # 否则使用物料的最近采购价或标准价格
    material = db.query(Material).filter(Material.id == material_id).first()
    if material:
        if material.last_price and material.last_price > 0:
            return material.last_price
        if material.standard_price and material.standard_price > 0:
            return material.standard_price

    return Decimal(0)


def create_urgent_purchase_request_from_alert(
    db: Session,
    alert: "AlertRecord",
    current_user_id: int,
    generate_request_no_func
) -> Optional[PurchaseRequest]:
    """
    根据缺料预警自动创建紧急采购申请（使用统一 AlertRecord）

    Args:
        db: 数据库会话
        alert: 预警记录对象 (target_type='SHORTAGE')
        current_user_id: 当前用户ID（系统用户）
        generate_request_no_func: 生成申请单号的函数

    Returns:
        创建的采购申请对象，如果创建失败则返回None
    """
    import json

    try:
        # 从 alert_data JSON 提取缺料特定字段
        alert_data = {}
        if alert.alert_data:
            try:
                alert_data = json.loads(alert.alert_data) if isinstance(alert.alert_data, str) else alert.alert_data
            except (json.JSONDecodeError, TypeError):
                alert_data = {}

        material_id = alert.target_id  # 缺料预警的 target_id 存储物料ID
        material_code = alert.target_no or alert_data.get('material_code', '')
        material_name = alert.target_name or alert_data.get('material_name', '')
        shortage_qty = Decimal(str(alert_data.get('shortage_qty', 0)))
        required_date = alert_data.get('required_date')
        specification = alert_data.get('specification', '')
        impact_description = alert_data.get('impact_description', '')

        # 检查物料是否存在
        if not material_id:
            logger.warning(f"缺料预警 {alert.alert_no} 没有关联物料ID，无法创建采购申请")
            return None

        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            logger.warning(f"物料ID {material_id} 不存在，无法创建采购申请")
            return None

        # 查找供应商
        supplier_id = get_material_supplier(db, material_id, alert.project_id)
        if not supplier_id:
            logger.warning(
                f"物料 {material_code} 没有找到供应商，"
                f"无法自动创建采购申请。预警编号：{alert.alert_no}"
            )
            # 更新预警状态，标记为需要人工处理
            alert.status = 'PENDING'
            alert_data['handle_method'] = 'manual'
            alert_data['impact_description'] = (
                f"{impact_description}\n"
                f"【系统提示】物料未配置供应商，需要人工处理采购申请"
            )
            alert.alert_data = json.dumps(alert_data, ensure_ascii=False)
            db.commit()
            return None

        # 获取物料价格
        unit_price = get_material_price(db, material_id, supplier_id)

        # 生成申请单号
        request_no = generate_request_no_func(db)

        # 创建采购申请
        request = PurchaseRequest(
            request_no=request_no,
            project_id=alert.project_id,
            supplier_id=supplier_id,
            request_type='URGENT',  # 紧急采购
            source_type='SHORTAGE',  # 来源：缺料预警
            source_id=alert.id,
            request_reason=(
                f"缺料预警自动触发紧急采购\n"
                f"预警编号：{alert.alert_no}\n"
                f"物料：{material_name} ({material_code})\n"
                f"缺料数量：{shortage_qty}\n"
                f"需求日期：{required_date}\n"
                f"预警级别：{alert.alert_level}\n"
                f"影响描述：{impact_description or '无'}"
            ),
            required_date=required_date,
            status='DRAFT',  # 草稿状态，需要人工审核
            created_by=current_user_id,
        )
        db.add(request)
        db.flush()

        # 创建申请明细
        amount = shortage_qty * unit_price
        item = PurchaseRequestItem(
            request_id=request.id,
            material_id=material_id,
            material_code=material_code,
            material_name=material_name,
            specification=specification,
            unit=material.unit or '件',
            quantity=shortage_qty,
            unit_price=unit_price,
            amount=amount,
            required_date=required_date,
            remark=f"由缺料预警 {alert.alert_no} 自动生成",
        )
        db.add(item)

        # 更新申请总金额
        request.total_amount = amount

        # 更新预警状态
        alert.status = 'PROCESSING'
        alert.handle_start_at = datetime.now()
        alert_data['handle_method'] = 'urgent_purchase'
        alert_data['handle_plan'] = f"已自动创建紧急采购申请：{request_no}，等待审核"
        alert_data['related_po_no'] = request_no
        alert.alert_data = json.dumps(alert_data, ensure_ascii=False)

        db.commit()
        db.refresh(request)

        logger.info(
            f"成功为缺料预警 {alert.alert_no} 创建紧急采购申请 {request_no}，"
            f"物料：{material_code}，数量：{shortage_qty}，"
            f"供应商ID：{supplier_id}"
        )

        return request

    except Exception as e:
        logger.error(
            f"为缺料预警 {alert.alert_no} 创建紧急采购申请失败：{str(e)}",
            exc_info=True
        )
        db.rollback()
        return None


def auto_trigger_urgent_purchase_for_alerts(
    db: Session,
    alert_levels: List[str] = None,
    current_user_id: int = 1  # 默认系统用户ID
) -> Dict[str, Any]:
    """
    自动为紧急级别的缺料预警触发采购申请（使用统一 AlertRecord）

    Args:
        db: 数据库会话
        alert_levels: 需要自动触发的预警级别列表，默认['level3', 'level4', 'CRITICAL', 'URGENT']
        current_user_id: 当前用户ID（系统用户）

    Returns:
        处理结果统计
    """
    import json
    from app.models.alert import AlertRecord

    if alert_levels is None:
        alert_levels = ['level3', 'level4', 'CRITICAL', 'URGENT']

    from app.api.v1.endpoints.purchase import generate_request_no

    result = {
        'checked_count': 0,
        'created_count': 0,
        'skipped_count': 0,
        'failed_count': 0,
        'details': []
    }

    try:
        # 查询符合条件的缺料预警（使用统一 AlertRecord 表）
        alerts = (
            db.query(AlertRecord)
            .filter(
                AlertRecord.target_type == 'SHORTAGE',
                AlertRecord.alert_level.in_(alert_levels),
                AlertRecord.status.in_(['PENDING', 'PROCESSING', 'pending', 'handling']),
            )
            .all()
        )

        result['checked_count'] = len(alerts)

        for alert in alerts:
            # 从 alert_data 提取 related_po_no
            alert_data = {}
            if alert.alert_data:
                try:
                    alert_data = json.loads(alert.alert_data) if isinstance(alert.alert_data, str) else alert.alert_data
                except (json.JSONDecodeError, TypeError):
                    alert_data = {}

            related_po_no = alert_data.get('related_po_no', '')

            # 检查是否已经有采购申请
            if related_po_no and related_po_no.startswith('PR'):
                result['skipped_count'] += 1
                result['details'].append({
                    'alert_no': alert.alert_no,
                    'material_code': alert.target_no,
                    'status': 'skipped',
                    'reason': '已有采购申请'
                })
                continue

            # 创建采购申请
            request = create_urgent_purchase_request_from_alert(
                db=db,
                alert=alert,
                current_user_id=current_user_id,
                generate_request_no_func=generate_request_no
            )

            if request:
                result['created_count'] += 1
                result['details'].append({
                    'alert_no': alert.alert_no,
                    'material_code': alert.target_no,
                    'request_no': request.request_no,
                    'status': 'created'
                })
            else:
                result['failed_count'] += 1
                result['details'].append({
                    'alert_no': alert.alert_no,
                    'material_code': alert.target_no,
                    'status': 'failed',
                    'reason': '创建失败（可能缺少供应商）'
                })

        logger.info(
            f"缺料预警自动触发紧急采购完成："
            f"检查 {result['checked_count']} 个预警，"
            f"创建 {result['created_count']} 个采购申请，"
            f"跳过 {result['skipped_count']} 个，"
            f"失败 {result['failed_count']} 个"
        )

        return result

    except Exception as e:
        logger.error(f"缺料预警自动触发紧急采购失败：{str(e)}", exc_info=True)
        result['error'] = str(e)
        return result
