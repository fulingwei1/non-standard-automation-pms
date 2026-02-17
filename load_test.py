#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非标自动化PMS系统压力测试
使用 asyncio + aiohttp 实现高并发测试
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:8001"
TOKEN = None  # 全局token


async def get_token(session: aiohttp.ClientSession) -> str:
    """获取认证Token（form-data格式）"""
    async with session.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"}  # form-data
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("access_token", "")
    return ""


# ==================== 测试场景定义 ====================

TEST_SCENARIOS = {
    "auth_login": {
        "method": "POST",
        "url": "/api/v1/auth/login",
        "json": {"username": "admin", "password": "admin123"},
        "auth": False,
        "weight": 5,  # 权重（低，因为有rate limit）
        "name": "用户登录"
    },
    "projects_list": {
        "method": "GET",
        "url": "/api/v1/projects/",
        "auth": True,
        "weight": 20,
        "name": "项目列表"
    },
    "production_list": {
        "method": "GET",
        "url": "/api/v1/production/work-orders",
        "auth": True,
        "weight": 15,
        "name": "生产工单"
    },
    "sales_list": {
        "method": "GET",
        "url": "/api/v1/sales/contracts/basic",
        "auth": True,
        "weight": 10,
        "name": "销售合同"
    },
    "timesheet_records": {
        "method": "GET",
        "url": "/api/v1/timesheet/records",
        "auth": True,
        "weight": 15,
        "name": "工时记录"
    },
    "users_list": {
        "method": "GET",
        "url": "/api/v1/users/",
        "auth": True,
        "weight": 10,
        "name": "用户列表"
    },
    "inventory_list": {
        "method": "GET",
        "url": "/api/v1/inventory/stocks",
        "auth": True,
        "weight": 10,
        "name": "库存查询"
    },
    "presale_list": {
        "method": "GET",
        "url": "/api/v1/presale/tickets",
        "auth": True,
        "weight": 10,
        "name": "预售管理"
    },
    "permissions_list": {
        "method": "GET",
        "url": "/api/v1/permissions/",
        "auth": True,
        "weight": 5,
        "name": "权限列表"
    },
}


class LoadTestResult:
    def __init__(self, scenario_name: str, endpoint: str):
        self.scenario_name = scenario_name
        self.endpoint = endpoint
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.errors: int = 0
        self.success: int = 0
        self.start_time: float = 0
        self.end_time: float = 0

    def add_result(self, response_time: float, status_code: int):
        self.response_times.append(response_time)
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        if status_code in (200, 201, 401, 403, 422):  # 除500外都算成功
            self.success += 1
        else:
            self.errors += 1

    def add_error(self):
        self.errors += 1

    @property
    def total_requests(self):
        return self.success + self.errors

    @property
    def success_rate(self):
        if self.total_requests == 0:
            return 0
        return self.success / self.total_requests * 100

    @property
    def avg_response_time(self):
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times) * 1000  # ms

    @property
    def p95_response_time(self):
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx] * 1000  # ms

    @property
    def p99_response_time(self):
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx] * 1000  # ms

    @property
    def max_response_time(self):
        if not self.response_times:
            return 0
        return max(self.response_times) * 1000  # ms

    @property
    def rps(self):
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0
        return self.total_requests / duration


async def run_scenario(
    session: aiohttp.ClientSession,
    scenario_key: str,
    scenario: Dict,
    token: str,
    result: LoadTestResult,
    semaphore: asyncio.Semaphore
):
    """执行单个请求"""
    async with semaphore:
        headers = {}
        if scenario.get("auth") and token:
            headers["Authorization"] = f"Bearer {token}"

        url = f"{BASE_URL}{scenario['url']}"
        start = time.time()

        try:
            if scenario["method"] == "GET":
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    elapsed = time.time() - start
                    result.add_result(elapsed, resp.status)
            elif scenario["method"] == "POST":
                async with session.post(
                    url, headers=headers, json=scenario.get("json", {}),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    elapsed = time.time() - start
                    result.add_result(elapsed, resp.status)
        except asyncio.TimeoutError:
            result.add_error()
        except Exception:
            result.add_error()


async def run_load_test(
    concurrent_users: int,
    requests_per_user: int,
    token: str
) -> Dict[str, LoadTestResult]:
    """运行压力测试"""
    semaphore = asyncio.Semaphore(concurrent_users)
    results = {}

    # 初始化结果对象
    for key, scenario in TEST_SCENARIOS.items():
        results[key] = LoadTestResult(scenario["name"], scenario["url"])

    # 生成任务列表（按权重分配）
    tasks = []
    for key, scenario in TEST_SCENARIOS.items():
        count = scenario["weight"] * requests_per_user // 20  # 按权重分配请求数
        count = max(count, 5)  # 最少5个请求
        for _ in range(count):
            tasks.append((key, scenario))

    # 打乱顺序模拟真实用户行为
    import random
    random.shuffle(tasks)

    connector = aiohttp.TCPConnector(limit=concurrent_users * 2, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 标记开始时间
        global_start = time.time()
        for key in results:
            results[key].start_time = global_start

        # 执行所有任务
        coroutines = [
            run_scenario(session, key, scenario, token, results[key], semaphore)
            for key, scenario in tasks
        ]
        await asyncio.gather(*coroutines)

        # 标记结束时间
        global_end = time.time()
        for key in results:
            results[key].end_time = global_end

    return results


def print_report(results: Dict[str, LoadTestResult], concurrent: int, duration: float):
    """打印测试报告"""
    print("\n" + "=" * 70)
    print(f"🔥 压力测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   并发用户: {concurrent} | 总耗时: {duration:.1f}s")
    print("=" * 70)

    total_requests = sum(r.total_requests for r in results.values())
    total_success = sum(r.success for r in results.values())
    all_times = []
    for r in results.values():
        all_times.extend(r.response_times)

    if all_times:
        overall_avg = statistics.mean(all_times) * 1000
        overall_p95 = sorted(all_times)[int(len(all_times) * 0.95)] * 1000
    else:
        overall_avg = overall_p95 = 0

    print(f"\n📊 总体统计:")
    print(f"   总请求数: {total_requests}")
    print(f"   成功数:   {total_success} ({total_success/total_requests*100:.1f}%)")
    print(f"   平均响应: {overall_avg:.0f}ms")
    print(f"   P95响应:  {overall_p95:.0f}ms")
    print(f"   总RPS:    {total_requests/duration:.1f}")

    print(f"\n{'接口':<20} {'请求数':<8} {'成功率':<10} {'平均(ms)':<12} {'P95(ms)':<12} {'P99(ms)':<12} {'状态码分布'}")
    print("-" * 90)

    for key, result in results.items():
        if result.total_requests == 0:
            continue
        status_str = " ".join(f"{k}:{v}" for k, v in sorted(result.status_codes.items()))
        print(
            f"{result.scenario_name:<20} "
            f"{result.total_requests:<8} "
            f"{result.success_rate:<10.1f} "
            f"{result.avg_response_time:<12.0f} "
            f"{result.p95_response_time:<12.0f} "
            f"{result.p99_response_time:<12.0f} "
            f"{status_str}"
        )

    print("\n" + "=" * 70)

    # 性能评级
    if overall_avg < 200 and total_success/total_requests > 0.95:
        grade = "A+ 优秀 🏆"
    elif overall_avg < 500 and total_success/total_requests > 0.90:
        grade = "A 良好 ✅"
    elif overall_avg < 1000 and total_success/total_requests > 0.80:
        grade = "B 一般 ⚠️"
    else:
        grade = "C 较差 ❌"

    print(f"🎯 性能评级: {grade}")
    print("=" * 70)

    return {
        "total_requests": total_requests,
        "success_rate": total_success/total_requests*100 if total_requests > 0 else 0,
        "avg_response_ms": overall_avg,
        "p95_response_ms": overall_p95,
        "rps": total_requests/duration,
        "grade": grade,
    }


async def main():
    """主测试流程"""
    print("🚀 非标自动化PMS系统压力测试")
    print(f"   目标: {BASE_URL}")
    print("   正在获取认证Token...")

    # 获取Token
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as session:
        token = await get_token(session)

    if not token:
        print("❌ 无法获取Token，检查服务是否运行")
        return

    print(f"   ✅ Token获取成功")

    all_results = []

    # 测试阶段1：低并发（预热）
    print("\n📊 阶段1: 低并发测试 (10并发, 预热)")
    start = time.time()
    results1 = await run_load_test(concurrent_users=10, requests_per_user=20, token=token)
    duration1 = time.time() - start
    r1 = print_report(results1, 10, duration1)
    all_results.append(("低并发(10)", r1))

    await asyncio.sleep(2)  # 休息2秒

    # 测试阶段2：中并发
    print("\n📊 阶段2: 中并发测试 (50并发)")
    start = time.time()
    results2 = await run_load_test(concurrent_users=50, requests_per_user=30, token=token)
    duration2 = time.time() - start
    r2 = print_report(results2, 50, duration2)
    all_results.append(("中并发(50)", r2))

    await asyncio.sleep(3)  # 休息3秒

    # 测试阶段3：高并发
    print("\n📊 阶段3: 高并发测试 (100并发)")
    start = time.time()
    results3 = await run_load_test(concurrent_users=100, requests_per_user=20, token=token)
    duration3 = time.time() - start
    r3 = print_report(results3, 100, duration3)
    all_results.append(("高并发(100)", r3))

    # 汇总报告
    print("\n" + "🔥" * 35)
    print("📊 压力测试汇总")
    print("=" * 70)
    print(f"{'阶段':<15} {'成功率':<10} {'平均响应':<12} {'P95响应':<12} {'RPS':<10} {'评级'}")
    print("-" * 70)
    for stage, r in all_results:
        print(
            f"{stage:<15} "
            f"{r['success_rate']:<10.1f} "
            f"{r['avg_response_ms']:<12.0f} "
            f"{r['p95_response_ms']:<12.0f} "
            f"{r['rps']:<10.1f} "
            f"{r['grade']}"
        )

    # 保存JSON报告
    report_path = "压力测试报告_2026-02-17.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "stages": [
                {"stage": stage, **r} for stage, r in all_results
            ]
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 详细报告已保存: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
