# -*- coding: utf-8 -*-
"""PROD-01: field commissioning endpoints must persist operational records."""

from inspect import signature
from types import SimpleNamespace

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.endpoints import field_commissioning


def _ensure_field_tables(db: Session) -> None:
    """Create the legacy field tables used by the production SQLite DB."""
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS field_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_no TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                project_name TEXT NOT NULL,
                address TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                assigned_to TEXT,
                scheduled_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER DEFAULT 0,
                progress_note TEXT,
                completion_signature TEXT,
                completion_time TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS field_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS field_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                photo_url TEXT,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                reported_by TEXT,
                reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolution_note TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.commit()


def _create_field_task(db: Session) -> int:
    _ensure_field_tables(db)
    result = db.execute(
        text(
            """
            INSERT INTO field_tasks (
                task_no,
                customer_name,
                project_name,
                address,
                status,
                progress,
                created_at,
                updated_at
            )
            VALUES (
                'FIELD-PROD01-API',
                '测试客户',
                '现场调试持久化测试',
                '测试现场',
                'pending',
                0,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        )
    )
    db.commit()
    return int(result.lastrowid)


def _call_endpoint(func, task_id: int, payload: dict, db: Session):
    current_user = SimpleNamespace(id=7, username="field_api_test", is_superuser=True)
    kwargs = {
        "task_id": task_id,
        "data": payload,
        "current_user": current_user,
    }
    if "db" in signature(func).parameters:
        kwargs["db"] = db
    return func(**kwargs)


def test_field_task_actions_persist_to_db(db_session: Session):
    task_id = _create_field_task(db_session)

    before_checkins = db_session.execute(text("SELECT count(*) FROM field_checkins")).scalar_one()
    _call_endpoint(
        field_commissioning.checkin_field_task,
        task_id,
        {"latitude": 31.23, "longitude": 121.47},
        db_session,
    )
    after_checkins = db_session.execute(text("SELECT count(*) FROM field_checkins")).scalar_one()
    assert after_checkins == before_checkins + 1

    _call_endpoint(
        field_commissioning.update_field_task_progress,
        task_id,
        {"progress": 55, "note": "设备上电调试完成"},
        db_session,
    )
    task = db_session.execute(
        text("SELECT status, progress, progress_note FROM field_tasks WHERE id=:id"),
        {"id": task_id},
    ).mappings().one()
    assert task["status"] == "in_progress"
    assert task["progress"] == 55
    assert task["progress_note"] == "设备上电调试完成"

    before_issues = db_session.execute(text("SELECT count(*) FROM field_issues")).scalar_one()
    _call_endpoint(
        field_commissioning.report_field_task_issue,
        task_id,
        {"description": "视觉定位偶发偏移", "severity": "high", "photo_url": "site://p1"},
        db_session,
    )
    after_issues = db_session.execute(text("SELECT count(*) FROM field_issues")).scalar_one()
    assert after_issues == before_issues + 1

    _call_endpoint(
        field_commissioning.complete_field_task,
        task_id,
        {"signature": "客户代表签收", "note": "SAT 调试通过"},
        db_session,
    )
    completed = db_session.execute(
        text(
            """
            SELECT status, progress, completion_signature, completion_time, progress_note
            FROM field_tasks
            WHERE id=:id
            """
        ),
        {"id": task_id},
    ).mappings().one()
    assert completed["status"] == "completed"
    assert completed["progress"] == 100
    assert completed["completion_signature"] == "客户代表签收"
    assert completed["completion_time"] is not None
    assert completed["progress_note"] == "SAT 调试通过"
