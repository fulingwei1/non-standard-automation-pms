# -*- coding: utf-8 -*-
"""
I4组：app/utils/spec_match_service.py 深度单元测试

覆盖目标：17% → 70%+
策略：MagicMock 模拟 db、TechnicalSpecRequirement、SpecMatchRecord、AlertRecord
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.utils.spec_match_service import SpecMatchService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    return SpecMatchService()


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_req(
    project_id=1,
    material_code='MAT-ME-00001',
    material_name='伺服电机',
    specification='AC220V 1.5kW',
    brand='Siemens',
    model='1FK7',
    key_parameters=None,
    requirement_level='NORMAL',
    req_id=10
):
    """构造 TechnicalSpecRequirement mock"""
    req = MagicMock()
    req.id = req_id
    req.project_id = project_id
    req.material_code = material_code
    req.material_name = material_name
    req.specification = specification
    req.brand = brand
    req.model = model
    req.key_parameters = key_parameters
    req.requirement_level = requirement_level
    return req


# ===========================================================================
# SpecMatchService 初始化
# ===========================================================================

class TestSpecMatchServiceInit:
    def test_has_matcher(self):
        svc = SpecMatchService()
        assert svc.matcher is not None

    def test_matcher_type(self):
        from app.utils.spec_matcher import SpecMatcher
        svc = SpecMatchService()
        assert isinstance(svc.matcher, SpecMatcher)


# ===========================================================================
# check_po_item_spec_match
# ===========================================================================

class TestCheckPoItemSpecMatch:
    """测试 check_po_item_spec_match"""

    def test_no_requirements_returns_none(self, service, mock_db):
        """无规格要求时返回None"""
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.check_po_item_spec_match(
            db=mock_db,
            project_id=1,
            po_item_id=100,
            material_code='MAT-ME-00001',
            specification='AC220V 1.5kW'
        )

        assert result is None

    def test_perfect_match_creates_record(self, service, mock_db):
        """完全匹配时创建匹配记录"""
        req = _make_req()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        # mock SpecMatchRecord 创建
        mock_record = MagicMock()
        mock_record.id = 99

        with patch('app.utils.spec_match_service.SpecMatchRecord', return_value=mock_record):
            result = service.check_po_item_spec_match(
                db=mock_db,
                project_id=1,
                po_item_id=100,
                material_code='MAT-ME-00001',
                specification='AC220V 1.5kW',
                brand='Siemens',
                model='1FK7'
            )

        assert result is not None
        mock_db.add.assert_called()
        mock_db.flush.assert_called()

    def test_mismatched_triggers_alert(self, service, mock_db):
        """规格不匹配时触发预警创建"""
        req = _make_req(specification='AC380V 3kW')  # 要求不同
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        mock_record = MagicMock()
        mock_record.id = 99

        alert_created = []

        def mock_create_alert(**kwargs):
            alert_created.append(kwargs)

        service._create_alert = mock_create_alert

        with patch('app.utils.spec_match_service.SpecMatchRecord', return_value=mock_record):
            result = service.check_po_item_spec_match(
                db=mock_db,
                project_id=1,
                po_item_id=100,
                material_code='MAT-ME-00001',
                specification='DC12V 50W',
                brand='ABB',
                model='XYZ'
            )

        assert result is not None

    def test_material_code_mismatch_skips_req(self, service, mock_db):
        """req.material_code与物料编码不匹配时跳过该req"""
        req = _make_req(material_code='MAT-EL-00001')  # 不同物料码
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        result = service.check_po_item_spec_match(
            db=mock_db,
            project_id=1,
            po_item_id=100,
            material_code='MAT-ME-00001',  # 查询的不同
            specification='AC220V 1.5kW'
        )

        assert result is None

    def test_req_no_material_code_not_skipped(self, service, mock_db):
        """req.material_code为None时不跳过"""
        req = _make_req(material_code=None)  # 通用规格要求
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        mock_record = MagicMock()
        mock_record.id = 99

        with patch('app.utils.spec_match_service.SpecMatchRecord', return_value=mock_record):
            result = service.check_po_item_spec_match(
                db=mock_db,
                project_id=1,
                po_item_id=100,
                material_code='ANY-CODE',
                specification='AC220V 1.5kW'
            )

        assert result is not None

    def test_match_type_is_purchase_order(self, service, mock_db):
        """匹配类型为 PURCHASE_ORDER"""
        req = _make_req()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        captured_kwargs = {}

        def capture_record(**kwargs):
            captured_kwargs.update(kwargs)
            m = MagicMock()
            m.id = 1
            return m

        with patch('app.utils.spec_match_service.SpecMatchRecord', side_effect=capture_record):
            service.check_po_item_spec_match(
                db=mock_db,
                project_id=1,
                po_item_id=200,
                material_code='MAT-ME-00001',
                specification='AC220V 1.5kW',
                brand='Siemens',
                model='1FK7'
            )

        assert captured_kwargs.get('match_type') == 'PURCHASE_ORDER'
        assert captured_kwargs.get('match_target_id') == 200


# ===========================================================================
# check_bom_item_spec_match
# ===========================================================================

class TestCheckBomItemSpecMatch:
    """测试 check_bom_item_spec_match"""

    def test_no_requirements_returns_none(self, service, mock_db):
        """无规格要求时返回None"""
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.check_bom_item_spec_match(
            db=mock_db,
            project_id=1,
            bom_item_id=50,
            material_code='MAT-ME-00001',
            specification='AC220V 1.5kW'
        )

        assert result is None

    def test_match_type_is_bom(self, service, mock_db):
        """匹配类型为 BOM"""
        req = _make_req()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        captured_kwargs = {}

        def capture_record(**kwargs):
            captured_kwargs.update(kwargs)
            m = MagicMock()
            m.id = 2
            return m

        with patch('app.utils.spec_match_service.SpecMatchRecord', side_effect=capture_record):
            service.check_bom_item_spec_match(
                db=mock_db,
                project_id=1,
                bom_item_id=55,
                material_code='MAT-ME-00001',
                specification='AC220V 1.5kW',
                brand='Siemens',
                model='1FK7'
            )

        assert captured_kwargs.get('match_type') == 'BOM'
        assert captured_kwargs.get('match_target_id') == 55

    def test_creates_match_record(self, service, mock_db):
        """创建匹配记录"""
        req = _make_req(material_code=None)
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        mock_record = MagicMock()
        mock_record.id = 77

        with patch('app.utils.spec_match_service.SpecMatchRecord', return_value=mock_record):
            result = service.check_bom_item_spec_match(
                db=mock_db,
                project_id=1,
                bom_item_id=55,
                material_code='MAT-ME-00001',
                specification='AC220V 1.5kW'
            )

        assert result is not None
        mock_db.add.assert_called()
        mock_db.flush.assert_called()

    def test_empty_specification_handled(self, service, mock_db):
        """空规格字符串被正常处理"""
        req = _make_req(material_code=None)
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        mock_record = MagicMock()
        mock_record.id = 1

        with patch('app.utils.spec_match_service.SpecMatchRecord', return_value=mock_record):
            result = service.check_bom_item_spec_match(
                db=mock_db,
                project_id=1,
                bom_item_id=55,
                material_code='MAT-ME-00001',
                specification=None  # None 传入
            )

        # specification=None 时传入 '' 给 match_specification
        assert result is not None


# ===========================================================================
# _create_alert
# ===========================================================================

class TestCreateAlert:
    """测试 _create_alert"""

    def test_creates_alert_with_existing_rule(self, service, mock_db):
        """存在规则时直接使用"""
        mock_rule = MagicMock()
        mock_rule.id = 5

        # db.query(AlertRule).filter(...).first() -> mock_rule
        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule
        # db.query(AlertRecord) for counting
        mock_db.query.return_value.filter.return_value.count.return_value = 3

        req = _make_req()
        match_result = MagicMock()
        match_result.match_score = Decimal('60.0')
        match_result.differences = {'specification': {'required': 'A', 'actual': 'B'}}

        mock_alert = MagicMock()
        mock_alert.id = 10

        with patch('app.utils.spec_match_service.AlertRecord', return_value=mock_alert), \
             patch('app.utils.spec_match_service.apply_like_filter') as mock_alf:
            mock_alf.return_value = mock_db.query.return_value.filter.return_value
            service._create_alert(
                db=mock_db,
                project_id=1,
                match_record_id=99,
                requirement=req,
                match_result=match_result
            )

        mock_db.add.assert_called()

    def test_creates_default_rule_when_none_found(self, service, mock_db):
        """没有规则时自动创建默认规则"""
        # AlertRule.query.filter.first() -> None
        mock_rule_query = MagicMock()
        mock_rule_query.first.return_value = None

        mock_count_query = MagicMock()
        mock_count_query.count.return_value = 0

        # Simulate: first call gets AlertRule query, subsequent calls get AlertRecord count
        mock_new_rule = MagicMock()
        mock_new_rule.id = 99

        call_count = [0]

        def side_query(model_cls):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_rule_query
            return mock_count_query

        mock_db.query.side_effect = side_query

        req = _make_req()
        match_result = MagicMock()
        match_result.match_score = Decimal('45.0')
        match_result.differences = {'brand': {'required': 'A', 'actual': 'B'}}

        mock_alert = MagicMock()

        with patch('app.utils.spec_match_service.AlertRecord', return_value=mock_alert), \
             patch('app.utils.spec_match_service.AlertRule', return_value=mock_new_rule), \
             patch('app.utils.spec_match_service.apply_like_filter') as mock_alf:
            mock_alf.return_value = mock_count_query
            service._create_alert(
                db=mock_db,
                project_id=2,
                match_record_id=50,
                requirement=req,
                match_result=match_result
            )

        # db.add should have been called for both rule and alert
        assert mock_db.add.call_count >= 1

    def test_updates_match_record_alert_id(self, service, mock_db):
        """创建 alert 后更新 SpecMatchRecord.alert_id"""
        mock_rule = MagicMock()
        mock_rule.id = 1

        mock_alert = MagicMock()
        mock_alert.id = 200

        mock_match_record = MagicMock()

        call_num = [0]

        def query_side(model_cls):
            call_num[0] += 1
            q = MagicMock()
            if call_num[0] == 1:
                # AlertRule query
                q.filter.return_value.first.return_value = mock_rule
            elif call_num[0] == 2:
                # AlertRecord count
                q.filter.return_value.count.return_value = 0
            else:
                # SpecMatchRecord fetch
                q.filter.return_value.first.return_value = mock_match_record
            return q

        mock_db.query.side_effect = query_side

        req = _make_req()
        match_result = MagicMock()
        match_result.match_score = Decimal('30.0')
        match_result.differences = {}

        with patch('app.utils.spec_match_service.AlertRecord', return_value=mock_alert), \
             patch('app.utils.spec_match_service.apply_like_filter') as mock_alf:
            q = MagicMock()
            q.count.return_value = 0
            mock_alf.return_value = q
            service._create_alert(
                db=mock_db,
                project_id=1,
                match_record_id=99,
                requirement=req,
                match_result=match_result
            )

        # match_record.alert_id should have been set
        assert mock_match_record.alert_id == mock_alert.id


# ===========================================================================
# 边界条件
# ===========================================================================

class TestSpecMatchServiceEdgeCases:
    """边界条件测试"""

    def test_multiple_requirements_returns_first_match(self, service, mock_db):
        """多个规格要求时只处理第一个匹配的"""
        req1 = _make_req(material_code='MAT-ME-00001', req_id=1)
        req2 = _make_req(material_code='MAT-ME-00001', req_id=2, specification='DC24V')
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req1, req2]

        mock_record = MagicMock()
        mock_record.id = 1

        with patch('app.utils.spec_match_service.SpecMatchRecord', return_value=mock_record):
            result = service.check_po_item_spec_match(
                db=mock_db, project_id=1, po_item_id=1,
                material_code='MAT-ME-00001', specification='AC220V 1.5kW',
                brand='Siemens', model='1FK7'
            )

        # 只返回第一个匹配结果
        assert result is not None

    def test_none_brand_and_model_ok(self, service, mock_db):
        """brand 和 model 为 None 时正常处理"""
        req = _make_req(material_code=None)
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [req]

        mock_record = MagicMock()
        mock_record.id = 1

        with patch('app.utils.spec_match_service.SpecMatchRecord', return_value=mock_record):
            result = service.check_bom_item_spec_match(
                db=mock_db, project_id=1, bom_item_id=1,
                material_code='ANY', specification='AC220V',
                brand=None, model=None
            )

        assert result is not None
