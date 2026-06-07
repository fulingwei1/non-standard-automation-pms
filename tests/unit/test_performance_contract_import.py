import importlib

from app.core.config import settings


def test_performance_contract_module_uses_configured_sqlite_path():
    module = importlib.import_module("app.api.v1.endpoints.performance.contract")

    assert module.DB_PATH == settings.SQLITE_DB_PATH
