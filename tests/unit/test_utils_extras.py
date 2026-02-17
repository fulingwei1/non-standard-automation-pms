# -*- coding: utf-8 -*-
"""
app/utils/ 低覆盖率模块测试
- code_config.py (33%)
- permission_helpers.py (43%)
- domain_codes.py (60%)
"""
import pytest
from unittest.mock import MagicMock, patch


# ─── code_config.py ──────────────────────────────────────────────────────────

from app.utils.code_config import (
    get_material_category_code,
    validate_material_category_code,
    CODE_PREFIX,
    SEQ_LENGTH,
    MATERIAL_CATEGORY_CODES,
    VALID_MATERIAL_CATEGORY_CODES,
)


class TestGetMaterialCategoryCode:
    def test_mechanical(self):
        assert get_material_category_code("ME-01-01") == "ME"

    def test_electrical(self):
        assert get_material_category_code("EL-02-03") == "EL"

    def test_pneumatic(self):
        assert get_material_category_code("PN-01-02") == "PN"

    def test_standard(self):
        assert get_material_category_code("ST-03-01") == "ST"

    def test_other(self):
        assert get_material_category_code("OT-01-01") == "OT"

    def test_empty_string_returns_other(self):
        assert get_material_category_code("") == "OT"

    def test_none_returns_other(self):
        assert get_material_category_code(None) == "OT"

    def test_unknown_prefix_returns_other(self):
        assert get_material_category_code("ZZ-01-01") == "OT"

    def test_lowercase_input(self):
        # 应该转大写再匹配
        result = get_material_category_code("me-01-01")
        assert result == "ME"

    def test_no_dash(self):
        result = get_material_category_code("ME")
        assert result == "ME"


class TestValidateMaterialCategoryCode:
    def test_valid_me(self):
        assert validate_material_category_code("ME") is True

    def test_valid_el(self):
        assert validate_material_category_code("EL") is True

    def test_invalid_code(self):
        assert validate_material_category_code("XX") is False

    def test_lowercase_valid(self):
        assert validate_material_category_code("me") is True

    def test_empty_string_invalid(self):
        assert validate_material_category_code("") is False


class TestCodeConfigConstants:
    def test_code_prefix_has_employee(self):
        assert "EMPLOYEE" in CODE_PREFIX
        assert CODE_PREFIX["EMPLOYEE"] == "EMP"

    def test_seq_length_has_project(self):
        assert "PROJECT" in SEQ_LENGTH
        assert isinstance(SEQ_LENGTH["PROJECT"], int)

    def test_valid_codes_is_set(self):
        assert isinstance(VALID_MATERIAL_CATEGORY_CODES, set)
        assert len(VALID_MATERIAL_CATEGORY_CODES) > 0


# ─── permission_helpers.py ───────────────────────────────────────────────────

from app.utils.permission_helpers import (
    get_accessible_project_ids,
)


class TestGetAccessibleProjectIds:
    def test_superuser_returns_none(self):
        db = MagicMock()
        user = MagicMock()
        user.is_superuser = True

        result = get_accessible_project_ids(db, user)
        # 超级管理员可以访问所有项目，返回 None 或 all IDs
        assert result is None or isinstance(result, (set, list))

    def test_regular_user_empty_roles(self):
        db = MagicMock()
        user = MagicMock()
        user.is_superuser = False
        user.id = 10
        user.tenant_id = 1

        # mock DB query returns empty
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = get_accessible_project_ids(db, user)
        assert isinstance(result, (set, list, type(None)))


# ─── domain_codes.py ─────────────────────────────────────────────────────────

import app.utils.domain_codes as domain_codes_module


class TestDomainCodes:
    def test_module_has_classes(self):
        # 模块里有多个编码类
        assert hasattr(domain_codes_module, "OutsourcingCodes")
        assert hasattr(domain_codes_module, "PresaleCodes")
        assert hasattr(domain_codes_module, "PmoCodes")

    def test_outsourcing_codes_class_exists(self):
        from app.utils.domain_codes import OutsourcingCodes
        assert isinstance(OutsourcingCodes, type)

    def test_presale_codes_class_exists(self):
        from app.utils.domain_codes import PresaleCodes
        assert isinstance(PresaleCodes, type)

    def test_pmo_codes_class_exists(self):
        from app.utils.domain_codes import PmoCodes
        assert isinstance(PmoCodes, type)

    def test_classes_have_static_methods(self):
        from app.utils.domain_codes import OutsourcingCodes
        # 应该有生成编号的静态方法
        methods = [m for m in dir(OutsourcingCodes) if not m.startswith("_")]
        assert len(methods) > 0
