"""
AI需求理解服务
负责调用AI模型进行需求分析、问题生成、可行性评估
"""
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.presale_ai_requirement_analysis import PresaleAIRequirementAnalysis
from app.schemas.presale_ai_requirement import (
    RequirementAnalysisRequest,
    RequirementRefinementRequest,
    RequirementUpdateRequest,
    StructuredRequirement,
    ClarificationQuestion,
    FeasibilityAnalysis,
    EquipmentItem,
    ProcessStep,
    TechnicalParameter
)
from app.core.config import settings
import httpx


class AIRequirementAnalyzer:
    """AI需求分析器 - 核心AI引擎"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', None)
        self.model = model
        self.api_base_url = "https://api.openai.com/v1/chat/completions"
        
    async def analyze_requirement(
        self, 
        raw_requirement: str, 
        analysis_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        分析原始需求，生成结构化输出
        
        Args:
            raw_requirement: 原始需求描述
            analysis_depth: 分析深度 (quick/standard/deep)
            
        Returns:
            包含结构化需求、设备清单、工艺流程等的字典
        """
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(analysis_depth)
        
        # 构建用户提示词
        user_prompt = self._build_user_prompt(raw_requirement)
        
        # 调用AI模型
        try:
            response = await self._call_openai_api(system_prompt, user_prompt)
            
            # 解析响应
            parsed_result = self._parse_ai_response(response)
            
            # 计算置信度
            confidence_score = self._calculate_confidence_score(raw_requirement, parsed_result)
            parsed_result['confidence_score'] = confidence_score
            
            return parsed_result
            
        except Exception as e:
            # 降级处理：使用规则引擎
            return self._fallback_rule_based_analysis(raw_requirement)
    
    async def generate_clarification_questions(
        self, 
        raw_requirement: str,
        structured_data: Optional[Dict[str, Any]] = None
    ) -> List[ClarificationQuestion]:
        """
        生成澄清问题
        
        Args:
            raw_requirement: 原始需求
            structured_data: 已有的结构化数据（可选）
            
        Returns:
            澄清问题列表
        """
        
        system_prompt = """你是一位资深的非标自动化项目需求分析专家。
你的任务是识别客户需求中的缺口和模糊点，生成高质量的澄清问题。

问题应该：
1. 聚焦关键技术参数和约束条件
2. 识别隐含假设
3. 澄清功能边界
4. 明确验收标准
5. 评估资源和时间约束

请以JSON格式返回5-10个澄清问题，每个问题包含：
- question_id: 问题编号
- category: 问题分类（技术参数/功能需求/约束条件/验收标准/资源预算）
- question: 问题内容
- importance: 重要性（critical/high/medium/low）
- suggested_answer: 建议的回答方向（可选）
"""
        
        user_prompt = f"""原始需求：
{raw_requirement}

{"当前已识别信息：" + json.dumps(structured_data, ensure_ascii=False, indent=2) if structured_data else ""}

请生成5-10个澄清问题。"""
        
        try:
            response = await self._call_openai_api(system_prompt, user_prompt)
            questions_data = self._extract_json_from_response(response)
            
            if isinstance(questions_data, dict) and 'questions' in questions_data:
                questions_data = questions_data['questions']
            
            questions = []
            for i, q in enumerate(questions_data[:10], 1):
                try:
                    questions.append(ClarificationQuestion(
                        question_id=q.get('question_id', i),
                        category=q.get('category', '其他'),
                        question=q['question'],
                        importance=q.get('importance', 'medium'),
                        suggested_answer=q.get('suggested_answer')
                    ))
                except Exception:
                    continue
            
            return questions
            
        except Exception as e:
            # 降级：使用规则生成问题
            return self._fallback_generate_questions(raw_requirement)
    
    async def perform_feasibility_analysis(
        self,
        raw_requirement: str,
        structured_data: Dict[str, Any]
    ) -> FeasibilityAnalysis:
        """
        执行技术可行性分析
        
        Args:
            raw_requirement: 原始需求
            structured_data: 结构化需求数据
            
        Returns:
            可行性分析结果
        """
        
        system_prompt = """你是非标自动化领域的技术可行性评估专家。
请从以下维度评估项目的技术可行性：
1. 技术成熟度
2. 资源可得性
3. 开发复杂度
4. 风险因素
5. 时间可行性

返回JSON格式的评估结果。"""
        
        user_prompt = f"""需求：{raw_requirement}

结构化数据：
{json.dumps(structured_data, ensure_ascii=False, indent=2)}

请进行可行性分析。"""
        
        try:
            response = await self._call_openai_api(system_prompt, user_prompt)
            analysis_data = self._extract_json_from_response(response)
            
            return FeasibilityAnalysis(
                overall_feasibility=analysis_data.get('overall_feasibility', 'medium'),
                technical_risks=analysis_data.get('technical_risks', []),
                resource_requirements=analysis_data.get('resource_requirements', {}),
                estimated_complexity=analysis_data.get('estimated_complexity', 'medium'),
                development_challenges=analysis_data.get('development_challenges', []),
                recommendations=analysis_data.get('recommendations', [])
            )
            
        except Exception:
            return self._fallback_feasibility_analysis(structured_data)
    
    def _build_system_prompt(self, analysis_depth: str) -> str:
        """构建系统提示词"""
        
        base_prompt = """你是一位资深的非标自动化项目需求分析专家，拥有20年的行业经验。
你擅长：
1. 从客户的自然语言描述中提取关键技术需求
2. 识别隐含需求和潜在风险
3. 将需求结构化为可执行的技术规格
4. 识别设备、工艺、参数等核心要素

请分析客户需求，并以JSON格式返回以下内容：
{
  "structured_requirement": {
    "project_type": "项目类型",
    "industry": "应用行业",
    "core_objectives": ["核心目标1", "核心目标2"],
    "functional_requirements": ["功能需求1", "功能需求2"],
    "non_functional_requirements": ["性能需求", "可靠性需求"],
    "constraints": ["约束条件1"],
    "assumptions": ["假设条件1"]
  },
  "equipment_list": [
    {
      "name": "设备名称",
      "type": "设备类型",
      "quantity": 1,
      "specifications": {},
      "priority": "high/medium/low"
    }
  ],
  "process_flow": [
    {
      "step_number": 1,
      "name": "步骤名称",
      "description": "步骤描述",
      "parameters": {},
      "equipment_required": ["设备1"]
    }
  ],
  "technical_parameters": [
    {
      "parameter_name": "参数名",
      "value": "值或范围",
      "unit": "单位",
      "tolerance": "公差",
      "is_critical": true/false
    }
  ],
  "acceptance_criteria": ["验收标准1", "验收标准2"]
}
"""
        
        if analysis_depth == "deep":
            base_prompt += "\n请进行深度分析，考虑所有可能的技术细节和边界条件。"
        elif analysis_depth == "quick":
            base_prompt += "\n请快速提取核心信息，聚焦最关键的要素。"
            
        return base_prompt
    
    def _build_user_prompt(self, raw_requirement: str) -> str:
        """构建用户提示词"""
        return f"""客户需求描述：

{raw_requirement}

请分析上述需求。"""
    
    async def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """调用OpenAI API"""
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        return self._extract_json_from_response(response)
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """从响应中提取JSON"""
        
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取代码块中的JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试查找任何JSON对象
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Unable to extract JSON from response: {response[:200]}")
    
    def _calculate_confidence_score(
        self, 
        raw_requirement: str, 
        parsed_result: Dict[str, Any]
    ) -> float:
        """计算需求理解置信度"""
        
        score = 0.0
        weights = {
            'length': 0.1,  # 需求描述长度
            'structured': 0.25,  # 结构化程度
            'equipment': 0.2,  # 设备识别
            'parameters': 0.25,  # 参数识别
            'process': 0.2  # 流程识别
        }
        
        # 需求长度评分
        req_length = len(raw_requirement)
        if req_length > 500:
            score += weights['length'] * 1.0
        elif req_length > 200:
            score += weights['length'] * 0.7
        else:
            score += weights['length'] * 0.4
        
        # 结构化需求评分
        structured = parsed_result.get('structured_requirement', {})
        if structured:
            completeness = sum([
                len(structured.get('core_objectives', [])) > 0,
                len(structured.get('functional_requirements', [])) > 0,
                len(structured.get('non_functional_requirements', [])) > 0,
                structured.get('project_type') is not None
            ]) / 4.0
            score += weights['structured'] * completeness
        
        # 设备清单评分
        equipment_list = parsed_result.get('equipment_list', [])
        if equipment_list:
            score += weights['equipment'] * min(len(equipment_list) / 5.0, 1.0)
        
        # 技术参数评分
        tech_params = parsed_result.get('technical_parameters', [])
        if tech_params:
            score += weights['parameters'] * min(len(tech_params) / 8.0, 1.0)
        
        # 工艺流程评分
        process_flow = parsed_result.get('process_flow', [])
        if process_flow:
            score += weights['process'] * min(len(process_flow) / 5.0, 1.0)
        
        return round(min(score, 1.0), 2)
    
    def _fallback_rule_based_analysis(self, raw_requirement: str) -> Dict[str, Any]:
        """降级：基于规则的需求分析"""
        
        # 简单的关键词提取
        equipment_keywords = ['机器人', '传送带', '视觉系统', 'PLC', '传感器', '执行器', '控制器']
        process_keywords = ['焊接', '装配', '检测', '搬运', '包装', '码垛']
        
        detected_equipment = [kw for kw in equipment_keywords if kw in raw_requirement]
        detected_processes = [kw for kw in process_keywords if kw in raw_requirement]
        
        return {
            'structured_requirement': {
                'project_type': '非标自动化',
                'industry': '未识别',
                'core_objectives': ['自动化生产'],
                'functional_requirements': detected_processes or ['待澄清'],
                'non_functional_requirements': [],
                'constraints': [],
                'assumptions': []
            },
            'equipment_list': [
                {'name': eq, 'type': '待确认', 'quantity': 1, 'priority': 'medium'}
                for eq in detected_equipment
            ],
            'process_flow': [],
            'technical_parameters': [],
            'acceptance_criteria': [],
            'confidence_score': 0.35
        }
    
    def _fallback_generate_questions(self, raw_requirement: str) -> List[ClarificationQuestion]:
        """降级：生成默认澄清问题"""
        
        default_questions = [
            {"category": "技术参数", "question": "请明确设备的具体技术参数要求（如速度、精度、负载等）", "importance": "critical"},
            {"category": "功能需求", "question": "请详细说明自动化系统需要实现的具体功能", "importance": "high"},
            {"category": "约束条件", "question": "项目是否有特殊的空间、环境或安全约束？", "importance": "high"},
            {"category": "验收标准", "question": "请明确项目的验收标准和成功指标", "importance": "critical"},
            {"category": "资源预算", "question": "项目的预算范围和交付时间要求是什么？", "importance": "medium"}
        ]
        
        return [
            ClarificationQuestion(
                question_id=i+1,
                category=q['category'],
                question=q['question'],
                importance=q['importance']
            )
            for i, q in enumerate(default_questions)
        ]
    
    def _fallback_feasibility_analysis(self, structured_data: Dict[str, Any]) -> FeasibilityAnalysis:
        """降级：默认可行性分析"""
        
        return FeasibilityAnalysis(
            overall_feasibility="medium",
            technical_risks=["需求信息不足，无法完整评估"],
            resource_requirements={"人力": "待评估", "设备": "待评估"},
            estimated_complexity="medium",
            development_challenges=["需进一步澄清需求细节"],
            recommendations=["建议补充详细的技术参数和功能说明"]
        )


class PresaleAIRequirementService:
    """AI需求理解服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analyzer = AIRequirementAnalyzer()
    
    async def analyze_requirement(
        self,
        request: RequirementAnalysisRequest,
        user_id: int
    ) -> PresaleAIRequirementAnalysis:
        """分析需求"""
        
        # 执行AI分析
        analysis_result = await self.analyzer.analyze_requirement(
            request.raw_requirement,
            request.analysis_depth
        )
        
        # 生成澄清问题
        clarification_questions = await self.analyzer.generate_clarification_questions(
            request.raw_requirement,
            analysis_result.get('structured_requirement')
        )
        
        # 执行可行性分析
        feasibility = await self.analyzer.perform_feasibility_analysis(
            request.raw_requirement,
            analysis_result
        )
        
        # 保存到数据库
        db_record = PresaleAIRequirementAnalysis(
            presale_ticket_id=request.presale_ticket_id,
            raw_requirement=request.raw_requirement,
            structured_requirement=analysis_result.get('structured_requirement'),
            clarification_questions=[q.dict() for q in clarification_questions],
            confidence_score=analysis_result.get('confidence_score'),
            feasibility_analysis=feasibility.dict(),
            equipment_list=analysis_result.get('equipment_list'),
            process_flow=analysis_result.get('process_flow'),
            technical_parameters=analysis_result.get('technical_parameters'),
            acceptance_criteria=analysis_result.get('acceptance_criteria'),
            ai_model_used=request.ai_model,
            ai_analysis_version="1.0.0",
            status="draft",
            created_by=user_id
        )
        
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        
        return db_record
    
    def get_analysis(self, analysis_id: int) -> Optional[PresaleAIRequirementAnalysis]:
        """获取分析结果"""
        return self.db.query(PresaleAIRequirementAnalysis).filter(
            PresaleAIRequirementAnalysis.id == analysis_id
        ).first()
    
    async def refine_requirement(
        self,
        request: RequirementRefinementRequest,
        user_id: int
    ) -> PresaleAIRequirementAnalysis:
        """精炼需求"""
        
        # 获取现有分析
        analysis = self.get_analysis(request.analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {request.analysis_id} not found")
        
        # 合并原始需求和额外上下文
        enhanced_requirement = analysis.raw_requirement
        if request.additional_context:
            enhanced_requirement += f"\n\n补充信息：\n{request.additional_context}"
        
        # 重新分析
        refined_result = await self.analyzer.analyze_requirement(
            enhanced_requirement,
            "deep"
        )
        
        # 更新数据库记录
        analysis.structured_requirement = refined_result.get('structured_requirement')
        analysis.equipment_list = refined_result.get('equipment_list')
        analysis.process_flow = refined_result.get('process_flow')
        analysis.technical_parameters = refined_result.get('technical_parameters')
        analysis.acceptance_criteria = refined_result.get('acceptance_criteria')
        analysis.confidence_score = refined_result.get('confidence_score')
        analysis.is_refined = True
        analysis.refinement_count += 1
        analysis.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    def get_clarification_questions(
        self,
        ticket_id: int
    ) -> Tuple[List[ClarificationQuestion], Optional[int]]:
        """获取澄清问题"""
        
        # 获取最新的分析记录
        analysis = self.db.query(PresaleAIRequirementAnalysis).filter(
            PresaleAIRequirementAnalysis.presale_ticket_id == ticket_id
        ).order_by(desc(PresaleAIRequirementAnalysis.created_at)).first()
        
        if not analysis or not analysis.clarification_questions:
            return [], None
        
        questions = [
            ClarificationQuestion(**q) 
            for q in analysis.clarification_questions
        ]
        
        return questions, analysis.id
    
    def update_structured_requirement(
        self,
        request: RequirementUpdateRequest,
        user_id: int
    ) -> PresaleAIRequirementAnalysis:
        """更新结构化需求"""
        
        analysis = self.get_analysis(request.analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {request.analysis_id} not found")
        
        # 更新各个字段
        if request.structured_requirement:
            analysis.structured_requirement = request.structured_requirement.dict()
        
        if request.equipment_list:
            analysis.equipment_list = [eq.dict() for eq in request.equipment_list]
        
        if request.process_flow:
            analysis.process_flow = [step.dict() for step in request.process_flow]
        
        if request.technical_parameters:
            analysis.technical_parameters = [param.dict() for param in request.technical_parameters]
        
        if request.acceptance_criteria:
            analysis.acceptance_criteria = request.acceptance_criteria
        
        analysis.status = "reviewed"
        analysis.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    def get_requirement_confidence(
        self,
        ticket_id: int
    ) -> Dict[str, Any]:
        """获取置信度评分"""
        
        analysis = self.db.query(PresaleAIRequirementAnalysis).filter(
            PresaleAIRequirementAnalysis.presale_ticket_id == ticket_id
        ).order_by(desc(PresaleAIRequirementAnalysis.created_at)).first()
        
        if not analysis:
            return {
                'analysis_id': None,
                'presale_ticket_id': ticket_id,
                'confidence_score': 0.0,
                'assessment': 'no_analysis',
                'recommendations': ['请先进行需求分析']
            }
        
        score = analysis.confidence_score or 0.0
        
        # 评估等级
        if score >= 0.85:
            assessment = "high_confidence"
            recommendations = ["需求理解充分，可以进入方案设计阶段"]
        elif score >= 0.60:
            assessment = "medium_confidence"
            recommendations = ["需求基本清晰，建议澄清部分细节"]
        else:
            assessment = "low_confidence"
            recommendations = ["需求信息不足，需要与客户进一步沟通"]
        
        # 分数分解
        score_breakdown = {
            '需求完整性': round(score * 0.3, 2),
            '技术清晰度': round(score * 0.3, 2),
            '参数明确性': round(score * 0.25, 2),
            '可执行性': round(score * 0.15, 2)
        }
        
        return {
            'analysis_id': analysis.id,
            'presale_ticket_id': ticket_id,
            'confidence_score': score,
            'score_breakdown': score_breakdown,
            'assessment': assessment,
            'recommendations': recommendations
        }
