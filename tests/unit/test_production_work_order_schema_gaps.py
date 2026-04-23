from app.schemas.production.work_order import WorkOrderAssignRequest


def test_work_order_assign_request_keeps_non_dict_input_and_exposes_worker_id_alias():
    schema = WorkOrderAssignRequest(worker_id=7)

    assert schema.assigned_to == 7
    assert schema.worker_id == 7

    payload = WorkOrderAssignRequest._normalize_worker_id(5)
    assert payload == 5
