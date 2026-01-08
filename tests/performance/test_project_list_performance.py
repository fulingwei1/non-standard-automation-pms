# -*- coding: utf-8 -*-
"""
项目列表查询性能测试

Sprint 5.1: 性能优化 - 项目列表查询性能测试
"""

import pytest
import time
from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.cache_service import CacheService


class TestProjectListPerformance:
    """项目列表查询性能测试"""
    
    @pytest.mark.skipif(True, reason="需要大量测试数据")
    def test_project_list_query_performance(self, db: Session):
        """
        测试项目列表查询性能
        
        目标：1000+项目场景下查询响应时间 < 500ms
        """
        # 创建测试数据（需要预先准备）
        # 这里假设已经有1000+项目数据
        
        start_time = time.time()
        
        # 执行查询
        projects = db.query(Project).filter(
            Project.is_active == True
        ).order_by(Project.created_at.desc()).limit(20).all()
        
        elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        assert elapsed_time < 500, f"查询耗时 {elapsed_time}ms，超过500ms阈值"
        assert len(projects) <= 20
    
    @pytest.mark.skipif(True, reason="需要大量测试数据")
    def test_project_list_with_filters_performance(self, db: Session):
        """测试带筛选条件的项目列表查询性能"""
        from sqlalchemy import or_
        
        start_time = time.time()
        
        query = db.query(Project).filter(
            Project.is_active == True,
            Project.stage == "S5",
            Project.health == "H1"
        )
        
        total = query.count()
        projects = query.order_by(Project.created_at.desc()).limit(20).all()
        
        elapsed_time = (time.time() - start_time) * 1000
        
        assert elapsed_time < 500, f"查询耗时 {elapsed_time}ms，超过500ms阈值"
    
    def test_project_list_cache_performance(self, db: Session):
        """测试项目列表缓存性能"""
        cache = CacheService()
        
        # 第一次查询（无缓存）
        start_time = time.time()
        projects = db.query(Project).filter(
            Project.is_active == True
        ).limit(20).all()
        first_query_time = (time.time() - start_time) * 1000
        
        # 模拟缓存数据
        cache_data = {
            "items": [{"id": p.id, "name": p.project_name} for p in projects],
            "total": len(projects),
            "page": 1,
            "page_size": 20
        }
        cache.set_project_list(cache_data, expire_seconds=300, page=1, page_size=20)
        
        # 第二次查询（从缓存）
        start_time = time.time()
        cached_data = cache.get_project_list(page=1, page_size=20)
        cached_query_time = (time.time() - start_time) * 1000
        
        # 缓存查询应该明显快于数据库查询
        assert cached_query_time < first_query_time
        assert cached_data is not None
        
        # 缓存查询应该在10ms以内
        assert cached_query_time < 10, f"缓存查询耗时 {cached_query_time}ms，超过10ms阈值"
