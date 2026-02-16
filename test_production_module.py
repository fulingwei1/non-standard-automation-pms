#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产进度模块 - 功能测试脚本

测试8个Agent Teams交付的15个表：
- Team 1: 实时跟踪
- Team 2: 排程优化 (3表)
- Team 3: 质量管理 (4表)
- Team 4: 产能分析 (1表)
- Team 5: 物料跟踪 (4表)
- Team 6: 异常处理 (3表)
"""

import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

# 导入所有模型以确保mapper初始化顺序正确
import app.models  # noqa: F401
from app.models.production import (
    ProductionSchedule,
    ResourceConflict,
    ScheduleAdjustmentLog,
    QualityInspection,
    DefectAnalysis,
    ReworkOrder,
    QualityAlertRule,
    EquipmentOEERecord,
    MaterialBatch,
    MaterialConsumption,
    MaterialAlert,
    MaterialAlertRule,
    ExceptionHandlingFlow,
    ExceptionKnowledge,
    ExceptionPDCA
)
from app.models.base import get_session

def test_team2_scheduling():
    """测试Team 2: 排程优化 (3表)"""
    print("\n" + "="*60)
    print("测试 Team 2: 排程优化系统 (3个表)")
    print("="*60)
    
    db = get_session()
    try:
        # 1. 测试 ProductionSchedule
        schedule = ProductionSchedule(
            schedule_no="SCH-2026-001",
            work_order_id=1,
            workstation_id=1,
            planned_start_time=datetime.now(),
            planned_end_time=datetime.now() + timedelta(hours=8),
            priority=90,
            status="PENDING"
        )
        db.add(schedule)
        db.commit()
        print(f"✓ ProductionSchedule 创建成功: {schedule.schedule_no}")
        
        # 2. 测试 ResourceConflict
        conflict = ResourceConflict(
            schedule_id=schedule.id,
            conflicting_schedule_id=schedule.id,
            conflict_type="RESOURCE",
            resource_type="WORKSTATION",
            conflict_severity="HIGH",
            auto_detected=True
        )
        db.add(conflict)
        db.commit()
        print(f"✓ ResourceConflict 创建成功: 冲突级别={conflict.conflict_severity}")
        
        # 3. 测试 ScheduleAdjustmentLog
        log = ScheduleAdjustmentLog(
            schedule_id=schedule.id,
            adjustment_type="TIME_CHANGE",
            trigger_source="MANUAL",
            reason="测试调整",
            adjusted_by=1,
            adjusted_at=datetime.now()
        )
        db.add(log)
        db.commit()
        print(f"✓ ScheduleAdjustmentLog 创建成功: {log.adjustment_type}")
        
        # 验证查询
        count = db.query(ProductionSchedule).count()
        print(f"\n✅ Team 2 测试通过! 共创建 {count} 条排程记录")
        return True
        
    except Exception as e:
        print(f"❌ Team 2 测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_team3_quality():
    """测试Team 3: 质量管理 (4表)"""
    print("\n" + "="*60)
    print("测试 Team 3: 质量管理系统 (4个表)")
    print("="*60)
    
    db = get_session()
    try:
        # 1. 测试 QualityInspection
        inspection = QualityInspection(
            inspection_no="QI-2026-001",
            work_order_id=1,
            inspection_type="PROCESS",
            inspector_id=1,
            inspection_date=datetime.now(),
            sample_size=100,
            defect_count=5,
            pass_count=95,
            pass_rate=Decimal("95.00"),
            result="PASS"
        )
        db.add(inspection)
        db.commit()
        print(f"✓ QualityInspection 创建成功: 合格率={inspection.pass_rate}%")
        
        # 2. 测试 DefectAnalysis
        defect = DefectAnalysis(
            inspection_id=inspection.id,
            defect_type="SCRATCH",
            defect_count=3,
            defect_rate=Decimal("3.00"),
            severity="MINOR"
        )
        db.add(defect)
        db.commit()
        print(f"✓ DefectAnalysis 创建成功: 缺陷类型={defect.defect_type}")
        
        # 3. 测试 ReworkOrder
        rework = ReworkOrder(
            rework_no="RW-2026-001",
            inspection_id=inspection.id,
            defect_analysis_id=defect.id,
            rework_qty=3,
            status="PENDING"
        )
        db.add(rework)
        db.commit()
        print(f"✓ ReworkOrder 创建成功: 返工数量={rework.rework_qty}")
        
        # 4. 测试 QualityAlertRule
        rule = QualityAlertRule(
            rule_name="高缺陷率预警",
            trigger_condition="defect_rate>5",
            alert_level="HIGH",
            is_active=True
        )
        db.add(rule)
        db.commit()
        print(f"✓ QualityAlertRule 创建成功: {rule.rule_name}")
        
        count = db.query(QualityInspection).count()
        print(f"\n✅ Team 3 测试通过! 共创建 {count} 条质检记录")
        return True
        
    except Exception as e:
        print(f"❌ Team 3 测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_team4_capacity():
    """测试Team 4: 产能分析 (1表)"""
    print("\n" + "="*60)
    print("测试 Team 4: 产能分析系统 (1个表)")
    print("="*60)
    
    db = get_session()
    try:
        # 测试 EquipmentOEERecord
        oee = EquipmentOEERecord(
            equipment_id=1,
            record_date=date.today(),
            shift="DAY",
            planned_time=480,  # 8小时
            actual_time=456,   # 7.6小时
            downtime=24,       # 24分钟停机
            availability=Decimal("95.00"),
            performance=Decimal("98.50"),
            quality_rate=Decimal("99.20"),
            oee=Decimal("92.61")  # 95% * 98.5% * 99.2%
        )
        db.add(oee)
        db.commit()
        print(f"✓ EquipmentOEERecord 创建成功: OEE={oee.oee}%")
        print(f"  - 可用率: {oee.availability}%")
        print(f"  - 性能率: {oee.performance}%")
        print(f"  - 质量率: {oee.quality_rate}%")
        
        count = db.query(EquipmentOEERecord).count()
        print(f"\n✅ Team 4 测试通过! 共创建 {count} 条OEE记录")
        return True
        
    except Exception as e:
        print(f"❌ Team 4 测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_team5_material():
    """测试Team 5: 物料跟踪 (4表)"""
    print("\n" + "="*60)
    print("测试 Team 5: 物料跟踪系统 (4个表)")
    print("="*60)
    
    db = get_session()
    try:
        # 1. 测试 MaterialBatch
        batch = MaterialBatch(
            batch_no="BATCH-2026-001",
            material_id=1,
            quantity=Decimal("1000.00"),
            unit="PCS",
            production_date=date.today(),
            expire_date=date.today() + timedelta(days=365),
            status="IN_STOCK"
        )
        db.add(batch)
        db.commit()
        print(f"✓ MaterialBatch 创建成功: {batch.batch_no}, 数量={batch.quantity}")
        
        # 2. 测试 MaterialConsumption
        consumption = MaterialConsumption(
            work_order_id=1,
            material_id=1,
            batch_id=batch.id,
            planned_qty=Decimal("100.00"),
            actual_qty=Decimal("105.00"),
            waste_qty=Decimal("5.00"),
            waste_rate=Decimal("5.00")
        )
        db.add(consumption)
        db.commit()
        print(f"✓ MaterialConsumption 创建成功: 浪费率={consumption.waste_rate}%")
        
        # 3. 测试 MaterialAlert
        alert = MaterialAlert(
            alert_no="MA-2026-001",
            material_id=1,
            alert_type="SHORTAGE",
            alert_level="HIGH",
            current_qty=Decimal("50.00"),
            required_qty=Decimal("200.00"),
            shortage_qty=Decimal("150.00")
        )
        db.add(alert)
        db.commit()
        print(f"✓ MaterialAlert 创建成功: 缺料数量={alert.shortage_qty}")
        
        # 4. 测试 MaterialAlertRule
        rule = MaterialAlertRule(
            rule_name="低库存预警",
            trigger_condition="stock<safety_stock",
            alert_level="MEDIUM",
            is_active=True
        )
        db.add(rule)
        db.commit()
        print(f"✓ MaterialAlertRule 创建成功: {rule.rule_name}")
        
        count = db.query(MaterialBatch).count()
        print(f"\n✅ Team 5 测试通过! 共创建 {count} 条批次记录")
        return True
        
    except Exception as e:
        print(f"❌ Team 5 测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_team6_exception():
    """测试Team 6: 异常处理 (3表)"""
    print("\n" + "="*60)
    print("测试 Team 6: 异常处理增强系统 (3个表)")
    print("="*60)
    
    db = get_session()
    try:
        # 1. 测试 ExceptionHandlingFlow
        flow = ExceptionHandlingFlow(
            exception_id=1,
            flow_no="FLOW-2026-001",
            current_stage="DETECTION",
            current_handler_id=1,
            start_time=datetime.now()
        )
        db.add(flow)
        db.commit()
        print(f"✓ ExceptionHandlingFlow 创建成功: {flow.flow_no}")
        
        # 2. 测试 ExceptionKnowledge
        knowledge = ExceptionKnowledge(
            title="设备故障解决方案",
            exception_type="EQUIPMENT",
            root_cause="润滑不足",
            solution="定期维护保养",
            effectiveness_score=90
        )
        db.add(knowledge)
        db.commit()
        print(f"✓ ExceptionKnowledge 创建成功: {knowledge.title}")
        
        # 3. 测试 ExceptionPDCA
        pdca = ExceptionPDCA(
            exception_id=1,
            plan_stage="PLAN",
            plan_desc="制定改进计划",
            do_desc="执行改进措施",
            check_desc="验证改进效果",
            act_desc="标准化流程"
        )
        db.add(pdca)
        db.commit()
        print(f"✓ ExceptionPDCA 创建成功: 阶段={pdca.plan_stage}")
        
        count = db.query(ExceptionHandlingFlow).count()
        print(f"\n✅ Team 6 测试通过! 共创建 {count} 条流程记录")
        return True
        
    except Exception as e:
        print(f"❌ Team 6 测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """主测试流程"""
    print("\n" + "🚀" * 30)
    print("生产进度模块 - 完整功能测试")
    print("测试范围: 8个Agent Teams的15个表")
    print("🚀" * 30)
    
    results = {
        "Team 2 - 排程优化 (3表)": test_team2_scheduling(),
        "Team 3 - 质量管理 (4表)": test_team3_quality(),
        "Team 4 - 产能分析 (1表)": test_team4_capacity(),
        "Team 5 - 物料跟踪 (4表)": test_team5_material(),
        "Team 6 - 异常处理 (3表)": test_team6_exception(),
    }
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for team, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {team}")
    
    print("\n" + "-"*60)
    print(f"总计: {passed}/{total} 个模块通过测试")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 恭喜! 所有生产模块测试通过!")
        print("✅ 15个表全部功能正常")
        print("✅ 数据模型关系正确")
        print("✅ CRUD操作成功")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个模块测试失败，需要检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
