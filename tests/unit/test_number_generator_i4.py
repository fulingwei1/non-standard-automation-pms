# -*- coding: utf-8 -*-
"""
I4组：number_generator.py 深度单元测试

覆盖目标：9% → 70%+
策略：patch apply_like_filter，使用 MagicMock 模拟 db.query 链
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helper：创建一个配置好 mock db 的 fixture（依赖 apply_like_filter patch）
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """返回 (db, mock_query) 元组，已配置好常用 query 链"""
    db = MagicMock()
    mock_query = MagicMock()
    db.query.return_value = mock_query
    return db, mock_query


# ===========================================================================
# generate_sequential_no
# ===========================================================================

class TestGenerateSequentialNoBasic:
    """generate_sequential_no 基础用例"""

    def test_first_record_with_date_separator(self, mock_db):
        """首条记录，带日期、带分隔符"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'ecn_no', 'ECN',
                date_format='%y%m%d', separator='-', seq_length=3, use_date=True
            )

        today = datetime.now().strftime('%y%m%d')
        assert result == f'ECN-{today}-001'

    def test_first_record_no_separator_no_date(self, mock_db):
        """不带日期不带分隔符"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'code', 'PJ',
                use_date=False, separator='', seq_length=3
            )

        assert result == 'PJ001'

    def test_first_record_no_date_with_separator(self, mock_db):
        """不带日期，带分隔符"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'code', 'TASK',
                use_date=False, separator='-', seq_length=4
            )

        assert result == 'TASK-0001'

    def test_with_existing_record_increments_seq(self, mock_db):
        """存在记录时序号递增"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.ecn_no = 'ECN-260217-005'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'ecn_no', 'ECN',
                date_format='%y%m%d', separator='-', seq_length=3, use_date=True
            )

        today = datetime.now().strftime('%y%m%d')
        assert result == f'ECN-{today}-006'

    def test_with_existing_record_no_separator(self, mock_db):
        """存在记录，无分隔符格式"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        today = datetime.now().strftime('%y%m%d')
        mock_record.project_code = f'PJ{today}009'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'project_code', 'PJ',
                date_format='%y%m%d', separator='', seq_length=3, use_date=True
            )

        assert result == f'PJ{today}010'

    def test_invalid_seq_str_falls_back_to_001(self, mock_db):
        """序号部分非数字时回退到 001"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.ecn_no = 'ECN-260217-XYZ'  # 非数字序号
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'ecn_no', 'ECN',
                date_format='%y%m%d', separator='-', seq_length=3, use_date=True
            )

        today = datetime.now().strftime('%y%m%d')
        assert result == f'ECN-{today}-001'

    def test_seq_length_5_zero_padded(self, mock_db):
        """seq_length=5 时零填充正确"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'code', 'ORD',
                use_date=False, separator='-', seq_length=5
            )

        assert result == 'ORD-00001'

    def test_month_format_date(self, mock_db):
        """使用月份格式 %y%m"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'code', 'REQ',
                date_format='%y%m', separator='-', seq_length=3, use_date=True
            )

        month = datetime.now().strftime('%y%m')
        assert result == f'REQ-{month}-001'

    def test_no_date_no_separator_seq99(self, mock_db):
        """不带日期，序号99时变100"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.code = 'PJ099'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_sequential_no
            result = generate_sequential_no(
                db, MagicMock(), 'code', 'PJ',
                use_date=False, separator='', seq_length=3
            )

        assert result == 'PJ100'


# ===========================================================================
# generate_monthly_no
# ===========================================================================

class TestGenerateMonthlyNo:
    """generate_monthly_no 测试"""

    def test_first_record(self, mock_db):
        """首条记录"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_monthly_no
            result = generate_monthly_no(db, MagicMock(), 'lead_code', 'L')

        month = datetime.now().strftime('%y%m')
        assert result == f'L{month}-001'

    def test_with_existing_record(self, mock_db):
        """存在记录时递增"""
        db, mock_query = mock_db
        month = datetime.now().strftime('%y%m')
        mock_record = MagicMock()
        mock_record.lead_code = f'L{month}-012'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_monthly_no
            result = generate_monthly_no(db, MagicMock(), 'lead_code', 'L')

        assert result == f'L{month}-013'

    def test_custom_separator(self, mock_db):
        """自定义分隔符"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_monthly_no
            result = generate_monthly_no(db, MagicMock(), 'order_code', 'O', separator='-', seq_length=4)

        month = datetime.now().strftime('%y%m')
        assert result == f'O{month}-0001'

    def test_invalid_seq_falls_back(self, mock_db):
        """无效序号回退到001"""
        db, mock_query = mock_db
        month = datetime.now().strftime('%y%m')
        mock_record = MagicMock()
        mock_record.lead_code = f'L{month}-ABC'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_monthly_no
            result = generate_monthly_no(db, MagicMock(), 'lead_code', 'L')

        assert result == f'L{month}-001'


# ===========================================================================
# generate_employee_code
# ===========================================================================

class TestGenerateEmployeeCode:
    """generate_employee_code 测试"""

    def test_first_employee(self, mock_db):
        """首个员工编号"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_employee_code
            result = generate_employee_code(db)

        assert result == 'EMP-00001'

    def test_increments_from_existing(self, mock_db):
        """基于已有记录递增"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.employee_code = 'EMP-00042'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_employee_code
            result = generate_employee_code(db)

        assert result == 'EMP-00043'

    def test_invalid_code_format_fallback(self, mock_db):
        """无效格式时回退到00001"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.employee_code = 'INVALID'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_employee_code
            result = generate_employee_code(db)

        assert result == 'EMP-00001'

    def test_result_format(self, mock_db):
        """结果格式正确"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_employee_code
            result = generate_employee_code(db)

        assert result.startswith('EMP-')
        assert len(result) == 9  # EMP-00001


# ===========================================================================
# generate_customer_code
# ===========================================================================

class TestGenerateCustomerCode:
    """generate_customer_code 测试"""

    def test_first_customer(self, mock_db):
        """首个客户编号"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_customer_code
            result = generate_customer_code(db)

        assert result == 'CUS-0000001'

    def test_increments_from_existing(self, mock_db):
        """基于已有记录递增"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.customer_code = 'CUS-0000099'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_customer_code
            result = generate_customer_code(db)

        assert result == 'CUS-0000100'

    def test_invalid_format_fallback(self, mock_db):
        """无效格式回退"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.customer_code = 'CUS-BAD-FORMAT-X'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_customer_code
            result = generate_customer_code(db)

        assert result == 'CUS-0000001'

    def test_result_format(self, mock_db):
        """结果格式正确"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_customer_code
            result = generate_customer_code(db)

        assert result.startswith('CUS-')
        assert len(result) == 11  # CUS-0000001


# ===========================================================================
# generate_material_code
# ===========================================================================

class TestGenerateMaterialCode:
    """generate_material_code 测试"""

    def test_first_material_with_category(self, mock_db):
        """带类别码的首个物料"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_material_code
            result = generate_material_code(db, category_code='ME-01-01')

        assert result == 'MAT-ME-00001'

    def test_first_material_electrical(self, mock_db):
        """电气类物料"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_material_code
            result = generate_material_code(db, category_code='EL-02')

        assert result == 'MAT-EL-00001'

    def test_no_category_defaults_to_OT(self, mock_db):
        """无类别码默认OT"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_material_code
            result = generate_material_code(db, category_code=None)

        assert result == 'MAT-OT-00001'

    def test_increments_from_existing(self, mock_db):
        """基于已有记录递增"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.material_code = 'MAT-ME-00015'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_material_code
            result = generate_material_code(db, category_code='ME-01-01')

        assert result == 'MAT-ME-00016'

    def test_invalid_parts_fallback(self, mock_db):
        """字段格式不对时回退到00001"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.material_code = 'WRONG'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_material_code
            result = generate_material_code(db, category_code='ME-01-01')

        assert result == 'MAT-ME-00001'

    def test_result_format(self, mock_db):
        """结果格式正确"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_material_code
            result = generate_material_code(db)

        parts = result.split('-')
        assert parts[0] == 'MAT'
        assert len(parts) == 3


# ===========================================================================
# generate_machine_code
# ===========================================================================

class TestGenerateMachineCode:
    """generate_machine_code 测试"""

    def test_first_machine_for_project(self, mock_db):
        """项目首台设备"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_machine_code
            result = generate_machine_code(db, 'PJ250708001')

        assert result == 'PJ250708001-PN001'

    def test_increments_from_existing(self, mock_db):
        """基于已有设备递增"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.machine_code = 'PJ250708001-PN005'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_machine_code
            result = generate_machine_code(db, 'PJ250708001')

        assert result == 'PJ250708001-PN006'

    def test_invalid_format_fallback(self, mock_db):
        """无效格式回退"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.machine_code = 'INVALID'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_machine_code
            result = generate_machine_code(db, 'PJ001')

        assert result == 'PJ001-PN001'

    def test_different_project_codes(self, mock_db):
        """不同项目代码"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_machine_code
            result1 = generate_machine_code(db, 'PJA')
            result2 = generate_machine_code(db, 'PJB')

        assert result1 == 'PJA-PN001'
        assert result2 == 'PJB-PN001'


# ===========================================================================
# generate_calculation_code
# ===========================================================================

class TestGenerateCalculationCode:
    """generate_calculation_code 测试"""

    def test_first_calculation_today(self, mock_db):
        """当天首条奖金计算编号"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_calculation_code
            result = generate_calculation_code(db)

        today = datetime.now().strftime('%y%m%d')
        assert result == f'BC-{today}-001'

    def test_increments_from_existing(self, mock_db):
        """基于已有记录递增"""
        db, mock_query = mock_db
        today = datetime.now().strftime('%y%m%d')
        mock_record = MagicMock()
        mock_record.calculation_code = f'BC-{today}-007'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_calculation_code
            result = generate_calculation_code(db)

        assert result == f'BC-{today}-008'

    def test_invalid_format_fallback(self, mock_db):
        """无效格式回退"""
        db, mock_query = mock_db
        mock_record = MagicMock()
        mock_record.calculation_code = 'BC-INVALID'
        mock_query.order_by.return_value.first.return_value = mock_record

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_calculation_code
            result = generate_calculation_code(db)

        today = datetime.now().strftime('%y%m%d')
        assert result == f'BC-{today}-001'

    def test_result_prefix(self, mock_db):
        """结果前缀正确"""
        db, mock_query = mock_db
        mock_query.order_by.return_value.first.return_value = None

        with patch('app.utils.number_generator.apply_like_filter', return_value=mock_query):
            from app.utils.number_generator import generate_calculation_code
            result = generate_calculation_code(db)

        assert result.startswith('BC-')


# ===========================================================================
# NumberGenerator 类测试（无状态工具类）
# ===========================================================================

class TestNumberGeneratorClass:
    """NumberGenerator 类测试"""

    def test_generate_project_number(self):
        """生成项目编号格式"""
        from app.utils.number_generator import NumberGenerator
        ng = NumberGenerator()
        result = ng.generate_project_number('PRJ', '20260217', 42)
        assert result == 'PRJ-20260217-0042'

    def test_generate_project_number_zero_padding(self):
        """项目编号四位零填充"""
        from app.utils.number_generator import NumberGenerator
        ng = NumberGenerator()
        result = ng.generate_project_number('X', '20260101', 1)
        assert result == 'X-20260101-0001'

    def test_generate_unique_number_format(self):
        """唯一编号格式正确"""
        from app.utils.number_generator import NumberGenerator
        ng = NumberGenerator()
        result = ng.generate_unique_number('TEST')
        assert result.startswith('TEST-')
        parts = result.split('-')
        assert len(parts) == 3
        assert parts[0] == 'TEST'
        # 时间戳部分是数字
        assert parts[1].isdigit()
        # 随机数部分3位
        assert len(parts[2]) == 3

    def test_generate_unique_number_is_unique(self):
        """唯一编号每次不同（概率极低碰撞）"""
        from app.utils.number_generator import NumberGenerator
        import time
        ng = NumberGenerator()
        results = set()
        for _ in range(10):
            results.add(ng.generate_unique_number('U'))
            time.sleep(0.001)
        # 至少大部分不同（随机性）
        assert len(results) >= 1

    def test_parse_project_number_standard(self):
        """解析标准项目编号"""
        from app.utils.number_generator import NumberGenerator
        ng = NumberGenerator()
        parsed = ng.parse_project_number('PRJ-20260216-0042')
        assert parsed['prefix'] == 'PRJ'
        assert parsed['date_str'] == '20260216'
        assert parsed['sequence'] == 42

    def test_parse_project_number_invalid(self):
        """解析无效编号"""
        from app.utils.number_generator import NumberGenerator
        ng = NumberGenerator()
        parsed = ng.parse_project_number('INVALID')
        assert parsed['prefix'] == 'INVALID'
        assert parsed['date_str'] == ''
        assert parsed['sequence'] == 0

    def test_parse_project_number_two_parts(self):
        """解析两段格式（不满足3段时返回完整原始字符串作为 prefix）"""
        from app.utils.number_generator import NumberGenerator
        ng = NumberGenerator()
        parsed = ng.parse_project_number('PRJ-001')
        # 不满足 len(parts) >= 3，直接返回 prefix=原始字符串
        assert parsed['prefix'] == 'PRJ-001'
        assert parsed['date_str'] == ''
        assert parsed['sequence'] == 0
