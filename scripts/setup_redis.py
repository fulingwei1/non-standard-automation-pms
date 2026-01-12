#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis配置和测试脚本

使用方法:
1. 设置Redis环境变量
2. 运行此脚本测试连接
3. 自动生成.env配置文件内容
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_redis_connection(redis_url: str) -> bool:
    """
    测试Redis连接

    Args:
        redis_url: Redis连接URL

    Returns:
        连接是否成功
    """
    try:
        import redis
        print(f"正在连接Redis: {redis_url}")
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        # 测试连接
        client.ping()
        print("✓ Redis连接成功!")

        # 获取Redis信息
        info = client.info('server')
        print(f"✓ Redis版本: {info.get('redis_version', 'unknown')}")
        print(f"✓ 运行模式: {info.get('redis_mode', 'unknown')}")

        # 测试读写
        test_key = "_test_connection_"
        client.setex(test_key, 10, "OK")
        value = client.get(test_key)
        if value == "OK":
            print("✓ Redis读写测试成功")
            client.delete(test_key)

        return True

    except ImportError:
        print("✗ 错误: redis包未安装")
        print("  请运行: pip install redis")
        return False

    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        return False


def generate_env_config(redis_url: str) -> str:
    """
    生成环境变量配置内容

    Args:
        redis_url: Redis连接URL

    Returns:
        .env文件内容
    """
    return f"""# Redis缓存配置
# ============================================

# Redis连接URL
# 格式: redis://localhost:6379/0
# 或者带密码: redis://:password@localhost:6379/0
# 或者使用Unix socket: unix:///path/to/redis.sock
REDIS_URL={redis_url}

# 是否启用Redis缓存
REDIS_CACHE_ENABLED=true

# 默认缓存过期时间（秒），5分钟
REDIS_CACHE_DEFAULT_TTL=300

# 项目详情缓存过期时间（秒），10分钟
REDIS_CACHE_PROJECT_DETAIL_TTL=600

# 项目列表缓存过期时间（秒），5分钟
REDIS_CACHE_PROJECT_LIST_TTL=300
"""


def setup_redis():
    """设置Redis缓存"""

    print("=" * 60)
    print("Redis缓存配置向导")
    print("=" * 60)
    print()

    # 检查Redis是否已安装
    try:
        import redis
        print("✓ redis包已安装")
    except ImportError:
        print("✗ redis包未安装")
        print("  正在安装redis...")
        os.system("pip install redis")
        print()

    # 获取Redis URL
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    print(f"当前Redis URL: {redis_url}")
    print()

    # 测试连接
    if test_redis_connection(redis_url):
        print()
        print("=" * 60)
        print("环境变量配置")
        print("=" * 60)
        print()
        print("请将以下配置添加到 .env 文件中:")
        print()
        print(generate_env_config(redis_url))
        print()
        print("=" * 60)
        print("配置完成！")
        print("=" * 60)
        print()
        print("下一步:")
        print("1. 将上述配置添加到 .env 文件")
        print("2. 重启应用: uvicorn app.main:app --reload")
        print("3. Redis缓存将自动启用")
        return True
    else:
        print()
        print("请检查:")
        print("1. Redis服务是否已启动")
        print("2. Redis连接地址是否正确")
        print("3. 防火墙是否允许连接")
        print()
        return False


if __name__ == "__main__":
    setup_redis()
