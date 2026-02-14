# -*- coding: utf-8 -*-
"""
权限缓存性能测试

对比启用和禁用缓存时的性能差异，生成性能报告。

运行方式：
    pytest tests/performance/test_permission_cache_performance.py -v -s
    或
    python tests/performance/test_permission_cache_performance.py
"""

import logging
import time
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole
from app.services.permission_service import PermissionService
from app.services.permission_cache_service import get_permission_cache_service

logger = logging.getLogger(__name__)


# ==================== 测试数据准备 ====================


class PerformanceTestContext:
    """性能测试上下文"""

    def __init__(self, db: Session):
        self.db = db
        self.test_users: List[User] = []
        self.test_roles: List[Role] = []
        self.test_permissions: List[ApiPermission] = []

    def setup_test_data(self, num_users: int = 100, num_roles: int = 10, num_permissions: int = 50):
        """创建测试数据

        Args:
            num_users: 用户数量
            num_roles: 角色数量
            num_permissions: 权限数量
        """
        logger.info(f"创建测试数据: {num_users} 用户, {num_roles} 角色, {num_permissions} 权限")

        # 创建权限
        for i in range(num_permissions):
            perm = ApiPermission(
                perm_code=f"test_perm_{i}",
                perm_name=f"测试权限 {i}",
                module=f"module_{i % 5}",
                action="read" if i % 2 == 0 else "write",
                is_active=True,
            )
            self.db.add(perm)
            self.test_permissions.append(perm)

        self.db.flush()

        # 创建角色
        for i in range(num_roles):
            role = Role(
                role_code=f"test_role_{i}",
                role_name=f"测试角色 {i}",
                is_active=True,
            )
            self.db.add(role)
            self.test_roles.append(role)

        self.db.flush()

        # 为角色分配权限（每个角色分配 10-30 个权限）
        import random
        for role in self.test_roles:
            num_perms = random.randint(10, 30)
            selected_perms = random.sample(self.test_permissions, num_perms)
            for perm in selected_perms:
                self.db.add(RoleApiPermission(role_id=role.id, permission_id=perm.id))

        self.db.flush()

        # 创建用户
        for i in range(num_users):
            user = User(
                username=f"test_user_{i}",
                email=f"test_{i}@example.com",
                hashed_password="hashed_password",
                is_active=True,
            )
            self.db.add(user)
            self.test_users.append(user)

        self.db.flush()

        # 为用户分配角色（每个用户 1-3 个角色）
        for user in self.test_users:
            num_roles_for_user = random.randint(1, 3)
            selected_roles = random.sample(self.test_roles, num_roles_for_user)
            for role in selected_roles:
                self.db.add(UserRole(user_id=user.id, role_id=role.id))

        self.db.commit()
        logger.info("测试数据创建完成")

    def cleanup(self):
        """清理测试数据"""
        logger.info("清理测试数据")
        for user in self.test_users:
            self.db.query(UserRole).filter(UserRole.user_id == user.id).delete()
            self.db.delete(user)

        for role in self.test_roles:
            self.db.query(RoleApiPermission).filter(RoleApiPermission.role_id == role.id).delete()
            self.db.delete(role)

        for perm in self.test_permissions:
            self.db.delete(perm)

        self.db.commit()
        logger.info("测试数据清理完成")


# ==================== 性能测试函数 ====================


def measure_permission_query_time(
    db: Session, user_ids: List[int], iterations: int = 10, use_cache: bool = True
) -> Dict[str, Any]:
    """测量权限查询性能

    Args:
        db: 数据库会话
        user_ids: 要测试的用户ID列表
        iterations: 每个用户重复查询次数
        use_cache: 是否使用缓存

    Returns:
        性能统计数据
    """
    cache_service = get_permission_cache_service()

    # 清空缓存
    cache_service.invalidate_all()

    query_times: List[float] = []
    total_queries = len(user_ids) * iterations

    logger.info(f"开始性能测试: use_cache={use_cache}, total_queries={total_queries}")

    start_time = time.time()

    for iteration in range(iterations):
        for user_id in user_ids:
            query_start = time.time()

            if use_cache:
                # 使用缓存的查询
                permissions = PermissionService.get_user_permissions(db, user_id)
            else:
                # 绕过缓存，直接查询数据库
                with patch.object(cache_service, "get_user_permissions", return_value=None):
                    with patch.object(cache_service, "set_user_permissions", return_value=True):
                        permissions = PermissionService.get_user_permissions(db, user_id)

            query_end = time.time()
            query_times.append((query_end - query_start) * 1000)  # 转换为毫秒

    end_time = time.time()
    total_time = end_time - start_time

    # 统计结果
    avg_time = sum(query_times) / len(query_times)
    min_time = min(query_times)
    max_time = max(query_times)
    p50 = sorted(query_times)[len(query_times) // 2]
    p95 = sorted(query_times)[int(len(query_times) * 0.95)]
    p99 = sorted(query_times)[int(len(query_times) * 0.99)]

    # 获取缓存统计
    cache_stats = cache_service.get_stats()

    result = {
        "use_cache": use_cache,
        "total_queries": total_queries,
        "total_time_seconds": round(total_time, 3),
        "avg_time_ms": round(avg_time, 3),
        "min_time_ms": round(min_time, 3),
        "max_time_ms": round(max_time, 3),
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "qps": round(total_queries / total_time, 2),
        "cache_stats": cache_stats,
    }

    logger.info(f"性能测试完成: {result}")
    return result


def compare_performance(
    db: Session, user_ids: List[int], iterations: int = 10
) -> Dict[str, Any]:
    """对比启用和禁用缓存的性能差异

    Args:
        db: 数据库会话
        user_ids: 要测试的用户ID列表
        iterations: 每个用户重复查询次数

    Returns:
        对比报告
    """
    logger.info("=" * 60)
    logger.info("开始性能对比测试")
    logger.info("=" * 60)

    # 1. 测试不使用缓存的性能
    logger.info("\n1️⃣  测试不使用缓存的性能...")
    no_cache_result = measure_permission_query_time(
        db, user_ids, iterations=iterations, use_cache=False
    )

    # 2. 测试使用缓存的性能（第一轮：冷启动）
    logger.info("\n2️⃣  测试使用缓存的性能（冷启动）...")
    cache_cold_result = measure_permission_query_time(
        db, user_ids, iterations=1, use_cache=True
    )

    # 3. 测试使用缓存的性能（第二轮：热缓存）
    logger.info("\n3️⃣  测试使用缓存的性能（热缓存）...")
    cache_hot_result = measure_permission_query_time(
        db, user_ids, iterations=iterations, use_cache=True
    )

    # 计算性能提升
    speedup_avg = no_cache_result["avg_time_ms"] / cache_hot_result["avg_time_ms"]
    speedup_p95 = no_cache_result["p95_ms"] / cache_hot_result["p95_ms"]

    comparison = {
        "no_cache": no_cache_result,
        "cache_cold": cache_cold_result,
        "cache_hot": cache_hot_result,
        "improvement": {
            "avg_speedup": round(speedup_avg, 2),
            "p95_speedup": round(speedup_p95, 2),
            "avg_time_reduction_percent": round(
                (1 - cache_hot_result["avg_time_ms"] / no_cache_result["avg_time_ms"]) * 100, 2
            ),
            "qps_improvement": round(
                cache_hot_result["qps"] / no_cache_result["qps"], 2
            ),
        },
    }

    logger.info("\n" + "=" * 60)
    logger.info("📊 性能对比结果")
    logger.info("=" * 60)
    logger.info(f"无缓存平均响应时间: {no_cache_result['avg_time_ms']:.3f} ms")
    logger.info(f"有缓存平均响应时间: {cache_hot_result['avg_time_ms']:.3f} ms")
    logger.info(f"性能提升: {speedup_avg:.2f}x")
    logger.info(f"响应时间减少: {comparison['improvement']['avg_time_reduction_percent']:.2f}%")
    logger.info(f"QPS 提升: {comparison['improvement']['qps_improvement']:.2f}x")
    logger.info(f"缓存命中率: {cache_hot_result['cache_stats']['hit_rate']:.2f}%")
    logger.info("=" * 60)

    return comparison


# ==================== Pytest 测试用例 ====================


@pytest.fixture(scope="module")
def test_db():
    """创建测试数据库"""
    # 使用内存数据库
    engine = create_engine("sqlite:///:memory:", echo=False)

    # 创建表结构（简化版）
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                hashed_password TEXT,
                is_active BOOLEAN DEFAULT 1,
                tenant_id INTEGER
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY,
                role_code TEXT UNIQUE NOT NULL,
                role_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                tenant_id INTEGER,
                parent_id INTEGER,
                inherit_permissions BOOLEAN DEFAULT 0
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE user_roles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE api_permissions (
                id INTEGER PRIMARY KEY,
                perm_code TEXT UNIQUE NOT NULL,
                perm_name TEXT,
                module TEXT,
                action TEXT,
                is_active BOOLEAN DEFAULT 1,
                tenant_id INTEGER
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE role_api_permissions (
                id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                FOREIGN KEY (role_id) REFERENCES roles(id),
                FOREIGN KEY (permission_id) REFERENCES api_permissions(id)
            )
        """
            )
        )
        conn.commit()

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    engine.dispose()


def test_permission_cache_performance(test_db):
    """测试权限缓存性能"""
    ctx = PerformanceTestContext(test_db)

    try:
        # 创建测试数据
        ctx.setup_test_data(num_users=50, num_roles=10, num_permissions=50)

        # 选择部分用户进行测试
        test_user_ids = [u.id for u in ctx.test_users[:20]]

        # 运行性能对比
        comparison = compare_performance(test_db, test_user_ids, iterations=5)

        # 验证性能提升
        assert comparison["improvement"]["avg_speedup"] > 2.0, "缓存性能提升应大于 2 倍"
        assert (
            comparison["cache_hot"]["cache_stats"]["hit_rate"] > 80.0
        ), "缓存命中率应大于 80%"

    finally:
        # 清理测试数据
        ctx.cleanup()


# ==================== 直接运行测试 ====================


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 创建测试数据库
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", echo=False)

    # 创建表结构
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                hashed_password TEXT,
                is_active BOOLEAN DEFAULT 1,
                tenant_id INTEGER
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY,
                role_code TEXT UNIQUE NOT NULL,
                role_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                tenant_id INTEGER,
                parent_id INTEGER,
                inherit_permissions BOOLEAN DEFAULT 0
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE user_roles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE api_permissions (
                id INTEGER PRIMARY KEY,
                perm_code TEXT UNIQUE NOT NULL,
                perm_name TEXT,
                module TEXT,
                action TEXT,
                is_active BOOLEAN DEFAULT 1,
                tenant_id INTEGER
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE role_api_permissions (
                id INTEGER PRIMARY KEY,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL
            )
        """
            )
        )
        conn.commit()

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    ctx = PerformanceTestContext(db)

    try:
        # 创建测试数据
        ctx.setup_test_data(num_users=100, num_roles=10, num_permissions=50)

        # 选择部分用户进行测试
        test_user_ids = [u.id for u in ctx.test_users[:30]]

        # 运行性能对比
        comparison = compare_performance(db, test_user_ids, iterations=10)

        # 打印详细报告
        print("\n" + "=" * 80)
        print("📈 详细性能报告")
        print("=" * 80)
        import json
        print(json.dumps(comparison, indent=2, ensure_ascii=False))

    finally:
        ctx.cleanup()
        db.close()
        engine.dispose()
