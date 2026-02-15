# -*- coding: utf-8 -*-
"""
销售目标管理单元测试
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.sales.target_v2 import SalesTargetV2
from app.models.sales.team import SalesTeam
from app.services.sales_target_service import SalesTargetService
from app.services.sales_team_service import SalesTeamService
from app.schemas.sales_target import (
    SalesTargetV2Create,
    SalesTargetV2Update,
    TargetBreakdownRequest,
    TargetBreakdownItem,
    AutoBreakdownRequest,
)
from app.schemas.sales_team import SalesTeamCreate


class TestSalesTargetService:
    """销售目标服务测试"""
    
    def test_create_company_target(self, db: Session):
        """测试创建公司目标"""
        target_data = SalesTargetV2Create(
            target_period="year",
            target_year=2026,
            target_type="company",
            sales_target=Decimal("10000000"),
            payment_target=Decimal("8000000"),
            new_customer_target=50,
            lead_target=500,
            opportunity_target=200,
            deal_target=100
        )
        
        target = SalesTargetService.create_target(db, target_data, created_by=1)
        assert target.id is not None
        assert target.target_type == "company"
        assert target.sales_target == Decimal("10000000")
    
    def test_create_team_target(self, db: Session):
        """测试创建团队目标"""
        # 先创建团队
        team_data = SalesTeamCreate(
            team_code="T301",
            team_name="销售一部",
            team_type="REGION"
        )
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        
        target_data = SalesTargetV2Create(
            target_period="month",
            target_year=2026,
            target_month=3,
            target_type="team",
            team_id=team.id,
            sales_target=Decimal("500000"),
            payment_target=Decimal("400000")
        )
        
        target = SalesTargetService.create_target(db, target_data, created_by=1)
        assert target.team_id == team.id
        assert target.target_month == 3
    
    def test_create_personal_target(self, db: Session):
        """测试创建个人目标"""
        target_data = SalesTargetV2Create(
            target_period="quarter",
            target_year=2026,
            target_quarter=1,
            target_type="personal",
            user_id=1,
            sales_target=Decimal("100000"),
            deal_target=10
        )
        
        target = SalesTargetService.create_target(db, target_data, created_by=1)
        assert target.user_id == 1
        assert target.target_quarter == 1
    
    def test_update_target(self, db: Session):
        """测试更新目标"""
        target_data = SalesTargetV2Create(
            target_period="year",
            target_year=2026,
            target_type="company",
            sales_target=Decimal("5000000")
        )
        
        target = SalesTargetService.create_target(db, target_data, created_by=1)
        
        update_data = SalesTargetV2Update(
            sales_target=Decimal("6000000"),
            actual_sales=Decimal("3000000")
        )
        
        updated = SalesTargetService.update_target(db, target.id, update_data)
        assert updated.sales_target == Decimal("6000000")
        assert updated.actual_sales == Decimal("3000000")
    
    def test_delete_target(self, db: Session):
        """测试删除目标"""
        target_data = SalesTargetV2Create(
            target_period="year",
            target_year=2026,
            target_type="company",
            sales_target=Decimal("1000000")
        )
        
        target = SalesTargetService.create_target(db, target_data, created_by=1)
        result = SalesTargetService.delete_target(db, target.id)
        
        assert result is True
        assert SalesTargetService.get_target(db, target.id) is None
    
    def test_manual_breakdown(self, db: Session):
        """测试手动分解目标"""
        # 创建公司目标
        company_target = SalesTargetV2Create(
            target_period="year",
            target_year=2026,
            target_type="company",
            sales_target=Decimal("10000000")
        )
        target = SalesTargetService.create_target(db, company_target, created_by=1)
        
        # 创建两个团队
        team1_data = SalesTeamCreate(team_code="T401", team_name="Team1", team_type="REGION")
        team2_data = SalesTeamCreate(team_code="T402", team_name="Team2", team_type="REGION")
        team1 = SalesTeamService.create_team(db, team1_data, created_by=1)
        team2 = SalesTeamService.create_team(db, team2_data, created_by=1)
        
        # 手动分解
        breakdown_data = TargetBreakdownRequest(
            breakdown_items=[
                TargetBreakdownItem(
                    target_type="team",
                    team_id=team1.id,
                    sales_target=Decimal("6000000")
                ),
                TargetBreakdownItem(
                    target_type="team",
                    team_id=team2.id,
                    sales_target=Decimal("4000000")
                )
            ]
        )
        
        sub_targets = SalesTargetService.breakdown_target(db, target.id, breakdown_data, created_by=1)
        assert len(sub_targets) == 2
        assert all(t.parent_target_id == target.id for t in sub_targets)
    
    def test_auto_breakdown_equal(self, db: Session):
        """测试自动平均分解"""
        # 创建公司目标
        company_target = SalesTargetV2Create(
            target_period="year",
            target_year=2026,
            target_type="company",
            sales_target=Decimal("10000000")
        )
        target = SalesTargetService.create_target(db, company_target, created_by=1)
        
        # 创建3个顶级团队
        for i in range(3):
            team_data = SalesTeamCreate(
                team_code=f"T50{i}",
                team_name=f"Team{i}",
                team_type="REGION"
            )
            SalesTeamService.create_team(db, team_data, created_by=1)
        
        # 自动平均分解
        breakdown_data = AutoBreakdownRequest(breakdown_method="EQUAL")
        sub_targets = SalesTargetService.auto_breakdown_target(db, target.id, breakdown_data, created_by=1)
        
        assert len(sub_targets) == 3
        # 每个团队应该分配到约 3333333.33
        for t in sub_targets:
            assert abs(t.sales_target - Decimal("3333333.33")) < Decimal("0.01")
    
    def test_get_breakdown_tree(self, db: Session):
        """测试获取分解树"""
        # 创建公司目标
        company_target = SalesTargetV2Create(
            target_period="year",
            target_year=2026,
            target_type="company",
            sales_target=Decimal("5000000")
        )
        target = SalesTargetService.create_target(db, company_target, created_by=1)
        
        # 创建团队和分解
        team_data = SalesTeamCreate(team_code="T601", team_name="TeamA", team_type="REGION")
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        
        breakdown_data = TargetBreakdownRequest(
            breakdown_items=[
                TargetBreakdownItem(
                    target_type="team",
                    team_id=team.id,
                    sales_target=Decimal("5000000")
                )
            ]
        )
        SalesTargetService.breakdown_target(db, target.id, breakdown_data, created_by=1)
        
        tree = SalesTargetService.get_breakdown_tree(db, target.id)
        assert tree['id'] == target.id
        assert len(tree['sub_targets']) == 1


class TestSalesTargetStatistics:
    """销售目标统计测试"""
    
    def test_team_ranking(self, db: Session):
        """测试团队排名"""
        # 创建团队和目标
        for i in range(3):
            team_data = SalesTeamCreate(
                team_code=f"T70{i}",
                team_name=f"RankTeam{i}",
                team_type="REGION"
            )
            team = SalesTeamService.create_team(db, team_data, created_by=1)
            
            target_data = SalesTargetV2Create(
                target_period="year",
                target_year=2026,
                target_type="team",
                team_id=team.id,
                sales_target=Decimal("1000000"),
                actual_sales=Decimal(str(500000 * (i + 1)))
            )
            SalesTargetService.create_target(db, target_data, created_by=1)
        
        rankings = SalesTargetService.get_team_ranking(db, 2026)
        assert len(rankings) == 3
    
    def test_personal_ranking(self, db: Session):
        """测试个人排名"""
        # 创建个人目标
        for i in range(3):
            target_data = SalesTargetV2Create(
                target_period="year",
                target_year=2026,
                target_type="personal",
                user_id=i + 1,
                sales_target=Decimal("500000"),
                actual_sales=Decimal(str(100000 * (i + 1)))
            )
            SalesTargetService.create_target(db, target_data, created_by=1)
        
        rankings = SalesTargetService.get_personal_ranking(db, 2026)
        assert len(rankings) == 3
    
    def test_completion_distribution(self, db: Session):
        """测试完成率分布"""
        # 创建不同完成率的目标
        completion_rates = [10, 30, 50, 70, 90, 110]
        
        for rate in completion_rates:
            target_data = SalesTargetV2Create(
                target_period="year",
                target_year=2026,
                target_type="company",
                sales_target=Decimal("100000"),
                actual_sales=Decimal(str(100000 * rate // 100))
            )
            SalesTargetService.create_target(db, target_data, created_by=1)
        
        distribution = SalesTargetService.get_completion_distribution(db, 2026)
        assert 'distribution' in distribution
        assert len(distribution['distribution']) > 0


# Fixtures
@pytest.fixture
def db():
    """数据库会话 fixture"""
    from app.models.base import get_session, init_db
    
    init_db(database_url="sqlite:///:memory:", drop_all=True)
    session = get_session()
    
    yield session
    
    session.close()
