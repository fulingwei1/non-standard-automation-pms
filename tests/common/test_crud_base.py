# -*- coding: utf-8 -*-
"""
通用CRUD基类测试
"""

import pytest
import pytest_asyncio

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel

from app.common.crud.service import BaseService
from app.common.crud.repository import BaseRepository
from app.common.crud.exceptions import NotFoundError, AlreadyExistsError

# 测试数据库
Base = declarative_base()


# 测试模型
class TestModel(Base):
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True)
    status = Column(String(20), default="ACTIVE")


# 测试Schema
class TestCreate(BaseModel):
    name: str
    code: str
    status: str = "ACTIVE"


class TestUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


class TestResponse(BaseModel):
    id: int
    name: str
    code: str
    status: str
    
    class Config:
        from_attributes = True


# 测试Service
class TestService(BaseService[TestModel, TestCreate, TestUpdate, TestResponse]):
    def __init__(self, db: AsyncSession):
        super().__init__(TestModel, db, "测试模型")
    
    def _to_response(self, obj: TestModel) -> TestResponse:
        """实现响应转换"""
        return TestResponse.model_validate(obj)


@pytest_asyncio.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    session = async_session()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
    await engine.dispose()


@pytest.mark.asyncio
async def test_create(db_session):
    """测试创建"""
    service = TestService(db_session)
    
    obj_in = TestCreate(name="测试对象", code="TEST001")
    obj = await service.create(obj_in)
    
    assert obj.id is not None
    assert obj.name == "测试对象"
    assert obj.code == "TEST001"


@pytest.mark.asyncio
async def test_get(db_session):
    """测试获取"""
    service = TestService(db_session)
    
    # 先创建
    obj_in = TestCreate(name="测试对象", code="TEST001")
    created = await service.create(obj_in)
    
    # 再获取
    obj = await service.get(created.id)
    
    assert obj.id == created.id
    assert obj.name == "测试对象"


@pytest.mark.asyncio
async def test_get_not_found(db_session):
    """测试获取不存在的对象"""
    service = TestService(db_session)
    
    with pytest.raises(Exception):  # 应该抛出HTTPException
        await service.get(999)


@pytest.mark.asyncio
async def test_list(db_session):
    """测试列表查询"""
    service = TestService(db_session)
    
    # 创建测试数据
    await service.create(TestCreate(name="对象1", code="TEST001"))
    await service.create(TestCreate(name="对象2", code="TEST002"))
    await service.create(TestCreate(name="对象3", code="TEST003"))
    
    # 查询列表
    result = await service.list(skip=0, limit=10)
    
    assert result["total"] == 3
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_list_with_filters(db_session):
    """测试带筛选的列表查询"""
    service = TestService(db_session)
    
    # 创建测试数据
    await service.create(TestCreate(name="对象1", code="TEST001", status="ACTIVE"))
    await service.create(TestCreate(name="对象2", code="TEST002", status="INACTIVE"))
    await service.create(TestCreate(name="对象3", code="TEST003", status="ACTIVE"))
    
    # 筛选查询
    result = await service.list(
        filters={"status": "ACTIVE"},
        skip=0,
        limit=10
    )
    
    assert result["total"] == 2
    assert all(item.status == "ACTIVE" for item in result["items"])


@pytest.mark.asyncio
async def test_list_with_keyword(db_session):
    """测试关键词搜索"""
    service = TestService(db_session)
    
    # 创建测试数据
    await service.create(TestCreate(name="测试对象1", code="TEST001"))
    await service.create(TestCreate(name="其他对象", code="OTHER001"))
    await service.create(TestCreate(name="测试对象2", code="TEST002"))
    
    # 关键词搜索
    result = await service.list(
        keyword="测试",
        keyword_fields=["name", "code"],
        skip=0,
        limit=10
    )
    
    assert result["total"] == 2
    assert all("测试" in item.name for item in result["items"])


@pytest.mark.asyncio
async def test_update(db_session):
    """测试更新"""
    service = TestService(db_session)
    
    # 先创建
    obj_in = TestCreate(name="测试对象", code="TEST001")
    created = await service.create(obj_in)
    
    # 再更新
    update_in = TestUpdate(name="更新后的名称")
    updated = await service.update(created.id, update_in)
    
    assert updated.name == "更新后的名称"
    assert updated.code == "TEST001"  # 未更新的字段保持不变


@pytest.mark.asyncio
async def test_delete(db_session):
    """测试删除"""
    service = TestService(db_session)
    
    # 先创建
    obj_in = TestCreate(name="测试对象", code="TEST001")
    created = await service.create(obj_in)
    
    # 再删除
    success = await service.delete(created.id)
    
    assert success is True
    
    # 验证已删除（应该抛出异常）
    # 注意：删除后，repository.get会返回None，service.get会抛出HTTPException
    from fastapi import HTTPException
    
    # 验证已删除 - service.get应该抛出HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await service.get(created.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_count(db_session):
    """测试统计"""
    service = TestService(db_session)
    
    # 创建测试数据
    await service.create(TestCreate(name="对象1", code="TEST001", status="ACTIVE"))
    await service.create(TestCreate(name="对象2", code="TEST002", status="ACTIVE"))
    await service.create(TestCreate(name="对象3", code="TEST003", status="INACTIVE"))
    
    # 统计总数
    total = await service.count()
    assert total == 3
    
    # 统计筛选后的数量
    active_count = await service.count(filters={"status": "ACTIVE"})
    assert active_count == 2
