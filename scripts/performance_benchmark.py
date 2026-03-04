#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试

对比优化前后的性能差异
"""

import json
import os
import statistics

# 添加项目路径
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.alert import AlertRecord
from app.models.base import get_db_session
from app.models.project import Project
from app.services.cache.business_cache import get_business_cache
from app.services.cache.redis_cache import RedisCacheManager
from app.services.database.query_optimizer import QueryOptimizer


class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self):
        self.results = {}
        self.db = None

    def setup(self):
        """设置测试环境"""
        self.db = get_db_session()
        print("🔧 性能测试环境初始化完成")

    def teardown(self):
        """清理测试环境"""
        if self.db:
            self.db.close()
            print("🔧 性能测试环境清理完成")

    def measure_time(self, func, *args, **kwargs):
        """
        测量函数执行时间

        Returns:
            tuple: (执行时间, 执行结果)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return execution_time, result

    def benchmark_project_list(self, iterations: int = 10):
        """基准测试：项目列表查询"""
        print("\n📊 基准测试：项目列表查询")

        # 测试原始查询
        original_times = []
        for i in range(iterations):

            def original_query():
                return (
                    self.db.query(Project)
                    .options(
                        # 没有优化的原始查询
                    )
                    .limit(100)
                    .all()
                )

            exec_time, _ = self.measure_time(original_query)
            original_times.append(exec_time)
            print(f"  原始查询 {i+1}: {exec_time:.3f}s")

        # 测试优化查询
        optimized_times = []
        optimizer = QueryOptimizer(self.db)
        for i in range(iterations):

            def optimized_query():
                return optimizer.get_project_list_optimized(skip=0, limit=100)

            exec_time, _ = self.measure_time(optimized_query)
            optimized_times.append(exec_time)
            print(f"  优化查询 {i+1}: {exec_time:.3f}s")

        # 测试缓存查询
        cached_times = []
        business_cache = get_business_cache()
        for i in range(iterations):

            def cached_query():
                # 先清除缓存确保第一次查询从数据库获取
                if i == 0:
                    RedisCacheManager.clear_project_cache()

                cached_projects = business_cache.get_project_list(0, 100)
                if cached_projects is None:
                    # 缓存未命中，执行查询并缓存
                    projects = optimizer.get_project_list_optimized(0, 100)
                    business_cache.set_project_list(projects, 0, 100)
                    return projects
                return cached_projects

            exec_time, _ = self.measure_time(cached_query)
            cached_times.append(exec_time)
            print(f"  缓存查询 {i+1}: {exec_time:.3f}s")

        # 计算统计信息
        self.results["project_list"] = {
            "original": {
                "avg": statistics.mean(original_times),
                "min": min(original_times),
                "max": max(original_times),
                "std": statistics.stdev(original_times) if len(original_times) > 1 else 0,
            },
            "optimized": {
                "avg": statistics.mean(optimized_times),
                "min": min(optimized_times),
                "max": max(optimized_times),
                "std": statistics.stdev(optimized_times) if len(optimized_times) > 1 else 0,
            },
            "cached": {
                "avg": statistics.mean(cached_times),
                "min": min(cached_times),
                "max": max(cached_times),
                "std": statistics.stdev(cached_times) if len(cached_times) > 1 else 0,
            },
        }

        # 计算性能提升
        original_avg = self.results["project_list"]["original"]["avg"]
        optimized_avg = self.results["project_list"]["optimized"]["avg"]
        cached_avg = self.results["project_list"]["cached"]["avg"]

        improvement_optimized = ((original_avg - optimized_avg) / original_avg) * 100
        improvement_cached = ((original_avg - cached_avg) / original_avg) * 100

        print("\n📈 性能提升统计:")
        print(f"  原始查询平均时间: {original_avg:.3f}s")
        print(f"  优化查询平均时间: {optimized_avg:.3f}s (提升 {improvement_optimized:.1f}%)")
        print(f"  缓存查询平均时间: {cached_avg:.3f}s (提升 {improvement_cached:.1f}%)")

    def benchmark_alert_statistics(self, iterations: int = 5):
        """基准测试：告警统计查询"""
        print("\n📊 基准测试：告警统计查询")

        # 测试原始统计查询
        original_times = []
        for i in range(iterations):

            def original_stats():
                # 模拟原始的统计查询（可能存在性能问题）
                return (
                    self.db.query(AlertRecord)
                    .filter(AlertRecord.created_at >= datetime.now() - timedelta(days=30))
                    .all()
                )

            exec_time, _ = self.measure_time(original_stats)
            original_times.append(exec_time)
            print(f"  原始统计 {i+1}: {exec_time:.3f}s")

        # 测试优化统计查询
        optimized_times = []
        optimizer = QueryOptimizer(self.db)
        for i in range(iterations):

            def optimized_stats():
                return optimizer.get_alert_statistics_optimized(days=30)

            exec_time, _ = self.measure_time(optimized_stats)
            optimized_times.append(exec_time)
            print(f"  优化统计 {i+1}: {exec_time:.3f}s")

        # 测试缓存统计查询
        cached_times = []
        business_cache = get_business_cache()
        for i in range(iterations):

            def cached_stats():
                stats = business_cache.get_alert_statistics(30)
                if stats is None:
                    stats = optimizer.get_alert_statistics_optimized(30)
                    business_cache.set_alert_statistics(stats, 30)
                return stats

            exec_time, _ = self.measure_time(cached_stats)
            cached_times.append(exec_time)
            print(f"  缓存统计 {i+1}: {exec_time:.3f}s")

        # 计算统计信息
        self.results["alert_statistics"] = {
            "original": {
                "avg": statistics.mean(original_times),
                "min": min(original_times),
                "max": max(original_times),
                "std": statistics.stdev(original_times) if len(original_times) > 1 else 0,
            },
            "optimized": {
                "avg": statistics.mean(optimized_times),
                "min": min(optimized_times),
                "max": max(optimized_times),
                "std": statistics.stdev(optimized_times) if len(optimized_times) > 1 else 0,
            },
            "cached": {
                "avg": statistics.mean(cached_times),
                "min": min(cached_times),
                "max": max(cached_times),
                "std": statistics.stdev(cached_times) if len(cached_times) > 1 else 0,
            },
        }

        # 计算性能提升
        original_avg = self.results["alert_statistics"]["original"]["avg"]
        optimized_avg = self.results["alert_statistics"]["optimized"]["avg"]
        cached_avg = self.results["alert_statistics"]["cached"]["avg"]

        improvement_optimized = ((original_avg - optimized_avg) / original_avg) * 100
        improvement_cached = ((original_avg - cached_avg) / original_avg) * 100

        print("\n📈 告警统计性能提升:")
        print(f"  原始统计平均时间: {original_avg:.3f}s")
        print(f"  优化统计平均时间: {optimized_avg:.3f}s (提升 {improvement_optimized:.1f}%)")
        print(f"  缓存统计平均时间: {cached_avg:.3f}s (提升 {improvement_cached:.1f}%)")

    def benchmark_database_connections(self):
        """基准测试：数据库连接池性能"""
        print("\n📊 基准测试：数据库连接性能")

        connection_times = []
        for i in range(20):

            def test_connection():
                try:
                    with self.db.begin():
                        self.db.execute("SELECT 1")
                    return True
                except Exception:
                    return False

            exec_time, success = self.measure_time(test_connection)
            connection_times.append(exec_time)
            print(f"  连接测试 {i+1}: {exec_time:.3f}s - {'成功' if success else '失败'}")

        avg_time = statistics.mean(connection_times)
        print("\n📈 连接性能统计:")
        print(f"  平均连接时间: {avg_time:.3f}s")
        print(f"  最快连接时间: {min(connection_times):.3f}s")
        print(f"  最慢连接时间: {max(connection_times):.3f}s")

    def benchmark_complexity_reduction(self):
        """基准测试：复杂函数拆分后的性能"""
        print("\n📊 基准测试：函数复杂度优化")

        # 测试重构前的收款计划生成
        print("  测试收款计划生成...")

        try:
            from app.api.v1.endpoints.sales.contracts import (
                _generate_payment_plans_from_contract,
            )
            from app.models.sales import Contract

            # 获取测试合同
            test_contract = self.db.query(Contract).first()
            if test_contract:
                # 测试原始函数（如果存在）
                original_times = []
                for i in range(3):

                    def original_payment():
                        return _generate_payment_plans_from_contract(self.db, test_contract)

                    exec_time, _ = self.measure_time(original_payment)
                    original_times.append(exec_time)
                    print(f"    重构后函数 {i+1}: {exec_time:.3f}s")

                avg_time = statistics.mean(original_times)
                print(f"    平均执行时间: {avg_time:.3f}s")

                self.results["payment_plans"] = {
                    "refactored": {
                        "avg": avg_time,
                        "min": min(original_times),
                        "max": max(original_times),
                    }
                }
        except Exception as e:
            print(f"    收款计划测试跳过: {str(e)}")

    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("🚀 开始性能基准测试")
        print("=" * 50)

        try:
            self.setup()

            # 运行各项测试
            self.benchmark_project_list()
            self.benchmark_alert_statistics()
            self.benchmark_database_connections()
            self.benchmark_complexity_reduction()

            # 生成综合报告
            self.generate_report()

        except Exception as e:
            print(f"❌ 基准测试失败: {str(e)}")
            import traceback

            traceback.print_exc()
        finally:
            self.teardown()

    def generate_report(self):
        """生成性能测试报告"""
        print("\n" + "=" * 50)
        print("📊 性能优化综合报告")
        print("=" * 50)

        if not self.results:
            print("❌ 没有测试结果数据")
            return

        # 生成报告数据
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "summary": self.generate_summary(),
        }

        # 保存报告文件
        report_file = (
            f"performance_benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n📋 详细报告已保存到: {report_file}")

        # 打印总结
        print("\n📈 优化效果总结:")
        for test_name, data in self.results.items():
            if "original" in data and "optimized" in data:
                original_time = data["original"]["avg"]
                optimized_time = data["optimized"]["avg"]
                improvement = ((original_time - optimized_time) / original_time) * 100
                print(
                    f"  {test_name}: 提升 {improvement:.1f}% ({original_time:.3f}s → {optimized_time:.3f}s)"
                )

    def generate_summary(self) -> Dict[str, Any]:
        """生成性能优化总结"""
        summary = {
            "total_tests": len(self.results),
            "significant_improvements": 0,
            "overall_improvement": 0,
        }

        total_improvement = 0
        test_count = 0

        for test_name, data in self.results.items():
            if "original" in data and "optimized" in data:
                original_time = data["original"]["avg"]
                optimized_time = data["optimized"]["avg"]
                improvement = ((original_time - optimized_time) / original_time) * 100

                total_improvement += improvement
                test_count += 1

                if improvement > 10:  # 超过10%认为显著改进
                    summary["significant_improvements"] += 1

        if test_count > 0:
            summary["overall_improvement"] = total_improvement / test_count

        return summary


def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    benchmark.run_all_benchmarks()


if __name__ == "__main__":
    main()
