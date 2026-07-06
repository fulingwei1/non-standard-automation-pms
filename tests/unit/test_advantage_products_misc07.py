from inspect import signature
from pathlib import Path

from app.modules.presale.api.advantage_products.import_excel import import_from_excel


def test_advantage_product_import_defaults_to_non_destructive_mode():
    clear_existing = signature(import_from_excel).parameters["clear_existing"]
    actual_default = getattr(clear_existing.default, "default", clear_existing.default)

    assert actual_default is False


def test_advantage_products_have_reachable_frontend_route_and_sidebar_entry():
    routes_source = Path("frontend/src/routes/modules/presalesRoutes.jsx").read_text()
    sidebar_source = Path("frontend/src/components/layout/sidebarConfig/default.js").read_text()

    assert "../../components/sales/AdvantageProducts" in routes_source
    assert 'path="/presales/advantage-products"' in routes_source
    assert '"优势产品"' in sidebar_source
    assert 'path: "/presales/advantage-products"' in sidebar_source


def test_advantage_products_search_input_does_not_render_unknown_by_default():
    source = Path("frontend/src/components/sales/AdvantageProducts.jsx").read_text()

    assert 'value={searchTerm || "unknown"}' not in source
    assert "value={searchTerm}" in source
