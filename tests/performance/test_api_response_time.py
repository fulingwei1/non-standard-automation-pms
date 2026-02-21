"""
API响应时间性能测试
"""
import pytest
import time
import statistics


class TestAPIResponseTime:
    """API响应时间测试"""
    
    @pytest.mark.performance
    def test_list_apis_response_time(self, client, auth_headers):
        """列表API响应时间"""
        endpoints = [
            "/api/projects",
            "/api/users",
            "/api/tasks",
            "/api/reports"
        ]
        
        for endpoint in endpoints:
            times = []
            for _ in range(20):
                start = time.time()
                response = client.get(endpoint, headers=auth_headers)
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            p95 = statistics.quantiles(times, n=20)[18]
            
            print(f"\n{endpoint}:")
            print(f"  平均: {avg_time*1000:.2f}ms")
            print(f"  P95: {p95*1000:.2f}ms")
            
            assert avg_time < 0.3, f"{endpoint}应<300ms"
            assert p95 < 0.5, f"{endpoint} P95应<500ms"
    
    @pytest.mark.performance
    def test_detail_apis_response_time(self, client, auth_headers):
        """详情API响应时间"""
        endpoints = [
            "/api/projects/1",
            "/api/users/1",
            "/api/tasks/1"
        ]
        
        for endpoint in endpoints:
            times = []
            for _ in range(30):
                start = time.time()
                response = client.get(endpoint, headers=auth_headers)
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            assert avg_time < 0.2, f"{endpoint}应<200ms"
    
    @pytest.mark.performance
    def test_create_apis_response_time(self, client, auth_headers):
        """创建API响应时间"""
        times = []
        
        for i in range(20):
            start = time.time()
            response = client.post(
                "/api/projects",
                json={
                    "name": f"Perf Test Project {i}",
                    "code": f"PTP{i:04d}"
                },
                headers=auth_headers
            )
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        assert avg_time < 0.5, "创建API应<500ms"
