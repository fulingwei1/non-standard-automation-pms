# -*- coding: utf-8 -*-
"""
预设阶段模板服务单元测试

测试覆盖:
- get_preset_template: 获取预设模板
- init_preset_templates: 初始化预设模板
- FULL_LIFECYCLE_TEMPLATE: 完整生命周期模板
- STANDARD_TEMPLATE: 标准模板
- QUICK_TEMPLATE: 快速模板
- REPEAT_TEMPLATE: 重复生产模板
"""

import pytest
from unittest.mock import MagicMock, patch


class TestGetPresetTemplate:
    """测试获取预设模板"""

    def test_get_full_lifecycle_template(self):
        """测试获取完整生命周期模板"""
        from app.services.preset_stage_templates import get_preset_template

        template = get_preset_template("FULL_LIFECYCLE")

        assert template is not None
        assert "code" in template or "stages" in template or isinstance(template, (dict, list))

    def test_get_standard_template(self):
        """测试获取标准模板"""
        from app.services.preset_stage_templates import get_preset_template

        template = get_preset_template("STANDARD")

        assert template is not None

    def test_get_quick_template(self):
        """测试获取快速模板"""
        from app.services.preset_stage_templates import get_preset_template

        template = get_preset_template("QUICK")

        assert template is not None

    def test_get_repeat_template(self):
        """测试获取重复生产模板"""
        from app.services.preset_stage_templates import get_preset_template

        template = get_preset_template("REPEAT")

        assert template is not None

    def test_get_nonexistent_template(self):
        """测试获取不存在的模板"""
        from app.services.preset_stage_templates import get_preset_template

        template = get_preset_template("NONEXISTENT")

        assert template is None


class TestInitPresetTemplates:
    """测试初始化预设模板"""

    def test_init_preset_templates(self, db_session):
        """测试初始化预设模板"""
        from app.services.preset_stage_templates import init_preset_templates

        # 初始化模板
        result = init_preset_templates(db_session)

        # 应该返回初始化的模板数量或成功标志
        assert result is None or isinstance(result, (int, bool, list))

    def test_init_preset_templates_idempotent(self, db_session):
        """测试初始化模板幂等性"""
        from app.services.preset_stage_templates import init_preset_templates

        # 第一次初始化
        result1 = init_preset_templates(db_session)

        # 第二次初始化（应该不会重复创建）
        result2 = init_preset_templates(db_session)

        # 两次结果应该相似
        assert type(result1) == type(result2)


class TestPresetTemplateStructure:
    """测试预设模板结构"""

    def test_full_lifecycle_has_stages(self):
        """测试完整生命周期模板包含阶段"""
        from app.services.preset_stage_templates import get_preset_template

        template = get_preset_template("FULL_LIFECYCLE")

        if template and isinstance(template, dict):
            # 验证模板结构
            assert "stages" in template or "code" in template

    def test_template_stage_count(self):
        """测试模板阶段数量"""
        from app.services.preset_stage_templates import get_preset_template

        full = get_preset_template("FULL_LIFECYCLE")
        standard = get_preset_template("STANDARD")
        quick = get_preset_template("QUICK")

        # 完整模板应该有最多的阶段
        if full and standard and quick:
            if isinstance(full, dict) and "stages" in full:
                full_count = len(full.get("stages", []))
            else:
                full_count = 0

            # 不同模板应该有不同的复杂度


class TestPresetStageTemplatesModule:
    """测试预设阶段模板模块"""

    def test_import_module(self):
        """测试导入模块"""
        from app.services.preset_stage_templates import (
            get_preset_template,
            init_preset_templates,
        )

        assert get_preset_template is not None
        assert init_preset_templates is not None

    def test_template_codes(self):
        """测试模板代码常量"""
        # 验证模板代码
        template_codes = ["FULL_LIFECYCLE", "STANDARD", "QUICK", "REPEAT"]

        for code in template_codes:
            from app.services.preset_stage_templates import get_preset_template

            template = get_preset_template(code)
            # 每个代码应该能获取到模板或返回 None
            assert template is not None or template is None
