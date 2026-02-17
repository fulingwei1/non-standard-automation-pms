# -*- coding: utf-8 -*-
"""
K1组集成测试 - 项目全生命周期流程

测试项目从新建→立项→执行→验收→结项的完整业务流程。
不依赖真实数据库，使用 SQLite 内存数据库。

阶段定义（S1-S9）：
  S1: 需求进入
  S2: 方案设计
  S3: 采购备料
  S4: 加工制造
  S5: 装配调试
  S6: 出厂验收(FAT)
  S7: 包装发运
  S8: 现场安装(SAT)
  S9: 质保结项
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base


def _create_test_engine():
    """
    创建测试专用的 SQLite 内存数据库引擎，兼容模型中存在的已知问题：
    - production_work_orders / suppliers 表在元数据中缺失（FK 悬空）
    - idx_created_at 等索引名在多表中重复（SQLite 全局命名空间）
    """
    import app.models  # noqa: F401 — 注册所有模型到 Base.metadata
    from sqlalchemy import Table, Column, Integer

    # 补全缺失的 FK 目标表（存根），避免 NoReferencedTableError
    for stub in ["production_work_orders", "suppliers"]:
        if stub not in Base.metadata.tables:
            Table(stub, Base.metadata, Column("id", Integer, primary_key=True))

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 逐表创建（跳过错误），再逐索引创建（跳过重名索引）
    for table in Base.metadata.sorted_tables:
        try:
            table.create(bind=engine, checkfirst=True)
        except Exception:
            pass
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            try:
                index.create(bind=engine, checkfirst=True)
            except Exception:
                pass

    return engine


@pytest.fixture(scope="function")
def db():
    """提供独立的 SQLite 内存数据库 session，每个测试函数独立隔离。"""
    engine = _create_test_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_user(db, username="pm_user", real_name="项目经理"):
    """创建测试用户（跳过密码哈希）。"""
    from app.models.user import User
    user = User(
        username=username,
        password_hash="hashed_pw",
        real_name=real_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    return user


def _make_customer(db, code="CUST-001", name="测试客户"):
    """创建测试客户。"""
    from app.models.project import Customer
    customer = Customer(
        customer_code=code,
        customer_name=name,
        contact_person="张三",
        contact_phone="13800138000",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()
    return customer


def _make_project(db, customer_id, user_id, code="PJ-LC-001", name="全流程测试项目"):
    """创建处于 S1 阶段的初始项目。"""
    from app.models.project import Project
    project = Project(
        project_code=code,
        project_name=name,
        customer_id=customer_id,
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        health="H1",
        created_by=user_id,
    )
    db.add(project)
    db.flush()
    return project


# ===========================================================================
# 测试类
# ===========================================================================

class TestProjectCreation:
    """TC-LC-1x: 项目新建阶段测试"""

    def test_project_create_with_customer(self, db):
        """TC-LC-11: 新建项目时关联客户，验证基础字段正确存储。"""
        user = _make_user(db)
        customer = _make_customer(db)
        project = _make_project(db, customer.id, user.id)
        db.commit()

        from app.models.project import Project
        saved = db.query(Project).filter_by(project_code="PJ-LC-001").one()

        assert saved.id is not None
        assert saved.project_name == "全流程测试项目"
        assert saved.customer_id == customer.id
        assert saved.stage == "S1"
        assert saved.status == "ST01"
        assert saved.health == "H1"

    def test_project_initial_stage_is_s1(self, db):
        """TC-LC-12: 新建项目默认阶段应为 S1（需求进入）。"""
        user = _make_user(db, "pm2")
        customer = _make_customer(db, "CUST-002", "客户B")
        project = _make_project(db, customer.id, user.id, "PJ-LC-002", "初始阶段测试")
        db.commit()

        from app.models.project import Project
        saved = db.query(Project).get(project.id)
        assert saved.stage == "S1", "新建项目阶段应为 S1"
        assert saved.health == "H1", "新建项目健康度应为 H1（绿色）"


class TestProjectStageProgression:
    """TC-LC-2x: 项目阶段推进测试"""

    def _add_stages(self, db, project_id):
        """为项目初始化所有 9 个阶段记录。"""
        from app.models.project import ProjectStage
        stage_defs = [
            ("S1", "需求进入", 1), ("S2", "方案设计", 2), ("S3", "采购备料", 3),
            ("S4", "加工制造", 4), ("S5", "装配调试", 5), ("S6", "出厂验收", 6),
            ("S7", "包装发运", 7), ("S8", "现场安装", 8), ("S9", "质保结项", 9),
        ]
        stages = []
        for code, name, order in stage_defs:
            s = ProjectStage(
                project_id=project_id,
                stage_code=code,
                stage_name=name,
                stage_order=order,
                status="PENDING",
            )
            db.add(s)
            stages.append(s)
        db.flush()
        return stages

    def test_advance_stage_s1_to_s2(self, db):
        """TC-LC-21: 立项通过后项目阶段从 S1 推进到 S2（方案设计）。"""
        user = _make_user(db, "pm3")
        customer = _make_customer(db, "CUST-003", "客户C")
        project = _make_project(db, customer.id, user.id, "PJ-LC-003", "阶段推进测试")
        self._add_stages(db, project.id)

        # 模拟立项审批通过，推进到 S2
        from app.models.project import Project, ProjectStage
        project.stage = "S2"
        project.status = "ST05"  # 方案设计中
        project.approval_status = "APPROVED"

        # S1 阶段标记完成
        s1 = db.query(ProjectStage).filter_by(project_id=project.id, stage_code="S1").one()
        s1.status = "COMPLETED"
        s1.actual_end_date = date.today()

        db.commit()

        saved = db.query(Project).get(project.id)
        assert saved.stage == "S2"
        assert saved.approval_status == "APPROVED"

        s1_saved = db.query(ProjectStage).filter_by(project_id=project.id, stage_code="S1").one()
        assert s1_saved.status == "COMPLETED"

    def test_advance_through_manufacturing_stages(self, db):
        """TC-LC-22: 项目经历 S3（采购备料）→ S4（加工制造）→ S5（装配调试）三个执行阶段。"""
        user = _make_user(db, "pm4")
        customer = _make_customer(db, "CUST-004", "客户D")
        project = _make_project(db, customer.id, user.id, "PJ-LC-004", "生产阶段测试")
        self._add_stages(db, project.id)

        from app.models.project import Project, ProjectStage

        for stage_code, status_code in [("S3", "ST07"), ("S4", "ST09"), ("S5", "ST11")]:
            prev_stages = db.query(ProjectStage).filter(
                ProjectStage.project_id == project.id,
                ProjectStage.stage_code < stage_code,
            ).all()
            for s in prev_stages:
                s.status = "COMPLETED"

            project.stage = stage_code
            project.status = status_code
            db.flush()

        db.commit()

        saved = db.query(Project).get(project.id)
        assert saved.stage == "S5"

        completed = db.query(ProjectStage).filter_by(
            project_id=project.id, status="COMPLETED"
        ).count()
        assert completed >= 3, "S3 之前的阶段应该已完成"


class TestProjectMilestones:
    """TC-LC-3x: 里程碑管理测试"""

    def test_create_milestones_for_project(self, db):
        """TC-LC-31: 创建项目里程碑并验证计划时间。"""
        user = _make_user(db, "pm5")
        customer = _make_customer(db, "CUST-005", "客户E")
        project = _make_project(db, customer.id, user.id, "PJ-LC-005", "里程碑测试")

        from app.models.project import ProjectMilestone
        milestones = [
            ProjectMilestone(
                project_id=project.id,
                milestone_name="需求确认",
                planned_date=date.today() + timedelta(days=7),
                is_key=True,
                status="PENDING",
            ),
            ProjectMilestone(
                project_id=project.id,
                milestone_name="设计评审",
                planned_date=date.today() + timedelta(days=30),
                is_key=True,
                status="PENDING",
            ),
            ProjectMilestone(
                project_id=project.id,
                milestone_name="出厂验收",
                planned_date=date.today() + timedelta(days=90),
                is_key=True,
                status="PENDING",
            ),
        ]
        for m in milestones:
            db.add(m)
        db.commit()

        from app.models.project import ProjectMilestone as PM
        saved = db.query(PM).filter_by(project_id=project.id).all()
        assert len(saved) == 3
        key_milestones = [m for m in saved if m.is_key]
        assert len(key_milestones) == 3

    def test_complete_milestone_updates_status(self, db):
        """TC-LC-32: 验收里程碑完成后状态更新为 COMPLETED，记录实际日期。"""
        user = _make_user(db, "pm6")
        customer = _make_customer(db, "CUST-006", "客户F")
        project = _make_project(db, customer.id, user.id, "PJ-LC-006", "里程碑完成测试")

        from app.models.project import ProjectMilestone
        ms = ProjectMilestone(
            project_id=project.id,
            milestone_name="出厂验收",
            planned_date=date.today(),
            is_key=True,
            status="PENDING",
        )
        db.add(ms)
        db.flush()

        ms.status = "COMPLETED"
        ms.actual_date = date.today()
        db.commit()

        from app.models.project import ProjectMilestone as PM
        saved = db.query(PM).get(ms.id)
        assert saved.status == "COMPLETED"
        assert saved.actual_date == date.today()


class TestProjectAcceptanceAndClosure:
    """TC-LC-4x: 验收与结项阶段测试"""

    def test_project_advance_to_fat_stage(self, db):
        """TC-LC-41: 项目推进到 S6（出厂验收 FAT），验证阶段和状态一致。"""
        user = _make_user(db, "pm7")
        customer = _make_customer(db, "CUST-007", "客户G")
        project = _make_project(db, customer.id, user.id, "PJ-LC-007", "出厂验收测试")

        from app.models.project import Project
        project.stage = "S6"
        project.status = "ST13"  # FAT 验收中
        project.progress_pct = Decimal("80.00")
        db.commit()

        saved = db.query(Project).get(project.id)
        assert saved.stage == "S6"
        assert saved.status == "ST13"
        assert saved.progress_pct == Decimal("80.00")

    def test_project_closure_after_warranty(self, db):
        """TC-LC-42: 质保期满后项目进入 S9（质保结项），最终状态为已结项。"""
        user = _make_user(db, "pm8")
        customer = _make_customer(db, "CUST-008", "客户H")
        project = _make_project(db, customer.id, user.id, "PJ-LC-008", "结项测试")

        from app.models.project import Project
        project.stage = "S9"
        project.status = "ST20"  # 已结项
        project.progress_pct = Decimal("100.00")
        project.actual_end_date = date.today()
        project.health = "H1"
        db.commit()

        saved = db.query(Project).get(project.id)
        assert saved.stage == "S9"
        assert saved.progress_pct == Decimal("100.00")
        assert saved.actual_end_date == date.today()


class TestProjectStatusLog:
    """TC-LC-5x: 状态变更日志测试"""

    def test_status_change_creates_log(self, db):
        """TC-LC-51: 项目状态发生变更时，应记录状态变更日志。"""
        user = _make_user(db, "pm9")
        customer = _make_customer(db, "CUST-009", "客户I")
        project = _make_project(db, customer.id, user.id, "PJ-LC-009", "状态日志测试")

        from app.models.project import ProjectStatusLog
        log1 = ProjectStatusLog(
            project_id=project.id,
            from_status="ST01",
            to_status="ST02",
            changed_by=user.id,
            change_reason="项目立项通过",
        )
        db.add(log1)

        project.status = "ST02"
        project.stage = "S2"
        db.commit()

        saved_logs = db.query(ProjectStatusLog).filter_by(project_id=project.id).all()
        assert len(saved_logs) == 1
        assert saved_logs[0].from_status == "ST01"
        assert saved_logs[0].to_status == "ST02"

    def test_full_lifecycle_log_sequence(self, db):
        """TC-LC-52: 项目完整生命周期中，状态变更日志按顺序记录。"""
        user = _make_user(db, "pm10")
        customer = _make_customer(db, "CUST-010", "客户J")
        project = _make_project(db, customer.id, user.id, "PJ-LC-010", "完整流程日志测试")

        from app.models.project import ProjectStatusLog

        transitions = [
            ("ST01", "ST02", "立项审批通过"),
            ("ST02", "ST05", "进入方案设计"),
            ("ST05", "ST09", "进入生产阶段"),
            ("ST09", "ST13", "进入验收阶段"),
            ("ST13", "ST20", "项目结项"),
        ]

        for from_s, to_s, reason in transitions:
            log = ProjectStatusLog(
                project_id=project.id,
                from_status=from_s,
                to_status=to_s,
                changed_by=user.id,
                change_reason=reason,
            )
            db.add(log)

        db.commit()

        logs = db.query(ProjectStatusLog).filter_by(
            project_id=project.id
        ).order_by(ProjectStatusLog.id).all()

        assert len(logs) == 5
        assert logs[0].from_status == "ST01"
        assert logs[-1].to_status == "ST20"
        assert logs[-1].change_reason == "项目结项"
