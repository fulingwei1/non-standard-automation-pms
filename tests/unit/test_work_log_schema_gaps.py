import pytest

from app.schemas.work_log import WorkLogCreate, WorkLogUpdate


def test_work_log_create_rejects_blank_content():
    with pytest.raises(ValueError, match="工作内容不能为空"):
        WorkLogCreate(work_date="2026-04-14", content="   ")


def test_work_log_update_rejects_blank_content():
    with pytest.raises(ValueError, match="工作内容不能为空"):
        WorkLogUpdate(content="   ")
