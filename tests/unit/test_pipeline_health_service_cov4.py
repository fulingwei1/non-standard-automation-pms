"""
第四批覆盖测试 - pipeline_health_service
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

try:
    from app.services.pipeline_health_service import PipelineHealthService
    HAS_SERVICE = True
except Exception:
    HAS_SERVICE = False

pytestmark = pytest.mark.skipif(not HAS_SERVICE, reason="服务导入失败")


def make_service():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    return PipelineHealthService(db), db


class TestPipelineHealthService:
    def setup_method(self):
        self.service, self.db = make_service()

    def test_init(self):
        assert self.service.db is not None

    def test_calculate_lead_health_not_found(self):
        with pytest.raises(ValueError, match="线索 .* 不存在"):
            self.service.calculate_lead_health(9999)

    def test_calculate_lead_health_converted(self):
        lead = MagicMock()
        lead.status = 'CONVERTED'
        lead.lead_code = 'L001'
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.service.calculate_lead_health(1)
        assert result['health_status'] == 'H4'

    def test_calculate_lead_health_active_healthy(self):
        lead = MagicMock()
        lead.status = 'ACTIVE'
        lead.lead_code = 'L001'
        lead.follow_ups = []
        lead.next_action_at = None
        lead.created_at = datetime.now()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.service.calculate_lead_health(1)
        assert result['health_status'] in ('H1', 'H2', 'H3')

    def test_calculate_opportunity_health_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="商机 .* 不存在"):
            self.service.calculate_opportunity_health(9999)

    def test_calculate_opportunity_health_won(self):
        opp = MagicMock()
        opp.stage = 'WON'
        opp.opp_code = 'O001'
        self.db.query.return_value.filter.return_value.first.return_value = opp
        result = self.service.calculate_opportunity_health(1)
        assert result['health_status'] == 'H4'

    def test_calculate_opportunity_health_lost(self):
        opp = MagicMock()
        opp.stage = 'LOST'
        opp.opp_code = 'O002'
        self.db.query.return_value.filter.return_value.first.return_value = opp
        result = self.service.calculate_opportunity_health(2)
        assert result['health_status'] == 'H4'

    def test_calculate_quote_health_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="报价 .* 不存在"):
            self.service.calculate_quote_health(9999)

    def test_calculate_contract_health_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="合同 .* 不存在"):
            self.service.calculate_contract_health(9999)

    def test_calculate_payment_health_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="发票 .* 不存在"):
            self.service.calculate_payment_health(9999)

    def test_health_thresholds_defined(self):
        thresholds = self.service.HEALTH_THRESHOLDS
        assert 'LEAD' in thresholds
        assert 'OPPORTUNITY' in thresholds
        assert 'QUOTE' in thresholds
        assert 'CONTRACT' in thresholds
        assert 'PAYMENT' in thresholds
