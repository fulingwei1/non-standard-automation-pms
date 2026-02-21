# -*- coding: utf-8 -*-
"""
测试 ResourceWasteAnalysisCore - 资源浪费分析核心类

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.resource_waste_analysis.core import ResourceWasteAnalysisCore


class TestResourceWasteAnalysisCoreInit:
    """测试ResourceWasteAnalysisCore初始化"""

    def test_init_default_rate(self):
        """测试默认工时成本初始化"""
        db = Mock(spec=Session)
        core = ResourceWasteAnalysisCore(db)
        
        assert core.db == db
        assert core.hourly_rate == ResourceWasteAnalysisCore.DEFAULT_HOURLY_RATE
        assert core.hourly_rate == Decimal('300')

    def test_init_custom_rate(self):
        """测试自定义工时成本初始化"""
        db = Mock(spec=Session)
        custom_rate = Decimal('500')
        core = ResourceWasteAnalysisCore(db, hourly_rate=custom_rate)
        
        assert core.db == db
        assert core.hourly_rate == custom_rate

    def test_init_integer_rate(self):
        """测试整数工时成本"""
        db = Mock(spec=Session)
        core = ResourceWasteAnalysisCore(db, hourly_rate=Decimal('400'))
        
        assert core.hourly_rate == Decimal('400')

    def test_init_zero_rate(self):
        """测试零工时成本"""
        db = Mock(spec=Session)
        core = ResourceWasteAnalysisCore(db, hourly_rate=Decimal('0'))
        
        assert core.hourly_rate == Decimal('0')

    def test_init_none_rate_uses_default(self):
        """测试None使用默认值"""
        db = Mock(spec=Session)
        core = ResourceWasteAnalysisCore(db, hourly_rate=None)
        
        assert core.hourly_rate == ResourceWasteAnalysisCore.DEFAULT_HOURLY_RATE


class TestDefaultHourlyRate:
    """测试默认工时成本常量"""

    def test_default_hourly_rate_value(self):
        """测试默认值为300"""
        assert ResourceWasteAnalysisCore.DEFAULT_HOURLY_RATE == Decimal('300')

    def test_default_hourly_rate_type(self):
        """测试默认值类型"""
        assert isinstance(ResourceWasteAnalysisCore.DEFAULT_HOURLY_RATE, Decimal)


class TestRoleHourlyRates:
    """测试角色工时成本"""

    def test_engineer_rate(self):
        """测试工程师工时成本"""
        rate = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES['engineer']
        assert rate == Decimal('300')

    def test_senior_engineer_rate(self):
        """测试高级工程师工时成本"""
        rate = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES['senior_engineer']
        assert rate == Decimal('400')

    def test_presales_rate(self):
        """测试售前工时成本"""
        rate = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES['presales']
        assert rate == Decimal('350')

    def test_designer_rate(self):
        """测试设计师工时成本"""
        rate = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES['designer']
        assert rate == Decimal('320')

    def test_project_manager_rate(self):
        """测试项目经理工时成本"""
        rate = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES['project_manager']
        assert rate == Decimal('450')

    def test_all_roles_count(self):
        """测试角色总数"""
        assert len(ResourceWasteAnalysisCore.ROLE_HOURLY_RATES) == 5

    def test_all_rates_are_decimal(self):
        """测试所有工时成本都是Decimal类型"""
        for role, rate in ResourceWasteAnalysisCore.ROLE_HOURLY_RATES.items():
            assert isinstance(rate, Decimal), f"{role} rate should be Decimal"

    def test_all_rates_are_positive(self):
        """测试所有工时成本都是正数"""
        for role, rate in ResourceWasteAnalysisCore.ROLE_HOURLY_RATES.items():
            assert rate > 0, f"{role} rate should be positive"

    def test_role_rate_ordering(self):
        """测试工时成本排序"""
        rates = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES
        # 项目经理应该最高
        assert rates['project_manager'] > rates['senior_engineer']
        # 高级工程师应该高于普通工程师
        assert rates['senior_engineer'] > rates['engineer']


class TestDatabaseSession:
    """测试数据库会话"""

    def test_db_session_stored(self):
        """测试数据库会话被正确存储"""
        db = Mock(spec=Session)
        core = ResourceWasteAnalysisCore(db)
        
        assert core.db is db

    def test_db_session_type(self):
        """测试数据库会话类型"""
        db = Mock(spec=Session)
        core = ResourceWasteAnalysisCore(db)
        
        # 验证db是Session类型的mock
        assert hasattr(core.db, 'query')
        assert hasattr(core.db, 'commit')


class TestDecimalPrecision:
    """测试Decimal精度"""

    def test_rate_precision(self):
        """测试工时成本精度"""
        db = Mock(spec=Session)
        rate = Decimal('300.50')
        core = ResourceWasteAnalysisCore(db, hourly_rate=rate)
        
        assert core.hourly_rate == Decimal('300.50')

    def test_high_precision_rate(self):
        """测试高精度工时成本"""
        db = Mock(spec=Session)
        rate = Decimal('300.123456')
        core = ResourceWasteAnalysisCore(db, hourly_rate=rate)
        
        assert core.hourly_rate == rate

    def test_calculation_precision(self):
        """测试计算精度"""
        # Decimal保证计算精度
        rate = Decimal('300.50')
        hours = Decimal('8.25')
        cost = rate * hours
        
        # 验证精度
        assert cost == Decimal('2479.125')


class TestEdgeCases:
    """测试边界情况"""

    def test_very_high_rate(self):
        """测试非常高的工时成本"""
        db = Mock(spec=Session)
        high_rate = Decimal('10000')
        core = ResourceWasteAnalysisCore(db, hourly_rate=high_rate)
        
        assert core.hourly_rate == high_rate

    def test_fractional_rate(self):
        """测试小数工时成本"""
        db = Mock(spec=Session)
        fractional_rate = Decimal('0.5')
        core = ResourceWasteAnalysisCore(db, hourly_rate=fractional_rate)
        
        assert core.hourly_rate == fractional_rate

    def test_multiple_instances(self):
        """测试多个实例"""
        db1 = Mock(spec=Session)
        db2 = Mock(spec=Session)
        
        core1 = ResourceWasteAnalysisCore(db1, hourly_rate=Decimal('300'))
        core2 = ResourceWasteAnalysisCore(db2, hourly_rate=Decimal('400'))
        
        assert core1.hourly_rate == Decimal('300')
        assert core2.hourly_rate == Decimal('400')
        assert core1.db is db1
        assert core2.db is db2

    def test_rate_immutability(self):
        """测试工时成本不可变性（Decimal特性）"""
        db = Mock(spec=Session)
        rate = Decimal('300')
        core = ResourceWasteAnalysisCore(db, hourly_rate=rate)
        
        original_rate = core.hourly_rate
        # Decimal是不可变的
        assert core.hourly_rate is original_rate


class TestRoleHourlyRatesAccess:
    """测试角色工时成本访问"""

    def test_access_existing_role(self):
        """测试访问存在的角色"""
        rate = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES.get('engineer')
        assert rate == Decimal('300')

    def test_access_nonexistent_role(self):
        """测试访问不存在的角色"""
        rate = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES.get('nonexistent')
        assert rate is None

    def test_iterate_all_roles(self):
        """测试遍历所有角色"""
        roles = list(ResourceWasteAnalysisCore.ROLE_HOURLY_RATES.keys())
        
        assert 'engineer' in roles
        assert 'senior_engineer' in roles
        assert 'presales' in roles
        assert 'designer' in roles
        assert 'project_manager' in roles


class TestClassConstants:
    """测试类常量"""

    def test_constants_are_class_attributes(self):
        """测试常量是类属性"""
        assert hasattr(ResourceWasteAnalysisCore, 'DEFAULT_HOURLY_RATE')
        assert hasattr(ResourceWasteAnalysisCore, 'ROLE_HOURLY_RATES')

    def test_constants_accessible_from_instance(self):
        """测试从实例访问常量"""
        db = Mock(spec=Session)
        core = ResourceWasteAnalysisCore(db)
        
        assert core.DEFAULT_HOURLY_RATE == Decimal('300')
        assert len(core.ROLE_HOURLY_RATES) == 5

    def test_role_rates_is_dict(self):
        """测试ROLE_HOURLY_RATES是字典"""
        assert isinstance(ResourceWasteAnalysisCore.ROLE_HOURLY_RATES, dict)


class TestInitialization:
    """测试初始化场景"""

    def test_init_with_all_parameters(self):
        """测试所有参数初始化"""
        db = Mock(spec=Session)
        rate = Decimal('350')
        
        core = ResourceWasteAnalysisCore(db=db, hourly_rate=rate)
        
        assert core.db == db
        assert core.hourly_rate == rate

    def test_init_positional_args(self):
        """测试位置参数初始化"""
        db = Mock(spec=Session)
        rate = Decimal('400')
        
        core = ResourceWasteAnalysisCore(db, rate)
        
        assert core.db == db
        assert core.hourly_rate == rate

    def test_init_keyword_args(self):
        """测试关键字参数初始化"""
        db = Mock(spec=Session)
        
        core = ResourceWasteAnalysisCore(db=db, hourly_rate=Decimal('500'))
        
        assert core.hourly_rate == Decimal('500')
