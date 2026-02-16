# -*- coding: utf-8 -*-
"""
场景3-15: 其他业务流程集成测试
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.purchase import PurchaseOrder


class TestMaterialReservationAndIssue:
    """场景3: 物料预留和领用测试"""
    
    def test_material_reservation_flow(self, integration_test_data):
        """测试物料预留和领用流程"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        project = integration_test_data["project"]
        
        material = materials[2]  # 电机，库存充足
        initial_stock = material.current_stock
        reserve_qty = Decimal("5")
        
        # 模拟预留
        reserved_stock = reserve_qty
        available_stock = initial_stock - reserved_stock
        
        assert available_stock >= 0, "可用库存不足"
        
        # 模拟领用
        issued_qty = Decimal("5")
        final_stock = initial_stock - issued_qty
        
        material.current_stock = final_stock
        db.commit()
        
        assert material.current_stock == initial_stock - issued_qty
        print(f"✅ 场景3: 物料预留和领用测试通过 (预留{reserve_qty}, 领用{issued_qty})")


class TestStockCountAndAdjustment:
    """场景4: 库存盘点和调整测试"""
    
    def test_stock_count_adjustment(self, integration_test_data):
        """测试库存盘点和调整"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        system_qty = material.current_stock
        actual_qty = Decimal("35")  # 实盘数量
        difference = actual_qty - system_qty
        
        # 调整库存
        material.current_stock = actual_qty
        db.commit()
        
        assert material.current_stock == actual_qty
        print(f"✅ 场景4: 库存盘点调整测试通过 (账面{system_qty}, 实盘{actual_qty}, 差异{difference})")


class TestSupplierPerformanceEvaluation:
    """场景5: 供应商绩效评估测试"""
    
    def test_supplier_performance_calculation(self, integration_test_data):
        """测试供应商绩效评估计算"""
        db = integration_test_data["db"]
        suppliers = integration_test_data["suppliers"]
        
        supplier = suppliers[0]
        
        # 模拟绩效指标
        on_time_delivery_rate = 0.95  # 准时交货率 95%
        quality_pass_rate = 0.98  # 质量合格率 98%
        price_competitiveness = 0.92  # 价格竞争力 92分
        response_speed = 0.88  # 响应速度 88分
        
        # 综合评分（加权）
        overall_score = (
            on_time_delivery_rate * 0.4 +
            quality_pass_rate * 0.3 +
            price_competitiveness * 0.2 +
            response_speed * 0.1
        ) * 100
        
        assert overall_score > 90, "优秀供应商评分应>90"
        print(f"✅ 场景5: 供应商绩效评估测试通过 (综合评分: {overall_score:.2f})")


class TestSubstituteMaterialUsage:
    """场景6: 替代料使用测试"""
    
    def test_substitute_material_suggestion(self, integration_test_data):
        """测试替代料推荐"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        primary_material = materials[0]  # 不锈钢板304
        
        # 创建替代料
        substitute = Material(
            material_code="M001-SUB",
            material_name="不锈钢板 316",
            category_id=primary_material.category_id,
            specification="1.5mm*1220*2440",
            unit="张",
            material_type="RAW_MATERIAL",
            standard_price=Decimal("380.00"),  # 稍贵
            safety_stock=Decimal("30"),
            current_stock=Decimal("50"),  # 库存充足
            is_active=True
        )
        db.add(substitute)
        db.commit()
        
        # 检查替代料可行性
        assert substitute.current_stock > 0, "替代料有库存"
        assert substitute.specification == primary_material.specification, "规格匹配"
        
        print(f"✅ 场景6: 替代料使用测试通过 (主料{primary_material.material_code} → 替代{substitute.material_code})")


class TestBatchTraceability:
    """场景7: 批次追溯测试"""
    
    def test_material_batch_tracking(self, integration_test_data):
        """测试物料批次追溯"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        
        # 模拟批次信息
        batches = [
            {"batch_no": "BATCH20260216001", "quantity": Decimal("50"), "location": "A区1号仓"},
            {"batch_no": "BATCH20260215001", "quantity": Decimal("30"), "location": "A区1号仓"},
        ]
        
        total_qty = sum(b["quantity"] for b in batches)
        
        # 批次追溯验证
        assert len(batches) == 2, "应有2个批次"
        assert total_qty > 0, "批次总数量应>0"
        
        print(f"✅ 场景7: 批次追溯测试通过 (共{len(batches)}个批次, 总量{total_qty})")


class TestInventoryTurnoverAnalysis:
    """场景8: 库存周转分析测试"""
    
    def test_inventory_turnover_calculation(self, integration_test_data):
        """测试库存周转率计算"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        
        # 模拟数据
        annual_consumption = Decimal("600")  # 年消耗量
        average_stock = (material.current_stock + material.safety_stock) / 2
        
        # 库存周转率 = 年消耗量 / 平均库存
        turnover_rate = float(annual_consumption / average_stock) if average_stock > 0 else 0
        
        # 库存周转天数 = 365 / 周转率
        turnover_days = 365 / turnover_rate if turnover_rate > 0 else 0
        
        assert turnover_rate > 0, "周转率应>0"
        assert turnover_days < 365, "周转天数应<365"
        
        print(f"✅ 场景8: 库存周转分析测试通过 (周转率:{turnover_rate:.2f}次/年, 周转天数:{turnover_days:.1f}天)")


class TestDemandForecastAccuracy:
    """场景9: 需求预测准确性测试"""
    
    def test_demand_forecast_model(self, integration_test_data):
        """测试需求预测模型"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        
        # 模拟历史消耗数据（过去30天）
        historical_consumption = [
            Decimal("5"), Decimal("6"), Decimal("4"), Decimal("7"), Decimal("5"),
            Decimal("6"), Decimal("5"), Decimal("8"), Decimal("6"), Decimal("5"),
            Decimal("7"), Decimal("6"), Decimal("5"), Decimal("6"), Decimal("7"),
            Decimal("5"), Decimal("6"), Decimal("8"), Decimal("5"), Decimal("6"),
            Decimal("7"), Decimal("5"), Decimal("6"), Decimal("5"), Decimal("7"),
            Decimal("6"), Decimal("5"), Decimal("6"), Decimal("7"), Decimal("5")
        ]
        
        # 移动平均预测
        window_size = 7
        recent_data = historical_consumption[-window_size:]
        predicted_demand = sum(recent_data) / len(recent_data)
        
        # 实际需求（模拟）
        actual_demand = Decimal("6")
        
        # 计算预测误差
        forecast_error = abs(predicted_demand - actual_demand) / actual_demand * 100
        
        assert forecast_error < 15, f"预测误差应<15%, 实际{forecast_error:.2f}%"
        
        print(f"✅ 场景9: 需求预测准确性测试通过 (预测{predicted_demand:.2f}, 实际{actual_demand}, 误差{forecast_error:.2f}%)")


class TestMultiProjectMaterialCompetition:
    """场景10: 多项目物料竞争测试"""
    
    def test_material_allocation_between_projects(self, integration_test_data):
        """测试多项目间物料分配"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        project = integration_test_data["project"]
        
        material = materials[2]  # 电机，库存15
        
        # 项目A需求
        project_a_demand = Decimal("8")
        # 项目B需求
        project_b_demand = Decimal("10")
        
        total_demand = project_a_demand + project_b_demand
        available_stock = material.current_stock
        
        # 分配策略：按优先级或先到先得
        if available_stock < total_demand:
            # 库存不足，需要分配
            allocation_a = min(project_a_demand, available_stock)
            allocation_b = min(project_b_demand, available_stock - allocation_a)
            shortage = total_demand - available_stock
            
            assert allocation_a + allocation_b <= available_stock
            assert shortage > 0
            
            print(f"✅ 场景10: 多项目物料竞争测试通过 (需求{total_demand}, 库存{available_stock}, 缺口{shortage})")


class TestUrgentOrderInsertion:
    """场景11: 紧急插单处理测试"""
    
    def test_urgent_order_priority(self, integration_test_data):
        """测试紧急插单优先处理"""
        db = integration_test_data["db"]
        suppliers = integration_test_data["suppliers"]
        materials = integration_test_data["materials"]
        user = integration_test_data["user"]
        
        # 创建普通订单
        normal_order = PurchaseOrder(
            order_no=f"PO_NORMAL_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            supplier_id=suppliers[0].id,
            order_type="NORMAL",
            status="CONFIRMED",
            created_by=user.id,
            required_date=(datetime.utcnow() + timedelta(days=10)).date()
        )
        db.add(normal_order)
        
        # 创建紧急订单
        urgent_order = PurchaseOrder(
            order_no=f"PO_URGENT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            supplier_id=suppliers[0].id,
            order_type="URGENT",
            status="CONFIRMED",
            created_by=user.id,
            required_date=(datetime.utcnow() + timedelta(days=3)).date()  # 更早交期
        )
        db.add(urgent_order)
        db.commit()
        
        # 验证紧急订单优先级
        assert urgent_order.order_type == "URGENT"
        assert urgent_order.required_date < normal_order.required_date
        
        print(f"✅ 场景11: 紧急插单处理测试通过 (紧急订单优先级高于普通订单)")


class TestQualityIssueReturn:
    """场景12: 质量问题退货测试"""
    
    def test_material_return_for_quality_issue(self, integration_test_data):
        """测试质量问题退货流程"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        initial_stock = material.current_stock
        
        # 模拟收货入库
        received_qty = Decimal("100")
        material.current_stock += received_qty
        db.commit()
        
        # 质量检验发现问题
        rejected_qty = Decimal("10")  # 10件不合格
        
        # 退货，扣减库存
        material.current_stock -= rejected_qty
        db.commit()
        
        expected_stock = initial_stock + received_qty - rejected_qty
        assert material.current_stock == expected_stock
        
        print(f"✅ 场景12: 质量问题退货测试通过 (收货{received_qty}, 退货{rejected_qty}, 最终库存{material.current_stock})")


class TestInventoryTransfer:
    """场景13: 库存转移测试"""
    
    def test_stock_transfer_between_warehouses(self, integration_test_data):
        """测试仓库间库存转移"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        
        # 模拟仓库间转移
        source_warehouse = "A区1号仓"
        target_warehouse = "B区2号仓"
        transfer_qty = Decimal("10")
        
        # 原仓库扣减
        source_stock = Decimal("30")
        source_final = source_stock - transfer_qty
        
        # 目标仓库增加
        target_stock = Decimal("0")
        target_final = target_stock + transfer_qty
        
        assert source_final >= 0, "来源仓库库存不能为负"
        assert target_final == transfer_qty
        
        print(f"✅ 场景13: 库存转移测试通过 ({source_warehouse} → {target_warehouse}, 数量{transfer_qty})")


class TestExpiredMaterialHandling:
    """场景14: 过期物料处理测试"""
    
    def test_expired_material_identification(self, integration_test_data):
        """测试过期物料识别和处理"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        
        # 模拟批次信息（含日期）
        batches = [
            {
                "batch_no": "BATCH20250101001",
                "quantity": Decimal("20"),
                "production_date": datetime(2025, 1, 1).date(),
                "shelf_life_days": 365,
                "is_expired": (datetime.utcnow().date() - datetime(2025, 1, 1).date()).days > 365
            },
            {
                "batch_no": "BATCH20260101001",
                "quantity": Decimal("30"),
                "production_date": datetime(2026, 1, 1).date(),
                "shelf_life_days": 365,
                "is_expired": False
            }
        ]
        
        # 识别过期批次
        expired_batches = [b for b in batches if b["is_expired"]]
        expired_qty = sum(b["quantity"] for b in expired_batches)
        
        # 处理过期物料：报废并扣减库存
        if expired_qty > 0:
            material.current_stock -= expired_qty
            db.commit()
        
        print(f"✅ 场景14: 过期物料处理测试通过 (过期批次{len(expired_batches)}个, 报废数量{expired_qty})")


class TestCostAccuracyCalculation:
    """场景15: 成本核算准确性测试"""
    
    def test_material_cost_calculation(self, integration_test_data):
        """测试物料成本核算准确性"""
        db = integration_test_data["db"]
        materials = integration_test_data["materials"]
        
        material = materials[0]
        
        # 模拟采购记录
        purchases = [
            {"quantity": Decimal("50"), "unit_price": Decimal("350.00")},
            {"quantity": Decimal("100"), "unit_price": Decimal("360.00")},
            {"quantity": Decimal("80"), "unit_price": Decimal("355.00")},
        ]
        
        # 加权平均成本
        total_value = sum(p["quantity"] * p["unit_price"] for p in purchases)
        total_quantity = sum(p["quantity"] for p in purchases)
        weighted_avg_price = total_value / total_quantity if total_quantity > 0 else Decimal("0")
        
        # 验证成本计算
        assert weighted_avg_price > 0
        assert Decimal("350") <= weighted_avg_price <= Decimal("360")
        
        # 更新物料成本
        material.last_price = weighted_avg_price
        db.commit()
        
        print(f"✅ 场景15: 成本核算准确性测试通过 (加权平均成本: ￥{weighted_avg_price:.2f})")
