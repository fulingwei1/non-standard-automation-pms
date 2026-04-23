from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.timesheet.reminders.service import TimesheetReminderService


def _query(*, first=None, count=0, all_result=None):
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.offset.return_value = q
    q.group_by.return_value = q
    q.count.return_value = count
    q.all.return_value = all_result or []
    q.first.return_value = first
    return q


def _service(db=None, manager=None):
    db = db or MagicMock()
    manager = manager or MagicMock()
    with patch("app.services.timesheet.reminders.service.TimesheetReminderManager", return_value=manager):
        service = TimesheetReminderService(db)
    return service, db, manager


def test_create_reminder_config_rejects_duplicate_rule_code():
    db = MagicMock()
    db.query.return_value = _query(first=SimpleNamespace(id=1))
    service, _, _ = _service(db=db)

    try:
        service.create_reminder_config(
            rule_code="RULE-1",
            rule_name="规则1",
            reminder_type="MISSING_TIMESHEET",
            created_by=1,
        )
    except ValueError as exc:
        assert "规则编码已存在: RULE-1" == str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_create_and_update_reminder_config_delegate_to_manager():
    db = MagicMock()
    db.query.return_value = _query(first=None)
    manager = MagicMock()
    created = SimpleNamespace(id=2)
    updated = SimpleNamespace(id=2, rule_name="已更新")
    manager.create_reminder_config.return_value = created
    manager.update_reminder_config.return_value = updated
    service, _, _ = _service(db=db, manager=manager)

    result = service.create_reminder_config(
        rule_code="RULE-2",
        rule_name="规则2",
        reminder_type="MISSING_TIMESHEET",
        created_by=99,
        rule_parameters={"check_days_ago": 1},
        apply_to_departments=[1],
        apply_to_roles=[2],
        apply_to_users=[3],
        notification_channels=["SYSTEM"],
        notification_template="tpl",
        remind_frequency="ONCE_DAILY",
        max_reminders_per_day=3,
        priority="HIGH",
    )
    updated_result = service.update_reminder_config(2, rule_name="已更新")

    assert result is created
    assert updated_result is updated
    kwargs = manager.create_reminder_config.call_args.kwargs
    assert kwargs["rule_code"] == "RULE-2"
    assert kwargs["reminder_type"].value == "MISSING_TIMESHEET"
    manager.update_reminder_config.assert_called_once_with(config_id=2, rule_name="已更新")


def test_list_reminder_configs_supports_filters_and_paging():
    db = MagicMock()
    expected = [SimpleNamespace(id=1)]
    db.query.return_value = _query(count=5, all_result=expected)
    service, _, _ = _service(db=db)

    records, total = service.list_reminder_configs(
        reminder_type="MISSING_TIMESHEET",
        is_active=True,
        limit=10,
        offset=20,
    )

    assert records == expected
    assert total == 5


def test_list_pending_reminders_and_history_support_filters():
    db = MagicMock()
    pending_query = _query(count=2, all_result=[SimpleNamespace(id=1), SimpleNamespace(id=2)])
    history_query = _query(count=3, all_result=[SimpleNamespace(id=3)])
    db.query.side_effect = [pending_query, history_query]
    service, _, _ = _service(db=db)

    reminders, reminder_total = service.list_pending_reminders(
        user_id=7,
        reminder_type="MISSING_TIMESHEET",
        priority="HIGH",
        limit=5,
        offset=1,
    )
    history, history_total = service.list_reminder_history(
        user_id=7,
        reminder_type="APPROVAL_TIMEOUT",
        status="SENT",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 30),
        limit=6,
        offset=2,
    )

    assert len(reminders) == 2
    assert reminder_total == 2
    assert history == [SimpleNamespace(id=3)]
    assert history_total == 3


def test_dismiss_and_mark_read_return_none_for_other_users():
    db = MagicMock()
    db.query.side_effect = [_query(first=None), _query(first=None)]
    service, _, manager = _service(db=db)

    assert service.dismiss_reminder(1, user_id=8, dismissed_by=9) is None
    assert service.mark_reminder_read(2, user_id=8) is None
    manager.dismiss_reminder.assert_not_called()
    manager.mark_reminder_read.assert_not_called()


def test_dismiss_and_mark_read_delegate_when_record_exists():
    db = MagicMock()
    db.query.side_effect = [_query(first=SimpleNamespace(id=1)), _query(first=SimpleNamespace(id=2))]
    manager = MagicMock()
    manager.dismiss_reminder.return_value = "dismissed"
    manager.mark_reminder_read.return_value = "read"
    service, _, _ = _service(db=db, manager=manager)

    assert service.dismiss_reminder(1, user_id=7, dismissed_by=9, reason="忽略") == "dismissed"
    assert service.mark_reminder_read(2, user_id=7) == "read"
    manager.dismiss_reminder.assert_called_once_with(reminder_id=1, dismissed_by=9, reason="忽略")
    manager.mark_reminder_read.assert_called_once_with(2)


def test_list_anomalies_supports_filters_and_paging():
    db = MagicMock()
    db.query.return_value = _query(count=4, all_result=[SimpleNamespace(id=1)])
    service, _, _ = _service(db=db)

    records, total = service.list_anomalies(
        user_id=5,
        anomaly_type="DAILY_OVER_12",
        is_resolved=False,
        limit=10,
        offset=3,
    )

    assert records == [SimpleNamespace(id=1)]
    assert total == 4


def test_resolve_anomaly_handles_missing_and_existing_record():
    db = MagicMock()
    manager = MagicMock()
    manager.resolve_anomaly.return_value = "resolved"
    db.query.side_effect = [_query(first=None), _query(first=SimpleNamespace(id=1))]
    service, _, _ = _service(db=db, manager=manager)

    assert service.resolve_anomaly(1, user_id=5, resolved_by=8) is None
    assert (
        service.resolve_anomaly(2, user_id=5, resolved_by=8, resolution_note="已处理")
        == "resolved"
    )
    manager.resolve_anomaly.assert_called_once_with(
        anomaly_id=2,
        resolved_by=8,
        resolution_note="已处理",
    )


def test_get_reminder_statistics_aggregates_counts_groups_and_recent_items():
    db = MagicMock()
    db.query.side_effect = [
        _query(count=10),
        _query(count=3),
        _query(count=2),
        _query(count=4),
        _query(count=1),
        _query(all_result=[("MISSING_TIMESHEET", 6), ("APPROVAL_TIMEOUT", 4)]),
        _query(all_result=[("HIGH", 5), ("URGENT", 1)]),
        _query(all_result=[SimpleNamespace(id=11), SimpleNamespace(id=12)]),
    ]
    service, _, _ = _service(db=db)

    stats = service.get_reminder_statistics(user_id=7)

    assert stats["total_reminders"] == 10
    assert stats["pending_reminders"] == 3
    assert stats["sent_reminders"] == 2
    assert stats["dismissed_reminders"] == 4
    assert stats["resolved_reminders"] == 1
    assert stats["by_type"] == {"MISSING_TIMESHEET": 6, "APPROVAL_TIMEOUT": 4}
    assert stats["by_priority"] == {"HIGH": 5, "URGENT": 1}
    assert [item.id for item in stats["recent_reminders"]] == [11, 12]


def test_get_anomaly_statistics_aggregates_counts_groups_and_recent_items():
    db = MagicMock()
    db.query.side_effect = [
        _query(count=9),
        _query(count=7),
        _query(count=2),
        _query(all_result=[("DAILY_OVER_12", 3), ("WEEKLY_OVER_60", 6)]),
        _query(all_result=[("HIGH", 4), ("LOW", 5)]),
        _query(all_result=[SimpleNamespace(id=21)]),
    ]
    service, _, _ = _service(db=db)

    stats = service.get_anomaly_statistics(user_id=7)

    assert stats["total_anomalies"] == 9
    assert stats["unresolved_anomalies"] == 7
    assert stats["resolved_anomalies"] == 2
    assert stats["by_type"] == {"DAILY_OVER_12": 3, "WEEKLY_OVER_60": 6}
    assert stats["by_severity"] == {"HIGH": 4, "LOW": 5}
    assert [item.id for item in stats["recent_anomalies"]] == [21]


def test_get_dashboard_combines_stats_active_configs_and_urgent_items():
    db = MagicMock()
    db.query.side_effect = [
        _query(all_result=[SimpleNamespace(id=1), SimpleNamespace(id=2)]),
        _query(all_result=[SimpleNamespace(id=3)]),
    ]
    service, _, _ = _service(db=db)
    service.get_reminder_statistics = MagicMock(return_value={"pending_reminders": 3})
    service.get_anomaly_statistics = MagicMock(return_value={"total_anomalies": 4})

    dashboard = service.get_dashboard(user_id=7)

    assert dashboard["reminder_stats"] == {"pending_reminders": 3}
    assert dashboard["anomaly_stats"] == {"total_anomalies": 4}
    assert [item.id for item in dashboard["active_configs"]] == [1, 2]
    assert [item.id for item in dashboard["urgent_items"]] == [3]
