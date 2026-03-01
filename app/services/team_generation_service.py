# -*- coding: utf-8 -*-
"""
AI 自动组队服务

根据项目需求自动生成项目组成员方案
"""

from typing import Any, Dict, List, Optional
from datetime import date, timedelta
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.project_team import ProjectTeamPlan, ProjectTeamMember
from app.models.user import User
from app.models.project import Project
from app.models.engineer_capacity import EngineerCapacity


class TeamGenerationService:
    """AI 自动组队服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_team_plan(self, project_id: int) -> Dict[str, Any]:
        """
        为项目自动生成团队方案
        
        流程：
        1. 分析项目需求
        2. 确定所需角色
        3. 匹配工程师
        4. 优化组合
        5. 生成方案
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}
        
        # 1. 分析项目需求
        requirements = self._analyze_project_requirements(project)
        
        # 2. 确定所需角色和人数
        roles_needed = self._determine_roles(requirements, project)
        
        # 3. 为每个角色匹配工程师
        role_assignments = {}
        for role, role_info in roles_needed.items():
            candidates = self._match_engineers_for_role(role, role_info, project)
            if candidates:
                role_assignments[role] = candidates[0]  # 选择最佳匹配
        
        # 4. 检查负载均衡
        workload_balance = self._check_workload_balance(role_assignments)
        
        # 5. 生成团队方案
        team_plan = self._create_team_plan(project, role_assignments, requirements)
        
        return team_plan
    
    def _analyze_project_requirements(self, project: Project) -> Dict[str, Any]:
        """分析项目需求"""
        product_category = project.product_category or ''
        industry = project.industry or ''
        contract_amount = project.contract_amount or 0
        
        # 确定项目规模
        if contract_amount > 5000000:
            scale = 'LARGE'
        elif contract_amount > 3000000:
            scale = 'MEDIUM'
        else:
            scale = 'SMALL'
        
        # 确定技术复杂度
        complexity_map = {
            'ICT': 'MEDIUM',
            'FCT': 'HIGH',
            'EOL': 'HIGH',
            'aging': 'MEDIUM',
            'vision': 'EXPERT',
        }
        tech_complexity = complexity_map.get(product_category, 'MEDIUM')
        
        # 确定行业特殊要求
        industry_requirements = {
            '锂电': ['安全规范', '高压系统'],
            '光伏': ['并网标准', '户外环境'],
            '3C 电子': ['快速交付', '高精度'],
            '汽车': ['IATF16949', '追溯系统'],
            '医疗': ['洁净规范', '验证文档'],
        }
        
        return {
            'scale': scale,
            'tech_complexity': tech_complexity,
            'industry_requirements': industry_requirements.get(industry, []),
            'product_category': product_category,
            'contract_amount': contract_amount,
        }
    
    def _determine_roles(self, requirements: Dict, project: Project) -> Dict[str, Any]:
        """确定所需角色和人数"""
        scale = requirements['scale']
        product_category = requirements['product_category']
        
        # 基础角色配置
        base_roles = {
            'PM': {  # 项目经理
                'count': 1,
                'required_skills': ['项目管理', '客户沟通'],
                'min_experience': 5,
                'ai_level': 'INTERMEDIATE',
                'multi_project_min': 3,
            },
            'TECH_LEAD': {  # 技术负责人
                'count': 1,
                'required_skills': ['系统设计', '技术评审'],
                'min_experience': 5,
                'ai_level': 'ADVANCED',
                'standardization_min': 7.0,
            },
        }
        
        # 根据产品类型添加专业角色
        if product_category in ['ICT', 'FCT', 'EOL']:
            base_roles['ELEC_ENG'] = {  # 电气工程师
                'count': 2 if scale == 'LARGE' else 1,
                'required_skills': ['电气设计', 'PLC 调试'],
                'min_experience': 3,
            }
            base_roles['MECH_ENG'] = {  # 机械工程师
                'count': 1,
                'required_skills': ['机械设计', 'CAD'],
                'min_experience': 3,
            }
        
        if product_category == 'vision':
            base_roles['VISION_ENG'] = {  # 视觉工程师
                'count': 1,
                'required_skills': ['视觉算法', '光学调试'],
                'min_experience': 4,
                'ai_level': 'ADVANCED',
            }
        
        # 售后服务工程师
        base_roles['SERVICE_ENG'] = {  # 售后工程师
            'count': 1,
            'required_skills': ['客户沟通', '快速诊断'],
            'min_experience': 2,
            'customer_facing': True,
        }
        
        return base_roles
    
    def _match_engineers_for_role(
        self,
        role: str,
        role_info: Dict,
        project: Project,
    ) -> List[Dict[str, Any]]:
        """为角色匹配工程师"""
        required_skills = role_info.get('required_skills', [])
        min_experience = role_info.get('min_experience', 0)
        min_ai_level = role_info.get('ai_level', 'NONE')
        
        # 查询工程师
        engineers = self.db.query(User, EngineerCapacity)\
            .outerjoin(EngineerCapacity, User.id == EngineerCapacity.engineer_id)\
            .filter(User.is_active == True)\
            .all()
        
        candidates = []
        
        for user, capacity in engineers:
            if not capacity:
                continue
            
            # 计算匹配度
            match_result = self._calculate_role_match(
                user, capacity, role, role_info, project
            )
            
            if match_result['score'] >= 60:
                candidates.append({
                    'engineer_id': user.id,
                    'engineer_name': user.real_name or user.username,
                    'department': user.department,
                    'role': role,
                    'role_name': self._get_role_name(role),
                    'match_score': match_result['score'],
                    'match_reason': match_result['reason'],
                    'estimated_hours': self._estimate_hours(role, project),
                    'capacity': capacity,
                })
        
        # 按匹配度排序
        candidates.sort(key=lambda x: x['match_score'], reverse=True)
        
        return candidates
    
    def _calculate_role_match(
        self,
        engineer: User,
        capacity: EngineerCapacity,
        role: str,
        role_info: Dict,
        project: Project,
    ) -> Dict[str, Any]:
        """计算工程师与角色的匹配度"""
        score = 100
        reasons = []
        
        # 1. 技能匹配（40 分）
        engineer_skills = []
        if capacity.skill_tags:
            try:
                engineer_skills = json.loads(capacity.skill_tags)
            except:
                pass
        
        required_skills = role_info.get('required_skills', [])
        matched = [s for s in required_skills if any(s in e or e in s for e in engineer_skills)]
        skill_score = len(matched) / len(required_skills) * 40 if required_skills else 40
        score = score - 40 + skill_score
        
        if skill_score >= 35:
            reasons.append(f"技能匹配 ({len(matched)}/{len(required_skills)})")
        
        # 2. 经验匹配（20 分）
        # 简化：假设有经验数据
        experience_score = 20
        score = score - 20 + experience_score
        
        # 3. AI 能力（15 分）
        ai_levels = {'NONE': 0, 'BASIC': 1, 'INTERMEDIATE': 2, 'ADVANCED': 3, 'EXPERT': 4}
        required_ai = role_info.get('ai_level', 'NONE')
        if ai_levels.get(capacity.ai_skill_level, 0) >= ai_levels.get(required_ai, 0):
            ai_score = 15
            reasons.append(f"AI 能力达标 ({capacity.ai_skill_level})")
        else:
            ai_score = 5
        score = score - 15 + ai_score
        
        # 4. 多项目能力（15 分）
        multi_project_min = role_info.get('multi_project_min', 0)
        if multi_project_min > 0:
            if capacity.multi_project_capacity >= multi_project_min:
                mp_score = 15
                reasons.append(f"多项目能力 ({capacity.multi_project_capacity})")
            else:
                mp_score = 5
        else:
            mp_score = 15
        score = score - 15 + mp_score
        
        # 5. 标准化能力（10 分）
        std_min = role_info.get('standardization_min', 0)
        if std_min > 0:
            if capacity.standardization_score >= std_min:
                std_score = 10
                reasons.append(f"标准化能力 ({capacity.standardization_score:.1f})")
            else:
                std_score = 3
        else:
            std_score = 10
        score = score - 10 + std_score
        
        # 6. 当前负载（额外扣分）
        if hasattr(capacity, 'workload_status'):
            if capacity.workload_status == 'OVERLOAD':
                score -= 20
            elif capacity.workload_status == 'BUSY':
                score -= 10
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 1),
            'reason': '。'.join(reasons[:3]),
        }
    
    def _get_role_name(self, role: str) -> str:
        """获取角色中文名称"""
        role_names = {
            'PM': '项目经理',
            'TECH_LEAD': '技术负责人',
            'MECH_ENG': '机械工程师',
            'ELEC_ENG': '电气工程师',
            'VISION_ENG': '视觉工程师',
            'SERVICE_ENG': '售后工程师',
        }
        return role_names.get(role, role)
    
    def _estimate_hours(self, role: str, project: Project) -> float:
        """估算工时"""
        contract_amount = project.contract_amount or 0
        
        # 简化估算
        base_hours = {
            'PM': 0.15,      # 15% 总工时
            'TECH_LEAD': 0.20,
            'MECH_ENG': 0.20,
            'ELEC_ENG': 0.25,
            'VISION_ENG': 0.15,
            'SERVICE_ENG': 0.05,
        }
        
        total_hours = contract_amount / 10000  # 每万元 1 小时
        return total_hours * base_hours.get(role, 0.1)
    
    def _check_workload_balance(self, role_assignments: Dict) -> Dict[str, Any]:
        """检查负载均衡"""
        overloaded = []
        balanced = []
        
        for role, assignment in role_assignments.items():
            capacity = assignment.get('capacity')
            if capacity and hasattr(capacity, 'workload_status'):
                if capacity.workload_status == 'OVERLOAD':
                    overloaded.append(assignment['engineer_name'])
                else:
                    balanced.append(assignment['engineer_name'])
        
        return {
            'overloaded_count': len(overloaded),
            'balanced_count': len(balanced),
            'overloaded_engineers': overloaded,
            'balance_score': 100 - (len(overloaded) * 20),
        }
    
    def _create_team_plan(
        self,
        project: Project,
        role_assignments: Dict,
        requirements: Dict,
    ) -> Dict[str, Any]:
        """创建团队方案"""
        total_hours = sum(a.get('estimated_hours', 0) for a in role_assignments.values())
        
        # 计算方案评分
        skill_coverage = 85  # 简化
        capacity_balance = 100 - len([a for a in role_assignments.values() 
                                      if a.get('capacity') and 
                                      getattr(a['capacity'], 'workload_status', '') == 'OVERLOAD']) * 20
        cost_efficiency = 80
        
        overall_score = (skill_coverage * 0.4 + capacity_balance * 0.3 + cost_efficiency * 0.3)
        
        # 生成优势
        advantages = []
        if overall_score >= 85:
            advantages.append("团队整体匹配度高")
        if any(a.get('capacity') and getattr(a['capacity'], 'ai_skill_level', '') in ['ADVANCED', 'EXPERT'] 
               for a in role_assignments.values()):
            advantages.append("包含 AI 高级用户，效率有保障")
        if any(a.get('capacity') and getattr(a['capacity'], 'multi_project_capacity', 0) >= 5 
               for a in role_assignments.values()):
            advantages.append("有多项目专家，可并行推进")
        
        # 生成风险
        risks = []
        overloaded = [a['engineer_name'] for a in role_assignments.values() 
                     if a.get('capacity') and getattr(a['capacity'], 'workload_status', '') == 'OVERLOAD']
        if overloaded:
            risks.append(f"{len(overloaded)}名工程师过载：{', '.join(overloaded[:3])}")
        
        return {
            'project_id': project.id,
            'project_name': project.project_name,
            'total_members': len(role_assignments),
            'total_estimated_hours': total_hours,
            'estimated_duration_days': int(total_hours / 8 / len(role_assignments)),
            'overall_score': round(overall_score, 1),
            'skill_coverage': skill_coverage,
            'capacity_balance': capacity_balance,
            'cost_efficiency': cost_efficiency,
            'role_assignments': role_assignments,
            'advantages': advantages,
            'risks': risks,
            'recommendations': ['建议确认过载工程师的时间安排'] if overloaded else [],
        }
    
    def save_team_plan(self, team_data: Dict[str, Any], submitted_by: int) -> ProjectTeamPlan:
        """保存团队方案"""
        from datetime import datetime
        
        plan = ProjectTeamPlan(
            plan_no=f"PTP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_id=team_data['project_id'],
            project_name=team_data['project_name'],
            total_members=team_data['total_members'],
            total_estimated_hours=team_data['total_estimated_hours'],
            estimated_duration_days=team_data['estimated_duration_days'],
            overall_score=team_data['overall_score'],
            skill_coverage=team_data['skill_coverage'],
            capacity_balance=team_data['capacity_balance'],
            cost_efficiency=team_data['cost_efficiency'],
            team_structure=json.dumps({'roles': list(team_data['role_assignments'].keys())}),
            role_assignments=json.dumps(team_data['role_assignments']),
            advantages=json.dumps(team_data['advantages']),
            risks=json.dumps(team_data['risks']),
            recommendations=json.dumps(team_data['recommendations']),
            status='DRAFT',
            submitted_by=submitted_by,
            submitted_at=datetime.now(),
        )
        
        self.db.add(plan)
        self.db.flush()
        
        # 添加成员
        for role, assignment in team_data['role_assignments'].items():
            member = ProjectTeamMember(
                team_plan_id=plan.id,
                engineer_id=assignment['engineer_id'],
                engineer_name=assignment['engineer_name'],
                role=role,
                role_name=assignment['role_name'],
                estimated_hours=assignment['estimated_hours'],
                match_score=assignment['match_score'],
                match_reason=assignment['match_reason'],
            )
            self.db.add(member)
        
        self.db.commit()
        self.db.refresh(plan)
        
        return plan
