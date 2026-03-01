# -*- coding: utf-8 -*-
"""
项目需求 AI 抽取与工程师推荐服务

功能：
1. 从项目文档抽取生产能力需求
2. 从项目文档抽取售后服务需求
3. 匹配工程师能力
4. 智能推荐工程师
"""

from typing import Any, Dict, List, Optional
from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.project_requirements import ProjectRequirement, EngineerRecommendation
from app.models.user import User
from app.models.project import Project
from app.models.engineer_capacity import EngineerCapacity


class RequirementExtractionService:
    """需求抽取与推荐服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== AI 需求抽取 ====================
    
    def extract_requirements_from_project(self, project_id: int) -> Dict[str, Any]:
        """
        从项目信息中 AI 抽取工程师需求
        
        分析维度：
        1. 项目类型（ICT/FCT/EOL/老化/视觉）
        2. 技术复杂度
        3. 客户行业（锂电/光伏/3C/汽车/医疗）
        4. 交付周期
        5. 售后服务要求
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}
        
        requirements = {
            'production': [],      # 生产需求
            'service': [],         # 售后需求
            'design': [],          # 设计需求
            'debug': [],           # 调试需求
        }
        
        # 1. 根据项目类型抽取
        product_category = project.product_category or ''
        industry = project.industry or ''
        contract_amount = project.contract_amount or 0
        
        # 2. 分析生产能力需求
        production_req = self._extract_production_requirements(project)
        requirements['production'].append(production_req)
        
        # 3. 分析售后服务需求
        service_req = self._extract_service_requirements(project)
        requirements['service'].append(service_req)
        
        # 4. 分析设计需求
        design_req = self._extract_design_requirements(project)
        requirements['design'].append(design_req)
        
        # 5. 分析调试需求
        debug_req = self._extract_debug_requirements(project)
        requirements['debug'].append(debug_req)
        
        return {
            'project_id': project_id,
            'project_name': project.project_name,
            'requirements': requirements,
            'total_requirements': sum(len(reqs) for reqs in requirements.values()),
        }
    
    def _extract_production_requirements(self, project: Project) -> Dict[str, Any]:
        """抽取生产能力需求"""
        product_category = project.product_category or ''
        contract_amount = project.contract_amount or 0
        
        # 根据产品类型确定技能需求
        skill_mapping = {
            'ICT': ['电气装配', 'PCB 测试', '探针调试'],
            'FCT': ['电气装配', '功能测试', 'PLC 调试'],
            'EOL': ['电气装配', '终检测试', '数据追溯'],
            'aging': ['电气装配', '老化测试', '温控系统'],
            'vision': ['机械装配', '光学调试', '视觉算法'],
        }
        
        # 根据合同金额确定复杂度
        if contract_amount > 5000000:
            complexity = 'EXPERT'
            required_experience = 5
        elif contract_amount > 3000000:
            complexity = 'HIGH'
            required_experience = 3
        elif contract_amount > 1000000:
            complexity = 'MEDIUM'
            required_experience = 2
        else:
            complexity = 'LOW'
            required_experience = 1
        
        # 估算工时
        estimated_hours = self._estimate_production_hours(project)
        
        return {
            'requirement_type': 'PRODUCTION',
            'product_category': product_category,
            'required_skills': skill_mapping.get(product_category, ['机械装配', '电气装配']),
            'production_complexity': complexity,
            'required_experience_years': required_experience,
            'estimated_hours': estimated_hours,
            'required_certifications': ['电工证'] if '电气' in str(skill_mapping.get(product_category, [])) else [],
        }
    
    def _extract_service_requirements(self, project: Project) -> Dict[str, Any]:
        """抽取售后服务需求"""
        customer_name = project.customer_name or ''
        industry = project.industry or ''
        
        # 根据行业确定服务要求
        service_requirements = {
            '锂电': {
                'response_time': 4,  # 4 小时响应
                'required_skills': ['锂电池安全', '高压系统'],
                'customer_facing': True,
                'language': ['中文'],
            },
            '光伏': {
                'response_time': 8,
                'required_skills': ['光伏系统', '逆变器'],
                'customer_facing': True,
                'language': ['中文'],
            },
            '3C 电子': {
                'response_time': 2,
                'required_skills': ['快速诊断', '客户沟通'],
                'customer_facing': True,
                'language': ['中文', '英文'],
            },
            '汽车': {
                'response_time': 4,
                'required_skills': ['汽车行业规范', 'IATF16949'],
                'customer_facing': True,
                'language': ['中文'],
            },
            '医疗': {
                'response_time': 2,
                'required_skills': ['医疗规范', '洁净室'],
                'customer_facing': True,
                'language': ['中文', '英文'],
            },
        }
        
        service_req = service_requirements.get(industry, {
            'response_time': 8,
            'required_skills': ['设备维护'],
            'customer_facing': True,
            'language': ['中文'],
        })
        
        return {
            'requirement_type': 'SERVICE',
            'service_type': 'INSTALLATION',  # 安装
            'service_location': customer_name,
            'service_duration': 5,  # 预计 5 天
            'required_experience_years': 3,
            'customer_facing': service_req['customer_facing'],
            'language_requirements': service_req['language'],
            'required_skills': service_req['required_skills'],
            'response_time_hours': service_req['response_time'],
        }
    
    def _extract_design_requirements(self, project: Project) -> Dict[str, Any]:
        """抽取设计需求"""
        product_category = project.product_category or ''
        
        design_skills = {
            'ICT': ['PCB 设计', '测试夹具设计'],
            'FCT': ['电气设计', '测试程序设计'],
            'EOL': ['系统设计', '数据追溯设计'],
            'aging': ['温控系统设计', '老化程序设计'],
            'vision': ['光学设计', '视觉算法'],
        }
        
        return {
            'requirement_type': 'DESIGN',
            'required_skills': design_skills.get(product_category, ['机械设计', '电气设计']),
            'design_complexity': 'MEDIUM',
            'required_software': ['AutoCAD', 'EPLAN'],
        }
    
    def _extract_debug_requirements(self, project: Project) -> Dict[str, Any]:
        """抽取调试需求"""
        product_category = project.product_category or ''
        
        debug_skills = {
            'ICT': ['探针调试', '测试覆盖率分析'],
            'FCT': ['PLC 调试', '功能测试'],
            'EOL': ['系统联调', '数据验证'],
            'aging': ['温控调试', '老化程序调试'],
            'vision': ['视觉调试', '算法优化'],
        }
        
        return {
            'requirement_type': 'DEBUG',
            'required_skills': debug_skills.get(product_category, ['电气调试', '机械调试']),
            'debug_complexity': 'MEDIUM',
            'required_tools': ['万用表', '示波器'],
        }
    
    def _estimate_production_hours(self, project: Project) -> float:
        """估算生产工时"""
        contract_amount = project.contract_amount or 0
        
        # 简化估算：合同金额越大，工时越多
        base_hours = contract_amount / 10000  # 每万元 1 小时
        
        # 根据行业调整
        industry_factor = {
            '锂电': 1.2,
            '光伏': 1.1,
            '3C 电子': 1.0,
            '汽车': 1.3,
            '医疗': 1.4,
        }
        
        factor = industry_factor.get(project.industry, 1.0)
        
        return base_hours * factor
    
    # ==================== 工程师推荐 ====================
    
    def recommend_engineers(
        self,
        requirement: Dict[str, Any],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        推荐合适的工程师
        
        Args:
            requirement: 需求信息
            limit: 推荐人数
        
        Returns:
            推荐的工程师列表（按匹配度排序）
        """
        # 1. 获取所有工程师及其能力
        engineers = self.db.query(User, EngineerCapacity)\
            .outerjoin(EngineerCapacity, User.id == EngineerCapacity.engineer_id)\
            .filter(User.is_active == True)\
            .all()
        
        recommendations = []
        
        for user, capacity in engineers:
            if not capacity:
                continue
            
            # 2. 计算匹配度
            match_result = self._calculate_match_score(requirement, user, capacity)
            
            # 3. 只推荐匹配度>60 的
            if match_result['overall_score'] >= 60:
                recommendations.append({
                    'engineer_id': user.id,
                    'engineer_name': user.real_name or user.username,
                    'department': user.department,
                    'overall_match_score': round(match_result['overall_score'], 1),
                    'skill_match_score': round(match_result['skill_score'], 1),
                    'capacity_match_score': round(match_result['capacity_score'], 1),
                    'availability_score': round(match_result['availability_score'], 1),
                    'matched_skills': match_result['matched_skills'],
                    'missing_skills': match_result['missing_skills'],
                    'advantages': match_result['advantages'],
                    'risks': match_result['risks'],
                    'recommendation_reason': match_result['reason'],
                })
        
        # 4. 按匹配度排序
        recommendations.sort(key=lambda x: x['overall_match_score'], reverse=True)
        
        return recommendations[:limit]
    
    def _calculate_match_score(
        self,
        requirement: Dict[str, Any],
        engineer: User,
        capacity: EngineerCapacity,
    ) -> Dict[str, Any]:
        """计算工程师与需求的匹配度"""
        
        required_skills = requirement.get('required_skills', [])
        
        # 1. 技能匹配度（40% 权重）
        engineer_skills = []
        if capacity.skill_tags:
            import json
            try:
                engineer_skills = json.loads(capacity.skill_tags)
            except:
                engineer_skills = []
        
        matched_skills = [s for s in required_skills if any(s in e or e in s for e in engineer_skills)]
        missing_skills = [s for s in required_skills if not any(s in e or e in s for e in engineer_skills)]
        
        skill_score = (len(matched_skills) / len(required_skills) * 100) if required_skills else 100
        
        # 2. 能力匹配度（30% 权重）
        capacity_score = 100
        
        # 多项目能力
        if requirement.get('min_multi_project_capacity', 0) > 0:
            if capacity.multi_project_capacity >= requirement['min_multi_project_capacity']:
                capacity_score += 10
            else:
                capacity_score -= 20
        
        # 标准化能力
        if requirement.get('min_standardization_score', 0) > 0:
            if capacity.standardization_score >= requirement['min_standardization_score']:
                capacity_score += 10
            else:
                capacity_score -= 10
        
        # AI 能力
        ai_level_req = requirement.get('min_ai_skill_level', 'NONE')
        ai_levels = {'NONE': 0, 'BASIC': 1, 'INTERMEDIATE': 2, 'ADVANCED': 3, 'EXPERT': 4}
        if ai_levels.get(capacity.ai_skill_level, 0) >= ai_levels.get(ai_level_req, 0):
            capacity_score += 10
        
        capacity_score = max(0, min(100, capacity_score))
        
        # 3. 可用性评分（30% 权重）
        availability_score = 100
        
        # 当前负载
        if hasattr(capacity, 'workload_status'):
            if capacity.workload_status == 'OVERLOAD':
                availability_score -= 40
            elif capacity.workload_status == 'BUSY':
                availability_score -= 20
        
        # 多项目效率
        if capacity.multi_project_efficiency and capacity.multi_project_efficiency < 0.8:
            availability_score -= 15
        
        # 上下文切换成本
        if capacity.context_switch_cost and capacity.context_switch_cost > 0.3:
            availability_score -= 15
        
        availability_score = max(0, min(100, availability_score))
        
        # 4. 综合匹配度
        overall_score = (
            skill_score * 0.4 +
            capacity_score * 0.3 +
            availability_score * 0.3
        )
        
        # 5. 生成推荐理由
        advantages = []
        risks = []
        
        if skill_score >= 80:
            advantages.append(f"技能匹配度高 ({skill_score:.0f}%)")
        if capacity.multi_project_capacity >= 5:
            advantages.append(f"多项目专家 (可同时负责{capacity.multi_project_capacity}个项目)")
        if capacity.ai_skill_level in ['ADVANCED', 'EXPERT']:
            advantages.append(f"AI 高级用户 (效率提升{capacity.ai_efficiency_boost*100-100:.0f}%)")
        if capacity.standardization_score >= 7:
            advantages.append(f"标准化能力强 ({capacity.standardization_score:.1f}/10)")
        
        if len(missing_skills) > 0:
            risks.append(f"缺少技能：{', '.join(missing_skills[:3])}")
        if capacity.workload_status == 'OVERLOAD':
            risks.append("当前工作过载")
        if capacity.context_switch_cost > 0.3:
            risks.append("上下文切换成本高")
        
        reason = f"匹配度{overall_score:.0f}%。"
        if advantages:
            reason += f"优势：{', '.join(advantages[:3])}。"
        if risks:
            reason += f"注意：{', '.join(risks[:2])}。"
        
        return {
            'overall_score': overall_score,
            'skill_score': skill_score,
            'capacity_score': capacity_score,
            'availability_score': availability_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'advantages': advantages,
            'risks': risks,
            'reason': reason,
        }
    
    def save_recommendations(
        self,
        requirement_id: int,
        recommendations: List[Dict[str, Any]],
    ) -> List[EngineerRecommendation]:
        """保存推荐结果"""
        saved = []
        
        for rank, rec in enumerate(recommendations, 1):
            recommendation = EngineerRecommendation(
                recommendation_no=f"REC{date.today().strftime('%Y%m%d%H%M%S')}{rank:03d}",
                requirement_id=requirement_id,
                engineer_id=rec['engineer_id'],
                engineer_name=rec['engineer_name'],
                overall_match_score=rec['overall_match_score'],
                skill_match_score=rec['skill_match_score'],
                capacity_match_score=rec['capacity_match_score'],
                availability_score=rec['availability_score'],
                matched_skills=str(rec['matched_skills']),
                missing_skills=str(rec['missing_skills']),
                advantages=str(rec['advantages']),
                risks=str(rec['risks']),
                recommendation_reason=rec['recommendation_reason'],
                rank=rank,
            )
            self.db.add(recommendation)
            saved.append(recommendation)
        
        self.db.commit()
        
        return saved
