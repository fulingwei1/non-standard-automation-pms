"""
内存性能测试
"""
import pytest
import time
import psutil
import os


class TestMemoryPerformance:
    """内存性能测试"""
    
    @pytest.mark.performance
    def test_memory_leak_detection(self, client, auth_headers):
        """测试内存泄漏"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量请求
        for _ in range(1000):
            response = client.get("/api/projects", headers=auth_headers)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n内存测试:")
        print(f"  初始: {initial_memory:.2f}MB")
        print(f"  最终: {final_memory:.2f}MB")
        print(f"  增长: {memory_increase:.2f}MB")
        
        assert memory_increase < 100, "内存增长不应超过100MB"
    
    @pytest.mark.performance
    def test_large_payload_memory(self, client, auth_headers):
        """测试大负载内存处理"""
        large_data = {"data": "x" * 1000000}  # 1MB数据
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        response = client.post(
            "/api/data/process",
            json=large_data,
            headers=auth_headers
        )
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_used = final_memory - initial_memory
        
        print(f"\n大负载内存: {memory_used:.2f}MB")
        assert memory_used < 50, "处理1MB数据不应使用超过50MB内存"
