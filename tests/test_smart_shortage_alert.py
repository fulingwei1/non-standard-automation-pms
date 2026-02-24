# -*- coding: utf-8 -*-
"""
智能缺料预警系统 - 测试用例

Team 3: 智能缺料预警系统
28+测试用例，覆盖率 ≥ 80%
"""
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy.orm import Session

try:
    from app.models.shortage.smart_alert import (
        ShortageAlert,
        ShortageHandlingPlan,
        MaterialDemandForecast
    )
except ImportError:
    pytest.skip("Shortage smart alert models not available", allow_module_level=True)

try:
    from app.models.material import Material
    from app.models.project import Project
    from app.models.production.work_order import WorkOrder
    from app.models.inventory import Inventory
    from app.services.shortage.smart_alert_engine import SmartAlertEngine
    from app.services.shortage.demand_forecast_engine import DemandForecastEngine
except ImportError as e:
    pytest.skip(f"Shortage alert dependencies not available: {e}", allow_module_level=True)


class TestSmartAlertEngine:
    """智能预警引擎测试"""
    
    def test_calculate_alert_level_urgent(self, db: Session):
        """测试预警级别计算 - URGENT"""
        engine = SmartAlertEngine(db)
        
        level = engine.calculate_alert_level(
            shortage_qty=Decimal('100'),
            required_qty=Decimal('100'),
            days_to_shortage=0,
            is_critical_path=False
        )
        
        assert level == 'URGENT'
    
    def test_calculate_alert_level_critical(self, db: Session):
        """测试预警级别计算 - CRITICAL"""
        engine = SmartAlertEngine(db)
        
        level = engine.calculate_alert_level(
            shortage_qty=Decimal('60'),
            required_qty=Decimal('100'),
            days_to_shortage=5,
            is_critical_path=False
        )
        
        assert level == 'CRITICAL'
    
    def test_calculate_alert_level_warning(self, db: Session):
        """测试预警级别计算 - WARNING"""
        engine = SmartAlertEngine(db)
        
        level = engine.calculate_alert_level(
            shortage_qty=Decimal('40'),
            required_qty=Decimal('100'),
            days_to_shortage=10,
            is_critical_path=False
        )
        
        assert level == 'WARNING'
    
    def test_calculate_alert_level_info(self, db: Session):
        """测试预警级别计算 - INFO"""
        engine = SmartAlertEngine(db)
        
        level = engine.calculate_alert_level(
            shortage_qty=Decimal('20'),
            required_qty=Decimal('100'),
            days_to_shortage=30,
            is_critical_path=False
        )
        
        assert level == 'INFO'
    
    def test_calculate_alert_level_critical_path(self, db: Session):
        """测试关键路径物料预警级别提升"""
        engine = SmartAlertEngine(db)
        
        level = engine.calculate_alert_level(
            shortage_qty=Decimal('40'),
            required_qty=Decimal('100'),
            days_to_shortage=5,
            is_critical_path=True
        )
        
        # 关键路径应该提升预警级别
        assert level in ['URGENT', 'CRITICAL']
    
    def test_predict_impact(self, db: Session, test_material, test_project):
        """测试影响预测"""
        engine = SmartAlertEngine(db)
        
        impact = engine.predict_impact(
            material_id=test_material.id,
            shortage_qty=Decimal('100'),
            required_date=datetime.now().date() + timedelta(days=7),
            project_id=test_project.id
        )
        
        assert 'estimated_delay_days' in impact
        assert 'estimated_cost_impact' in impact
        assert 'affected_projects' in impact
        assert 'risk_score' in impact
        assert impact['risk_score'] >= 0
        assert impact['risk_score'] <= 100
    
    def test_generate_alert_no(self, db: Session):
        """测试预警单号生成"""
        engine = SmartAlertEngine(db)
        
        alert_no = engine._generate_alert_no()
        
        assert alert_no.startswith('SA')
        assert len(alert_no) >= 12  # SA + YYYYMMDD + 序号
    
    def test_calculate_risk_score(self, db: Session):
        """测试风险评分计算"""
        engine = SmartAlertEngine(db)
        
        score = engine._calculate_risk_score(
            delay_days=15,
            cost_impact=Decimal('50000'),
            project_count=3,
            shortage_qty=Decimal('100')
        )
        
        assert score >= 0
        assert score <= 100
    
    def test_generate_urgent_purchase_plan(self, db: Session, test_alert):
        """测试生成紧急采购方案"""
        engine = SmartAlertEngine(db)
        
        plan = engine._generate_urgent_purchase_plan(test_alert)
        
        assert plan is not None
        assert plan.solution_type == 'URGENT_PURCHASE'
        assert plan.proposed_qty == test_alert.shortage_qty
    
    def test_generate_partial_delivery_plan(self, db: Session, test_alert):
        """测试生成分批交付方案"""
        engine = SmartAlertEngine(db)
        
        # 设置有可用库存
        test_alert.available_qty = Decimal('50')
        
        plan = engine._generate_partial_delivery_plan(test_alert)
        
        assert plan is not None
        assert plan.solution_type == 'PARTIAL_DELIVERY'
        assert plan.proposed_qty == test_alert.available_qty
    
    def test_generate_reschedule_plan(self, db: Session, test_alert):
        """测试生成重排期方案"""
        engine = SmartAlertEngine(db)
        
        plan = engine._generate_reschedule_plan(test_alert)
        
        assert plan is not None
        assert plan.solution_type == 'RESCHEDULE'
    
    def test_score_solution_feasibility(self, db: Session, test_alert):
        """测试方案可行性评分"""
        engine = SmartAlertEngine(db)
        
        plan = ShortageHandlingPlan(
            alert_id=test_alert.id,
            solution_type='URGENT_PURCHASE',
            plan_no='TEST001'
        )
        
        score = engine._score_feasibility(plan)
        
        assert score > 0
        assert score <= 100
    
    def test_score_solution_cost(self, db: Session, test_alert):
        """测试方案成本评分"""
        engine = SmartAlertEngine(db)
        
        plan = ShortageHandlingPlan(
            alert_id=test_alert.id,
            solution_type='RESCHEDULE',
            plan_no='TEST002',
            estimated_cost=Decimal('0')
        )
        
        score = engine._score_cost(plan, test_alert)
        
        assert score == 100  # 零成本应该满分
    
    def test_score_solution_time(self, db: Session, test_alert):
        """测试方案时间评分"""
        engine = SmartAlertEngine(db)
        
        plan = ShortageHandlingPlan(
            alert_id=test_alert.id,
            solution_type='PARTIAL_DELIVERY',
            plan_no='TEST003',
            estimated_lead_time=0
        )
        
        score = engine._score_time(plan, test_alert)
        
        assert score == 100  # 零交期应该满分
    
    def test_score_solution_risk(self, db: Session, test_alert):
        """测试方案风险评分"""
        engine = SmartAlertEngine(db)
        
        plan = ShortageHandlingPlan(
            alert_id=test_alert.id,
            solution_type='URGENT_PURCHASE',
            plan_no='TEST004',
            risks=[]
        )
        
        score = engine._score_risk(plan)
        
        assert score == 100  # 无风险应该满分


class TestDemandForecastEngine:
    """需求预测引擎测试"""
    
    def test_calculate_average(self, db: Session):
        """测试平均值计算"""
        engine = DemandForecastEngine(db)
        
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        avg = engine._calculate_average(data)
        
        assert avg == Decimal('20')
    
    def test_calculate_std(self, db: Session):
        """测试标准差计算"""
        engine = DemandForecastEngine(db)
        
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        std = engine._calculate_std(data)
        
        assert std > 0
    
    def test_detect_seasonality(self, db: Session):
        """测试季节性检测"""
        engine = DemandForecastEngine(db)
        
        # 模拟季节性数据（前期低后期高）
        data = [Decimal('10')] * 7 + [Decimal('20')] * 7
        factor = engine._detect_seasonality(data)
        
        assert factor > Decimal('1.0')  # 上升趋势
        assert factor <= Decimal('2.0')  # 限制在合理范围
    
    def test_moving_average_forecast(self, db: Session):
        """测试移动平均预测"""
        engine = DemandForecastEngine(db)
        
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        forecast = engine._moving_average_forecast(data, window=3)
        
        # 最近3个的平均值 (20+30+40)/3 = 30
        assert forecast == Decimal('30')
    
    def test_exponential_smoothing_forecast(self, db: Session):
        """测试指数平滑预测"""
        engine = DemandForecastEngine(db)
        
        data = [Decimal('10'), Decimal('20'), Decimal('30')]
        forecast = engine._exponential_smoothing_forecast(data)
        
        assert forecast > Decimal('10')
        assert forecast <= Decimal('30')
    
    def test_linear_regression_forecast(self, db: Session):
        """测试线性回归预测"""
        engine = DemandForecastEngine(db)
        
        # 线性增长数据
        data = [Decimal('10'), Decimal('20'), Decimal('30'), Decimal('40')]
        forecast = engine._linear_regression_forecast(data)
        
        # 预测下一个应该接近50
        assert forecast >= Decimal('40')
        assert forecast <= Decimal('60')
    
    def test_calculate_confidence_interval(self, db: Session):
        """测试置信区间计算"""
        engine = DemandForecastEngine(db)
        
        forecast = Decimal('100')
        std = Decimal('10')
        
        lower, upper = engine._calculate_confidence_interval(
            forecast=forecast,
            std=std,
            confidence=95.0
        )
        
        assert lower < forecast
        assert upper > forecast
        assert upper - lower > Decimal('0')
    
    def test_generate_forecast_no(self, db: Session):
        """测试预测编号生成"""
        engine = DemandForecastEngine(db)
        
        forecast_no = engine._generate_forecast_no()
        
        assert forecast_no.startswith('FC')
        assert len(forecast_no) >= 12
    
    def test_validate_forecast_accuracy(
        self,
        db: Session,
        test_material,
        test_forecast
    ):
        """测试预测准确率验证"""
        engine = DemandForecastEngine(db)
        
        actual_demand = Decimal('110')
        
        result = engine.validate_forecast_accuracy(
            forecast_id=test_forecast.id,
            actual_demand=actual_demand
        )
        
        assert 'forecast_id' in result
        assert 'accuracy_score' in result
        assert 'mae' in result
        assert 'rmse' in result
        assert 'mape' in result
        assert result['accuracy_score'] >= 0
        assert result['accuracy_score'] <= 100


class TestShortageAlertAPI:
    """智能预警API测试"""
    
    @pytest.mark.asyncio
    async def test_get_shortage_alerts(self, client, auth_headers):
        """测试获取预警列表"""
        response = await client.get(
            "/api/v1/shortage/smart/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'items' in data
    
    @pytest.mark.asyncio
    async def test_get_alert_detail(self, client, auth_headers, test_alert):
        """测试获取预警详情"""
        response = await client.get(
            f"/api/v1/shortage/smart/alerts/{test_alert.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == test_alert.id
        assert data['alert_no'] == test_alert.alert_no
    
    @pytest.mark.asyncio
    async def test_trigger_scan(self, client, auth_headers):
        """测试触发扫描"""
        response = await client.post(
            "/api/v1/shortage/smart/scan",
            headers=auth_headers,
            json={
                "days_ahead": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'scanned_at' in data
        assert 'alerts_generated' in data
    
    @pytest.mark.asyncio
    async def test_get_handling_solutions(self, client, auth_headers, test_alert):
        """测试获取处理方案"""
        response = await client.get(
            f"/api/v1/shortage/smart/alerts/{test_alert.id}/solutions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'alert_id' in data
        assert 'items' in data
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, client, auth_headers, test_alert):
        """测试解决预警"""
        response = await client.post(
            f"/api/v1/shortage/smart/alerts/{test_alert.id}/resolve",
            headers=auth_headers,
            json={
                "resolution_type": "PURCHASE",
                "resolution_note": "已安排采购"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
    
    @pytest.mark.asyncio
    async def test_get_material_forecast(self, client, auth_headers, test_material):
        """测试获取物料预测"""
        response = await client.get(
            f"/api/v1/shortage/smart/forecast/{test_material.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'forecast_no' in data
        assert 'forecasted_demand' in data
    
    @pytest.mark.asyncio
    async def test_get_shortage_trend(self, client, auth_headers):
        """测试缺料趋势分析"""
        response = await client.get(
            "/api/v1/shortage/smart/analysis/trend?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_alerts' in data
        assert 'by_level' in data
        assert 'trend_data' in data
    
    @pytest.mark.asyncio
    async def test_get_root_cause(self, client, auth_headers):
        """测试根因分析"""
        response = await client.get(
            "/api/v1/shortage/smart/analysis/root-cause?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_analyzed' in data
        assert 'top_causes' in data
        assert 'recommendations' in data
    
    @pytest.mark.asyncio
    async def test_get_project_impact(self, client, auth_headers):
        """测试项目影响分析"""
        response = await client.get(
            "/api/v1/shortage/smart/impact/projects",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_projects' in data
        assert 'items' in data
    
    @pytest.mark.asyncio
    async def test_subscribe_notifications(self, client, auth_headers):
        """测试订阅通知"""
        response = await client.post(
            "/api/v1/shortage/smart/notifications/subscribe",
            headers=auth_headers,
            json={
                "alert_levels": ["URGENT", "CRITICAL"],
                "notification_channels": ["EMAIL"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'subscription_id' in data
        assert data['alert_levels'] == ["URGENT", "CRITICAL"]


# ==================== Fixtures ====================

@pytest.fixture
def test_material(db: Session):
    """测试物料"""
    material = Material(
        material_code='MAT001',
        material_name='测试物料',
        standard_price=Decimal('100')
    )
    db.add(material)
    db.commit()
    return material


@pytest.fixture
def test_project(db: Session):
    """测试项目"""
    project = Project(
        project_no='PRJ001',
        project_name='测试项目'
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def test_alert(db: Session, test_material, test_project):
    """测试预警"""
    alert = ShortageAlert(
        alert_no='SA20260216001',
        project_id=test_project.id,
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        required_qty=Decimal('100'),
        available_qty=Decimal('20'),
        shortage_qty=Decimal('80'),
        alert_level='WARNING',
        alert_date=datetime.now().date(),
        required_date=datetime.now().date() + timedelta(days=7),
        estimated_cost_impact=Decimal('8000'),
        status='PENDING'
    )
    db.add(alert)
    db.commit()
    return alert


@pytest.fixture
def test_forecast(db: Session, test_material):
    """测试预测"""
    forecast = MaterialDemandForecast(
        forecast_no='FC20260216001',
        material_id=test_material.id,
        forecast_start_date=datetime.now().date(),
        forecast_end_date=datetime.now().date() + timedelta(days=30),
        forecast_horizon_days=30,
        algorithm='EXP_SMOOTHING',
        forecasted_demand=Decimal('100'),
        lower_bound=Decimal('80'),
        upper_bound=Decimal('120'),
        confidence_interval=Decimal('95'),
        status='ACTIVE'
    )
    db.add(forecast)
    db.commit()
    return forecast
