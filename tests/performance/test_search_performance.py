"""
搜索性能测试
"""
import pytest
import time
import statistics


class TestSearchPerformance:
    """搜索性能测试"""
    
    @pytest.mark.performance
    def test_fulltext_search_performance(self, client, auth_headers, test_db):
        """全文搜索性能测试"""
        search_terms = ["项目", "测试", "开发", "管理", "系统"]
        
        for term in search_terms:
            times = []
            for _ in range(20):
                start = time.time()
                response = client.get(
                    f"/api/projects/search?q={term}",
                    headers=auth_headers
                )
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            print(f"\n搜索 '{term}': {avg_time*1000:.2f}ms")
            assert avg_time < 0.3, f"搜索应<300ms"
    
    @pytest.mark.performance
    def test_fuzzy_search_performance(self, client, auth_headers):
        """模糊搜索性能测试"""
        times = []
        
        for i in range(50):
            start = time.time()
            response = client.get(
                f"/api/projects/search?q=test&fuzzy=true",
                headers=auth_headers
            )
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        assert avg_time < 0.5, "模糊搜索应<500ms"
    
    @pytest.mark.performance
    def test_multi_field_search_performance(self, client, auth_headers):
        """多字段搜索性能"""
        times = []
        
        for i in range(30):
            start = time.time()
            response = client.post(
                "/api/search",
                json={
                    "name": "test",
                    "code": "TP",
                    "status": "active"
                },
                headers=auth_headers
            )
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        assert avg_time < 0.4, "多字段搜索应<400ms"
    
    @pytest.mark.performance
    def test_search_result_pagination(self, client, auth_headers):
        """搜索结果分页性能"""
        for page in [1, 5, 10, 20]:
            start = time.time()
            response = client.get(
                f"/api/projects/search?q=test&page={page}&page_size=20",
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            print(f"  第{page}页: {elapsed*1000:.2f}ms")
            assert elapsed < 0.5, f"第{page}页搜索应<500ms"
    
    @pytest.mark.performance
    def test_search_with_filters(self, client, auth_headers):
        """带过滤器的搜索性能"""
        filters = {
            "status": ["active", "pending"],
            "budget_min": 10000,
            "budget_max": 100000
        }
        
        times = []
        for _ in range(30):
            start = time.time()
            response = client.post(
                "/api/projects/search",
                json={"q": "test", "filters": filters},
                headers=auth_headers
            )
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        assert avg_time < 0.5, "带过滤器搜索应<500ms"
