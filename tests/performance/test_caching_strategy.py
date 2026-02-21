"""
缓存策略性能测试
"""
import pytest
import time
import statistics


class TestCachingStrategy:
    """缓存策略测试"""
    
    @pytest.mark.performance
    async def test_cache_aside_pattern(self, client, redis_client, auth_headers):
        """测试Cache-Aside模式"""
        project_id = 1
        cache_key = f"project:{project_id}"
        
        # 第一次请求 - 缓存未命中
        start = time.time()
        response1 = client.get(f"/api/projects/{project_id}", headers=auth_headers)
        time1 = time.time() - start
        
        # 第二次请求 - 缓存命中
        start = time.time()
        response2 = client.get(f"/api/projects/{project_id}", headers=auth_headers)
        time2 = time.time() - start
        
        print(f"\nCache-Aside:")
        print(f"  未命中: {time1*1000:.2f}ms")
        print(f"  命中: {time2*1000:.2f}ms")
        print(f"  提升: {time1/time2:.1f}x")
        
        assert time2 < time1, "缓存应该更快"
    
    @pytest.mark.performance
    def test_cache_ttl_performance(self, client, auth_headers):
        """测试缓存TTL性能"""
        times = []
        
        for i in range(50):
            start = time.time()
            response = client.get("/api/projects/1", headers=auth_headers)
            elapsed = time.time() - start
            times.append(elapsed)
            
            if i == 25:
                # 中途清理缓存
                time.sleep(0.1)
        
        first_half = statistics.mean(times[:25])
        second_half = statistics.mean(times[25:])
        
        print(f"\nTTL测试:")
        print(f"  前半: {first_half*1000:.2f}ms")
        print(f"  后半: {second_half*1000:.2f}ms")
    
    @pytest.mark.performance
    def test_cache_warming(self, client, auth_headers):
        """测试缓存预热"""
        # 预热常用数据
        common_ids = [1, 2, 3, 4, 5]
        
        start = time.time()
        for pid in common_ids:
            client.get(f"/api/projects/{pid}", headers=auth_headers)
        warming_time = time.time() - start
        
        # 测试预热后的性能
        times = []
        for pid in common_ids:
            start = time.time()
            response = client.get(f"/api/projects/{pid}", headers=auth_headers)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        
        print(f"\n缓存预热:")
        print(f"  预热时间: {warming_time*1000:.2f}ms")
        print(f"  平均命中: {avg_time*1000:.2f}ms")
        
        assert avg_time < 0.1, "预热后访问应很快"
