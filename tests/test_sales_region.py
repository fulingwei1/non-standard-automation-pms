# -*- coding: utf-8 -*-
"""
销售区域管理单元测试
"""

import pytest
from sqlalchemy.orm import Session

from app.models.sales.region import SalesRegion
from app.services.sales_team_service import SalesRegionService, SalesTeamService
from app.schemas.sales_team import (
    SalesRegionCreate,
    SalesRegionUpdate,
    SalesTeamCreate,
)


class TestSalesRegionService:
    """销售区域服务测试"""
    
    def test_create_region(self, db: Session):
        """测试创建销售区域"""
        region_data = SalesRegionCreate(
            region_code="R001",
            region_name="华东区",
            provinces=["江苏", "浙江", "上海"],
            cities=["南京", "杭州", "上海"]
        )
        
        region = SalesRegionService.create_region(db, region_data, created_by=1)
        assert region.id is not None
        assert region.region_code == "R001"
        assert region.region_name == "华东区"
        assert len(region.provinces) == 3
    
    def test_create_duplicate_region_code(self, db: Session):
        """测试创建重复区域编码"""
        region_data = SalesRegionCreate(
            region_code="R002",
            region_name="华南区"
        )
        
        SalesRegionService.create_region(db, region_data, created_by=1)
        
        with pytest.raises(Exception):
            SalesRegionService.create_region(db, region_data, created_by=1)
    
    def test_get_region(self, db: Session):
        """测试获取区域详情"""
        region_data = SalesRegionCreate(
            region_code="R003",
            region_name="华北区"
        )
        
        region = SalesRegionService.create_region(db, region_data, created_by=1)
        retrieved = SalesRegionService.get_region(db, region.id)
        
        assert retrieved is not None
        assert retrieved.id == region.id
        assert retrieved.region_code == "R003"
    
    def test_update_region(self, db: Session):
        """测试更新区域"""
        region_data = SalesRegionCreate(
            region_code="R004",
            region_name="西南区"
        )
        
        region = SalesRegionService.create_region(db, region_data, created_by=1)
        
        update_data = SalesRegionUpdate(
            region_name="西南大区",
            description="覆盖四川、重庆等地"
        )
        
        updated = SalesRegionService.update_region(db, region.id, update_data)
        assert updated.region_name == "西南大区"
        assert updated.description == "覆盖四川、重庆等地"
    
    def test_assign_team(self, db: Session):
        """测试分配团队"""
        # 创建区域
        region_data = SalesRegionCreate(
            region_code="R005",
            region_name="华中区"
        )
        region = SalesRegionService.create_region(db, region_data, created_by=1)
        
        # 创建团队
        team_data = SalesTeamCreate(
            team_code="T801",
            team_name="华中团队",
            team_type="REGION"
        )
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        
        # 分配团队
        updated = SalesRegionService.assign_team(db, region.id, team.id, leader_id=1)
        
        assert updated.team_id == team.id
        assert updated.leader_id == 1
    
    def test_hierarchical_regions(self, db: Session):
        """测试层级区域"""
        # 创建父区域
        parent_data = SalesRegionCreate(
            region_code="R100",
            region_name="中国区",
            level=1
        )
        parent = SalesRegionService.create_region(db, parent_data, created_by=1)
        
        # 创建子区域
        sub_data = SalesRegionCreate(
            region_code="R101",
            region_name="华东省",
            parent_region_id=parent.id,
            level=2
        )
        sub = SalesRegionService.create_region(db, sub_data, created_by=1)
        
        assert sub.parent_region_id == parent.id
        assert sub.level == 2
    
    def test_get_regions_list(self, db: Session):
        """测试获取区域列表"""
        # 创建多个区域
        for i in range(5):
            region_data = SalesRegionCreate(
                region_code=f"R20{i}",
                region_name=f"区域{i}"
            )
            SalesRegionService.create_region(db, region_data, created_by=1)
        
        regions = SalesRegionService.get_regions(db, skip=0, limit=10)
        assert len(regions) >= 5


# Fixtures
@pytest.fixture
def db():
    """数据库会话 fixture"""
    from app.models.base import get_session, init_db
    
    init_db(database_url="sqlite:///:memory:", drop_all=True)
    session = get_session()
    
    yield session
    
    session.close()
