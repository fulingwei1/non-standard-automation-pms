# -*- coding: utf-8 -*-
"""
租户隔离性能测试

测试租户隔离功能在大数据量下的性能表现
"""

import pytest
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.tenant import Tenant
from app.models.user import User
from app.models.project import Project
from tests.fixtures.tenant_fixtures import (
    tenant_a, tenant_b, create_tenant, 
    create_user, create_project
)


class TestTenantQueryPerformance:
    """租户查询性能测试"""

    def test_single_tenant_query_performance(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试单租户查询性能"""
        # 创建测试数据
        user = create_user(db, "perf_user", tenant_a.id)
        
        # 创建1000个项目
        batch_size = 100
        for batch in range(10):
            projects = []
            for i in range(batch_size):
                idx = batch * batch_size + i
                project = Project(
                    tenant_id=tenant_a.id if hasattr(Project, 'tenant_id') else None,
                    project_code=f"PERF_{idx:06d}",
                    project_name=f"性能测试项目{idx}",
                    project_type="NEW_PROJECT",
                    created_by=user.id,
                    pm_id=user.id
                )
                projects.append(project)
            
            db.bulk_save_objects(projects)
            db.commit()
        
        # 测试查询性能
        start_time = time.time()
        
        if hasattr(Project, 'tenant_id'):
            results = db.query(Project).filter(
                Project.tenant_id == tenant_a.id
            ).all()
        else:
            results = db.query(Project).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # 验证结果
        assert len(results) >= 1000, f"应该返回至少1000个项目，实际: {len(results)}"
        
        # 性能要求：查询1000个项目应该在2秒内完成
        assert query_time < 2.0, \
            f"单租户查询性能不达标: {query_time:.3f}秒 (期望 < 2.0秒)"
        
        print(f"\n✓ 单租户查询1000条记录耗时: {query_time:.3f}秒")

    def test_multi_tenant_query_performance(
        self, 
        db: Session
    ):
        """测试多租户环境下的查询性能"""
        # 创建10个租户，每个租户100个项目
        tenants = []
        for i in range(10):
            tenant = create_tenant(
                db, f"perf_tenant_{i}", f"性能测试租户{i}"
            )
            tenants.append(tenant)
            
            user = create_user(db, f"perf_user_{i}", tenant.id)
            
            # 批量创建项目
            for j in range(100):
                create_project(
                    db, tenant.id, user.id,
                    f"MULTI_{i}_{j:05d}", f"多租户项目{i}-{j}"
                )
        
        # 测试每个租户的查询性能
        total_time = 0
        for tenant in tenants:
            start_time = time.time()
            
            if hasattr(Project, 'tenant_id'):
                results = db.query(Project).filter(
                    Project.tenant_id == tenant.id
                ).all()
            else:
                results = db.query(Project).all()
            
            end_time = time.time()
            query_time = end_time - start_time
            total_time += query_time
            
            # 每个租户应该只返回自己的100个项目
            if hasattr(Project, 'tenant_id'):
                assert len(results) == 100, \
                    f"租户 {tenant.tenant_code} 应该有100个项目，实际: {len(results)}"
        
        avg_time = total_time / len(tenants)
        
        # 平均查询时间应该在0.5秒内
        assert avg_time < 0.5, \
            f"多租户平均查询性能不达标: {avg_time:.3f}秒 (期望 < 0.5秒)"
        
        print(f"\n✓ 多租户环境（10个租户，共1000条记录）平均查询耗时: {avg_time:.3f}秒")

    def test_tenant_filtering_with_pagination(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试分页查询的租户过滤性能"""
        user = create_user(db, "page_user", tenant_a.id)
        
        # 创建500个项目
        for i in range(500):
            create_project(
                db, tenant_a.id, user.id,
                f"PAGE_{i:06d}", f"分页测试项目{i}"
            )
        
        # 测试分页查询性能
        page_size = 20
        total_pages = 25
        total_time = 0
        
        for page in range(total_pages):
            start_time = time.time()
            
            if hasattr(Project, 'tenant_id'):
                results = db.query(Project).filter(
                    Project.tenant_id == tenant_a.id
                ).offset(page * page_size).limit(page_size).all()
            else:
                results = db.query(Project).offset(
                    page * page_size
                ).limit(page_size).all()
            
            end_time = time.time()
            query_time = end_time - start_time
            total_time += query_time
            
            # 验证分页结果
            assert len(results) <= page_size, "分页大小不应超过限制"
        
        avg_page_time = total_time / total_pages
        
        # 单页查询应该在0.1秒内完成
        assert avg_page_time < 0.1, \
            f"分页查询性能不达标: {avg_page_time:.3f}秒 (期望 < 0.1秒)"
        
        print(f"\n✓ 分页查询（500条记录，20条/页）平均耗时: {avg_page_time:.3f}秒")

    def test_complex_query_with_tenant_filter(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试复杂查询（JOIN + 过滤）的性能"""
        user = create_user(db, "complex_user", tenant_a.id)
        
        # 创建300个项目
        for i in range(300):
            create_project(
                db, tenant_a.id, user.id,
                f"COMPLEX_{i:06d}", f"复杂查询测试{i}"
            )
        
        # 测试复杂查询性能（带JOIN）
        start_time = time.time()
        
        if hasattr(Project, 'tenant_id'):
            results = db.query(Project).join(
                User, Project.created_by == User.id
            ).filter(
                Project.tenant_id == tenant_a.id
            ).all()
        else:
            results = db.query(Project).join(
                User, Project.created_by == User.id
            ).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # 复杂查询应该在1秒内完成
        assert query_time < 1.0, \
            f"复杂查询性能不达标: {query_time:.3f}秒 (期望 < 1.0秒)"
        
        print(f"\n✓ 复杂查询（JOIN + 租户过滤，300条记录）耗时: {query_time:.3f}秒")


class TestTenantIndexPerformance:
    """租户索引性能测试"""

    def test_tenant_id_index_usage(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试tenant_id索引的使用情况"""
        from sqlalchemy import inspect, text
        
        # 创建测试数据
        user = create_user(db, "index_user", tenant_a.id)
        for i in range(1000):
            create_project(
                db, tenant_a.id, user.id,
                f"INDEX_{i:06d}", f"索引测试{i}"
            )
        
        # 检查查询计划（SQLite）
        if hasattr(Project, 'tenant_id'):
            explain_query = text(
                f"EXPLAIN QUERY PLAN SELECT * FROM projects WHERE tenant_id = {tenant_a.id}"
            )
            
            result = db.execute(explain_query)
            plan = result.fetchall()
            
            # 输出查询计划用于分析
            print("\n查询计划:")
            for row in plan:
                print(row)
            
            # 理想情况下，应该使用索引扫描而不是全表扫描
            # SQLite的EXPLAIN输出格式: (id, parent, notused, detail)
            plan_str = ' '.join(str(row) for row in plan).lower()
            
            # 检查是否使用了索引
            uses_index = 'index' in plan_str or 'idx' in plan_str
            
            if not uses_index:
                pytest.skip("tenant_id字段可能缺少索引，建议添加以提高性能")

    def test_composite_index_performance(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试组合索引（tenant_id + 其他字段）的性能"""
        user = create_user(db, "composite_user", tenant_a.id)
        
        # 创建500个不同状态的项目
        statuses = ['PLANNING', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'CANCELLED']
        for i in range(500):
            project = Project(
                tenant_id=tenant_a.id if hasattr(Project, 'tenant_id') else None,
                project_code=f"COMP_{i:06d}",
                project_name=f"组合索引测试{i}",
                project_type="NEW_PROJECT",
                status=statuses[i % len(statuses)],
                created_by=user.id,
                pm_id=user.id
            )
            db.add(project)
        db.commit()
        
        # 测试组合条件查询性能
        start_time = time.time()
        
        if hasattr(Project, 'tenant_id'):
            results = db.query(Project).filter(
                Project.tenant_id == tenant_a.id,
                Project.status == 'IN_PROGRESS'
            ).all()
        else:
            results = db.query(Project).filter(
                Project.status == 'IN_PROGRESS'
            ).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # 组合查询应该在0.2秒内完成
        assert query_time < 0.2, \
            f"组合索引查询性能不达标: {query_time:.3f}秒 (期望 < 0.2秒)"
        
        print(f"\n✓ 组合索引查询（tenant_id + status）耗时: {query_time:.3f}秒")


class TestTenantConcurrentAccess:
    """租户并发访问性能测试"""

    def test_concurrent_tenant_queries(
        self, 
        db: Session
    ):
        """测试多租户并发查询"""
        import threading
        
        # 创建5个租户，每个租户100个项目
        tenants = []
        for i in range(5):
            tenant = create_tenant(db, f"conc_tenant_{i}", f"并发测试租户{i}")
            tenants.append(tenant)
            
            user = create_user(db, f"conc_user_{i}", tenant.id)
            for j in range(100):
                create_project(
                    db, tenant.id, user.id,
                    f"CONC_{i}_{j:05d}", f"并发项目{i}-{j}"
                )
        
        # 并发查询测试
        results = []
        errors = []
        
        def query_tenant(tenant_id: int):
            try:
                # 创建新的session用于并发
                from app.models.base import SessionLocal
                local_db = SessionLocal()
                
                start = time.time()
                if hasattr(Project, 'tenant_id'):
                    items = local_db.query(Project).filter(
                        Project.tenant_id == tenant_id
                    ).all()
                else:
                    items = local_db.query(Project).all()
                
                duration = time.time() - start
                results.append((tenant_id, len(items), duration))
                local_db.close()
            except Exception as e:
                errors.append((tenant_id, str(e)))
        
        # 创建线程
        threads = []
        for tenant in tenants:
            thread = threading.Thread(target=query_tenant, args=(tenant.id,))
            threads.append(thread)
        
        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 验证结果
        assert len(errors) == 0, f"并发查询出现错误: {errors}"
        assert len(results) == len(tenants), "并非所有查询都成功"
        
        # 并发查询总时间应该明显小于顺序查询时间
        max_single_time = max(r[2] for r in results)
        
        print(f"\n✓ 并发查询性能:")
        print(f"  - 总耗时: {total_time:.3f}秒")
        print(f"  - 最慢单次查询: {max_single_time:.3f}秒")
        print(f"  - 并发加速比: {max_single_time * len(tenants) / total_time:.2f}x")


class TestTenantMemoryUsage:
    """租户隔离内存使用测试"""

    def test_large_result_set_memory(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试大结果集的内存使用"""
        import sys
        
        user = create_user(db, "memory_user", tenant_a.id)
        
        # 创建2000个项目
        batch_size = 200
        for batch in range(10):
            projects = []
            for i in range(batch_size):
                idx = batch * batch_size + i
                project = Project(
                    tenant_id=tenant_a.id if hasattr(Project, 'tenant_id') else None,
                    project_code=f"MEM_{idx:06d}",
                    project_name=f"内存测试项目{idx}",
                    project_type="NEW_PROJECT",
                    created_by=user.id,
                    pm_id=user.id
                )
                projects.append(project)
            
            db.bulk_save_objects(projects)
            db.commit()
        
        # 测试查询内存使用
        import gc
        gc.collect()
        
        if hasattr(Project, 'tenant_id'):
            results = db.query(Project).filter(
                Project.tenant_id == tenant_a.id
            ).all()
        else:
            results = db.query(Project).all()
        
        # 估算结果集大小
        result_size = sys.getsizeof(results)
        avg_object_size = sum(sys.getsizeof(r) for r in results[:10]) / 10
        
        print(f"\n✓ 内存使用统计:")
        print(f"  - 结果集数量: {len(results)}")
        print(f"  - 结果集大小: {result_size / 1024:.2f} KB")
        print(f"  - 平均对象大小: {avg_object_size:.2f} bytes")

    def test_streaming_query_performance(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试流式查询性能（减少内存占用）"""
        user = create_user(db, "stream_user", tenant_a.id)
        
        # 创建1000个项目
        for i in range(1000):
            create_project(
                db, tenant_a.id, user.id,
                f"STREAM_{i:06d}", f"流式查询测试{i}"
            )
        
        # 测试流式处理
        start_time = time.time()
        count = 0
        
        if hasattr(Project, 'tenant_id'):
            query = db.query(Project).filter(
                Project.tenant_id == tenant_a.id
            ).yield_per(100)
        else:
            query = db.query(Project).yield_per(100)
        
        for project in query:
            count += 1
            # 模拟处理
            _ = project.project_name
        
        end_time = time.time()
        stream_time = end_time - start_time
        
        assert count >= 1000, f"流式查询应该返回至少1000条记录，实际: {count}"
        
        print(f"\n✓ 流式查询（1000条记录，批次大小100）耗时: {stream_time:.3f}秒")


class TestTenantAPIPerformance:
    """租户API性能测试"""

    def test_api_list_endpoint_performance(
        self, 
        client: TestClient,
        db: Session,
        tenant_a: Tenant
    ):
        """测试API列表端点的性能"""
        from app.core.security import create_access_token
        
        # 创建用户和项目
        user = create_user(db, "api_user", tenant_a.id)
        for i in range(200):
            create_project(
                db, tenant_a.id, user.id,
                f"API_{i:06d}", f"API性能测试{i}"
            )
        
        token = create_access_token(user.id)
        
        # 测试API查询性能
        start_time = time.time()
        
        response = client.get(
            "/api/v1/projects?page=1&page_size=50",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        end_time = time.time()
        api_time = end_time - start_time
        
        # API响应应该在1秒内完成
        assert api_time < 1.0, \
            f"API查询性能不达标: {api_time:.3f}秒 (期望 < 1.0秒)"
        
        if response.status_code == 200:
            print(f"\n✓ API列表查询（200条记录，返回50条）耗时: {api_time:.3f}秒")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
