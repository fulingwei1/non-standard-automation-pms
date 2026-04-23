from app.schemas.production.work_order import WorkOrderAssignRequest


def test_work_order_assign_normalizes_worker_id_alias_and_property():
    req = WorkOrderAssignRequest.model_validate({"worker_id": 9, "workstation_id": 3})

    assert req.assigned_to == 9
    assert req.worker_id == 9
    assert WorkOrderAssignRequest._normalize_worker_id({"worker_id": 9}) == {"worker_id": 9, "assigned_to": 9}


def test_work_order_assign_normalize_worker_id_returns_raw_for_non_dict():
    sentinel = object()

    assert WorkOrderAssignRequest._normalize_worker_id(sentinel) is sentinel
