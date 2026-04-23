import asyncio
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _register_module(monkeypatch, name: str, *, package: bool = False, **attrs):
    module = ModuleType(name)
    if package:
        module.__path__ = []
    module.__dict__.update(attrs)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def _register_absolute_module(monkeypatch, name: str, *, package: bool = False, **attrs):
    parts = name.split(".")
    parent = None
    for i in range(1, len(parts)):
        pkg_name = ".".join(parts[:i])
        pkg = sys.modules.get(pkg_name)
        if pkg is None:
            pkg = _register_module(monkeypatch, pkg_name, package=True)
        if parent is not None:
            setattr(parent, parts[i - 1], pkg)
        parent = pkg

    module = _register_module(monkeypatch, name, package=package, **attrs)
    if parent is not None:
        setattr(parent, parts[-1], module)
    return module


def _load_module_from_path(monkeypatch, module_name: str, relative_path: str, *, package: bool = False):
    module_path = ROOT / relative_path
    kwargs = {}
    if package or module_path.name == "__init__.py":
        kwargs["submodule_search_locations"] = [str(module_path.parent)]

    parts = module_name.split(".")
    parent = None
    for i in range(1, len(parts)):
        pkg_name = ".".join(parts[:i])
        pkg = sys.modules.get(pkg_name)
        if pkg is None:
            pkg = _register_module(monkeypatch, pkg_name, package=True)
        if parent is not None:
            setattr(parent, parts[i - 1], pkg)
        parent = pkg

    spec = importlib.util.spec_from_file_location(module_name, module_path, **kwargs)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    if parent is not None:
        setattr(parent, parts[-1], module)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("module_name", "relative_path", "child_module", "export_names", "expected_all"),
    [
        (
            "compat_bom_attributes_pkg_batch5",
            "app/services/bom_attributes/__init__.py",
            "bom_attributes_service",
            ["BomAttributesService"],
            ["BomAttributesService"],
        ),
        (
            "compat_business_support_reports_pkg_batch5",
            "app/services/business_support_reports/__init__.py",
            "business_support_reports_service",
            ["BusinessSupportReportsService"],
            ["BusinessSupportReportsService"],
        ),
        (
            "compat_ecn_approval_pkg_batch5",
            "app/services/ecn/approval/__init__.py",
            "service",
            ["EcnApprovalService"],
            ["EcnApprovalService"],
        ),
        (
            "compat_ecn_integration_pkg_batch5",
            "app/services/ecn/integration/__init__.py",
            "ecn_integration_service",
            ["EcnIntegrationService"],
            ["EcnIntegrationService"],
        ),
        (
            "compat_employee_performance_pkg_batch5",
            "app/services/employee_performance/__init__.py",
            "employee_performance_service",
            ["EmployeePerformanceService"],
            ["EmployeePerformanceService"],
        ),
        (
            "compat_kit_rate_pkg_batch5",
            "app/services/kit_rate/__init__.py",
            "kit_rate_service",
            ["KitRateService"],
            ["KitRateService"],
        ),
        (
            "compat_machine_custom_pkg_batch5",
            "app/services/machine_custom/__init__.py",
            "service",
            ["MachineCustomService"],
            ["MachineCustomService"],
        ),
        (
            "compat_manager_performance_pkg_batch5",
            "app/services/manager_performance/__init__.py",
            "manager_performance_service",
            ["ManagerPerformanceService"],
            ["ManagerPerformanceService"],
        ),
        (
            "compat_outsourcing_workflow_pkg_batch5",
            "app/services/outsourcing_workflow/__init__.py",
            "outsourcing_workflow_service",
            ["OutsourcingWorkflowService"],
            ["OutsourcingWorkflowService"],
        ),
        (
            "compat_pitfall_pkg_batch5",
            "app/services/pitfall/__init__.py",
            "pitfall_service",
            ["PitfallService"],
            ["PitfallService"],
        ),
        (
            "compat_ppt_generator_pkg_batch5",
            "app/services/ppt_generator/__init__.py",
            "generator",
            ["PresentationGenerator"],
            ["PresentationGenerator"],
        ),
        (
            "compat_project_change_requests_pkg_batch5",
            "app/services/project_change_requests/__init__.py",
            "service",
            ["ProjectChangeRequestsService"],
            ["ProjectChangeRequestsService"],
        ),
        (
            "compat_project_crud_pkg_batch5",
            "app/services/project_crud/__init__.py",
            "service",
            ["ProjectCrudService"],
            ["ProjectCrudService"],
        ),
        (
            "compat_project_performance_pkg_batch5",
            "app/services/project_performance/__init__.py",
            "service",
            ["ProjectPerformanceService"],
            ["ProjectPerformanceService"],
        ),
        (
            "compat_purchase_workflow_pkg_batch5",
            "app/services/purchase_workflow/__init__.py",
            "service",
            ["PurchaseWorkflowService"],
            ["PurchaseWorkflowService"],
        ),
        (
            "compat_quality_risk_management_pkg_batch5",
            "app/services/quality_risk_management/__init__.py",
            "service",
            ["QualityRiskManagementService"],
            ["QualityRiskManagementService"],
        ),
        (
            "compat_role_management_pkg_batch5",
            "app/services/role_management/__init__.py",
            "service",
            ["RoleManagementService"],
            ["RoleManagementService"],
        ),
    ],
)
def test_service_packages_reexport_expected_symbols(
    monkeypatch, module_name, relative_path, child_module, export_names, expected_all
):
    sentinels = {name: object() for name in export_names}
    _register_module(monkeypatch, f"{module_name}.{child_module}", **sentinels)

    module = _load_module_from_path(monkeypatch, module_name, relative_path, package=True)

    for export_name, sentinel in sentinels.items():
        assert getattr(module, export_name) is sentinel

    assert module.__all__ == expected_all


def test_collaboration_rating_package_reexports_expected_symbols(monkeypatch):
    sentinels = {
        "base": {"CollaborationRatingService": object()},
        "rating_manager": {"RatingManager": object()},
        "selector": {"Selector": object()},
        "statistics": {"Statistics": object()},
    }

    for child_module, attrs in sentinels.items():
        _register_module(monkeypatch, f"compat_collaboration_rating_pkg_batch5.{child_module}", **attrs)

    module = _load_module_from_path(
        monkeypatch,
        "compat_collaboration_rating_pkg_batch5",
        "app/services/collaboration_rating/__init__.py",
        package=True,
    )

    assert module.CollaborationRatingService is sentinels["base"]["CollaborationRatingService"]
    assert module.RatingManager is sentinels["rating_manager"]["RatingManager"]
    assert module.Selector is sentinels["selector"]["Selector"]
    assert module.Statistics is sentinels["statistics"]["Statistics"]
    assert module.__all__ == ["CollaborationRatingService", "RatingManager", "Selector", "Statistics"]


def test_business_support_compat_schema_module_reexports_expected_symbols(monkeypatch):
    sentinels = {}

    def _module_getattr(name):
        return sentinels.setdefault(name, object())

    compat_source = _register_absolute_module(monkeypatch, "app.schemas.business_support")
    compat_source.__getattr__ = _module_getattr

    module = _load_module_from_path(
        monkeypatch,
        "compat_business_support_schema_batch5",
        "app/schemas/business_support.py",
    )

    assert module.BiddingProjectCreate is sentinels["BiddingProjectCreate"]
    assert module.InvoiceRequestResponse is sentinels["InvoiceRequestResponse"]
    assert module.SupplierRegistrationReviewRequest is sentinels["SupplierRegistrationReviewRequest"]
    assert "BiddingProjectCreate" in module.__all__
    assert "SupplierRegistrationReviewRequest" in module.__all__


@pytest.mark.parametrize(
    ("module_name", "relative_path", "class_name"),
    [
        (
            "performance_service_base_batch5",
            "app/services/performance_service/base.py",
            "PerformanceService",
        ),
        (
            "resource_allocation_service_base_batch5",
            "app/services/resource_allocation_service/base.py",
            "ResourceAllocationService",
        ),
        (
            "spec_extractor_base_batch5",
            "app/utils/spec_extractor/base.py",
            "SpecExtractor",
        ),
    ],
)
def test_placeholder_base_classes_can_be_instantiated(monkeypatch, module_name, relative_path, class_name):
    module = _load_module_from_path(monkeypatch, module_name, relative_path)
    cls = getattr(module, class_name)

    instance = cls()

    assert isinstance(instance, cls)


def test_invoice_service_generate_code_returns_prefixed_timestamp(monkeypatch):
    module = _load_module_from_path(monkeypatch, "invoice_service_batch5", "app/services/invoice_service.py")

    code = asyncio.run(module.InvoiceService.generate_code())

    assert re.fullmatch(r"INV\d{14}", code)


def test_batch_notification_mixin_sends_every_notification(monkeypatch):
    module = _load_module_from_path(
        monkeypatch,
        "batch_notification_mixin_batch5",
        "app/services/approval_engine/notify/batch.py",
    )

    class DummyNotifier(module.BatchNotificationMixin):
        def __init__(self):
            super().__init__(db="fake-db")
            self.sent = []

        def _send_notification(self, notification):
            self.sent.append(notification)

    notifications = [{"id": 1}, {"id": 2}]
    notifier = DummyNotifier()
    notifier.batch_notify(notifications)

    assert notifier.db == "fake-db"
    assert notifier.sent == notifications


def test_external_channels_mixin_logs_compat_messages(monkeypatch):
    module = _load_module_from_path(
        monkeypatch,
        "external_channels_mixin_batch5",
        "app/services/approval_engine/notify/external_channels.py",
    )
    debug = MagicMock()
    monkeypatch.setattr(module.logger, "debug", debug)

    mixin = module.ExternalChannelsMixin(db="fake-db")
    mixin._queue_email_notification({"title": "邮件标题"})
    mixin._queue_wechat_notification({"title": "企微标题"})

    messages = [call.args[0] for call in debug.call_args_list]
    assert mixin.db == "fake-db"
    assert any("[邮件]" in message and "邮件标题" in message for message in messages)
    assert any("[企微]" in message and "企微标题" in message for message in messages)


def test_core_security_reexports_and_is_admin(monkeypatch):
    auth_sentinels = {
        "create_token_pair": object(),
        "extract_jti_from_token": object(),
        "verify_refresh_token": object(),
        "check_permission": object(),
        "create_access_token": object(),
        "get_current_active_superuser": object(),
        "get_current_active_user": object(),
        "get_current_user": object(),
        "get_password_hash": object(),
        "is_token_revoked": object(),
        "oauth2_scheme": object(),
        "pwd_context": object(),
        "require_permission": object(),
        "revoke_token": object(),
        "revoke_token_jti": object(),
        "verify_password": object(),
        "is_system_admin": lambda user: getattr(user, "from_system", False),
    }
    sales_sentinels = {
        "check_sales_approval_permission": object(),
        "check_sales_create_permission": object(),
        "check_sales_data_permission": object(),
        "check_sales_delete_permission": object(),
        "check_sales_edit_permission": object(),
        "filter_sales_data_by_scope": object(),
        "filter_sales_finance_data_by_scope": object(),
        "get_sales_data_scope": object(),
        "has_sales_approval_access": object(),
        "has_sales_assessment_access": object(),
        "require_sales_approval_permission": object(),
        "require_sales_assessment_access": object(),
        "require_sales_create_permission": object(),
        "require_sales_delete_permission": object(),
        "require_sales_edit_permission": object(),
    }

    _register_module(monkeypatch, "compat_core_batch5", package=True)
    _register_module(monkeypatch, "compat_core_batch5.auth", **auth_sentinels)
    _register_module(monkeypatch, "compat_core_batch5.sales_permissions", **sales_sentinels)

    module = _load_module_from_path(
        monkeypatch,
        "compat_core_batch5.security",
        "app/core/security.py",
    )

    assert module.create_token_pair is auth_sentinels["create_token_pair"]
    assert module.get_sales_data_scope is sales_sentinels["get_sales_data_scope"]
    assert "is_admin" in module.__all__
    assert module.is_admin(SimpleNamespace(is_superuser=True, from_system=False)) is True
    assert module.is_admin(SimpleNamespace(is_superuser=False, from_system=True)) is True
    assert module.is_admin(SimpleNamespace(is_superuser=False, from_system=False)) is False
