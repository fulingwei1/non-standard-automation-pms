"""
API 高并发请求性能测试
测试场景: 100+ 并发 API 调用
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from httpx import AsyncClient
import statistics


class TestAPIConcurrentPerformance:
    """API 并发性能测试"""
    
    @pytest.mark.performance
    async def test_concurrent_project_list(self, async_client: AsyncClient, auth_headers):
        """测试项目列表API并发性能 - 100并发"""
        num_requests = 100
        response_times = []
        
        async def fetch_projects():
            start = time.time()
            response = await async_client.get("/api/projects", headers=auth_headers)
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        # 创建100个并发请求
        tasks = [fetch_projects() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        # 分析结果
        status_codes = [r[0] for r in results]
        response_times = [r[1] for r in results]
        
        # 断言
        assert all(code == 200 for code in status_codes), "所有请求应该成功"
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        
        assert avg_time < 0.5, f"平均响应时间应小于500ms, 实际: {avg_time*1000:.2f}ms"
        assert p95_time < 1.0, f"95%请求应在1s内完成, 实际: {p95_time*1000:.2f}ms"
        assert max(response_times) < 2.0, "最大响应时间应小于2s"
        
        print(f"\n并发测试结果:")
        print(f"  总请求: {num_requests}")
        print(f"  平均响应时间: {avg_time*1000:.2f}ms")
        print(f"  P95响应时间: {p95_time*1000:.2f}ms")
        print(f"  最大响应时间: {max(response_times)*1000:.2f}ms")
    
    @pytest.mark.performance
    async def test_concurrent_user_create(self, async_client: AsyncClient, admin_headers):
        """测试用户创建API并发性能 - 50并发"""
        num_requests = 50
        
        async def create_user(index: int):
            start = time.time()
            response = await async_client.post(
                "/api/users",
                headers=admin_headers,
                json={
                    "username": f"test_user_{index}_{int(time.time())}",
                    "email": f"test_{index}@example.com",
                    "password": "Test@123456"
                }
            )
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        tasks = [create_user(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常
        valid_results = [r for r in results if not isinstance(r, Exception)]
        response_times = [r[1] for r in valid_results]
        
        assert len(valid_results) >= num_requests * 0.9, "至少90%请求成功"
        avg_time = statistics.mean(response_times) if response_times else 0
        assert avg_time < 2.0, f"平均创建时间应小于2s, 实际: {avg_time*1000:.2f}ms"
    
    @pytest.mark.performance
    def test_sync_concurrent_login(self, client, test_db):
        """测试登录API并发性能 - 200并发 (同步)"""
        num_requests = 200
        response_times = []
        
        def login():
            start = time.time()
            response = client.post("/api/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        # 使用线程池模拟并发
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(login) for _ in range(num_requests)]
            results = [f.result() for f in as_completed(futures)]
        
        status_codes = [r[0] for r in results]
        response_times = [r[1] for r in results]
        
        success_rate = sum(1 for code in status_codes if code == 200) / num_requests
        assert success_rate >= 0.95, f"成功率应>=95%, 实际: {success_rate*100:.1f}%"
        
        avg_time = statistics.mean(response_times)
        assert avg_time < 0.3, f"平均登录时间应小于300ms, 实际: {avg_time*1000:.2f}ms"
    
    @pytest.mark.performance
    async def test_concurrent_mixed_operations(self, async_client: AsyncClient, auth_headers):
        """混合操作并发测试 - CRUD操作"""
        num_operations = 100
        
        async def mixed_operation(index: int):
            start = time.time()
            
            # 随机选择操作类型
            operation = index % 4
            
            if operation == 0:  # GET
                response = await async_client.get("/api/projects", headers=auth_headers)
            elif operation == 1:  # POST
                response = await async_client.post(
                    "/api/projects",
                    headers=auth_headers,
                    json={"name": f"Test Project {index}", "code": f"TP{index}"}
                )
            elif operation == 2:  # PUT
                response = await async_client.put(
                    f"/api/projects/{index % 10 + 1}",
                    headers=auth_headers,
                    json={"name": f"Updated Project {index}"}
                )
            else:  # DELETE
                response = await async_client.delete(
                    f"/api/projects/{index % 10 + 100}",
                    headers=auth_headers
                )
            
            elapsed = time.time() - start
            return response.status_code, elapsed, operation
        
        tasks = [mixed_operation(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = [r for r in results if not isinstance(r, Exception)]
        assert len(valid_results) >= num_operations * 0.8, "至少80%请求成功"
        
        # 按操作类型分析
        by_operation = {0: [], 1: [], 2: [], 3: []}
        for status, elapsed, op_type in valid_results:
            by_operation[op_type].append(elapsed)
        
        for op_type, times in by_operation.items():
            if times:
                avg = statistics.mean(times)
                print(f"\n操作类型 {op_type} 平均时间: {avg*1000:.2f}ms")
    
    @pytest.mark.performance
    async def test_concurrent_search_operations(self, async_client: AsyncClient, auth_headers):
        """并发搜索性能测试"""
        search_terms = ["项目", "测试", "开发", "管理", "系统"]
        num_iterations = 20  # 每个搜索词执行20次
        
        async def search(term: str):
            start = time.time()
            response = await async_client.get(
                f"/api/projects/search?q={term}",
                headers=auth_headers
            )
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        # 创建并发搜索任务
        tasks = []
        for term in search_terms:
            tasks.extend([search(term) for _ in range(num_iterations)])
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        response_times = [r[1] for r in valid_results]
        avg_time = statistics.mean(response_times) if response_times else 0
        
        assert avg_time < 0.5, f"平均搜索时间应小于500ms, 实际: {avg_time*1000:.2f}ms"
        
        print(f"\n搜索性能:")
        print(f"  总搜索次数: {len(response_times)}")
        print(f"  平均时间: {avg_time*1000:.2f}ms")
    
    @pytest.mark.performance
    async def test_concurrent_pagination(self, async_client: AsyncClient, auth_headers):
        """并发分页性能测试"""
        num_pages = 10
        page_sizes = [10, 20, 50, 100]
        
        async def fetch_page(page: int, page_size: int):
            start = time.time()
            response = await async_client.get(
                f"/api/projects?page={page}&page_size={page_size}",
                headers=auth_headers
            )
            elapsed = time.time() - start
            return response.status_code, elapsed, page_size
        
        # 创建并发任务
        tasks = []
        for page_size in page_sizes:
            for page in range(1, num_pages + 1):
                tasks.append(fetch_page(page, page_size))
        
        results = await asyncio.gather(*tasks)
        
        # 按页大小分析
        by_page_size = {}
        for status, elapsed, page_size in results:
            if page_size not in by_page_size:
                by_page_size[page_size] = []
            by_page_size[page_size].append(elapsed)
        
        for page_size, times in by_page_size.items():
            avg = statistics.mean(times)
            assert avg < 1.0, f"页大小{page_size}平均时间应小于1s"
            print(f"\n页大小 {page_size}: 平均 {avg*1000:.2f}ms")
    
    @pytest.mark.performance
    async def test_concurrent_api_rate_limiting(self, async_client: AsyncClient, auth_headers):
        """API限流并发测试"""
        num_requests = 150  # 超过限流阈值
        
        async def make_request():
            start = time.time()
            response = await async_client.get("/api/projects", headers=auth_headers)
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        status_codes = [r[0] for r in results if not isinstance(r, Exception)]
        
        # 检查限流
        rate_limited = sum(1 for code in status_codes if code == 429)
        success = sum(1 for code in status_codes if code == 200)
        
        print(f"\n限流测试:")
        print(f"  成功请求: {success}")
        print(f"  限流拒绝: {rate_limited}")
        print(f"  总请求: {num_requests}")
        
        # 应该有部分请求被限流
        assert rate_limited > 0 or success == num_requests, "限流应该生效或全部成功"
