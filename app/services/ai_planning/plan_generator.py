# -*- coding: utf-8 -*-
"""
AI项目计划生成器
基于历史项目数据和AI模型生成项目计划
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Project
from app.models.ai_planning import AIProjectPlanTemplate
from .glm_service import GLMService

logger = logging.getLogger(__name__)


class AIProjectPlanGenerator:
    """AI项目计划生成器"""
    
    def __init__(self, db: Session, glm_service: Optional[GLMService] = None):
        """
        初始化计划生成器
        
        Args:
            db: 数据库会话
            glm_service: GLM AI服务实例
        """
        self.db = db
        self.glm_service = glm_service or GLMService()
    
    async def generate_plan(
        self,
        project_name: str,
        project_type: str,
        requirements: str,
        industry: Optional[str] = None,
        complexity: Optional[str] = "MEDIUM",
        use_template: bool = True
    ) -> Optional[AIProjectPlanTemplate]:
        """
        生成项目计划
        
        Args:
            project_name: 项目名称
            project_type: 项目类型
            requirements: 项目需求
            industry: 行业
            complexity: 复杂度等级
            use_template: 是否使用已有模板
            
        Returns:
            生成的计划模板对象
        """
        start_time = datetime.now()
        
        try:
            # 1. 查找参考项目
            reference_projects = self._find_reference_projects(
                project_type, industry, complexity
            )
            
            # 2. 检查是否有现成的模板
            if use_template:
                existing_template = self._find_existing_template(
                    project_type, industry, complexity
                )
                if existing_template:
                    logger.info(f"找到现有模板: {existing_template.template_name}")
                    return existing_template
            
            # 3. 使用AI生成计划
            plan_data = self.glm_service.generate_project_plan(
                project_name=project_name,
                project_type=project_type,
                requirements=requirements,
                industry=industry,
                complexity=complexity,
                reference_projects=[self._project_to_dict(p) for p in reference_projects]
            )
            
            if not plan_data:
                logger.error("AI生成计划失败")
                # 使用规则引擎生成备用计划
                plan_data = self._generate_fallback_plan(
                    project_name, project_type, requirements,
                    reference_projects
                )
            
            # 4. 创建模板对象
            template = self._create_template_from_data(
                plan_data, project_type, industry, complexity,
                reference_projects
            )
            
            # 5. 计算生成时间
            generation_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"计划生成完成，耗时: {generation_time:.2f}秒")
            
            if generation_time > 30:
                logger.warning(f"生成时间超过30秒: {generation_time:.2f}秒")
            
            return template
            
        except Exception as e:
            logger.error(f"生成计划时出错: {e}", exc_info=True)
            return None
    
    def _find_reference_projects(
        self,
        project_type: str,
        industry: Optional[str],
        complexity: Optional[str],
        limit: int = 5
    ) -> List[Project]:
        """查找参考项目"""
        
        query = self.db.query(Project).filter(
            Project.project_type == project_type,
            Project.status.in_(['ST06', 'ST07'])  # 已完成或已验收的项目
        )
        
        if industry:
            query = query.filter(Project.industry == industry)
        
        # 优先选择最近完成的项目
        query = query.order_by(Project.actual_end_date.desc())
        
        return query.limit(limit).all()
    
    def _find_existing_template(
        self,
        project_type: str,
        industry: Optional[str],
        complexity: Optional[str]
    ) -> Optional[AIProjectPlanTemplate]:
        """查找现有模板"""
        
        query = self.db.query(AIProjectPlanTemplate).filter(
            AIProjectPlanTemplate.project_type == project_type,
            AIProjectPlanTemplate.is_active == True,
            AIProjectPlanTemplate.is_verified == True
        )
        
        if industry:
            query = query.filter(AIProjectPlanTemplate.industry == industry)
        
        if complexity:
            query = query.filter(AIProjectPlanTemplate.complexity_level == complexity)
        
        # 优先选择推荐的、使用次数多的模板
        query = query.order_by(
            AIProjectPlanTemplate.is_recommended.desc(),
            AIProjectPlanTemplate.success_rate.desc(),
            AIProjectPlanTemplate.usage_count.desc()
        )
        
        return query.first()
    
    def _project_to_dict(self, project: Project) -> Dict:
        """将项目对象转换为字典"""
        return {
            'id': project.id,
            'name': project.project_name,
            'type': project.project_type,
            'industry': project.industry,
            'duration_days': (
                (project.actual_end_date - project.actual_start_date).days
                if project.actual_end_date and project.actual_start_date
                else None
            ),
            'contract_amount': float(project.contract_amount) if project.contract_amount else None,
            'actual_cost': float(project.actual_cost) if project.actual_cost else None,
        }
    
    def _generate_fallback_plan(
        self,
        project_name: str,
        project_type: str,
        requirements: str,
        reference_projects: List[Project]
    ) -> Dict:
        """生成备用计划（基于规则引擎）"""
        
        logger.info("使用规则引擎生成备用计划")
        
        # 基于参考项目计算平均值
        if reference_projects:
            avg_duration = sum(
                (p.actual_end_date - p.actual_start_date).days
                for p in reference_projects
                if p.actual_end_date and p.actual_start_date
            ) / len(reference_projects) if reference_projects else 90
            
            avg_cost = sum(
                float(p.actual_cost) for p in reference_projects if p.actual_cost
            ) / len(reference_projects) if reference_projects else 100000
        else:
            avg_duration = 90
            avg_cost = 100000
        
        # 生成标准阶段
        phases = [
            {"name": "需求分析", "duration_days": int(avg_duration * 0.15), "deliverables": ["需求规格说明书"]},
            {"name": "设计阶段", "duration_days": int(avg_duration * 0.20), "deliverables": ["设计方案", "技术架构"]},
            {"name": "开发阶段", "duration_days": int(avg_duration * 0.40), "deliverables": ["代码", "单元测试"]},
            {"name": "测试阶段", "duration_days": int(avg_duration * 0.15), "deliverables": ["测试报告"]},
            {"name": "部署上线", "duration_days": int(avg_duration * 0.10), "deliverables": ["部署文档", "培训材料"]},
        ]
        
        # 生成里程碑
        milestones = [
            {"name": "需求评审", "phase": "需求分析", "estimated_day": phases[0]["duration_days"]},
            {"name": "设计评审", "phase": "设计阶段", "estimated_day": sum(p["duration_days"] for p in phases[:2])},
            {"name": "开发完成", "phase": "开发阶段", "estimated_day": sum(p["duration_days"] for p in phases[:3])},
            {"name": "测试通过", "phase": "测试阶段", "estimated_day": sum(p["duration_days"] for p in phases[:4])},
            {"name": "正式上线", "phase": "部署上线", "estimated_day": int(avg_duration)},
        ]
        
        return {
            "project_name": project_name,
            "estimated_duration_days": int(avg_duration),
            "estimated_effort_hours": int(avg_duration * 8 * 3),  # 假设3人团队
            "estimated_cost": avg_cost,
            "phases": phases,
            "milestones": milestones,
            "required_roles": [
                {"role": "项目经理", "skill_level": "Senior", "count": 1},
                {"role": "架构师", "skill_level": "Senior", "count": 1},
                {"role": "开发工程师", "skill_level": "Middle", "count": 3},
                {"role": "测试工程师", "skill_level": "Middle", "count": 2},
            ],
            "recommended_team_size": 7,
            "risk_factors": [
                {"category": "技术风险", "description": "技术难度较高", "mitigation": "提前技术验证"},
                {"category": "进度风险", "description": "工期紧张", "mitigation": "合理资源分配"},
            ]
        }
    
    def _create_template_from_data(
        self,
        plan_data: Dict,
        project_type: str,
        industry: Optional[str],
        complexity: Optional[str],
        reference_projects: List[Project]
    ) -> AIProjectPlanTemplate:
        """从计划数据创建模板对象"""
        
        import json
        from datetime import datetime
        
        template_code = f"TPL_{project_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        template = AIProjectPlanTemplate(
            template_code=template_code,
            template_name=plan_data.get('project_name', f"{project_type}标准模板"),
            project_type=project_type,
            industry=industry,
            complexity_level=complexity,
            
            # AI生成信息
            ai_model_version=self.glm_service.model if self.glm_service.is_available() else "RULE_ENGINE",
            generation_time=datetime.now(),
            confidence_score=85.0 if self.glm_service.is_available() else 70.0,
            
            # 模板内容
            description=f"基于{len(reference_projects)}个参考项目生成",
            phases=json.dumps(plan_data.get('phases', []), ensure_ascii=False),
            milestones=json.dumps(plan_data.get('milestones', []), ensure_ascii=False),
            risk_factors=json.dumps(plan_data.get('risk_factors', []), ensure_ascii=False),
            
            # 估算信息
            estimated_duration_days=plan_data.get('estimated_duration_days'),
            estimated_effort_hours=plan_data.get('estimated_effort_hours'),
            estimated_cost=plan_data.get('estimated_cost'),
            
            # 资源需求
            required_roles=json.dumps(plan_data.get('required_roles', []), ensure_ascii=False),
            recommended_team_size=plan_data.get('recommended_team_size'),
            
            # 参考数据
            reference_project_ids=json.dumps([p.id for p in reference_projects]),
            reference_count=len(reference_projects),
            
            # 初始统计
            usage_count=0,
            is_active=True,
            is_recommended=False,
        )
        
        self.db.add(template)
        self.db.flush()
        
        return template
