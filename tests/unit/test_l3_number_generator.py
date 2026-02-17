# -*- coding: utf-8 -*-
"""
L3组 单元测试 - app/utils/number_generator.py
NumberGenerator 类：纯逻辑（无需 db）
其他函数：mock db.query
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.utils.number_generator import (
    NumberGenerator,
    generate_calculation_code,
    generate_customer_code,
    generate_employee_code,
    generate_machine_code,
    generate_material_code,
    generate_monthly_no,
    generate_sequential_no,
)


# =============================================================================
# NumberGenerator 类 - 纯逻辑，不需要 DB
# =============================================================================

class TestNumberGeneratorClass:

    def setup_method(self):
        self.gen = NumberGenerator()

    def test_generate_project_number_format(self):
        result = self.gen.generate_project_number("PRJ", "20260217", 1)
        assert result == "PRJ-20260217-0001"

    def test_generate_project_number_sequence_padded(self):
        result = self.gen.generate_project_number("ECN", "260217", 42)
        assert result == "ECN-260217-0042"

    def test_generate_project_number_large_sequence(self):
        result = self.gen.generate_project_number("PJ", "260101", 9999)
        assert result == "PJ-260101-9999"

    def test_generate_unique_number_format(self):
        result = self.gen.generate_unique_number("TEST")
        assert result.startswith("TEST-")
        parts = result.split("-")
        assert len(parts) == 3  # TEST, timestamp, rand

    def test_generate_unique_number_different_each_time(self):
        r1 = self.gen.generate_unique_number("X")
        r2 = self.gen.generate_unique_number("X")
        # 有极小概率相同，但通常不同
        assert r1.startswith("X-")
        assert r2.startswith("X-")

    def test_parse_project_number_standard(self):
        info = self.gen.parse_project_number("PRJ-20260216-0042")
        assert info["prefix"] == "PRJ"
        assert info["date_str"] == "20260216"
        assert info["sequence"] == 42

    def test_parse_project_number_short(self):
        info = self.gen.parse_project_number("PJ-260101-007")
        assert info["prefix"] == "PJ"
        assert info["date_str"] == "260101"
        assert info["sequence"] == 7

    def test_parse_project_number_no_dash(self):
        info = self.gen.parse_project_number("NODASH")
        assert info["prefix"] == "NODASH"
        assert info["date_str"] == ""
        assert info["sequence"] == 0


# =============================================================================
# generate_sequential_no - mock db
# =============================================================================

def make_mock_db(first_result=None):
    """构造支持链式调用的 mock db"""
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    # apply_like_filter 会修改 query，最后 order_by().first()
    q.order_by.return_value.first.return_value = first_result
    # apply_like_filter returns same mock
    q.filter.return_value = q
    return db, q


class MockModel:
    """Mock SQLAlchemy model - columns must support .desc() for order_by"""
    __tablename__ = "test_table"

    class _Col:
        def desc(self):
            return self
        def asc(self):
            return self

    sequential_no = _Col()


class TestGenerateSequentialNo:

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_first_record_with_separator(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "260217"
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_sequential_no(db, MockModel, "sequential_no", "ECN",
                                        separator="-", seq_length=3)
        assert result == "ECN-260217-001"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_first_record_without_separator(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "260217"
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_sequential_no(db, MockModel, "sequential_no", "PJ",
                                        separator="", use_date=True, seq_length=3)
        assert result == "PJ260217001"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_increment_sequence(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "260217"
        mock_record = MagicMock()
        mock_record.sequential_no = "ECN-260217-005"
        db, q = make_mock_db(first_result=mock_record)
        mock_filter.return_value = q

        result = generate_sequential_no(db, MockModel, "sequential_no", "ECN",
                                        separator="-", seq_length=3)
        assert result == "ECN-260217-006"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_without_date(self, mock_dt, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_sequential_no(db, MockModel, "sequential_no", "TEST",
                                        use_date=False, separator="-", seq_length=3)
        assert result == "TEST-001"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_custom_seq_length_5(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "260217"
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_sequential_no(db, MockModel, "sequential_no", "X",
                                        separator="-", seq_length=5)
        seq_part = result.split("-")[-1]
        assert len(seq_part) == 5
        assert seq_part == "00001"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_no_separator_no_date(self, mock_dt, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_sequential_no(db, MockModel, "sequential_no", "ID",
                                        use_date=False, separator="", seq_length=4)
        assert result == "ID0001"


# =============================================================================
# generate_monthly_no
# =============================================================================

class TestGenerateMonthlyNo:

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_first_monthly_record(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "2602"
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_monthly_no(db, MockModel, "sequential_no", "L",
                                     separator="-", seq_length=3)
        assert result == "L2602-001"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_monthly_increment(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "2602"
        mock_record = MagicMock()
        mock_record.sequential_no = "L2602-010"
        db, q = make_mock_db(first_result=mock_record)
        mock_filter.return_value = q

        result = generate_monthly_no(db, MockModel, "sequential_no", "L",
                                     separator="-", seq_length=3)
        assert result == "L2602-011"


# =============================================================================
# generate_employee_code
# =============================================================================

class TestGenerateEmployeeCode:

    @patch("app.utils.number_generator.apply_like_filter")
    def test_first_employee_code(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_employee_code(db)
        assert result == "EMP-00001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_increment_employee_code(self, mock_filter):
        mock_emp = MagicMock()
        mock_emp.employee_code = "EMP-00005"
        db, q = make_mock_db(first_result=mock_emp)
        mock_filter.return_value = q

        result = generate_employee_code(db)
        assert result == "EMP-00006"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_employee_code_prefix(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_employee_code(db)
        assert result.startswith("EMP-")

    @patch("app.utils.number_generator.apply_like_filter")
    def test_employee_code_length(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_employee_code(db)
        # "EMP-" + 5 digits
        assert len(result) == 9


# =============================================================================
# generate_customer_code
# =============================================================================

class TestGenerateCustomerCode:

    @patch("app.utils.number_generator.apply_like_filter")
    def test_first_customer_code(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_customer_code(db)
        assert result == "CUS-0000001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_increment_customer_code(self, mock_filter):
        mock_cust = MagicMock()
        mock_cust.customer_code = "CUS-0000010"
        db, q = make_mock_db(first_result=mock_cust)
        mock_filter.return_value = q

        result = generate_customer_code(db)
        assert result == "CUS-0000011"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_customer_code_prefix(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_customer_code(db)
        assert result.startswith("CUS-")


# =============================================================================
# generate_material_code
# =============================================================================

class TestGenerateMaterialCode:

    @patch("app.utils.number_generator.apply_like_filter")
    def test_material_code_me_category(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_material_code(db, "ME-01-01")
        assert result == "MAT-ME-00001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_material_code_el_category(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_material_code(db, "EL-02-03")
        assert result == "MAT-EL-00001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_material_code_no_category_defaults_ot(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_material_code(db)
        assert result == "MAT-OT-00001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_material_code_increment(self, mock_filter):
        mock_mat = MagicMock()
        mock_mat.material_code = "MAT-ME-00005"
        db, q = make_mock_db(first_result=mock_mat)
        mock_filter.return_value = q

        result = generate_material_code(db, "ME-01-01")
        assert result == "MAT-ME-00006"


# =============================================================================
# generate_machine_code
# =============================================================================

class TestGenerateMachineCode:

    @patch("app.utils.number_generator.apply_like_filter")
    def test_first_machine_code(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_machine_code(db, "PJ250708001")
        assert result == "PJ250708001-PN001"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_machine_code_increment(self, mock_filter):
        mock_machine = MagicMock()
        mock_machine.machine_code = "PJ250708001-PN003"
        db, q = make_mock_db(first_result=mock_machine)
        mock_filter.return_value = q

        result = generate_machine_code(db, "PJ250708001")
        assert result == "PJ250708001-PN004"

    @patch("app.utils.number_generator.apply_like_filter")
    def test_machine_code_format(self, mock_filter):
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_machine_code(db, "PJ260101001")
        assert result.startswith("PJ260101001-PN")
        assert len(result.split("-PN")[1]) == 3


# =============================================================================
# generate_calculation_code
# =============================================================================

class TestGenerateCalculationCode:

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_first_calculation_code(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "260217"
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_calculation_code(db)
        assert result == "BC-260217-001"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_calculation_code_increment(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "260217"
        mock_calc = MagicMock()
        mock_calc.calculation_code = "BC-260217-005"
        db, q = make_mock_db(first_result=mock_calc)
        mock_filter.return_value = q

        result = generate_calculation_code(db)
        assert result == "BC-260217-006"

    @patch("app.utils.number_generator.apply_like_filter")
    @patch("app.utils.number_generator.datetime")
    def test_calculation_code_prefix(self, mock_dt, mock_filter):
        mock_dt.now.return_value.strftime.return_value = "260217"
        db, q = make_mock_db(first_result=None)
        mock_filter.return_value = q

        result = generate_calculation_code(db)
        assert result.startswith("BC-")
