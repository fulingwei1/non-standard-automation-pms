# -*- coding: utf-8 -*-
"""
项目成本预测服务测试
测试覆盖: 成本预测、历史数据、预测模型、准确度评估
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from sqlalchemy.orm import Session

from app.models import (
    CostOptimizationSuggestion,
    CostPrediction,
    EarnedValueData,
    Project,
)
from app.services.project_cost_prediction.service import ProjectCostPredictionService


class TestProjectCostPredictionServiceInit:
    """测试服务初始化"""
    
    def test_init_with_api_key(self, db_session):
        """测试带API密钥的初始化"""
        service = ProjectCostPredictionService(db_session, glm_api_key="test_key")
        assert service.db == db_session
        assert service.calculator is not None
    
    def test_init_without_api_key(self, db_session):
        """测试无API密钥的初始化"""
        with patch.dict('os.environ', {}, clear=True):
            service = ProjectCostPredictionService(db_session)
            assert service.db == db_session
            assert service.calculator is not None


class TestCreatePrediction:
    """测试成本预测创建"""
    
    def test_create_prediction_project_not_found(self, db_session):
        """测试项目不存在的情况"""
        service = ProjectCostPredictionService(db_session)
        
        with pytest.raises(ValueError, match="项目不存在"):
            service.create_prediction(project_id=99999)
    
    def test_create_prediction_no_evm_data(self, db_session, sample_project):
        """测试项目无EVM数据的情况"""
        service = ProjectCostPredictionService(db_session)
        
        with pytest.raises(ValueError, match="项目无EVM数据"):
            service.create_prediction(project_id=sample_project.id)
    
    def test_create_prediction_traditional_method(
        self, db_session, sample_project, sample_evm_data
    ):
        """测试传统方法预测"""
        service = ProjectCostPredictionService(db_session)
        
        prediction = service.create_prediction(
            project_id=sample_project.id,
            use_ai=False,
            created_by=1,
            notes="测试预测"
        )
        
        assert prediction.project_id == sample_project.id
        assert prediction.project_code == sample_project.project_code
        assert prediction.prediction_method == "CPI_BASED"
        assert prediction.predicted_eac is not None
        assert prediction.predicted_eac > 0
        assert prediction.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert prediction.created_by == 1
        assert prediction.notes == "测试预测"
    
    @patch('app.services.project_cost_prediction.service.GLM5CostPredictor')
    def test_create_prediction_ai_method(
        self, mock_predictor_class, db_session, sample_project, sample_evm_data
    ):
        """测试AI方法预测"""
        # Mock AI预测器
        mock_predictor = Mock()
        mock_predictor.predict_eac.return_value = {
            'predicted_eac': 12000.0,
            'confidence': 85.0,
            'eac_lower_bound': 11500.0,
            'eac_upper_bound': 12500.0,
            'eac_most_likely': 12000.0,
            'reasoning': 'AI分析结果',
            'key_assumptions': ['假设1', '假设2'],
            'uncertainty_factors': ['不确定因素1']
        }
        mock_predictor.analyze_cost_risks.return_value = {
            'overrun_probability': 65.0,
            'risk_level': 'MEDIUM',
            'risk_score': 55.0,
            'risk_factors': ['因素1'],
            'trend_analysis': '趋势分析',
            'cost_trend': 'INCREASING',
            'key_concerns': ['关注点1'],
            'early_warning_signals': ['预警信号1']
        }
        mock_predictor_class.return_value = mock_predictor
        
        service = ProjectCostPredictionService(db_session, glm_api_key="test_key")
        service.ai_predictor = mock_predictor
        
        prediction = service.create_prediction(
            project_id=sample_project.id,
            use_ai=True,
            prediction_version="V2.0"
        )
        
        assert prediction.prediction_method == "AI_GLM5"
        assert prediction.predicted_eac == Decimal('12000.0')
        assert prediction.predicted_eac_confidence == Decimal('85.0')
        assert prediction.risk_level == "MEDIUM"
        assert prediction.prediction_version == "V2.0"
    
    @patch('app.services.project_cost_prediction.service.GLM5CostPredictor')
    def test_create_prediction_with_high_risk_generates_suggestions(
        self, mock_predictor_class, db_session, sample_project, sample_evm_data
    ):
        """测试高风险预测自动生成优化建议"""
        # Mock AI预测器
        mock_predictor = Mock()
        mock_predictor.predict_eac.return_value = {
            'predicted_eac': 15000.0,
            'confidence': 80.0,
            'eac_lower_bound': 14500.0,
            'eac_upper_bound': 15500.0,
            'eac_most_likely': 15000.0,
            'reasoning': 'AI分析结果'
        }
        mock_predictor.analyze_cost_risks.return_value = {
            'overrun_probability': 85.0,
            'risk_level': 'HIGH',
            'risk_score': 75.0,
            'risk_factors': [],
            'trend_analysis': '',
            'cost_trend': 'INCREASING'
        }
        mock_predictor.generate_optimization_suggestions.return_value = [
            {
                'title': '优化建议1',
                'type': 'RESOURCE_OPTIMIZATION',
                'priority': 'HIGH',
                'description': '描述',
                'current_situation': '当前情况',
                'proposed_action': '建议措施',
                'implementation_steps': ['步骤1'],
                'estimated_cost_saving': 2000.0,
                'implementation_cost': 500.0,
                'impact_on_schedule': '无影响',
                'impact_on_quality': '无影响',
                'implementation_risk': 'LOW',
                'ai_confidence_score': 75.0,
                'ai_reasoning': 'AI推理'
            }
        ]
        mock_predictor_class.return_value = mock_predictor
        
        service = ProjectCostPredictionService(db_session, glm_api_key="test_key")
        service.ai_predictor = mock_predictor
        
        prediction = service.create_prediction(
            project_id=sample_project.id,
            use_ai=True
        )
        
        assert prediction.risk_level == "HIGH"
        
        # 验证生成了优化建议
        suggestions = db_session.query(CostOptimizationSuggestion).filter(
            CostOptimizationSuggestion.prediction_id == prediction.id
        ).all()
        
        assert len(suggestions) >= 1
        assert suggestions[0].suggestion_title == '优化建议1'
        assert suggestions[0].priority == 'HIGH'
    
    def test_create_prediction_saves_cpi_trend_data(
        self, db_session, sample_project, sample_evm_history
    ):
        """测试预测保存CPI趋势数据"""
        service = ProjectCostPredictionService(db_session)
        
        prediction = service.create_prediction(
            project_id=sample_project.id,
            use_ai=False
        )
        
        assert prediction.cpi_trend_data is not None
        assert len(prediction.cpi_trend_data) == len(sample_evm_history)
        assert all('month' in item and 'cpi' in item for item in prediction.cpi_trend_data)


class TestGetLatestPrediction:
    """测试获取最新预测"""
    
    def test_get_latest_prediction_exists(
        self, db_session, sample_project, sample_predictions
    ):
        """测试获取最新预测 - 存在预测"""
        service = ProjectCostPredictionService(db_session)
        
        latest = service.get_latest_prediction(sample_project.id)
        
        assert latest is not None
        assert latest.project_id == sample_project.id
        # 应该返回最新的一条
        assert latest.prediction_date == max(p.prediction_date for p in sample_predictions)
    
    def test_get_latest_prediction_not_exists(self, db_session, sample_project):
        """测试获取最新预测 - 无预测"""
        service = ProjectCostPredictionService(db_session)
        
        latest = service.get_latest_prediction(sample_project.id)
        
        assert latest is None


class TestGetPredictionHistory:
    """测试获取预测历史"""
    
    def test_get_prediction_history_no_limit(
        self, db_session, sample_project, sample_predictions
    ):
        """测试获取全部历史"""
        service = ProjectCostPredictionService(db_session)
        
        history = service.get_prediction_history(sample_project.id)
        
        assert len(history) == len(sample_predictions)
        # 验证按日期降序排列
        dates = [p.prediction_date for p in history]
        assert dates == sorted(dates, reverse=True)
    
    def test_get_prediction_history_with_limit(
        self, db_session, sample_project, sample_predictions
    ):
        """测试限制数量的历史"""
        service = ProjectCostPredictionService(db_session)
        
        history = service.get_prediction_history(sample_project.id, limit=2)
        
        assert len(history) == 2
        # 应该是最新的两条
        dates = [p.prediction_date for p in history]
        all_dates = [p.prediction_date for p in sample_predictions]
        assert dates == sorted(all_dates, reverse=True)[:2]
    
    def test_get_prediction_history_empty(self, db_session, sample_project):
        """测试空历史"""
        service = ProjectCostPredictionService(db_session)
        
        history = service.get_prediction_history(sample_project.id)
        
        assert history == []


class TestGetCostHealthAnalysis:
    """测试成本健康度分析"""
    
    def test_get_cost_health_analysis_no_prediction(self, db_session, sample_project):
        """测试无预测数据时的健康度分析"""
        service = ProjectCostPredictionService(db_session)
        
        with pytest.raises(ValueError, match="项目暂无预测数据"):
            service.get_cost_health_analysis(sample_project.id)
    
    def test_get_cost_health_analysis_healthy_project(
        self, db_session, sample_project, sample_healthy_prediction
    ):
        """测试健康项目的健康度分析"""
        service = ProjectCostPredictionService(db_session)
        
        analysis = service.get_cost_health_analysis(sample_project.id)
        
        assert analysis['project_id'] == sample_project.id
        assert analysis['health_score'] >= 80
        assert analysis['risk_level'] == 'LOW'
        assert 'recommendation' in analysis
        assert '良好' in analysis['recommendation']
    
    def test_get_cost_health_analysis_risky_project(
        self, db_session, sample_project, sample_risky_prediction
    ):
        """测试高风险项目的健康度分析"""
        service = ProjectCostPredictionService(db_session)
        
        analysis = service.get_cost_health_analysis(sample_project.id)
        
        assert analysis['project_id'] == sample_project.id
        assert analysis['health_score'] < 60
        assert analysis['risk_level'] in ['HIGH', 'CRITICAL']
        assert '风险' in analysis['recommendation']
    
    def test_get_cost_health_analysis_includes_suggestions(
        self, db_session, sample_project, sample_prediction_with_suggestions
    ):
        """测试健康度分析包含建议摘要"""
        service = ProjectCostPredictionService(db_session)
        
        analysis = service.get_cost_health_analysis(sample_project.id)
        
        assert 'suggestions_summary' in analysis
        summary = analysis['suggestions_summary']
        assert 'pending' in summary
        assert 'approved' in summary
        assert 'in_progress' in summary


class TestPrivateMethods:
    """测试私有方法"""
    
    def test_prepare_project_data(self, db_session, sample_project, sample_evm_data):
        """测试准备项目数据"""
        service = ProjectCostPredictionService(db_session)
        
        project_data = service._prepare_project_data(sample_project, sample_evm_data)
        
        assert project_data['project_code'] == sample_project.project_code
        assert project_data['project_name'] == sample_project.project_name
        assert project_data['bac'] == sample_evm_data.budget_at_completion
        assert project_data['current_cpi'] == sample_evm_data.cost_performance_index
        assert 'planned_start' in project_data
        assert 'planned_end' in project_data
    
    def test_prepare_evm_history_data(self, db_session, sample_evm_history):
        """测试准备EVM历史数据"""
        service = ProjectCostPredictionService(db_session)
        
        history_data = service._prepare_evm_history_data(sample_evm_history)
        
        assert len(history_data) == len(sample_evm_history)
        for item in history_data:
            assert 'period' in item
            assert 'cpi' in item
            assert 'spi' in item
            assert 'ac' in item
            assert 'ev' in item
            assert 'pv' in item
    
    def test_traditional_eac_prediction(self, db_session, sample_evm_data):
        """测试传统EAC预测方法"""
        service = ProjectCostPredictionService(db_session)
        
        result = service._traditional_eac_prediction(sample_evm_data)
        
        assert 'predicted_eac' in result
        assert 'confidence' in result
        assert 'eac_lower_bound' in result
        assert 'eac_upper_bound' in result
        assert 'eac_most_likely' in result
        assert result['predicted_eac'] > 0
        assert result['confidence'] == 70.0
    
    def test_traditional_eac_prediction_zero_cpi(self, db_session, sample_evm_data):
        """测试CPI为0时的传统预测"""
        service = ProjectCostPredictionService(db_session)
        sample_evm_data.cost_performance_index = Decimal('0')
        
        result = service._traditional_eac_prediction(sample_evm_data)
        
        # 应该使用默认的120%预测
        expected_eac = float(sample_evm_data.budget_at_completion * Decimal('1.2'))
        assert result['predicted_eac'] == expected_eac
    
    def test_traditional_risk_analysis_low_risk(self, db_session, sample_evm_data):
        """测试低风险场景的传统风险分析"""
        service = ProjectCostPredictionService(db_session)
        sample_evm_data.cost_performance_index = Decimal('0.98')
        
        result = service._traditional_risk_analysis(sample_evm_data, [])
        
        assert result['risk_level'] == 'LOW'
        assert result['overrun_probability'] == 20.0
    
    def test_traditional_risk_analysis_medium_risk(self, db_session, sample_evm_data):
        """测试中风险场景的传统风险分析"""
        service = ProjectCostPredictionService(db_session)
        sample_evm_data.cost_performance_index = Decimal('0.88')
        
        result = service._traditional_risk_analysis(sample_evm_data, [])
        
        assert result['risk_level'] == 'MEDIUM'
        assert result['overrun_probability'] == 50.0
    
    def test_traditional_risk_analysis_high_risk(self, db_session, sample_evm_data):
        """测试高风险场景的传统风险分析"""
        service = ProjectCostPredictionService(db_session)
        sample_evm_data.cost_performance_index = Decimal('0.78')
        
        result = service._traditional_risk_analysis(sample_evm_data, [])
        
        assert result['risk_level'] == 'HIGH'
        assert result['overrun_probability'] == 75.0
    
    def test_traditional_risk_analysis_critical_risk(self, db_session, sample_evm_data):
        """测试严重风险场景的传统风险分析"""
        service = ProjectCostPredictionService(db_session)
        sample_evm_data.cost_performance_index = Decimal('0.65')
        
        result = service._traditional_risk_analysis(sample_evm_data, [])
        
        assert result['risk_level'] == 'CRITICAL'
        assert result['overrun_probability'] == 90.0
    
    def test_calculate_data_quality_sufficient_data(self, db_session):
        """测试充足数据的质量评分"""
        service = ProjectCostPredictionService(db_session)
        
        history_data = [{'period': f'2024-{i:02d}', 'cpi': 0.9} for i in range(1, 13)]
        score = service._calculate_data_quality(history_data)
        
        assert score == Decimal('100')
    
    def test_calculate_data_quality_moderate_data(self, db_session):
        """测试中等数据的质量评分"""
        service = ProjectCostPredictionService(db_session)
        
        history_data = [{'period': f'2024-0{i}', 'cpi': 0.9} for i in range(1, 5)]
        score = service._calculate_data_quality(history_data)
        
        assert score == Decimal('85')
    
    def test_calculate_data_quality_insufficient_data(self, db_session):
        """测试不足数据的质量评分"""
        service = ProjectCostPredictionService(db_session)
        
        history_data = [{'period': '2024-01', 'cpi': 0.9}]
        score = service._calculate_data_quality(history_data)
        
        assert score == Decimal('70')
    
    def test_calculate_health_score_healthy(self, db_session, sample_healthy_prediction):
        """测试健康项目的健康评分"""
        service = ProjectCostPredictionService(db_session)
        suggestions_summary = {'pending': 0, 'approved': 0, 'in_progress': 0}
        
        score = service._calculate_health_score(sample_healthy_prediction, suggestions_summary)
        
        assert score >= 90
    
    def test_calculate_health_score_with_pending_suggestions(
        self, db_session, sample_healthy_prediction
    ):
        """测试有待处理建议的健康评分"""
        service = ProjectCostPredictionService(db_session)
        suggestions_summary = {'pending': 3, 'approved': 0, 'in_progress': 0}
        
        score = service._calculate_health_score(sample_healthy_prediction, suggestions_summary)
        
        # 应该扣除5分
        assert score < 100
    
    def test_calculate_health_score_critical_risk(
        self, db_session, sample_critical_prediction
    ):
        """测试严重风险项目的健康评分"""
        service = ProjectCostPredictionService(db_session)
        suggestions_summary = {'pending': 0, 'approved': 0, 'in_progress': 0}
        
        score = service._calculate_health_score(sample_critical_prediction, suggestions_summary)
        
        assert score <= 60
    
    def test_get_health_recommendation_excellent(self, db_session):
        """测试优秀健康度的建议"""
        service = ProjectCostPredictionService(db_session)
        
        recommendation = service._get_health_recommendation(85, 'LOW')
        
        assert '良好' in recommendation
    
    def test_get_health_recommendation_moderate(self, db_session):
        """测试中等健康度的建议"""
        service = ProjectCostPredictionService(db_session)
        
        recommendation = service._get_health_recommendation(65, 'MEDIUM')
        
        assert '风险' in recommendation or '建议' in recommendation
    
    def test_get_health_recommendation_poor(self, db_session):
        """测试较差健康度的建议"""
        service = ProjectCostPredictionService(db_session)
        
        recommendation = service._get_health_recommendation(45, 'HIGH')
        
        assert '优化' in recommendation or '措施' in recommendation
    
    def test_get_health_recommendation_critical(self, db_session):
        """测试严重健康度的建议"""
        service = ProjectCostPredictionService(db_session)
        
        recommendation = service._get_health_recommendation(25, 'CRITICAL')
        
        assert '紧急' in recommendation or '干预' in recommendation


# ==================== Fixtures ====================

@pytest.fixture
def db_session():
    """模拟数据库会话"""
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    session.query.return_value.filter.return_value.count.return_value = 0
    return session


@pytest.fixture
def sample_project():
    """示例项目"""
    return Project(
        id=1,
        project_code="PRJ001",
        project_name="测试项目",
        planned_start_date=date(2024, 1, 1),
        planned_end_date=date(2024, 12, 31)
    )


@pytest.fixture
def sample_evm_data(sample_project):
    """示例EVM数据"""
    return EarnedValueData(
        id=1,
        project_id=sample_project.id,
        period_date=date(2024, 6, 30),
        budget_at_completion=Decimal('10000'),
        planned_value=Decimal('5000'),
        earned_value=Decimal('4500'),
        actual_cost=Decimal('4800'),
        cost_performance_index=Decimal('0.9375'),
        schedule_performance_index=Decimal('0.9'),
        actual_percent_complete=Decimal('45')
    )


@pytest.fixture
def sample_evm_history(sample_project):
    """示例EVM历史数据（最近3期）"""
    return [
        EarnedValueData(
            id=i,
            project_id=sample_project.id,
            period_date=date(2024, i, 30),
            budget_at_completion=Decimal('10000'),
            planned_value=Decimal(str(i * 1000)),
            earned_value=Decimal(str(i * 900)),
            actual_cost=Decimal(str(i * 950)),
            cost_performance_index=Decimal('0.947'),
            schedule_performance_index=Decimal('0.9')
        )
        for i in range(4, 7)
    ]


@pytest.fixture
def sample_predictions(sample_project, sample_evm_data, db_session):
    """示例预测记录（3条）"""
    predictions = [
        CostPrediction(
            id=i,
            project_id=sample_project.id,
            project_code=sample_project.project_code,
            prediction_date=date(2024, 6, i),
            prediction_version=f"V{i}.0",
            evm_data_id=sample_evm_data.id,
            current_pv=sample_evm_data.planned_value,
            current_ev=sample_evm_data.earned_value,
            current_ac=sample_evm_data.actual_cost,
            current_bac=sample_evm_data.budget_at_completion,
            current_cpi=sample_evm_data.cost_performance_index,
            current_spi=sample_evm_data.schedule_performance_index,
            current_percent_complete=sample_evm_data.actual_percent_complete,
            predicted_eac=Decimal('10500'),
            predicted_eac_confidence=Decimal('75'),
            prediction_method="CPI_BASED",
            risk_level="MEDIUM",
            risk_score=Decimal('50'),
            overrun_probability=Decimal('50')
        )
        for i in range(1, 4)
    ]
    
    # Mock查询返回
    db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = predictions
    db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = predictions[-1]
    
    return predictions


@pytest.fixture
def sample_healthy_prediction(sample_project, sample_evm_data, db_session):
    """健康项目的预测"""
    prediction = CostPrediction(
        id=1,
        project_id=sample_project.id,
        project_code=sample_project.project_code,
        prediction_date=date.today(),
        prediction_version="V1.0",
        evm_data_id=sample_evm_data.id,
        current_pv=Decimal('5000'),
        current_ev=Decimal('5100'),
        current_ac=Decimal('4900'),
        current_bac=Decimal('10000'),
        current_cpi=Decimal('1.04'),
        current_spi=Decimal('1.02'),
        predicted_eac=Decimal('9800'),
        predicted_eac_confidence=Decimal('85'),
        prediction_method="AI_GLM5",
        risk_level="LOW",
        risk_score=Decimal('15'),
        overrun_probability=Decimal('10')
    )
    
    db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = prediction
    return prediction


@pytest.fixture
def sample_risky_prediction(sample_project, sample_evm_data, db_session):
    """高风险项目的预测"""
    prediction = CostPrediction(
        id=2,
        project_id=sample_project.id,
        project_code=sample_project.project_code,
        prediction_date=date.today(),
        prediction_version="V1.0",
        evm_data_id=sample_evm_data.id,
        current_pv=Decimal('5000'),
        current_ev=Decimal('4000'),
        current_ac=Decimal('5500'),
        current_bac=Decimal('10000'),
        current_cpi=Decimal('0.727'),
        current_spi=Decimal('0.8'),
        predicted_eac=Decimal('13000'),
        predicted_eac_confidence=Decimal('75'),
        prediction_method="AI_GLM5",
        risk_level="HIGH",
        risk_score=Decimal('80'),
        overrun_probability=Decimal('75')
    )
    
    db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = prediction
    return prediction


@pytest.fixture
def sample_critical_prediction(sample_project, sample_evm_data, db_session):
    """严重风险项目的预测"""
    prediction = CostPrediction(
        id=3,
        project_id=sample_project.id,
        project_code=sample_project.project_code,
        prediction_date=date.today(),
        prediction_version="V1.0",
        evm_data_id=sample_evm_data.id,
        current_pv=Decimal('5000'),
        current_ev=Decimal('3500'),
        current_ac=Decimal('6000'),
        current_bac=Decimal('10000'),
        current_cpi=Decimal('0.583'),
        current_spi=Decimal('0.7'),
        predicted_eac=Decimal('15000'),
        predicted_eac_confidence=Decimal('70'),
        prediction_method="AI_GLM5",
        risk_level="CRITICAL",
        risk_score=Decimal('95'),
        overrun_probability=Decimal('90')
    )
    
    return prediction


@pytest.fixture
def sample_prediction_with_suggestions(sample_project, sample_evm_data, db_session):
    """带优化建议的预测"""
    prediction = CostPrediction(
        id=4,
        project_id=sample_project.id,
        project_code=sample_project.project_code,
        prediction_date=date.today(),
        prediction_version="V1.0",
        evm_data_id=sample_evm_data.id,
        current_pv=Decimal('5000'),
        current_ev=Decimal('4500'),
        current_ac=Decimal('5000'),
        current_bac=Decimal('10000'),
        current_cpi=Decimal('0.9'),
        predicted_eac=Decimal('11000'),
        predicted_eac_confidence=Decimal('80'),
        prediction_method="AI_GLM5",
        risk_level="MEDIUM",
        risk_score=Decimal('55'),
        overrun_probability=Decimal('60')
    )
    
    # Mock建议查询
    def count_side_effect(*args, **kwargs):
        # 根据filter条件返回不同的count
        return 2  # pending
    
    mock_filter = MagicMock()
    mock_filter.count.side_effect = [2, 1, 1]  # pending, approved, in_progress
    db_session.query.return_value.filter.return_value = mock_filter
    db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = prediction
    
    return prediction
