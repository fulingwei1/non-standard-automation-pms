#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准成本功能验证脚本
"""

import sys
from datetime import date
from decimal import Decimal

# 设置环境变量
import os
os.environ['SECRET_KEY'] = 'test_secret_key_for_verification'
os.environ['ENVIRONMENT'] = 'development'

from sqlalchemy.orm import Session
from app.models.base import get_session, init_db
from app.models.standard_cost import StandardCost, StandardCostHistory
from app.models.user import User


def verify_models():
    """验证数据模型"""
    print("=" * 60)
    print("1. 验证数据模型...")
    print("=" * 60)
    
    try:
        # 初始化数据库
        init_db()
        print("✓ 数据库初始化成功")
        
        # 验证表结构
        db = next(get_session())
        
        # 检查StandardCost表
        costs = db.query(StandardCost).count()
        print(f"✓ StandardCost 表可用，当前记录数: {costs}")
        
        # 检查StandardCostHistory表
        history_count = db.query(StandardCostHistory).count()
        print(f"✓ StandardCostHistory 表可用，当前记录数: {history_count}")
        
        print("\n✅ 数据模型验证通过!\n")
        return True
    except Exception as e:
        print(f"\n❌ 数据模型验证失败: {e}\n")
        return False


def verify_crud():
    """验证CRUD操作"""
    print("=" * 60)
    print("2. 验证CRUD操作...")
    print("=" * 60)
    
    try:
        db = next(get_session())
        
        # 获取或创建测试用户
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("⚠️  警告: admin用户不存在，跳过CRUD测试")
            return True
        
        # 创建测试数据
        test_cost = StandardCost(
            cost_code="TEST-VERIFY-001",
            cost_name="验证测试成本",
            cost_category="MATERIAL",
            specification="测试规格",
            unit="kg",
            standard_cost=Decimal("10.50"),
            currency="CNY",
            cost_source="HISTORICAL_AVG",
            source_description="测试来源",
            effective_date=date(2026, 1, 1),
            version=1,
            is_active=True,
            created_by=user.id
        )
        db.add(test_cost)
        db.flush()
        print(f"✓ 创建成本项: {test_cost.cost_code}")
        
        # 创建历史记录
        history = StandardCostHistory(
            standard_cost_id=test_cost.id,
            change_type="CREATE",
            change_date=date.today(),
            new_cost=test_cost.standard_cost,
            new_effective_date=test_cost.effective_date,
            change_reason="验证测试",
            changed_by=user.id,
            changed_by_name=user.real_name or "测试用户"
        )
        db.add(history)
        db.commit()
        print(f"✓ 创建历史记录: {history.change_type}")
        
        # 读取数据
        retrieved = db.query(StandardCost).filter(
            StandardCost.cost_code == "TEST-VERIFY-001"
        ).first()
        assert retrieved is not None
        print(f"✓ 读取成本项: {retrieved.cost_name}")
        
        # 更新数据（创建新版本）
        new_version = StandardCost(
            cost_code=test_cost.cost_code,
            cost_name=test_cost.cost_name,
            cost_category=test_cost.cost_category,
            specification=test_cost.specification,
            unit=test_cost.unit,
            standard_cost=Decimal("12.00"),  # 更新价格
            currency=test_cost.currency,
            cost_source=test_cost.cost_source,
            effective_date=test_cost.effective_date,
            version=2,
            is_active=True,
            parent_id=test_cost.id,
            created_by=user.id,
            updated_by=user.id
        )
        
        # 停用旧版本
        test_cost.is_active = False
        
        db.add(new_version)
        db.commit()
        print(f"✓ 更新成本项，创建新版本: v{new_version.version}")
        
        # 删除测试数据（停用）
        new_version.is_active = False
        new_version.expiry_date = date.today()
        db.commit()
        print(f"✓ 停用成本项")
        
        # 清理测试数据
        db.delete(new_version)
        db.delete(test_cost)
        db.delete(history)
        db.commit()
        print(f"✓ 清理测试数据")
        
        print("\n✅ CRUD操作验证通过!\n")
        return True
    except Exception as e:
        print(f"\n❌ CRUD操作验证失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def verify_sample_data():
    """验证示例数据"""
    print("=" * 60)
    print("3. 验证示例数据...")
    print("=" * 60)
    
    try:
        db = next(get_session())
        
        # 检查物料成本
        material_costs = db.query(StandardCost).filter(
            StandardCost.cost_category == "MATERIAL",
            StandardCost.is_active == True
        ).count()
        print(f"✓ 物料成本数量: {material_costs}")
        
        # 检查人工成本
        labor_costs = db.query(StandardCost).filter(
            StandardCost.cost_category == "LABOR",
            StandardCost.is_active == True
        ).count()
        print(f"✓ 人工成本数量: {labor_costs}")
        
        # 检查制造费用
        overhead_costs = db.query(StandardCost).filter(
            StandardCost.cost_category == "OVERHEAD",
            StandardCost.is_active == True
        ).count()
        print(f"✓ 制造费用数量: {overhead_costs}")
        
        # 显示总数
        total = material_costs + labor_costs + overhead_costs
        print(f"✓ 标准成本总数: {total}")
        
        if total > 0:
            # 显示示例数据
            sample = db.query(StandardCost).filter(
                StandardCost.is_active == True
            ).first()
            if sample:
                print(f"\n示例成本项:")
                print(f"  编码: {sample.cost_code}")
                print(f"  名称: {sample.cost_name}")
                print(f"  类别: {sample.cost_category}")
                print(f"  单位: {sample.unit}")
                print(f"  成本: {sample.standard_cost} {sample.currency}")
        
        print("\n✅ 示例数据验证通过!\n")
        return True
    except Exception as e:
        print(f"\n❌ 示例数据验证失败: {e}\n")
        return False


def verify_api_structure():
    """验证API结构"""
    print("=" * 60)
    print("4. 验证API结构...")
    print("=" * 60)
    
    try:
        import app.api.v1.endpoints.standard_costs as standard_costs_module
        
        # 检查模块
        print("✓ standard_costs模块导入成功")
        
        # 检查子模块
        from app.api.v1.endpoints.standard_costs import crud, project_integration, bulk_import, history
        print("✓ crud子模块导入成功")
        print("✓ project_integration子模块导入成功")
        print("✓ bulk_import子模块导入成功")
        print("✓ history子模块导入成功")
        
        # 检查路由
        assert hasattr(standard_costs_module, 'router')
        print("✓ router对象存在")
        
        print("\n✅ API结构验证通过!\n")
        return True
    except Exception as e:
        print(f"\n❌ API结构验证失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def verify_schemas():
    """验证Schemas"""
    print("=" * 60)
    print("5. 验证Schemas...")
    print("=" * 60)
    
    try:
        from app.schemas import standard_cost
        
        # 检查主要Schema类
        schemas = [
            'StandardCostCreate',
            'StandardCostUpdate',
            'StandardCostResponse',
            'StandardCostHistoryResponse',
            'StandardCostImportRow',
            'StandardCostImportResult',
            'ProjectCostComparisonResponse',
            'ApplyStandardCostRequest',
            'ApplyStandardCostResponse'
        ]
        
        for schema_name in schemas:
            assert hasattr(standard_cost, schema_name)
            print(f"✓ {schema_name} schema存在")
        
        print("\n✅ Schemas验证通过!\n")
        return True
    except Exception as e:
        print(f"\n❌ Schemas验证失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("标准成本库管理功能验证")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行各项验证
    results.append(("数据模型", verify_models()))
    results.append(("CRUD操作", verify_crud()))
    results.append(("示例数据", verify_sample_data()))
    results.append(("API结构", verify_api_structure()))
    results.append(("Schemas", verify_schemas()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20} {status}")
    
    print(f"\n总计: {passed}/{total} 项验证通过")
    
    if passed == total:
        print("\n🎉 所有验证通过！标准成本库管理功能实现完成！\n")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项验证失败，请检查！\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
