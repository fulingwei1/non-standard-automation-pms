# -*- coding: utf-8 -*-
"""
销售团队管理单元测试
"""

import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.sales.team import SalesTeam, SalesTeamMember
from app.services.sales_team_service import SalesTeamService
from app.schemas.sales_team import (
    SalesTeamCreate,
    SalesTeamUpdate,
    SalesTeamMemberCreate,
    SalesTeamMemberUpdate,
)


class TestSalesTeamService:
    """销售团队服务测试"""
    
    def test_create_team(self, db: Session):
        """测试创建销售团队"""
        team_data = SalesTeamCreate(
            team_code="T001",
            team_name="华东团队",
            team_type="REGION",
            description="负责华东区域销售"
        )
        
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        assert team.id is not None
        assert team.team_code == "T001"
        assert team.team_name == "华东团队"
    
    def test_create_duplicate_team_code(self, db: Session):
        """测试创建重复团队编码"""
        team_data = SalesTeamCreate(
            team_code="T002",
            team_name="华南团队",
            team_type="REGION"
        )
        
        SalesTeamService.create_team(db, team_data, created_by=1)
        
        # 尝试创建相同编码的团队
        with pytest.raises(Exception):
            SalesTeamService.create_team(db, team_data, created_by=1)
    
    def test_get_team(self, db: Session):
        """测试获取团队详情"""
        team_data = SalesTeamCreate(
            team_code="T003",
            team_name="华北团队",
            team_type="REGION"
        )
        
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        retrieved = SalesTeamService.get_team(db, team.id)
        
        assert retrieved is not None
        assert retrieved.id == team.id
        assert retrieved.team_code == "T003"
    
    def test_update_team(self, db: Session):
        """测试更新团队"""
        team_data = SalesTeamCreate(
            team_code="T004",
            team_name="西南团队",
            team_type="REGION"
        )
        
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        
        update_data = SalesTeamUpdate(
            team_name="西南大区",
            description="负责西南区域销售业务"
        )
        
        updated = SalesTeamService.update_team(db, team.id, update_data)
        assert updated.team_name == "西南大区"
        assert updated.description == "负责西南区域销售业务"
    
    def test_delete_team(self, db: Session):
        """测试删除团队"""
        team_data = SalesTeamCreate(
            team_code="T005",
            team_name="西北团队",
            team_type="REGION"
        )
        
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        result = SalesTeamService.delete_team(db, team.id)
        
        assert result is True
        assert SalesTeamService.get_team(db, team.id) is None
    
    def test_get_team_tree(self, db: Session):
        """测试获取团队组织树"""
        # 创建父团队
        parent_data = SalesTeamCreate(
            team_code="T100",
            team_name="销售总部",
            team_type="REGION"
        )
        parent = SalesTeamService.create_team(db, parent_data, created_by=1)
        
        # 创建子团队
        sub_data = SalesTeamCreate(
            team_code="T101",
            team_name="华东分部",
            team_type="REGION",
            parent_team_id=parent.id
        )
        SalesTeamService.create_team(db, sub_data, created_by=1)
        
        tree = SalesTeamService.get_team_tree(db)
        assert len(tree) > 0
        assert any(node['team_code'] == 'T100' for node in tree)


class TestSalesTeamMember:
    """销售团队成员测试"""
    
    def test_add_member(self, db: Session):
        """测试添加团队成员"""
        # 先创建团队
        team_data = SalesTeamCreate(
            team_code="T201",
            team_name="产品团队",
            team_type="PRODUCT"
        )
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        
        # 添加成员
        member_data = SalesTeamMemberCreate(
            team_id=team.id,
            user_id=1,
            role="MEMBER"
        )
        
        member = SalesTeamService.add_member(db, member_data)
        assert member.id is not None
        assert member.team_id == team.id
        assert member.user_id == 1
    
    def test_remove_member(self, db: Session):
        """测试移除团队成员"""
        team_data = SalesTeamCreate(
            team_code="T202",
            team_name="行业团队",
            team_type="INDUSTRY"
        )
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        
        member_data = SalesTeamMemberCreate(
            team_id=team.id,
            user_id=2,
            role="MEMBER"
        )
        SalesTeamService.add_member(db, member_data)
        
        result = SalesTeamService.remove_member(db, team.id, 2)
        assert result is True
    
    def test_update_member_role(self, db: Session):
        """测试更新成员角色"""
        team_data = SalesTeamCreate(
            team_code="T203",
            team_name="大客户团队",
            team_type="OTHER"
        )
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        
        member_data = SalesTeamMemberCreate(
            team_id=team.id,
            user_id=3,
            role="MEMBER"
        )
        SalesTeamService.add_member(db, member_data)
        
        update_data = SalesTeamMemberUpdate(role="LEADER")
        updated = SalesTeamService.update_member_role(db, team.id, 3, update_data)
        
        assert updated.role == "LEADER"


# Fixtures
@pytest.fixture
def db():
    """数据库会话 fixture（需要根据实际项目配置）"""
    from app.models.base import get_session, init_db
    
    # 使用测试数据库
    init_db(database_url="sqlite:///:memory:", drop_all=True)
    session = get_session()
    
    yield session
    
    session.close()
