# -*- coding: utf-8 -*-
"""PRE-21：AI 后台任务重启恢复与超时终止契约。

进程内线程池不跨重启，重启后 DB 里遗留的 PENDING/RUNNING 任务永远无人推进；
轮询端点也没有超时判定。契约：
1. recover_stale_jobs() 在启动时把遗留 PENDING/RUNNING 任务标记为 FAILED（带可读原因）。
2. get() 对超过最大运行时长仍未完成的任务惰性判超时并标记 FAILED。
3. main.py startup 必须接线 recover_stale_jobs。
"""
from datetime import datetime, timedelta

from app.models.ai_job import AIGenerationJob
from app.services import ai_job_service


def _make_job(db, status: str, started_delta_minutes: int | None = None) -> AIGenerationJob:
    job = AIGenerationJob(
        job_type="three_tier_quotation",
        status=status,
        params={"presale_ticket_id": 1},
        progress=10 if status == "RUNNING" else 0,
        created_by=1,
    )
    if started_delta_minutes is not None:
        job.started_at = datetime.now() - timedelta(minutes=started_delta_minutes)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_recover_stale_jobs_marks_pending_and_running_failed(db_session):
    pending = _make_job(db_session, "PENDING")
    running = _make_job(db_session, "RUNNING", started_delta_minutes=5)
    success = _make_job(db_session, "SUCCESS")

    recovered = ai_job_service.recover_stale_jobs(db_session)
    assert recovered >= 2

    db_session.expire_all()
    pending = db_session.get(AIGenerationJob, pending.id)
    running = db_session.get(AIGenerationJob, running.id)
    success = db_session.get(AIGenerationJob, success.id)

    assert pending.status == "FAILED"
    assert running.status == "FAILED"
    assert pending.finished_at is not None
    assert "重启" in (pending.error or "")
    assert success.status == "SUCCESS"


def test_get_marks_overtime_running_job_failed(db_session):
    stuck = _make_job(db_session, "RUNNING", started_delta_minutes=24 * 60)

    fetched = ai_job_service.get(db_session, stuck.id)

    assert fetched is not None
    assert fetched.status == "FAILED"
    assert "超时" in (fetched.error or "")
    assert fetched.finished_at is not None


def test_get_keeps_fresh_running_job_untouched(db_session):
    fresh = _make_job(db_session, "RUNNING", started_delta_minutes=1)

    fetched = ai_job_service.get(db_session, fresh.id)

    assert fetched.status == "RUNNING"
    assert fetched.error is None


def test_startup_wires_recover_stale_jobs():
    import inspect

    import app.main as main_module

    source = inspect.getsource(main_module)
    assert "recover_stale_jobs" in source, "main.py startup 未接线 AI 任务恢复"
