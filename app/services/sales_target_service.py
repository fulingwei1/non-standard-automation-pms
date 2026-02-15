# -*- coding: utf-8 -*-
"""
销售目标管理服务
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException
import json

from app.models.sales.target_v2 import SalesTargetV2, TargetBreakdownLog
from app.models.sales.team import SalesTeam, SalesTeamMember
from app.models import User
from app.schemas.sales_target import (
    SalesTargetV2Create,
    SalesTargetV2Update,
    TargetBreakdownRequest,
    AutoBreakdownRequest,
)


class SalesTargetService:
    """销售目标服务类"""
    
    @staticmethod
    def create_target(db: Session, target_data: SalesTargetV2Create, created_by: int) -> SalesTargetV2:
        """创建销售目标"""
        # 验证目标类型和对应的ID
        if target_data.target_type == 'team' and not target_data.team_id:
            raise HTTPException(status_code=400, detail="团队目标必须指定team_id")
        if target_data.target_type == 'personal' and not target_data.user_id:
            raise HTTPException(status_code=400, detail="个人目标必须指定user_id")
        
        # 检查目标是否已存在
        existing = db.query(SalesTargetV2).filter(
            and_(
                SalesTargetV2.target_period == target_data.target_period,
                SalesTargetV2.target_year == target_data.target_year,
                SalesTargetV2.target_type == target_data.target_type,
                or_(
                    SalesTargetV2.team_id == target_data.team_id if target_data.team_id else False,
                    SalesTargetV2.user_id == target_data.user_id if target_data.user_id else False
                )
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="该期间的目标已存在")
        
        target = SalesTargetV2(**target_data.model_dump(), created_by=created_by)
        db.add(target)
        db.commit()
        db.refresh(target)
        return target
    
    @staticmethod
    def get_target(db: Session, target_id: int) -> Optional[SalesTargetV2]:
        """获取目标详情"""
        return db.query(SalesTargetV2).filter(SalesTargetV2.id == target_id).first()
    
    @staticmethod
    def get_targets(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        target_type: Optional[str] = None,
        target_period: Optional[str] = None,
        target_year: Optional[int] = None,
        target_month: Optional[int] = None,
        team_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> List[SalesTargetV2]:
        """获取目标列表"""
        query = db.query(SalesTargetV2)
        
        if target_type:
            query = query.filter(SalesTargetV2.target_type == target_type)
        if target_period:
            query = query.filter(SalesTargetV2.target_period == target_period)
        if target_year:
            query = query.filter(SalesTargetV2.target_year == target_year)
        if target_month:
            query = query.filter(SalesTargetV2.target_month == target_month)
        if team_id:
            query = query.filter(SalesTargetV2.team_id == team_id)
        if user_id:
            query = query.filter(SalesTargetV2.user_id == user_id)
        
        return query.order_by(desc(SalesTargetV2.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_target(db: Session, target_id: int, target_data: SalesTargetV2Update) -> SalesTargetV2:
        """更新目标"""
        target = db.query(SalesTargetV2).filter(SalesTargetV2.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="目标不存在")
        
        update_data = target_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(target, field, value)
        
        # 重新计算完成率
        target.completion_rate = SalesTargetService._calculate_completion_rate(target)
        
        db.commit()
        db.refresh(target)
        return target
    
    @staticmethod
    def delete_target(db: Session, target_id: int) -> bool:
        """删除目标"""
        target = db.query(SalesTargetV2).filter(SalesTargetV2.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="目标不存在")
        
        # 检查是否有子目标
        sub_targets = db.query(SalesTargetV2).filter(SalesTargetV2.parent_target_id == target_id).count()
        if sub_targets > 0:
            raise HTTPException(status_code=400, detail="存在子目标，无法删除")
        
        db.delete(target)
        db.commit()
        return True
    
    # ============= 目标分解 =============
    
    @staticmethod
    def breakdown_target(
        db: Session,
        target_id: int,
        breakdown_data: TargetBreakdownRequest,
        created_by: int
    ) -> List[SalesTargetV2]:
        """手动分解目标"""
        parent_target = db.query(SalesTargetV2).filter(SalesTargetV2.id == target_id).first()
        if not parent_target:
            raise HTTPException(status_code=404, detail="上级目标不存在")
        
        created_targets = []
        breakdown_details = []
        
        for item in breakdown_data.breakdown_items:
            target = SalesTargetV2(
                target_period=parent_target.target_period,
                target_year=parent_target.target_year,
                target_month=parent_target.target_month,
                target_quarter=parent_target.target_quarter,
                target_type=item.target_type,
                team_id=item.team_id,
                user_id=item.user_id,
                sales_target=item.sales_target,
                payment_target=item.payment_target,
                new_customer_target=item.new_customer_target,
                lead_target=item.lead_target,
                opportunity_target=item.opportunity_target,
                deal_target=item.deal_target,
                parent_target_id=target_id,
                created_by=created_by
            )
            db.add(target)
            created_targets.append(target)
            
            breakdown_details.append({
                'target_type': item.target_type,
                'team_id': item.team_id,
                'user_id': item.user_id,
                'sales_target': float(item.sales_target),
            })
        
        # 记录分解日志
        log = TargetBreakdownLog(
            parent_target_id=target_id,
            breakdown_type='MANUAL',
            breakdown_method='CUSTOM',
            breakdown_details=json.dumps(breakdown_details),
            created_by=created_by
        )
        db.add(log)
        
        db.commit()
        for target in created_targets:
            db.refresh(target)
        
        return created_targets
    
    @staticmethod
    def auto_breakdown_target(
        db: Session,
        target_id: int,
        breakdown_data: AutoBreakdownRequest,
        created_by: int
    ) -> List[SalesTargetV2]:
        """自动分解目标"""
        parent_target = db.query(SalesTargetV2).filter(SalesTargetV2.id == target_id).first()
        if not parent_target:
            raise HTTPException(status_code=404, detail="上级目标不存在")
        
        # 根据上级目标类型确定分解对象
        if parent_target.target_type == 'company':
            # 公司目标分解到团队
            targets = db.query(SalesTeam).filter(
                SalesTeam.is_active == True,
                SalesTeam.parent_team_id == None  # 只分解到顶级团队
            ).all()
            target_type = 'team'
        elif parent_target.target_type == 'team':
            # 团队目标分解到个人
            members = db.query(SalesTeamMember).filter(
                SalesTeamMember.team_id == parent_target.team_id,
                SalesTeamMember.is_active == True
            ).all()
            targets = [m.user for m in members]
            target_type = 'personal'
        else:
            raise HTTPException(status_code=400, detail="个人目标无法再分解")
        
        if not targets:
            raise HTTPException(status_code=400, detail="没有可分解的对象")
        
        # 计算每个对象的目标值
        count = len(targets)
        created_targets = []
        breakdown_details = []
        
        if breakdown_data.breakdown_method == 'EQUAL':
            # 平均分配
            for target in targets:
                sub_target = SalesTargetV2(
                    target_period=parent_target.target_period,
                    target_year=parent_target.target_year,
                    target_month=parent_target.target_month,
                    target_quarter=parent_target.target_quarter,
                    target_type=target_type,
                    team_id=target.id if target_type == 'team' else None,
                    user_id=target.id if target_type == 'personal' else None,
                    sales_target=parent_target.sales_target / count,
                    payment_target=parent_target.payment_target / count,
                    new_customer_target=int(parent_target.new_customer_target / count),
                    lead_target=int(parent_target.lead_target / count),
                    opportunity_target=int(parent_target.opportunity_target / count),
                    deal_target=int(parent_target.deal_target / count),
                    parent_target_id=target_id,
                    created_by=created_by
                )
                db.add(sub_target)
                created_targets.append(sub_target)
                
                breakdown_details.append({
                    'target_type': target_type,
                    'id': target.id,
                    'sales_target': float(sub_target.sales_target),
                })
        
        # 记录分解日志
        log = TargetBreakdownLog(
            parent_target_id=target_id,
            breakdown_type='AUTO',
            breakdown_method=breakdown_data.breakdown_method,
            breakdown_details=json.dumps(breakdown_details),
            created_by=created_by
        )
        db.add(log)
        
        db.commit()
        for target in created_targets:
            db.refresh(target)
        
        return created_targets
    
    @staticmethod
    def get_breakdown_tree(db: Session, target_id: int) -> Dict[str, Any]:
        """获取目标分解树"""
        target = db.query(SalesTargetV2).filter(SalesTargetV2.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="目标不存在")
        
        def build_tree(target_obj: SalesTargetV2) -> Dict[str, Any]:
            sub_targets = db.query(SalesTargetV2).filter(
                SalesTargetV2.parent_target_id == target_obj.id
            ).all()
            
            return {
                'id': target_obj.id,
                'target_type': target_obj.target_type,
                'team_id': target_obj.team_id,
                'user_id': target_obj.user_id,
                'sales_target': float(target_obj.sales_target),
                'actual_sales': float(target_obj.actual_sales),
                'completion_rate': float(target_obj.completion_rate),
                'sub_targets': [build_tree(sub) for sub in sub_targets]
            }
        
        return build_tree(target)
    
    # ============= 统计分析 =============
    
    @staticmethod
    def get_team_ranking(
        db: Session,
        target_year: int,
        target_month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取团队排名"""
        query = db.query(SalesTargetV2).filter(
            and_(
                SalesTargetV2.target_type == 'team',
                SalesTargetV2.target_year == target_year
            )
        )
        
        if target_month:
            query = query.filter(SalesTargetV2.target_month == target_month)
        
        targets = query.order_by(desc(SalesTargetV2.completion_rate)).all()
        
        rankings = []
        for idx, target in enumerate(targets, 1):
            rankings.append({
                'rank': idx,
                'team_id': target.team_id,
                'sales_target': float(target.sales_target),
                'actual_sales': float(target.actual_sales),
                'completion_rate': float(target.completion_rate),
            })
        
        return rankings
    
    @staticmethod
    def get_personal_ranking(
        db: Session,
        target_year: int,
        target_month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取个人排名"""
        query = db.query(SalesTargetV2).filter(
            and_(
                SalesTargetV2.target_type == 'personal',
                SalesTargetV2.target_year == target_year
            )
        )
        
        if target_month:
            query = query.filter(SalesTargetV2.target_month == target_month)
        
        targets = query.order_by(desc(SalesTargetV2.completion_rate)).all()
        
        rankings = []
        for idx, target in enumerate(targets, 1):
            rankings.append({
                'rank': idx,
                'user_id': target.user_id,
                'sales_target': float(target.sales_target),
                'actual_sales': float(target.actual_sales),
                'completion_rate': float(target.completion_rate),
            })
        
        return rankings
    
    @staticmethod
    def get_completion_trend(
        db: Session,
        target_id: int
    ) -> List[Dict[str, Any]]:
        """获取完成趋势（简化版，实际应该记录历史快照）"""
        target = db.query(SalesTargetV2).filter(SalesTargetV2.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="目标不存在")
        
        # 简化版：只返回当前状态
        return [{
            'date': datetime.now().strftime('%Y-%m-%d'),
            'completion_rate': float(target.completion_rate),
            'actual_sales': float(target.actual_sales),
            'target_sales': float(target.sales_target),
        }]
    
    @staticmethod
    def get_completion_distribution(
        db: Session,
        target_year: int,
        target_month: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取完成率分布"""
        query = db.query(SalesTargetV2).filter(SalesTargetV2.target_year == target_year)
        
        if target_month:
            query = query.filter(SalesTargetV2.target_month == target_month)
        
        targets = query.all()
        
        # 统计分布
        distribution = {
            '0-20%': 0,
            '20-40%': 0,
            '40-60%': 0,
            '60-80%': 0,
            '80-100%': 0,
            '100%+': 0,
        }
        
        for target in targets:
            rate = float(target.completion_rate)
            if rate < 20:
                distribution['0-20%'] += 1
            elif rate < 40:
                distribution['20-40%'] += 1
            elif rate < 60:
                distribution['40-60%'] += 1
            elif rate < 80:
                distribution['60-80%'] += 1
            elif rate < 100:
                distribution['80-100%'] += 1
            else:
                distribution['100%+'] += 1
        
        return {
            'period': f"{target_year}-{target_month or '全年'}",
            'distribution': [{'range_label': k, 'count': v} for k, v in distribution.items()]
        }
    
    # ============= 辅助方法 =============
    
    @staticmethod
    def _calculate_completion_rate(target: SalesTargetV2) -> Decimal:
        """计算完成率"""
        if target.sales_target == 0:
            return Decimal('0')
        return (target.actual_sales / target.sales_target * 100).quantize(Decimal('0.01'))
