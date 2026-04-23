from app.schemas.strategy.review import RoutineManagementCycleItem, RoutineManagementCycleResponse


def test_routine_management_cycle_item_backfills_cycle_fields_from_event_fields():
    item = RoutineManagementCycleItem(
        frequency="MONTHLY",
        event_type="MONTHLY_REVIEW",
        event_type_name="月度复盘",
    )

    assert item.cycle_type == "MONTHLY_REVIEW"
    assert item.cycle_name == "月度复盘"


def test_routine_management_cycle_response_combines_event_lists_when_cycles_empty():
    annual = RoutineManagementCycleItem(frequency="YEARLY", cycle_type="ANNUAL", cycle_name="年度审视")
    monthly = RoutineManagementCycleItem(frequency="MONTHLY", cycle_type="MONTHLY", cycle_name="月度复盘")

    response = RoutineManagementCycleResponse(
        strategy_id=1,
        annual_events=[annual],
        monthly_events=[monthly],
    )

    assert response.cycles == [annual, monthly]
