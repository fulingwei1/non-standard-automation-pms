import pytest

from app.schemas.scheduler_config import SchedulerTaskConfigUpdate


def test_scheduler_task_config_update_allows_none_cron_config():
    schema = SchedulerTaskConfigUpdate(cron_config=None)

    assert schema.cron_config is None


def test_scheduler_task_config_update_accepts_valid_cron_field():
    schema = SchedulerTaskConfigUpdate(cron_config={"minute": "*/5"})

    assert schema.cron_config == {"minute": "*/5"}


def test_scheduler_task_config_update_rejects_invalid_cron_field():
    with pytest.raises(ValueError, match="无效的Cron字段: invalid"):
        SchedulerTaskConfigUpdate(cron_config={"invalid": "*"})
