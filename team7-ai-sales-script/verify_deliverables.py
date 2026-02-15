#!/usr/bin/env python3
"""
验证项目交付物的完整性
"""
import os
import sys
from pathlib import Path


def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {description}: {file_path} ({size} bytes)")
        return True
    else:
        print(f"❌ {description}: {file_path} [NOT FOUND]")
        return False


def check_directory_exists(dir_path, description):
    """检查目录是否存在"""
    if os.path.isdir(dir_path):
        files = len(list(Path(dir_path).glob('**/*')))
        print(f"✅ {description}: {dir_path} ({files} files)")
        return True
    else:
        print(f"❌ {description}: {dir_path} [NOT FOUND]")
        return False


def count_lines(file_path):
    """统计文件行数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 AI智能话术推荐引擎 - 交付物验证")
    print("=" * 80)
    print()
    
    results = []
    
    # 1. 核心代码文件
    print("📁 1. 核心代码文件")
    print("-" * 80)
    code_files = [
        ("app/models/customer_profile.py", "客户画像模型"),
        ("app/models/sales_script.py", "销售话术模型"),
        ("app/services/ai_service.py", "AI服务"),
        ("app/services/customer_profile_service.py", "客户画像服务"),
        ("app/services/sales_script_service.py", "销售话术服务"),
        ("app/routes/customer_profile.py", "客户画像路由"),
        ("app/routes/sales_script.py", "销售话术路由"),
        ("app/schemas/customer_profile.py", "客户画像Schema"),
        ("app/schemas/sales_script.py", "销售话术Schema"),
        ("app/config.py", "配置文件"),
        ("app/database.py", "数据库连接"),
        ("app/main.py", "应用入口"),
    ]
    
    for file_path, desc in code_files:
        results.append(check_file_exists(file_path, desc))
    
    print()
    
    # 2. 数据库迁移
    print("📁 2. 数据库迁移文件")
    print("-" * 80)
    results.append(check_file_exists("migrations/001_create_tables.sql", "数据库迁移脚本"))
    print()
    
    # 3. 测试文件
    print("📁 3. 单元测试文件")
    print("-" * 80)
    test_files = [
        ("tests/conftest.py", "测试配置"),
        ("tests/test_customer_profile.py", "客户画像测试"),
        ("tests/test_sales_script.py", "销售话术测试"),
        ("tests/test_objection_handling.py", "异议处理测试"),
        ("tests/test_sales_progress.py", "销售进程测试"),
        ("tests/test_api.py", "API端点测试"),
    ]
    
    for file_path, desc in test_files:
        results.append(check_file_exists(file_path, desc))
    
    # 统计测试用例数量
    print()
    print("🧪 测试用例统计:")
    total_tests = 0
    for file_path, _ in test_files[1:]:  # 跳过conftest.py
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                test_count = content.count('def test_')
                print(f"   {os.path.basename(file_path)}: {test_count}个用例")
                total_tests += test_count
    print(f"   📊 总计: {total_tests}个测试用例 (目标: ≥22个)")
    
    print()
    
    # 4. 数据种子文件
    print("📁 4. 数据种子文件")
    print("-" * 80)
    results.append(check_file_exists("data/sales_script_seeds.py", "话术模板种子数据"))
    results.append(check_file_exists("data/import_seeds.py", "数据导入脚本"))
    
    # 统计话术模板数量
    if os.path.exists("data/sales_script_seeds.py"):
        with open("data/sales_script_seeds.py", 'r') as f:
            content = f.read()
            # 统计SALES_SCRIPT_TEMPLATES列表中的字典数量
            template_count = content.count('"scenario":')
            strategy_count = content.count('"objection_type":')
            print(f"   📊 话术模板: {template_count}条 (目标: ≥100条)")
            print(f"   📊 异议策略: {strategy_count}个 (目标: ≥20个)")
    
    print()
    
    # 5. 文档文件
    print("📁 5. 文档文件")
    print("-" * 80)
    doc_files = [
        ("docs/API_DOCUMENTATION.md", "API文档"),
        ("docs/USER_MANUAL.md", "用户使用手册"),
        ("docs/IMPLEMENTATION_REPORT.md", "实施总结报告"),
        ("README.md", "README文档"),
    ]
    
    for file_path, desc in doc_files:
        results.append(check_file_exists(file_path, desc))
        if os.path.exists(file_path):
            lines = count_lines(file_path)
            print(f"      {lines}行")
    
    print()
    
    # 6. 配置文件
    print("📁 6. 配置文件")
    print("-" * 80)
    config_files = [
        ("requirements.txt", "依赖配置"),
        (".env.example", "环境变量示例"),
        ("pytest.ini", "pytest配置"),
    ]
    
    for file_path, desc in config_files:
        results.append(check_file_exists(file_path, desc))
    
    print()
    
    # 7. 目录结构
    print("📁 7. 目录结构")
    print("-" * 80)
    directories = [
        ("app", "应用代码"),
        ("app/models", "数据模型"),
        ("app/services", "业务服务"),
        ("app/routes", "API路由"),
        ("app/schemas", "数据Schema"),
        ("tests", "测试代码"),
        ("migrations", "数据库迁移"),
        ("data", "种子数据"),
        ("docs", "文档"),
    ]
    
    for dir_path, desc in directories:
        results.append(check_directory_exists(dir_path, desc))
    
    print()
    
    # 统计总结
    print("=" * 80)
    print("📊 验证总结")
    print("=" * 80)
    total = len(results)
    passed = sum(results)
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 完成率: {passed/total*100:.1f}%")
    print()
    
    # API端点统计
    print("🔌 API端点统计:")
    if os.path.exists("app/routes/customer_profile.py") and os.path.exists("app/routes/sales_script.py"):
        with open("app/routes/customer_profile.py", 'r') as f:
            profile_routes = f.read().count('@router.')
        with open("app/routes/sales_script.py", 'r') as f:
            script_routes = f.read().count('@router.')
        total_routes = profile_routes + script_routes
        print(f"   客户画像API: {profile_routes}个")
        print(f"   销售话术API: {script_routes}个")
        print(f"   📊 总计: {total_routes}个API端点 (目标: ≥9个)")
    print()
    
    # 验收标准检查
    print("✅ 验收标准检查:")
    checks = [
        ("客户画像准确率 >80%", "需人工测试验证", "🔄"),
        ("话术推荐相关性 >85%", "需人工测试验证", "🔄"),
        ("异议处理有效性 >80%", "需人工测试验证", "🔄"),
        ("响应时间 <3秒", "需性能测试验证", "🔄"),
        (f"单元测试 ≥22个", f"实际{total_tests}个", "✅" if total_tests >= 22 else "❌"),
        ("API端点 ≥9个", f"实际{total_routes if 'total_routes' in locals() else 0}个", 
         "✅" if 'total_routes' in locals() and total_routes >= 9 else "❌"),
        ("话术模板 ≥100条", f"实际{template_count if 'template_count' in locals() else 0}条", 
         "✅" if 'template_count' in locals() and template_count >= 100 else "❌"),
        ("异议策略 ≥20个", f"实际{strategy_count if 'strategy_count' in locals() else 0}个", 
         "✅" if 'strategy_count' in locals() and strategy_count >= 20 else "❌"),
    ]
    
    for check, status, icon in checks:
        print(f"   {icon} {check}: {status}")
    
    print()
    print("=" * 80)
    
    if passed == total:
        print("🎉 所有交付物验证通过！项目完成！")
        return 0
    else:
        print("⚠️  部分交付物缺失，请检查！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
