# -*- coding: utf-8 -*-
"""Service record API regression contracts."""

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.service import KnowledgeBase
from app.models.service.enums import KnowledgeBaseStatusEnum


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_service_record_get_update_frontend_contract(
    client: TestClient, admin_token: str
):
    headers = _auth_headers(admin_token)
    payload = {
        "service_type": "ON_SITE",
        "project_id": 1,
        "machine_no": "QA-SERVICE-RECORD",
        "customer_id": 1,
        "location": "QA service location",
        "service_date": date.today().isoformat(),
        "start_time": "09:00",
        "end_time": "10:30",
        "duration_hours": "1.50",
        "service_engineer_id": 1,
        "customer_contact": "QA Contact",
        "customer_phone": "13800000000",
        "service_content": "QA service record contract create",
        "service_result": "Initial result",
        "issues_found": "Initial issue",
        "solution_provided": "Initial solution",
        "customer_satisfaction": 4,
        "customer_feedback": "Initial feedback",
        "customer_signed": False,
        "status": "SCHEDULED",
    }

    created = client.post(
        f"{settings.API_V1_PREFIX}/records",
        json=payload,
        headers=headers,
    )
    assert created.status_code == 201, created.text
    record_id = created.json()["id"]

    fetched = client.get(
        f"{settings.API_V1_PREFIX}/records/{record_id}",
        headers=headers,
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["id"] == record_id

    updated = client.put(
        f"{settings.API_V1_PREFIX}/records/{record_id}",
        json={
            "service_content": "QA service record contract updated",
            "service_result": "Updated result",
            "customer_satisfaction": 5,
            "customer_signed": True,
            "status": "COMPLETED",
        },
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    updated_body = updated.json()
    assert updated_body["id"] == record_id
    assert updated_body["service_content"] == "QA service record contract updated"
    assert updated_body["customer_satisfaction"] == 5
    assert updated_body["customer_signed"] is True
    assert updated_body["status"] == "COMPLETED"


def test_knowledge_delete_removes_uploaded_file(
    client: TestClient,
    admin_token: str,
    db: Session,
    tmp_path,
    monkeypatch,
):
    headers = _auth_headers(admin_token)
    upload_root = tmp_path / "uploads"
    attachment = upload_root / "knowledge_base" / "qa-delete.txt"
    attachment.parent.mkdir(parents=True)
    attachment.write_text("QA knowledge attachment", encoding="utf-8")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_root))

    article = KnowledgeBase(
        article_no=f"KB-QA-{uuid4().hex[:8]}",
        title="QA knowledge delete removes file",
        category="QA",
        content="QA content",
        tags=["qa"],
        is_faq=False,
        is_featured=False,
        status=KnowledgeBaseStatusEnum.PUBLISHED.value,
        author_id=1,
        author_name="admin",
        file_path="knowledge_base/qa-delete.txt",
        file_name="qa-delete.txt",
        file_size=attachment.stat().st_size,
        file_type="text/plain",
        allow_download=True,
        download_count=0,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    response = client.delete(
        f"{settings.API_V1_PREFIX}/knowledge-base/{article.id}",
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert not attachment.exists()
    assert db.query(KnowledgeBase).filter(KnowledgeBase.id == article.id).first() is None
