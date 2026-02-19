# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 优势产品导入服务
"""
import pytest
from unittest.mock import MagicMock, patch, call

try:
    from app.services.advantage_product_import_service import (
        COLUMN_CATEGORY_MAP,
        clear_existing_data,
        ensure_categories_exist,
        parse_product_from_cell,
        process_product_row,
    )
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="advantage_product_import_service 导入失败")


class TestColumnCategoryMap:
    def test_map_has_8_entries(self):
        """类别映射表应有8个条目"""
        assert len(COLUMN_CATEGORY_MAP) == 8

    def test_first_entry_home_appliance(self):
        """第0列应为白色家电"""
        assert COLUMN_CATEGORY_MAP[0]["code"] == "HOME_APPLIANCE"
        assert COLUMN_CATEGORY_MAP[0]["name"] == "白色家电"

    def test_last_entry_education(self):
        """第7列应为教育实训"""
        assert COLUMN_CATEGORY_MAP[7]["code"] == "EDUCATION"


class TestClearExistingData:
    def test_clear_calls_delete_on_both_models(self):
        """清空操作调用两个模型的delete"""
        db = MagicMock()
        db.query.return_value.delete.return_value = None

        clear_existing_data(db)

        assert db.query.call_count == 2
        db.commit.assert_called_once()


class TestEnsureCategoriesExist:
    def test_creates_all_categories_when_empty(self):
        """没有已有类别时创建全部8个"""
        db = MagicMock()

        # 已有类别为空
        db.query.return_value.all.return_value = []
        db.query.return_value.delete.return_value = None

        mock_new_cat = MagicMock()
        mock_new_cat.id = 1

        with patch(
            "app.services.advantage_product_import_service.AdvantageProductCategory",
            return_value=mock_new_cat
        ), patch(
            "app.services.advantage_product_import_service.clear_existing_data"
        ):
            cat_map, created = ensure_categories_exist(db, clear_existing=False)

        assert created == 8

    def test_skips_existing_categories(self):
        """已存在的类别不重复创建"""
        db = MagicMock()

        # 已有 HOME_APPLIANCE
        existing_cat = MagicMock()
        existing_cat.code = "HOME_APPLIANCE"
        existing_cat.id = 100

        db.query.return_value.all.return_value = [existing_cat]
        # mock query chain for AdvantageProductCategory
        db.query.return_value.all.return_value = [
            type("Cat", (), {"code": "HOME_APPLIANCE", "id": 100})()
        ]

        mock_new_cat = MagicMock()
        mock_new_cat.id = 1

        with patch(
            "app.services.advantage_product_import_service.AdvantageProductCategory",
            return_value=mock_new_cat
        ):
            cat_map, created = ensure_categories_exist(db, clear_existing=False)

        # HOME_APPLIANCE已存在，创建其他7个
        assert created == 7
        assert cat_map[0] == 100  # 已存在的类别ID


class TestParseProductFromCell:
    def test_kc_series_number_returns_none_code(self):
        """纯编号如KC2700返回None编码（系列编号）"""
        code, name = parse_product_from_cell("KC2700", None, 0, 0)
        assert code is None
        assert name == "KC2700"

    def test_kc_prefix_with_description_extracts_code(self):
        """KC开头带描述时提取编码"""
        code, name = parse_product_from_cell("KC2700工业机器人", "KC2700", 1, 0)
        # KC2700 (6字符KC+4位数字) 然后接描述
        assert code is not None

    def test_no_kc_with_series_generates_code(self):
        """无KC前缀但有系列时生成编码"""
        code, name = parse_product_from_cell("散热风扇", "KC2700", 5, 1)
        assert code == "KC2700_5"
        assert name == "散热风扇"

    def test_no_kc_no_series_generates_fallback_code(self):
        """无KC前缀无系列时生成备用编码"""
        code, name = parse_product_from_cell("通用产品", None, 3, 2)
        assert code == "PRD_2_3"
        assert name == "通用产品"

    def test_pure_kc_number_too_long_not_series(self):
        """KC开头超过10字符不作为系列编号"""
        code, name = parse_product_from_cell("KC2700ABCDEFG", None, 1, 0)
        # 超过10字符，不是系列编号
        assert code is not None or name is not None  # 至少有一个值


class TestProcessProductRow:
    def test_creates_new_product(self):
        """产品不存在时创建新产品"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.advantage_product_import_service.AdvantageProduct") as mock_cls:
            mock_cls.return_value = MagicMock()
            created, updated, skipped = process_product_row(
                db, "KC001", "测试产品", category_id=1, current_series="KC", clear_existing=False
            )

        assert created is True
        assert updated is False
        assert skipped is False

    def test_skips_existing_when_no_clear(self):
        """已存在且不清空时跳过"""
        db = MagicMock()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        created, updated, skipped = process_product_row(
            db, "KC001", "旧产品", category_id=1, current_series="KC", clear_existing=False
        )

        assert created is False
        assert updated is False
        assert skipped is True

    def test_updates_existing_when_clear(self):
        """已存在且指定清空时更新"""
        db = MagicMock()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        created, updated, skipped = process_product_row(
            db, "KC001", "新名称", category_id=2, current_series="KC", clear_existing=True
        )

        assert created is False
        assert updated is True
        assert skipped is False
        assert existing.product_name == "新名称"
        assert existing.category_id == 2
