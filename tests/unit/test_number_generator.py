# -*- coding: utf-8 -*-
"""
Tests for number_generator utils
Covers: app/utils/number_generator.py
Coverage Target: 8% -> 60%+
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestNumberGenerator:
    """编号生成器测试"""

    @pytest.fixture
    def generator(self, db_session: Session):
        """创建生成器实例"""
        from app.utils.number_generator import NumberGenerator
        return NumberGenerator(db_session)

    def test_generate_sequential_no_first_record(self, generator, db_session: Session):
        """测试第一个记录的编号生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_sequential_no("PJ", date(2025, 1, 20), separator="-")

        assert result == "PJ-20250120-001"
        db_session.add.assert_called()

    def test_generate_sequential_no_with_existing(self, generator, db_session: Session):
        """测试已有记录时的编号生成"""
        mock_existing = MagicMock()
        mock_existing.serial_no = 5

        db_session.query.return_value.filter.return_value.first.return_value = mock_existing

        result = generator.generate_sequential_no("PJ", date(2025, 1, 20), separator="-")

        assert result == "PJ-20250120-006"

    def test_generate_sequential_no_without_separator(self, generator, db_session: Session):
        """测试不带分隔符的编号生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_sequential_no("PJ", date(2025, 1, 20), separator="")

        assert result == "PJ20250120001"

    def test_generate_sequential_no_no_date(self, generator, db_session: Session):
        """测试不带日期的编号生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_sequential_no("TASK", None, separator="-")

        assert result == "TASK-0001"

    def test_generate_monthly_no_first_record(self, generator, db_session: Session):
        """测试月编号第一个记录"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_monthly_no("PO", 2025, 1, prefix="PO")

        assert result == "PO-202501-001"

    def test_generate_monthly_no_with_existing(self, generator, db_session: Session):
        """测试月编号已有记录"""
        mock_existing = MagicMock()
        mock_existing.monthly_no = 15

        db_session.query.return_value.filter.return_value.first.return_value = mock_existing

        result = generator.generate_monthly_no("PO", 2025, 1, prefix="PO")

        assert result == "PO-202501-016"

    def test_generate_employee_code_first(self, generator, db_session: Session):
        """测试员工编号第一个记录"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_employee_code()

        assert result.startswith("EMP")
        assert len(result) == 10

    def test_generate_employee_code_with_existing(self, generator, db_session: Session):
        """测试员工编号已有记录"""
        mock_existing = MagicMock()
        mock_existing.employee_code = "EMP000050"

        db_session.query.return_value.filter.return_value.first.return_value = mock_existing

        result = generator.generate_employee_code()

        assert result == "EMP000051"

    def test_generate_customer_code(self, generator, db_session: Session):
        """测试客户编号生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_customer_code()

        assert result.startswith("CUS")

    def test_generate_material_code(self, generator, db_session: Session):
        """测试物料编号生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_material_code(category="ME")

        assert result.startswith("ME")

    def test_generate_material_code_default_category(self, generator, db_session: Session):
        """测试物料编号默认类别"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_material_code()

        assert result.startswith("MAT")

    def test_generate_machine_code(self, generator, db_session: Session):
        """测试机台编号生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_machine_code()

        assert result.startswith("PN")

    def test_generate_machine_code_with_existing(self, generator, db_session: Session):
        """测试机台编号已有记录"""
        mock_existing = MagicMock()
        mock_existing.machine_code = "PN099"

        db_session.query.return_value.filter.return_value.first.return_value = mock_existing

        result = generator.generate_machine_code()

        assert result == "PN100"

    def test_generate_calculation_code(self, generator, db_session: Session):
        """测试计算编号生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_calculation_code()

        assert result.startswith("CALC")


class TestNumberGeneratorPadding:
    """编号填充测试"""

    @pytest.fixture
    def generator(self, db_session: Session):
        from app.utils.number_generator import NumberGenerator
        return NumberGenerator(db_session)

    def test_padding_zeros(self, generator, db_session: Session):
        """测试零填充"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_sequential_no("TEST", None, separator="-", padding=4)

        assert result == "TEST--0001"

    def test_padding_length(self, generator, db_session: Session):
        """测试填充长度"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_sequential_no("TEST", None, separator="-", padding=6)

        assert "-000001" in result


class TestNumberGeneratorCustomPrefix:
    """自定义前缀测试"""

    @pytest.fixture
    def generator(self, db_session: Session):
        from app.utils.number_generator import NumberGenerator
        return NumberGenerator(db_session)

    def test_custom_prefix(self, generator, db_session: Session):
        """测试自定义前缀"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_sequential_no(
            "CUSTOM", date(2025, 1, 20),
            prefix="PRE", separator="-"
        )

        assert result.startswith("PRE-20250120")

    def test_custom_prefix_no_date(self, generator, db_session: Session):
        """测试无日期的自定义前缀"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = generator.generate_sequential_no(
            "CUSTOM", None,
            prefix="PRE", separator="-"
        )

        assert result.startswith("PRE-")
