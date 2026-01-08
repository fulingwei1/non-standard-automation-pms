#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试技术评估功能（不依赖HTTP服务器）
直接测试数据库和服务层
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.base import get_session
from app.models.sales import (
    Lead, TechnicalAssessment, ScoringRule, FailureCase, OpenItem
)
from app.models.user import User
from app.services.technical_assessment_service import TechnicalAssessmentService
from app.models.enums import AssessmentSourceTypeEnum, AssessmentStatusEnum


def test_scoring_rule():
    """测试评分规则"""
    print("\n1. 测试评分规则...")
    db = get_session()
    try:
        rule = db.query(ScoringRule).filter(ScoringRule.is_active == True).first()
        if rule:
            print(f"   ✅ 找到启用的评分规则: {rule.version}")
            return True
        else:
            print("   ❌ 未找到启用的评分规则")
            return False
    finally:
        db.close()


def test_assessment_service():
    """测试评估服务"""
    print("\n2. 测试评估服务...")
    db = get_session()
    try:
        # 获取一个线索
        lead = db.query(Lead).first()
        if not lead:
            print("   ⚠️  没有可用的线索，跳过测试")
            return False
        
        print(f"   ℹ️  使用线索: {lead.lead_code} (ID: {lead.id})")
        
        # 创建评估申请
        assessment = TechnicalAssessment(
            source_type=AssessmentSourceTypeEnum.LEAD.value,
            source_id=lead.id,
            evaluator_id=1,  # 假设admin用户ID为1
            status=AssessmentStatusEnum.PENDING.value
        )
        db.add(assessment)
        db.flush()
        print(f"   ✅ 创建评估申请: ID={assessment.id}")
        
        # 执行评估
        service = TechnicalAssessmentService(db)
        requirement_data = {
            "industry": "新能源",
            "customerType": "新客户",
            "budgetStatus": "明确",
            "techRequirements": "电池测试设备",
            "requirementMaturity": 3,
            "customerPotential": "中",
            "demandClarity": "详细规范",
            "techMaturity": "成熟",
            "deliveryFeasibility": "合理"
        }
        
        try:
            result = service.evaluate(
                assessment.source_type,
                assessment.source_id,
                1,
                requirement_data
            )
            print(f"   ✅ 评估完成:")
            print(f"      总分: {result.total_score}")
            print(f"      决策: {result.decision}")
            print(f"      一票否决: {result.veto_triggered}")
            
            if result.dimension_scores:
                import json
                dims = json.loads(result.dimension_scores)
                print(f"      维度分数: {dims}")
            
            return True
        except Exception as e:
            print(f"   ❌ 评估失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    finally:
        db.close()


def test_failure_case_matching():
    """测试失败案例匹配"""
    print("\n3. 测试失败案例匹配...")
    db = get_session()
    try:
        # 检查是否已存在
        from datetime import datetime
        case_code = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        existing = db.query(FailureCase).filter(FailureCase.case_code == case_code).first()
        if existing:
            case = existing
            print(f"   ℹ️  使用现有失败案例: {case.case_code}")
        else:
            # 创建测试失败案例
            case = FailureCase(
                case_code=case_code,
                project_name="测试失败项目",
                industry="新能源",
                product_types='["电池测试"]',
                takt_time_s=30,
                failure_tags='["需求不明确"]',
                core_failure_reason="客户需求频繁变更",
                early_warning_signals='["需求文档不完整"]',
                lesson_learned="需要在项目前期充分沟通需求",
                keywords='["需求变更"]'
            )
            db.add(case)
            db.commit()
            print(f"   ✅ 创建测试失败案例: {case.case_code}")
        
        # 测试匹配
        service = TechnicalAssessmentService(db)
        requirement_data = {
            "industry": "新能源",
            "productTypes": '["电池测试"]',
            "targetTakt": 30
        }
        
        similar_cases = service._match_similar_cases(requirement_data)
        print(f"   ✅ 找到 {len(similar_cases)} 个相似案例")
        for case_info in similar_cases:
            print(f"      - {case_info.get('project_name')} (相似度: {case_info.get('similarity_score', 0):.2%})")
        
        return True
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_open_items():
    """测试未决事项"""
    print("\n4. 测试未决事项...")
    db = get_session()
    try:
        lead = db.query(Lead).first()
        if not lead:
            print("   ⚠️  没有可用的线索，跳过测试")
            return False
        
        from datetime import datetime
        import time
        item_code = f"TEST-{datetime.now().strftime('%y%m%d')}-{int(time.time()) % 10000:04d}"
        # 检查是否已存在
        existing = db.query(OpenItem).filter(OpenItem.item_code == item_code).first()
        if existing:
            open_item = existing
            print(f"   ℹ️  使用现有未决事项: {open_item.item_code}")
        else:
            open_item = OpenItem(
                source_type=AssessmentSourceTypeEnum.LEAD.value,
                source_id=lead.id,
                item_code=item_code,
                item_type="INTERFACE",
                description="测试未决事项：接口协议文档尚未提供",
                responsible_party="CUSTOMER",
                blocks_quotation=True
            )
            db.add(open_item)
            db.commit()
            print(f"   ✅ 创建未决事项: {open_item.item_code}")
        
        # 检查阻塞报价的事项
        blocking = db.query(OpenItem).filter(
            OpenItem.source_type == AssessmentSourceTypeEnum.LEAD.value,
            OpenItem.source_id == lead.id,
            OpenItem.blocks_quotation == True,
            OpenItem.status != 'CLOSED'
        ).count()
        print(f"   ✅ 阻塞报价的未决事项数量: {blocking}")
        
        return True
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """主测试函数"""
    print("="*60)
    print("技术评估系统快速测试（数据库层）")
    print("="*60)
    
    results = []
    
    # 测试评分规则
    results.append(("评分规则", test_scoring_rule()))
    
    # 测试评估服务
    results.append(("评估服务", test_assessment_service()))
    
    # 测试失败案例匹配
    results.append(("失败案例匹配", test_failure_case_matching()))
    
    # 测试未决事项
    results.append(("未决事项", test_open_items()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")


if __name__ == "__main__":
    main()

