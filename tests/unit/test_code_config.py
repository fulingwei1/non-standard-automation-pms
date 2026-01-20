# -*- coding: utf-8 -*-
"""
Tests for code_config utils
Covers: app/utils/code_config.py
Coverage Target: 43% -> 70%+
"""

import pytest


class TestCodeConfig:
    """编号配置测试"""

    def test_get_material_category_code(self):
        """测试获取物料类别编码"""
        from app.utils.code_config import get_material_category_code
        
        result = get_material_category_code("电机")
        assert result is not None

    def test_validate_material_category_code(self):
        """测试验证物料类别编码"""
        from app.utils.code_config import validate_material_category_code
        
        # 有效编码
        assert validate_material_category_code("ME") is True
        assert validate_material_category_code("EL") is True
        
        # 无效编码
        assert validate_material_category_code("INVALID") is False

    def test_code_prefix(self):
        """测试编号前缀"""
        from app.utils.code_config import CODE_PREFIX
        
        assert CODE_PREFIX is not None
        assert isinstance(CODE_PREFIX, dict)

    def test_seq_length(self):
        """测试序号长度"""
        from app.utils.code_config import SEQ_LENGTH
        
        assert SEQ_LENGTH is not None
        assert isinstance(SEQ_LENGTH, dict)


class TestCodeConfigHelpers:
    """编号配置辅助测试"""

    def test_get_material_category_code_empty(self):
        """测试空字符串类别"""
        from app.utils.code_config import get_material_category_code
        
        result = get_material_category_code("")
        assert result is not None

    def test_get_material_category_code_unknown(self):
        """测试未知类别"""
        from app.utils.code_config import get_material_category_code
        
        result = get_material_category_code("未知类别")
        assert result is not None
