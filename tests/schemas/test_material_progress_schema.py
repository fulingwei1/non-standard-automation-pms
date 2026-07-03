from decimal import Decimal

from app.schemas.material_progress import MaterialProgressOverview


def test_material_progress_overview_accepts_key_material_without_material_id():
    payload = {
        "project_id": 61,
        "project_code": "PJ-61",
        "project_name": "QA Project",
        "total_bom_items": 1,
        "kitted_items": 0,
        "in_progress_items": 1,
        "shortage_items": 0,
        "kitting_rate": Decimal("0"),
        "key_materials": [
            {
                "material_id": None,
                "material_code": "M-001",
                "material_name": "Unlinked material",
                "required_qty": Decimal("1"),
                "received_qty": Decimal("0"),
                "shortage_qty": Decimal("1"),
                "kitting_status": "PENDING",
            }
        ],
        "kitting_trend": [],
    }

    overview = MaterialProgressOverview.model_validate(payload)

    assert overview.key_materials[0].material_id is None
