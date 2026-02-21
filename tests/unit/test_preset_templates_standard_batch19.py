# -*- coding: utf-8 -*-
"""
预设阶段模板 - 标准全流程 单元测试 (Batch 19)

测试 app/services/preset_stage_templates/templates/standard/__init__.py
覆盖率目标: 60%+
"""

import pytest


@pytest.mark.unit
class TestStandardTemplateImport:
    """测试标准模板导入"""

    def test_can_import_standard_stages(self):
        """测试可以导入STANDARD_STAGES"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        assert STANDARD_STAGES is not None

    def test_can_import_standard_template(self):
        """测试可以导入STANDARD_TEMPLATE"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        assert STANDARD_TEMPLATE is not None

    def test_can_import_sub_stages(self):
        """测试可以导入子阶段"""
        from app.services.preset_stage_templates.templates.standard import (
            DELIVERY_STAGES,
            PLANNING_STAGES,
            PRODUCTION_STAGES,
        )

        assert PLANNING_STAGES is not None
        assert PRODUCTION_STAGES is not None
        assert DELIVERY_STAGES is not None

    def test_all_export(self):
        """测试__all__导出"""
        from app.services.preset_stage_templates.templates import standard

        assert hasattr(standard, "__all__")
        assert "STANDARD_STAGES" in standard.__all__
        assert "STANDARD_TEMPLATE" in standard.__all__


@pytest.mark.unit
class TestStandardStagesStructure:
    """测试标准阶段结构"""

    def test_standard_stages_is_list(self):
        """测试STANDARD_STAGES是列表"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        assert isinstance(STANDARD_STAGES, list)

    def test_standard_stages_not_empty(self):
        """测试标准阶段不为空"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        assert len(STANDARD_STAGES) > 0

    def test_standard_stages_aggregation(self):
        """测试标准阶段是各子阶段的聚合"""
        from app.services.preset_stage_templates.templates.standard import (
            DELIVERY_STAGES,
            PLANNING_STAGES,
            PRODUCTION_STAGES,
            STANDARD_STAGES,
        )

        expected_count = (
            len(PLANNING_STAGES) + len(PRODUCTION_STAGES) + len(DELIVERY_STAGES)
        )

        assert len(STANDARD_STAGES) == expected_count

    def test_stages_order_preserved(self):
        """测试阶段顺序保持（先规划、再生产、后交付）"""
        from app.services.preset_stage_templates.templates.standard import (
            DELIVERY_STAGES,
            PLANNING_STAGES,
            PRODUCTION_STAGES,
            STANDARD_STAGES,
        )

        # 验证前N个是规划阶段
        planning_count = len(PLANNING_STAGES)
        assert STANDARD_STAGES[:planning_count] == PLANNING_STAGES

        # 验证中间是生产阶段
        production_count = len(PRODUCTION_STAGES)
        assert (
            STANDARD_STAGES[planning_count : planning_count + production_count]
            == PRODUCTION_STAGES
        )

        # 验证最后是交付阶段
        assert STANDARD_STAGES[planning_count + production_count :] == DELIVERY_STAGES


@pytest.mark.unit
class TestStandardTemplateStructure:
    """测试标准模板结构"""

    def test_standard_template_is_dict(self):
        """测试STANDARD_TEMPLATE是字典"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        assert isinstance(STANDARD_TEMPLATE, dict)

    def test_template_has_required_fields(self):
        """测试模板包含必需字段"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        required_fields = [
            "template_code",
            "template_name",
            "description",
            "project_type",
            "stages",
        ]

        for field in required_fields:
            assert field in STANDARD_TEMPLATE

    def test_template_code(self):
        """测试模板代码"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        assert STANDARD_TEMPLATE["template_code"] == "TPL_STANDARD"

    def test_template_name(self):
        """测试模板名称"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        assert STANDARD_TEMPLATE["template_name"] == "标准全流程"

    def test_template_project_type(self):
        """测试项目类型"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        assert STANDARD_TEMPLATE["project_type"] == "NEW"

    def test_template_stages_reference(self):
        """测试模板stages引用STANDARD_STAGES"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
            STANDARD_TEMPLATE,
        )

        assert STANDARD_TEMPLATE["stages"] == STANDARD_STAGES

    def test_template_description_not_empty(self):
        """测试模板描述不为空"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        assert STANDARD_TEMPLATE["description"]
        assert len(STANDARD_TEMPLATE["description"]) > 0


@pytest.mark.unit
class TestSubStagesIndependence:
    """测试子阶段独立性"""

    def test_planning_stages_structure(self):
        """测试规划阶段结构"""
        from app.services.preset_stage_templates.templates.standard import (
            PLANNING_STAGES,
        )

        assert isinstance(PLANNING_STAGES, list)
        assert len(PLANNING_STAGES) > 0

    def test_production_stages_structure(self):
        """测试生产阶段结构"""
        from app.services.preset_stage_templates.templates.standard import (
            PRODUCTION_STAGES,
        )

        assert isinstance(PRODUCTION_STAGES, list)
        assert len(PRODUCTION_STAGES) > 0

    def test_delivery_stages_structure(self):
        """测试交付阶段结构"""
        from app.services.preset_stage_templates.templates.standard import (
            DELIVERY_STAGES,
        )

        assert isinstance(DELIVERY_STAGES, list)
        assert len(DELIVERY_STAGES) > 0

    def test_no_duplicate_stages_across_phases(self):
        """测试各阶段之间无重复"""
        from app.services.preset_stage_templates.templates.standard import (
            DELIVERY_STAGES,
            PLANNING_STAGES,
            PRODUCTION_STAGES,
        )

        planning_codes = {s.get("stage_code") for s in PLANNING_STAGES}
        production_codes = {s.get("stage_code") for s in PRODUCTION_STAGES}
        delivery_codes = {s.get("stage_code") for s in DELIVERY_STAGES}

        # 检查无交集
        assert planning_codes.isdisjoint(production_codes)
        assert planning_codes.isdisjoint(delivery_codes)
        assert production_codes.isdisjoint(delivery_codes)


@pytest.mark.unit
class TestStandardTemplateUsage:
    """测试标准模板使用"""

    def test_can_iterate_stages(self):
        """测试可以遍历阶段"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        count = 0
        for stage in STANDARD_STAGES:
            count += 1
            assert stage is not None

        assert count == len(STANDARD_STAGES)

    def test_can_access_template_metadata(self):
        """测试可以访问模板元数据"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        metadata = {
            "code": STANDARD_TEMPLATE["template_code"],
            "name": STANDARD_TEMPLATE["template_name"],
            "type": STANDARD_TEMPLATE["project_type"],
        }

        assert metadata["code"] == "TPL_STANDARD"
        assert metadata["name"] == "标准全流程"
        assert metadata["type"] == "NEW"

    def test_can_count_total_stages(self):
        """测试可以统计总阶段数"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        total_stages = len(STANDARD_TEMPLATE["stages"])
        assert total_stages > 0

    def test_can_filter_stages_by_property(self):
        """测试可以按属性筛选阶段"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        # 筛选必需阶段
        required_stages = [s for s in STANDARD_STAGES if s.get("is_required")]

        assert isinstance(required_stages, list)

    def test_template_can_be_serialized(self):
        """测试模板可以序列化"""
        import json

        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        # 尝试JSON序列化
        try:
            json_str = json.dumps(STANDARD_TEMPLATE, ensure_ascii=False)
            assert len(json_str) > 0

            # 尝试反序列化
            deserialized = json.loads(json_str)
            assert deserialized["template_code"] == "TPL_STANDARD"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Template serialization failed: {e}")


@pytest.mark.unit
class TestStandardTemplateValidation:
    """测试标准模板验证"""

    def test_all_stages_have_codes(self):
        """测试所有阶段都有代码"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        for stage in STANDARD_STAGES:
            assert "stage_code" in stage
            assert stage["stage_code"]

    def test_all_stages_have_names(self):
        """测试所有阶段都有名称"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        for stage in STANDARD_STAGES:
            assert "stage_name" in stage
            assert stage["stage_name"]

    def test_stage_codes_unique(self):
        """测试阶段代码唯一"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_STAGES,
        )

        codes = [s["stage_code"] for s in STANDARD_STAGES]
        unique_codes = set(codes)

        assert len(codes) == len(unique_codes)

    def test_template_description_meaningful(self):
        """测试模板描述有意义"""
        from app.services.preset_stage_templates.templates.standard import (
            STANDARD_TEMPLATE,
        )

        description = STANDARD_TEMPLATE["description"]

        # 描述应该提到关键词
        keywords = ["售前", "设计", "生产", "交付"]
        found_keywords = [kw for kw in keywords if kw in description]

        # 至少包含一些关键词
        assert len(found_keywords) > 0
