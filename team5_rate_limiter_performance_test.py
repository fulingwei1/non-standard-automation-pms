#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate Limiter 性能测试

测试slowapi rate limiter对请求处理时间的影响
"""
import time
import statistics
from typing import List, Dict
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


def create_app_with_limiter() -> FastAPI:
    """创建启用rate limiter的应用"""
    app = FastAPI(title="Test with Limiter")
    
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000/minute"]  # 高限制避免测试时触发
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    @app.post("/test")
    @limiter.limit("1000/minute")
    def test_endpoint(request: Request):
        return {"status": "ok", "timestamp": time.time()}
    
    return app


def create_app_without_limiter() -> FastAPI:
    """创建未启用rate limiter的应用"""
    app = FastAPI(title="Test without Limiter")
    
    @app.post("/test")
    def test_endpoint():
        return {"status": "ok", "timestamp": time.time()}
    
    return app


def measure_performance(client: TestClient, iterations: int = 1000) -> Dict[str, float]:
    """
    测量性能指标
    
    Returns:
        字典包含: mean, median, min, max, p95, p99
    """
    times: List[float] = []
    
    # 预热
    for _ in range(10):
        client.post("/test")
    
    # 实际测试
    for _ in range(iterations):
        start = time.perf_counter()
        response = client.post("/test")
        duration = (time.perf_counter() - start) * 1000  # 转换为毫秒
        
        if response.status_code == 200:
            times.append(duration)
    
    # 计算统计指标
    times_sorted = sorted(times)
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "p95": times_sorted[int(len(times_sorted) * 0.95)],
        "p99": times_sorted[int(len(times_sorted) * 0.99)],
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
    }


def format_result(name: str, result: Dict[str, float], baseline: Dict[str, float] = None) -> None:
    """格式化并打印结果"""
    print(f"\n{'=' * 80}")
    print(f"{name}")
    print(f"{'=' * 80}")
    
    metrics = [
        ("平均耗时", "mean"),
        ("中位数", "median"),
        ("最小值", "min"),
        ("最大值", "max"),
        ("P95", "p95"),
        ("P99", "p99"),
        ("标准差", "stdev"),
    ]
    
    for label, key in metrics:
        value = result[key]
        
        # 计算与baseline的差异
        if baseline and key in baseline:
            diff = value - baseline[key]
            diff_pct = (diff / baseline[key] * 100) if baseline[key] > 0 else 0
            diff_str = f" ({diff:+.2f}ms, {diff_pct:+.1f}%)"
        else:
            diff_str = ""
        
        # 根据值大小选择颜色标记
        if value < 3.0:
            marker = "✅"
        elif value < 5.0:
            marker = "⚠️"
        else:
            marker = "❌"
        
        print(f"{marker} {label:10s}: {value:6.2f}ms{diff_str}")


def check_performance_requirement(result: Dict[str, float], max_mean: float = 5.0) -> bool:
    """
    检查是否满足性能要求
    
    Args:
        result: 性能测试结果
        max_mean: 最大允许平均耗时（毫秒）
    
    Returns:
        是否满足要求
    """
    return result["mean"] < max_mean and result["p99"] < max_mean * 2


def main():
    """主测试函数"""
    print("=" * 80)
    print("Rate Limiter 性能测试")
    print("=" * 80)
    print(f"测试迭代次数: 1000")
    print(f"性能要求: 平均耗时 < 5ms")
    print("=" * 80)
    
    # 测试1: 无rate limiter（baseline）
    print("\n正在测试: 无 Rate Limiter (baseline)...")
    app_without = create_app_without_limiter()
    client_without = TestClient(app_without)
    result_without = measure_performance(client_without)
    format_result("测试1: 无 Rate Limiter (基准)", result_without)
    
    # 测试2: 启用rate limiter
    print("\n正在测试: 启用 Rate Limiter...")
    app_with = create_app_with_limiter()
    client_with = TestClient(app_with)
    result_with = measure_performance(client_with)
    format_result("测试2: 启用 Rate Limiter", result_with, result_without)
    
    # 性能评估
    print(f"\n{'=' * 80}")
    print("性能评估")
    print(f"{'=' * 80}")
    
    overhead = result_with["mean"] - result_without["mean"]
    overhead_pct = (overhead / result_without["mean"] * 100)
    
    print(f"\n性能开销:")
    print(f"  平均耗时增加: {overhead:.2f}ms ({overhead_pct:.1f}%)")
    print(f"  P99耗时增加: {result_with['p99'] - result_without['p99']:.2f}ms")
    
    # 判断是否达标
    if check_performance_requirement(result_with):
        print(f"\n✅ 性能测试通过！平均耗时 {result_with['mean']:.2f}ms < 5ms")
    else:
        print(f"\n❌ 性能测试未通过！平均耗时 {result_with['mean']:.2f}ms >= 5ms")
    
    # 建议
    print(f"\n{'=' * 80}")
    print("建议")
    print(f"{'=' * 80}")
    
    if result_with["mean"] < 3.0:
        print("✅ 性能优秀，可以在生产环境使用")
    elif result_with["mean"] < 5.0:
        print("⚠️  性能良好，建议使用本地Redis以进一步优化")
    else:
        print("❌ 性能不足，建议:")
        print("   1. 使用本地Redis替代远程Redis")
        print("   2. 在开发环境使用内存存储")
        print("   3. 仅对敏感endpoint启用限流")
    
    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
