#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis性能测试脚本

测试Redis缓存功能的性能表现
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_basic_operations():
    """测试基本Redis操作性能"""
    print("\n" + "=" * 60)
    print("测试1: 基本操作性能")
    print("=" * 60)

    try:
        import redis

        # 创建Redis客户端
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url, decode_responses=True)

        # 测试写入性能
        print("\n写入测试...")
        start = time.time()
        for i in range(1000):
            client.setex(f"test_key_{i}", 300, f"test_value_{i}")
        write_time = time.time() - start
        print(f"✓ 写入1000条数据: {write_time:.4f}秒 ({1000/write_time:.2f} ops/sec)")

        # 测试读取性能
        print("\n读取测试...")
        start = time.time()
        for i in range(1000):
            client.get(f"test_key_{i}")
        read_time = time.time() - start
        print(f"✓ 读取1000条数据: {read_time:.4f}秒 ({1000/read_time:.2f} ops/sec)")

        # 测试删除性能
        print("\n删除测试...")
        start = time.time()
        for i in range(1000):
            client.delete(f"test_key_{i}")
        delete_time = time.time() - start
        print(f"✓ 删除1000条数据: {delete_time:.4f}秒 ({1000/delete_time:.2f} ops/sec)")

        # 清理
        client.delete("test_key_1000")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_json_operations():
    """测试JSON数据操作性能"""
    print("\n" + "=" * 60)
    print("测试2: JSON数据操作性能")
    print("=" * 60)

    import json

    try:
        import redis

        # 创建Redis客户端
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url, decode_responses=True)

        # 模拟项目数据
        test_data = {
            "id": 1,
            "code": "PJ250708001",
            "name": "测试项目",
            "status": "ACTIVE",
            "stage": "S2",
            "health": "H1",
            "customer": {"id": 1, "name": "测试客户"},
            "pm": {"id": 1, "name": "张三"},
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-10T00:00:00",
        }
        json_data = json.dumps(test_data, ensure_ascii=False)

        print("\nJSON写入测试...")
        start = time.time()
        for i in range(100):
            client.setex(f"project_{i}", 300, json_data)
        write_time = time.time() - start
        print(f"✓ 写入100个JSON对象: {write_time:.4f}秒 ({100/write_time:.2f} ops/sec)")
        print(f"  数据大小: {len(json_data)} bytes")

        print("\nJSON读取测试...")
        start = time.time()
        for i in range(100):
            data = client.get(f"project_{i}")
            if data:
                parsed = json.loads(data)
        read_time = time.time() - start
        print(f"✓ 读取并解析100个JSON对象: {read_time:.4f}秒 ({100/read_time:.2f} ops/sec)")

        # 清理
        for i in range(100):
            client.delete(f"project_{i}")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_cache_manager():
    """测试缓存管理器功能"""
    print("\n" + "=" * 60)
    print("测试3: 缓存管理器功能")
    print("=" * 60)

    try:
        from app.core.cache import cache_manager, CACHE_PREFIXES

        print("\n可用缓存前缀:")
        for prefix, description in CACHE_PREFIXES.items():
            print(f"  - {prefix}")

        print("\n测试基本功能...")

        # 测试设置缓存
        test_key = "test:cache:basic"
        test_data = {"id": 1, "name": "测试数据"}
        cache_manager.set(test_key, test_data, ttl=10)
        print(f"✓ 设置缓存: {test_key}")

        # 测试获取缓存
        cached_data = cache_manager.get(test_key)
        if cached_data == test_data:
            print(f"✓ 获取缓存成功: {cached_data}")
        else:
            print(f"✗ 获取缓存失败: 预期 {test_data}, 实际 {cached_data}")
            return False

        # 测试删除缓存
        cache_manager.delete(test_key)
        deleted_data = cache_manager.get(test_key)
        if deleted_data is None:
            print(f"✓ 删除缓存成功")
        else:
            print(f"✗ 删除缓存失败")
            return False

        # 测试批量删除
        for i in range(5):
            cache_manager.set(f"test:batch:{i}", {"value": i}, ttl=10)
        deleted_count = cache_manager.delete_pattern("test:batch:*")
        print(f"✓ 批量删除缓存: 删除了 {deleted_count} 个键")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cached_decorator():
    """测试缓存装饰器"""
    print("\n" + "=" * 60)
    print("测试4: 缓存装饰器")
    print("=" * 60)

    try:
        from app.core.cache import cached

        call_count = {"count": 0}

        @cached(prefix="test:decorator", ttl=10)
        def expensive_function(x, y):
            """模拟耗时函数"""
            call_count["count"] += 1
            time.sleep(0.1)  # 模拟耗时操作
            return x + y

        print("\n第一次调用（未缓存）:")
        start = time.time()
        result1 = expensive_function(2, 3)
        elapsed1 = time.time() - start
        print(f"  结果: {result1}, 耗时: {elapsed1:.4f}秒, 调用次数: {call_count['count']}")

        print("\n第二次调用（从缓存）:")
        start = time.time()
        result2 = expensive_function(2, 3)
        elapsed2 = time.time() - start
        print(f"  结果: {result2}, 耗时: {elapsed2:.4f}秒, 调用次数: {call_count['count']}")

        print("\n第三次调用（不同参数）:")
        start = time.time()
        result3 = expensive_function(3, 4)
        elapsed3 = time.time() - start
        print(f"  结果: {result3}, 耗时: {elapsed3:.4f}秒, 调用次数: {call_count['count']}")

        # 验证缓存效果
        if elapsed2 < elapsed1 / 10:
            print(f"\n✓ 缓存效果显著: 加速 {elapsed1/elapsed2:.2f}倍")
        else:
            print(f"\n✗ 缓存效果不明显")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_concurrent_access():
    """测试并发访问性能"""
    print("\n" + "=" * 60)
    print("测试5: 并发访问性能")
    print("=" * 60)

    try:
        import redis
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # 创建Redis客户端
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url, decode_responses=True)

        # 清理测试数据
        client.delete_pattern("test:concurrent:*")

        def worker(worker_id: int):
            """工作线程"""
            results = []
            for i in range(100):
                # 写入
                client.setex(f"test:concurrent:{worker_id}:{i}", 300, f"value_{i}")
                # 读取
                value = client.get(f"test:concurrent:{worker_id}:{i}")
                results.append(value == f"value_{i}")
            return all(results)

        print(f"\n使用5个并发线程，每个线程执行100次读写...")
        start = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]

        elapsed = time.time() - start
        print(f"✓ 完成500次读写操作: {elapsed:.4f}秒 ({500/elapsed:.2f} ops/sec)")
        print(f"✓ 所有操作成功: {all(results)}")

        # 清理
        client.delete_pattern("test:concurrent:*")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Redis性能测试套件")
    print("=" * 60)

    # 检查Redis连接
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    print(f"\nRedis URL: {redis_url}")

    try:
        import redis
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print("✓ Redis连接正常\n")
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        print("请先运行: python scripts/setup_redis.py")
        return False

    # 运行所有测试
    tests = [
        ("基本操作性能", test_basic_operations),
        ("JSON数据操作", test_json_operations),
        ("缓存管理器功能", test_cache_manager),
        ("缓存装饰器", test_cached_decorator),
        ("并发访问性能", test_concurrent_access),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name}测试出错: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name}: {status}")

    total = len(results)
    passed = sum(1 for _, s in results if s)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n✓ 所有测试通过！Redis缓存功能正常。")
        return True
    else:
        print(f"\n✗ {total - passed} 个测试失败，请检查Redis配置。")
        return False


if __name__ == "__main__":
    import json

    success = run_all_tests()
    sys.exit(0 if success else 1)
