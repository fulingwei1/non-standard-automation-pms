import importlib


def test_legacy_dashboard_adapters_package_imports_canonical_adapters():
    package = importlib.import_module("app.services.dashboard_adapters")

    assert package is not None

    strategy = importlib.import_module("app.services.dashboard_adapters.strategy")
    presales = importlib.import_module("app.services.dashboard_adapters.presales")
    shortage = importlib.import_module("app.services.dashboard_adapters.shortage")

    assert strategy.StrategyDashboardAdapter is not None
    assert presales.PresalesDashboardAdapter is not None
    assert shortage.ShortageDashboardAdapter is not None
