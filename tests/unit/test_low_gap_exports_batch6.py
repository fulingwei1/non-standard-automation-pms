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


def _make_adapter(name: str):
    class Adapter:
        def __init__(self, db):
            self.db = db

    Adapter.__name__ = name
    return Adapter


def test_approval_engine_adapters_package_exposes_registry_and_factory(monkeypatch):
    adapter_specs = [
        ("acceptance", "AcceptanceOrderApprovalAdapter", "ACCEPTANCE_ORDER"),
        ("base", "ApprovalAdapter", None),
        ("contract", "ContractApprovalAdapter", "CONTRACT"),
        ("ecn", "EcnApprovalAdapter", "ECN"),
        ("invoice", "InvoiceApprovalAdapter", "INVOICE"),
        ("outsourcing", "OutsourcingOrderApprovalAdapter", "OUTSOURCING_ORDER"),
        ("project", "ProjectApprovalAdapter", "PROJECT"),
        ("purchase", "PurchaseOrderApprovalAdapter", "PURCHASE_ORDER"),
        ("quote", "QuoteApprovalAdapter", "QUOTE"),
        ("timesheet", "TimesheetApprovalAdapter", "TIMESHEET"),
    ]

    classes = {}
    for child_module, class_name, _registry_key in adapter_specs:
        cls = _make_adapter(class_name)
        classes[class_name] = cls
        _register_module(monkeypatch, f"compat_approval_adapters_pkg_batch6.{child_module}", **{class_name: cls})

    module = _load_module_from_path(
        monkeypatch,
        "compat_approval_adapters_pkg_batch6",
        "app/services/approval_engine/adapters/__init__.py",
        package=True,
    )

    assert module.__all__ == [
        "ApprovalAdapter",
        "QuoteApprovalAdapter",
        "ContractApprovalAdapter",
        "InvoiceApprovalAdapter",
        "EcnApprovalAdapter",
        "ProjectApprovalAdapter",
        "TimesheetApprovalAdapter",
        "PurchaseOrderApprovalAdapter",
        "OutsourcingOrderApprovalAdapter",
        "AcceptanceOrderApprovalAdapter",
    ]
    assert module.ADAPTER_REGISTRY["QUOTE"] is classes["QuoteApprovalAdapter"]
    assert module.ADAPTER_REGISTRY["ACCEPTANCE_ORDER"] is classes["AcceptanceOrderApprovalAdapter"]

    db = object()
    adapter = module.get_adapter("PROJECT", db)
    assert isinstance(adapter, classes["ProjectApprovalAdapter"])
    assert adapter.db is db

    with pytest.raises(ValueError, match="不支持的业务类型"):
        module.get_adapter("UNKNOWN", db)


def test_approval_notify_service_initializes_and_caches_unified_service(monkeypatch):
    class NotificationService:
        pass

    class ApprovalNotifyServiceBase:
        def __init__(self, db):
            self.db = db

    class BasicNotificationsMixin:
        pass

    class BatchNotificationMixin:
        pass

    class CommentNotificationsMixin:
        pass

    class ExternalChannelsMixin:
        pass

    class FlowNotificationsMixin:
        pass

    class ReminderNotificationsMixin:
        pass

    class SendNotificationMixin:
        pass

    class NotificationUtilsMixin:
        pass

    service_instance = NotificationService()
    calls = []

    def fake_get_notification_service(db):
        calls.append(db)
        return service_instance

    _register_absolute_module(
        monkeypatch,
        "app.services.notification.unified_notification_service",
        NotificationService=NotificationService,
        get_notification_service=fake_get_notification_service,
    )

    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.base",
        ApprovalNotifyServiceBase=ApprovalNotifyServiceBase,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.basic_notifications",
        BasicNotificationsMixin=BasicNotificationsMixin,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.batch",
        BatchNotificationMixin=BatchNotificationMixin,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.comment_notifications",
        CommentNotificationsMixin=CommentNotificationsMixin,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.external_channels",
        ExternalChannelsMixin=ExternalChannelsMixin,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.flow_notifications",
        FlowNotificationsMixin=FlowNotificationsMixin,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.reminder_notifications",
        ReminderNotificationsMixin=ReminderNotificationsMixin,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.send_notification",
        SendNotificationMixin=SendNotificationMixin,
    )
    _register_module(
        monkeypatch,
        "compat_approval_notify_pkg_batch6.utils",
        NotificationUtilsMixin=NotificationUtilsMixin,
    )

    module = _load_module_from_path(
        monkeypatch,
        "compat_approval_notify_pkg_batch6",
        "app/services/approval_engine/notify/__init__.py",
        package=True,
    )

    db = object()
    service = module.ApprovalNotifyService(db)

    assert service.db is db
    assert service._unified_service is None
    assert module.__all__ == ["ApprovalNotifyService"]

    assert service.get_unified_service() is service_instance
    assert service.get_unified_service() is service_instance
    assert calls == [db]


def test_plugins_package_reexports_core_and_hook_symbols(monkeypatch):
    core_symbols = {
        "Plugin": object(),
        "PluginConfig": object(),
        "PluginManager": object(),
        "PluginMetadata": object(),
        "PluginStatus": object(),
        "get_plugin_manager": object(),
    }
    hook_symbols = {
        "EventHook": object(),
        "HookManager": object(),
        "hook": object(),
    }

    _register_module(monkeypatch, "compat_plugins_pkg_batch6.core", **core_symbols)
    _register_module(monkeypatch, "compat_plugins_pkg_batch6.hooks", **hook_symbols)

    module = _load_module_from_path(
        monkeypatch,
        "compat_plugins_pkg_batch6",
        "app/plugins/__init__.py",
        package=True,
    )

    for name, value in {**core_symbols, **hook_symbols}.items():
        assert getattr(module, name) is value

    assert module.__all__ == [
        "Plugin",
        "PluginConfig",
        "PluginManager",
        "PluginMetadata",
        "PluginStatus",
        "get_plugin_manager",
        "EventHook",
        "HookManager",
        "hook",
    ]
