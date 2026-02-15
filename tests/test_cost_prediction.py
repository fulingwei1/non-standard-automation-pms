# -*- coding: utf-8 -*-
"""
成本预测与优化系统测试

测试覆盖：
1. 数据模型创建和关系
2. AI预测服务（使用mock）
3. API端点
4. 边界条件和异常处理
"""

import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    CostOptimizationSuggestion,
    CostPrediction,
    EarnedValueData,
    Project,
    User,
)
from app.services.cost_prediction_service import (
    CostPredictionService,
    GLM5CostPredictor,
)


# ==================== Fixtures ====================

@pytest.fixture
def test_project(db: Session) -> Project:
    """创建测试项目"""
    project = Project(
        project_code="TEST-COST-001",
        project_name="成本预测测试项目",
        budget_amount=Decimal("1000000.00"),
        planned_start_date=date.today() - timedelta(days=180),
        planned_end_date=date.today() + timedelta(days=180),
        status="IN_PROGRESS"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def test_evm_data(db: Session, test_project: Project) -> EarnedValueData:
    """创建测试EVM数据"""
    evm = EarnedValueData(
        project_id=test_project.id,
        project_code=test_project.project_code,
        period_type="MONTH",
        period_date=date.today(),
        period_label="2026-02",
        planned_value=Decimal("500000.00"),
        earned_value=Decimal("450000.00"),
        actual_cost=Decimal("480000.00"),
        budget_at_completion=Decimal("1000000.00"),
        schedule_variance=Decimal("-50000.00"),
        cost_variance=Decimal("-30000.00"),
        schedule_performance_index=Decimal("0.90"),
        cost_performance_index=Decimal("0.9375"),
        actual_percent_complete=Decimal("45.00"),
        is_verified=True
    )
    db.add(evm)
    db.commit()
    db.refresh(evm)
    return evm


@pytest.fixture
def test_evm_history(db: Session, test_project: Project) -> list:
    """创建EVM历史数据"""
    history = []
    
    # 创建6个月的历史数据，模拟CPI逐渐下降
    base_date = date.today() - timedelta(days=150)
    cpi_values = [1.05, 1.02, 0.98, 0.95, 0.92, 0.9375]
    
    for i in range(6):
        evm = EarnedValueData(
            project_id=test_project.id,
            project_code=test_project.project_code,
            period_type="MONTH",
            period_date=base_date + timedelta(days=30*i),
            period_label=f"2025-{7+i:02d}",
            planned_value=Decimal(str(100000 * (i+1))),
            earned_value=Decimal(str(95000 * (i+1))),
            actual_cost=Decimal(str(100000 * (i+1) / cpi_values[i])),
            budget_at_completion=Decimal("1000000.00"),
            cost_performance_index=Decimal(str(cpi_values[i])),
            schedule_performance_index=Decimal("0.95"),
            is_verified=True
        )
        db.add(evm)
        history.append(evm)
    
    db.commit()
    return history


# ==================== 数据模型测试 ====================

class TestCostPredictionModel:
    """成本预测模型测试"""
    
    def test_create_prediction(self, db: Session, test_project: Project, test_evm_data: EarnedValueData):
        """测试创建预测记录"""
        prediction = CostPrediction(
            project_id=test_project.id,
            project_code=test_project.project_code,
            prediction_date=date.today(),
            prediction_version="V1.0",
            evm_data_id=test_evm_data.id,
            current_bac=Decimal("1000000.00"),
            current_ac=Decimal("480000.00"),
            current_ev=Decimal("450000.00"),
            current_cpi=Decimal("0.9375"),
            predicted_eac=Decimal("1066667.00"),
            predicted_eac_confidence=Decimal("75.00"),
            prediction_method="AI_GLM5",
            overrun_probability=Decimal("65.00"),
            expected_overrun_amount=Decimal("66667.00"),
            overrun_percentage=Decimal("6.67"),
            risk_level="MEDIUM",
            risk_score=Decimal("65.00"),
            cost_trend="DECLINING",
            model_version="GLM-4-Plus",
            data_quality_score=Decimal("85.00")
        )
        
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        assert prediction.id is not None
        assert prediction.project_code == "TEST-COST-001"
        assert prediction.predicted_eac == Decimal("1066667.00")
        assert prediction.risk_level == "MEDIUM"
    
    def test_prediction_relationships(self, db: Session, test_project: Project, test_evm_data: EarnedValueData):
        """测试预测记录的关系"""
        prediction = CostPrediction(
            project_id=test_project.id,
            project_code=test_project.project_code,
            prediction_date=date.today(),
            prediction_version="V1.0",
            evm_data_id=test_evm_data.id,
            predicted_eac=Decimal("1066667.00")
        )
        
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        # 验证关系
        assert prediction.project is not None
        assert prediction.project.id == test_project.id
        assert prediction.evm_data is not None
        assert prediction.evm_data.id == test_evm_data.id


class TestOptimizationSuggestionModel:
    """优化建议模型测试"""
    
    def test_create_suggestion(self, db: Session, test_project: Project, test_evm_data: EarnedValueData):
        """测试创建优化建议"""
        # 先创建预测
        prediction = CostPrediction(
            project_id=test_project.id,
            project_code=test_project.project_code,
            prediction_date=date.today(),
            prediction_version="V1.0",
            predicted_eac=Decimal("1066667.00")
        )
        db.add(prediction)
        db.commit()
        
        # 创建建议
        suggestion = CostOptimizationSuggestion(
            prediction_id=prediction.id,
            project_id=test_project.id,
            project_code=test_project.project_code,
            suggestion_code="OPT-TEST-COST-001-202602-001",
            suggestion_title="优化供应商采购",
            suggestion_type="VENDOR_NEGOTIATION",
            priority="HIGH",
            description="与主要供应商重新谈判，降低材料采购成本",
            estimated_cost_saving=Decimal("50000.00"),
            implementation_cost=Decimal("5000.00"),
            net_benefit=Decimal("45000.00"),
            roi_percentage=Decimal("900.00"),
            impact_on_schedule="NEUTRAL",
            impact_on_quality="NEUTRAL",
            implementation_risk="LOW",
            ai_confidence_score=Decimal("82.00"),
            status="PENDING"
        )
        
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)
        
        assert suggestion.id is not None
        assert suggestion.suggestion_code == "OPT-TEST-COST-001-202602-001"
        assert suggestion.net_benefit == Decimal("45000.00")
        assert suggestion.status == "PENDING"
    
    def test_suggestion_workflow(self, db: Session, test_project: Project):
        """测试建议的工作流程"""
        # 创建预测
        prediction = CostPrediction(
            project_id=test_project.id,
            project_code=test_project.project_code,
            prediction_date=date.today(),
            prediction_version="V1.0",
            predicted_eac=Decimal("1066667.00")
        )
        db.add(prediction)
        db.commit()
        
        # 创建建议
        suggestion = CostOptimizationSuggestion(
            prediction_id=prediction.id,
            project_id=test_project.id,
            project_code=test_project.project_code,
            suggestion_code="OPT-TEST-002",
            suggestion_title="流程优化",
            suggestion_type="PROCESS_IMPROVEMENT",
            priority="MEDIUM",
            description="优化生产流程",
            estimated_cost_saving=Decimal("30000.00"),
            status="PENDING"
        )
        db.add(suggestion)
        db.commit()
        
        # 审批
        suggestion.status = "APPROVED"
        suggestion.review_decision = "APPROVED"
        db.commit()
        
        # 分配
        suggestion.status = "IN_PROGRESS"
        suggestion.start_date = date.today()
        db.commit()
        
        # 完成
        suggestion.status = "COMPLETED"
        suggestion.actual_cost_saving = Decimal("32000.00")
        suggestion.actual_completion_date = date.today()
        suggestion.effectiveness_rating = 5
        db.commit()
        
        assert suggestion.status == "COMPLETED"
        assert suggestion.actual_cost_saving > suggestion.estimated_cost_saving


# ==================== AI服务测试 ====================

class TestGLM5CostPredictor:
    """GLM-5成本预测器测试"""
    
    @patch('app.services.cost_prediction_service.requests.post')
    def test_predict_eac_with_mock(self, mock_post):
        """测试EAC预测（使用mock）"""
        # Mock API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "predicted_eac": 1066667,
                        "confidence": 75,
                        "prediction_method": "AI_GLM5",
                        "eac_lower_bound": 1013334,
                        "eac_upper_bound": 1120000,
                        "eac_most_likely": 1066667,
                        "reasoning": "基于当前CPI=0.9375的趋势分析",
                        "key_assumptions": ["CPI维持当前水平"],
                        "uncertainty_factors": ["市场波动"]
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # 创建预测器
        predictor = GLM5CostPredictor(api_key="test-key")
        
        # 准备测试数据
        project_data = {
            'project_code': 'TEST-001',
            'bac': 1000000,
            'current_cpi': 0.9375,
            'current_ac': 480000,
            'current_ev': 450000
        }
        evm_history = []
        
        # 执行预测
        result = predictor.predict_eac(project_data, evm_history)
        
        assert result['predicted_eac'] == 1066667
        assert result['confidence'] == 75
        assert 'reasoning' in result
    
    @patch('app.services.cost_prediction_service.requests.post')
    def test_analyze_cost_risks_with_mock(self, mock_post):
        """测试成本风险分析（使用mock）"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "overrun_probability": 65,
                        "risk_level": "MEDIUM",
                        "risk_score": 65,
                        "risk_factors": [
                            {
                                "factor": "CPI下降",
                                "impact": "HIGH",
                                "weight": 0.4,
                                "description": "成本绩效持续恶化"
                            }
                        ],
                        "cost_trend": "DECLINING",
                        "key_concerns": ["成本控制不力"],
                        "early_warning_signals": ["CPI低于0.95"]
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        predictor = GLM5CostPredictor(api_key="test-key")
        
        project_data = {'project_code': 'TEST-001', 'bac': 1000000}
        evm_history = []
        current_evm = {'cpi': 0.9375, 'ac': 480000}
        
        result = predictor.analyze_cost_risks(project_data, evm_history, current_evm)
        
        assert result['risk_level'] == "MEDIUM"
        assert result['overrun_probability'] == 65
        assert len(result['risk_factors']) > 0


class TestCostPredictionService:
    """成本预测服务测试"""
    
    def test_traditional_eac_prediction(self, db: Session, test_project: Project, test_evm_data: EarnedValueData):
        """测试传统EAC预测方法"""
        service = CostPredictionService(db)
        result = service._traditional_eac_prediction(test_evm_data)
        
        # 验证结果
        assert 'predicted_eac' in result
        assert 'confidence' in result
        assert result['predicted_eac'] > 0
        
        # 验证CPI方法计算
        # EAC = AC + (BAC - EV) / CPI
        # = 480000 + (1000000 - 450000) / 0.9375
        # = 480000 + 586666.67 = 1066666.67
        assert abs(result['predicted_eac'] - 1066666.67) < 1
    
    def test_traditional_risk_analysis(self, db: Session, test_project: Project, test_evm_data: EarnedValueData, test_evm_history: list):
        """测试传统风险分析"""
        service = CostPredictionService(db)
        result = service._traditional_risk_analysis(test_evm_data, test_evm_history)
        
        assert 'risk_level' in result
        assert 'overrun_probability' in result
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        # CPI=0.9375应该是MEDIUM风险
        assert result['risk_level'] == 'MEDIUM'
    
    @patch('app.services.cost_prediction_service.GLM5CostPredictor')
    def test_create_prediction_with_ai(self, mock_predictor_class, db: Session, test_project: Project, test_evm_data: EarnedValueData, test_evm_history: list):
        """测试使用AI创建预测"""
        # Mock AI预测器
        mock_predictor = Mock()
        mock_predictor.predict_eac.return_value = {
            'predicted_eac': 1066667,
            'confidence': 75,
            'eac_lower_bound': 1013334,
            'eac_upper_bound': 1120000,
            'eac_most_likely': 1066667,
            'reasoning': 'AI分析结果',
            'key_assumptions': [],
            'uncertainty_factors': []
        }
        mock_predictor.analyze_cost_risks.return_value = {
            'overrun_probability': 65,
            'risk_level': 'MEDIUM',
            'risk_score': 65,
            'risk_factors': [],
            'cost_trend': 'DECLINING',
            'trend_analysis': 'CPI下降',
            'key_concerns': [],
            'early_warning_signals': []
        }
        mock_predictor_class.return_value = mock_predictor
        
        # 创建预测
        service = CostPredictionService(db, glm_api_key="test-key")
        service.ai_predictor = mock_predictor
        
        prediction = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=True,
            created_by=1
        )
        
        assert prediction.id is not None
        assert prediction.predicted_eac == Decimal("1066667.00")
        assert prediction.risk_level == "MEDIUM"
        assert prediction.prediction_method == "AI_GLM5"
    
    def test_create_prediction_without_ai(self, db: Session, test_project: Project, test_evm_data: EarnedValueData, test_evm_history: list):
        """测试不使用AI创建预测"""
        service = CostPredictionService(db)
        
        prediction = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=False,
            created_by=1
        )
        
        assert prediction.id is not None
        assert prediction.predicted_eac > 0
        assert prediction.prediction_method == "CPI_BASED"
    
    def test_get_latest_prediction(self, db: Session, test_project: Project, test_evm_data: EarnedValueData):
        """测试获取最新预测"""
        service = CostPredictionService(db)
        
        # 创建两个预测
        pred1 = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=False
        )
        
        pred2 = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V2.0",
            use_ai=False
        )
        
        # 获取最新
        latest = service.get_latest_prediction(test_project.id)
        
        assert latest.id == pred2.id
        assert latest.prediction_version == "V2.0"


# ==================== API端点测试 ====================

class TestCostPredictionAPI:
    """成本预测API测试"""
    
    def test_create_prediction_api(self, client: TestClient, test_project: Project, test_evm_data: EarnedValueData, auth_headers: dict):
        """测试创建预测API"""
        response = client.post(
            "/api/v1/projects/costs/predictions",
            json={
                "project_id": test_project.id,
                "prediction_version": "V1.0",
                "use_ai": False,
                "notes": "测试预测"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['project_id'] == test_project.id
        assert 'predicted_eac' in data
    
    def test_get_prediction_detail_api(self, client: TestClient, db: Session, test_project: Project, test_evm_data: EarnedValueData, auth_headers: dict):
        """测试获取预测详情API"""
        # 先创建预测
        service = CostPredictionService(db)
        prediction = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=False
        )
        
        # 获取详情
        response = client.get(
            f"/api/v1/projects/costs/predictions/{prediction.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == prediction.id
    
    def test_get_latest_prediction_api(self, client: TestClient, db: Session, test_project: Project, test_evm_data: EarnedValueData, auth_headers: dict):
        """测试获取最新预测API"""
        # 创建预测
        service = CostPredictionService(db)
        prediction = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=False
        )
        
        response = client.get(
            f"/api/v1/projects/costs/predictions/project/{test_project.id}/latest",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == prediction.id
    
    def test_approve_prediction_api(self, client: TestClient, db: Session, test_project: Project, test_evm_data: EarnedValueData, auth_headers: dict):
        """测试审批预测API"""
        # 创建预测
        service = CostPredictionService(db)
        prediction = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=False
        )
        
        # 审批
        response = client.post(
            f"/api/v1/projects/costs/predictions/{prediction.id}/approve",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_approved'] is True
    
    def test_get_project_cost_health_api(self, client: TestClient, db: Session, test_project: Project, test_evm_data: EarnedValueData, auth_headers: dict):
        """测试获取项目成本健康度API"""
        # 创建预测
        service = CostPredictionService(db)
        prediction = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=False
        )
        
        response = client.get(
            f"/api/v1/projects/costs/projects/{test_project.id}/cost-health",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'health_score' in data
        assert 'risk_level' in data
        assert 'recommendation' in data


class TestOptimizationSuggestionAPI:
    """优化建议API测试"""
    
    def test_get_suggestions_api(self, client: TestClient, db: Session, test_project: Project, test_evm_data: EarnedValueData, auth_headers: dict):
        """测试获取优化建议列表API"""
        # 创建预测
        prediction = CostPrediction(
            project_id=test_project.id,
            project_code=test_project.project_code,
            prediction_date=date.today(),
            prediction_version="V1.0",
            predicted_eac=Decimal("1066667.00")
        )
        db.add(prediction)
        db.commit()
        
        # 创建建议
        suggestion = CostOptimizationSuggestion(
            prediction_id=prediction.id,
            project_id=test_project.id,
            project_code=test_project.project_code,
            suggestion_code="OPT-TEST-001",
            suggestion_title="优化测试",
            suggestion_type="PROCESS_IMPROVEMENT",
            priority="HIGH",
            description="测试建议",
            estimated_cost_saving=Decimal("50000.00")
        )
        db.add(suggestion)
        db.commit()
        
        # 获取列表
        response = client.get(
            f"/api/v1/projects/costs/predictions/{prediction.id}/suggestions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]['suggestion_code'] == "OPT-TEST-001"
    
    def test_review_suggestion_api(self, client: TestClient, db: Session, test_project: Project, auth_headers: dict):
        """测试审核建议API"""
        # 创建预测和建议
        prediction = CostPrediction(
            project_id=test_project.id,
            project_code=test_project.project_code,
            prediction_date=date.today(),
            prediction_version="V1.0",
            predicted_eac=Decimal("1066667.00")
        )
        db.add(prediction)
        db.commit()
        
        suggestion = CostOptimizationSuggestion(
            prediction_id=prediction.id,
            project_id=test_project.id,
            project_code=test_project.project_code,
            suggestion_code="OPT-TEST-002",
            suggestion_title="测试建议",
            suggestion_type="VENDOR_NEGOTIATION",
            priority="HIGH",
            description="测试",
            estimated_cost_saving=Decimal("30000.00")
        )
        db.add(suggestion)
        db.commit()
        
        # 审核
        response = client.post(
            f"/api/v1/projects/costs/suggestions/{suggestion.id}/review",
            json={
                "decision": "APPROVED",
                "comments": "同意实施"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['review_decision'] == "APPROVED"
        assert data['status'] == "APPROVED"


# ==================== 边界条件和异常测试 ====================

class TestEdgeCases:
    """边界条件测试"""
    
    def test_prediction_without_evm_data(self, db: Session):
        """测试没有EVM数据时创建预测"""
        # 创建没有EVM数据的项目
        project = Project(
            project_code="TEST-NO-EVM",
            project_name="无EVM数据项目",
            budget_amount=Decimal("1000000.00")
        )
        db.add(project)
        db.commit()
        
        service = CostPredictionService(db)
        
        with pytest.raises(ValueError, match="项目无EVM数据"):
            service.create_prediction(
                project_id=project.id,
                prediction_version="V1.0",
                use_ai=False
            )
    
    def test_prediction_with_zero_cpi(self, db: Session, test_project: Project):
        """测试CPI为0时的预测"""
        # 创建CPI为0的EVM数据
        evm = EarnedValueData(
            project_id=test_project.id,
            project_code=test_project.project_code,
            period_type="MONTH",
            period_date=date.today(),
            period_label="2026-02",
            planned_value=Decimal("500000.00"),
            earned_value=Decimal("0.00"),
            actual_cost=Decimal("480000.00"),
            budget_at_completion=Decimal("1000000.00"),
            cost_performance_index=Decimal("0.00"),
            is_verified=True
        )
        db.add(evm)
        db.commit()
        
        service = CostPredictionService(db)
        
        # 应该使用备用方法
        prediction = service.create_prediction(
            project_id=test_project.id,
            prediction_version="V1.0",
            use_ai=False
        )
        
        assert prediction.predicted_eac > 0
    
    def test_data_quality_calculation(self, db: Session, test_project: Project):
        """测试数据质量评分计算"""
        service = CostPredictionService(db)
        
        # 测试空历史
        score = service._calculate_data_quality([])
        assert score == Decimal("70.00")  # 100 - 30 (少于3条)
        
        # 测试部分未验证数据
        evm1 = EarnedValueData(
            project_id=test_project.id,
            project_code=test_project.project_code,
            period_date=date.today(),
            is_verified=True
        )
        evm2 = EarnedValueData(
            project_id=test_project.id,
            project_code=test_project.project_code,
            period_date=date.today() - timedelta(days=30),
            is_verified=False
        )
        
        score = service._calculate_data_quality([evm1, evm2])
        assert score == Decimal("80.00")  # 100 - 15 (少于6条) - 5 (一条未验证)
