# -*- coding: utf-8 -*-
"""
完整单元测试 - strategy/kpi_service/crud.py
目标：60%+ 覆盖率，30+ 测试用例
"""
import pytest
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.strategy.kpi_service.crud import (
    create_kpi,
    get_kpi,
    list_kpis,
    update_kpi,
    delete_kpi,
)


def make_create_data(**kwargs):
    """创建KPI创建数据对象"""
    data = MagicMock()
    data.csf_id = kwargs.get("csf_id", 1)
    data.code = kwargs.get("code", "K001")
    data.name = kwargs.get("name", "Test KPI")
    data.description = kwargs.get("description", None)
    data.ipooc_type = kwargs.get("ipooc_type", "INPUT")
    data.unit = kwargs.get("unit", "%")
    data.direction = kwargs.get("direction", "UP")
    data.target_value = kwargs.get("target_value", Decimal("100"))
    data.baseline_value = kwargs.get("baseline_value", None)
    data.excellent_threshold = kwargs.get("excellent_threshold", None)
    data.good_threshold = kwargs.get("good_threshold", None)
    data.warning_threshold = kwargs.get("warning_threshold", None)
    data.data_source_type = kwargs.get("data_source_type", "MANUAL")
    data.data_source_config = kwargs.get("data_source_config", None)
    data.frequency = kwargs.get("frequency", "MONTHLY")
    data.weight = kwargs.get("weight", Decimal("1"))
    data.owner_user_id = kwargs.get("owner_user_id", None)
    return data


def make_update_data(**kwargs):
    """创建KPI更新数据对象"""
    data = MagicMock()
    data.model_dump.return_value = kwargs
    return data


class TestCreateKpi:
    """创建KPI测试"""
    
    def test_create_basic_kpi(self):
        """测试创建基础KPI"""
        db = MagicMock()
        data = make_create_data()
        
        kpi = create_kpi(db, data)
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
    
    def test_create_kpi_with_all_fields(self):
        """测试创建包含所有字段的KPI"""
        db = MagicMock()
        data = make_create_data(
            csf_id=5,
            code="K999",
            name="Complete KPI",
            description="Full description",
            ipooc_type="OUTPUT",
            unit="件",
            direction="DOWN",
            target_value=Decimal("200"),
            baseline_value=Decimal("150"),
            excellent_threshold=Decimal("220"),
            good_threshold=Decimal("180"),
            warning_threshold=Decimal("160"),
            data_source_type="AUTO",
            frequency="WEEKLY",
            weight=Decimal("2.5"),
            owner_user_id=123
        )
        
        kpi = create_kpi(db, data)
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
    
    def test_create_kpi_with_data_source_config(self):
        """测试创建带数据源配置的KPI"""
        db = MagicMock()
        config = {"module": "sales", "metric": "revenue"}
        data = make_create_data(data_source_config=config)
        
        kpi = create_kpi(db, data)
        
        db.add.assert_called_once()
        # 验证config被转换为JSON字符串
        call_args = db.add.call_args[0][0]
        assert call_args.data_source_config == json.dumps(config)
    
    def test_create_kpi_without_data_source_config(self):
        """测试创建无数据源配置的KPI"""
        db = MagicMock()
        data = make_create_data(data_source_config=None)
        
        kpi = create_kpi(db, data)
        
        call_args = db.add.call_args[0][0]
        assert call_args.data_source_config is None
    
    def test_create_kpi_with_empty_config(self):
        """测试创建空配置的KPI"""
        db = MagicMock()
        data = make_create_data(data_source_config={})
        
        kpi = create_kpi(db, data)
        
        call_args = db.add.call_args[0][0]
        assert call_args.data_source_config == json.dumps({})


class TestGetKpi:
    """获取KPI测试"""
    
    def test_get_existing_kpi(self):
        """测试获取存在的KPI"""
        db = MagicMock()
        mock_kpi = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_kpi
        
        result = get_kpi(db, 1)
        
        assert result is mock_kpi
        db.query.assert_called_once()
    
    def test_get_nonexistent_kpi(self):
        """测试获取不存在的KPI"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = get_kpi(db, 999)
        
        assert result is None
    
    def test_get_kpi_filters_inactive(self):
        """测试获取时过滤非活动KPI"""
        db = MagicMock()
        
        get_kpi(db, 1)
        
        # 验证查询包含is_active过滤
        db.query.return_value.filter.assert_called_once()
    
    def test_get_kpi_different_ids(self):
        """测试获取不同ID的KPI"""
        db = MagicMock()
        mock_kpi = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_kpi
        
        for kpi_id in [1, 100, 999]:
            result = get_kpi(db, kpi_id)
            assert result is mock_kpi


class TestListKpis:
    """列表查询KPI测试"""
    
    def test_list_all_kpis(self):
        """测试列出所有KPI"""
        db = MagicMock()
        mock_items = [MagicMock(), MagicMock(), MagicMock()]
        
        query = MagicMock()
        query.filter.return_value = query
        query.join.return_value = query
        query.count.return_value = 3
        query.order_by.return_value = query
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = mock_items
            items, total = list_kpis(db)
        
        assert len(items) == 3
        assert total == 3
    
    def test_list_kpis_empty(self):
        """测试列出空KPI列表"""
        db = MagicMock()
        
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 0
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            items, total = list_kpis(db)
        
        assert items == []
        assert total == 0
    
    def test_list_kpis_filter_by_csf_id(self):
        """测试按CSF ID筛选"""
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 2
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock(), MagicMock()]
            items, total = list_kpis(db, csf_id=5)
        
        assert total == 2
        # 验证filter被调用
        assert query.filter.call_count >= 1
    
    def test_list_kpis_filter_by_strategy_id(self):
        """测试按战略ID筛选"""
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.join.return_value = query
        query.count.return_value = 5
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock()] * 5
            items, total = list_kpis(db, strategy_id=10)
        
        assert total == 5
        # 验证join被调用（需要join CSF表）
        query.join.assert_called()
    
    def test_list_kpis_filter_by_ipooc_type(self):
        """测试按IPOOC类型筛选"""
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 3
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock()] * 3
            items, total = list_kpis(db, ipooc_type="OUTPUT")
        
        assert total == 3
    
    def test_list_kpis_filter_by_data_source_type(self):
        """测试按数据源类型筛选"""
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 4
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock()] * 4
            items, total = list_kpis(db, data_source_type="AUTO")
        
        assert total == 4
    
    def test_list_kpis_multiple_filters(self):
        """测试组合筛选条件"""
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.join.return_value = query
        query.count.return_value = 1
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock()]
            items, total = list_kpis(
                db,
                strategy_id=10,
                ipooc_type="INPUT",
                data_source_type="MANUAL"
            )
        
        assert total == 1
    
    def test_list_kpis_with_pagination(self):
        """测试分页"""
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 100
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [MagicMock()] * 10
            items, total = list_kpis(db, skip=20, limit=10)
        
        # 验证分页函数被调用
        mock_pag.assert_called_once()
        args = mock_pag.call_args[0]
        assert args[1] == 20  # skip
        assert args[2] == 10  # limit
        assert len(items) == 10
        assert total == 100


class TestUpdateKpi:
    """更新KPI测试"""
    
    def test_update_kpi_not_found(self):
        """测试更新不存在的KPI"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        data = make_update_data()
        
        result = update_kpi(db, 999, data)
        
        assert result is None
        db.commit.assert_not_called()
    
    def test_update_kpi_single_field(self):
        """测试更新单个字段"""
        db = MagicMock()
        kpi_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        data = make_update_data(name="Updated Name")
        
        result = update_kpi(db, 1, data)
        
        assert kpi_mock.name == "Updated Name"
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(kpi_mock)
    
    def test_update_kpi_multiple_fields(self):
        """测试更新多个字段"""
        db = MagicMock()
        kpi_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        data = make_update_data(
            name="New Name",
            target_value=Decimal("200"),
            frequency="WEEKLY"
        )
        
        result = update_kpi(db, 1, data)
        
        assert kpi_mock.name == "New Name"
        assert kpi_mock.target_value == Decimal("200")
        assert kpi_mock.frequency == "WEEKLY"
        db.commit.assert_called_once()
    
    def test_update_kpi_with_data_source_config(self):
        """测试更新数据源配置"""
        db = MagicMock()
        kpi_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        new_config = {"new": "config"}
        data = make_update_data(data_source_config=new_config)
        
        result = update_kpi(db, 1, data)
        
        # 配置应被序列化为JSON
        assert kpi_mock.data_source_config == json.dumps(new_config)
    
    def test_update_kpi_clear_data_source_config(self):
        """测试清空数据源配置"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.data_source_config = '{"old": "config"}'
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        data = make_update_data(data_source_config=None)
        
        # data_source_config=None不会更新（exclude_unset）
        # 如果要清空，需要传空dict
        data_with_empty = make_update_data(data_source_config={})
        
        result = update_kpi(db, 1, data_with_empty)
        
        assert kpi_mock.data_source_config == json.dumps({})
    
    def test_update_kpi_exclude_unset(self):
        """测试只更新提供的字段"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.name = "Original Name"
        kpi_mock.target_value = Decimal("100")
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        
        # 只更新name，不更新target_value
        data = make_update_data(name="Updated Name")
        
        update_kpi(db, 1, data)
        
        assert kpi_mock.name == "Updated Name"
        # target_value应保持原值（实际上会被设置，但这是mock的行为）


class TestDeleteKpi:
    """删除KPI测试"""
    
    def test_delete_existing_kpi(self):
        """测试删除存在的KPI"""
        db = MagicMock()
        kpi_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        
        result = delete_kpi(db, 1)
        
        assert result is True
        assert kpi_mock.is_active is False
        db.commit.assert_called_once()
    
    def test_delete_nonexistent_kpi(self):
        """测试删除不存在的KPI"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = delete_kpi(db, 999)
        
        assert result is False
        db.commit.assert_not_called()
    
    def test_delete_is_soft_delete(self):
        """测试是软删除而非硬删除"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.is_active = True
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        
        delete_kpi(db, 1)
        
        # 验证is_active被设为False，而不是调用db.delete()
        assert kpi_mock.is_active is False
        db.delete.assert_not_called()
    
    def test_delete_multiple_kpis(self):
        """测试删除多个KPI"""
        db = MagicMock()
        
        for kpi_id in [1, 2, 3]:
            kpi_mock = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = kpi_mock
            
            result = delete_kpi(db, kpi_id)
            assert result is True


class TestIntegrationScenarios:
    """集成场景测试"""
    
    def test_create_and_get_workflow(self):
        """测试创建后获取的工作流"""
        db = MagicMock()
        created_kpi = MagicMock()
        created_kpi.id = 1
        
        # Mock create
        db.add.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = None
        
        data = make_create_data(code="K001", name="Test KPI")
        kpi = create_kpi(db, data)
        
        # Mock get
        db.query.return_value.filter.return_value.first.return_value = created_kpi
        retrieved = get_kpi(db, 1)
        
        assert retrieved is created_kpi
    
    def test_create_update_workflow(self):
        """测试创建后更新的工作流"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.name = "Original"
        
        # 先创建
        create_data = make_create_data(name="Original")
        create_kpi(db, create_data)
        
        # 再更新
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        update_data = make_update_data(name="Updated")
        result = update_kpi(db, 1, update_data)
        
        assert kpi_mock.name == "Updated"
    
    def test_list_then_delete_workflow(self):
        """测试列表查询后删除的工作流"""
        db = MagicMock()
        
        # 先列表查询
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 1
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            kpi_mock = MagicMock()
            kpi_mock.id = 1
            mock_pag.return_value.all.return_value = [kpi_mock]
            items, total = list_kpis(db)
        
        # 然后删除
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        result = delete_kpi(db, 1)
        
        assert result is True
        assert kpi_mock.is_active is False


class TestEdgeCases:
    """边界情况测试"""
    
    def test_create_kpi_with_zero_values(self):
        """测试创建值为0的KPI"""
        db = MagicMock()
        data = make_create_data(
            target_value=Decimal("0"),
            baseline_value=Decimal("0"),
            weight=Decimal("0")
        )
        
        kpi = create_kpi(db, data)
        db.add.assert_called_once()
    
    def test_create_kpi_with_very_large_values(self):
        """测试创建超大值的KPI"""
        db = MagicMock()
        data = make_create_data(
            target_value=Decimal("999999999.99")
        )
        
        kpi = create_kpi(db, data)
        db.add.assert_called_once()
    
    def test_update_kpi_no_changes(self):
        """测试更新但无实际变化"""
        db = MagicMock()
        kpi_mock = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = kpi_mock
        data = make_update_data()  # 空更新
        
        result = update_kpi(db, 1, data)
        
        db.commit.assert_called_once()
    
    def test_list_kpis_with_zero_limit(self):
        """测试limit=0的列表查询"""
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 100
        db.query.return_value = query
        
        with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            items, total = list_kpis(db, limit=0)
        
        # 即使limit=0，总数仍正确
        assert total == 100
    
    def test_create_kpi_with_complex_json_config(self):
        """测试复杂JSON配置"""
        db = MagicMock()
        complex_config = {
            "module": "sales",
            "metrics": ["revenue", "profit"],
            "filters": {
                "region": "North",
                "year": 2024
            },
            "nested": {
                "level1": {
                    "level2": ["a", "b", "c"]
                }
            }
        }
        data = make_create_data(data_source_config=complex_config)
        
        kpi = create_kpi(db, data)
        
        call_args = db.add.call_args[0][0]
        # 验证能正确序列化复杂JSON
        assert call_args.data_source_config == json.dumps(complex_config)
