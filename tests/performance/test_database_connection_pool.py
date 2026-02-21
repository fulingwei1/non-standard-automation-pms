"""
数据库连接池性能测试
"""
import pytest
import time
import asyncio
from sqlalchemy import select
from app.models.project import Project


class TestDatabaseConnectionPool:
    """数据库连接池测试"""
    
    @pytest.mark.performance
    async def test_connection_pool_size(self, test_db):
        """测试连接池大小"""
        async def query():
            return test_db.query(Project).limit(10).all()
        
        # 并发执行多个查询
        tasks = [query() for _ in range(50)]
        start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start
        
        errors = [r for r in results if isinstance(r, Exception)]
        
        print(f"\n连接池测试 (50并发):")
        print(f"  时间: {elapsed:.2f}s")
        print(f"  错误: {len(errors)}")
        
        assert len(errors) == 0, "不应该有连接池耗尽"
        assert elapsed < 2.0, "应在2s内完成"
    
    @pytest.mark.performance
    def test_connection_acquisition_time(self, test_db):
        """测试连接获取时间"""
        times = []
        
        for _ in range(100):
            start = time.time()
            conn = test_db.connection()
            elapsed = time.time() - start
            times.append(elapsed)
            conn.close()
        
        import statistics
        avg_time = statistics.mean(times)
        
        print(f"\n连接获取平均时间: {avg_time*1000:.2f}ms")
        assert avg_time < 0.01, "连接获取应<10ms"
    
    @pytest.mark.performance
    def test_connection_leak_detection(self, test_db):
        """测试连接泄漏检测"""
        initial_connections = len(test_db.bind.pool._pool._queue.queue)
        
        # 执行一些操作
        for _ in range(50):
            projects = test_db.query(Project).limit(10).all()
        
        final_connections = len(test_db.bind.pool._pool._queue.queue)
        
        # 连接数不应该增长
        assert final_connections == initial_connections, "可能存在连接泄漏"
