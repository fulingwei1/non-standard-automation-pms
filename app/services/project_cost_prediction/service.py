# -*- coding: utf-8 -*-
"""
项目成本预测服务
提供成本预测、风险分析、优化建议等核心业务逻辑
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import (
    CostOptimizationSuggestion,
    CostPrediction,
    EarnedValueData,
    Project,
)
from app.services.evm_service import EVMCalculator
from app.services.project_cost_prediction.ai_predictor import GLM5CostPredictor
from app.utils.db_helpers import save_obj


class ProjectCostPredictionService:
    """
    项目成本预测服务
    
    核心业务逻辑：
    - 成本预测（AI/传统）
    - 风险分析
    - 优化建议生成
    - 预测历史管理
    """
    
    def __init__(self, db: Session, glm_api_key: Optional[str] = None):
        """
        初始化服务
        
        Args:
            db: 数据库会话
            glm_api_key: GLM API密钥（可选）
        """
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
            
        Raises:
            ValueError: 项目不存在或无EVM数据
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
        project_data = self._prepare_project_data(project, latest_evm)
        evm_history_data = self._prepare_evm_history_data(evm_history)
        
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
        prediction = self._create_prediction_record(
            project, latest_evm, prediction_result, risk_analysis,
            prediction_version, prediction_method, evm_history_data,
            created_by, notes
        )
        
        save_obj(self.db, prediction)
        
        # 如果使用AI且超支风险高，自动生成优化建议
        if use_ai and self.ai_predictor and risk_analysis['risk_level'] in ['HIGH', 'CRITICAL']:
            self._generate_optimization_suggestions(
                prediction, project_data, prediction_result, risk_analysis
            )
        
        return prediction
    
    def get_latest_prediction(self, project_id: int) -> Optional[CostPrediction]:
        """
        获取项目最新的成本预测
        
        Args:
            project_id: 项目ID
            
        Returns:
            最新预测记录，无预测时返回None
        """
        return self.db.query(CostPrediction).filter(
            CostPrediction.project_id == project_id
        ).order_by(desc(CostPrediction.prediction_date)).first()
    
    def get_prediction_history(
        self,
        project_id: int,
        limit: Optional[int] = None
    ) -> List[CostPrediction]:
        """
        获取预测历史
        
        Args:
            project_id: 项目ID
            limit: 返回数量限制
            
        Returns:
            预测记录列表
        """
        query = self.db.query(CostPrediction).filter(
            CostPrediction.project_id == project_id
        ).order_by(desc(CostPrediction.prediction_date))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_cost_health_analysis(self, project_id: int) -> Dict:
        """
        获取项目成本健康度分析
        
        Args:
            project_id: 项目ID
            
        Returns:
            健康度分析结果
            
        Raises:
            ValueError: 项目无预测数据
        """
        prediction = self.get_latest_prediction(project_id)
        
        if not prediction:
            raise ValueError(f"项目暂无预测数据: project_id={project_id}")
        
        # 统计优化建议
        suggestions_summary = self._get_suggestions_summary(project_id)
        
        # 计算健康评分
        health_score = self._calculate_health_score(prediction, suggestions_summary)
        
        # 生成建议
        recommendation = self._get_health_recommendation(health_score, prediction.risk_level)
        
        return {
            "project_id": project_id,
            "health_score": health_score,
            "risk_level": prediction.risk_level,
            "overrun_probability": float(prediction.overrun_probability or 0),
            "expected_overrun_amount": float(prediction.expected_overrun_amount or 0),
            "cost_trend": prediction.cost_trend,
            "current_cpi": float(prediction.current_cpi or 1),
            "prediction_date": prediction.prediction_date,
            "suggestions_summary": suggestions_summary,
            "recommendation": recommendation
        }
    
    # ==================== 私有方法 ====================
    
    def _prepare_project_data(self, project: Project, latest_evm: EarnedValueData) -> Dict:
        """准备项目数据"""
        return {
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
    
    def _prepare_evm_history_data(self, evm_history: List[EarnedValueData]) -> List[Dict]:
        """准备EVM历史数据"""
        return [
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
    
    def _create_prediction_record(
        self,
        project: Project,
        latest_evm: EarnedValueData,
        prediction_result: Dict,
        risk_analysis: Dict,
        prediction_version: str,
        prediction_method: str,
        evm_history_data: List[Dict],
        created_by: Optional[int],
        notes: Optional[str]
    ) -> CostPrediction:
        """创建预测记录"""
        return CostPrediction(
            project_id=project.id,
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
            model_version="GLM-4-Plus" if prediction_method == "AI_GLM5" else "Traditional",
            data_quality_score=self._calculate_data_quality(evm_history_data),
            created_by=created_by,
            notes=notes
        )
    
    def _traditional_eac_prediction(self, latest_evm: EarnedValueData) -> Dict:
        """传统EAC预测方法"""
        cpi = latest_evm.cost_performance_index if latest_evm.cost_performance_index is not None else Decimal('1')
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
    
    def _calculate_data_quality(self, evm_history_data: List[Dict]) -> Decimal:
        """计算数据质量评分"""
        score = Decimal('100')
        
        # 历史数据充分性
        if len(evm_history_data) < 3:
            score -= Decimal('30')
        elif len(evm_history_data) < 6:
            score -= Decimal('15')
        
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
    
    def _get_suggestions_summary(self, project_id: int) -> Dict:
        """获取优化建议摘要"""
        pending = self.db.query(CostOptimizationSuggestion).filter(
            CostOptimizationSuggestion.project_id == project_id,
            CostOptimizationSuggestion.status == "PENDING"
        ).count()
        
        approved = self.db.query(CostOptimizationSuggestion).filter(
            CostOptimizationSuggestion.project_id == project_id,
            CostOptimizationSuggestion.status == "APPROVED"
        ).count()
        
        in_progress = self.db.query(CostOptimizationSuggestion).filter(
            CostOptimizationSuggestion.project_id == project_id,
            CostOptimizationSuggestion.status == "IN_PROGRESS"
        ).count()
        
        return {
            "pending": pending,
            "approved": approved,
            "in_progress": in_progress
        }
    
    def _calculate_health_score(
        self,
        prediction: CostPrediction,
        suggestions_summary: Dict
    ) -> float:
        """计算健康评分"""
        health_score = 100.0
        
        # 根据超支风险扣分
        if prediction.risk_level == "CRITICAL":
            health_score -= 40
        elif prediction.risk_level == "HIGH":
            health_score -= 25
        elif prediction.risk_level == "MEDIUM":
            health_score -= 10
        
        # 根据CPI扣分
        if prediction.current_cpi:
            cpi = float(prediction.current_cpi)
            if cpi < 0.8:
                health_score -= 20
            elif cpi < 0.9:
                health_score -= 10
        
        # 有待处理建议则扣分
        if suggestions_summary["pending"] > 0:
            health_score -= 5
        
        return max(0, health_score)
    
    def _get_health_recommendation(self, health_score: float, risk_level: str) -> str:
        """根据健康评分和风险等级生成建议"""
        if health_score >= 80:
            return "项目成本状况良好，继续保持。"
        elif health_score >= 60:
            return "项目成本存在一定风险，建议关注优化建议。"
        elif health_score >= 40:
            return "项目成本风险较高，建议立即采取优化措施。"
        else:
            return "项目成本风险严重，需要紧急干预！"
