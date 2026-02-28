import uuid
# -*- coding: utf-8 -*-
"""
K2组集成测试 - 工时录入到报表全流程
流程：工时录入（草稿） → 提交审批 → 审批通过/驳回 → 汇总统计 → 报表生成
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal


# ============================================================
# SQLite 内存数据库 fixture
# ============================================================
@pytest.fixture(scope="module")
def db():
    """为本模块提供独立的 SQLite 内存数据库"""
    import sys
    from unittest.mock import MagicMock
    if "redis" not in sys.modules:
        sys.modules["redis"] = MagicMock()
        sys.modules["redis.exceptions"] = MagicMock()

    import os
    os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
    os.environ.setdefault("REDIS_URL", "")
    os.environ.setdefault("ENABLE_SCHEDULER", "false")

    import app.models  # noqa: F401 - 注册所有 ORM 元数据
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ============================================================
# 基础数据 fixtures
# ============================================================
@pytest.fixture(scope="module")
def ts_engineer(db):
    """创建工程师用户（工时填报人）"""
    from app.models.user import User
    from app.models.organization import Employee
    from app.core.security import get_password_hash

    emp = Employee(
        employee_code=f"EMP-TS-ENG-001-{uuid.uuid4().hex[:8]}",
        name="工程师小王",
        department="工程部",
        role="ENGINEER",
        phone="13800000010",
    )
    db.add(emp)
    db.flush()
    user = User(
        employee_id=emp.id,
        username="ts_engineer_flow",
        password_hash=get_password_hash("test123"),
        real_name="工程师小王",
        department="工程部",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def ts_manager(db):
    """创建项目经理用户（工时审批人）"""
    from app.models.user import User
    from app.models.organization import Employee
    from app.core.security import get_password_hash

    emp = Employee(
        employee_code=f"EMP-TS-PM-001-{uuid.uuid4().hex[:8]}",
        name="项目经理老李",
        department="项目管理部",
        role="PM",
        phone="13800000011",
    )
    db.add(emp)
    db.flush()
    user = User(
        employee_id=emp.id,
        username="ts_manager_flow",
        password_hash=get_password_hash("test123"),
        real_name="项目经理老李",
        department="项目管理部",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def ts_project(db, ts_manager):
    """创建工时关联项目"""
    from app.models.project import Customer, Project

    cust = Customer(
        customer_code=f"CUST-TS-001-{uuid.uuid4().hex[:8]}",
        customer_name="工时测试客户",
        contact_person="张客户",
        contact_phone="13900000010",
        status="ACTIVE",
    )
    db.add(cust)
    db.flush()

    project = Project(
        project_code=f"PJ-TS-001-{uuid.uuid4().hex[:8]}",
        project_name="工时测试项目",
        customer_id=cust.id,
        customer_name=cust.customer_name,
        stage="S2",
        status="ST01",
        health="H1",
        pm_id=ts_manager.id,
        pm_name=ts_manager.real_name,
        created_by=ts_manager.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


# ============================================================
# 测试用例
# ============================================================
class TestTimesheetFlowIntegration:
    """工时录入到报表生成全流程集成测试"""

    # 本周一
    WEEK_START = date.today() - timedelta(days=date.today().weekday())

    # ─── 1. 工时记录创建（草稿状态） ──────────────────────────
    def test_timesheet_entries_created_as_draft(self, db, ts_engineer, ts_project):
        """工程师填报本周工时，初始为草稿状态"""
        from app.models.timesheet import Timesheet

        entries = []
        work_contents = [
            ("机械结构设计", "完成了主体框架设计方案"),
            ("零件采购清单整理", "整理了轴承、导轨等关键部件采购清单"),
            ("装配图纸绘制", "完成了总装图及部分零件图"),
        ]
        for i, (content, result) in enumerate(work_contents):
            ts = Timesheet(
                timesheet_no=f"TS-FLOW-{str(i+1).zfill(3)}",
                user_id=ts_engineer.id,
                user_name=ts_engineer.real_name,
                department_name="工程部",
                project_id=ts_project.id,
                project_code=ts_project.project_code,
                project_name=ts_project.project_name,
                work_date=self.WEEK_START + timedelta(days=i),
                hours=Decimal("8.0"),
                overtime_type="NORMAL",
                work_content=content,
                work_result=result,
                progress_before=i * 10,
                progress_after=(i + 1) * 10,
                status="DRAFT",
                created_by=ts_engineer.id,
            )
            entries.append(ts)

        db.add_all(entries)
        db.commit()

        saved = db.query(Timesheet).filter(
            Timesheet.user_id == ts_engineer.id,
            Timesheet.status == "DRAFT",
        ).all()
        assert len(saved) == 3
        total_hours = sum(float(e.hours) for e in saved)
        assert total_hours == 24.0

    # ─── 2. 创建工时批次并提交 ───────────────────────────────
    def test_timesheet_batch_submitted(self, db, ts_engineer, ts_manager):
        """创建周工时批次并提交审批，状态变为 SUBMITTED"""
        from app.models.timesheet import Timesheet, TimesheetBatch

        entries = db.query(Timesheet).filter(
            Timesheet.user_id == ts_engineer.id,
            Timesheet.status == "DRAFT",
        ).all()
        assert len(entries) == 3

        # 创建周批次
        batch = TimesheetBatch(
            batch_no="BATCH-FLOW-001",
            user_id=ts_engineer.id,
            user_name=ts_engineer.real_name,
            week_start=self.WEEK_START,
            week_end=self.WEEK_START + timedelta(days=6),
            year=self.WEEK_START.year,
            week_number=self.WEEK_START.isocalendar()[1],
            total_hours=Decimal("24.0"),
            normal_hours=Decimal("24.0"),
            overtime_hours=Decimal("0"),
            entries_count=3,
            status="SUBMITTED",
            submit_time=datetime.now(),
            approver_id=ts_manager.id,
            approver_name=ts_manager.real_name,
        )
        db.add(batch)
        db.flush()

        # 同步更新各条工时记录状态
        for entry in entries:
            entry.status = "SUBMITTED"
            entry.submit_time = datetime.now()
            entry.approver_id = ts_manager.id
            entry.approver_name = ts_manager.real_name

        db.commit()
        db.refresh(batch)

        assert batch.id is not None
        assert batch.status == "SUBMITTED"
        assert float(batch.total_hours) == 24.0
        assert batch.entries_count == 3

    # ─── 3. 审批人审批通过 ───────────────────────────────────
    def test_timesheet_batch_approved(self, db, ts_engineer, ts_manager):
        """项目经理审批通过工时批次"""
        from app.models.timesheet import Timesheet, TimesheetBatch, TimesheetApprovalLog

        batch = db.query(TimesheetBatch).filter(
            TimesheetBatch.batch_no == "BATCH-FLOW-001"
        ).first()
        assert batch is not None

        # 审批通过
        batch.status = "APPROVED"
        batch.approve_time = datetime.now()
        batch.approve_comment = "工时填报内容完整，与项目计划吻合，审批通过"
        db.flush()

        # 记录审批日志
        approval_log = TimesheetApprovalLog(
            batch_id=batch.id,
            approver_id=ts_manager.id,
            approver_name=ts_manager.real_name,
            action="APPROVE",
            comment="工时填报内容完整，与项目计划吻合，审批通过",
            approved_at=datetime.now(),
        )
        db.add(approval_log)

        # 更新工时记录状态
        entries = db.query(Timesheet).filter(
            Timesheet.user_id == ts_engineer.id,
            Timesheet.status == "SUBMITTED",
        ).all()
        for entry in entries:
            entry.status = "APPROVED"
            entry.approve_time = datetime.now()
            entry.approve_comment = "已审批通过"

        db.commit()

        db.refresh(batch)
        assert batch.status == "APPROVED"

        logs = db.query(TimesheetApprovalLog).filter(
            TimesheetApprovalLog.batch_id == batch.id
        ).all()
        assert len(logs) == 1
        assert logs[0].action == "APPROVE"

    # ─── 4. 工时驳回再重新提交测试 ──────────────────────────
    def test_timesheet_rejected_and_resubmitted(self, db, ts_engineer, ts_manager,
                                                  ts_project):
        """新增一条工时 → 提交 → 驳回 → 修改 → 重新提交"""
        from app.models.timesheet import Timesheet, TimesheetApprovalLog

        # 新增一条工时
        ts_extra = Timesheet(
            timesheet_no="TS-FLOW-EXTRA",
            user_id=ts_engineer.id,
            user_name=ts_engineer.real_name,
            department_name="工程部",
            project_id=ts_project.id,
            project_code=ts_project.project_code,
            project_name=ts_project.project_name,
            work_date=self.WEEK_START + timedelta(days=4),
            hours=Decimal("4.0"),   # 只写了4小时，描述不清
            overtime_type="NORMAL",
            work_content="会议",    # 内容过于简单
            status="SUBMITTED",
            submit_time=datetime.now(),
            approver_id=ts_manager.id,
            created_by=ts_engineer.id,
        )
        db.add(ts_extra)
        db.flush()

        # 审批驳回
        ts_extra.status = "REJECTED"
        ts_extra.approve_comment = "工作内容描述过于简单，请补充具体工作内容"
        ts_extra.approve_time = datetime.now()
        db.flush()

        reject_log = TimesheetApprovalLog(
            timesheet_id=ts_extra.id,
            approver_id=ts_manager.id,
            approver_name=ts_manager.real_name,
            action="REJECT",
            comment="工作内容描述过于简单，请补充具体工作内容",
            approved_at=datetime.now(),
        )
        db.add(reject_log)
        db.commit()

        # 工程师修改后重新提交
        ts_extra.work_content = "参加项目启动评审会议，讨论了装配工艺方案和关键节点"
        ts_extra.status = "SUBMITTED"
        ts_extra.submit_time = datetime.now()
        db.commit()

        db.refresh(ts_extra)
        assert ts_extra.status == "SUBMITTED"
        assert "装配工艺" in ts_extra.work_content

        logs = db.query(TimesheetApprovalLog).filter(
            TimesheetApprovalLog.timesheet_id == ts_extra.id
        ).all()
        assert any(log.action == "REJECT" for log in logs)

    # ─── 5. 工时汇总统计生成 ─────────────────────────────────
    def test_timesheet_summary_generated(self, db, ts_engineer, ts_project):
        """基于已审批工时，生成月度工时汇总"""
        from app.models.timesheet import Timesheet, TimesheetSummary

        # 统计已审批工时
        approved = db.query(Timesheet).filter(
            Timesheet.user_id == ts_engineer.id,
            Timesheet.status == "APPROVED",
        ).all()
        total = sum(float(e.hours) for e in approved)

        # 生成月度汇总
        today = date.today()
        summary = TimesheetSummary(
            summary_type="USER_MONTH",
            user_id=ts_engineer.id,
            project_id=ts_project.id,
            year=today.year,
            month=today.month,
            total_hours=Decimal(str(total)),
            normal_hours=Decimal(str(total)),
            overtime_hours=Decimal("0"),
            weekend_hours=Decimal("0"),
            holiday_hours=Decimal("0"),
            standard_hours=Decimal("176"),   # 22天 × 8小时
            work_days=22,
            entries_count=len(approved),
            projects_count=1,
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)

        assert summary.id is not None
        assert float(summary.total_hours) == 24.0
        assert summary.summary_type == "USER_MONTH"
        assert summary.entries_count == 3

    # ─── 6. 项目工时汇总统计 ─────────────────────────────────
    def test_project_timesheet_statistics(self, db, ts_engineer, ts_project):
        """统计项目维度的工时分布"""
        from app.models.timesheet import Timesheet

        project_entries = db.query(Timesheet).filter(
            Timesheet.project_id == ts_project.id,
            Timesheet.status == "APPROVED",
        ).all()

        assert len(project_entries) >= 3

        # 按日统计
        daily = {}
        for entry in project_entries:
            key = str(entry.work_date)
            daily[key] = daily.get(key, 0) + float(entry.hours)

        assert len(daily) >= 3            # 至少 3 天有工时
        assert all(h > 0 for h in daily.values())

        # 检查进度更新情况
        with_progress = [e for e in project_entries if e.progress_after is not None]
        assert len(with_progress) > 0

    # ─── 7. 生成工时报表 ─────────────────────────────────────
    def test_timesheet_report_generated(self, db, ts_engineer, ts_manager):
        """基于汇总数据，生成工时分析报表"""
        from app.models.report_center import ReportGeneration

        today = date.today()
        report_data = {
            "period": f"{today.year}-{today.month:02d}",
            "users": [
                {
                    "user_id": ts_engineer.id,
                    "user_name": ts_engineer.real_name,
                    "total_hours": 24.0,
                    "normal_hours": 24.0,
                    "overtime_hours": 0.0,
                    "projects": 1,
                }
            ],
            "total_hours": 24.0,
            "approval_rate": 100.0,
            "avg_daily_hours": 8.0,
        }

        report = ReportGeneration(
            report_type="TIMESHEET",
            report_title=f"{today.year}年{today.month}月工时分析报表",
            period_type="MONTHLY",
            period_start=date(today.year, today.month, 1),
            period_end=today,
            scope_type="DEPARTMENT",
            scope_id=None,
            viewer_role="PM",
            report_data=report_data,
            status="COMPLETED",
            generated_by=ts_manager.id,
            generated_at=datetime.now(),
            export_format="JSON",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        assert report.id is not None
        assert report.status == "COMPLETED"
        assert report.report_type == "TIMESHEET"
        assert report.report_data["total_hours"] == 24.0

    # ─── 8. 全流程闭环验证 ───────────────────────────────────
    def test_full_timesheet_flow_end_to_end(self, db, ts_engineer, ts_manager,
                                              ts_project):
        """验证工时录入→审批→汇总→报表的完整链路数据一致性"""
        from app.models.timesheet import (
            Timesheet, TimesheetBatch, TimesheetSummary, TimesheetApprovalLog
        )
        from app.models.report_center import ReportGeneration

        today = date.today()

        # 各环节记录查询
        entries = db.query(Timesheet).filter(
            Timesheet.user_id == ts_engineer.id,
            Timesheet.status == "APPROVED",
        ).all()

        batch = db.query(TimesheetBatch).filter(
            TimesheetBatch.batch_no == "BATCH-FLOW-001"
        ).first()

        summary = db.query(TimesheetSummary).filter(
            TimesheetSummary.user_id == ts_engineer.id,
            TimesheetSummary.year == today.year,
            TimesheetSummary.month == today.month,
        ).first()

        approval_logs = db.query(TimesheetApprovalLog).filter(
            TimesheetApprovalLog.approver_id == ts_manager.id
        ).all()

        report = db.query(ReportGeneration).filter(
            ReportGeneration.report_type == "TIMESHEET"
        ).first()

        # ── 数据完整性校验 ──
        assert len(entries) == 3, "应有 3 条已审批工时记录"
        assert batch is not None and batch.status == "APPROVED"
        assert summary is not None
        assert report is not None and report.status == "COMPLETED"

        # ── 数值一致性校验 ──
        entries_total = sum(float(e.hours) for e in entries)
        assert float(batch.total_hours) == entries_total, "批次工时与明细合计应一致"
        assert float(summary.total_hours) == entries_total, "汇总工时与明细合计应一致"
        assert report.report_data["total_hours"] == entries_total, "报表工时与汇总应一致"

        # ── 审批链路校验 ──
        assert len(approval_logs) >= 1, "应有审批日志"
        approved_logs = [l for l in approval_logs if l.action == "APPROVE"]
        assert len(approved_logs) >= 1, "应有通过记录"

        # ── 工时关联项目校验 ──
        project_entries = [e for e in entries if e.project_id == ts_project.id]
        assert len(project_entries) == 3, "所有工时应关联到测试项目"
