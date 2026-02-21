"""
Redis缓存性能测试
测试场景: 缓存命中率、缓存失效、缓存更新性能
"""
import pytest
import time
import statistics
import json
from typing import List
import asyncio


class TestCachePerformance:
    """缓存性能测试"""
    
    @pytest.mark.performance
    async def test_cache_hit_rate(self, redis_client, test_db):
        """测试缓存命中率"""
        cache_key_prefix = "perf_test_project_"
        num_keys = 1000
        num_reads = 5000
        
        # 预填充缓存
        for i in range(num_keys):
            key = f"{cache_key_prefix}{i}"
            value = json.dumps({"id": i, "name": f"Project {i}", "data": "x" * 100})
            await redis_client.set(key, value, ex=300)
        
        # 测试随机读取
        import random
        hits = 0
        misses = 0
        read_times = []
        
        for _ in range(num_reads):
            key_id = random.randint(0, num_keys + 100)  # 包含一些不存在的key
            key = f"{cache_key_prefix}{key_id}"
            
            start = time.time()
            value = await redis_client.get(key)
            elapsed = time.time() - start
            
            read_times.append(elapsed)
            if value:
                hits += 1
            else:
                misses += 1
        
        hit_rate = hits / num_reads
        avg_read_time = statistics.mean(read_times)
        
        print(f"\n缓存命中率测试:")
        print(f"  总读取: {num_reads}")
        print(f"  命中: {hits}")
        print(f"  未命中: {misses}")
        print(f"  命中率: {hit_rate*100:.2f}%")
        print(f"  平均读取时间: {avg_read_time*1000:.2f}ms")
        
        assert hit_rate >= 0.85, f"命中率应>=85%, 实际: {hit_rate*100:.1f}%"
        assert avg_read_time < 0.01, f"平均读取时间应<10ms, 实际: {avg_read_time*1000:.2f}ms"
        
        # 清理
        for i in range(num_keys):
            await redis_client.delete(f"{cache_key_prefix}{i}")
    
    @pytest.mark.performance
    async def test_cache_write_performance(self, redis_client):
        """测试缓存写入性能"""
        num_writes = 1000
        key_prefix = "perf_write_test_"
        
        # 小数据写入
        small_data = json.dumps({"id": 1, "name": "test"})
        small_times = []
        
        for i in range(num_writes):
            start = time.time()
            await redis_client.set(f"{key_prefix}small_{i}", small_data, ex=60)
            elapsed = time.time() - start
            small_times.append(elapsed)
        
        # 大数据写入
        large_data = json.dumps({"id": 1, "data": "x" * 10000})
        large_times = []
        
        for i in range(num_writes):
            start = time.time()
            await redis_client.set(f"{key_prefix}large_{i}", large_data, ex=60)
            elapsed = time.time() - start
            large_times.append(elapsed)
        
        avg_small = statistics.mean(small_times)
        avg_large = statistics.mean(large_times)
        
        print(f"\n缓存写入性能:")
        print(f"  小数据({len(small_data)}B): {avg_small*1000:.2f}ms")
        print(f"  大数据({len(large_data)}B): {avg_large*1000:.2f}ms")
        
        assert avg_small < 0.01, f"小数据写入应<10ms"
        assert avg_large < 0.02, f"大数据写入应<20ms"
        
        # 清理
        for i in range(num_writes):
            await redis_client.delete(f"{key_prefix}small_{i}")
            await redis_client.delete(f"{key_prefix}large_{i}")
    
    @pytest.mark.performance
    async def test_cache_concurrent_access(self, redis_client):
        """测试缓存并发访问性能"""
        key = "concurrent_test_key"
        value = json.dumps({"data": "test" * 100})
        num_concurrent = 100
        
        # 先设置值
        await redis_client.set(key, value, ex=60)
        
        async def read_cache():
            start = time.time()
            result = await redis_client.get(key)
            elapsed = time.time() - start
            return elapsed, result is not None
        
        # 并发读取
        tasks = [read_cache() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        
        times = [r[0] for r in results]
        successes = sum(1 for r in results if r[1])
        
        avg_time = statistics.mean(times)
        success_rate = successes / num_concurrent
        
        print(f"\n并发缓存访问({num_concurrent}并发):")
        print(f"  成功率: {success_rate*100:.1f}%")
        print(f"  平均时间: {avg_time*1000:.2f}ms")
        print(f"  最大时间: {max(times)*1000:.2f}ms")
        
        assert success_rate == 1.0, "所有读取都应成功"
        assert avg_time < 0.02, f"平均时间应<20ms"
        
        await redis_client.delete(key)
    
    @pytest.mark.performance
    async def test_cache_expiration_performance(self, redis_client):
        """测试缓存过期性能"""
        num_keys = 500
        key_prefix = "exp_test_"
        
        # 批量设置不同过期时间的key
        start = time.time()
        for i in range(num_keys):
            key = f"{key_prefix}{i}"
            value = json.dumps({"id": i})
            expiration = 10 + (i % 50)  # 10-60秒过期
            await redis_client.set(key, value, ex=expiration)
        elapsed = time.time() - start
        
        per_key = (elapsed / num_keys) * 1000
        
        print(f"\n缓存过期设置性能({num_keys}个key):")
        print(f"  总时间: {elapsed*1000:.2f}ms")
        print(f"  单个key平均: {per_key:.2f}ms")
        
        assert per_key < 2.0, f"单个key设置应<2ms"
        
        # 检查TTL性能
        ttl_times = []
        for i in range(100):
            key = f"{key_prefix}{i}"
            start = time.time()
            ttl = await redis_client.ttl(key)
            elapsed = time.time() - start
            ttl_times.append(elapsed)
        
        avg_ttl = statistics.mean(ttl_times)
        print(f"  TTL查询平均: {avg_ttl*1000:.2f}ms")
        
        assert avg_ttl < 0.01, "TTL查询应<10ms"
        
        # 清理
        for i in range(num_keys):
            await redis_client.delete(f"{key_prefix}{i}")
    
    @pytest.mark.performance
    async def test_cache_pipeline_performance(self, redis_client):
        """测试缓存管道性能"""
        num_operations = 1000
        key_prefix = "pipeline_test_"
        
        # 测试非管道模式
        non_pipeline_times = []
        start = time.time()
        for i in range(num_operations):
            await redis_client.set(f"{key_prefix}{i}", f"value_{i}", ex=60)
        non_pipeline_elapsed = time.time() - start
        
        # 测试管道模式
        start = time.time()
        pipe = redis_client.pipeline()
        for i in range(num_operations):
            await pipe.set(f"{key_prefix}pipe_{i}", f"value_{i}", ex=60)
        await pipe.execute()
        pipeline_elapsed = time.time() - start
        
        speedup = non_pipeline_elapsed / pipeline_elapsed
        
        print(f"\n缓存管道性能({num_operations}操作):")
        print(f"  非管道: {non_pipeline_elapsed*1000:.2f}ms")
        print(f"  管道: {pipeline_elapsed*1000:.2f}ms")
        print(f"  性能提升: {speedup:.1f}x")
        
        assert speedup > 2.0, f"管道模式应至少快2倍"
        
        # 清理
        for i in range(num_operations):
            await redis_client.delete(f"{key_prefix}{i}")
            await redis_client.delete(f"{key_prefix}pipe_{i}")
    
    @pytest.mark.performance
    async def test_cache_memory_efficiency(self, redis_client):
        """测试缓存内存效率"""
        key_prefix = "mem_test_"
        
        # 获取初始内存
        info = await redis_client.info("memory")
        initial_memory = int(info.get("used_memory", 0))
        
        # 写入1000个1KB的数据
        data_size = 1024  # 1KB
        num_keys = 1000
        data = "x" * data_size
        
        for i in range(num_keys):
            await redis_client.set(f"{key_prefix}{i}", data, ex=300)
        
        # 获取当前内存
        info = await redis_client.info("memory")
        current_memory = int(info.get("used_memory", 0))
        
        memory_used = current_memory - initial_memory
        per_key_memory = memory_used / num_keys
        
        print(f"\n缓存内存效率:")
        print(f"  写入数据: {num_keys} x {data_size}B")
        print(f"  内存增长: {memory_used / 1024:.2f}KB")
        print(f"  单key平均: {per_key_memory:.2f}B")
        print(f"  内存开销比: {per_key_memory / data_size:.2f}x")
        
        # Redis有一定的内存开销，但不应该太大
        assert per_key_memory < data_size * 1.5, "单key内存开销不应超过1.5倍数据大小"
        
        # 清理
        for i in range(num_keys):
            await redis_client.delete(f"{key_prefix}{i}")
    
    @pytest.mark.performance
    async def test_cache_invalidation_performance(self, redis_client):
        """测试缓存失效性能"""
        pattern_prefix = "invalidation_test_"
        num_keys = 500
        
        # 创建多个key
        for i in range(num_keys):
            await redis_client.set(f"{pattern_prefix}{i}", f"value_{i}", ex=300)
        
        # 测试单个删除
        single_delete_times = []
        for i in range(50):
            key = f"{pattern_prefix}{i}"
            start = time.time()
            await redis_client.delete(key)
            elapsed = time.time() - start
            single_delete_times.append(elapsed)
        
        avg_single = statistics.mean(single_delete_times)
        
        # 测试批量删除 (使用 scan + delete)
        start = time.time()
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await redis_client.scan(
                cursor, 
                match=f"{pattern_prefix}*",
                count=100
            )
            if keys:
                await redis_client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        batch_delete_elapsed = time.time() - start
        
        print(f"\n缓存失效性能:")
        print(f"  单个删除平均: {avg_single*1000:.2f}ms")
        print(f"  批量删除{deleted}个: {batch_delete_elapsed*1000:.2f}ms")
        print(f"  批量单个平均: {(batch_delete_elapsed/deleted)*1000:.2f}ms")
        
        assert avg_single < 0.01, "单个删除应<10ms"
        assert batch_delete_elapsed < 1.0, "批量删除应<1s"
    
    @pytest.mark.performance
    async def test_cache_data_structure_performance(self, redis_client):
        """测试不同数据结构的性能"""
        key = "struct_test"
        
        # String 性能
        string_times = []
        for i in range(100):
            start = time.time()
            await redis_client.set(f"{key}_string_{i}", f"value_{i}", ex=60)
            await redis_client.get(f"{key}_string_{i}")
            elapsed = time.time() - start
            string_times.append(elapsed)
        
        # Hash 性能
        hash_times = []
        for i in range(100):
            start = time.time()
            await redis_client.hset(f"{key}_hash", str(i), f"value_{i}")
            await redis_client.hget(f"{key}_hash", str(i))
            elapsed = time.time() - start
            hash_times.append(elapsed)
        
        # List 性能
        list_times = []
        for i in range(100):
            start = time.time()
            await redis_client.lpush(f"{key}_list", f"value_{i}")
            await redis_client.lrange(f"{key}_list", 0, 0)
            elapsed = time.time() - start
            list_times.append(elapsed)
        
        avg_string = statistics.mean(string_times)
        avg_hash = statistics.mean(hash_times)
        avg_list = statistics.mean(list_times)
        
        print(f"\n数据结构性能对比:")
        print(f"  String: {avg_string*1000:.2f}ms")
        print(f"  Hash: {avg_hash*1000:.2f}ms")
        print(f"  List: {avg_list*1000:.2f}ms")
        
        assert avg_string < 0.02, "String操作应<20ms"
        assert avg_hash < 0.02, "Hash操作应<20ms"
        assert avg_list < 0.02, "List操作应<20ms"
        
        # 清理
        for i in range(100):
            await redis_client.delete(f"{key}_string_{i}")
        await redis_client.delete(f"{key}_hash")
        await redis_client.delete(f"{key}_list")
