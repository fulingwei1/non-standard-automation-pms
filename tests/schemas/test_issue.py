# -*- coding: utf-8 -*-
"""Tests for app/schemas/issue.py"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.issue import (
    IssueBase,
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueFollowUpBase,
    IssueFollowUpCreate,
    IssueAssignRequest,
    IssueResolveRequest,
    IssueVerifyRequest,
    IssueStatusChangeRequest,
    IssueFilterParams,
    IssueStatistics,
    EngineerIssueStatistics,
    IssueTemplateBase,
    IssueTemplateCreate,
    IssueFromTemplateRequest,
)


class TestIssueBase:
    def test_valid(self):
        i = IssueBase(
            category="DESIGN", issue_type="DEFECT",
            severity="MAJOR", title="设计缺陷",
            description="xxx零件尺寸偏差",
        )
        assert i.priority == "MEDIUM"
        assert i.is_blocking is False
        assert i.attachments == []
        assert i.tags == []

    def test_missing(self):
        with pytest.raises(ValidationError):
            IssueBase()

    def test_long_title(self):
        with pytest.raises(ValidationError):
            IssueBase(
                category="C", issue_type="T", severity="S",
                title="x" * 201, description="d",
            )

    def test_with_responsibility(self):
        i = IssueBase(
            category="C", issue_type="T", severity="S",
            title="T", description="D",
            root_cause="DESIGN_ERROR",
            responsible_engineer_id=1,
            estimated_inventory_loss=Decimal("5000"),
            estimated_extra_hours=Decimal("16"),
        )
        assert i.root_cause == "DESIGN_ERROR"


class TestIssueCreate:
    def test_inherits(self):
        i = IssueCreate(
            category="C", issue_type="T", severity="S",
            title="T", description="D",
        )
        assert i.priority == "MEDIUM"


class TestIssueUpdate:
    def test_all_none(self):
        i = IssueUpdate()
        assert i.title is None

    def test_partial(self):
        i = IssueUpdate(status="RESOLVED", solution="已修复")
        assert i.status == "RESOLVED"


class TestIssueResponse:
    def test_valid(self):
        now = datetime.now()
        i = IssueResponse(
            id=1, issue_no="ISS001",
            category="C", issue_type="T", severity="S",
            title="T", description="D",
            reporter_id=1, report_date=now,
            status="OPEN", created_at=now, updated_at=now,
        )
        assert i.follow_up_count == 0
        assert i.resolved_at is None


class TestIssueFollowUpBase:
    def test_valid(self):
        f = IssueFollowUpBase(follow_up_type="COMMENT", content="已跟进")
        assert f.attachments == []

    def test_missing(self):
        with pytest.raises(ValidationError):
            IssueFollowUpBase()


class TestIssueFollowUpCreate:
    def test_valid(self):
        f = IssueFollowUpCreate(
            follow_up_type="STATUS_CHANGE", content="状态变更",
            issue_id=1, old_status="OPEN", new_status="PROCESSING",
        )
        assert f.issue_id == 1


class TestIssueAssignRequest:
    def test_valid(self):
        r = IssueAssignRequest(assignee_id=1)
        assert r.due_date is None
        assert r.comment is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            IssueAssignRequest()


class TestIssueResolveRequest:
    def test_valid(self):
        r = IssueResolveRequest(solution="修改设计图纸")
        assert r.comment is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            IssueResolveRequest()


class TestIssueVerifyRequest:
    def test_valid(self):
        r = IssueVerifyRequest(verified_result="VERIFIED")
        assert r.comment is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            IssueVerifyRequest()


class TestIssueFilterParams:
    def test_all_none(self):
        f = IssueFilterParams()
        assert f.category is None

    def test_with_filters(self):
        f = IssueFilterParams(
            category="DESIGN", severity="CRITICAL",
            is_blocking=True, keyword="螺丝",
        )
        assert f.is_blocking is True


class TestIssueStatistics:
    def test_defaults(self):
        s = IssueStatistics()
        assert s.total == 0
        assert s.by_severity == {}

    def test_none_to_zero(self):
        s = IssueStatistics(total=None, open=None)
        assert s.total == 0
        assert s.open == 0

    def test_with_data(self):
        s = IssueStatistics(total=100, open=30, resolved=50, closed=20)
        assert s.total == 100


class TestEngineerIssueStatistics:
    def test_valid(self):
        e = EngineerIssueStatistics(engineer_id=1, engineer_name="张三")
        assert e.total_issues == 0
        assert e.total_inventory_loss == Decimal(0)
        assert e.issues == []


class TestIssueTemplateBase:
    def test_valid(self):
        t = IssueTemplateBase(
            template_name="设计问题模板",
            template_code="TPL001",
            category="DESIGN",
            issue_type="DEFECT",
            title_template="[设计]问题标题",
        )
        assert t.default_priority == "MEDIUM"
        assert t.is_active is True
        assert t.default_is_blocking is False

    def test_missing(self):
        with pytest.raises(ValidationError):
            IssueTemplateBase()


class TestIssueFromTemplateRequest:
    def test_all_none(self):
        r = IssueFromTemplateRequest()
        assert r.project_id is None

    def test_with_overrides(self):
        r = IssueFromTemplateRequest(
            project_id=1, severity="CRITICAL", title="自定义标题",
        )
        assert r.severity == "CRITICAL"
