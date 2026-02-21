"""
微服务性能测试
"""
import pytest
import time
import statistics


class TestMicroservicePerformance:
    """微服务性能测试"""
    
    @pytest.mark.performance
    def test_service_to_service_latency(self, client, auth_headers):
        """测试服务间延迟"""
        times = []
        
        for _ in range(30):
            start = time.time()
            # 调用需要跨服务的接口
            response = client.get("/api/reports/generate/1", headers=auth_headers)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        p95 = statistics.quantiles(times, n=20)[18]
        
        print(f"\n服务间调用:")
        print(f"  平均: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95*1000:.2f}ms")
        
        assert avg_time < 1.0, "服务间调用应<1s"
    
    @pytest.mark.performance
    def test_service_timeout_handling(self, client, auth_headers):
        """测试服务超时处理"""
        start = time.time()
        response = client.get(
            "/api/external/slow-service",
            headers=auth_headers,
            timeout=5
        )
        elapsed = time.time() - start
        
        # 应该在合理时间内超时或返回
        assert elapsed < 6, "应该正确处理超时"
