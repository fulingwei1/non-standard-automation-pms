# -*- coding: utf-8 -*-
"""
CRUD基类集成测试
测试通用CRUD基类在实际API场景中的使用
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel
from typing import Optional

from app.main import app
from app.common.crud.service import BaseService
from app.common.crud.repository import BaseRepository
from app.common.crud.exceptions import raise_not_found

# 测试数据库
Base = declarative_base()


# 测试模型
class TestResource(Base):
    __tablename__ = "test_resources"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True)
    status = Column(String(20), default="ACTIVE")
    description = Column(String(500))


# 测试Schema
class TestResourceCreate(BaseModel):
    name: str
    code: str
    status: str = "ACTIVE"
    description: Optional[str] = None


class TestResourceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class TestResourceResponse(BaseModel):
    id: int
    name: str
    code: str
    status: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


# 测试Service
class TestResourceService(BaseService[TestResource, TestResourceCreate, TestResourceUpdate, TestResourceResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(TestResource, db, "测试资源")
    
    def _to_response(self, obj: TestResource) -> TestResourceResponse:
        return TestResourceResponse.model_validate(obj)


import pytest_asyncio

@pytest_asyncio.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.integration
class TestCRUDBaseIntegration:
    """CRUD基类集成测试"""
    
    async def test_create_and_get_workflow(self, db_session):
        """测试创建和获取的完整流程"""
        service = TestResourceService(db_session)
        
        # 创建资源
        create_data = TestResourceCreate(
            name="测试资源1",
            code="TEST001",
            description="这是一个测试资源"
        )
        created = await service.create(create_data)
        
        assert created.id is not None
        assert created.name == "测试资源1"
        assert created.code == "TEST001"
        
        # 获取资源
        retrieved = await service.get(created.id)
        assert retrieved.id == created.id
        assert retrieved.name == "测试资源1"
    
    async def test_list_with_filters_and_keyword(self, db_session):
        """测试列表查询、筛选和关键词搜索的集成"""
        service = TestResourceService(db_session)
        
        # 创建测试数据
        await service.create(TestResourceCreate(name="项目A", code="PROJ001", status="ACTIVE"))
        await service.create(TestResourceCreate(name="项目B", code="PROJ002", status="INACTIVE"))
        await service.create(TestResourceCreate(name="任务A", code="TASK001", status="ACTIVE"))
        
        # 测试筛选
        result = await service.list(
            filters={"status": "ACTIVE"},
            skip=0,
            limit=10
        )
        assert result["total"] == 2
        assert all(item.status == "ACTIVE" for item in result["items"])
        
        # 测试关键词搜索
        result = await service.list(
            keyword="项目",
            keyword_fields=["name", "code"],
            skip=0,
            limit=10
        )
        assert result["total"] == 2
        assert all("项目" in item.name for item in result["items"])
    
    async def test_update_workflow(self, db_session):
        """测试更新流程"""
        service = TestResourceService(db_session)
        
        # 创建资源
        created = await service.create(
            TestResourceCreate(name="原始名称", code="TEST001")
        )
        
        # 更新资源
        updated = await service.update(
            created.id,
            TestResourceUpdate(name="更新后的名称", status="INACTIVE")
        )
        
        assert updated.name == "更新后的名称"
        assert updated.status == "INACTIVE"
        assert updated.code == "TEST001"  # 未更新的字段保持不变
        
        # 验证更新
        retrieved = await service.get(created.id)
        assert retrieved.name == "更新后的名称"
        assert retrieved.status == "INACTIVE"
    
    async def test_delete_workflow(self, db_session):
        """测试删除流程"""
        service = TestResourceService(db_session)
        
        # 创建资源
        created = await service.create(
            TestResourceCreate(name="待删除资源", code="TEST001")
        )
        
        # 删除资源
        success = await service.delete(created.id)
        assert success is True
        
        # 验证已删除
        with pytest.raises(Exception):
            await service.get(created.id)
    
    async def test_pagination_workflow(self, db_session):
        """测试分页流程"""
        service = TestResourceService(db_session)
        
        # 创建多个资源
        for i in range(25):
            await service.create(
                TestResourceCreate(name=f"资源{i}", code=f"TEST{i:03d}")
            )
        
        # 测试第一页
        result = await service.list(skip=0, limit=10)
        assert result["total"] == 25
        assert len(result["items"]) == 10
        
        # 测试第二页
        result = await service.list(skip=10, limit=10)
        assert len(result["items"]) == 10
        
        # 测试最后一页
        result = await service.list(skip=20, limit=10)
        assert len(result["items"]) == 5
    
    async def test_count_with_filters(self, db_session):
        """测试统计功能"""
        service = TestResourceService(db_session)
        
        # 创建测试数据
        await service.create(TestResourceCreate(name="资源1", code="TEST001", status="ACTIVE"))
        await service.create(TestResourceCreate(name="资源2", code="TEST002", status="ACTIVE"))
        await service.create(TestResourceCreate(name="资源3", code="TEST003", status="INACTIVE"))
        
        # 统计总数
        total = await service.count()
        assert total == 3
        
        # 统计筛选后的数量
        active_count = await service.count(filters={"status": "ACTIVE"})
        assert active_count == 2
        
        inactive_count = await service.count(filters={"status": "INACTIVE"})
        assert inactive_count == 1
    
    async def test_get_by_field(self, db_session):
        """测试根据字段获取"""
        service = TestResourceService(db_session)
        
        # 创建资源
        created = await service.create(
            TestResourceCreate(name="测试资源", code="UNIQUE001")
        )
        
        # 根据code获取
        retrieved = await service.get_by_field("code", "UNIQUE001")
        assert retrieved is not None
        assert retrieved.code == "UNIQUE001"
        assert retrieved.id == created.id
    
    async def test_create_many_workflow(self, db_session):
        """测试批量创建"""
        service = TestResourceService(db_session)
        
        # 批量创建
        items = [
            TestResourceCreate(name=f"资源{i}", code=f"BATCH{i:03d}")
            for i in range(5)
        ]
        
        created = await service.repository.create_many(items)
        assert len(created) == 5
        
        # 验证所有都创建成功
        result = await service.list(skip=0, limit=10)
        assert result["total"] == 5


@pytest.mark.asyncio
@pytest.mark.integration
class TestCRUDBaseErrorHandling:
    """CRUD基类错误处理集成测试"""
    
    async def test_get_not_found(self, db_session):
        """测试获取不存在的资源"""
        service = TestResourceService(db_session)
        
        with pytest.raises(Exception):
            await service.get(99999)
    
    async def test_update_not_found(self, db_session):
        """测试更新不存在的资源"""
        service = TestResourceService(db_session)
        
        with pytest.raises(Exception):
            await service.update(
                99999,
                TestResourceUpdate(name="不存在的资源")
            )
    
    async def test_delete_not_found(self, db_session):
        """测试删除不存在的资源"""
        service = TestResourceService(db_session)
        
        # service.delete在资源不存在时会抛出HTTPException
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.delete(99999)
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
class TestCRUDBasePerformance:
    """CRUD基类性能测试"""
    
    async def test_bulk_operations(self, db_session):
        """测试批量操作性能"""
        service = TestResourceService(db_session)
        
        # 批量创建
        items = [
            TestResourceCreate(name=f"资源{i}", code=f"PERF{i:05d}")
            for i in range(100)
        ]
        
        import time
        start = time.time()
        await service.repository.create_many(items)
        create_time = time.time() - start
        
        # 批量查询
        start = time.time()
        result = await service.list(skip=0, limit=100)
        query_time = time.time() - start
        
        assert result["total"] == 100
        assert create_time < 5.0  # 创建应该在5秒内完成
        assert query_time < 2.0   # 查询应该在2秒内完成
