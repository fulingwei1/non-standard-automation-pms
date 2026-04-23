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
    ("relative_path", "source_module", "export_name"),
    [
        (
            "app/services/notification_handlers/email_handler.py",
            "app.services.notification.handlers.email_handler",
            "EmailNotificationHandler",
        ),
        (
            "app/services/notification_handlers/sms_handler.py",
            "app.services.notification.handlers.sms_handler",
            "SMSNotificationHandler",
        ),
        (
            "app/services/notification_handlers/unified_adapter.py",
            "app.services.notification.handlers.unified_adapter",
            "send_alert_via_unified",
        ),
        (
            "app/services/notification_handlers/wechat_handler.py",
            "app.services.notification.handlers.wechat_handler",
            "WeChatNotificationHandler",
        ),
    ],
)
def test_notification_handler_compat_shims_reexport_target_symbols(
    monkeypatch, relative_path, source_module, export_name
):
    _register_module(monkeypatch, "app.services.notification", package=True)
    _register_module(monkeypatch, "app.services.notification.handlers", package=True)

    sentinel = object()
    _register_module(
        monkeypatch,
        source_module,
        __all__=[export_name],
        **{export_name: sentinel},
    )

    module = _load_module_from_path(
        monkeypatch,
        f"compat_{export_name.lower()}",
        relative_path,
    )

    assert getattr(module, export_name) is sentinel


def test_notification_handlers_package_reexports_all_handlers(monkeypatch):
    _register_module(monkeypatch, "app.services.notification_handlers", package=True)

    class SystemNotificationHandler:
        pass

    class EmailNotificationHandler:
        pass

    class WeChatNotificationHandler:
        pass

    class SMSNotificationHandler:
        pass

    _register_module(
        monkeypatch,
        "app.services.notification_handlers.system_handler",
        SystemNotificationHandler=SystemNotificationHandler,
    )
    _register_module(
        monkeypatch,
        "app.services.notification_handlers.email_handler",
        EmailNotificationHandler=EmailNotificationHandler,
    )
    _register_module(
        monkeypatch,
        "app.services.notification_handlers.wechat_handler",
        WeChatNotificationHandler=WeChatNotificationHandler,
    )
    _register_module(
        monkeypatch,
        "app.services.notification_handlers.sms_handler",
        SMSNotificationHandler=SMSNotificationHandler,
    )

    module = _load_module_from_path(
        monkeypatch,
        "compat_notification_handlers_pkg",
        "app/services/notification_handlers/__init__.py",
        package=True,
    )

    assert module.SystemNotificationHandler is SystemNotificationHandler
    assert module.EmailNotificationHandler is EmailNotificationHandler
    assert module.WeChatNotificationHandler is WeChatNotificationHandler
    assert module.SMSNotificationHandler is SMSNotificationHandler
    assert module.__all__ == [
        "SystemNotificationHandler",
        "EmailNotificationHandler",
        "WeChatNotificationHandler",
        "SMSNotificationHandler",
    ]


@pytest.mark.parametrize(
    ("module_name", "relative_path", "service_module", "export_name"),
    [
        (
            "compat_timesheet_records_pkg",
            "app/services/timesheet/records/__init__.py",
            "app.services.timesheet.records.service",
            "TimesheetRecordsService",
        ),
        (
            "compat_timesheet_reminders_pkg",
            "app/services/timesheet/reminders/__init__.py",
            "app.services.timesheet.reminders.service",
            "TimesheetReminderService",
        ),
    ],
)
def test_timesheet_packages_reexport_service_classes(
    monkeypatch, module_name, relative_path, service_module, export_name
):
    _register_module(monkeypatch, "app.services.timesheet", package=True)
    _register_module(monkeypatch, service_module.rsplit(".", 1)[0], package=True)

    sentinel = type(export_name, (), {})
    _register_module(monkeypatch, service_module, **{export_name: sentinel})

    module = _load_module_from_path(
        monkeypatch,
        module_name,
        relative_path,
        package=True,
    )

    assert getattr(module, export_name) is sentinel
    assert module.__all__ == [export_name]


def test_bom_package_reexports_cost_breakdown_models(monkeypatch):
    class CostBreakdown:
        pass

    class ProjectCostSummary:
        pass

    _register_module(
        monkeypatch,
        "compat_bom_pkg.cost_breakdown",
        CostBreakdown=CostBreakdown,
        ProjectCostSummary=ProjectCostSummary,
    )

    module = _load_module_from_path(
        monkeypatch,
        "compat_bom_pkg",
        "app/models/bom/__init__.py",
        package=True,
    )

    assert module.CostBreakdown is CostBreakdown
    assert module.ProjectCostSummary is ProjectCostSummary
    assert module.__all__ == ["CostBreakdown", "ProjectCostSummary"]


def test_scheduler_config_compat_module_reexports_scheduler_tasks(monkeypatch):
    tasks = [{"id": "demo-job", "enabled": True}]
    _register_module(monkeypatch, "app.utils.scheduler_config", SCHEDULER_TASKS=tasks)

    module = _load_module_from_path(
        monkeypatch,
        "compat_scheduler_config",
        "app/utils/scheduler_config.py",
    )

    assert module.SCHEDULER_TASKS is tasks
    assert module.__all__ == ["SCHEDULER_TASKS"]
