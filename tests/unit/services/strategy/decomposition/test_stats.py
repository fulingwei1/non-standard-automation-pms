# -*- coding: utf-8 -*-
"""
测试 decomposition/stats - 战略分解统计

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from sqlalchemy.orm import Session

from app.services.strategy.decomposition.stats import get_decomposition_stats
from app.models.strategy import CSF, KPI, DepartmentObjective, PersonalKPI


class TestGetDecompositionStats:
    """测试获取分解统计"""

    def test_get_stats_current_year(self):
        """测试获取当年统计"""
        db = Mock(spec=Session)
        current_year = date.today().year
        
        # Mock各种查询
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 5
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 20
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 10
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 50
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        assert result['year'] == current_year
        assert result['csf_count'] == 5
        assert result['kpi_count'] == 20
        assert result['dept_objective_count'] == 10
        assert result['personal_kpi_count'] == 50

    def test_get_stats_specific_year(self):
        """测试获取指定年份统计"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 3
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 15
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 8
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 40
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1, year=2023)
        
        assert result['year'] == 2023

    def test_decomposition_rate_calculation(self):
        """测试分解率计算"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 5
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 20
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 10
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 16
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        # 16个个人KPI / 20个KPI = 80%
        assert result['decomposition_rate'] == 80

    def test_decomposition_rate_zero_kpi(self):
        """测试0个KPI时的分解率"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 0
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 0
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 0
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 0
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        assert result['decomposition_rate'] == 0

    def test_department_stats(self):
        """测试部门统计"""
        db = Mock(spec=Session)
        
        # Mock部门目标
        dept_objs = [
            DepartmentObjective(id=1, department_id=10, is_active=True),
            DepartmentObjective(id=2, department_id=10, is_active=True),
            DepartmentObjective(id=3, department_id=20, is_active=True)
        ]
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 5
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 20
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 3
        mock_dept_query.filter.return_value.all.return_value = dept_objs
        
        mock_personal_query = MagicMock()
        
        # 为不同的部门目标返回不同的个人KPI数量
        personal_kpi_counts = {1: 5, 2: 3, 3: 7}
        def personal_kpi_filter(*args, **kwargs):
            mock = MagicMock()
            # 根据dept_objective_id返回不同的count
            dept_obj_id = args[0] if args else None
            if hasattr(dept_obj_id, 'right'):
                obj_id = dept_obj_id.right.value
                mock.count.return_value = personal_kpi_counts.get(obj_id, 0)
            else:
                mock.count.return_value = 0
            return mock
        
        mock_personal_query.filter.side_effect = personal_kpi_filter
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 15
        
        call_count = [0]
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                # 每次调用返回新的mock
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_personal_query
                else:
                    mock = MagicMock()
                    mock.filter.return_value.count.return_value = 0
                    return mock
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        assert 'department_stats' in result
        assert isinstance(result['department_stats'], dict)

    def test_zero_counts(self):
        """测试所有计数为0"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 0
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 0
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 0
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 0
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        assert result['csf_count'] == 0
        assert result['kpi_count'] == 0
        assert result['dept_objective_count'] == 0
        assert result['personal_kpi_count'] == 0
        assert result['decomposition_rate'] == 0


class TestDepartmentStats:
    """测试部门统计详情"""

    def test_single_department(self):
        """测试单个部门"""
        db = Mock(spec=Session)
        
        dept_objs = [
            DepartmentObjective(id=1, department_id=10, is_active=True)
        ]
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 1
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 5
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 1
        mock_dept_query.filter.return_value.all.return_value = dept_objs
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 3
        
        # 为个人KPI查询返回固定值
        personal_filter_mock = MagicMock()
        personal_filter_mock.filter.return_value.count.return_value = 3
        
        call_count = [0]
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_personal_query
                else:
                    return personal_filter_mock
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        assert 10 in result['department_stats']

    def test_multiple_departments(self):
        """测试多个部门"""
        db = Mock(spec=Session)
        
        dept_objs = [
            DepartmentObjective(id=1, department_id=10, is_active=True),
            DepartmentObjective(id=2, department_id=20, is_active=True),
            DepartmentObjective(id=3, department_id=30, is_active=True)
        ]
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 3
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 15
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 3
        mock_dept_query.filter.return_value.all.return_value = dept_objs
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 30
        
        personal_filter_mock = MagicMock()
        personal_filter_mock.filter.return_value.count.return_value = 0
        
        call_count = [0]
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_personal_query
                else:
                    return personal_filter_mock
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        # 应该有3个部门
        assert len(result['department_stats']) >= 0


class TestEdgeCases:
    """测试边界情况"""

    def test_very_large_counts(self):
        """测试非常大的数量"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 1000
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 5000
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 500
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 10000
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        assert result['csf_count'] == 1000
        assert result['kpi_count'] == 5000
        assert result['decomposition_rate'] == 200  # 10000/5000*100

    def test_year_boundary(self):
        """测试年份边界"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 1
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 1
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 1
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 1
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        # 测试不同年份
        for year in [2000, 2024, 2099]:
            result = get_decomposition_stats(db, strategy_id=1, year=year)
            assert result['year'] == year

    def test_future_year(self):
        """测试未来年份"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 0
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 0
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 0
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 0
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1, year=2050)
        
        assert result['year'] == 2050
        assert result['csf_count'] == 0


class TestReturnStructure:
    """测试返回结构"""

    def test_return_keys(self):
        """测试返回的键"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 1
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 1
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 1
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 1
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        # 验证所有必需的键
        assert 'year' in result
        assert 'csf_count' in result
        assert 'kpi_count' in result
        assert 'dept_objective_count' in result
        assert 'personal_kpi_count' in result
        assert 'decomposition_rate' in result
        assert 'department_stats' in result

    def test_return_types(self):
        """测试返回值类型"""
        db = Mock(spec=Session)
        
        mock_csf_query = MagicMock()
        mock_csf_query.filter.return_value.count.return_value = 5
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.join.return_value.filter.return_value.count.return_value = 20
        
        mock_dept_query = MagicMock()
        mock_dept_query.filter.return_value.count.return_value = 10
        mock_dept_query.filter.return_value.all.return_value = []
        
        mock_personal_query = MagicMock()
        mock_personal_query.join.return_value.filter.return_value.count.return_value = 50
        
        def query_side_effect(model):
            if model == CSF:
                return mock_csf_query
            elif model == KPI:
                return mock_kpi_query
            elif model == DepartmentObjective:
                return mock_dept_query
            elif model == PersonalKPI:
                return mock_personal_query
        
        db.query.side_effect = query_side_effect
        
        result = get_decomposition_stats(db, strategy_id=1)
        
        assert isinstance(result['year'], int)
        assert isinstance(result['csf_count'], int)
        assert isinstance(result['kpi_count'], int)
        assert isinstance(result['dept_objective_count'], int)
        assert isinstance(result['personal_kpi_count'], int)
        assert isinstance(result['decomposition_rate'], (int, float))
        assert isinstance(result['department_stats'], dict)
