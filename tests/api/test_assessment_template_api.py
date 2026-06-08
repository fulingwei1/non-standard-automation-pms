# -*- coding: utf-8 -*-
"""技术评估模板、风险版本 API 的真实服务闭环测试。"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AssessmentSourceTypeEnum, AssessmentStatusEnum
from app.models.sales import AssessmentItem, TechnicalAssessment
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_assessment_template_item_route_persists_scoring_criteria(
    client: TestClient, db_session: Session, admin_token: str
):
    """模板评估项接口应能把前端评分标准写入 AssessmentItem.scoring_criteria。"""
    if not admin_token:
        pytest.skip("Admin token not available")

    headers = _auth_headers(admin_token)
    prefix = settings.API_V1_PREFIX
    unique = uuid4().hex[:8].upper()

    response = client.post(
        f"{prefix}/sales/assessment-templates",
        json={
            "template_code": f"TPL-{unique}",
            "template_name": f"非标设备评估模板-{unique}",
            "category": "CUSTOM",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    template_id = response.json()["data"]["id"]
    criteria = {
        "levels": [
            {"score": 10, "description": "已有成熟案例"},
            {"score": 5, "description": "需要专项验证"},
        ]
    }

    response = client.post(
        f"{prefix}/sales/assessment-templates/{template_id}/items",
        json={
            "item_code": f"TECH-{unique}",
            "item_name": "关键工艺成熟度",
            "dimension": "TECHNICAL",
            "score_criteria": criteria,
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    item_id = response.json()["data"]["id"]

    db_session.expire_all()
    item = db_session.get(AssessmentItem, item_id)
    assert item is not None
    assert item.scoring_criteria == criteria


def test_assessment_version_routes_create_list_and_compare_snapshots(
    client: TestClient, db_session: Session, admin_token: str
):
    """评估版本接口应使用真实服务创建快照、列表和版本对比。"""
    if not admin_token:
        pytest.skip("Admin token not available")

    headers = _auth_headers(admin_token)
    prefix = settings.API_V1_PREFIX

    admin_user = db_session.query(User).filter(User.username == "admin").first()
    assert admin_user is not None

    assessment = TechnicalAssessment(
        source_type=AssessmentSourceTypeEnum.LEAD.value,
        source_id=10001,
        evaluator_id=admin_user.id,
        status=AssessmentStatusEnum.COMPLETED.value,
        total_score=72,
        dimension_scores='{"technology": 16, "business": 14}',
        decision="有条件立项",
        risks="[]",
        conditions="[]",
    )
    db_session.add(assessment)
    db_session.commit()

    response = client.post(
        f"{prefix}/sales/assessments/{assessment.id}/versions",
        json={"change_summary": "初版技术评估归档"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    first_version_id = response.json()["data"]["id"]
    assert response.json()["data"]["version_no"] == "V1.0"

    assessment.total_score = 88
    assessment.dimension_scores = '{"technology": 19, "business": 18}'
    assessment.decision = "推荐立项"
    db_session.commit()

    response = client.post(
        f"{prefix}/sales/assessments/{assessment.id}/versions",
        json={"change_summary": "客户补齐样品和接口资料"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    second_version_id = response.json()["data"]["id"]
    assert response.json()["data"]["version_no"] == "V1.1"

    response = client.get(
        f"{prefix}/sales/assessments/{assessment.id}/versions",
        headers=headers,
    )

    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["total"] == 2
    assert [item["change_summary"] for item in payload["items"]] == [
        "客户补齐样品和接口资料",
        "初版技术评估归档",
    ]

    response = client.get(
        f"{prefix}/sales/assessments/versions/{second_version_id}/compare",
        params={"compare_to_version_id": first_version_id},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    comparison = response.json()["data"]
    assert comparison["score_change"] == 16
    assert comparison["decision_change"] == {
        "from": "有条件立项",
        "to": "推荐立项",
    }
    assert comparison["dimension_score_changes"]["technology"] == {
        "from": 16,
        "to": 19,
        "change": 3,
    }
