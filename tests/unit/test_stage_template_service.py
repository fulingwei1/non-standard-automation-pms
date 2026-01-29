# -*- coding: utf-8 -*-
"""
阶段模板系统单元测试

测试内容：
- StageTemplateService CRUD 操作
- 预置模板数据完整性
- 模板导入导出功能
- 节点依赖关系
"""

import pytest
from sqlalchemy.orm import Session

from app.models.stage_template import StageTemplate, StageDefinition, NodeDefinition
from app.services.stage_template import StageTemplateService
from app.services.preset_stage_templates import (
    PRESET_TEMPLATES,
    FULL_LIFECYCLE_TEMPLATE,
    STANDARD_TEMPLATE,
    QUICK_TEMPLATE,
    REPEAT_TEMPLATE,
    get_preset_template,
)


@pytest.mark.unit
class TestPresetTemplateData:
    """预置模板数据完整性测试"""

    def test_all_templates_defined(self):
        """测试所有预置模板已定义"""
        assert len(PRESET_TEMPLATES) == 4
        codes = [t["template_code"] for t in PRESET_TEMPLATES]
        assert "TPL_FULL_LIFECYCLE" in codes
        assert "TPL_STANDARD" in codes
        assert "TPL_QUICK" in codes
        assert "TPL_REPEAT" in codes

    def test_full_lifecycle_template_structure(self):
        """测试完整生命周期模板结构"""
        template = FULL_LIFECYCLE_TEMPLATE
        assert template["template_code"] == "TPL_FULL_LIFECYCLE"
        assert template["template_name"] == "完整生命周期模板"
        assert template["project_type"] == "NEW"
        assert len(template["stages"]) == 22  # 22个阶段

        # 验证阶段编码顺序
        stage_codes = [s["stage_code"] for s in template["stages"]]
        expected_codes = [f"S{i:02d}" for i in range(1, 23)]
        assert stage_codes == expected_codes

    def test_standard_template_structure(self):
        """测试标准模板结构"""
        template = STANDARD_TEMPLATE
        assert template["template_code"] == "TPL_STANDARD"
        assert len(template["stages"]) == 9  # S1-S9

        # 验证阶段编码
        stage_codes = [s["stage_code"] for s in template["stages"]]
        expected_codes = [f"S{i}" for i in range(1, 10)]
        assert stage_codes == expected_codes

    def test_quick_template_structure(self):
        """测试快速模板结构"""
        template = QUICK_TEMPLATE
        assert template["template_code"] == "TPL_QUICK"
        assert template["project_type"] == "SIMPLE"
        assert len(template["stages"]) == 4  # Q1-Q4

    def test_repeat_template_structure(self):
        """测试重复生产模板结构"""
        template = REPEAT_TEMPLATE
        assert template["template_code"] == "TPL_REPEAT"
        assert template["project_type"] == "REPEAT"
        assert len(template["stages"]) == 4  # R1-R4

    def test_get_preset_template(self):
        """测试获取预置模板函数"""
        template = get_preset_template("TPL_STANDARD")
        assert template is not None
        assert template["template_code"] == "TPL_STANDARD"

        # 测试不存在的模板
        result = get_preset_template("NON_EXISTENT")
        assert result is None

    def test_all_templates_have_required_fields(self):
        """测试所有模板具有必填字段"""
        required_template_fields = ["template_code", "template_name", "project_type", "stages"]
        required_stage_fields = ["stage_code", "stage_name", "sequence", "nodes"]
        required_node_fields = ["node_code", "node_name", "node_type", "sequence"]

        for template in PRESET_TEMPLATES:
            # 验证模板字段
            for field in required_template_fields:
                assert field in template, f"模板 {template.get('template_code')} 缺��字段: {field}"

            # 验证阶段字段
            for stage in template["stages"]:
                for field in required_stage_fields:
                    assert field in stage, f"阶段 {stage.get('stage_code')} 缺少字段: {field}"

                # 验证节点字段
                for node in stage.get("nodes", []):
                    for field in required_node_fields:
                        assert field in node, f"节点 {node.get('node_code')} 缺少字段: {field}"

    def test_node_dependency_references_valid(self):
        """测试节点依赖引用有效性"""
        for template in PRESET_TEMPLATES:
            # 收集所有节点编码
            all_node_codes = set()
            for stage in template["stages"]:
                for node in stage.get("nodes", []):
                    all_node_codes.add(node["node_code"])

            # 验证依赖引用
            for stage in template["stages"]:
                for node in stage.get("nodes", []):
                    deps = node.get("dependency_node_codes", [])
                    for dep_code in deps:
                        assert dep_code in all_node_codes, (
                            f"模板 {template['template_code']} 节点 {node['node_code']} "
                            f"引用了不存在的依赖: {dep_code}"
                        )


@pytest.mark.unit
class TestStageTemplateService:
    """StageTemplateService 单元测试"""

    def test_create_template(self, db_session: Session):
        """测试创建模板"""
        service = StageTemplateService(db_session)

        template = service.create_template(
        template_code="TEST_TPL_001",
        template_name="测试模板",
        description="用于测试的模板",
        project_type="NEW",
        is_default=False,
        )
        db_session.flush()

        assert template.id is not None
        assert template.template_code == "TEST_TPL_001"
        assert template.template_name == "测试模板"
        assert template.is_active is True

    def test_create_duplicate_template_code_fails(self, db_session: Session):
        """测试重复模板编码创建失败"""
        service = StageTemplateService(db_session)

        service.create_template(
        template_code="TEST_TPL_DUP",
        template_name="模板1",
        project_type="NEW",
        )
        db_session.flush()

        with pytest.raises(ValueError, match="模板编码.*已存在"):
            service.create_template(
            template_code="TEST_TPL_DUP",
            template_name="模板2",
            project_type="NEW",
            )

    def test_add_stage_to_template(self, db_session: Session):
        """测试向模板添加阶段"""
        service = StageTemplateService(db_session)

        template = service.create_template(
        template_code="TEST_TPL_STAGE",
        template_name="测试模板",
        project_type="NEW",
        )
        db_session.flush()

        stage = service.add_stage(
        template_id=template.id,
        stage_code="S1",
        stage_name="需求进入",
        sequence=0,
        estimated_days=7,
        description="接收客户需求",
        is_required=True,
        )
        db_session.flush()

        assert stage.id is not None
        assert stage.stage_code == "S1"
        assert stage.template_id == template.id

    def test_add_node_to_stage(self, db_session: Session):
        """测试向阶段添加节点"""
        service = StageTemplateService(db_session)

        template = service.create_template(
        template_code="TEST_TPL_NODE",
        template_name="测试模板",
        project_type="NEW",
        )
        stage = service.add_stage(
        template_id=template.id,
        stage_code="S1",
        stage_name="需求进入",
        sequence=0,
        )
        db_session.flush()

        node = service.add_node(
        stage_definition_id=stage.id,
        node_code="S1N01",
        node_name="需求接收登记",
        node_type="TASK",
        sequence=0,
        estimated_days=1,
        completion_method="MANUAL",
        is_required=True,
        description="登记客户需求基本信息",
        )
        db_session.flush()

        assert node.id is not None
        assert node.node_code == "S1N01"
        assert node.stage_definition_id == stage.id

    def test_import_template(self, db_session: Session):
        """测试导入模板"""
        service = StageTemplateService(db_session)

        # 使用快速模板测试（较小）
        template = service.import_template(QUICK_TEMPLATE)
        db_session.flush()

        assert template.id is not None
        assert template.template_code == "TPL_QUICK"

        # 验证阶段和节点已创建
        stages = db_session.query(StageDefinition).filter(
        StageDefinition.template_id == template.id
        ).all()
        assert len(stages) == 4

        # 验证节点
        total_nodes = sum(len(s.nodes) for s in stages)
        expected_nodes = sum(len(s["nodes"]) for s in QUICK_TEMPLATE["stages"])
        assert total_nodes == expected_nodes

    def test_import_template_with_dependencies(self, db_session: Session):
        """测试导入带依赖关系的模板"""
        service = StageTemplateService(db_session)

        # 导入标准模板（有依赖关系）
        template = service.import_template(STANDARD_TEMPLATE)
        db_session.flush()

        # 检查节点依赖关系
        nodes_with_deps = db_session.query(NodeDefinition).filter(
        NodeDefinition.dependency_node_ids.isnot(None)
        ).all()

        # 标准模板中有多个节点有依赖
        assert len(nodes_with_deps) > 0

    def test_export_template(self, db_session: Session):
        """测试导出模板"""
        service = StageTemplateService(db_session)

        # 先导入一个模板
        template = service.import_template(REPEAT_TEMPLATE)
        db_session.flush()

        # 导出
        exported = service.export_template(template.id)

        assert exported["template_code"] == "TPL_REPEAT"
        assert exported["template_name"] == "重复生产"
        assert len(exported["stages"]) == 4

    def test_copy_template(self, db_session: Session):
        """测试复制模板"""
        service = StageTemplateService(db_session)

        # 创建原始模板
        original = service.import_template(QUICK_TEMPLATE)
        db_session.flush()

        # 复制
        copied = service.copy_template(
        source_template_id=original.id,
        new_code="TPL_QUICK_COPY",
        new_name="快速模板副本",
        )
        db_session.flush()

        assert copied.id != original.id
        assert copied.template_code == "TPL_QUICK_COPY"
        assert copied.template_name == "快速模板副本"

        # 验证阶段也被复制
        original_stages = len(original.stages)
        copied_stages = len(copied.stages)
        assert copied_stages == original_stages

    def test_set_default_template(self, db_session: Session):
        """测试设置默认模板"""
        service = StageTemplateService(db_session)

        # 创建两个同类型模板
        tpl1 = service.create_template(
        template_code="TPL_DEFAULT_1",
        template_name="模板1",
        project_type="NEW",
        is_default=True,
        )
        tpl2 = service.create_template(
        template_code="TPL_DEFAULT_2",
        template_name="模板2",
        project_type="NEW",
        is_default=False,
        )
        db_session.flush()

        # 设置第二个为默认
        service.set_default_template(tpl2.id)
        db_session.flush()

        # 刷新数据
        db_session.refresh(tpl1)
        db_session.refresh(tpl2)

        assert tpl2.is_default is True
        assert tpl1.is_default is False

    def test_delete_template(self, db_session: Session):
        """测试删除模板"""
        service = StageTemplateService(db_session)

        template = service.create_template(
        template_code="TPL_TO_DELETE",
        template_name="待删除模板",
        project_type="NEW",
        )
        db_session.flush()
        template_id = template.id

        success = service.delete_template(template_id)
        db_session.flush()

        assert success is True

        # 验证已删除（硬删除）
        deleted = db_session.query(StageTemplate).filter(
        StageTemplate.id == template_id
        ).first()
        assert deleted is None

    def test_list_templates(self, db_session: Session):
        """测试列出模板"""
        service = StageTemplateService(db_session)

        # 创建几个模板
        service.create_template(
        template_code="TPL_LIST_1",
        template_name="列表模板1",
        project_type="NEW",
        )
        service.create_template(
        template_code="TPL_LIST_2",
        template_name="列表模板2",
        project_type="REPEAT",
        )
        db_session.flush()

        # 列出所有
        templates = service.list_templates()
        assert len(templates) >= 2

        # 按项目类型筛选
        new_templates = service.list_templates(project_type="NEW")
        assert all(t.project_type == "NEW" for t in new_templates)


@pytest.mark.unit
class TestInitPresetTemplates:
    """预置模板初始化测试"""

    def test_init_preset_templates_creates_all(self, db_session: Session):
        """测试初始化创建所有预置模板"""
        from app.utils.init_data import init_preset_stage_templates

        created = init_preset_stage_templates(db_session)
        db_session.commit()

        assert len(created) == 4

        # 验证所有模板已创建
        codes = [t.template_code for t in created]
        assert "TPL_FULL_LIFECYCLE" in codes
        assert "TPL_STANDARD" in codes
        assert "TPL_QUICK" in codes
        assert "TPL_REPEAT" in codes

    def test_init_preset_templates_idempotent(self, db_session: Session):
        """测试初始化幂等性（重复执行不会重复创建）"""
        from app.utils.init_data import init_preset_stage_templates

        # 第一次初始化
        created1 = init_preset_stage_templates(db_session)
        db_session.commit()
        assert len(created1) == 4

        # 第二次初始化
        created2 = init_preset_stage_templates(db_session)
        db_session.commit()
        assert len(created2) == 0  # 不应创建新模板

        # 验证数据库中只有4个预置模板
        preset_codes = [t["template_code"] for t in PRESET_TEMPLATES]
        count = db_session.query(StageTemplate).filter(
        StageTemplate.template_code.in_(preset_codes)
        ).count()
        assert count == 4
