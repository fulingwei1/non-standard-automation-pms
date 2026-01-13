#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时服务验证脚本
用于验证所有注册的预警/定时服务是否正常工作
"""

import sys
import traceback
from datetime import datetime, date
from importlib import import_module

from app.utils.scheduler_config import SCHEDULER_TASKS

ACTIVE_TASKS = [task for task in SCHEDULER_TASKS if task.get("enabled", True)]
EXPECTED_JOBS = [(task["id"], task["name"]) for task in ACTIVE_TASKS]
SERVICE_IMPORTS = sorted(
    {(task["module"], task["callable"]) for task in SCHEDULER_TASKS},
    key=lambda item: (item[0], item[1]),
)

# 添加项目路径
sys.path.insert(0, '.')

def test_imports():
    """测试所有服务的导入"""
    print("=" * 60)
    print("测试服务导入...")
    print("=" * 60)
    
    missing = []
    for module_path, attr in SERVICE_IMPORTS:
        try:
            module = import_module(module_path)
            if not hasattr(module, attr):
                missing.append(f"{module_path}.{attr}")
        except Exception as exc:
            missing.append(f"{module_path}.{attr} (导入失败: {exc})")
    if missing:
        print("❌ 以下服务导入失败或不存在：")
        for item in missing:
            print(f"   - {item}")
        return False
    print(f"✅ 服务导入成功，共 {len(SERVICE_IMPORTS)} 个函数")
    return True


def test_scheduler_config():
    """测试调度器配置与注册情况"""
    print("\n" + "=" * 60)
    print("测试调度器配置...")
    print("=" * 60)
    
    try:
        from app.utils.scheduler import scheduler, init_scheduler
        
        # 检查调度器是否已初始化
        if not scheduler.running:
            print("⚠️  调度器未运行，尝试初始化...")
            try:
                init_scheduler()
                print("✅ 调度器初始化成功")
            except Exception as e:
                print(f"❌ 调度器初始化失败: {str(e)}")
                return False
        else:
            print("✅ 调度器正在运行")
        
        # 检查已注册的任务
        jobs = scheduler.get_jobs()
        actual_ids = {job.id for job in jobs}
        expected_ids = {job_id for job_id, _ in EXPECTED_JOBS}
        missing = expected_ids - actual_ids
        extra = actual_ids - expected_ids
        print(f"✅ 已注册任务数: {len(jobs)}（期望 {len(EXPECTED_JOBS)}）")
        
        if missing:
            print("⚠️ 缺失的任务:")
            for job_id in sorted(missing):
                print(f"  - {job_id}")
        if extra:
            print("⚠️ 未在期望列表的任务:")
            for job_id in sorted(extra):
                print(f"  - {job_id}")
        
        print("\n已注册的任务列表:")
        for job in sorted(jobs, key=lambda j: j.id):
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else "未计划"
            print(f"  - {job.id}: {job.name} (下次执行: {next_run})")
        
        return not missing
    except ImportError as e:
        if 'apscheduler' in str(e):
            print("⚠️  APScheduler未安装，跳过调度器测试")
            print("   提示: 运行 'pip install apscheduler' 安装依赖")
            return True  # 不算失败，只是缺少依赖
        else:
            print(f"❌ 导入失败: {str(e)}")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"❌ 调度器配置测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_service_functions():
    """测试服务函数（不实际执行，只检查函数是否存在）"""
    print("\n" + "=" * 60)
    print("测试服务函数...")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    visited = set()
    
    for task in SCHEDULER_TASKS:
        key = (task["module"], task["callable"])
        if key in visited:
            continue
        visited.add(key)
        module_path, attr = key
        try:
            module = import_module(module_path)
            func = getattr(module, attr, None)
            if callable(func):
                print(f"✅ {attr}: {task['name']} ({module_path})")
                success_count += 1
            else:
                print(f"❌ {attr}: 不是可调用函数 ({module_path})")
                fail_count += 1
        except Exception as exc:
            print(f"❌ {attr}: 导入失败 ({module_path}) -> {exc}")
            fail_count += 1
    
    print(f"\n测试结果: {success_count} 个成功, {fail_count} 个失败")
    return fail_count == 0


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("测试数据库连接...")
    print("=" * 60)
    
    try:
        from app.models.base import get_db_session
        
        with get_db_session() as db:
            # 简单查询测试
            from app.models.project import Project
            count = db.query(Project).count()
            print(f"✅ 数据库连接成功（项目数: {count}）")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("定时服务验证脚本")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    # 测试导入
    results.append(("服务导入", test_imports()))
    
    # 测试数据库连接
    results.append(("数据库连接", test_database_connection()))
    
    # 测试服务函数
    results.append(("服务函数", test_service_functions()))
    
    # 测试调度器配置
    results.append(("调度器配置", test_scheduler_config()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查上述错误信息")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
