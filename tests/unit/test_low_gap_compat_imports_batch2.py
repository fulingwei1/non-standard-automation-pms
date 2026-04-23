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


def _register_absolute_module(monkeypatch, name: str, **attrs):
    parts = name.split(".")
    for i in range(1, len(parts)):
        _register_module(monkeypatch, ".".join(parts[:i]), package=True)
    return _register_module(monkeypatch, name, **attrs)


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
    ("module_name", "relative_path", "source_module", "export_names", "expected_all", "package"),
    [
        (
            "compat_shortage_report_service_batch2",
            "app/services/shortage_report_service.py",
            "app.services.shortage.shortage_reports_service",
            [
                "ShortageReportsService",
                "build_daily_report_data",
                "calculate_alert_statistics",
                "calculate_arrival_statistics",
                "calculate_kit_statistics",
                "calculate_report_statistics",
                "calculate_response_time_statistics",
                "calculate_stoppage_statistics",
            ],
            None,
            False,
        ),
        (
            "compat_permission_service_batch2",
            "app/services/permission_service.py",
            "app.services.permission_management.permission_service",
            ["PermissionService", "check_permission_compat", "has_module_permission"],
            ["PermissionService", "check_permission_compat", "has_module_permission"],
            False,
        ),
        (
            "compat_permission_audit_service_batch2",
            "app/services/permission_audit_service.py",
            "app.services.permission_management.permission_audit_service",
            ["PermissionAuditService", "get_permission_audit_service"],
            ["PermissionAuditService", "get_permission_audit_service"],
            False,
        ),
        (
            "compat_cost_forecast_service_batch2",
            "app/services/cost_forecast_service.py",
            "app.services.cost.cost_forecast_service",
            ["CostForecastService"],
            ["CostForecastService"],
            False,
        ),
        (
            "compat_cost_prediction_service_batch2",
            "app/services/cost_prediction_service.py",
            "app.services.cost.cost_prediction_service",
            ["CostPredictionService", "GLM5CostPredictor"],
            ["CostPredictionService", "GLM5CostPredictor"],
            False,
        ),
        (
            "compat_presale_ai_service_batch2",
            "app/services/presale_ai_service.py",
            "app.services.presale.presale_ai_service",
            ["PresaleAIService"],
            ["PresaleAIService"],
            False,
        ),
        (
            "compat_task_progress_service_batch2",
            "app/services/task_progress_service.py",
            "app.services.progress_service",
            ["apply_task_progress_update", "progress_error_to_http", "update_task_progress"],
            ["apply_task_progress_update", "progress_error_to_http", "update_task_progress"],
            False,
        ),
        (
            "compat_rate_limit_batch2",
            "app/core/rate_limit.py",
            "app.core.rate_limiting",
            [
                "limiter",
                "user_limiter",
                "strict_limiter",
                "get_remote_address",
                "get_user_or_ip",
                "get_ip_and_user",
            ],
            [
                "limiter",
                "user_limiter",
                "strict_limiter",
                "get_remote_address",
                "get_user_or_ip",
                "get_ip_and_user",
            ],
            False,
        ),
        (
            "compat_common_dashboard_pkg_batch2",
            "app/common/dashboard/__init__.py",
            "app.common.dashboard.base",
            ["BaseDashboardService"],
            ["BaseDashboardService"],
            True,
        ),
        (
            "compat_project_members_pkg_batch2",
            "app/services/project_members/__init__.py",
            "app.services.project_members.service",
            ["ProjectMembersService"],
            ["ProjectMembersService"],
            True,
        ),
        (
            "compat_resource_scheduling_pkg_batch2",
            "app/services/resource_scheduling/__init__.py",
            "app.services.resource_scheduling.resource_scheduling_service",
            ["ResourceSchedulingService"],
            ["ResourceSchedulingService"],
            True,
        ),
        (
            "compat_report_formatters_pkg_batch2",
            "app/services/report_framework/formatters/__init__.py",
            "app.services.report_framework.formatters.builtin",
            ["format_currency", "format_date", "format_percentage", "format_status_badge"],
            ["format_status_badge", "format_percentage", "format_currency", "format_date"],
            True,
        ),
        (
            "compat_ecn_cost_impact_pkg_batch2",
            "app/services/ecn_cost_impact_service/__init__.py",
            "app.services.ecn.ecn_cost_impact_service",
            [
                "cost_impact_analysis",
                "get_cost_tracking",
                "create_cost_record",
                "list_cost_records",
                "approve_cost_record",
                "get_project_ecn_cost_summary",
                "check_cost_alerts",
                "COST_TYPE_LABELS",
                "DIRECT_COST_TYPES",
                "INDIRECT_COST_TYPES",
            ],
            [
                "cost_impact_analysis",
                "get_cost_tracking",
                "create_cost_record",
                "list_cost_records",
                "approve_cost_record",
                "get_project_ecn_cost_summary",
                "check_cost_alerts",
                "COST_TYPE_LABELS",
                "DIRECT_COST_TYPES",
                "INDIRECT_COST_TYPES",
            ],
            True,
        ),
    ],
)
def test_absolute_compat_modules_reexport_expected_symbols(
    monkeypatch, module_name, relative_path, source_module, export_names, expected_all, package
):
    sentinels = {name: object() for name in export_names}
    _register_absolute_module(monkeypatch, source_module, **sentinels)

    module = _load_module_from_path(
        monkeypatch,
        module_name,
        relative_path,
        package=package,
    )

    for export_name, sentinel in sentinels.items():
        assert getattr(module, export_name) is sentinel

    if expected_all is not None:
        assert module.__all__ == expected_all


@pytest.mark.parametrize(
    ("module_name", "relative_path", "child_module", "export_names", "expected_all"),
    [
        (
            "compat_core_decorators_pkg_batch2",
            "app/core/decorators/__init__.py",
            "tenant_isolation",
            ["allow_cross_tenant", "require_tenant_isolation", "tenant_resource_check"],
            ["require_tenant_isolation", "allow_cross_tenant", "tenant_resource_check"],
        ),
        (
            "compat_core_permissions_pkg_batch2",
            "app/core/permissions/__init__.py",
            "timesheet",
            [
                "apply_timesheet_access_filter",
                "check_bulk_timesheet_approval_permission",
                "check_timesheet_approval_permission",
                "get_user_manageable_dimensions",
                "has_timesheet_approval_access",
                "is_timesheet_admin",
                "require_timesheet_approval_access",
            ],
            [
                "is_timesheet_admin",
                "get_user_manageable_dimensions",
                "apply_timesheet_access_filter",
                "check_timesheet_approval_permission",
                "check_bulk_timesheet_approval_permission",
                "has_timesheet_approval_access",
                "require_timesheet_approval_access",
            ],
        ),
        (
            "compat_services_dashboard_pkg_batch2",
            "app/services/dashboard/__init__.py",
            "base",
            ["BaseDashboardService", "DateRange"],
            ["BaseDashboardService", "DateRange"],
        ),
        (
            "compat_services_export_pkg_batch2",
            "app/services/export/__init__.py",
            "watermark_service",
            ["WatermarkConfig", "WatermarkService", "add_watermark_to_excel", "add_watermark_to_pdf"],
            ["WatermarkConfig", "WatermarkService", "add_watermark_to_pdf", "add_watermark_to_excel"],
        ),
        (
            "compat_best_practices_pkg_batch2",
            "app/services/best_practices/__init__.py",
            "best_practices_service",
            ["BestPracticesService"],
            ["BestPracticesService"],
        ),
        (
            "compat_quote_approval_pkg_batch2",
            "app/services/quote_approval/__init__.py",
            "quote_approval_service",
            ["QuoteApprovalService"],
            ["QuoteApprovalService"],
        ),
    ],
)
def test_relative_init_packages_reexport_expected_symbols(
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
