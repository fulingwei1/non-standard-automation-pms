# -*- coding: utf-8 -*-
"""技术评审详情页前后端子资源契约测试。"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.issue import Issue
from app.models.project import Customer, Project
from app.models.technical_review import TechnicalReview
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestTechnicalReviewDetailSubresourceContract:
    """验证详情页的参与人、材料、检查项入口能真实落库并回到详情。"""

    def test_review_detail_subresources_can_be_added_and_read_back(
        self, client: TestClient, db_session: Session, admin_token: str
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        prefix = settings.API_V1_PREFIX
        unique = uuid4().hex[:8].upper()

        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        customer = Customer(
            customer_code=f"CUST-TR-{unique}",
            customer_name=f"技术评审客户-{unique}",
            industry="电子制造",
            created_by=admin_user.id,
        )
        db_session.add(customer)
        db_session.flush()

        project = Project(
            project_code=f"PRJTR{unique[:6]}",
            project_name=f"技术评审项目-{unique}",
            customer=customer,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            pm_id=admin_user.id,
            pm_name=admin_user.real_name or admin_user.username,
            created_by=admin_user.id,
        )
        db_session.add(project)
        db_session.flush()

        review = TechnicalReview(
            review_no=f"RV-PDR-{unique}",
            review_type="PDR",
            review_name=f"项目PDR评审-{unique}",
            project_id=project.id,
            project_no=project.project_code,
            status="DRAFT",
            scheduled_date=datetime(2026, 6, 20, 9, 0, 0),
            location="评审室",
            meeting_type="ONSITE",
            host_id=admin_user.id,
            presenter_id=admin_user.id,
            recorder_id=admin_user.id,
            created_by=admin_user.id,
        )
        db_session.add(review)
        db_session.commit()

        participant_response = client.post(
            f"{prefix}/technical-reviews/{review.id}/participants",
            headers=headers,
            json={
                "review_id": review.id,
                "user_id": admin_user.id,
                "role": "expert",
                "is_required": True,
            },
        )
        assert participant_response.status_code == 201, participant_response.text
        assert participant_response.json()["user_id"] == admin_user.id

        material_response = client.post(
            f"{prefix}/technical-reviews/{review.id}/materials",
            headers=headers,
            json={
                "review_id": review.id,
                "material_type": "drawing",
                "material_name": "总装图纸",
                "file_path": f"/reviews/{review.id}/assembly.pdf",
                "file_size": 2048,
                "version": "A1",
                "is_required": True,
            },
        )
        assert material_response.status_code == 201, material_response.text
        assert material_response.json()["material_name"] == "总装图纸"

        issue_response = client.post(
            f"{prefix}/technical-reviews/{review.id}/issues",
            headers=headers,
            json={
                "review_id": review.id,
                "issue_level": "B",
                "category": "设计风险",
                "description": "夹具定位方案需要复核",
                "suggestion": "补充定位销校核",
                "assignee_id": admin_user.id,
                "deadline": "2026-06-25",
            },
        )
        assert issue_response.status_code == 201, issue_response.text
        issue_payload = issue_response.json()
        assert issue_payload["linked_issue_id"] is not None
        linked_project_issue_id = issue_payload["linked_issue_id"]

        issues_list_response = client.get(
            f"{prefix}/technical-reviews/issues",
            headers=headers,
            params={"review_id": review.id},
        )
        assert issues_list_response.status_code == 200, issues_list_response.text
        issues_payload = issues_list_response.json()
        assert issues_payload["total"] == 1
        assert issues_payload["items"][0]["id"] == issue_payload["id"]

        resolve_response = client.put(
            f"{prefix}/technical-reviews/issues/{issue_payload['id']}",
            headers=headers,
            json={
                "status": "RESOLVED",
                "solution": "已补充定位销受力校核和复核记录",
            },
        )
        assert resolve_response.status_code == 200, resolve_response.text

        resolved_workspace_issues_response = client.get(
            f"{prefix}/project-workspace/projects/{project.id}/issues",
            headers=headers,
        )
        assert (
            resolved_workspace_issues_response.status_code == 200
        ), resolved_workspace_issues_response.text
        resolved_workspace_issue = next(
            issue
            for issue in resolved_workspace_issues_response.json()["issues"]
            if issue["id"] == linked_project_issue_id
        )
        assert resolved_workspace_issue["status"] == "RESOLVED"
        assert resolved_workspace_issue["solution"] == "已补充定位销受力校核和复核记录"

        verify_response = client.put(
            f"{prefix}/technical-reviews/issues/{issue_payload['id']}",
            headers=headers,
            json={
                "status": "VERIFIED",
                "verify_result": "PASS",
                "verifier_id": admin_user.id,
            },
        )
        assert verify_response.status_code == 200, verify_response.text

        linked_project_issue = (
            db_session.query(Issue).filter(Issue.id == linked_project_issue_id).one()
        )
        assert linked_project_issue.status == "CLOSED"
        assert linked_project_issue.verified_result == "VERIFIED"
        assert linked_project_issue.verified_by == admin_user.id

        checklist_response = client.post(
            f"{prefix}/technical-reviews/{review.id}/checklist-records",
            headers=headers,
            json={
                "review_id": review.id,
                "checklist_item_id": None,
                "category": "机械设计",
                "check_item": "定位基准是否明确",
                "result": "FAIL",
                "issue_level": "B",
                "issue_desc": "定位销校核缺少计算依据",
                "checker_id": admin_user.id,
                "remark": "评审会上提出",
            },
        )
        assert checklist_response.status_code == 201, checklist_response.text
        checklist_payload = checklist_response.json()
        assert checklist_payload["result"] == "FAIL"
        assert checklist_payload["issue_id"] is not None

        detail_response = client.get(
            f"{prefix}/technical-reviews/{review.id}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        detail = detail_response.json()

        assert [p["user_id"] for p in detail["participants"]] == [admin_user.id]
        assert [m["material_name"] for m in detail["materials"]] == ["总装图纸"]
        assert [c["check_item"] for c in detail["checklist_records"]] == [
            "定位基准是否明确"
        ]
        linked_issue_ids = [issue["linked_issue_id"] for issue in detail["issues"]]
        assert all(linked_issue_ids)

        workspace_issues_response = client.get(
            f"{prefix}/project-workspace/projects/{project.id}/issues",
            headers=headers,
        )
        assert workspace_issues_response.status_code == 200, workspace_issues_response.text
        workspace_issue_titles = {
            issue["title"] for issue in workspace_issues_response.json()["issues"]
        }
        assert "技术评审问题：夹具定位方案需要复核" in workspace_issue_titles
        assert "技术评审问题：定位销校核缺少计算依据" in workspace_issue_titles
