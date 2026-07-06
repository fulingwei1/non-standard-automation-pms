# -*- coding: utf-8 -*-
"""HR-14: monthly performance workflow must write the canonical result table."""

from datetime import date
from decimal import Decimal
import uuid


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def test_completed_monthly_evaluations_upsert_performance_result(db_session):
    from app.models.performance import (
        EvaluationWeightConfig,
        MonthlyWorkSummary,
        PerformanceEvaluationRecord,
        PerformancePeriod,
        PerformanceResult,
    )
    from app.models.user import User
    from app.schemas.performance import PerformanceEvaluationRecordCreate
    from app.services.manager_performance.manager_performance_service import (
        ManagerPerformanceService,
    )

    employee = User(
        username=_code("hr14-employee").lower(),
        password_hash="not-used",
        real_name="HR14被评员工",
        department_id=14,
        department="HR14绩效部",
        is_active=True,
    )
    dept_manager = User(
        username=_code("hr14-dept").lower(),
        password_hash="not-used",
        real_name="HR14部门经理",
        is_active=True,
    )
    project_manager = User(
        username=_code("hr14-pm").lower(),
        password_hash="not-used",
        real_name="HR14项目经理",
        is_active=True,
    )
    db_session.add_all([employee, dept_manager, project_manager])
    db_session.flush()

    summary = MonthlyWorkSummary(
        employee_id=employee.id,
        period="2026-07",
        work_content="本月完成自动化测试平台关键模块。",
        self_evaluation="整体按计划推进，项目协同正常。",
        status="EVALUATING",
    )
    db_session.add(summary)
    db_session.flush()

    db_session.add(
        EvaluationWeightConfig(
            dept_manager_weight=60,
            project_manager_weight=40,
            effective_date=date(2026, 1, 1),
            operator_id=dept_manager.id,
            reason="HR14测试权重",
        )
    )
    db_session.add_all(
        [
            PerformanceEvaluationRecord(
                summary_id=summary.id,
                evaluator_id=dept_manager.id,
                evaluator_type="DEPT_MANAGER",
                score=90,
                comment="部门评价：能力稳定，交付质量好。",
                status="COMPLETED",
            ),
            PerformanceEvaluationRecord(
                summary_id=summary.id,
                evaluator_id=project_manager.id,
                evaluator_type="PROJECT_MANAGER",
                project_id=None,
                project_weight=100,
                score=0,
                comment="",
                status="PENDING",
            ),
        ]
    )
    db_session.commit()

    result = ManagerPerformanceService(db_session).submit_evaluation(
        current_user=project_manager,
        task_id=summary.id,
        evaluation_in=PerformanceEvaluationRecordCreate(
            score=80,
            comment="项目评价：任务完成及时，仍需增强跨项目复盘。",
            project_weight=100,
        ),
    )

    db_session.refresh(summary)
    period = db_session.query(PerformancePeriod).filter_by(period_code="MONTHLY-2026-07").one()
    canonical_result = (
        db_session.query(PerformanceResult)
        .filter(
            PerformanceResult.period_id == period.id,
            PerformanceResult.user_id == employee.id,
        )
        .one()
    )

    assert result.status == "COMPLETED"
    assert summary.status == "COMPLETED"
    assert period.period_name == "2026-07 月度绩效"
    assert period.period_type == "MONTHLY"
    assert period.status == "FINALIZED"
    assert canonical_result.total_score == Decimal("86.00")
    assert canonical_result.level == "B+"
    assert canonical_result.user_name == "HR14被评员工"
    assert canonical_result.department_id == 14
    assert canonical_result.department_name == "HR14绩效部"
    assert canonical_result.status == "CALCULATED"
    assert canonical_result.indicator_scores == {
        "monthly_final_score": 86.0,
        "dept_score": 90.0,
        "project_score": 80.0,
        "dept_weight": 60,
        "project_weight": 40,
    }

