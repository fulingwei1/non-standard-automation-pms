# -*- coding: utf-8 -*-
"""
编码配置模块单元测试
"""


from app.utils.code_config import (
    CODE_PREFIX,
    MATERIAL_CATEGORY_CODES,
    SEQ_LENGTH,
    VALID_MATERIAL_CATEGORY_CODES,
    get_material_category_code,
    validate_material_category_code,
)


class TestCodePrefix:
    """测试编码前缀配置"""

    def test_code_prefix_is_dict(self):
        """测试 CODE_PREFIX 是字典"""
        assert isinstance(CODE_PREFIX, dict)

    def test_code_prefix_contains_employee(self):
        """测试包含员工前缀"""
        assert "EMPLOYEE" in CODE_PREFIX
        assert CODE_PREFIX["EMPLOYEE"] == "EMP"

    def test_code_prefix_contains_customer(self):
        """测试包含客户前缀"""
        assert "CUSTOMER" in CODE_PREFIX
        assert CODE_PREFIX["CUSTOMER"] == "CUS"

    def test_code_prefix_contains_material(self):
        """测试包含物料前缀"""
        assert "MATERIAL" in CODE_PREFIX
        assert CODE_PREFIX["MATERIAL"] == "MAT"

    def test_code_prefix_contains_project(self):
        """测试包含项目前缀"""
        assert "PROJECT" in CODE_PREFIX
        assert CODE_PREFIX["PROJECT"] == "PJ"

    def test_code_prefix_contains_machine(self):
        """测试包含设备前缀"""
        assert "MACHINE" in CODE_PREFIX
        assert CODE_PREFIX["MACHINE"] == "PN"


class TestSeqLength:
    """测试序号长度配置"""

    def test_seq_length_is_dict(self):
        """测试 SEQ_LENGTH 是字典"""
        assert isinstance(SEQ_LENGTH, dict)

    def test_seq_length_employee(self):
        """测试员工序号长度"""
        assert "EMPLOYEE" in SEQ_LENGTH
        assert SEQ_LENGTH["EMPLOYEE"] == 5

    def test_seq_length_customer(self):
        """测试客户序号长度"""
        assert "CUSTOMER" in SEQ_LENGTH
        assert SEQ_LENGTH["CUSTOMER"] == 7

    def test_seq_length_material(self):
        """测试物料序号长度"""
        assert "MATERIAL" in SEQ_LENGTH
        assert SEQ_LENGTH["MATERIAL"] == 5

    def test_seq_length_project(self):
        """测试项目序号长度"""
        assert "PROJECT" in SEQ_LENGTH
        assert SEQ_LENGTH["PROJECT"] == 3

    def test_seq_length_machine(self):
        """测试设备序号长度"""
        assert "MACHINE" in SEQ_LENGTH
        assert SEQ_LENGTH["MACHINE"] == 3


class TestMaterialCategoryCodes:
    """测试物料类别码配置"""

    def test_material_category_codes_is_dict(self):
        """测试 MATERIAL_CATEGORY_CODES 是字典"""
        assert isinstance(MATERIAL_CATEGORY_CODES, dict)

    def test_material_category_codes_contains_mechanical(self):
        """测试包含机械件类别码"""
        assert "ME" in MATERIAL_CATEGORY_CODES
        assert MATERIAL_CATEGORY_CODES["ME"] == "机械件"

    def test_material_category_codes_contains_electrical(self):
        """测试包含电气件类别码"""
        assert "EL" in MATERIAL_CATEGORY_CODES
        assert MATERIAL_CATEGORY_CODES["EL"] == "电气件"

    def test_material_category_codes_contains_pneumatic(self):
        """测试包含气动件类别码"""
        assert "PN" in MATERIAL_CATEGORY_CODES
        assert MATERIAL_CATEGORY_CODES["PN"] == "气动件"

    def test_material_category_codes_contains_standard(self):
        """测试包含标准件类别码"""
        assert "ST" in MATERIAL_CATEGORY_CODES
        assert MATERIAL_CATEGORY_CODES["ST"] == "标准件"

    def test_material_category_codes_contains_other(self):
        """测试包含其他类别码"""
        assert "OT" in MATERIAL_CATEGORY_CODES
        assert MATERIAL_CATEGORY_CODES["OT"] == "其他"

    def test_material_category_codes_contains_trade(self):
        """测试包含贸易件类别码"""
        assert "TR" in MATERIAL_CATEGORY_CODES
        assert MATERIAL_CATEGORY_CODES["TR"] == "贸易件"


class TestValidMaterialCategoryCodes:
    """测试有效物料类别码验证"""

    def test_valid_material_category_codes_is_set(self):
        """测试 VALID_MATERIAL_CATEGORY_CODES 是集合"""
        assert isinstance(VALID_MATERIAL_CATEGORY_CODES, set)

    def test_valid_material_category_codes_contains_all_codes(self):
        """测试包含所有物料类别码"""
        assert "ME" in VALID_MATERIAL_CATEGORY_CODES
        assert "EL" in VALID_MATERIAL_CATEGORY_CODES
        assert "PN" in VALID_MATERIAL_CATEGORY_CODES
        assert "ST" in VALID_MATERIAL_CATEGORY_CODES
        assert "OT" in VALID_MATERIAL_CATEGORY_CODES
        assert "TR" in VALID_MATERIAL_CATEGORY_CODES

    def test_valid_material_category_codes_count(self):
        """测试类别码数量"""
        assert len(VALID_MATERIAL_CATEGORY_CODES) == 6


class TestGetMaterialCategoryCode:
    """测试 get_material_category_code 函数"""

    def test_mechanical_code(self):
        """测试提取机械件类别码"""
        category_code = get_material_category_code("ME-01-01")
        assert category_code == "ME"

    def test_electrical_code(self):
        """测试提取电气件类别码"""
        category_code = get_material_category_code("EL-02-03")
        assert category_code == "EL"

    def test_pneumatic_code(self):
        """测试提取气动件类别码"""
        category_code = get_material_category_code("PN-01-01")
        assert category_code == "PN"

    def test_standard_code(self):
        """测试提取标准件类别码"""
        category_code = get_material_category_code("ST-01-01")
        assert category_code == "ST"

    def test_trade_code(self):
        """测试提取贸易件类别码"""
        category_code = get_material_category_code("TR-01-01")
        assert category_code == "TR"

    def test_lowercase_code(self):
        """测试小写类别码自动转大写"""
        category_code = get_material_category_code("me-01-01")
        assert category_code == "ME"

    def test_empty_string_returns_other(self):
        """测试空字符串返回其他"""
        category_code = get_material_category_code("")
        assert category_code == "OT"

    def test_none_returns_other(self):
        """测试 None 返回其他"""
        category_code = get_material_category_code(None)
        assert category_code == "OT"

    def test_invalid_code_returns_other(self):
        """测试无效类别码返回其他"""
        category_code = get_material_category_code("XX-01-01")
        assert category_code == "OT"

    def test_code_without_separator(self):
        """测试无分隔符的类别码"""
        category_code = get_material_category_code("ME0101")
        assert category_code == "ME"

    def test_code_with_multiple_separators(self):
        """测试多个分隔符的类别码"""
        category_code = get_material_category_code("ME-01-02-03")
        assert category_code == "ME"


class TestValidateMaterialCategoryCode:
    """测试 validate_material_category_code 函数"""

    def test_validate_mechanical(self):
        """测试验证机械件类别码"""
        assert validate_material_category_code("ME") is True

    def test_validate_electrical(self):
        """测试验证电气件类别码"""
        assert validate_material_category_code("EL") is True

    def test_validate_pneumatic(self):
        """测试验证气动件类别码"""
        assert validate_material_category_code("PN") is True

    def test_validate_standard(self):
        """测试验证标准件类别码"""
        assert validate_material_category_code("ST") is True

    def test_validate_other(self):
        """测试验证其他类别码"""
        assert validate_material_category_code("OT") is True

    def test_validate_trade(self):
        """测试验证贸易件类别码"""
        assert validate_material_category_code("TR") is True

    def test_lowercase_validation(self):
        """测试小写类别码自动转大写验证"""
        assert validate_material_category_code("me") is True
        assert validate_material_category_code("el") is True
        assert validate_material_category_code("pn") is True

    def test_invalid_code(self):
        """测试无效类别码"""
        assert validate_material_category_code("XX") is False
        assert validate_material_category_code("AA") is False
        assert validate_material_category_code("123") is False

    def test_empty_string(self):
        """测试空字符串"""
        assert validate_material_category_code("") is False

    def test_whitespace_code(self):
        """测试空格类别码"""
        assert validate_material_category_code(" ") is False
