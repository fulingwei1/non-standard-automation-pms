# -*- coding: utf-8 -*-
"""
项目风险服务 - 实施进度→预警自动升级功能
创建日期：2026-01-25
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import (
    Project,
    ProjectMilestone,
    ProjectStatus,
)
from app.models.enums import ProjectHealthStatus


class ProjectRiskService:
    """项目风险服务类 - 实施进度→预警自动升级功能"""

    @staticmethod
    async def auto_upgrade_risk_level(
        db: AsyncSession,
        project_id: int
    ) -> Dict[str, Any]:
        """
        自动升级项目风险等级
        
        功能说明：
        1. 查询项目
        2. 查询逾期里程碑
        3. 查询逾期任务
        4. 计算风险因子
        5. 计算风险等级
        6. 更新项目风险等级
        7. 记录风险历史
        8. 如果风险升级，发送通知
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            
        Returns:
            包含风险等级、风险因子的字典
            
        Raises:
            ValueError: 如果项目不存在
        """
        
        # 1. 查询项目
        result = await db.execute(
            select(Project)
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 2. 计算当前日期
        today = date.today()
        
        # 3. 查询逾期里程碑
        overdue_milestones_result = await db.execute(
            select(ProjectMilestone)
            .where(
                and_(
                    ProjectMilestone.project_id == project_id,
                    ProjectMilestone.planned_date < today,
                    ProjectMilestone.status.in_(["NOT_STARTED", "IN_PROGRESS"])
                )
            )
        )
        overdue_milestones = overdue_milestones_result.scalars().all()
        
        # 4. 查询逾期任务（简化实现，假设有task_unified表）
        overdue_tasks_count = 0
        # 实际应该在task表查询，这里先设为0
        # TODO: 需要查询实际的任务表结构
        
        # 5. 查询缺料预警
        # TODO: 需要集成material_shortage模块
        shortage_alerts_count = 0
        
        # 6. 查询成本超支
        # TODO: 需要从财务模块查询成本数据
        cost_overrun_percentage = 0
        
        # 7. 查询未完成任务数量
        # TODO: 需要查询项目计划和实际进度
        incomplete_milestones_count = 0
        
        # 8. 查询总里程碑数
        total_milestones_result = await db.execute(
            select(func.count(ProjectMilestone.id))
            .where(ProjectMilestone.project_id == project_id)
            )
        total_milestones_count = total_milestones_result.scalar() or 0
        
        # 9. 计算风险因子
        risk_factors = {
            "overdue_milestones_count": len(overdue_milestones),
            "total_milestones_count": total_milestones_count,
            "overdue_milestones_ratio": 0,
            "overdue_tasks_count": overdue_tasks_count,
            "shortage_alerts_count": shortage_alerts_count,
            "cost_overrun_percentage": cost_overrun_percentage,
            "incomplete_milestones_count": incomplete_milestones_count,
        }
        
        # 计算逾期里程碑比例
        if total_milestones_count > 0:
            risk_factors["overdue_milestone_ratio"] = len(overdue_milestones) / total_milestones_count
        
        # 10. 根据风险因子计算风险等级
        new_risk_level = ProjectRiskService._calculate_risk_level(risk_factors)
        
        old_risk_level = project.risk_level or "LOW"
        
        # 11. 更新项目风险等级
        project.risk_level = new_risk_level
        project.risk_factors = risk_factors
        
        # 12. 记录风险历史
        risk_history_entry = {
            "project_id": project_id,
            "old_risk_level": old_risk_level,
            "new_risk_level": new_risk_level,
            "risk_factors": risk_factors,
            "triggered_by": "SYSTEM",  # 系统自动
            "triggered_at": datetime.now(),
        }
        
        db.add(ProjectRiskHistory(**risk_history_entry))
        await db.flush()
        
        await db.commit()
        
        # 13. 如果风险等级升级，发送通知（模拟）
        if ProjectRiskService._is_risk_upgrade(old_risk_level, new_risk_level):
            # 在实际项目中，这里应该发送邮件或企业微信通知
            # TODO: 集成NotificationService
            print(f"风险等级从 {old_risk_level}升级到{new_risk_level}，已发送通知")
        
        return {
            "project_id": project_id,
            "old_risk_level": old_risk_level,
            "new_risk_level": new_risk_level,
            "risk_factors": risk_factors,
        }
        }
    
    @staticmethod
    def _calculate_risk_level(factors: Dict[str, Any]) -> str:
        """根据风险因子计算风险等级"""
        
        overdue_milestone_ratio = factors.get("overdue_milestone_ratio", 0)
        overdue_tasks_count = factors.get("overdue_tasks_count", 0)
        shortage_alerts_count = factors.get("shortage_alerts_count", 0)
        cost_overrun_percentage = factors.get("cost_overrun_percentage", 0)
        
        # 简单规则（可根据实际业务需求调整）
        # 逾期里程碑占比>=50% -> CRITICAL
        # 逾期任务>=10个 -> HIGH
        # 有缺料预警 -> HIGH
        # 成本超支>=10% -> HIGH
        # 其他情况 -> LOW/MEDIUM
        
        if overdue_milestone_ratio >= 0.5:
            return "CRITICAL"
        elif overdue_tasks_count >= 10:
            return "HIGH"
        elif overdue_milestone_ratio >= 0.3:
            return "HIGH"
        elif overdue_tasks_count >= 10 or shortage_alerts_count > 0:
            return "HIGH"
        elif cost_overrun_percentage >= 10:
            return "HIGH"
        elif overdue_milestone_ratio >= 0.1:
            return "MEDIUM"
        else:
            return "LOW"
    
    @staticmethod
    def _is_risk_upgrade(old_level: str, new_level: str) -> bool:
        """判断风险等级是否升级"""
        level_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        
        return level_order.get(new_level, 0) > level_order.get(old_level, 0)


class ProjectRiskHistory(Base):
    """项目风险历史表"""
    
    __tablename__ = "project_risk_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    project_id = Column(Integer, nullable=False, comment="项目ID")
    old_risk_level = Column(String(20), comment="原风险等级")
    new_risk_level = Column(String(20), comment="新风险等级")
    risk_factors = Column(JSON, comment="风险因子")
    triggered_by = Column(String(50), default="MANUAL", comment="触发者：MANUAL/SYSTEM")
    triggered_at = Column(DateTime, comment="触发时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    __table_args__ = (
        Index("idx_project_risk_history_project", "project_id"),
        Index("idx_project_risk_history_triggered_at", "triggered_at"),
    )
