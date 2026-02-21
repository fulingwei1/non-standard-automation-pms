"""
API网关性能测试
"""
import pytest
import time
import statistics


class TestAPIGatewayPerformance:
    """API网关性能测试"""
    
    @pytest.mark.performance
    def test_gateway_routing_performance(self, client):
        """测试网关路由性能"""
        endpoints = [
            "/api/projects",
            "/api/users",
            "/api/reports",
            "/api/tasks"
        ]
        
        times = {}
        for endpoint in endpoints:
            endpoint_times = []
            for _ in range(30):
                start = time.time()
                response = client.get(endpoint)
                elapsed = time.time() - start
                endpoint_times.append(elapsed)
            
            times[endpoint] = statistics.mean(endpoint_times)
        
        for endpoint, avg_time in times.items():
            print(f"{endpoint}: {avg_time*1000:.2f}ms")
            assert avg_time < 0.1, f"路由应<100ms"
    
    @pytest.mark.performance
    def test_gateway_load_balancing(self, client):
        """测试负载均衡性能"""
        num_requests = 100
        times = []
        
        for _ in range(num_requests):
            start = time.time()
            response = client.get("/api/projects")
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times)
        
        print(f"\n负载均衡测试:")
        print(f"  平均: {avg_time*1000:.2f}ms")
        print(f"  标准差: {std_dev*1000:.2f}ms")
        
        # 标准差应该较小,表示负载均衡良好
        assert std_dev < avg_time * 0.5, "响应时间波动过大"
