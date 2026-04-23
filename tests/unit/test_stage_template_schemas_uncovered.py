import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_STAGE_ENUMS_PATH = Path(__file__).resolve().parents[2] / "app/models/enums/stage.py"
_STAGE_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "app/schemas/stage_template.py"

stage_enum_spec = spec_from_file_location("app.models.enums.stage", _STAGE_ENUMS_PATH)
stage_enum_module = module_from_spec(stage_enum_spec)
assert stage_enum_spec and stage_enum_spec.loader
stage_enum_spec.loader.exec_module(stage_enum_module)

fake_models_pkg = types.ModuleType("app.models")
fake_models_pkg.__path__ = []
fake_enums_module = types.ModuleType("app.models.enums")
fake_enums_module.CompletionMethodEnum = stage_enum_module.CompletionMethodEnum
fake_enums_module.NodeTypeEnum = stage_enum_module.NodeTypeEnum
fake_enums_module.TemplateProjectTypeEnum = stage_enum_module.TemplateProjectTypeEnum

_original_app_models = sys.modules.get("app.models")
_original_app_models_enums = sys.modules.get("app.models.enums")

sys.modules.setdefault("app.models", fake_models_pkg)
sys.modules["app.models.enums"] = fake_enums_module

schema_spec = spec_from_file_location("app.schemas._stage_template_flat", _STAGE_TEMPLATE_PATH)
stage_template = module_from_spec(schema_spec)
assert schema_spec and schema_spec.loader
schema_spec.loader.exec_module(stage_template)

if _original_app_models is None:
    sys.modules.pop("app.models", None)
else:
    sys.modules["app.models"] = _original_app_models

if _original_app_models_enums is None:
    sys.modules.pop("app.models.enums", None)
else:
    sys.modules["app.models.enums"] = _original_app_models_enums

CompletionMethodEnum = stage_enum_module.CompletionMethodEnum
NodeTypeEnum = stage_enum_module.NodeTypeEnum
TemplateProjectTypeEnum = stage_enum_module.TemplateProjectTypeEnum
NodeDefinitionCreate = stage_template.NodeDefinitionCreate
NodeDefinitionExport = stage_template.NodeDefinitionExport
NodeDefinitionResponse = stage_template.NodeDefinitionResponse
NodeDefinitionUpdate = stage_template.NodeDefinitionUpdate
ReorderNodesRequest = stage_template.ReorderNodesRequest
SetNodeDependenciesRequest = stage_template.SetNodeDependenciesRequest
StageDefinitionCreate = stage_template.StageDefinitionCreate
StageDefinitionExport = stage_template.StageDefinitionExport
StageDefinitionResponse = stage_template.StageDefinitionResponse
StageDefinitionUpdate = stage_template.StageDefinitionUpdate
StageTemplateDetail = stage_template.StageTemplateDetail
StageTemplateResponse = stage_template.StageTemplateResponse
StageTemplateUpdate = stage_template.StageTemplateUpdate
TemplateExportData = stage_template.TemplateExportData
TemplateImportRequest = stage_template.TemplateImportRequest


def make_node_create() -> NodeDefinitionCreate:
    return NodeDefinitionCreate(
        stage_definition_id=10,
        node_code="N001",
        node_name="设计评审",
        node_type=NodeTypeEnum.APPROVAL,
        sequence=1,
        estimated_days=3,
        completion_method=CompletionMethodEnum.APPROVAL,
        dependency_node_ids=[1, 2],
        is_required=True,
        required_attachments=True,
        approval_role_ids=[11],
        auto_condition={"field": "status", "value": "DONE"},
        description="关键评审节点",
        owner_role_code="PM",
        participant_role_codes=["ENG", "QA"],
        deliverables=[{"name": "评审记录"}],
    )


def test_node_definition_models():
    create = make_node_create()
    update = NodeDefinitionUpdate(node_code="N002", node_name="更新节点")
    response = NodeDefinitionResponse(
        id=100,
        stage_definition_id=10,
        node_code=create.node_code,
        node_name=create.node_name,
        node_type=create.node_type,
        sequence=create.sequence,
        estimated_days=create.estimated_days,
        completion_method=create.completion_method,
        dependency_node_ids=create.dependency_node_ids,
        is_required=create.is_required,
        required_attachments=create.required_attachments,
        approval_role_ids=create.approval_role_ids,
        auto_condition=create.auto_condition,
        description=create.description,
        owner_role_code=create.owner_role_code,
        participant_role_codes=create.participant_role_codes,
        deliverables=create.deliverables,
        created_at="2026-04-14T03:00:00",
        updated_at="2026-04-14T03:10:00",
    )
    export = NodeDefinitionExport(
        id=1,
        stage_definition_id=10,
        **create.model_dump(exclude={"stage_definition_id"}),
    )

    assert create.node_type == NodeTypeEnum.APPROVAL
    assert create.completion_method == CompletionMethodEnum.APPROVAL
    assert update.sequence == 0
    assert response.id == 100
    assert response.required_attachments is True
    assert export.stage_definition_id == 10


def test_stage_definition_models():
    node = make_node_create()
    create = StageDefinitionCreate(
        stage_code="S001",
        stage_name="方案阶段",
        sequence=2,
        category="presales",
        estimated_days=10,
        description="售前方案设计",
        is_required=True,
        is_milestone=True,
        is_parallel=True,
        nodes=[node],
    )
    update = StageDefinitionUpdate(stage_code="S002", stage_name="更新阶段")
    response = StageDefinitionResponse(
        id=9,
        template_id=3,
        stage_code=create.stage_code,
        stage_name=create.stage_name,
        sequence=create.sequence,
        category=create.category,
        estimated_days=create.estimated_days,
        description=create.description,
        is_required=create.is_required,
        is_milestone=create.is_milestone,
        is_parallel=create.is_parallel,
        nodes=[
            NodeDefinitionResponse(
                id=100,
                stage_definition_id=9,
                **node.model_dump(exclude={"stage_definition_id"}),
            )
        ],
        created_at="2026-04-14T03:00:00",
        updated_at="2026-04-14T03:10:00",
    )
    export = StageDefinitionExport(id=9, template_id=3, **create.model_dump())

    assert create.nodes[0].node_code == "N001"
    assert update.category == "execution"
    assert response.nodes[0].stage_definition_id == 9
    assert export.template_id == 3


def test_stage_template_response_detail_and_import_models():
    response = StageTemplateResponse(
        id=1,
        template_code="TPL-001",
        template_name="标准模板",
        description="模板说明",
        project_type=TemplateProjectTypeEnum.CUSTOM,
        is_default=False,
        is_active=True,
        stage_count=2,
        node_count=5,
        created_by=8,
        created_at="2026-04-14T03:00:00",
        updated_at="2026-04-14T03:10:00",
    )
    detail = StageTemplateDetail(
        id=1,
        template_code="TPL-001",
        template_name="标准模板",
        project_type=TemplateProjectTypeEnum.NEW,
        stages=[],
    )
    update = StageTemplateUpdate(template_code="TPL-002", template_name="更新模板")
    export = TemplateExportData(
        id=1,
        template_code="TPL-001",
        template_name="标准模板",
        project_type=TemplateProjectTypeEnum.REPEAT,
        stages=[],
    )
    req = TemplateImportRequest(data=export, override_code="TPL-OVERRIDE")

    assert response.stage_count == 2
    assert response.node_count == 5
    assert detail.project_type == TemplateProjectTypeEnum.NEW
    assert update.is_active is True
    assert req.data.template_code == "TPL-001"
    assert req.override_code == "TPL-OVERRIDE"


def test_reorder_and_dependency_requests():
    reorder = ReorderNodesRequest(node_ids=[5, 2, 3])
    deps = SetNodeDependenciesRequest(dependency_node_ids=[10, 11])

    assert reorder.node_ids == [5, 2, 3]
    assert deps.dependency_node_ids == [10, 11]
