from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_legacy_ai_strategy_backend_route_is_not_mounted():
    api_source = read_text("app/api/v1/api.py")
    shim_source = read_text("app/api/v1/endpoints/ai_strategy.py")

    assert "include_router(ai_strategy_router" not in api_source
    assert 'prefix="/ai-strategy"' not in api_source
    assert "ai_strategy module placeholder" not in shim_source
    assert "legacy_ai_strategy_disabled" in shim_source
    assert "status_code=501" in shim_source


def test_ai_strategy_frontend_entry_and_dead_api_are_removed():
    service_barrel = read_text("frontend/src/services/api.js")
    strategy_routes = read_text("frontend/src/routes/modules/strategyRoutes.jsx")
    default_sidebar = read_text("frontend/src/components/layout/sidebarConfig/default.js")

    assert "aiStrategy.js" not in service_barrel
    assert not (ROOT / "frontend/src/services/api/aiStrategy.js").exists()
    assert "AIStrategyAssistant" not in strategy_routes
    assert "/strategy/ai-assistant" not in strategy_routes
    assert "AI战略助手" not in default_sidebar


def test_legacy_ai_strategy_contract_references_are_removed():
    contract_paths = [
        "tests/api/test_path_param_route_contracts.py",
        "tests/api/test_required_query_route_contracts.py",
        "tests/api/test_batch14_route_contracts.py",
    ]

    for relative_path in contract_paths:
        assert "/ai-strategy" not in read_text(relative_path)
