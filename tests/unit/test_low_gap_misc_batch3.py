import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


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


def test_invoice_auto_logging_compat_delegates_when_service_and_order_present(monkeypatch):
    calls = []

    def _fake_log(service, order, created_items, auto_create):
        calls.append((service, order, created_items, auto_create))
        return "delegated"

    _register_module(monkeypatch, "compat_invoice_auto_service", package=True)
    _register_module(
        monkeypatch,
        "compat_invoice_auto_service.notifications",
        log_auto_invoice=_fake_log,
    )

    module = _load_module_from_path(
        monkeypatch,
        "compat_invoice_auto_service.logging",
        "app/services/invoice_auto_service/logging.py",
    )

    service = SimpleNamespace(db=object())
    order = object()

    assert module.log_auto_invoice(service, order, None, True) == "delegated"
    assert calls == [(service, order, [], True)]


def test_data_integrity_service_init_delegates_to_core_init(monkeypatch):
    class AutoFixMixin:
        pass

    class DataCheckMixin:
        pass

    class DataIntegrityCore:
        def __init__(self, db):
            self.initialized_with = db

    class ExportMixin:
        pass

    class RemindersMixin:
        pass

    class DataReportMixin:
        pass

    _register_module(monkeypatch, "compat_data_integrity.auto_fix", AutoFixMixin=AutoFixMixin)
    _register_module(monkeypatch, "compat_data_integrity.check", DataCheckMixin=DataCheckMixin)
    _register_module(monkeypatch, "compat_data_integrity.core", DataIntegrityCore=DataIntegrityCore)
    _register_module(monkeypatch, "compat_data_integrity.export", ExportMixin=ExportMixin)
    _register_module(monkeypatch, "compat_data_integrity.reminders", RemindersMixin=RemindersMixin)
    _register_module(monkeypatch, "compat_data_integrity.report", DataReportMixin=DataReportMixin)

    module = _load_module_from_path(
        monkeypatch,
        "compat_data_integrity",
        "app/services/data_integrity/__init__.py",
        package=True,
    )

    db = object()
    service = module.DataIntegrityService(db)

    assert service.initialized_with is db
    assert module.__all__ == ["DataIntegrityService"]


def test_strategy_dashboard_adapter_active_strategy_uses_base_get_stats(monkeypatch):
    class DashboardStatCard:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Strategy:
        is_active = object()

    class BaseAdapter:
        def __init__(self, db):
            self.db = db

        def get_stats(self):
            return ["base-stats"]

    class FakeQuery:
        def filter(self, *_args):
            return self

        def count(self):
            return 3

    class FakeDB:
        def query(self, _model):
            return FakeQuery()

    strategy_module = _register_absolute_module(
        monkeypatch,
        "app.services.strategy",
        get_active_strategy=lambda _db: object(),
    )
    _register_absolute_module(monkeypatch, "app.schemas.dashboard", DashboardStatCard=DashboardStatCard)
    _register_absolute_module(monkeypatch, "app.models.strategy", Strategy=Strategy)
    _register_absolute_module(
        monkeypatch,
        "app.services.dashboard.adapters.strategy",
        StrategyDashboardAdapter=BaseAdapter,
    )
    sys.modules["app.services"].strategy = strategy_module

    module = _load_module_from_path(
        monkeypatch,
        "compat_dashboard_strategy",
        "app/services/dashboard_adapters/strategy.py",
    )

    adapter = module.StrategyDashboardAdapter(FakeDB())
    assert adapter.get_stats() == ["base-stats"]


def test_ecn_bom_analysis_service_init_stores_db(monkeypatch):
    module = _load_module_from_path(
        monkeypatch,
        "compat_ecn_bom_analysis_base",
        "app/services/ecn/bom_analysis/base.py",
    )

    db = object()
    service = module.EcnBomAnalysisService(db)

    assert service.db is db
