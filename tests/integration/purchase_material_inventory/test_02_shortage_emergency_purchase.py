# -*- coding: utf-8 -*-
"""
场景2: 缺料预警触发紧急采购测试
缺料扫描 → 生成预警 → 采购建议 → 紧急采购订单
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.shortage.smart_alert import ShortageAlert
from app.models.purchase import PurchaseRequest, PurchaseRequestItem, PurchaseOrder


class TestShortageEmergencyPurchase:
    """缺料预警触发紧急采购集成测试"""
    
    def test_low_stock_alert_and_emergency_purchase(self, integration_test_data):
        """测试低库存预警并触发紧急采购"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        suppliers = integration_test_data["suppliers"]
        project = integration_test_data["project"]
        user = integration_test_data["user"]
        
        # 获取库存不足的物料
        material_m001 = materials[0]  # 当前库存30, 安全库存50
        material_m002 = materials[1]  # 当前库存180, 安全库存200
        
        # 步骤1: 扫描库存，生成缺料预警
        shortage_alerts = []
        
        for idx, material in enumerate([material_m001, material_m002]):
            if material.current_stock < material.safety_stock:
                shortage_qty = material.safety_stock - material.current_stock
                
                alert = ShortageAlert(
                    alert_no=f"ALERT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{idx}_{material.material_code}",
                    material_id=material.id,
                    material_code=material.material_code,
                    material_name=material.material_name,
                    project_id=project.id,
                    required_qty=material.safety_stock,
                    shortage_qty=shortage_qty,
                    alert_level="WARNING" if material.is_key_material else "INFO",
                    required_date=(datetime.utcnow() + timedelta(days=material.lead_time_days)).date(),
                    status="PENDING",
                    remark=f"{material.material_name}库存低于安全库存"
                )
                db.add(alert)
                shortage_alerts.append(alert)
        
        db.commit()
        
        assert len(shortage_alerts) == 2, "应该生成2条缺料预警"
        
        # 步骤2: 根据预警生成采购建议
        for alert in shortage_alerts:
            material = db.query(Material).get(alert.material_id)
            
            # 计算采购数量（补足到安全库存 + 考虑最小订购量）
            suggested_qty = alert.shortage_qty
            if suggested_qty < material.min_order_qty:
                suggested_qty = material.min_order_qty
            
            # 步骤3: 创建紧急采购申请
            purchase_request = PurchaseRequest(
                request_no=f"PR_EMERGENCY_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{material.material_code}",
                request_type="SHORTAGE",
                project_id=project.id,
                status="DRAFT",
                created_by=user.id,
                remark=f"缺料预警自动生成 - {alert.remark}"
            )
            db.add(purchase_request)
            db.flush()
            
            request_item = PurchaseRequestItem(
                request_id=purchase_request.id,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                unit=material.unit,
                quantity=suggested_qty,
                required_date=alert.required_date,
                remark=f"补充安全库存 - 紧急度: {'URGENT' if material.is_key_material else 'HIGH'}"
            )
            db.add(request_item)
            
            # 自动审批（紧急情况）
            purchase_request.status = "APPROVED"
            purchase_request.submitted_at = datetime.utcnow()
            purchase_request.approved_by = user.id
            purchase_request.approved_at = datetime.utcnow()
            
            # 步骤4: 直接创建紧急采购订单
            purchase_order = PurchaseOrder(
                order_no=f"PO_URGENT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{material.material_code}",
                supplier_id=material.default_supplier_id or suppliers[0].id,
                project_id=project.id,
                source_request_id=purchase_request.id,
                order_type="URGENT",  # 标记为紧急订单
                order_title=f"紧急采购 - {material.material_name}",
                order_date=datetime.utcnow().date(),
                required_date=(datetime.utcnow() + timedelta(days=material.lead_time_days // 2)).date(),  # 缩短交期
                status="SENT",  # 直接发送给供应商
                created_by=user.id,
                approved_by=user.id,
                approved_at=datetime.utcnow()
            )
            db.add(purchase_order)
            db.flush()
            
            # 关联预警 - 更新状态为处理中
            alert.status = "PROCESSING"
            alert.resolution_note = f"已创建紧急采购订单: {purchase_order.order_no}"
            
            print(f"✅ 缺料预警处理完成:")
            print(f"   物料: {material.material_name}")
            print(f"   缺料数量: {alert.shortage_qty}")
            print(f"   采购数量: {suggested_qty}")
            print(f"   采购订单: {purchase_order.order_no}")
            print(f"   预计交期: {purchase_order.required_date}")
        
        db.commit()
        
        # 验证结果
        processing_alerts = db.query(ShortageAlert).filter(
            ShortageAlert.status == "PROCESSING"
        ).count()
        
        assert processing_alerts == 2, "所有预警应处于处理中状态"
        
        print(f"\n✅ 缺料预警触发紧急采购流程测试通过")
        print(f"   生成预警: {len(shortage_alerts)}条")
        print(f"   创建采购订单: {len(shortage_alerts)}个")
    
    def test_critical_shortage_alert_level(self, integration_test_data):
        """测试关键物料缺料预警级别"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        project = integration_test_data["project"]
        
        material_m001 = materials[0]  # 关键物料
        
        # 创建严重缺料预警
        alert = ShortageAlert(
            alert_no=f"ALERT_CRITICAL_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            material_id=material_m001.id,
            material_code=material_m001.material_code,
            material_name=material_m001.material_name,
            project_id=project.id,
            required_qty=Decimal("100"),
            shortage_qty=Decimal("100"),  # 严重缺料
            alert_level="CRITICAL",
            required_date=datetime.utcnow().date(),  # 今天就需要
            status="PENDING",
            remark="关键物料严重缺料",
            is_critical_path=True
        )
        db.add(alert)
        db.commit()
        
        assert alert.alert_level == "CRITICAL"
        assert alert.status == "PENDING"
        assert alert.is_critical_path == True
        
        print(f"✅ 关键物料缺料预警级别测试通过")
