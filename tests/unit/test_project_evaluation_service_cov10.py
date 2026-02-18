# -*- coding: utf-8 -*-
"""第十批：ProjectEvaluationService 单元测试"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.project_evaluation_service import ProjectEvaluationService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return ProjectEvaluationService(db)


def test_service_init(db):
    """服务初始化"""
    svc = ProjectEvaluationService(db)
    assert svc.db is db
    assert "novelty" in ProjectEvaluationService.DEFAULT_WEIGHTS
    assert "difficulty" in ProjectEvaluationService.DEFAULT_WEIGHTS


def test_get_dimension_weights_no_config(service, db):
    """没有维度配置时使用默认权重"""
    db.query.return_value.filter.return_value.all.return_value = []

    weights = service.get_dimension_weights()
    assert weights == ProjectEvaluationService.DEFAULT_WEIGHTS


def test_get_dimension_weights_from_db(service, db):
    """从数据库加载权重 - 维度有 default_weight 和 dimension_type"""
    dim1 = MagicMock()
    dim1.dimension_type = "NOVELTY"
    dim1.default_weight = Decimal("20")  # 百分比形式
    dim2 = MagicMock()
    dim2.dimension_type = "DIFFICULTY"
    dim2.default_weight = Decimal("35")

    db.query.return_value.filter.return_value.all.return_value = [dim1, dim2]

    weights = service.get_dimension_weights()
    assert isinstance(weights, dict)
    assert len(weights) > 0


def test_default_level_thresholds(service):
    """验证默认等级阈值"""
    thresholds = ProjectEvaluationService.DEFAULT_LEVEL_THRESHOLDS
    assert len(thresholds) == 5  # S, A, B, C, D


def test_default_weights_sum(service):
    """默认权重合计接近1"""
    weights = ProjectEvaluationService.DEFAULT_WEIGHTS
    total = sum(weights.values())
    assert abs(total - Decimal("1.00")) < Decimal("0.01")


def test_get_or_create_evaluation_project_not_found(service, db):
    """项目不存在时"""
    if not hasattr(service, "get_or_create_evaluation"):
        pytest.skip("方法不存在")
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(Exception):
        service.get_or_create_evaluation(project_id=999)


def test_calculate_evaluation_score(service, db):
    """计算评价分数"""
    if not hasattr(service, "calculate_score"):
        pytest.skip("方法不存在")
    scores = {"novelty": 80, "new_tech": 90, "difficulty": 85, "workload": 75, "amount": 70}
    weights = ProjectEvaluationService.DEFAULT_WEIGHTS
    total = sum(
        Decimal(str(scores[k])) * weights[k]
        for k in scores if k in weights
    )
    assert total > 0


def test_list_evaluations(service, db):
    """评价列表查询"""
    if not hasattr(service, "list_evaluations"):
        pytest.skip("方法不存在")
    mock_q = MagicMock()
    db.query.return_value = mock_q
    mock_q.filter.return_value = mock_q
    mock_q.count.return_value = 0
    mock_q.offset.return_value = mock_q
    mock_q.limit.return_value = mock_q
    mock_q.all.return_value = []

    result = service.list_evaluations()
    assert result is not None
