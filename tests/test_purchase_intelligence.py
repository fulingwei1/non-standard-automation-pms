# -*- coding: utf-8 -*-
"""
智能采购管理系统测试

测试覆盖:
1. 数据模型测试
2. 采购建议引擎测试
3. 供应商绩效评估测试
4. API接口测试
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import (
    Material,
    MaterialCategory,
    MaterialShortage,
    MaterialSupplier,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseSuggestion,
    SupplierPerformance,
    SupplierQuotation,
    User,
    Vendor,
    GoodsReceipt,
    GoodsReceiptItem,
    Project,
)
from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine
from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator


# ==================== Fixtures ====================

@pytest.fixture
def test_db(db_session):
    """测试数据库会话"""
    return db_session


@pytest.fixture
def test_user(test_db):
    """测试用户"""
    user = User(
        username="test_purchase_user",
        email="purchase@test.com",
        password_hash="test",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_project(test_db):
    """测试项目"""
    project = Project(
        project_no="TEST-PROJ-001",
        project_name="测试项目",
        status="PLANNING",
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project


@pytest.fixture
def test_supplier(test_db):
    """测试供应商"""
    supplier = Vendor(
        supplier_code="SUP001",
        supplier_name="测试供应商A",
        vendor_type="MATERIAL",
        status="ACTIVE",
        contact_person="张三",
        contact_phone="13800138000",
    )
    test_db.add(supplier)
    test_db.commit()
    test_db.refresh(supplier)
    return supplier


@pytest.fixture
def test_material(test_db, test_supplier):
    """测试物料"""
    category = MaterialCategory(
        category_code="CAT001",
        category_name="电子元件",
    )
    test_db.add(category)
    test_db.flush()
    
    material = Material(
        material_code="MAT001",
        material_name="测试物料A",
        category_id=category.id,
        unit="个",
        standard_price=Decimal("100.00"),
        last_price=Decimal("95.00"),
        safety_stock=Decimal("100"),
        current_stock=Decimal("50"),
        lead_time_days=7,
        default_supplier_id=test_supplier.id,
        is_active=True,
    )
    test_db.add(material)
    test_db.flush()
    
    # 创建物料-供应商关联
    ms = MaterialSupplier(
        material_id=material.id,
        supplier_id=test_supplier.id,
        price=Decimal("95.00"),
        lead_time_days=7,
        min_order_qty=Decimal("10"),
        is_preferred=True,
        is_active=True,
    )
    test_db.add(ms)
    test_db.commit()
    test_db.refresh(material)
    
    return material


# ==================== 数据模型测试 ====================

def test_purchase_suggestion_model(test_db, test_material, test_supplier):
    """测试采购建议模型"""
    suggestion = PurchaseSuggestion(
        tenant_id=1,
        suggestion_no="PS20260216001",
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        unit=test_material.unit,
        suggested_qty=Decimal("50"),
        current_stock=Decimal("50"),
        safety_stock=Decimal("100"),
        source_type="SAFETY_STOCK",
        urgency_level="NORMAL",
        suggested_supplier_id=test_supplier.id,
        estimated_unit_price=Decimal("95.00"),
        estimated_total_amount=Decimal("4750.00"),
        status="PENDING",
    )
    
    test_db.add(suggestion)
    test_db.commit()
    
    # 验证
    assert suggestion.id is not None
    assert suggestion.suggestion_no == "PS20260216001"
    assert suggestion.material_id == test_material.id
    assert suggestion.suggested_qty == Decimal("50")


def test_supplier_quotation_model(test_db, test_material, test_supplier):
    """测试供应商报价模型"""
    quotation = SupplierQuotation(
        tenant_id=1,
        quotation_no="QT20260216001",
        supplier_id=test_supplier.id,
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        unit_price=Decimal("92.00"),
        currency="CNY",
        min_order_qty=Decimal("10"),
        lead_time_days=7,
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=90),
        status="ACTIVE",
    )
    
    test_db.add(quotation)
    test_db.commit()
    
    # 验证
    assert quotation.id is not None
    assert quotation.quotation_no == "QT20260216001"
    assert quotation.unit_price == Decimal("92.00")


def test_supplier_performance_model(test_db, test_supplier):
    """测试供应商绩效模型"""
    performance = SupplierPerformance(
        tenant_id=1,
        supplier_id=test_supplier.id,
        supplier_code=test_supplier.supplier_code,
        supplier_name=test_supplier.supplier_name,
        evaluation_period="2026-01",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        total_orders=10,
        total_amount=Decimal("50000.00"),
        on_time_delivery_rate=Decimal("95.00"),
        on_time_orders=9,
        late_orders=1,
        quality_pass_rate=Decimal("98.50"),
        price_competitiveness=Decimal("85.00"),
        response_speed_score=Decimal("90.00"),
        overall_score=Decimal("92.13"),
        rating="A+",
        status="CALCULATED",
    )
    
    test_db.add(performance)
    test_db.commit()
    
    # 验证
    assert performance.id is not None
    assert performance.overall_score == Decimal("92.13")
    assert performance.rating == "A+"


# ==================== 采购建议引擎测试 ====================

def test_generate_from_safety_stock(test_db, test_material):
    """测试基于安全库存生成建议"""
    engine = PurchaseSuggestionEngine(test_db)
    
    # 当前库存50，安全库存100，应生成建议
    suggestions = engine.generate_from_safety_stock()
    
    assert len(suggestions) > 0
    
    # 验证建议
    suggestion = next((s for s in suggestions if s.material_id == test_material.id), None)
    assert suggestion is not None
    assert suggestion.source_type == "SAFETY_STOCK"
    assert suggestion.suggested_qty > Decimal("0")


def test_generate_from_shortages(test_db, test_material, test_project):
    """测试基于缺料预警生成建议"""
    # 创建缺料记录
    shortage = MaterialShortage(
        project_id=test_project.id,
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        required_qty=Decimal("100"),
        available_qty=Decimal("50"),
        shortage_qty=Decimal("50"),
        required_date=date.today() + timedelta(days=7),
        status="OPEN",
        alert_level="WARNING",
    )
    test_db.add(shortage)
    test_db.commit()
    
    engine = PurchaseSuggestionEngine(test_db)
    suggestions = engine.generate_from_shortages(project_id=test_project.id)
    
    assert len(suggestions) > 0
    suggestion = suggestions[0]
    assert suggestion.source_type == "SHORTAGE"
    assert suggestion.source_id == shortage.id
    assert suggestion.suggested_qty == Decimal("50")


def test_recommend_supplier(test_db, test_material, test_supplier):
    """测试AI推荐供应商"""
    engine = PurchaseSuggestionEngine(test_db)
    
    supplier_id, confidence, reason, alternatives = engine._recommend_supplier(test_material.id)
    
    assert supplier_id == test_supplier.id
    assert confidence is not None
    assert reason is not None
    assert isinstance(reason, dict)


def test_supplier_scoring(test_db, test_material, test_supplier):
    """测试供应商评分算法"""
    engine = PurchaseSuggestionEngine(test_db)
    
    weight_config = {
        'performance': Decimal('40'),
        'price': Decimal('30'),
        'delivery': Decimal('20'),
        'history': Decimal('10'),
    }
    
    scores = engine._calculate_supplier_score(test_supplier.id, test_material.id, weight_config)
    
    assert 'total_score' in scores
    assert 'performance_score' in scores
    assert 'price_score' in scores
    assert scores['total_score'] >= Decimal('0')
    assert scores['total_score'] <= Decimal('100')


# ==================== 供应商绩效评估测试 ====================

def test_evaluate_supplier_basic(test_db, test_supplier):
    """测试基本供应商评估"""
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    evaluation_period = "2026-01"
    performance = evaluator.evaluate_supplier(test_supplier.id, evaluation_period)
    
    # 即使没有订单数据，也应创建记录
    assert performance is not None
    assert performance.supplier_id == test_supplier.id
    assert performance.evaluation_period == evaluation_period


def test_delivery_metrics_calculation(test_db, test_supplier, test_material, test_project):
    """测试准时交货率计算"""
    # 创建测试订单
    order = PurchaseOrder(
        order_no="PO20260201001",
        supplier_id=test_supplier.id,
        project_id=test_project.id,
        order_date=date(2026, 1, 10),
        required_date=date(2026, 1, 20),
        promised_date=date(2026, 1, 20),
        total_amount=Decimal("5000.00"),
        status="COMPLETED",
    )
    test_db.add(order)
    test_db.flush()
    
    # 创建收货记录（延迟2天）
    receipt = GoodsReceipt(
        receipt_no="GR20260122001",
        order_id=order.id,
        supplier_id=test_supplier.id,
        receipt_date=date(2026, 1, 22),  # 延迟2天
        status="COMPLETED",
    )
    test_db.add(receipt)
    test_db.commit()
    
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    orders = [order]
    metrics = evaluator._calculate_delivery_metrics(
        orders,
        date(2026, 1, 1),
        date(2026, 1, 31)
    )
    
    assert metrics['late_orders'] == 1
    assert metrics['avg_delay_days'] == Decimal('2')


def test_quality_metrics_calculation(test_db, test_supplier, test_material, test_project):
    """测试质量合格率计算"""
    # 创建订单
    order = PurchaseOrder(
        order_no="PO20260201002",
        supplier_id=test_supplier.id,
        order_date=date(2026, 1, 10),
        total_amount=Decimal("5000.00"),
        status="COMPLETED",
    )
    test_db.add(order)
    test_db.flush()
    
    # 创建订单明细
    order_item = PurchaseOrderItem(
        order_id=order.id,
        item_no=1,
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        quantity=Decimal("100"),
        unit_price=Decimal("50.00"),
        amount=Decimal("5000.00"),
    )
    test_db.add(order_item)
    test_db.flush()
    
    # 创建收货单
    receipt = GoodsReceipt(
        receipt_no="GR20260122002",
        order_id=order.id,
        supplier_id=test_supplier.id,
        receipt_date=date(2026, 1, 22),
        status="COMPLETED",
    )
    test_db.add(receipt)
    test_db.flush()
    
    # 创建收货明细（98个合格，2个不合格）
    receipt_item = GoodsReceiptItem(
        receipt_id=receipt.id,
        order_item_id=order_item.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        delivery_qty=Decimal("100"),
        received_qty=Decimal("100"),
        qualified_qty=Decimal("98"),
        rejected_qty=Decimal("2"),
    )
    test_db.add(receipt_item)
    test_db.commit()
    
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    orders = [order]
    metrics = evaluator._calculate_quality_metrics(
        orders,
        date(2026, 1, 1),
        date(2026, 1, 31)
    )
    
    assert metrics['pass_rate'] == Decimal('98.00')
    assert metrics['total_qty'] == Decimal('100')
    assert metrics['qualified_qty'] == Decimal('98')
    assert metrics['rejected_qty'] == Decimal('2')


def test_overall_score_calculation(test_db):
    """测试综合评分计算"""
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    delivery_metrics = {
        'on_time_rate': Decimal('95.00'),
        'on_time_orders': 19,
        'late_orders': 1,
        'avg_delay_days': Decimal('1.00'),
    }
    
    quality_metrics = {
        'pass_rate': Decimal('98.50'),
        'total_qty': Decimal('1000'),
        'qualified_qty': Decimal('985'),
        'rejected_qty': Decimal('15'),
    }
    
    price_metrics = {
        'competitiveness': Decimal('85.00'),
        'vs_market': Decimal('-5.00'),
    }
    
    response_metrics = {
        'score': Decimal('90.00'),
        'avg_hours': Decimal('6.00'),
    }
    
    weight_config = {
        'on_time_delivery': Decimal('30'),
        'quality': Decimal('30'),
        'price': Decimal('20'),
        'response': Decimal('20'),
    }
    
    overall_score = evaluator._calculate_overall_score(
        delivery_metrics,
        quality_metrics,
        price_metrics,
        response_metrics,
        weight_config
    )
    
    # 95*0.3 + 98.5*0.3 + 85*0.2 + 90*0.2 = 92.55
    expected = Decimal('92.55')
    assert abs(overall_score - expected) < Decimal('0.01')


def test_rating_determination(test_db):
    """测试评级判定"""
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    assert evaluator._determine_rating(Decimal('95.00')) == 'A+'
    assert evaluator._determine_rating(Decimal('85.00')) == 'A'
    assert evaluator._determine_rating(Decimal('75.00')) == 'B'
    assert evaluator._determine_rating(Decimal('65.00')) == 'C'
    assert evaluator._determine_rating(Decimal('55.00')) == 'D'


def test_batch_evaluate_all_suppliers(test_db, test_supplier):
    """测试批量评估所有供应商"""
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    count = evaluator.batch_evaluate_all_suppliers("2026-01")
    
    assert count > 0


def test_get_supplier_ranking(test_db, test_supplier):
    """测试供应商排名"""
    # 创建绩效记录
    perf1 = SupplierPerformance(
        tenant_id=1,
        supplier_id=test_supplier.id,
        supplier_code=test_supplier.supplier_code,
        supplier_name=test_supplier.supplier_name,
        evaluation_period="2026-01",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        overall_score=Decimal("92.00"),
        rating="A+",
    )
    test_db.add(perf1)
    test_db.commit()
    
    evaluator = SupplierPerformanceEvaluator(test_db)
    rankings = evaluator.get_supplier_ranking("2026-01", limit=10)
    
    assert len(rankings) > 0
    assert rankings[0].supplier_id == test_supplier.id


# ==================== API 接口测试 (使用 TestClient) ====================

def test_api_get_purchase_suggestions(client, test_user, test_material):
    """测试获取采购建议列表 API"""
    # 创建测试建议
    from app.models import PurchaseSuggestion
    suggestion = PurchaseSuggestion(
        tenant_id=1,
        suggestion_no="PS20260216TEST",
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        unit=test_material.unit,
        suggested_qty=Decimal("50"),
        source_type="MANUAL",
        status="PENDING",
    )
    client.db.add(suggestion)
    client.db.commit()
    
    # 调用 API
    response = client.get("/api/v1/purchase/suggestions", headers={"Authorization": f"Bearer {test_user.token}"})
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_approve_suggestion(client, test_user, test_material):
    """测试批准采购建议 API"""
    # 创建测试建议
    from app.models import PurchaseSuggestion
    suggestion = PurchaseSuggestion(
        tenant_id=1,
        suggestion_no="PS20260216APPROVE",
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        unit=test_material.unit,
        suggested_qty=Decimal("50"),
        source_type="MANUAL",
        status="PENDING",
    )
    client.db.add(suggestion)
    client.db.commit()
    
    # 调用 API
    response = client.post(
        f"/api/v1/purchase/suggestions/{suggestion.id}/approve",
        json={"approved": True, "review_note": "批准"},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "采购建议已批准"


def test_api_create_quotation(client, test_user, test_supplier, test_material):
    """测试创建供应商报价 API"""
    quotation_data = {
        "supplier_id": test_supplier.id,
        "material_id": test_material.id,
        "unit_price": 92.00,
        "currency": "CNY",
        "min_order_qty": 10,
        "lead_time_days": 7,
        "valid_from": str(date.today()),
        "valid_to": str(date.today() + timedelta(days=90)),
    }
    
    response = client.post(
        "/api/v1/purchase/quotations",
        json=quotation_data,
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "quotation_no" in data


def test_api_compare_quotations(client, test_user, test_supplier, test_material):
    """测试比价 API"""
    # 创建报价
    quotation = SupplierQuotation(
        tenant_id=1,
        quotation_no="QT20260216COMP",
        supplier_id=test_supplier.id,
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        unit_price=Decimal("92.00"),
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=90),
        status="ACTIVE",
    )
    client.db.add(quotation)
    client.db.commit()
    
    # 调用 API
    response = client.get(
        f"/api/v1/purchase/quotations/compare?material_id={test_material.id}",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "material_id" in data
    assert "quotations" in data


def test_api_evaluate_supplier(client, test_user, test_supplier):
    """测试触发供应商评估 API"""
    eval_data = {
        "supplier_id": test_supplier.id,
        "evaluation_period": "2026-01",
    }
    
    response = client.post(
        f"/api/v1/purchase/suppliers/{test_supplier.id}/evaluate",
        json=eval_data,
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data


def test_api_get_supplier_ranking(client, test_user, test_supplier):
    """测试供应商排名 API"""
    # 创建绩效记录
    perf = SupplierPerformance(
        tenant_id=1,
        supplier_id=test_supplier.id,
        supplier_code=test_supplier.supplier_code,
        supplier_name=test_supplier.supplier_name,
        evaluation_period="2026-01",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        overall_score=Decimal("90.00"),
        rating="A+",
    )
    client.db.add(perf)
    client.db.commit()
    
    # 调用 API
    response = client.get(
        "/api/v1/purchase/suppliers/ranking?evaluation_period=2026-01",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "rankings" in data


# ==================== 边界情况测试 ====================

def test_suggestion_duplicate_prevention(test_db, test_material):
    """测试防止重复建议"""
    engine = PurchaseSuggestionEngine(test_db)
    
    # 第一次生成
    suggestions1 = engine.generate_from_safety_stock()
    count1 = len([s for s in suggestions1 if s.material_id == test_material.id])
    
    # 第二次生成（应跳过已存在的）
    suggestions2 = engine.generate_from_safety_stock()
    count2 = len([s for s in suggestions2 if s.material_id == test_material.id])
    
    assert count2 == 0  # 不应重复创建


def test_performance_without_orders(test_db, test_supplier):
    """测试无订单时的绩效评估"""
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    performance = evaluator.evaluate_supplier(test_supplier.id, "2026-02")
    
    assert performance is not None
    assert performance.total_orders == 0
    assert performance.overall_score == Decimal('0')


def test_invalid_evaluation_period(test_db, test_supplier):
    """测试无效的评估期间"""
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    performance = evaluator.evaluate_supplier(test_supplier.id, "invalid-period")
    
    assert performance is None


# ==================== 性能测试 ====================

def test_batch_suggestion_generation_performance(test_db, test_material):
    """测试批量生成建议的性能"""
    import time
    
    engine = PurchaseSuggestionEngine(test_db)
    
    start_time = time.time()
    suggestions = engine.generate_from_safety_stock()
    end_time = time.time()
    
    elapsed = end_time - start_time
    
    # 应在1秒内完成
    assert elapsed < 1.0
    assert len(suggestions) >= 0


def test_batch_evaluation_performance(test_db):
    """测试批量评估性能"""
    import time
    
    evaluator = SupplierPerformanceEvaluator(test_db)
    
    start_time = time.time()
    count = evaluator.batch_evaluate_all_suppliers("2026-01")
    end_time = time.time()
    
    elapsed = end_time - start_time
    
    # 应在5秒内完成
    assert elapsed < 5.0


# ==================== 集成测试 ====================

def test_full_purchase_workflow(test_db, test_material, test_supplier, test_project, test_user):
    """测试完整采购流程"""
    # 1. 创建缺料
    shortage = MaterialShortage(
        project_id=test_project.id,
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        required_qty=Decimal("100"),
        available_qty=Decimal("0"),
        shortage_qty=Decimal("100"),
        required_date=date.today() + timedelta(days=7),
        status="OPEN",
    )
    test_db.add(shortage)
    test_db.commit()
    
    # 2. 生成采购建议
    engine = PurchaseSuggestionEngine(test_db)
    suggestions = engine.generate_from_shortages(project_id=test_project.id)
    
    assert len(suggestions) > 0
    suggestion = suggestions[0]
    
    # 3. 批准建议
    suggestion.status = "APPROVED"
    suggestion.reviewed_by = test_user.id
    suggestion.reviewed_at = datetime.now()
    test_db.commit()
    
    # 4. 创建报价
    quotation = SupplierQuotation(
        tenant_id=1,
        quotation_no="QT20260216WF",
        supplier_id=test_supplier.id,
        material_id=test_material.id,
        material_code=test_material.material_code,
        material_name=test_material.material_name,
        unit_price=Decimal("95.00"),
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=90),
        status="ACTIVE",
    )
    test_db.add(quotation)
    test_db.commit()
    
    # 5. 创建订单
    order = PurchaseOrder(
        order_no="PO20260216WF",
        supplier_id=test_supplier.id,
        project_id=test_project.id,
        order_date=date.today(),
        total_amount=Decimal("9500.00"),
        status="CONFIRMED",
    )
    test_db.add(order)
    test_db.flush()
    
    # 更新建议状态
    suggestion.purchase_order_id = order.id
    suggestion.status = "ORDERED"
    test_db.commit()
    
    # 6. 评估供应商
    evaluator = SupplierPerformanceEvaluator(test_db)
    performance = evaluator.evaluate_supplier(test_supplier.id, "2026-02")
    
    assert performance is not None
    
    # 验证完整流程
    assert suggestion.status == "ORDERED"
    assert suggestion.purchase_order_id == order.id
    assert quotation.status == "ACTIVE"
    assert performance.supplier_id == test_supplier.id
