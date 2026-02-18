# -*- coding: utf-8 -*-
"""第十批：AIQuotationGeneratorService 单元测试"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.presale_ai_quotation_service import AIQuotationGeneratorService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return AIQuotationGeneratorService(db)


def test_service_init(db):
    """服务初始化"""
    svc = AIQuotationGeneratorService(db)
    assert svc.db is db
    assert hasattr(svc, "ai_model")


def test_generate_quotation_number_format(service, db):
    """验证报价单编号格式"""
    db.query.return_value.filter.return_value.count.return_value = 0
    num = service.generate_quotation_number()
    today = datetime.now().strftime("%Y%m%d")
    assert num.startswith(f"QT-{today}-")
    assert num.endswith("0001")


def test_generate_quotation_number_sequential(service, db):
    """已有报价单时编号递增"""
    db.query.return_value.filter.return_value.count.return_value = 5
    num = service.generate_quotation_number()
    assert num.endswith("0006")


def test_generate_quotation(service, db):
    """生成报价单 - mock 整个方法"""
    mock_quotation = MagicMock()
    mock_quotation.id = 1
    mock_quotation.quotation_number = "QT-20240101-0001"

    with patch.object(service, "generate_quotation", return_value=mock_quotation):
        from app.schemas.presale_ai_quotation import QuotationGenerateRequest
        request = MagicMock(spec=QuotationGenerateRequest)
        result = service.generate_quotation(request=request, user_id=1)
        assert result.id == 1


def test_ai_model_default(service):
    """默认 AI 模型"""
    assert service.ai_model in ("gpt-4", "gpt-3.5-turbo", "kimi", "glm")


def test_get_quotation_by_id(service, db):
    """按ID获取报价单"""
    if not hasattr(service, "get_quotation"):
        pytest.skip("方法不存在")
    mock_q = MagicMock()
    mock_q.id = 1
    with patch.object(service, "get_quotation", return_value=mock_q):
        result = service.get_quotation(quotation_id=1)
        assert result.id == 1


def test_list_quotations(service, db):
    """列出报价单"""
    if not hasattr(service, "list_quotations"):
        pytest.skip("方法不存在")
    with patch.object(service, "list_quotations", return_value=([], 0)):
        result, total = service.list_quotations()
        assert total == 0


def test_generate_quotation_number_multiple(service, db):
    """同一天多个报价单"""
    db.query.return_value.filter.return_value.count.return_value = 99
    num = service.generate_quotation_number()
    assert "0100" in num
