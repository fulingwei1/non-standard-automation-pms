# -*- coding: utf-8 -*-
"""
GLM-5 AI服务集成
提供与智谱AI GLM-5模型的交互接口
"""

import os
import json
import time
from typing import Dict, List, Optional
import logging

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

logger = logging.getLogger(__name__)


class GLMService:
    """GLM-5 AI服务"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化GLM服务
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv('GLM_API_KEY')
        if not self.api_key:
            logger.warning("GLM API密钥未配置，AI功能将不可用")
            self.client = None
        else:
            if ZhipuAI is None:
                logger.error("zhipuai包未安装，请运行: pip install zhipuai")
                self.client = None
            else:
                self.client = ZhipuAI(api_key=self.api_key)
        
        self.model = "glm-4"  # 使用GLM-4模型
        self.max_retries = 3
        self.timeout = 30
    
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        return self.client is not None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Optional[str]:
        """
        与GLM模型对话
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数(0-1)
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            AI回复内容，失败返回None
        """
        if not self.is_available():
            logger.error("GLM服务不可用")
            return None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content
                else:
                    logger.warning(f"GLM响应为空: {response}")
                    return None
                    
            except Exception as e:
                logger.error(f"GLM请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    return None
        
        return None
    
    def generate_project_plan(
        self,
        project_name: str,
        project_type: str,
        requirements: str,
        industry: Optional[str] = None,
        complexity: Optional[str] = None,
        reference_projects: Optional[List[Dict]] = None
    ) -> Optional[Dict]:
        """
        生成项目计划
        
        Args:
            project_name: 项目名称
            project_type: 项目类型
            requirements: 项目需求
            industry: 行业
            complexity: 复杂度
            reference_projects: 参考项目列表
            
        Returns:
            项目计划JSON数据
        """
        prompt = self._build_plan_generation_prompt(
            project_name, project_type, requirements,
            industry, complexity, reference_projects
        )
        
        messages = [
            {"role": "system", "content": "你是一个专业的项目管理专家，擅长制定详细的项目计划。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.5, max_tokens=3000)
        
        if response:
            try:
                # 尝试解析JSON响应
                return self._parse_plan_response(response)
            except Exception as e:
                logger.error(f"解析计划响应失败: {e}")
                return None
        
        return None
    
    def decompose_wbs(
        self,
        task_name: str,
        task_description: str,
        task_type: str,
        estimated_duration: Optional[int] = None,
        reference_tasks: Optional[List[Dict]] = None
    ) -> Optional[List[Dict]]:
        """
        WBS任务分解
        
        Args:
            task_name: 任务名称
            task_description: 任务描述
            task_type: 任务类型
            estimated_duration: 预计工期
            reference_tasks: 参考任务列表
            
        Returns:
            子任务列表
        """
        prompt = self._build_wbs_decomposition_prompt(
            task_name, task_description, task_type,
            estimated_duration, reference_tasks
        )
        
        messages = [
            {"role": "system", "content": "你是一个项目管理专家，擅长工作分解结构(WBS)设计。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.6, max_tokens=2500)
        
        if response:
            try:
                return self._parse_wbs_response(response)
            except Exception as e:
                logger.error(f"解析WBS响应失败: {e}")
                return None
        
        return None
    
    def recommend_resources(
        self,
        task_info: Dict,
        available_users: List[Dict],
        constraints: Optional[Dict] = None
    ) -> Optional[List[Dict]]:
        """
        推荐资源分配
        
        Args:
            task_info: 任务信息
            available_users: 可用用户列表
            constraints: 约束条件
            
        Returns:
            资源分配建议列表
        """
        prompt = self._build_resource_recommendation_prompt(
            task_info, available_users, constraints
        )
        
        messages = [
            {"role": "system", "content": "你是一个资源管理专家，擅长人员分配和技能匹配。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, temperature=0.4, max_tokens=2000)
        
        if response:
            try:
                return self._parse_resource_response(response)
            except Exception as e:
                logger.error(f"解析资源推荐响应失败: {e}")
                return None
        
        return None
    
    def _build_plan_generation_prompt(
        self,
        project_name: str,
        project_type: str,
        requirements: str,
        industry: Optional[str],
        complexity: Optional[str],
        reference_projects: Optional[List[Dict]]
    ) -> str:
        """构建项目计划生成提示词"""
        
        prompt = f"""请为以下项目生成详细的项目计划:

项目名称: {project_name}
项目类型: {project_type}
行业领域: {industry or '通用'}
复杂度: {complexity or '中等'}

项目需求:
{requirements}

"""
        if reference_projects:
            prompt += "\n参考项目:\n"
            for i, proj in enumerate(reference_projects[:3], 1):
                prompt += f"{i}. {proj.get('name', '未知')} - {proj.get('type', '')} (工期:{proj.get('duration_days', '?')}天)\n"
        
        prompt += """
请以JSON格式返回项目计划，包含以下内容:
{
  "project_name": "项目名称",
  "estimated_duration_days": 预计工期天数,
  "estimated_effort_hours": 预计工时,
  "estimated_cost": 预计成本,
  "phases": [
    {
      "name": "阶段名称",
      "duration_days": 天数,
      "deliverables": ["交付物1", "交付物2"]
    }
  ],
  "milestones": [
    {
      "name": "里程碑名称",
      "phase": "所属阶段",
      "estimated_day": 第几天
    }
  ],
  "required_roles": [
    {
      "role": "角色名称",
      "skill_level": "技能等级",
      "count": 人数
    }
  ],
  "recommended_team_size": 推荐团队规模,
  "risk_factors": [
    {
      "category": "风险类别",
      "description": "风险描述",
      "mitigation": "缓解措施"
    }
  ]
}
"""
        return prompt
    
    def _build_wbs_decomposition_prompt(
        self,
        task_name: str,
        task_description: str,
        task_type: str,
        estimated_duration: Optional[int],
        reference_tasks: Optional[List[Dict]]
    ) -> str:
        """构建WBS分解提示词"""
        
        prompt = f"""请将以下任务进行WBS分解:

任务名称: {task_name}
任务类型: {task_type}
任务描述:
{task_description}

预计工期: {estimated_duration or '待估算'}天

"""
        if reference_tasks:
            prompt += "\n参考任务:\n"
            for i, task in enumerate(reference_tasks[:3], 1):
                prompt += f"{i}. {task.get('name', '未知')} (工时:{task.get('effort_hours', '?')}小时)\n"
        
        prompt += """
请以JSON数组格式返回子任务列表，每个子任务包含:
[
  {
    "task_name": "子任务名称",
    "task_description": "任务描述",
    "task_type": "任务类型",
    "estimated_duration_days": 预计工期,
    "estimated_effort_hours": 预计工时,
    "complexity": "SIMPLE/MEDIUM/COMPLEX",
    "required_skills": [{"skill": "技能", "level": "等级"}],
    "dependencies": [], // 依赖的子任务索引
    "deliverables": [{"name": "交付物", "type": "类型"}],
    "risk_level": "LOW/MEDIUM/HIGH"
  }
]
"""
        return prompt
    
    def _build_resource_recommendation_prompt(
        self,
        task_info: Dict,
        available_users: List[Dict],
        constraints: Optional[Dict]
    ) -> str:
        """构建资源推荐提示词"""
        
        prompt = f"""请为以下任务推荐合适的执行人员:

任务信息:
- 名称: {task_info.get('name', '未知')}
- 类型: {task_info.get('type', '未知')}
- 工时: {task_info.get('effort_hours', '?')}小时
- 所需技能: {', '.join([s.get('skill', '') for s in task_info.get('required_skills', [])])}

可用人员:
"""
        for i, user in enumerate(available_users[:10], 1):
            prompt += f"{i}. {user.get('name', '未知')} - {user.get('role', '')} "
            prompt += f"(技能:{', '.join(user.get('skills', []))})"
            prompt += f" [当前负载:{user.get('workload', 0)}%]\n"
        
        if constraints:
            prompt += f"\n约束条件: {constraints}\n"
        
        prompt += """
请以JSON数组格式返回推荐人员列表(最多5人)，按匹配度排序:
[
  {
    "user_id": 用户ID,
    "allocation_type": "PRIMARY/SECONDARY/BACKUP",
    "match_score": 匹配度(0-100),
    "skill_match_score": 技能匹配度,
    "availability_score": 可用性评分,
    "recommendation_reason": "推荐理由",
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["劣势1"]
  }
]
"""
        return prompt
    
    def _parse_plan_response(self, response: str) -> Dict:
        """解析计划生成响应"""
        # 尝试提取JSON部分
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # 如果没有找到JSON，返回原始文本
            return {"raw_response": response}
    
    def _parse_wbs_response(self, response: str) -> List[Dict]:
        """解析WBS分解响应"""
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return []
    
    def _parse_resource_response(self, response: str) -> List[Dict]:
        """解析资源推荐响应"""
        import re
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return []
