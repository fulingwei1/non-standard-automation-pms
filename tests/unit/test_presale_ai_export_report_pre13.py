# -*- coding: utf-8 -*-
"""PRE-13: AI usage report export must generate a real downloadable file."""

import asyncio
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from app.api.v1 import presale_ai_integration as integration_api
from app.models.presale_ai import AIFunctionEnum, PresaleAIUsageStats
from app.models.user import User
from app.schemas.presale_ai import ExportReportRequest


def _seed_user(db_session) -> User:
    user = User(
        username="pre13_export_user",
        password_hash="test",
        real_name="PRE13测试用户",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _request():
    return SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={"user-agent": "pytest"},
    )


def test_export_report_generates_real_file_and_download_response(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(integration_api.settings, "UPLOAD_DIR", str(tmp_path))
    user = _seed_user(db_session)
    db_session.add(
        PresaleAIUsageStats(
            user_id=user.id,
            ai_function=AIFunctionEnum.REQUIREMENT,
            usage_count=3,
            success_count=2,
            avg_response_time=1200,
            date=date(2026, 7, 4),
        )
    )
    db_session.commit()

    response = asyncio.run(
        integration_api.export_report(
            export_request=ExportReportRequest(
                start_date=date(2026, 7, 1),
                end_date=date(2026, 7, 4),
                format="csv",
            ),
            request=_request(),
            db=db_session,
            current_user=user,
        )
    )

    assert response.file_size > 0
    assert response.file_name.endswith(".csv")
    assert response.file_url == f"/api/v1/presale/ai/downloads/{response.file_name}"
    report_path = tmp_path / "presale_ai_reports" / response.file_name
    assert report_path.exists()
    assert report_path.stat().st_size == response.file_size
    assert "requirement" in report_path.read_text(encoding="utf-8-sig")

    download = asyncio.run(
        integration_api.download_exported_report(
            file_name=response.file_name,
            current_user=user,
        )
    )
    assert Path(download.path) == report_path
