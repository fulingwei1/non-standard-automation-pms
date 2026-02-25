# -*- coding: utf-8 -*-
"""
AI资源优化器
推荐最优资源分配方案，考虑技能匹配、可用性和成本
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, TaskUnified
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation
from .glm_service import GLMService

logger = logging.getLogger(__name__)


class AIResourceOptimizer:
    """AI资源优化器"""
    
    def __init__(self, db: Session, glm_service: Optional[GLMService] = None):
        """
        初始化资源优化器
        
        Args:
            db: 数据库会话
            glm_service: GLM AI服务实例
        """
        self.db = db
        self.glm_service = glm_service or GLMService()
    
    async def allocate_resources(
        self,
        wbs_suggestion_id: int,
        available_user_ids: Optional[List[int]] = None,
        constraints: Optional[Dict] = None
    ) -> List[AIResourceAllocation]:
        """
        为WBS任务分配资源
        
        Args:
            wbs_suggestion_id: WBS建议ID
            available_user_ids: 可用用户ID列表（None表示所有用户）
            constraints: 约束条件
            
        Returns:
            资源分配建议列表
        """
        # 获取WBS建议
        wbs = self.db.query(AIWbsSuggestion).get(wbs_suggestion_id)
        if not wbs:
            logger.error(f"WBS建议不存在: {wbs_suggestion_id}")
            return []
        
        # 获取可用用户
        users = self._get_available_users(available_user_ids, wbs)
        
        if not users:
            logger.warning("没有可用用户")
            return []
        
        # 分析每个用户的匹配度
        allocations = []
        for user in users:
            allocation = await self._analyze_user_match(
                user, wbs, constraints
            )
            if allocation:
                allocations.append(allocation)
        
        # 排序：按综合匹配度降序
        allocations.sort(key=lambda x: x.overall_match_score or 0, reverse=True)
        
        # 优化分配（考虑资源冲突）
        optimized = self._optimize_allocations(allocations, wbs)
        
        # 保存到数据库
        for alloc in optimized:
            self.db.add(alloc)
        
        self.db.flush()
        
        return optimized
    
    def _get_available_users(
        self,
        user_ids: Optional[List[int]],
        wbs: AIWbsSuggestion
    ) -> List[User]:
        """获取可用用户列表"""
        
        query = self.db.query(User).filter(User.is_active == True)
        
        if user_ids:
            query = query.filter(User.id.in_(user_ids))
        
        users = query.all()
        
        # TODO: 根据WBS要求的技能过滤用户
        
        return users
    
    async def _analyze_user_match(
        self,
        user: User,
        wbs: AIWbsSuggestion,
        constraints: Optional[Dict]
    ) -> Optional[AIResourceAllocation]:
        """
        分析用户匹配度
        
        Args:
            user: 用户对象
            wbs: WBS建议对象
            constraints: 约束条件
            
        Returns:
            资源分配建议对象
        """
        # 1. 技能匹配度
        skill_match = self._calculate_skill_match(user, wbs)
        
        # 2. 经验匹配度
        experience_match = self._calculate_experience_match(user, wbs)
        
        # 3. 可用性评分
        availability = self._calculate_availability(user, wbs)
        
        # 4. 历史绩效
        performance = self._calculate_performance_score(user, wbs)
        
        # 5. 综合匹配度（加权平均）
        overall_match = (
            skill_match * 0.4 +
            experience_match * 0.2 +
            availability * 0.2 +
            performance * 0.2
        )
        
        # 如果综合匹配度太低，不推荐
        if overall_match < 40:
            return None
        
        # 6. 成本分析
        hourly_rate = self._get_hourly_rate(user)
        estimated_cost = (wbs.estimated_effort_hours or 0) * hourly_rate
        
        # 7. 生成推荐理由
        recommendation_reason = self._generate_recommendation_reason(
            user, wbs, skill_match, experience_match, availability, performance
        )
        
        # 8. 确定分配类型
        allocation_type = "PRIMARY" if overall_match >= 80 else "SECONDARY"
        
        # 9. 创建分配对象
        allocation = AIResourceAllocation(
            allocation_code=f"RA_{wbs.id}_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_id=wbs.project_id,
            wbs_suggestion_id=wbs.id,
            user_id=user.id,
            role_name=user.role or "未指定",
            allocation_type=allocation_type,
            
            # AI生成信息
            ai_model_version=self.glm_service.model if self.glm_service.is_available() else "RULE_ENGINE",
            generation_time=datetime.now(),
            confidence_score=overall_match,
            optimization_method="GREEDY",  # 使用贪心算法
            
            # 时间分配
            allocated_hours=wbs.estimated_effort_hours,
            workload_percentage=None,  # 稍后计算
            
            # 匹配度分析
            skill_match_score=skill_match,
            experience_match_score=experience_match,
            availability_score=availability,
            performance_score=performance,
            overall_match_score=overall_match,
            
            # 成本信息
            hourly_rate=hourly_rate,
            estimated_cost=estimated_cost,
            cost_efficiency_score=self._calculate_cost_efficiency(overall_match, hourly_rate),
            
            # 推荐理由
            recommendation_reason=recommendation_reason,
            strengths=json.dumps(self._analyze_strengths(user, wbs, skill_match, performance), ensure_ascii=False),
            weaknesses=json.dumps(self._analyze_weaknesses(user, wbs, skill_match, availability), ensure_ascii=False),
            
            # 状态
            status='SUGGESTED',
            is_active=True,
        )
        
        return allocation
    
    def _calculate_skill_match(self, user: User, wbs: AIWbsSuggestion) -> float:
        """计算技能匹配度 (0-100)"""
        
        # TODO: 实现真实的技能匹配算法
        # 目前返回模拟值
        
        required_skills = json.loads(wbs.required_skills) if wbs.required_skills else []
        if not required_skills:
            return 70.0  # 无特定技能要求，默认70分
        
        # 简化版：根据用户角色匹配
        user_role = (user.role or "").lower()
        
        match_score = 50.0  # 基础分
        
        for skill in required_skills:
            skill_name = skill.get('skill', '').lower()
            if skill_name in user_role or user_role in skill_name:
                match_score += 15.0
        
        return min(match_score, 100.0)
    
    def _calculate_experience_match(self, user: User, wbs: AIWbsSuggestion) -> float:
        """计算经验匹配度 (0-100)"""
        
        # 基于用户完成的类似任务数量
        similar_tasks_count = self.db.query(func.count(TaskUnified.id)).filter(
            TaskUnified.assignee_id == user.id,
            TaskUnified.task_type == wbs.task_type,
            TaskUnified.status == 'COMPLETED'
        ).scalar()
        
        if similar_tasks_count == 0:
            return 40.0
        elif similar_tasks_count < 3:
            return 60.0
        elif similar_tasks_count < 10:
            return 80.0
        else:
            return 95.0
    
    def _calculate_availability(self, user: User, wbs: AIWbsSuggestion) -> float:
        """计算可用性评分 (0-100)"""
        
        # 计算用户当前工作负载
        current_workload = self._get_current_workload(user)
        
        # 可用性 = 100 - 当前负载
        availability = 100.0 - current_workload
        
        return max(0.0, availability)
    
    def _get_current_workload(self, user: User) -> float:
        """获取当前工作负载百分比"""
        
        # 统计用户正在进行的任务
        active_tasks = self.db.query(TaskUnified).filter(
            TaskUnified.assignee_id == user.id,
            TaskUnified.status.in_(['IN_PROGRESS', 'ACCEPTED'])
        ).all()
        
        if not active_tasks:
            return 0.0
        
        # 简化计算：每个任务占用20%
        return min(len(active_tasks) * 20.0, 100.0)
    
    def _calculate_performance_score(self, user: User, wbs: AIWbsSuggestion) -> float:
        """计算历史绩效评分 (0-100)"""
        
        # 查询用户完成的任务
        completed_tasks = self.db.query(TaskUnified).filter(
            TaskUnified.assignee_id == user.id,
            TaskUnified.status == 'COMPLETED'
        ).limit(20).all()
        
        if not completed_tasks:
            return 70.0  # 无历史数据，默认70分
        
        # 计算按时完成率
        on_time_count = 0
        for task in completed_tasks:
            if task.planned_end_date and task.actual_end_date:
                if task.actual_end_date <= task.planned_end_date:
                    on_time_count += 1
        
        on_time_rate = (on_time_count / len(completed_tasks)) * 100 if completed_tasks else 70.0
        
        return on_time_rate
    
    def _get_hourly_rate(self, user: User) -> float:
        """获取用户小时费率"""
        
        # TODO: 从用户配置或薪资表获取
        # 目前基于角色的默认费率
        
        role = (user.role or "").lower()
        
        if 'senior' in role or '高级' in role or '资深' in role:
            return 200.0
        elif 'middle' in role or '中级' in role:
            return 150.0
        elif 'junior' in role or '初级' in role:
            return 100.0
        else:
            return 120.0
    
    def _calculate_cost_efficiency(self, match_score: float, hourly_rate: float) -> float:
        """计算成本效益评分 (0-100)"""
        
        # 成本效益 = 匹配度 / (费率/100)
        # 费率越低，成本效益越高
        
        if hourly_rate == 0:
            return match_score
        
        normalized_rate = hourly_rate / 100.0
        efficiency = match_score / normalized_rate
        
        return min(efficiency, 100.0)
    
    def _generate_recommendation_reason(
        self,
        user: User,
        wbs: AIWbsSuggestion,
        skill_match: float,
        experience_match: float,
        availability: float,
        performance: float
    ) -> str:
        """生成推荐理由"""
        
        reasons = []
        
        if skill_match >= 80:
            reasons.append("技能高度匹配")
        elif skill_match >= 60:
            reasons.append("技能较为匹配")
        
        if experience_match >= 80:
            reasons.append("拥有丰富的相关经验")
        
        if availability >= 80:
            reasons.append("当前工作负载较低")
        elif availability < 40:
            reasons.append("当前工作负载较高（需谨慎分配）")
        
        if performance >= 80:
            reasons.append("历史绩效优秀")
        
        if not reasons:
            reasons.append("综合评估基本符合要求")
        
        return "；".join(reasons)
    
    def _analyze_strengths(
        self,
        user: User,
        wbs: AIWbsSuggestion,
        skill_match: float,
        performance: float
    ) -> List[Dict]:
        """分析优势"""
        
        strengths = []
        
        if skill_match >= 80:
            strengths.append({
                "category": "技能",
                "description": "技能高度匹配任务要求",
                "score": skill_match
            })
        
        if performance >= 80:
            strengths.append({
                "category": "绩效",
                "description": "历史任务完成质量高",
                "score": performance
            })
        
        return strengths
    
    def _analyze_weaknesses(
        self,
        user: User,
        wbs: AIWbsSuggestion,
        skill_match: float,
        availability: float
    ) -> List[Dict]:
        """分析劣势"""
        
        weaknesses = []
        
        if skill_match < 60:
            weaknesses.append({
                "category": "技能",
                "description": "技能匹配度偏低",
                "impact": "HIGH"
            })
        
        if availability < 40:
            weaknesses.append({
                "category": "可用性",
                "description": "当前工作负载过高",
                "impact": "HIGH"
            })
        
        return weaknesses
    
    def _optimize_allocations(
        self,
        allocations: List[AIResourceAllocation],
        wbs: AIWbsSuggestion
    ) -> List[AIResourceAllocation]:
        """优化资源分配（避免冲突）"""
        
        # 简化版：选择Top 3推荐
        # TODO: 实现更复杂的优化算法（遗传算法、模拟退火等）
        
        optimized = allocations[:5]  # 最多推荐5个人选
        
        # 设置优先级和分配类型
        if optimized:
            optimized[0].allocation_type = "PRIMARY"
            optimized[0].priority = "HIGH"
            optimized[0].sequence = 1
            
            for i, alloc in enumerate(optimized[1:], 2):
                alloc.allocation_type = "SECONDARY" if i == 2 else "BACKUP"
                alloc.priority = "MEDIUM" if i == 2 else "LOW"
                alloc.sequence = i
        
        return optimized
