#!/bin/bash

# 性能分析脚本

echo "=== 非标自动化项目管理系统 - 性能分析 ==="
echo

# 1. 检查数据库连接池使用情况
echo "1. 数据库连接池分析..."
python3 -c "
from app.models.base import get_engine
from sqlalchemy import inspect
engine = get_engine()
pool = engine.pool
print(f'连接池大小: {pool.size()}')
print(f'已用连接: {pool.checkedout()}')
print(f'空闲连接: {pool.checkedin()}')
"

echo
echo "2. 慢查询分析（前10）..."
sqlite3 data/app.db <<EOF
SELECT sql, count(*) as exec_count,
       sum(time) as total_time,
       avg(time) as avg_time
FROM sqlite_master
WHERE type = 'table'
ORDER BY total_time DESC
LIMIT 10;
EOF 2>/dev/null || echo "需要配置 SQLite 查询日志"

echo
echo "3. Redis 缓存命中率..."
python3 <<EOF
try:
    from app.utils.redis_client import get_redis_client
    redis = get_redis_client()
    info = redis.info('stats')
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    total = hits + misses
    if total > 0:
        hit_rate = (hits / total) * 100
        print(f'缓存命中率: {hit_rate:.2f}%')
        print(f'命中次数: {hits}')
        print(f'未命中次数: {misses}')
    else:
        print('暂无缓存数据')
except Exception as e:
    print(f'Redis 不可用: {e}')
EOF

echo
echo "4. API 响应时间统计..."
echo "运行: pytest tests/performance/ -v --benchmark-only"

echo
echo "5. 内存使用情况..."
ps aux | grep -E "(python|uvicorn)" | grep -v grep | awk '{print $2, $4, $11}'

echo
echo "性能分析完成！"
echo "建议:"
echo "  - 使用 locust 进行压力测试: locust -f tests/performance/load_test.py"
echo "  - 使用 Py-Spy 分析 CPU 使用: py-spy top --pid \$(pgrep -f uvicorn)"
echo "  - 使用 Memory Profiler 分析内存: python -m memory_profiler script.py"
