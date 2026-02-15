#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
销售团队管理功能验证脚本

用于快速验证销售团队管理功能是否正常工作
"""

import sys
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.base import init_db, get_session
from app.models.sales.team import SalesTeam, SalesTeamMember
from app.models.sales.target_v2 import SalesTargetV2
from app.models.sales.region import SalesRegion
from app.services.sales_team_service import SalesTeamService, SalesRegionService
from app.services.sales_target_service import SalesTargetService
from app.schemas.sales_team import (
    SalesTeamCreate,
    SalesTeamMemberCreate,
    SalesRegionCreate,
)
from app.schemas.sales_target import (
    SalesTargetV2Create,
    AutoBreakdownRequest,
)


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_success(message):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误消息"""
    print(f"❌ {message}")


def verify_sales_team(db: Session):
    """验证销售团队功能"""
    print_section("验证销售团队管理")
    
    try:
        # 1. 创建团队
        team_data = SalesTeamCreate(
            team_code="TEST_T001",
            team_name="测试团队",
            team_type="REGION",
            description="测试用团队"
        )
        team = SalesTeamService.create_team(db, team_data, created_by=1)
        print_success(f"创建团队成功: {team.team_name} (ID: {team.id})")
        
        # 2. 获取团队
        retrieved = SalesTeamService.get_team(db, team.id)
        assert retrieved is not None
        print_success("获取团队成功")
        
        # 3. 添加成员
        member_data = SalesTeamMemberCreate(
            team_id=team.id,
            user_id=1,
            role="MEMBER"
        )
        member = SalesTeamService.add_member(db, member_data)
        print_success(f"添加成员成功: User {member.user_id}")
        
        # 4. 获取团队树
        tree = SalesTeamService.get_team_tree(db)
        print_success(f"获取团队树成功: {len(tree)} 个顶级团队")
        
        return team
        
    except Exception as e:
        print_error(f"销售团队验证失败: {str(e)}")
        raise


def verify_sales_target(db: Session, team: SalesTeam):
    """验证销售目标功能"""
    print_section("验证销售目标管理")
    
    try:
        # 1. 创建公司目标
        company_target = SalesTargetV2Create(
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
        target = SalesTargetService.create_target(db, company_target, created_by=1)
        print_success(f"创建公司目标成功: {float(target.sales_target)}万 (ID: {target.id})")
        
        # 2. 创建团队目标
        team_target = SalesTargetV2Create(
            target_period="year",
            target_year=2026,
            target_type="team",
            team_id=team.id,
            sales_target=Decimal("3000000"),
            payment_target=Decimal("2400000")
        )
        team_target_obj = SalesTargetService.create_target(db, team_target, created_by=1)
        print_success(f"创建团队目标成功: {float(team_target_obj.sales_target)}万")
        
        # 3. 自动分解（如果有多个团队）
        # breakdown_req = AutoBreakdownRequest(breakdown_method="EQUAL")
        # sub_targets = SalesTargetService.auto_breakdown_target(db, target.id, breakdown_req, created_by=1)
        # print_success(f"自动分解成功: 分解为 {len(sub_targets)} 个子目标")
        
        # 4. 获取分解树
        tree = SalesTargetService.get_breakdown_tree(db, target.id)
        print_success(f"获取分解树成功: {len(tree.get('sub_targets', []))} 个子目标")
        
        # 5. 团队排名
        rankings = SalesTargetService.get_team_ranking(db, 2026)
        print_success(f"获取团队排名成功: {len(rankings)} 个团队")
        
        # 6. 完成率分布
        distribution = SalesTargetService.get_completion_distribution(db, 2026)
        print_success(f"获取完成率分布成功: {len(distribution.get('distribution', []))} 个区间")
        
        return target
        
    except Exception as e:
        print_error(f"销售目标验证失败: {str(e)}")
        raise


def verify_sales_region(db: Session, team: SalesTeam):
    """验证销售区域功能"""
    print_section("验证销售区域管理")
    
    try:
        # 1. 创建区域
        region_data = SalesRegionCreate(
            region_code="TEST_R001",
            region_name="测试区域",
            provinces=["江苏", "浙江"],
            cities=["南京", "杭州"],
            description="测试用区域"
        )
        region = SalesRegionService.create_region(db, region_data, created_by=1)
        print_success(f"创建区域成功: {region.region_name} (ID: {region.id})")
        
        # 2. 分配团队
        updated = SalesRegionService.assign_team(db, region.id, team.id, leader_id=1)
        print_success(f"分配团队成功: 区域 {region.region_name} → 团队 {team.team_name}")
        
        # 3. 获取区域列表
        regions = SalesRegionService.get_regions(db, skip=0, limit=10)
        print_success(f"获取区域列表成功: {len(regions)} 个区域")
        
        return region
        
    except Exception as e:
        print_error(f"销售区域验证失败: {str(e)}")
        raise


def cleanup(db: Session, team: SalesTeam = None, target: SalesTargetV2 = None, region: SalesRegion = None):
    """清理测试数据"""
    print_section("清理测试数据")
    
    try:
        if region:
            db.delete(region)
            print_success(f"删除测试区域: {region.region_name}")
        
        if target:
            db.delete(target)
            print_success(f"删除测试目标: ID {target.id}")
        
        if team:
            db.delete(team)
            print_success(f"删除测试团队: {team.team_name}")
        
        db.commit()
        print_success("清理完成")
        
    except Exception as e:
        print_error(f"清理失败: {str(e)}")
        db.rollback()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  销售团队管理功能验证")
    print("="*60)
    
    # 初始化数据库
    print("\n初始化数据库连接...")
    try:
        db = get_session()
        print_success("数据库连接成功")
    except Exception as e:
        print_error(f"数据库连接失败: {str(e)}")
        sys.exit(1)
    
    team = None
    target = None
    region = None
    
    try:
        # 验证销售团队
        team = verify_sales_team(db)
        
        # 验证销售目标
        target = verify_sales_target(db, team)
        
        # 验证销售区域
        region = verify_sales_region(db, team)
        
        # 打印总结
        print_section("验证结果总结")
        print_success("所有功能验证通过！")
        print("\n功能清单:")
        print("  ✅ 销售团队管理 (创建、查询、成员管理)")
        print("  ✅ 销售目标管理 (创建、分解、统计)")
        print("  ✅ 销售区域管理 (创建、分配)")
        
    except Exception as e:
        print_error(f"\n验证过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # 清理测试数据
        cleanup(db, team, target, region)
        db.close()
    
    print("\n" + "="*60)
    print("  验证完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
