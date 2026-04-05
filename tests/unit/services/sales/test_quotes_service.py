# -*- coding: utf-8 -*-
"""
quotes_service 单元测试

测试销售报价管理服务。
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.quotes_service import QuotesService


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return QuotesService(mock_db)


@pytest.fixture
def mock_user():
    """模拟用户"""
    user = MagicMock()
    user.id = 1
    user.username = "zhangsan"
    user.real_name = "张三"
    return user


@pytest.fixture
def sample_quote():
    """示例报价"""
    quote = MagicMock()
    quote.id = 1
    quote.quote_code = "QT202603120001"
    quote.opportunity_id = 10
    quote.customer_id = 100
    quote.status = "draft"
    quote.valid_until = date.today() + timedelta(days=30)
    quote.owner_id = 1
    quote.created_at = date.today()
    quote.updated_at = date.today()

    # 关联对象
    quote.customer = MagicMock()
    quote.customer.customer_name = "测试客户"

    quote.owner = MagicMock()
    quote.owner.real_name = "张三"

    quote.opportunity = MagicMock()
    quote.opportunity.opp_name = "测试商机"

    quote.current_version = MagicMock()
    quote.current_version.id = 1
    quote.current_version.version_no = "v1"
    quote.current_version.total_price = 100000
    quote.current_version.cost_total = 80000
    quote.current_version.gross_margin = 20.0
    quote.current_version.lead_time_days = 30
    quote.current_version.delivery_date = date.today() + timedelta(days=60)

    quote.versions = [quote.current_version]

    return quote


# ========== _infer_quote_type 测试 ==========

class TestInferQuoteType:
    """_infer_quote_type 测试"""

    def test_service_type(self, service):
        """服务类型"""
        assert service._infer_quote_type("维保服务合同") == "SERVICE"
        assert service._infer_quote_type("售后服务") == "SERVICE"
        assert service._infer_quote_type("设备调试") == "SERVICE"
        assert service._infer_quote_type("培训服务") == "SERVICE"
        assert service._infer_quote_type("Service Agreement") == "SERVICE"

    def test_standard_type(self, service):
        """标准类型"""
        assert service._infer_quote_type("标准备件") == "STANDARD"
        assert service._infer_quote_type("备件采购") == "STANDARD"
        assert service._infer_quote_type("耗材订单") == "STANDARD"
        assert service._infer_quote_type("Standard Parts") == "STANDARD"

    def test_project_type(self, service):
        """项目类型"""
        assert service._infer_quote_type("自动化产线项目") == "PROJECT"
        assert service._infer_quote_type("机器人工站") == "PROJECT"
        assert service._infer_quote_type("输送线改造") == "PROJECT"
        assert service._infer_quote_type("系统集成") == "PROJECT"

    def test_custom_type(self, service):
        """自定义类型（默认）"""
        assert service._infer_quote_type("其他报价") == "CUSTOM"
        assert service._infer_quote_type("") == "CUSTOM"
        assert service._infer_quote_type(None) == "CUSTOM"


# ========== _infer_priority 测试 ==========

class TestInferPriority:
    """_infer_priority 测试"""

    def test_low_priority_for_rejected(self, service):
        """驳回状态为低优先级"""
        assert service._infer_priority("REJECTED", None) == "LOW"
        assert service._infer_priority("EXPIRED", None) == "LOW"

    def test_high_priority_for_in_review(self, service):
        """审核中为高优先级"""
        assert service._infer_priority("IN_REVIEW", None) == "HIGH"
        assert service._infer_priority("SUBMITTED", None) == "HIGH"

    def test_urgent_priority_for_expiring_soon(self, service):
        """即将过期为紧急"""
        valid_until = date.today() + timedelta(days=3)
        assert service._infer_priority("draft", valid_until) == "URGENT"

        valid_until = date.today() + timedelta(days=7)
        assert service._infer_priority("draft", valid_until) == "URGENT"

    def test_medium_priority_default(self, service):
        """默认中优先级"""
        assert service._infer_priority("draft", None) == "MEDIUM"
        
        valid_until = date.today() + timedelta(days=30)
        assert service._infer_priority("draft", valid_until) == "MEDIUM"


# ========== _pick_display_version 测试 ==========

class TestPickDisplayVersion:
    """_pick_display_version 测试"""

    def test_use_current_version(self, service, sample_quote):
        """使用当前版本"""
        result = service._pick_display_version(sample_quote)
        assert result == sample_quote.current_version

    def test_use_latest_version_when_no_current(self, service):
        """无当前版本时使用最新版本"""
        quote = MagicMock()
        quote.current_version = None

        v1 = MagicMock()
        v1.id = 1
        v2 = MagicMock()
        v2.id = 2
        quote.versions = [v1, v2]

        result = service._pick_display_version(quote)
        assert result == v2  # ID 最大的

    def test_no_version(self, service):
        """无版本"""
        quote = MagicMock()
        quote.current_version = None
        quote.versions = []

        result = service._pick_display_version(quote)
        assert result is None


# ========== _generate_quote_number 测试 ==========

class TestGenerateQuoteNumber:
    """_generate_quote_number 测试"""

    def test_generate_first_quote_of_day(self, service, mock_db):
        """当天第一个报价"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        result = service._generate_quote_number()

        today = date.today().strftime("%Y%m%d")
        assert result == f"QT{today}0001"

    def test_generate_subsequent_quote(self, service, mock_db):
        """当天后续报价"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5

        result = service._generate_quote_number()

        today = date.today().strftime("%Y%m%d")
        assert result == f"QT{today}0006"


# ========== get_quotes 测试 ==========

class TestGetQuotes:
    """get_quotes 测试"""

    def test_get_quotes_basic(self, service, mock_db, sample_quote):
        """获取报价列表基础"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_quote]

        with patch("app.services.sales.quotes_service.apply_keyword_filter", return_value=mock_query):
            with patch("app.services.sales.quotes_service.apply_pagination", return_value=mock_query):
                result = service.get_quotes(page=1, page_size=20)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0]["quote_code"] == "QT202603120001"

    def test_get_quotes_with_filters(self, service, mock_db, sample_quote):
        """获取报价列表（带筛选）"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_quote]

        with patch("app.services.sales.quotes_service.apply_keyword_filter", return_value=mock_query):
            with patch("app.services.sales.quotes_service.apply_pagination", return_value=mock_query):
                result = service.get_quotes(
                    status="draft",
                    customer_id=100,
                    start_date=date.today() - timedelta(days=30),
                    end_date=date.today(),
                )

        assert result.total == 1

    def test_get_quotes_with_user_permission(self, service, mock_db, mock_user, sample_quote):
        """获取报价列表（带用户权限）"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_quote]

        with patch("app.services.sales.quotes_service.apply_keyword_filter", return_value=mock_query):
            with patch("app.services.sales.quotes_service.apply_pagination", return_value=mock_query):
                with patch("app.core.sales_permissions.filter_sales_data_by_scope", return_value=mock_query):
                    result = service.get_quotes(current_user=mock_user)

        assert result.total == 1


# ========== create_quote 测试 ==========

class TestCreateQuote:
    """create_quote 测试"""

    def test_create_quote_success(self, service, mock_db, mock_user):
        """创建报价成功"""
        quote_data = MagicMock()
        quote_data.customer_id = 100
        quote_data.title = "测试报价"
        quote_data.description = "描述"
        quote_data.total_amount = 100000
        quote_data.valid_until = date.today() + timedelta(days=30)
        quote_data.terms = "条款"

        # 模拟生成编号
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        # 模拟 Quote 类和 save_obj
        mock_quote_instance = MagicMock()
        mock_quote_instance.id = 1
        mock_quote_instance.quote_number = "QT202603120001"

        with patch("app.services.sales.quotes_service.Quote", return_value=mock_quote_instance) as mock_quote_class:
            with patch("app.services.sales.quotes_service.save_obj") as mock_save:
                result = service.create_quote(quote_data, mock_user)

        mock_quote_class.assert_called_once()
        mock_save.assert_called_once()
