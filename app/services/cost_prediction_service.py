# -*- coding: utf-8 -*-
"""
成本预测与优化服务
使用GLM-5 AI模型进行成本预测、风险分析和优化建议生成
"""

import json
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import requests
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.models import (
    CostOptimizationSuggestion,
    CostPrediction,
    EarnedValueData,
    Project,
)
from app.services.evm_service import EVMCalculator


class GLM5CostPredictor:
    """
    GLM-5成本预测器
    
    使用智谱AI GLM-5模型进行成本预测和分析
    """
    
    # GLM-5 API配置
    API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化GLM-5预测器
        
        Args:
            api_key: 智谱AI API密钥（如未提供，从环境变量获取）
        """
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        if not self.api_key:
            raise ValueError("GLM API密钥未配置。请设置环境变量 GLM_API_KEY 或传入 api_key 参数")
        
        self.calculator = EVMCalculator()
    
    def predict_eac(
        self,
        project_data: Dict,
        evm_history: List[Dict],
        additional_context: Optional[Dict] = None
    ) -> Dict:
        """
        使用GLM-5预测完工估算（EAC）
        
        Args:
            project_data: 项目基础数据
            evm_history: EVM历史数据
            additional_context: 额外上下文信息
        
        Returns:
            预测结果字典
        """
        # 构建AI提示词
        prompt = self._build_eac_prediction_prompt(
            project_data, evm_history, additional_context
        )
        
        # 调用GLM-5 API
        response = self._call_glm5_api(prompt, temperature=0.3)
        
        # 解析AI响应
        prediction_result = self._parse_eac_prediction(response, project_data)
        
        return prediction_result
    
    def analyze_cost_risks(
        self,
        project_data: Dict,
        evm_history: List[Dict],
        current_evm: Dict
    ) -> Dict:
        """
        分析成本超支风险
        
        Args:
            project_data: 项目数据
            evm_history: EVM历史
            current_evm: 当前EVM状态
        
        Returns:
            风险分析结果
        """
        prompt = self._build_risk_analysis_prompt(
            project_data, evm_history, current_evm
        )
        
        response = self._call_glm5_api(prompt, temperature=0.4)
        
        risk_analysis = self._parse_risk_analysis(response)
        
        return risk_analysis
    
    def generate_optimization_suggestions(
        self,
        project_data: Dict,
        prediction_result: Dict,
        risk_analysis: Dict
    ) -> List[Dict]:
        """
        生成成本优化建议
        
        Args:
            project_data: 项目数据
            prediction_result: 预测结果
            risk_analysis: 风险分析结果
        
        Returns:
            优化建议列表
        """
        prompt = self._build_optimization_prompt(
            project_data, prediction_result, risk_analysis
        )
        
        response = self._call_glm5_api(prompt, temperature=0.6)
        
        suggestions = self._parse_optimization_suggestions(response)
        
        return suggestions
    
    def _build_eac_prediction_prompt(
        self,
        project_data: Dict,
        evm_history: List[Dict],
        additional_context: Optional[Dict]
    ) -> str:
        """构建EAC预测提示词"""
        
        # 准备历史数据摘要
        history_summary = self._summarize_evm_history(evm_history)
        
        prompt = f"""
你是一位资深的项目成本管理专家，精通挣值管理（EVM）和成本预测。

# 任务
基于项目的当前状态和历史数据，预测项目的最终成本（EAC - Estimate at Completion）。

# 项目基本信息
- 项目编号：{project_data.get('project_code')}
- 项目名称：{project_data.get('project_name')}
- 完工预算（BAC）：{project_data.get('bac')} 元
- 计划开始日期：{project_data.get('planned_start')}
- 计划结束日期：{project_data.get('planned_end')}
- 当前日期：{date.today()}

# 当前EVM状态
- 计划价值（PV）：{project_data.get('current_pv')} 元
- 挣得价值（EV）：{project_data.get('current_ev')} 元
- 实际成本（AC）：{project_data.get('current_ac')} 元
- 成本绩效指数（CPI）：{project_data.get('current_cpi')}
- 进度绩效指数（SPI）：{project_data.get('current_spi')}
- 完成百分比：{project_data.get('percent_complete')}%

# 历史趋势
{history_summary}

# 额外上下文
{json.dumps(additional_context or {}, ensure_ascii=False, indent=2)}

# 输出要求
请以JSON格式返回预测结果，包含以下字段：
{{
    "predicted_eac": <预测的完工估算（数值）>,
    "confidence": <置信度（0-100）>,
    "prediction_method": <预测方法说明>,
    "eac_lower_bound": <乐观情况下的EAC>,
    "eac_upper_bound": <悲观情况下的EAC>,
    "eac_most_likely": <最可能的EAC>,
    "reasoning": <预测的详细推理过程>,
    "key_assumptions": [<关键假设列表>],
    "uncertainty_factors": [<不确定因素列表>]
}}

注意：
1. 综合考虑CPI和SPI的趋势
2. 分析历史数据的波动性
3. 考虑项目当前阶段的特点
4. 使用三点估算法（乐观、最可能、悲观）
5. 确保预测结果具有实际可操作性
"""
        
        return prompt
    
    def _build_risk_analysis_prompt(
        self,
        project_data: Dict,
        evm_history: List[Dict],
        current_evm: Dict
    ) -> str:
        """构建风险分析提示词"""
        
        prompt = f"""
你是一位项目风险管理专家，擅长识别成本超支风险并评估其概率和影响。

# 任务
分析项目的成本超支风险，识别关键风险因素，并评估超支概率。

# 项目信息
- 项目编号：{project_data.get('project_code')}
- 完工预算（BAC）：{project_data.get('bac')} 元
- 当前成本绩效指数（CPI）：{current_evm.get('cpi')}
- 当前进度绩效指数（SPI）：{current_evm.get('spi')}
- 当前实际成本（AC）：{current_evm.get('ac')} 元
- 完成百分比：{current_evm.get('percent_complete')}%

# 历史CPI趋势
{json.dumps([{'period': h.get('period'), 'cpi': h.get('cpi')} for h in evm_history], ensure_ascii=False)}

# 输出要求
以JSON格式返回风险分析结果：
{{
    "overrun_probability": <超支概率（0-100）>,
    "risk_level": <风险等级：LOW/MEDIUM/HIGH/CRITICAL>,
    "risk_score": <风险评分（0-100）>,
    "risk_factors": [
        {{
            "factor": <风险因素名称>,
            "impact": <影响程度：LOW/MEDIUM/HIGH>,
            "weight": <权重（0-1）>,
            "description": <详细描述>,
            "evidence": <支持证据>
        }}
    ],
    "trend_analysis": <趋势分析说明>,
    "cost_trend": <成本趋势：IMPROVING/STABLE/DECLINING/VOLATILE>,
    "key_concerns": [<关键关注点列表>],
    "early_warning_signals": [<预警信号列表>]
}}
"""
        
        return prompt
    
    def _build_optimization_prompt(
        self,
        project_data: Dict,
        prediction_result: Dict,
        risk_analysis: Dict
    ) -> str:
        """构建优化建议提示词"""
        
        prompt = f"""
你是一位项目成本优化专家，擅长提出切实可行的成本削减和优化方案。

# 任务
基于成本预测和风险分析，生成具体的成本优化建议。

# 项目信息
- 项目编号：{project_data.get('project_code')}
- 完工预算（BAC）：{project_data.get('bac')} 元
- 预测完工成本（EAC）：{prediction_result.get('predicted_eac')} 元
- 预期超支：{float(prediction_result.get('predicted_eac', 0)) - float(project_data.get('bac', 0))} 元

# 风险分析
- 风险等级：{risk_analysis.get('risk_level')}
- 超支概率：{risk_analysis.get('overrun_probability')}%
- 主要风险因素：{json.dumps(risk_analysis.get('risk_factors', []), ensure_ascii=False)}

# 输出要求
生成3-5条优化建议，每条建议以JSON格式返回：
[
    {{
        "title": <建议标题>,
        "type": <类型：RESOURCE_OPTIMIZATION/SCOPE_ADJUSTMENT/PROCESS_IMPROVEMENT/VENDOR_NEGOTIATION/SCHEDULE_OPTIMIZATION>,
        "priority": <优先级：CRITICAL/HIGH/MEDIUM/LOW>,
        "description": <详细描述>,
        "current_situation": <当前情况分析>,
        "proposed_action": <建议采取的行动>,
        "implementation_steps": [
            {{
                "step": <步骤序号>,
                "action": <行动内容>,
                "duration_days": <所需天数>,
                "responsible": <责任方>
            }}
        ],
        "estimated_cost_saving": <预计成本节约（数值）>,
        "implementation_cost": <实施成本（数值）>,
        "roi_percentage": <ROI百分比>,
        "impact_on_schedule": <对进度的影响：POSITIVE/NEUTRAL/NEGATIVE>,
        "impact_on_quality": <对质量的影响：POSITIVE/NEUTRAL/NEGATIVE>,
        "implementation_risk": <实施风险：LOW/MEDIUM/HIGH>,
        "ai_confidence_score": <AI置信度（0-100）>,
        "ai_reasoning": <AI推理过程>
    }}
]

注意：
1. 建议要具体、可操作
2. 成本节约估算要基于实际数据
3. 考虑实施的可行性和风险
4. 平衡成本、进度、质量三者关系
"""
        
        return prompt
    
    def _call_glm5_api(
        self,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 4000
    ) -> str:
        """
        调用GLM-5 API
        
        Args:
            prompt: 提示词
            temperature: 温度参数（0-1）
            max_tokens: 最大token数
        
        Returns:
            API响应文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "glm-4-plus",  # 使用GLM-4-Plus（最新版本）
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的项目成本管理和风险分析专家。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                self.API_BASE_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"GLM-5 API调用失败: {str(e)}")
    
    def _parse_eac_prediction(
        self,
        ai_response: str,
        project_data: Dict
    ) -> Dict:
        """解析EAC预测响应"""
        try:
            # 尝试提取JSON内容
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(ai_response)
            
            # 验证和补充必要字段
            bac = Decimal(str(project_data.get('bac', 0)))
            predicted_eac = Decimal(str(result.get('predicted_eac', bac)))
            
            return {
                "predicted_eac": float(predicted_eac),
                "confidence": float(result.get('confidence', 70)),
                "prediction_method": result.get('prediction_method', 'AI_GLM5'),
                "eac_lower_bound": float(result.get('eac_lower_bound', predicted_eac * Decimal('0.95'))),
                "eac_upper_bound": float(result.get('eac_upper_bound', predicted_eac * Decimal('1.05'))),
                "eac_most_likely": float(result.get('eac_most_likely', predicted_eac)),
                "reasoning": result.get('reasoning', ''),
                "key_assumptions": result.get('key_assumptions', []),
                "uncertainty_factors": result.get('uncertainty_factors', [])
            }
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # 解析失败时使用传统方法
            bac = Decimal(str(project_data.get('bac', 0)))
            cpi = Decimal(str(project_data.get('current_cpi', 1)))
            ac = Decimal(str(project_data.get('current_ac', 0)))
            ev = Decimal(str(project_data.get('current_ev', 0)))
            
            if cpi > 0:
                predicted_eac = ac + (bac - ev) / cpi
            else:
                predicted_eac = bac * Decimal('1.2')
            
            return {
                "predicted_eac": float(predicted_eac),
                "confidence": 50.0,
                "prediction_method": "CPI_BASED_FALLBACK",
                "eac_lower_bound": float(predicted_eac * Decimal('0.95')),
                "eac_upper_bound": float(predicted_eac * Decimal('1.05')),
                "eac_most_likely": float(predicted_eac),
                "reasoning": f"AI解析失败，使用CPI方法回退。错误: {str(e)}",
                "key_assumptions": ["CPI保持当前水平"],
                "uncertainty_factors": ["AI预测不可用"]
            }
    
    def _parse_risk_analysis(self, ai_response: str) -> Dict:
        """解析风险分析响应"""
        try:
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(ai_response)
            
            return {
                "overrun_probability": float(result.get('overrun_probability', 50)),
                "risk_level": result.get('risk_level', 'MEDIUM'),
                "risk_score": float(result.get('risk_score', 50)),
                "risk_factors": result.get('risk_factors', []),
                "trend_analysis": result.get('trend_analysis', ''),
                "cost_trend": result.get('cost_trend', 'STABLE'),
                "key_concerns": result.get('key_concerns', []),
                "early_warning_signals": result.get('early_warning_signals', [])
            }
            
        except (json.JSONDecodeError, KeyError, ValueError):
            return {
                "overrun_probability": 50.0,
                "risk_level": "MEDIUM",
                "risk_score": 50.0,
                "risk_factors": [],
                "trend_analysis": "AI分析失败，使用默认风险评估",
                "cost_trend": "STABLE",
                "key_concerns": ["AI风险分析不可用"],
                "early_warning_signals": []
            }
    
    def _parse_optimization_suggestions(self, ai_response: str) -> List[Dict]:
        """解析优化建议响应"""
        try:
            # 提取JSON数组
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                suggestions = json.loads(json_str)
            else:
                suggestions = json.loads(ai_response)
            
            # 确保返回列表
            if isinstance(suggestions, dict):
                suggestions = [suggestions]
            
            return suggestions
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # 返回默认建议
            return [
                {
                    "title": "成本控制措施",
                    "type": "PROCESS_IMPROVEMENT",
                    "priority": "MEDIUM",
                    "description": "AI建议生成失败，建议进行人工成本分析",
                    "ai_confidence_score": 0
                }
            ]
    
    def _summarize_evm_history(self, evm_history: List[Dict]) -> str:
        """总结EVM历史数据"""
        if not evm_history:
            return "无历史数据"
        
        summary_lines = ["最近的EVM数据："]
        
        for i, data in enumerate(evm_history[-6:], 1):  # 最近6期
            summary_lines.append(
                f"{i}. {data.get('period')}: "
                f"CPI={data.get('cpi')}, SPI={data.get('spi')}, "
                f"AC={data.get('ac')}, EV={data.get('ev')}"
            )
        
        # 计算趋势
        if len(evm_history) >= 3:
            recent_cpi = [float(d.get('cpi', 1)) for d in evm_history[-3:]]
            if all(recent_cpi[i] < recent_cpi[i-1] for i in range(1, len(recent_cpi))):
                summary_lines.append("\n趋势分析：CPI持续下降，成本效率恶化")
            elif all(recent_cpi[i] > recent_cpi[i-1] for i in range(1, len(recent_cpi))):
                summary_lines.append("\n趋势分析：CPI持续上升，成本效率改善")
            else:
                summary_lines.append("\n趋势分析：CPI波动，成本控制不稳定")
        
        return "\n".join(summary_lines)


class CostPredictionService:
    """
    成本预测服务 - 业务逻辑层
    """
    
    def __init__(self, db: Session, glm_api_key: Optional[str] = None):
        self.db = db
        self.calculator = EVMCalculator()
        try:
            self.ai_predictor = GLM5CostPredictor(api_key=glm_api_key)
        except ValueError:
            # API密钥未配置时，ai_predictor为None
            self.ai_predictor = None
    
    def create_prediction(
        self,
        project_id: int,
        prediction_version: str = "V1.0",
        use_ai: bool = True,
        created_by: Optional[int] = None,
        notes: Optional[str] = None
    ) -> CostPrediction:
        """
        创建成本预测
        
        Args:
            project_id: 项目ID
            prediction_version: 预测版本号
            use_ai: 是否使用AI预测
            created_by: 创建人ID
            notes: 备注
        
        Returns:
            成本预测记录
        """
        # 获取项目信息
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: project_id={project_id}")
        
        # 获取最新的EVM数据
        latest_evm = self.db.query(EarnedValueData).filter(
            EarnedValueData.project_id == project_id
        ).order_by(desc(EarnedValueData.period_date)).first()
        
        if not latest_evm:
            raise ValueError(f"项目无EVM数据: project_id={project_id}")
        
        # 获取历史EVM数据（最近12期）
        evm_history = self.db.query(EarnedValueData).filter(
            EarnedValueData.project_id == project_id
        ).order_by(desc(EarnedValueData.period_date)).limit(12).all()
        
        # 准备数据
        project_data = {
            'project_code': project.project_code,
            'project_name': project.project_name,
            'bac': latest_evm.budget_at_completion,
            'current_pv': latest_evm.planned_value,
            'current_ev': latest_evm.earned_value,
            'current_ac': latest_evm.actual_cost,
            'current_cpi': latest_evm.cost_performance_index,
            'current_spi': latest_evm.schedule_performance_index,
            'percent_complete': latest_evm.actual_percent_complete,
            'planned_start': project.planned_start_date,
            'planned_end': project.planned_end_date,
        }
        
        evm_history_data = [
            {
                'period': str(evm.period_date),
                'cpi': float(evm.cost_performance_index or 1),
                'spi': float(evm.schedule_performance_index or 1),
                'ac': float(evm.actual_cost),
                'ev': float(evm.earned_value),
                'pv': float(evm.planned_value)
            }
            for evm in reversed(evm_history)
        ]
        
        # 执行预测
        if use_ai and self.ai_predictor:
            prediction_result = self.ai_predictor.predict_eac(
                project_data, evm_history_data
            )
            risk_analysis = self.ai_predictor.analyze_cost_risks(
                project_data, evm_history_data, {
                    'cpi': float(latest_evm.cost_performance_index or 1),
                    'spi': float(latest_evm.schedule_performance_index or 1),
                    'ac': float(latest_evm.actual_cost),
                    'percent_complete': float(latest_evm.actual_percent_complete or 0)
                }
            )
            prediction_method = "AI_GLM5"
        else:
            # 使用传统CPI方法
            prediction_result = self._traditional_eac_prediction(latest_evm)
            risk_analysis = self._traditional_risk_analysis(latest_evm, evm_history)
            prediction_method = "CPI_BASED"
        
        # 创建预测记录
        prediction = CostPrediction(
            project_id=project_id,
            project_code=project.project_code,
            prediction_date=date.today(),
            prediction_version=prediction_version,
            evm_data_id=latest_evm.id,
            # 当前状态快照
            current_pv=latest_evm.planned_value,
            current_ev=latest_evm.earned_value,
            current_ac=latest_evm.actual_cost,
            current_bac=latest_evm.budget_at_completion,
            current_cpi=latest_evm.cost_performance_index,
            current_spi=latest_evm.schedule_performance_index,
            current_percent_complete=latest_evm.actual_percent_complete,
            # AI预测结果
            predicted_eac=Decimal(str(prediction_result['predicted_eac'])),
            predicted_eac_confidence=Decimal(str(prediction_result['confidence'])),
            prediction_method=prediction_method,
            # 预测区间
            eac_lower_bound=Decimal(str(prediction_result.get('eac_lower_bound'))),
            eac_upper_bound=Decimal(str(prediction_result.get('eac_upper_bound'))),
            eac_most_likely=Decimal(str(prediction_result.get('eac_most_likely'))),
            # 超支风险
            overrun_probability=Decimal(str(risk_analysis['overrun_probability'])),
            expected_overrun_amount=Decimal(str(prediction_result['predicted_eac'])) - latest_evm.budget_at_completion,
            overrun_percentage=(
                (Decimal(str(prediction_result['predicted_eac'])) - latest_evm.budget_at_completion)
                / latest_evm.budget_at_completion * Decimal('100')
            ) if latest_evm.budget_at_completion > 0 else Decimal('0'),
            risk_level=risk_analysis['risk_level'],
            risk_score=Decimal(str(risk_analysis['risk_score'])),
            # 风险因素
            risk_factors=risk_analysis.get('risk_factors'),
            # 趋势分析
            cost_trend=risk_analysis.get('cost_trend'),
            trend_analysis=risk_analysis.get('trend_analysis'),
            cpi_trend_data=[{'month': d['period'], 'cpi': d['cpi']} for d in evm_history_data],
            # AI分析
            ai_analysis_summary=prediction_result.get('reasoning'),
            ai_insights={
                'key_assumptions': prediction_result.get('key_assumptions', []),
                'uncertainty_factors': prediction_result.get('uncertainty_factors', []),
                'key_concerns': risk_analysis.get('key_concerns', []),
                'early_warning_signals': risk_analysis.get('early_warning_signals', [])
            },
            # 元数据
            model_version="GLM-4-Plus" if use_ai else "Traditional",
            data_quality_score=self._calculate_data_quality(evm_history),
            created_by=created_by,
            notes=notes
        )
        
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        
        # 如果使用AI且超支风险高，自动生成优化建议
        if use_ai and self.ai_predictor and risk_analysis['risk_level'] in ['HIGH', 'CRITICAL']:
            self._generate_optimization_suggestions(prediction, project_data, prediction_result, risk_analysis)
        
        return prediction
    
    def _traditional_eac_prediction(self, latest_evm: EarnedValueData) -> Dict:
        """传统EAC预测方法"""
        cpi = latest_evm.cost_performance_index or Decimal('1')
        bac = latest_evm.budget_at_completion
        ac = latest_evm.actual_cost
        ev = latest_evm.earned_value
        
        if cpi > 0:
            eac = ac + (bac - ev) / cpi
        else:
            eac = bac * Decimal('1.2')
        
        return {
            'predicted_eac': float(eac),
            'confidence': 70.0,
            'eac_lower_bound': float(eac * Decimal('0.95')),
            'eac_upper_bound': float(eac * Decimal('1.05')),
            'eac_most_likely': float(eac),
            'reasoning': f"基于CPI={cpi}的传统预测方法"
        }
    
    def _traditional_risk_analysis(
        self,
        latest_evm: EarnedValueData,
        evm_history: List[EarnedValueData]
    ) -> Dict:
        """传统风险分析方法"""
        cpi = float(latest_evm.cost_performance_index or 1)
        
        # 简单的风险评估
        if cpi >= 0.95:
            risk_level = "LOW"
            overrun_probability = 20.0
        elif cpi >= 0.85:
            risk_level = "MEDIUM"
            overrun_probability = 50.0
        elif cpi >= 0.75:
            risk_level = "HIGH"
            overrun_probability = 75.0
        else:
            risk_level = "CRITICAL"
            overrun_probability = 90.0
        
        risk_score = 100 - (cpi * 100)
        
        return {
            'overrun_probability': overrun_probability,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': [],
            'trend_analysis': f"当前CPI为{cpi}",
            'cost_trend': 'STABLE',
            'key_concerns': [],
            'early_warning_signals': []
        }
    
    def _calculate_data_quality(self, evm_history: List[EarnedValueData]) -> Decimal:
        """计算数据质量评分"""
        score = Decimal('100')
        
        # 历史数据充分性
        if len(evm_history) < 3:
            score -= Decimal('30')
        elif len(evm_history) < 6:
            score -= Decimal('15')
        
        # 数据完整性
        for evm in evm_history:
            if not evm.is_verified:
                score -= Decimal('5')
        
        return max(score, Decimal('0'))
    
    def _generate_optimization_suggestions(
        self,
        prediction: CostPrediction,
        project_data: Dict,
        prediction_result: Dict,
        risk_analysis: Dict
    ):
        """生成优化建议"""
        if not self.ai_predictor:
            return
        
        try:
            suggestions = self.ai_predictor.generate_optimization_suggestions(
                project_data, prediction_result, risk_analysis
            )
            
            for idx, sug in enumerate(suggestions[:5], 1):  # 最多5条
                suggestion_code = f"OPT-{prediction.project_code}-{prediction.prediction_date.strftime('%Y%m')}-{idx:03d}"
                
                # 计算净收益和ROI
                cost_saving = Decimal(str(sug.get('estimated_cost_saving', 0)))
                impl_cost = Decimal(str(sug.get('implementation_cost', 0)))
                net_benefit = cost_saving - impl_cost
                roi = (net_benefit / impl_cost * Decimal('100')) if impl_cost > 0 else Decimal('0')
                
                suggestion_record = CostOptimizationSuggestion(
                    prediction_id=prediction.id,
                    project_id=prediction.project_id,
                    project_code=prediction.project_code,
                    suggestion_code=suggestion_code,
                    suggestion_title=sug.get('title'),
                    suggestion_type=sug.get('type'),
                    priority=sug.get('priority'),
                    description=sug.get('description'),
                    current_situation=sug.get('current_situation'),
                    proposed_action=sug.get('proposed_action'),
                    implementation_steps=sug.get('implementation_steps'),
                    estimated_cost_saving=cost_saving,
                    implementation_cost=impl_cost,
                    net_benefit=net_benefit,
                    roi_percentage=roi,
                    impact_on_schedule=sug.get('impact_on_schedule'),
                    impact_on_quality=sug.get('impact_on_quality'),
                    implementation_risk=sug.get('implementation_risk'),
                    ai_confidence_score=Decimal(str(sug.get('ai_confidence_score', 70))),
                    ai_reasoning=sug.get('ai_reasoning'),
                    created_by=prediction.created_by
                )
                
                self.db.add(suggestion_record)
            
            self.db.commit()
            
        except Exception as e:
            # 建议生成失败不影响预测创建
            print(f"优化建议生成失败: {str(e)}")
    
    def get_latest_prediction(self, project_id: int) -> Optional[CostPrediction]:
        """获取项目最新的成本预测"""
        return self.db.query(CostPrediction).filter(
            CostPrediction.project_id == project_id
        ).order_by(desc(CostPrediction.prediction_date)).first()
    
    def get_prediction_history(
        self,
        project_id: int,
        limit: Optional[int] = None
    ) -> List[CostPrediction]:
        """获取预测历史"""
        query = self.db.query(CostPrediction).filter(
            CostPrediction.project_id == project_id
        ).order_by(desc(CostPrediction.prediction_date))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
