# -*- coding: utf-8 -*-
"""
销售团队管理服务
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from fastapi import HTTPException

from app.models.sales.team import SalesTeam, SalesTeamMember
from app.models.sales.region import SalesRegion
from app.models import User, Department
from app.schemas.sales_team import (
    SalesTeamCreate,
    SalesTeamUpdate,
    SalesTeamMemberCreate,
    SalesTeamMemberUpdate,
    SalesRegionCreate,
    SalesRegionUpdate,
)
from app.utils.db_helpers import get_or_404, save_obj, delete_obj


class SalesTeamService:
    """销售团队服务类"""
    
    @staticmethod
    def create_team(db: Session, team_data: SalesTeamCreate, created_by: int) -> SalesTeam:
        """创建销售团队"""
        # 检查团队编码是否已存在
        existing = db.query(SalesTeam).filter(SalesTeam.team_code == team_data.team_code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"团队编码 {team_data.team_code} 已存在")
        
        # 创建团队
        team = SalesTeam(**team_data.model_dump(), created_by=created_by)
        save_obj(db, team)
        return team
    
    @staticmethod
    def get_team(db: Session, team_id: int) -> Optional[SalesTeam]:
        """获取团队详情"""
        return db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    
    @staticmethod
    def get_teams(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        team_type: Optional[str] = None,
        department_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> List[SalesTeam]:
        """获取团队列表"""
        query = db.query(SalesTeam)
        
        if team_type:
            query = query.filter(SalesTeam.team_type == team_type)
        if department_id:
            query = query.filter(SalesTeam.department_id == department_id)
        if is_active is not None:
            query = query.filter(SalesTeam.is_active == is_active)
        
        return query.order_by(SalesTeam.sort_order, SalesTeam.id).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_team(db: Session, team_id: int, team_data: SalesTeamUpdate) -> SalesTeam:
        """更新团队"""
        team = get_or_404(db, SalesTeam, team_id, detail="团队不存在")
        
        update_data = team_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(team, field, value)
        
        db.commit()
        db.refresh(team)
        return team
    
    @staticmethod
    def delete_team(db: Session, team_id: int) -> bool:
        """删除团队"""
        team = get_or_404(db, SalesTeam, team_id, detail="团队不存在")
        
        # 检查是否有子团队
        sub_teams = db.query(SalesTeam).filter(SalesTeam.parent_team_id == team_id).count()
        if sub_teams > 0:
            raise HTTPException(status_code=400, detail="存在子团队，无法删除")
        
        delete_obj(db, team)
        return True
    
    @staticmethod
    def get_team_tree(db: Session) -> List[Dict[str, Any]]:
        """获取团队组织树"""
        teams = db.query(SalesTeam).filter(SalesTeam.is_active == True).all()
        
        # 构建树形结构
        def build_tree(parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
            nodes = []
            for team in teams:
                if team.parent_team_id == parent_id:
                    node = {
                        'id': team.id,
                        'team_code': team.team_code,
                        'team_name': team.team_name,
                        'team_type': team.team_type,
                        'leader_id': team.leader_id,
                        'sub_teams': build_tree(team.id)
                    }
                    nodes.append(node)
            return nodes
        
        return build_tree()
    
    # ============= 团队成员管理 =============
    
    @staticmethod
    def add_member(db: Session, member_data: SalesTeamMemberCreate) -> SalesTeamMember:
        """添加团队成员"""
        # 检查用户是否已在团队中
        existing = db.query(SalesTeamMember).filter(
            and_(
                SalesTeamMember.team_id == member_data.team_id,
                SalesTeamMember.user_id == member_data.user_id,
                SalesTeamMember.is_active == True
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="用户已在该团队中")
        
        member = SalesTeamMember(**member_data.model_dump())
        save_obj(db, member)
        return member
    
    @staticmethod
    def get_team_members(db: Session, team_id: int, is_active: Optional[bool] = True) -> List[SalesTeamMember]:
        """获取团队成员列表"""
        query = db.query(SalesTeamMember).filter(SalesTeamMember.team_id == team_id)
        if is_active is not None:
            query = query.filter(SalesTeamMember.is_active == is_active)
        return query.all()
    
    @staticmethod
    def remove_member(db: Session, team_id: int, user_id: int) -> bool:
        """移除团队成员"""
        member = db.query(SalesTeamMember).filter(
            and_(
                SalesTeamMember.team_id == team_id,
                SalesTeamMember.user_id == user_id,
                SalesTeamMember.is_active == True
            )
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="成员不存在或已移除")
        
        # 软删除：设置为不活跃
        member.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def update_member_role(
        db: Session,
        team_id: int,
        user_id: int,
        member_data: SalesTeamMemberUpdate
    ) -> SalesTeamMember:
        """更新成员角色"""
        member = db.query(SalesTeamMember).filter(
            and_(
                SalesTeamMember.team_id == team_id,
                SalesTeamMember.user_id == user_id,
                SalesTeamMember.is_active == True
            )
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="成员不存在")
        
        update_data = member_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)
        
        db.commit()
        db.refresh(member)
        return member


class SalesRegionService:
    """销售区域服务类"""
    
    @staticmethod
    def create_region(db: Session, region_data: SalesRegionCreate, created_by: int) -> SalesRegion:
        """创建销售区域"""
        # 检查区域编码是否已存在
        existing = db.query(SalesRegion).filter(SalesRegion.region_code == region_data.region_code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"区域编码 {region_data.region_code} 已存在")
        
        region = SalesRegion(**region_data.model_dump(), created_by=created_by)
        save_obj(db, region)
        return region
    
    @staticmethod
    def get_region(db: Session, region_id: int) -> Optional[SalesRegion]:
        """获取区域详情"""
        return db.query(SalesRegion).filter(SalesRegion.id == region_id).first()
    
    @staticmethod
    def get_regions(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> List[SalesRegion]:
        """获取区域列表"""
        query = db.query(SalesRegion)
        
        if is_active is not None:
            query = query.filter(SalesRegion.is_active == is_active)
        
        return query.order_by(SalesRegion.sort_order, SalesRegion.id).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_region(db: Session, region_id: int, region_data: SalesRegionUpdate) -> SalesRegion:
        """更新区域"""
        region = get_or_404(db, SalesRegion, region_id, detail="区域不存在")
        
        update_data = region_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(region, field, value)
        
        db.commit()
        db.refresh(region)
        return region
    
    @staticmethod
    def assign_team(db: Session, region_id: int, team_id: int, leader_id: Optional[int] = None) -> SalesRegion:
        """分配团队"""
        region = get_or_404(db, SalesRegion, region_id, detail="区域不存在")
        
        # 检查团队是否存在
        team = get_or_404(db, SalesTeam, team_id, detail="团队不存在")
        
        region.team_id = team_id
        if leader_id:
            region.leader_id = leader_id
        
        db.commit()
        db.refresh(region)
        return region
