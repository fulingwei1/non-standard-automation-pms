#!/usr/bin/env python3
"""
售前AI方案生成模块 - 快速验证脚本
Presale AI Solution Generation - Quick Verification Script
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest


def print_header(text):
    """打印标题"""
    print(f"\n{'=' * 80}")
    print(f"{text:^80}")
    print(f"{'=' * 80}\n")


def print_success(text):
    """打印成功消息"""
    print(f"✓ {text}")


def print_error(text):
    """打印错误消息"""
    print(f"✗ {text}")


def print_warning(text):
    """打印警告消息"""
    print(f"⚠ {text}")


def print_info(text):
    """打印信息"""
    print(f"{text}")


def check_files():
    """检查文件是否存在"""
    print_header("1. 文件检查")
    
    files = {
        "数据模型": "app/models/presale_ai_solution.py",
        "Schemas": "app/schemas/presale_ai_solution.py",
        "核心服务": "app/services/presale_ai_service.py",
        "AI客户端": "app/services/ai_client_service.py",
        "模板服务": "app/services/presale_ai_template_service.py",
        "导出服务": "app/services/presale_ai_export_service.py",
        "API路由": "app/api/presale_ai_routes.py",
        "数据迁移": "migrations/versions/20260215_add_presale_ai_solution.py",
        "单元测试": "tests/test_presale_ai_solution.py",
        "模板样例": "data/presale_solution_templates_samples.json",
        "API文档": "docs/API_PRESALE_AI_SOLUTION.md",
        "用户手册": "docs/USER_MANUAL_PRESALE_AI_SOLUTION.md",
        "实施报告": "docs/IMPLEMENTATION_REPORT_PRESALE_AI_SOLUTION.md",
    }
    
    all_exist = True
    for name, path in files.items():
        if os.path.exists(path):
            print_success(f"{name:20s} {path}")
        else:
            print_error(f"{name:20s} {path} [缺失]")
            all_exist = False
    
    return all_exist


def check_imports():
    """检查Python模块导入"""
    print_header("2. 模块导入检查")
    
    imports = {
        "数据模型": "from app.models.presale_ai_solution import PresaleAISolution, PresaleSolutionTemplate",
        "Schemas": "from app.schemas.presale_ai_solution import SolutionGenerationRequest",
        "服务层": "from app.services.presale_ai_service import PresaleAIService",
        "AI客户端": "from app.services.ai_client_service import AIClientService",
    }
    
    all_success = True
    for name, import_stmt in imports.items():
        try:
            exec(import_stmt)
            print_success(f"{name:15s} 导入成功")
        except Exception as e:
            print_error(f"{name:15s} 导入失败: {e}")
            all_success = False
    
    return all_success


def run_unit_tests():
    """运行单元测试"""
    print_header("3. 单元测试")
    
    print_info("运行测试套件...")
    result = pytest.main([
        "tests/test_presale_ai_solution.py",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
    
    if result == 0:
        print_success("\n所有单元测试通过 ✓")
        return True
    else:
        print_error(f"\n单元测试失败 (退出码: {result})")
        return False


def check_api_endpoints():
    """检查API端点定义"""
    print_header("4. API端点检查")
    
    try:
        from app.api.presale_ai_routes import router
        
        endpoints = []
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    if method != "HEAD":  # 忽略HEAD方法
                        endpoints.append(f"{method:6s} {route.path}")
        
        print_info(f"发现 {len(endpoints)} 个API端点:\n")
        for endpoint in sorted(endpoints):
            print_success(f"  {endpoint}")
        
        # 验证核心端点
        required_paths = [
            "/match-templates",
            "/generate-solution",
            "/generate-architecture",
            "/generate-bom",
            "/solution/{solution_id}",
            "/export-solution-pdf",
            "/template-library"
        ]
        
        all_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        missing = [path for path in required_paths if not any(path in p for p in all_paths)]
        
        if not missing:
            print_success("\n✓ 所有核心API端点已定义")
            return True
        else:
            print_error(f"\n✗ 缺失端点: {missing}")
            return False
            
    except Exception as e:
        print_error(f"API端点检查失败: {e}")
        return False


def check_template_samples():
    """检查模板样例数据"""
    print_header("5. 模板样例检查")
    
    try:
        import json
        with open("data/presale_solution_templates_samples.json", "r", encoding="utf-8") as f:
            templates = json.load(f)
        
        print_success(f"加载了 {len(templates)} 个模板样例")
        
        for i, template in enumerate(templates, 1):
            industry = template.get("industry", "未知")
            equipment = template.get("equipment_type", "未知")
            print_info(f"  {i}. {template['name']} ({industry} - {equipment})")
        
        if len(templates) >= 10:
            print_success(f"\n✓ 模板数量符合要求 (>= 10)")
            return True
        else:
            print_warning(f"\n⚠ 模板数量不足 ({len(templates)}/10)")
            return False
            
    except Exception as e:
        print_error(f"模板样例检查失败: {e}")
        return False


def print_summary(results):
    """打印总结"""
    print_header("验证总结")
    
    total = len(results)
    passed = sum(results.values())
    
    for name, status in results.items():
        if status:
            print_success(f"{name:20s} PASSED")
        else:
            print_error(f"{name:20s} FAILED")
    
    print(f"\n{'=' * 80}")
    if passed == total:
        print(f"✓ 所有验证通过! ({passed}/{total})")
        print(f"{'=' * 80}\n")
        return 0
    else:
        print(f"✗ 验证失败: {passed}/{total} 通过")
        print(f"{'=' * 80}\n")
        return 1


def main():
    """主函数"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║           售前AI方案生成模块 - 快速验证脚本                                    ║")
    print("║              Presale AI Solution - Quick Verification                      ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    
    results = {}
    
    # 1. 文件检查
    results["文件检查"] = check_files()
    
    # 2. 模块导入检查
    results["模块导入"] = check_imports()
    
    # 3. 单元测试
    results["单元测试"] = run_unit_tests()
    
    # 4. API端点检查
    results["API端点"] = check_api_endpoints()
    
    # 5. 模板样例检查
    results["模板样例"] = check_template_samples()
    
    # 打印总结
    return print_summary(results)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n验证已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证失败: {e}")
        sys.exit(1)
