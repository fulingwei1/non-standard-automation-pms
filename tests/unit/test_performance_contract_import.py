import importlib
import sys
from types import SimpleNamespace

from app.core.config import settings


def test_performance_contract_module_uses_configured_sqlite_path():
    module = importlib.import_module("app.api.v1.endpoints.performance.contract")

    assert module.DB_PATH == settings.SQLITE_DB_PATH


def test_performance_contract_module_does_not_open_sqlite_on_import(monkeypatch):
    """HR-15: endpoint import must not create tables through sqlite3.connect."""
    module_name = "app.api.v1.endpoints.performance.contract"
    sys.modules.pop(module_name, None)

    def fail_connect(*args, **kwargs):
        raise AssertionError("performance contract endpoint must not open sqlite on import")

    monkeypatch.setattr("sqlite3.connect", fail_connect)

    importlib.import_module(module_name)


def test_create_contract_uses_injected_session(db_session):
    """HR-15: create_contract should persist through the injected SQLAlchemy session."""
    module = importlib.import_module("app.api.v1.endpoints.performance.contract")

    current_user = SimpleNamespace(id=1)

    result = module.create_contract(
        contract_no="PC-HR15-2026-001",
        contract_type="L3",
        year=2026,
        quarter=1,
        signer_id=10,
        signer_name="员工甲",
        signer_title="工程师",
        counterpart_id=20,
        counterpart_name="经理乙",
        counterpart_title="部门经理",
        department_id=3,
        department_name="研发部",
        strategy_id=None,
        status="draft",
        sign_date=None,
        effective_date=None,
        expiry_date=None,
        remarks="HR-15 TDD",
        db=db_session,
        current_user=current_user,
    )

    assert result.code == 200
    contract = result.data
    assert contract["contract_no"] == "PC-HR15-2026-001"
    assert contract["created_by"] == current_user.id

    listed = module.list_contracts(
        contract_type="L3",
        status=None,
        year=2026,
        signer_id=None,
        department_id=None,
        skip=0,
        limit=10,
        db=db_session,
        current_user=current_user,
    )
    assert listed.data["total"] == 1
    assert listed.data["items"][0]["contract_no"] == "PC-HR15-2026-001"


def test_contract_items_submit_and_sign_use_injected_session(db_session):
    """HR-15: item weight, submit, and sign flow should all use the injected session."""
    module = importlib.import_module("app.api.v1.endpoints.performance.contract")
    current_user = SimpleNamespace(id=1)

    created = module.create_contract(
        contract_no="PC-HR15-2026-002",
        contract_type="L3",
        year=2026,
        quarter=1,
        signer_id=10,
        signer_name="员工甲",
        signer_title="工程师",
        counterpart_id=20,
        counterpart_name="经理乙",
        counterpart_title="部门经理",
        department_id=3,
        department_name="研发部",
        strategy_id=None,
        status="draft",
        sign_date=None,
        effective_date=None,
        expiry_date=None,
        remarks=None,
        db=db_session,
        current_user=current_user,
    )
    contract_id = created.data["id"]

    item = module.add_contract_item(
        contract_id=contract_id,
        sort_order=1,
        category="业绩指标",
        indicator_name="项目交付",
        indicator_description=None,
        weight=100,
        unit="分",
        target_value="100",
        challenge_value=None,
        baseline_value=None,
        scoring_rule="达成即满分",
        data_source="系统",
        evaluation_method="自动",
        source_type="custom",
        source_id=None,
        db=db_session,
        current_user=current_user,
    )
    assert item.code == 200

    detail = module.get_contract(
        contract_id=contract_id,
        db=db_session,
        current_user=current_user,
    )
    assert detail.data["total_weight"] == 100.0
    assert detail.data["items"][0]["indicator_name"] == "项目交付"

    submitted = module.submit_contract(
        contract_id=contract_id,
        db=db_session,
        current_user=current_user,
    )
    assert submitted.code == 200

    module.update_contract(
        contract_id=contract_id,
        status="pending_sign",
        db=db_session,
        current_user=current_user,
    )
    module.sign_contract(
        contract_id=contract_id,
        sign_as="signer",
        db=db_session,
        current_user=current_user,
    )
    module.sign_contract(
        contract_id=contract_id,
        sign_as="counterpart",
        db=db_session,
        current_user=current_user,
    )
    signed = module.get_contract(
        contract_id=contract_id,
        db=db_session,
        current_user=current_user,
    )
    assert signed.data["status"] == "active"
    assert signed.data["signer_signature"]
    assert signed.data["counterpart_signature"]
