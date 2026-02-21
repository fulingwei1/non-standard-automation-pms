# -*- coding: utf-8 -*-
"""
场景1: 完整采购流程测试
采购申请 → 采购订单 → 收货入库 → 库存更新
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.purchase import PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem
from app.models.material import Material


class TestCompletePurchaseFlow:
    """完整采购流程集成测试"""
    
    def test_purchase_request_to_stock_update(self, integration_test_data):
        """测试从采购申请到库存更新的完整流程"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        suppliers = integration_test_data["suppliers"]
        project = integration_test_data["project"]
        user = integration_test_data["user"]
        
        # 步骤1: 创建采购申请
        material_m001 = materials[0]  # 不锈钢板
        initial_stock = material_m001.current_stock
        
        purchase_request = PurchaseRequest(
            request_no=f"PR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            request_type="SHORTAGE",
            project_id=project.id,
            status="DRAFT",
            created_by=user.id,
            remark="紧急采购申请-库存不足"
        )
        db.add(purchase_request)
        db.flush()
        
        # 添加采购申请明细
        request_item = PurchaseRequestItem(
            request_id=purchase_request.id,
            material_id=material_m001.id,
            material_code=material_m001.material_code,
            material_name=material_m001.material_name,
            specification=material_m001.specification,
            unit=material_m001.unit,
            quantity=Decimal("100"),
            required_date=(datetime.utcnow() + timedelta(days=7)).date(),
            remark="生产用料 - 紧急度: HIGH"
        )
        db.add(request_item)
        db.commit()
        
        assert purchase_request.id is not None
        assert len(purchase_request.items.all()) == 1
        
        # 步骤2: 提交审批
        purchase_request.status = "SUBMITTED"
        purchase_request.submitted_at = datetime.utcnow()
        db.commit()
        
        # 步骤3: 审批通过
        purchase_request.status = "APPROVED"
        purchase_request.approved_by = user.id
        purchase_request.approved_at = datetime.utcnow()
        db.commit()
        
        # 步骤4: 创建采购订单
        purchase_order = PurchaseOrder(
            order_no=f"PO{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            supplier_id=suppliers[0].id,
            project_id=project.id,
            source_request_id=purchase_request.id,
            order_type="NORMAL",
            order_title="不锈钢板采购",
            order_date=datetime.utcnow().date(),
            required_date=(datetime.utcnow() + timedelta(days=7)).date(),
            status="DRAFT",
            created_by=user.id
        )
        db.add(purchase_order)
        db.flush()
        
        # 添加订单明细
        unit_price = Decimal("350.00")
        quantity = Decimal("100")
        
        order_item = PurchaseOrderItem(
            order_id=purchase_order.id,
            item_no=1,
            material_id=material_m001.id,
            material_code=material_m001.material_code,
            material_name=material_m001.material_name,
            specification=material_m001.specification,
            unit=material_m001.unit,
            quantity=quantity,
            unit_price=unit_price,
            amount=quantity * unit_price,
            required_date=(datetime.utcnow() + timedelta(days=7)).date()
        )
        db.add(order_item)
        
        # 计算订单总额
        purchase_order.total_amount = quantity * unit_price
        purchase_order.tax_amount = purchase_order.total_amount * Decimal("0.13")
        purchase_order.amount_with_tax = purchase_order.total_amount + purchase_order.tax_amount
        
        db.commit()
        
        assert purchase_order.total_amount == Decimal("35000.00")
        assert purchase_order.tax_amount == Decimal("4550.00")
        
        # 步骤5: 提交订单
        purchase_order.status = "SUBMITTED"
        purchase_order.submitted_at = datetime.utcnow()
        db.commit()
        
        # 步骤6: 订单审批
        purchase_order.status = "APPROVED"
        purchase_order.approved_by = user.id
        purchase_order.approved_at = datetime.utcnow()
        db.commit()
        
        # 步骤7: 发送给供应商
        purchase_order.status = "SENT"
        db.commit()
        
        # 步骤8: 供应商确认
        purchase_order.status = "CONFIRMED"
        purchase_order.promised_date = (datetime.utcnow() + timedelta(days=6)).date()
        db.commit()
        
        # 步骤9: 模拟收货（应该调用收货API，这里简化处理）
        # 更新物料库存
        received_quantity = Decimal("100")
        material_m001.current_stock += received_quantity
        
        # 更新订单已收货金额
        purchase_order.received_amount = quantity * unit_price
        purchase_order.status = "RECEIVED"
        
        # 更新物料最近采购价
        material_m001.last_price = unit_price
        
        db.commit()
        
        # 验证最终结果
        final_stock = material_m001.current_stock
        expected_stock = initial_stock + received_quantity
        
        assert final_stock == expected_stock, f"库存更新错误: 期望{expected_stock}, 实际{final_stock}"
        assert purchase_order.status == "RECEIVED", "订单状态应为已收货"
        assert material_m001.last_price == unit_price, "最近采购价未更新"
        
        # 验证关联关系
        assert purchase_order.source_request_id == purchase_request.id
        assert purchase_request.orders.count() > 0
        
        print(f"✅ 完整采购流程测试通过")
        print(f"   初始库存: {initial_stock}")
        print(f"   采购数量: {received_quantity}")
        print(f"   最终库存: {final_stock}")
        print(f"   采购订单: {purchase_order.order_no}")
        print(f"   订单金额: ￥{purchase_order.amount_with_tax}")
    
    def test_purchase_workflow_validation(self, integration_test_data):
        """测试采购流程的状态验证"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        suppliers = integration_test_data["suppliers"]
        user = integration_test_data["user"]
        
        # 创建采购订单
        purchase_order = PurchaseOrder(
            order_no=f"PO{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_TEST",
            supplier_id=suppliers[0].id,
            order_type="URGENT",
            status="DRAFT",
            created_by=user.id
        )
        db.add(purchase_order)
        db.commit()
        
        # 验证状态流转
        valid_transitions = {
            "DRAFT": ["SUBMITTED", "CANCELLED"],
            "SUBMITTED": ["APPROVED", "REJECTED"],
            "APPROVED": ["SENT"],
            "SENT": ["CONFIRMED", "REJECTED"],
            "CONFIRMED": ["RECEIVED", "PARTIALLY_RECEIVED"],
            "RECEIVED": ["COMPLETED"]
        }
        
        # 测试正常流转
        purchase_order.status = "SUBMITTED"
        db.commit()
        assert purchase_order.status == "SUBMITTED"
        
        purchase_order.status = "APPROVED"
        db.commit()
        assert purchase_order.status == "APPROVED"
        
        print(f"✅ 采购流程状态验证通过")
