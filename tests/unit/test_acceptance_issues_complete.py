# -*- coding: utf-8 -*-
"""
验收问题管理单元测试

覆盖 app/api/v1/endpoints/acceptance/issues.py 的关键端点
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.factories import (
    AcceptanceIssueFactory,
    AcceptanceOrderFactory,
    UserFactory,
)
from app.models.enums import IssueStatusEnum


class TestReadAcceptanceIssue:
    """读取验收问题测试"""

    def test_read_issue_success(self, db_session: Session, test_acceptance_order):
        """成功读取验收问题"""
        issue = AcceptanceIssueFactory.create(
            order=test_acceptance_order,
            title="测试问题",
            severity="HIGH",
            status="OPEN",
        )
        db_session.commit()

        from app.api.v1.endpoints.acceptance import issues

        response = issues.read_acceptance_issue(issue.id, db_session)
        assert response.id == issue.id
        assert response.title == "测试问题"

    def test_read_issue_not_found(self, db_session: Session):
        """问题不存在时应抛出 404 错误"""
        with pytest.raises(HTTPException) as exc_info:
            from app.api.v1.endpoints.acceptance import issues

            issues.read_acceptance_issue(99999, db_session)
        assert exc_info.value.status_code == 404


class TestReadAcceptanceIssues:
    """读取验收问题列表测试"""

    def test_read_issues_by_order(self, db_session: Session, test_acceptance_order):
        """按验收单号读取问题列表"""
        AcceptanceIssueFactory.create(
            order=test_acceptance_order,
            title="问题1",
            status="OPEN",
        )
        AcceptanceIssueFactory.create(
            order=test_acceptance_order,
            title="问题2",
            status="RESOLVED",
        )
        db_session.commit()

        from app.api.v1.endpoints.acceptance import issues

        response = issues.read_acceptance_issues(
            order_id=test_acceptance_order.id, db_session=db_session, skip=0, limit=10
        )
        assert len(response.items) == 2

    def test_read_issues_with_filter_by_status(
        self, db_session: Session, test_acceptance_order
    ):
        """按状态过滤问题列表"""
        AcceptanceIssueFactory.create(order=test_acceptance_order, status="OPEN")
        AcceptanceIssueFactory.create(order=test_acceptance_order, status="RESOLVED")
        db_session.commit()

        from app.api.v1.endpoints.acceptance import issues

        response = issues.read_acceptance_issues(
            order_id=test_acceptance_order.id,
            status="OPEN",
            db_session=db_session,
            skip=0,
            limit=10,
        )
        assert len(response.items) == 1
        assert response.items[0].status == "OPEN"


class TestCreateAcceptanceIssue:
    """创建验收问题测试"""

    def test_create_issue_success(
        self, db_session: Session, test_acceptance_order, test_user
    ):
        """成功创建验收问题"""
        from app.api.v1.endpoints.acceptance import issues
        from app.schemas.acceptance import IssueCreateRequest

        issue_data = IssueCreateRequest(
            title="测试问题",
            description="问题描述",
            severity="HIGH",
            is_blocking=False,
        )

        response = issues.create_acceptance_issue(
            order_id=test_acceptance_order.id,
            issue_data=issue_data,
            current_user=test_user,
            db_session=db_session,
        )
        assert response.title == "测试问题"
        assert response.severity == "HIGH"
        assert response.created_by_id == test_user.id

    def test_create_blocking_issue(
        self, db_session: Session, test_acceptance_order, test_user
    ):
        """成功创建阻塞问题"""
        from app.api.v1.endpoints.acceptance import issues
        from app.schemas.acceptance import IssueCreateRequest

        issue_data = IssueCreateRequest(
            title="阻塞问题",
            description="阻塞问题描述",
            severity="CRITICAL",
            is_blocking=True,
        )

        response = issues.create_acceptance_issue(
            order_id=test_acceptance_order.id,
            issue_data=issue_data,
            current_user=test_user,
            db_session=db_session,
        )
        assert response.is_blocking == True
        assert response.severity == "CRITICAL"


class TestUpdateAcceptanceIssue:
    """更新验收问题测试"""

    def test_update_issue_success(
        self, db_session: Session, test_acceptance_issue, test_user
    ):
        """成功更新验收问题"""
        from app.api.v1.endpoints.acceptance import issues
        from app.schemas.acceptance import IssueUpdateRequest

        update_data = IssueUpdateRequest(
            title="更新后的问题", description="更新后的描述", status="PROCESSING"
        )

        response = issues.update_acceptance_issue(
            issue_id=test_acceptance_issue.id,
            issue_data=update_data,
            current_user=test_user,
            db_session=db_session,
        )
        assert response.title == "更新后的问题"
        assert response.status == "PROCESSING"

    def test_update_nonexistent_issue(self, db_session: Session, test_user):
        """更新不存在的问题应抛出 404 错误"""
        from app.api.v1.endpoints.acceptance import issues
        from app.schemas.acceptance import IssueUpdateRequest

        update_data = IssueUpdateRequest(title="更新")

        with pytest.raises(HTTPException) as exc_info:
            issues.update_acceptance_issue(99999, update_data, test_user, db_session)
        assert exc_info.value.status_code == 404


class TestCloseAcceptanceIssue:
    """关闭验收问题测试"""

    def test_close_issue_success(
        self, db_session: Session, test_acceptance_issue, test_user
    ):
        """成功关闭验收问题"""
        from app.api.v1.endpoints.acceptance import issues

        response = issues.close_acceptance_issue(
            issue_id=test_acceptance_issue.id,
            current_user=test_user,
            db_session=db_session,
        )
        assert response.status == IssueStatusEnum.CLOSED.value


class TestAssignAcceptanceIssue:
    """指派验收问题测试"""

    def test_assign_issue_success(
        self, db_session: Session, test_acceptance_issue, test_user
    ):
        """成功指派验收问题"""
        from app.api.v1.endpoints.acceptance import issues

        assignee = UserFactory.create(real_name="指派人")
        db_session.commit()

        response = issues.assign_acceptance_issue(
            issue_id=test_acceptance_issue.id,
            assignee_id=assignee.id,
            current_user=test_user,
            db_session=db_session,
        )
        assert response.assigned_to_id == assignee.id


class TestResolveAcceptanceIssue:
    """解决验收问题测试"""

    def test_resolve_issue_success(
        self, db_session: Session, test_acceptance_issue, test_user
    ):
        """成功解决验收问题"""
        from app.api.v1.endpoints.acceptance import issues

        response = issues.resolve_acceptance_issue(
            issue_id=test_acceptance_issue.id,
            resolution="已解决",
            current_user=test_user,
            db_session=db_session,
        )
        assert response.status == IssueStatusEnum.RESOLVED.value
        assert response.resolution == "已解决"


class TestVerifyAcceptanceIssue:
    """验证验收问题测试"""

    def test_verify_issue_success(
        self, db_session: Session, test_acceptance_issue, test_user
    ):
        """成功验证验收问题"""
        from app.api.v1.endpoints.acceptance import issues

        test_acceptance_issue.status = IssueStatusEnum.RESOLVED.value
        db_session.commit()

        response = issues.verify_acceptance_issue(
            issue_id=test_acceptance_issue.id,
            verified_result="VERIFIED",
            current_user=test_user,
            db_session=db_session,
        )
        assert response.verified_result == "VERIFIED"


class TestDeferAcceptanceIssue:
    """延期验收问题测试"""

    def test_defer_issue_success(
        self, db_session: Session, test_acceptance_issue, test_user
    ):
        """成功延期验收问题"""
        from app.api.v1.endpoints.acceptance import issues

        response = issues.defer_acceptance_issue(
            issue_id=test_acceptance_issue.id,
            reason="需要更多信息",
            current_user=test_user,
            db_session=db_session,
        )
        assert response.status == IssueStatusEnum.DEFERRED.value


class TestIssueFollowUps:
    """问题跟进记录测试"""

    def test_add_follow_up_success(
        self, db_session: Session, test_acceptance_issue, test_user
    ):
        """成功添加问题跟进记录"""
        from app.api.v1.endpoints.acceptance import issues

        response = issues.add_issue_follow_up(
            issue_id=test_acceptance_issue.id,
            content="跟进记录内容",
            current_user=test_user,
            db_session=db_session,
        )
        assert response.content == "跟进记录内容"

    def test_read_follow_ups_success(self, db_session: Session, test_acceptance_issue):
        """成功读取问题跟进记录"""
        from app.api.v1.endpoints.acceptance import issues

        response = issues.read_issue_follow_ups(
            issue_id=test_acceptance_issue.id, db_session=db_session, skip=0, limit=10
        )
        assert len(response.items) >= 0


# Fixtures
@pytest.fixture
def test_acceptance_order(db_session: Session):
    """创建测试验收单"""
    from app.factories import ProjectFactory, MachineFactory

    project = ProjectFactory.create(project_code="P2025001", stage="S5")
    machine = MachineFactory.create(project=project, machine_code="PN001", stage="S5")
    order = AcceptanceOrderFactory.create(
        project=project,
        machine=machine,
        acceptance_type="FAT",
        order_no="FAT-P2025001-M01-001",
        status="IN_PROGRESS",
    )
    db_session.commit()
    return order


@pytest.fixture
def test_acceptance_issue(db_session: Session, test_acceptance_order, test_user):
    """创建测试问题"""
    issue = AcceptanceIssueFactory.create(
        order=test_acceptance_order,
        title="测试问题",
        description="问题描述",
        severity="HIGH",
        status="OPEN",
        is_blocking=False,
        created_by_id=test_user.id,
    )
    db_session.commit()
    return issue


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = UserFactory.create(username="testuser", real_name="测试用户")
    db_session.commit()
    return user
