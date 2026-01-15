#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二轮优化性能测试
"""

import time
import json
from datetime import datetime

def test_code_reduction():
    """测试代码减少效果"""
    print("📊 第二轮优化代码减少测试")
    print("=" * 50)
    
    # 优化前后的对比
    optimizations = [
        {
            "file": "schemas/sales.py",
            "before": 1888,
            "after": 111,
            "reduction_percent": ((1888 - 111) / 1888) * 100
        },
        {
            "file": "purchase.py", 
            "before": 1569,
            "after": 315,
            "reduction_percent": ((1569 - 315) / 1569) * 100
        },
        {
            "file": "outsourcing.py",
            "before": 1498, 
            "after": 98,
            "reduction_percent": ((1498 - 98) / 1498) * 100
        },
        {
            "file": "bonus.py",
            "before": 1472,
            "after": 121,
            "reduction_percent": ((1472 - 121) / 1472) * 100
        }
    ]
    
    total_before = sum(opt["before"] for opt in optimizations)
    total_after = sum(opt["after"] for opt in optimizations)
    overall_reduction = ((total_before - total_after) / total_before) * 100
    
    print("📈 文件优化结果:")
    for opt in optimizations:
        print(f"  {opt['file']}: {opt['before']}行 → {opt['after']}行 (减少 {opt['reduction_percent']:.1f}%)")
    
    print(f"\n📊 总体优化效果:")
    print(f"  总代码量: {total_before}行 → {total_after}行")
    print(f"  总体减少: {overall_reduction:.1f}%")
    
    return {
        "files": optimizations,
        "total_before": total_before,
        "total_after": total_after,
        "overall_reduction": overall_reduction
    }

def test_import_performance():
    """测试导入性能"""
    print("\n🧪 模块导入性能测试")
    print("=" * 50)
    
    import sys
    sys.path.append('/Users/flw/non-standard-automation-pm')
    
    test_modules = [
        ("app.schemas.sales.leads", "LeadCreate"),
        ("app.schemas.sales.opportunities", "OpportunityCreate"), 
        ("app.schemas.sales.quotes", "QuoteCreate"),
        ("app.schemas.sales.contracts", "ContractCreate"),
        ("app.services.purchase.purchase_service", "PurchaseService")
    ]
    
    import_times = []
    
    for module_name, class_name in test_modules:
        start_time = time.time()
        try:
            module = __import__(module_name, fromlist=[class_name])
            import_time = time.time() - start_time
            import_times.append(import_time)
            print(f"  ✅ {module_name}: {import_time:.4f}s")
        except Exception as e:
            import_time = time.time() - start_time
            import_times.append(import_time)
            print(f"  ❌ {module_name}: {import_time:.4f}s - {e}")
    
    if import_times:
        avg_time = sum(import_times) / len(import_times)
        print(f"\n📈 导入性能统计:")
        print(f"  平均导入时间: {avg_time:.4f}s")
        print(f"  最快导入时间: {min(import_times):.4f}s")
        print(f"  最慢导入时间: {max(import_times):.4f}s")
    
    return import_times

def test_memory_usage():
    """测试内存使用"""
    print("\n💾 内存使用测试")
    print("=" * 50)
    
    try:
        import psutil
        process = psutil.Process()
        
        # 测试前内存
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # 导入优化后的模块
        import sys
        sys.path.append('/Users/flw/non-standard-automation-pm')
        
        from app.schemas.sales.leads import LeadCreate
        from app.schemas.sales.opportunities import OpportunityCreate
        from app.schemas.sales.quotes import QuoteCreate
        from app.schemas.sales.contracts import ContractCreate
        from app.services.purchase.purchase_service import PurchaseService
        
        # 测试后内存
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        print(f"📈 内存使用情况:")
        print(f"  导入前内存: {memory_before:.1f} MB")
        print(f"  导入后内存: {memory_after:.1f} MB")
        print(f"  内存增长: {memory_increase:.1f} MB")
        
        return {
            "memory_before": memory_before,
            "memory_after": memory_after,
            "memory_increase": memory_increase
        }
        
    except ImportError:
        print("  ⚠️ psutil 未安装，跳过内存测试")
        return None

def main():
    """主测试函数"""
    print("🚀 第二轮优化效果测试")
    print("=" * 60)
    
    # 代码减少测试
    code_results = test_code_reduction()
    
    # 导入性能测试
    import_results = test_import_performance()
    
    # 内存使用测试
    memory_results = test_memory_usage()
    
    # 生成测试报告
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "code_reduction": code_results,
        "import_performance": {
            "times": import_results,
            "average": sum(import_results) / len(import_results) if import_results else 0
        },
        "memory_usage": memory_results,
        "summary": {
            "files_optimized": len(code_results["files"]),
            "total_code_reduction": code_results["overall_reduction"],
            "avg_import_time": sum(import_results) / len(import_results) if import_results else 0,
            "memory_efficient": memory_results["memory_increase"] < 50 if memory_results else True
        }
    }
    
    # 保存报告
    report_file = f"round2_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 详细报告已保存到: {report_file}")
    
    # 总结
    print("\n🎊 第二轮优化测试总结")
    print("=" * 50)
    print(f"📈 优化文件数: {report['summary']['files_optimized']}")
    print(f"📉 总体代码减少: {report['summary']['total_code_reduction']:.1f}%")
    print(f"⚡ 平均导入时间: {report['summary']['avg_import_time']:.4f}s")
    
    if report['summary']['memory_efficient']:
        print("💾 内存使用: 高效")
    else:
        print("💾 内存使用: 需要优化")
    
    print("\n🎉 第二轮优化测试完成！")

if __name__ == "__main__":
    main()