# -*- coding: utf-8 -*-
"""
项目风险服务层
处理风险管理的核心业务逻辑
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.project_risk import ProjectRisk, RiskTypeEnum, RiskStatusEnum
from app.models.project import Project
from app.models.user import User
from app.utils.db_helpers import delete_obj, get_or_404, save_obj


class ProjectRiskService:
    """项目风险管理服务"""
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def generate_risk_code(self, project_id: int) -> str:
        """
        生成风险编号
        
        Args:
            project_id: 项目ID
            
        Returns:
            风险编号，格式：RISK-{项目代码}-{序号}
        """
        project = get_or_404(self.db, Project, project_id, detail="项目不存在")
        count = self.db.query(ProjectRisk).filter(
            ProjectRisk.project_id == project_id
        ).count()
        return f"RISK-{project.project_code}-{count + 1:04d}"
    
    def create_risk(
        self,
        project_id: int,
        risk_name: str,
        description: Optional[str],
        risk_type: str,
        probability: int,
        impact: int,
        mitigation_plan: Optional[str],
        contingency_plan: Optional[str],
        owner_id: Optional[int],
        target_closure_date: Optional[datetime],
        current_user: User,
    ) -> ProjectRisk:
        """
        创建项目风险
        
        Args:
            project_id: 项目ID
            risk_name: 风险名称
            description: 风险描述
            risk_type: 风险类型
            probability: 概率 (1-5)
            impact: 影响 (1-5)
            mitigation_plan: 缓解计划
            contingency_plan: 应急计划
            owner_id: 负责人ID
            target_closure_date: 目标关闭日期
            current_user: 当前用户
            
        Returns:
            创建的风险对象
        """
        # 检查项目是否存在
        get_or_404(self.db, Project, project_id, detail="项目不存在")
        
        # 生成风险编号
        risk_code = self.generate_risk_code(project_id)
        
        # 创建风险对象
        risk = ProjectRisk(
            risk_code=risk_code,
            project_id=project_id,
            risk_name=risk_name,
            description=description,
            risk_type=risk_type,
            probability=probability,
            impact=impact,
            mitigation_plan=mitigation_plan,
            contingency_plan=contingency_plan,
            owner_id=owner_id,
            target_closure_date=target_closure_date,
            status=RiskStatusEnum.IDENTIFIED,
            created_by_id=current_user.id,
            created_by_name=current_user.real_name or current_user.username,
        )
        
        # 如果有负责人，设置负责人姓名
        if owner_id:
            owner = self.db.query(User).filter(User.id == owner_id).first()
            if owner:
                risk.owner_name = owner.real_name or owner.username
        
        # 计算风险评分
        risk.calculate_risk_score()
        
        save_obj(self.db, risk)
        return risk
    
    def get_risk_list(
        self,
        project_id: int,
        risk_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        owner_id: Optional[int] = None,
        is_occurred: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ProjectRisk], int]:
        """
        获取风险列表
        
        Args:
            project_id: 项目ID
            risk_type: 风险类型筛选
            risk_level: 风险等级筛选
            status: 状态筛选
            owner_id: 负责人筛选
            is_occurred: 是否已发生
            offset: 分页偏移量
            limit: 分页大小
            
        Returns:
            (风险列表, 总数)
        """
        # 检查项目是否存在
        get_or_404(self.db, Project, project_id, detail="项目不存在")
        
        # 构建查询
        query = self.db.query(ProjectRisk).filter(ProjectRisk.project_id == project_id)
        
        # 应用筛选
        if risk_type:
            query = query.filter(ProjectRisk.risk_type == risk_type)
        if risk_level:
            query = query.filter(ProjectRisk.risk_level == risk_level)
        if status:
            query = query.filter(ProjectRisk.status == status)
        if owner_id:
            query = query.filter(ProjectRisk.owner_id == owner_id)
        if is_occurred is not None:
            query = query.filter(ProjectRisk.is_occurred == is_occurred)
        
        # 获取总数
        total = query.count()
        
        # 应用分页并排序
        risks = query.order_by(
            desc(ProjectRisk.risk_score),
            desc(ProjectRisk.created_at)
        ).offset(offset).limit(limit).all()
        
        return risks, total
    
    def get_risk_by_id(self, project_id: int, risk_id: int) -> ProjectRisk:
        """
        获取风险详情
        
        Args:
            project_id: 项目ID
            risk_id: 风险ID
            
        Returns:
            风险对象
            
        Raises:
            HTTPException: 风险不存在时抛出404
        """
        risk = self.db.query(ProjectRisk).filter(
            and_(
                ProjectRisk.id == risk_id,
                ProjectRisk.project_id == project_id
            )
        ).first()
        
        if not risk:
            raise HTTPException(status_code=404, detail="风险不存在")
        
        return risk
    
    def update_risk(
        self,
        project_id: int,
        risk_id: int,
        update_data: Dict[str, Any],
        current_user: User,
    ) -> ProjectRisk:
        """
        更新风险信息
        
        Args:
            project_id: 项目ID
            risk_id: 风险ID
            update_data: 更新数据字典
            current_user: 当前用户
            
        Returns:
            更新后的风险对象
            
        Raises:
            HTTPException: 风险不存在时抛出404
        """
        risk = self.get_risk_by_id(project_id, risk_id)
        
        # 更新字段
        for field, value in update_data.items():
            if hasattr(risk, field):
                setattr(risk, field, value)
        
        # 如果概率或影响发生变化，重新计算评分
        if "probability" in update_data or "impact" in update_data:
            risk.calculate_risk_score()
        
        # 如果负责人变化，更新负责人姓名
        if "owner_id" in update_data and update_data["owner_id"]:
            owner = self.db.query(User).filter(
                User.id == update_data["owner_id"]
            ).first()
            if owner:
                risk.owner_name = owner.real_name or owner.username
        
        # 更新审计字段
        risk.updated_by_id = current_user.id
        risk.updated_by_name = current_user.real_name or current_user.username
        
        # 如果状态变为已关闭，设置关闭日期
        if update_data.get("status") == "CLOSED" and not risk.actual_closure_date:
            risk.actual_closure_date = datetime.now()
        
        self.db.commit()
        self.db.refresh(risk)
        
        return risk
    
    def delete_risk(self, project_id: int, risk_id: int) -> Dict[str, Any]:
        """
        删除风险
        
        Args:
            project_id: 项目ID
            risk_id: 风险ID
            
        Returns:
            删除的风险信息字典
            
        Raises:
            HTTPException: 风险不存在时抛出404
        """
        risk = self.get_risk_by_id(project_id, risk_id)
        
        # 记录删除信息
        risk_info = {
            "risk_code": risk.risk_code,
            "risk_name": risk.risk_name,
            "risk_type": risk.risk_type,
            "risk_score": risk.risk_score,
        }
        
        delete_obj(self.db, risk)
        
        return risk_info
    
    def get_risk_matrix(self, project_id: int) -> Dict[str, Any]:
        """
        获取风险矩阵（概率×影响）
        
        Args:
            project_id: 项目ID
            
        Returns:
            包含矩阵数据和汇总统计的字典
        """
        # 检查项目是否存在
        get_or_404(self.db, Project, project_id, detail="项目不存在")
        
        # 获取所有未关闭的风险
        risks = self.db.query(ProjectRisk).filter(
            and_(
                ProjectRisk.project_id == project_id,
                ProjectRisk.status != RiskStatusEnum.CLOSED
            )
        ).all()
        
        # 构建矩阵数据
        matrix_data = {}
        for prob in range(1, 6):
            for imp in range(1, 6):
                key = f"{prob}_{imp}"
                matrix_data[key] = []
        
        # 填充矩阵
        for risk in risks:
            key = f"{risk.probability}_{risk.impact}"
            matrix_data[key].append({
                "id": risk.id,
                "risk_code": risk.risk_code,
                "risk_name": risk.risk_name,
                "risk_type": risk.risk_type,
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
            })
        
        # 转换为列表格式
        matrix = []
        for prob in range(1, 6):
            for imp in range(1, 6):
                key = f"{prob}_{imp}"
                risks_in_cell = matrix_data[key]
                matrix.append({
                    "probability": prob,
                    "impact": imp,
                    "count": len(risks_in_cell),
                    "risks": risks_in_cell,
                })
        
        # 计算汇总统计
        summary = {
            "total_risks": len(risks),
            "critical_count": sum(1 for r in risks if r.risk_level == "CRITICAL"),
            "high_count": sum(1 for r in risks if r.risk_level == "HIGH"),
            "medium_count": sum(1 for r in risks if r.risk_level == "MEDIUM"),
            "low_count": sum(1 for r in risks if r.risk_level == "LOW"),
        }
        
        return {
            "matrix": matrix,
            "summary": summary,
        }
    
    def get_risk_summary(self, project_id: int) -> Dict[str, Any]:
        """
        获取风险汇总统计
        
        Args:
            project_id: 项目ID
            
        Returns:
            包含各维度统计的字典
        """
        # 检查项目是否存在
        get_or_404(self.db, Project, project_id, detail="项目不存在")
        
        # 获取所有风险
        risks = self.db.query(ProjectRisk).filter(
            ProjectRisk.project_id == project_id
        ).all()
        
        # 按类型统计
        by_type = {}
        for risk_type in RiskTypeEnum:
            count = sum(1 for r in risks if r.risk_type == risk_type)
            by_type[risk_type.value] = count
        
        # 按等级统计
        by_level = {
            "CRITICAL": sum(1 for r in risks if r.risk_level == "CRITICAL"),
            "HIGH": sum(1 for r in risks if r.risk_level == "HIGH"),
            "MEDIUM": sum(1 for r in risks if r.risk_level == "MEDIUM"),
            "LOW": sum(1 for r in risks if r.risk_level == "LOW"),
        }
        
        # 按状态统计
        by_status = {}
        for status in RiskStatusEnum:
            count = sum(1 for r in risks if r.status == status)
            by_status[status.value] = count
        
        # 计算平均风险评分
        avg_score = sum(r.risk_score for r in risks) / len(risks) if risks else 0
        
        # 高优先级风险数量（HIGH + CRITICAL）
        high_priority_count = by_level["HIGH"] + by_level["CRITICAL"]
        
        return {
            "total_risks": len(risks),
            "by_type": by_type,
            "by_level": by_level,
            "by_status": by_status,
            "occurred_count": sum(1 for r in risks if r.is_occurred),
            "closed_count": sum(1 for r in risks if r.status == RiskStatusEnum.CLOSED),
            "high_priority_count": high_priority_count,
            "avg_risk_score": round(avg_score, 2),
        }
