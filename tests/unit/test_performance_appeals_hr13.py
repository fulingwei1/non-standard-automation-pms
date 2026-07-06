# -*- coding: utf-8 -*-
"""HR-13: performance appeals need real write/query/handle endpoints."""

from datetime import date
from decimal import Decimal
import uuid


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_result_with_users(db_session):
    from app.models.performance import PerformancePeriod, PerformanceResult
    from app.models.user import User

    employee = User(
        username=_code("hr13-employee").lower(),
        password_hash="not-used",
        real_name="HR13申诉员工",
        department_id=13,
        department="绩效测试部",
        is_active=True,
    )
    handler = User(
        username=_code("hr13-handler").lower(),
        password_hash="not-used",
        real_name="HR13处理人",
        department_id=1,
        department="人力资源部",
        is_active=True,
        is_superuser=True,
    )
    db_session.add_all([employee, handler])
    db_session.flush()

    period = PerformancePeriod(
        period_code=_code("HR13P"),
        period_name="HR13申诉周期",
        period_type="MONTHLY",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
        status="REVIEW",
        is_active=True,
    )
    db_session.add(period)
    db_session.flush()

    result = PerformanceResult(
        period_id=period.id,
        user_id=employee.id,
        user_name=employee.display_name,
        department_id=employee.department_id,
        department_name=employee.department,
        total_score=Decimal("78.00"),
        level="A",
        dept_rank=3,
        company_rank=9,
        status="CALCULATED",
    )
    db_session.add(result)
    db_session.commit()
    return employee, handler, result


def test_submit_performance_appeal_persists_pending_record_and_marks_result(db_session):
    from app.api.v1.endpoints.performance.appeals import (
        PerformanceAppealCreate,
        submit_performance_appeal,
    )
    from app.models.performance import PerformanceAppeal, PerformanceResult

    employee, _handler, result = _seed_result_with_users(db_session)

    response = submit_performance_appeal(
        payload=PerformanceAppealCreate(
            result_id=result.id,
            appeal_reason="项目延期责任归因已修正，请复核质量扣分。",
            expected_score=Decimal("88.50"),
            supporting_evidence="会议纪要与客户确认邮件已上传。",
            attachments=[{"name": "customer-confirmation.pdf"}],
        ),
        db=db_session,
        current_user=employee,
    )

    appeal = db_session.query(PerformanceAppeal).one()
    refreshed_result = db_session.query(PerformanceResult).filter_by(id=result.id).one()

    assert response.code == 200
    assert response.data["id"] == appeal.id
    assert appeal.result_id == result.id
    assert appeal.appellant_id == employee.id
    assert appeal.appellant_name == "HR13申诉员工"
    assert appeal.status == "PENDING"
    assert appeal.expected_score == Decimal("88.50")
    assert appeal.supporting_evidence == "会议纪要与客户确认邮件已上传。"
    assert appeal.attachments == [{"name": "customer-confirmation.pdf"}]
    assert refreshed_result.status == "APPEALING"


def test_list_performance_appeals_filters_to_current_user_unless_admin(db_session):
    from app.api.v1.endpoints.performance.appeals import (
        PerformanceAppealCreate,
        list_performance_appeals,
        submit_performance_appeal,
    )
    from app.models.user import User

    employee, handler, result = _seed_result_with_users(db_session)
    other_user = User(
        username=_code("hr13-other").lower(),
        password_hash="not-used",
        real_name="HR13其他员工",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    submit_performance_appeal(
        payload=PerformanceAppealCreate(
            result_id=result.id,
            appeal_reason="员工本人提交申诉，等待 HR 复核。",
            expected_score=Decimal("82.00"),
        ),
        db=db_session,
        current_user=employee,
    )

    employee_view = list_performance_appeals(db=db_session, current_user=employee)
    other_view = list_performance_appeals(db=db_session, current_user=other_user)
    admin_view = list_performance_appeals(db=db_session, current_user=handler, result_id=result.id)

    assert employee_view.data["total"] == 1
    assert employee_view.data["items"][0]["result_id"] == result.id
    assert other_view.data["total"] == 0
    assert admin_view.data["total"] == 1


def test_handle_performance_appeal_accepts_adjustment_and_writes_history(db_session):
    from app.api.v1.endpoints.performance.appeals import (
        PerformanceAppealCreate,
        PerformanceAppealHandle,
        handle_performance_appeal,
        submit_performance_appeal,
    )
    from app.models.performance import PerformanceAdjustmentHistory, PerformanceAppeal
    from app.models.performance import PerformanceResult

    employee, handler, result = _seed_result_with_users(db_session)
    created = submit_performance_appeal(
        payload=PerformanceAppealCreate(
            result_id=result.id,
            appeal_reason="售后返工原因已排除本人责任，申请恢复绩效分。",
            expected_score=Decimal("91.25"),
        ),
        db=db_session,
        current_user=employee,
    )

    response = handle_performance_appeal(
        appeal_id=created.data["id"],
        payload=PerformanceAppealHandle(
            status="ACCEPTED",
            handle_result="申诉成立，按复核分数调整。",
            new_score=Decimal("91.25"),
            new_level="S",
        ),
        db=db_session,
        current_user=handler,
    )

    appeal = db_session.query(PerformanceAppeal).one()
    refreshed_result = db_session.query(PerformanceResult).filter_by(id=result.id).one()
    history = db_session.query(PerformanceAdjustmentHistory).one()

    assert response.code == 200
    assert appeal.status == "ACCEPTED"
    assert appeal.handler_id == handler.id
    assert appeal.handler_name == "HR13处理人"
    assert appeal.handle_time is not None
    assert appeal.new_score == Decimal("91.25")
    assert appeal.new_level == "S"
    assert refreshed_result.total_score == Decimal("91.25")
    assert refreshed_result.adjusted_total_score == Decimal("91.25")
    assert refreshed_result.level == "S"
    assert refreshed_result.is_adjusted is True
    assert refreshed_result.status == "APPEAL_ACCEPTED"
    assert history.result_id == result.id
    assert history.original_total_score == Decimal("78.00")
    assert history.adjusted_total_score == Decimal("91.25")
    assert history.adjustment_reason == "绩效申诉处理：申诉成立，按复核分数调整。"
    assert history.adjusted_by == handler.id


def test_performance_appeal_routes_are_registered_under_performance_router():
    from app.api.v1.endpoints.performance import router

    paths = {route.path for route in router.routes}

    assert "/performance/appeals" in paths
    assert "/performance/appeals/{appeal_id}/handle" in paths
