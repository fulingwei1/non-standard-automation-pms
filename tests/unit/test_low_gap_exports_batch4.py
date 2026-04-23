import importlib.util
import sys
from pathlib import Path
from types import ModuleType

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

    spec = importlib.util.spec_from_file_location(module_name, module_path, **kwargs)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("module_name", "relative_path", "child_module", "export_names", "expected_all"),
    [
        (
            "compat_acceptance_approval_pkg_batch4",
            "app/services/acceptance_approval/__init__.py",
            "service",
            ["AcceptanceApprovalService"],
            ["AcceptanceApprovalService"],
        ),
        (
            "compat_business_support_utils_pkg_batch4",
            "app/services/business_support_utils/__init__.py",
            "service",
            ["BusinessSupportUtilsService"],
            ["BusinessSupportUtilsService"],
        ),
        (
            "compat_contract_approval_pkg_batch4",
            "app/services/contract_approval/__init__.py",
            "service",
            ["ContractApprovalService"],
            ["ContractApprovalService"],
        ),
        (
            "compat_permission_management_pkg_batch4",
            "app/services/permission_management/__init__.py",
            "permission_management_service",
            ["PermissionManagementService"],
            ["PermissionManagementService"],
        ),
        (
            "compat_pmo_cockpit_pkg_batch4",
            "app/services/pmo_cockpit/__init__.py",
            "pmo_cockpit_service",
            ["PmoCockpitService"],
            ["PmoCockpitService"],
        ),
        (
            "compat_pmo_initiation_pkg_batch4",
            "app/services/pmo_initiation/__init__.py",
            "service",
            ["PmoInitiationService"],
            ["PmoInitiationService"],
        ),
        (
            "compat_purchase_intelligence_pkg_batch4",
            "app/services/purchase_intelligence/__init__.py",
            "service",
            ["PurchaseIntelligenceService"],
            ["PurchaseIntelligenceService"],
        ),
        (
            "compat_report_pkg_batch4",
            "app/services/report/__init__.py",
            "report_service",
            ["ReportService"],
            ["ReportService"],
        ),
        (
            "compat_shortage_alerts_pkg_batch4",
            "app/services/shortage_alerts/__init__.py",
            "service",
            ["ShortageAlertService"],
            ["ShortageAlertService"],
        ),
        (
            "compat_shortage_analytics_pkg_batch4",
            "app/services/shortage_analytics/__init__.py",
            "shortage_analytics_service",
            ["ShortageAnalyticsService"],
            ["ShortageAnalyticsService"],
        ),
        (
            "compat_team_performance_pkg_batch4",
            "app/services/team_performance/__init__.py",
            "service",
            ["TeamPerformanceService"],
            ["TeamPerformanceService"],
        ),
    ],
)
def test_relative_service_packages_reexport_expected_symbols(
    monkeypatch, module_name, relative_path, child_module, export_names, expected_all
):
    sentinels = {name: object() for name in export_names}
    _register_module(monkeypatch, f"{module_name}.{child_module}", **sentinels)

    module = _load_module_from_path(
        monkeypatch,
        module_name,
        relative_path,
        package=True,
    )

    for export_name, sentinel in sentinels.items():
        assert getattr(module, export_name) is sentinel

    assert module.__all__ == expected_all


def test_acceptance_package_reexports_report_utils_symbols(monkeypatch):
    sentinels = {
        "build_report_content": object(),
        "generate_report_no": object(),
        "get_report_version": object(),
        "save_report_file": object(),
    }
    _register_absolute_module(
        monkeypatch,
        "app.services.acceptance.report_utils",
        **sentinels,
    )

    module = _load_module_from_path(
        monkeypatch,
        "compat_acceptance_pkg_batch4",
        "app/services/acceptance/__init__.py",
        package=True,
    )

    for export_name, sentinel in sentinels.items():
        assert getattr(module, export_name) is sentinel

    assert module.__all__ == [
        "generate_report_no",
        "get_report_version",
        "save_report_file",
        "build_report_content",
    ]


def test_statistics_package_reexports_sync_statistics_symbols(monkeypatch):
    sentinels = {
        "AggregationServiceProtocol": object(),
        "SyncStatisticsService": object(),
    }
    _register_absolute_module(
        monkeypatch,
        "app.services.statistics.base",
        **sentinels,
    )

    module = _load_module_from_path(
        monkeypatch,
        "compat_statistics_pkg_batch4",
        "app/services/statistics/__init__.py",
        package=True,
    )

    assert module.SyncStatisticsService is sentinels["SyncStatisticsService"]
    assert module.AggregationServiceProtocol is sentinels["AggregationServiceProtocol"]
    assert module.__all__ == ["SyncStatisticsService", "AggregationServiceProtocol"]


@pytest.mark.parametrize(
    ("module_name", "relative_path", "export_name"),
    [
        ("scheduler_alerting_batch4", "app/utils/scheduler_config/alerting.py", "ALERTING_TASKS"),
        ("scheduler_finance_batch4", "app/utils/scheduler_config/finance.py", "FINANCE_TASKS"),
        (
            "scheduler_issue_management_batch4",
            "app/utils/scheduler_config/issue_management.py",
            "ISSUE_MANAGEMENT_TASKS",
        ),
        ("scheduler_milestone_batch4", "app/utils/scheduler_config/milestone.py", "MILESTONE_TASKS"),
        ("scheduler_other_batch4", "app/utils/scheduler_config/other.py", "OTHER_TASKS"),
        ("scheduler_production_batch4", "app/utils/scheduler_config/production.py", "PRODUCTION_TASKS"),
        (
            "scheduler_project_health_batch4",
            "app/utils/scheduler_config/project_health.py",
            "PROJECT_HEALTH_TASKS",
        ),
        ("scheduler_risk_batch4", "app/utils/scheduler_config/risk.py", "RISK_TASKS"),
        ("scheduler_schedule_batch4", "app/utils/scheduler_config/schedule.py", "SCHEDULE_TASKS"),
        ("scheduler_shortage_batch4", "app/utils/scheduler_config/shortage.py", "SHORTAGE_TASKS"),
        ("scheduler_timesheet_batch4", "app/utils/scheduler_config/timesheet.py", "TIMESHEET_TASKS"),
    ],
)
def test_scheduler_category_modules_define_non_empty_task_lists(
    monkeypatch, module_name, relative_path, export_name
):
    module = _load_module_from_path(monkeypatch, module_name, relative_path)
    tasks = getattr(module, export_name)

    assert isinstance(tasks, list)
    assert tasks
    assert all(
        {"id", "module", "callable", "cron", "enabled", "risk_level", "sla"}.issubset(task)
        for task in tasks
    )


def test_scheduler_config_package_aggregates_category_lists_in_declared_order(monkeypatch):
    category_specs = [
        ("alerting", "ALERTING_TASKS", [{"id": "alerting"}]),
        ("finance", "FINANCE_TASKS", [{"id": "finance"}]),
        ("issue_management", "ISSUE_MANAGEMENT_TASKS", [{"id": "issue_management"}]),
        ("milestone", "MILESTONE_TASKS", [{"id": "milestone"}]),
        ("other", "OTHER_TASKS", [{"id": "other"}]),
        ("production", "PRODUCTION_TASKS", [{"id": "production"}]),
        ("project_health", "PROJECT_HEALTH_TASKS", [{"id": "project_health"}]),
        ("risk", "RISK_TASKS", [{"id": "risk"}]),
        ("schedule", "SCHEDULE_TASKS", [{"id": "schedule"}]),
        ("shortage", "SHORTAGE_TASKS", [{"id": "shortage"}]),
        ("timesheet", "TIMESHEET_TASKS", [{"id": "timesheet"}]),
    ]

    for child_module, export_name, tasks in category_specs:
        _register_module(
            monkeypatch,
            f"compat_scheduler_config_pkg_batch4.{child_module}",
            **{export_name: tasks},
        )

    module = _load_module_from_path(
        monkeypatch,
        "compat_scheduler_config_pkg_batch4",
        "app/utils/scheduler_config/__init__.py",
        package=True,
    )

    assert module.SCHEDULER_TASKS == [
        {"id": "project_health"},
        {"id": "risk"},
        {"id": "issue_management"},
        {"id": "milestone"},
        {"id": "shortage"},
        {"id": "production"},
        {"id": "finance"},
        {"id": "schedule"},
        {"id": "alerting"},
        {"id": "timesheet"},
        {"id": "other"},
    ]
    assert module.__all__ == ["SCHEDULER_TASKS"]
