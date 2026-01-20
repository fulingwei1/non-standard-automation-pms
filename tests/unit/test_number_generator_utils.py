# -*- coding: utf-8 -*-
"""
编号生成工具单元测试
测试 app/utils/number_generator.py
目标覆盖率: 8% -> 60%+
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

# 延迟导入以避免SQLAlchemy关系配置问题


class TestGenerateSequentialNo:
    """测试 generate_sequential_no 函数"""

    @pytest.fixture
    def mock_model(self):
        """创建模拟模型类"""
        model = MagicMock()
        model.id = 1
        model.no_field = "TEST-250115-001"
        return model

    def test_first_record_with_separator(self):
        """测试第一个记录（带分隔符）"""
        from app.utils.number_generator import generate_sequential_no
        
        db = MagicMock()
        # 模拟没有现有记录
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_no(
            db, MagicMock, "no_field", "TEST", separator="-"
        )

        assert result.startswith("TEST-")
        assert "-" in result
        assert result.endswith("-001")

    def test_first_record_without_separator(self):
        """测试第一个记录（不带分隔符）"""
        from app.utils.number_generator import generate_sequential_no
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_no(
            db, MagicMock, "no_field", "TEST", separator="", use_date=True
        )

        assert result.startswith("TEST")
        assert "-" not in result
        assert result.endswith("001")

    def test_increment_sequence(self, mock_model):
        """测试序号递增"""
        from app.utils.number_generator import generate_sequential_no
        
        db = MagicMock()
        # 模拟已有记录
        mock_model.no_field = "TEST-250115-005"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_model

        result = generate_sequential_no(
            db, MagicMock, "no_field", "TEST", separator="-"
        )

        assert result.endswith("-006")

    def test_without_date(self):
        """测试不使用日期"""
        from app.utils.number_generator import generate_sequential_no
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_no(
            db, MagicMock, "no_field", "TEST", use_date=False, separator="-"
        )

        assert result.startswith("TEST-")
        assert result.endswith("-001")
        # 不应该包含日期
        assert len(result.split("-")) == 2

    def test_custom_date_format(self):
        """测试自定义日期格式"""
        from app.utils.number_generator import generate_sequential_no
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_no(
            db,
            MagicMock,
            "no_field",
            "TEST",
            date_format="%Y%m%d",
            separator="-",
        )

        # 应该包含完整日期格式
        assert "2025" in result or "2024" in result

    def test_custom_seq_length(self):
        """测试自定义序号长度"""
        from app.utils.number_generator import generate_sequential_no
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_sequential_no(
            db, MagicMock, "no_field", "TEST", seq_length=5, separator="-"
        )

        # 序号应该是5位
        seq_part = result.split("-")[-1]
        assert len(seq_part) == 5
        assert seq_part == "00001"


class TestGenerateMonthlyNo:
    """测试 generate_monthly_no 函数"""

    def test_first_record_monthly(self):
        """测试月度编号第一个记录"""
        from app.utils.number_generator import generate_monthly_no
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_monthly_no(db, MagicMock, "no_field", "L")

        assert result.startswith("L")
        assert "-" in result
        assert result.endswith("-001")
        # 应该包含年月（yymm格式）
        assert len(result.split("-")) == 2

    def test_increment_monthly(self):
        """测试月度编号递增"""
        from app.utils.number_generator import generate_monthly_no
        
        db = MagicMock()
        mock_model = MagicMock()
        mock_model.no_field = "L2507-010"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_model

        result = generate_monthly_no(db, MagicMock, "no_field", "L")

        assert result.endswith("-011")


class TestGenerateEmployeeCode:
    """测试 generate_employee_code 函数"""

    @patch("app.utils.number_generator.Employee")
    def test_first_employee_code(self, mock_employee):
        """测试第一个员工编号"""
        from app.utils.number_generator import generate_employee_code
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_employee_code(db)

        assert result.startswith("EMP-")
        assert result.endswith("00001")

    @patch("app.utils.number_generator.Employee")
    def test_increment_employee_code(self, mock_employee):
        """测试员工编号递增"""
        from app.utils.number_generator import generate_employee_code
        
        db = MagicMock()
        mock_emp = MagicMock()
        mock_emp.employee_code = "EMP-00005"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_emp

        result = generate_employee_code(db)

        assert result == "EMP-00006"


class TestGenerateCustomerCode:
    """测试 generate_customer_code 函数"""

    @patch("app.utils.number_generator.Customer")
    def test_first_customer_code(self, mock_customer):
        """测试第一个客户编号"""
        from app.utils.number_generator import generate_customer_code
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_customer_code(db)

        assert result.startswith("CUST-")
        assert result.endswith("00001")

    @patch("app.utils.number_generator.Customer")
    def test_increment_customer_code(self, mock_customer):
        """测试客户编号递增"""
        from app.utils.number_generator import generate_customer_code
        
        db = MagicMock()
        mock_cust = MagicMock()
        mock_cust.customer_code = "CUST-00010"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_cust

        result = generate_customer_code(db)

        assert result == "CUST-00011"


class TestGenerateMaterialCode:
    """测试 generate_material_code 函数"""

    @patch("app.utils.number_generator.Material")
    @patch("app.utils.number_generator.get_material_category_code")
    def test_material_code_with_category(
        self, mock_get_code, mock_material
    ):
        """测试带分类的物料编号"""
        from app.utils.number_generator import generate_material_code
        
        db = MagicMock()
        mock_get_code.return_value = "ELEC"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_material_code(db, "ELECTRICAL")

        assert result.startswith("MAT-")
        assert "ELEC" in result
        assert "-" in result

    @patch("app.utils.number_generator.Material")
    @patch("app.utils.number_generator.get_material_category_code")
    def test_material_code_invalid_category(
        self, mock_get_code, mock_material
    ):
        """测试无效分类使用默认值"""
        from app.utils.number_generator import generate_material_code
        
        db = MagicMock()
        mock_get_code.return_value = None
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # 无效分类应该使用默认值"OT"
        result = generate_material_code(db, "INVALID_CATEGORY")
        
        assert result.startswith("MAT-")
        assert "OT" in result


class TestGenerateMachineCode:
    """测试 generate_machine_code 函数"""

    @patch("app.utils.number_generator.Machine")
    def test_first_machine_code(self, mock_machine):
        """测试第一个机台编号"""
        from app.utils.number_generator import generate_machine_code
        
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = generate_machine_code(db, project_code="PJ250708001")

        assert "PN" in result
        assert len(result) > 2

    @patch("app.utils.number_generator.Machine")
    def test_machine_code_increment(self, mock_machine):
        """测试机台编号递增"""
        from app.utils.number_generator import generate_machine_code
        
        db = MagicMock()
        mock_m = MagicMock()
        mock_m.machine_code = "PJ250708001-PN003"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_m

        result = generate_machine_code(db, project_code="PJ250708001")

        assert result == "PJ250708001-PN004"
