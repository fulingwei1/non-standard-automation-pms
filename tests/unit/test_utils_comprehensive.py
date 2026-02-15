"""
Utils层综合测试
测试各种工具函数、计算器、转换器等
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.utils.risk_calculator import RiskCalculator
from app.utils.project_utils import ProjectUtils
from app.utils.number_generator import NumberGenerator
from app.utils.pagination import paginate
from app.utils.holiday_utils import is_holiday, get_working_days
from app.utils.pinyin_utils import to_pinyin, get_initials


class TestRiskCalculator:
    """风险计算器测试"""

    def test_calculate_basic_risk_score(self):
        """测试基本风险评分"""
        factors = {
            'complexity': 'high',
            'team_experience': 'low',
            'timeline_pressure': 'high',
            'requirements_clarity': 'medium'
        }
        
        calculator = RiskCalculator()
        score = calculator.calculate_risk_score(factors)
        
        assert 0 <= score <= 100
        assert score > 50  # 高复杂度+低经验应该是高风险

    def test_risk_level_mapping(self):
        """测试风险等级映射"""
        calculator = RiskCalculator()
        
        assert calculator.get_risk_level(20) == 'low'
        assert calculator.get_risk_level(45) == 'medium'
        assert calculator.get_risk_level(70) == 'high'
        assert calculator.get_risk_level(90) == 'critical'

    def test_calculate_weighted_risk(self):
        """测试加权风险计算"""
        risk_items = [
            {'score': 80, 'weight': 0.5},  # 技术风险
            {'score': 60, 'weight': 0.3},  # 资源风险
            {'score': 40, 'weight': 0.2},  # 时间风险
        ]
        
        calculator = RiskCalculator()
        weighted_score = calculator.calculate_weighted_risk(risk_items)
        
        # 80*0.5 + 60*0.3 + 40*0.2 = 40 + 18 + 8 = 66
        assert weighted_score == 66.0

    def test_assess_schedule_risk(self):
        """测试进度风险评估"""
        calculator = RiskCalculator()
        
        project_data = {
            'delay_days': 10,
            'progress_deviation': -15,
            'remaining_days': 30
        }
        
        schedule_risk = calculator.assess_schedule_risk(project_data)
        
        assert schedule_risk['level'] in ['low', 'medium', 'high', 'critical']
        assert schedule_risk['score'] > 0

    def test_assess_budget_risk(self):
        """测试预算风险评估"""
        calculator = RiskCalculator()
        
        budget_data = {
            'planned_cost': 1000000,
            'actual_cost': 800000,
            'remaining_budget': 200000,
            'completion_percentage': 90
        }
        
        budget_risk = calculator.assess_budget_risk(budget_data)
        
        # 90%完成但只剩20%预算，风险应该较高
        assert budget_risk['level'] in ['high', 'critical']


class TestProjectUtils:
    """项目工具测试"""

    def test_calculate_project_health_score(self):
        """测试项目健康度评分"""
        utils = ProjectUtils()
        
        metrics = {
            'schedule_performance': 0.9,  # SPI
            'cost_performance': 0.85,     # CPI
            'quality_score': 88,
            'team_satisfaction': 4.2
        }
        
        health_score = utils.calculate_health_score(metrics)
        
        assert 0 <= health_score <= 100
        assert health_score > 70  # 各项指标都不错

    def test_estimate_project_duration(self):
        """测试项目工期估算"""
        utils = ProjectUtils()
        
        params = {
            'story_points': 120,
            'team_velocity': 20,  # 每周20点
            'buffer_factor': 1.2   # 20%缓冲
        }
        
        estimated_weeks = utils.estimate_duration(params)
        
        # 120 / 20 * 1.2 = 7.2周
        assert estimated_weeks == pytest.approx(7.2, abs=0.1)

    def test_calculate_earned_value(self):
        """测试挣值计算"""
        utils = ProjectUtils()
        
        data = {
            'total_budget': 1000000,
            'completion_percentage': 60
        }
        
        ev = utils.calculate_earned_value(data)
        
        assert ev == 600000

    def test_calculate_evm_indices(self):
        """测试EVM指标计算"""
        utils = ProjectUtils()
        
        data = {
            'pv': 500000,  # Planned Value
            'ev': 450000,  # Earned Value
            'ac': 480000   # Actual Cost
        }
        
        indices = utils.calculate_evm_indices(data)
        
        # CPI = EV / AC = 450000 / 480000 ≈ 0.9375
        assert indices['cpi'] == pytest.approx(0.9375, abs=0.01)
        
        # SPI = EV / PV = 450000 / 500000 = 0.9
        assert indices['spi'] == 0.9


class TestNumberGenerator:
    """编号生成器测试"""

    def test_generate_project_number(self):
        """测试项目编号生成"""
        generator = NumberGenerator()
        
        project_number = generator.generate_project_number(
            prefix='PRJ',
            date_str='20260216',
            sequence=1
        )
        
        assert project_number == 'PRJ-20260216-0001'

    def test_generate_unique_number(self):
        """测试唯一编号生成"""
        generator = NumberGenerator()
        
        numbers = [generator.generate_unique_number('TSK') for _ in range(100)]
        
        # 所有编号应该唯一
        assert len(numbers) == len(set(numbers))

    def test_parse_project_number(self):
        """测试项目编号解析"""
        generator = NumberGenerator()
        
        parsed = generator.parse_project_number('PRJ-20260216-0042')
        
        assert parsed['prefix'] == 'PRJ'
        assert parsed['date'] == '20260216'
        assert parsed['sequence'] == 42


class TestPagination:
    """分页工具测试"""

    def test_basic_pagination(self):
        """测试基本分页"""
        items = list(range(1, 101))  # 100个项目
        
        result = paginate(items, page=1, page_size=20)
        
        assert result['total'] == 100
        assert result['page'] == 1
        assert result['page_size'] == 20
        assert result['total_pages'] == 5
        assert len(result['items']) == 20
        assert result['items'][0] == 1

    def test_pagination_last_page(self):
        """测试最后一页分页"""
        items = list(range(1, 101))
        
        result = paginate(items, page=5, page_size=20)
        
        assert len(result['items']) == 20
        assert result['items'][0] == 81

    def test_pagination_partial_page(self):
        """测试不完整页"""
        items = list(range(1, 96))  # 95个项目
        
        result = paginate(items, page=5, page_size=20)
        
        assert len(result['items']) == 15  # 最后一页只有15个
        assert result['total_pages'] == 5

    def test_pagination_empty_result(self):
        """测试空结果分页"""
        result = paginate([], page=1, page_size=20)
        
        assert result['total'] == 0
        assert result['items'] == []
        assert result['total_pages'] == 0


class TestHolidayUtils:
    """节假日工具测试"""

    def test_is_weekend(self):
        """测试周末判断"""
        saturday = date(2026, 2, 14)  # 周六
        sunday = date(2026, 2, 15)    # 周日
        monday = date(2026, 2, 16)    # 周一
        
        assert is_holiday(saturday) is True
        assert is_holiday(sunday) is True
        assert is_holiday(monday) is False

    def test_is_chinese_holiday(self):
        """测试中国法定节假日"""
        spring_festival = date(2026, 1, 1)  # 春节
        
        # 需要Mock节假日配置
        with patch('app.utils.holiday_utils.CHINESE_HOLIDAYS', [date(2026, 1, 1)]):
            assert is_holiday(spring_festival) is True

    def test_get_working_days(self):
        """测试工作日计算"""
        start_date = date(2026, 2, 16)  # 周一
        end_date = date(2026, 2, 22)    # 周日
        
        working_days = get_working_days(start_date, end_date)
        
        # 周一到周日，应该有5个工作日
        assert working_days == 5

    def test_get_working_days_with_holidays(self):
        """测试包含节假日的工作日计算"""
        start_date = date(2026, 2, 16)
        end_date = date(2026, 2, 22)
        
        holidays = [date(2026, 2, 18)]  # 周三是假日
        
        working_days = get_working_days(
            start_date,
            end_date,
            exclude_holidays=holidays
        )
        
        # 5个工作日 - 1个假日 = 4天
        assert working_days == 4

    def test_add_working_days(self):
        """测试添加工作日"""
        from app.utils.holiday_utils import add_working_days
        
        start = date(2026, 2, 16)  # 周一
        
        result = add_working_days(start, 5)
        
        # 加5个工作日应该到下周一（跳过周末）
        assert result == date(2026, 2, 23)


class TestPinyinUtils:
    """拼音工具测试"""

    def test_chinese_to_pinyin(self):
        """测试中文转拼音"""
        text = "项目管理系统"
        
        pinyin = to_pinyin(text)
        
        assert 'xiang' in pinyin.lower()
        assert 'mu' in pinyin.lower()

    def test_get_name_initials(self):
        """测试获取姓名首字母"""
        name = "张三"
        
        initials = get_initials(name)
        
        assert initials == 'ZS'

    def test_get_initials_english(self):
        """测试英文名首字母"""
        name = "John Smith"
        
        initials = get_initials(name)
        
        assert initials == 'JS'

    def test_mixed_chinese_english(self):
        """测试中英文混合"""
        text = "ABC项目"
        
        pinyin = to_pinyin(text)
        
        assert 'ABC' in pinyin
        assert 'xiang' in pinyin.lower() or 'mu' in pinyin.lower()


class TestCacheDecorator:
    """缓存装饰器测试"""

    def test_function_result_cached(self):
        """测试函数结果被缓存"""
        from app.utils.cache_decorator import cached
        
        call_count = {'count': 0}
        
        @cached(ttl=60)
        def expensive_function(x):
            call_count['count'] += 1
            return x * 2
        
        # 第一次调用
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count['count'] == 1
        
        # 第二次调用，应该使用缓存
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count['count'] == 1  # 没有增加

    def test_cache_different_params(self):
        """测试不同参数不使用缓存"""
        from app.utils.cache_decorator import cached
        
        call_count = {'count': 0}
        
        @cached(ttl=60)
        def func(x):
            call_count['count'] += 1
            return x * 2
        
        func(5)
        func(10)  # 不同参数
        
        assert call_count['count'] == 2


class TestBatchOperations:
    """批量操作工具测试"""

    def test_batch_create(self):
        """测试批量创建"""
        from app.utils.batch_operations import batch_create
        
        items = [
            {'name': f'Item {i}', 'value': i}
            for i in range(100)
        ]
        
        result = batch_create(items, batch_size=20)
        
        assert result['total'] == 100
        assert result['batches'] == 5

    def test_batch_update(self):
        """测试批量更新"""
        from app.utils.batch_operations import batch_update
        
        updates = [
            {'id': i, 'status': 'completed'}
            for i in range(50)
        ]
        
        result = batch_update(updates, batch_size=10)
        
        assert result['updated_count'] == 50

    def test_batch_delete(self):
        """测试批量删除"""
        from app.utils.batch_operations import batch_delete
        
        ids = list(range(1, 101))
        
        result = batch_delete(ids, batch_size=25)
        
        assert result['deleted_count'] == 100


class TestDataValidation:
    """数据验证测试"""

    def test_validate_email(self):
        """测试邮箱验证"""
        from app.utils.validators import is_valid_email
        
        assert is_valid_email('user@example.com') is True
        assert is_valid_email('invalid-email') is False
        assert is_valid_email('user@') is False

    def test_validate_phone(self):
        """测试手机号验证"""
        from app.utils.validators import is_valid_phone
        
        assert is_valid_phone('13800138000') is True
        assert is_valid_phone('12345678901') is True
        assert is_valid_phone('1234567890') is False

    def test_validate_date_range(self):
        """测试日期范围验证"""
        from app.utils.validators import is_valid_date_range
        
        start = date(2026, 1, 1)
        end = date(2026, 12, 31)
        
        assert is_valid_date_range(start, end) is True
        assert is_valid_date_range(end, start) is False

    def test_sanitize_input(self):
        """测试输入清理"""
        from app.utils.validators import sanitize_input
        
        dangerous_input = "<script>alert('xss')</script>"
        
        safe_input = sanitize_input(dangerous_input)
        
        assert '<script>' not in safe_input
        assert 'alert' not in safe_input
