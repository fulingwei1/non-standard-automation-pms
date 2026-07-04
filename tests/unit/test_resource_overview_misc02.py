from pathlib import Path

from app.schemas.pmo import ResourceOverviewResponse


ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_legacy_resource_overview_route_is_not_mounted_as_placeholder():
    api_source = read_text("app/api/v1/api.py")
    shim_source = read_text("app/api/v1/endpoints/resource_overview.py")

    assert "include_router(resource_overview_router" not in api_source
    assert 'prefix="/resource-overview"' not in api_source
    assert "resource_overview module placeholder" not in shim_source
    assert "legacy_resource_overview_disabled" in shim_source
    assert "status_code=501" in shim_source


def test_pmo_resource_overview_response_contains_timeline_payload():
    fields = ResourceOverviewResponse.model_fields

    assert "total_employees" in fields
    assert "employees_with_conflicts" in fields
    assert "total_conflicts" in fields
    assert "avg_utilization" in fields
    assert "employees" in fields

    response = ResourceOverviewResponse(
        total_resources=1,
        allocated_resources=1,
        available_resources=0,
        overloaded_resources=1,
        total_employees=1,
        employees_with_conflicts=1,
        total_conflicts=1,
        avg_utilization=120,
        employees=[
            {
                "user_id": 7,
                "real_name": "张三",
                "department": "研发部",
                "current_allocation": 120,
                "total_projects": 2,
                "has_conflict": True,
                "conflicts": [{"total_allocation": 120, "projects": ["A", "B"]}],
                "allocations": [{"project_id": 1, "project_name": "A", "allocation_pct": 60}],
            }
        ],
    )

    assert response.employees[0]["allocations"][0]["project_name"] == "A"


def test_frontend_resource_overview_service_uses_pmo_endpoint_only():
    service_source = read_text("frontend/src/services/api/resourceOverview.js")

    assert 'api.get("/pmo/resource-overview"' in service_source
    assert 'api.get("/resource-overview' not in service_source
