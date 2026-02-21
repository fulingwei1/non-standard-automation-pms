"""
批量操作性能测试
"""
import pytest
import time


class TestBatchOperations:
    """批量操作性能测试"""
    
    @pytest.mark.performance
    def test_batch_create(self, client, auth_headers):
        """批量创建性能"""
        batch_sizes = [10, 50, 100, 200]
        
        for size in batch_sizes:
            data = [
                {"name": f"Project {i}", "code": f"P{i:05d}"}
                for i in range(size)
            ]
            
            start = time.time()
            response = client.post(
                "/api/projects/batch",
                json={"items": data},
                headers=auth_headers
            )
            elapsed = time.time() - start
            
            per_item = (elapsed / size) * 1000
            print(f"\n批量创建 {size}条: {elapsed:.2f}s ({per_item:.2f}ms/条)")
            
            assert per_item < 50, f"单条应<50ms"
    
    @pytest.mark.performance
    def test_batch_update(self, client, auth_headers):
        """批量更新性能"""
        ids = list(range(1, 101))
        
        start = time.time()
        response = client.put(
            "/api/projects/batch",
            json={
                "ids": ids,
                "data": {"status": "updated"}
            },
            headers=auth_headers
        )
        elapsed = time.time() - start
        
        per_item = (elapsed / len(ids)) * 1000
        print(f"\n批量更新 {len(ids)}条: {per_item:.2f}ms/条")
        
        assert per_item < 30, "单条更新应<30ms"
    
    @pytest.mark.performance
    def test_batch_delete(self, client, auth_headers):
        """批量删除性能"""
        ids = list(range(100, 200))
        
        start = time.time()
        response = client.delete(
            "/api/projects/batch",
            json={"ids": ids},
            headers=auth_headers
        )
        elapsed = time.time() - start
        
        per_item = (elapsed / len(ids)) * 1000
        assert per_item < 20, "单条删除应<20ms"
