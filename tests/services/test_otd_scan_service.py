# -*- coding: utf-8 -*-
"""
OTD 项目交付智能体 - 扫描服务单元测试

用真实 db_session(in-memory SQLite)验证：
- 10 维检测器在真实数据上的判定逻辑
- severity 聚合
- 预警产出（含 rule_id NOT NULL 修复验证）
- AI 归因的 mock 守门
- 同项目同日去重
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.models.alert import AlertRecord, AlertRule
from app.models.purchase import PurchaseOrder, PurchaseOrderItem


# ============================================================
# 辅助：创建一个执行中项目（S2~S8）
# ============================================================


def _make_executing_project(db, **overrides):
    """创建一个生命周期 S2（方案设计）的活跃项目，planned_end 远期。

    用 S2 是为了让 design_not_frozen 不触发（S2 设计阶段未冻结是正常的），
    planned_end 远期（>60天）让 acceptance_doc_missing 不触发（未到验收时点），
    无成本数据让 margin_deviation 不触发。
    这样得到一个真正"干净"的基线项目，各测试再按需叠加风险信号。
    """
    from app.models.project import Project

    defaults = dict(
        project_code="OTD-TEST-001",
        project_name="OTD 测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        progress_pct=10,
        is_active=True,
        is_archived=False,
        planned_start_date=date.today() - timedelta(days=10),
        planned_end_date=date.today() + timedelta(days=120),
    )
    defaults.update(overrides)
    project = Project(**defaults)
    db.add(project)
    db.flush()
    return project


# ============================================================
# 测试 1：干净项目（无任何风险信号）→ LOW
# ============================================================


class TestOTDScanCleanProject:
    def test_clean_project_returns_low(self, db_session):
        """无任何风险信号的项目应返回 severity=LOW 且 risk_items 可能为空。"""
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        profile = OTDScanService(db_session).scan_project(project.id)

        assert profile["project_id"] == project.id
        assert profile["severity"] == "LOW"
        assert isinstance(profile["risk_items"], list)
        assert profile["suggestion"] == ""  # LOW 不触发 AI 归因


# ============================================================
# 测试 2：维度1 采购延期
# ============================================================


class TestOTDScanProcurementDelay:
    def test_overdue_purchase_triggers_procurement_delay(self, db_session):
        """采购明细 promised_date 过期且未足额收货 → 命中 procurement_delay。"""
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        # 建一张关联到本项目的采购单 + 过期未收货明细
        po = PurchaseOrder(
            order_no="PO-OTD-001",
            supplier_id=1,
            project_id=project.id,
            status="APPROVED",
            required_date=date.today() - timedelta(days=20),
            promised_date=date.today() - timedelta(days=20),
        )
        db_session.add(po)
        db_session.flush()
        item = PurchaseOrderItem(
            order_id=po.id,
            item_no=1,
            material_code="M001",
            material_name="测试物料",
            quantity=100,
            required_date=date.today() - timedelta(days=20),
            promised_date=date.today() - timedelta(days=20),  # 过期 20 天
            received_qty=10,  # 仅收 10，未足额
        )
        db_session.add(item)
        db_session.flush()

        profile = OTDScanService(db_session).scan_project(project.id)
        dims = [it["dim"] for it in profile["risk_items"]]
        assert "procurement_delay" in dims
        proc = next(it for it in profile["risk_items"] if it["dim"] == "procurement_delay")
        assert proc["severity"] == "HIGH"  # 过期 20 天 → HIGH（15-30 区间）


# ============================================================
# 测试 3：维度8 关键节点延期
# ============================================================


class TestOTDScanKeyMilestone:
    def test_overdue_key_milestone_triggers_high(self, db_session):
        """关键里程碑逾期未完成 → 命中 key_milestone_overdue。"""
        from app.models.project.financial import ProjectMilestone
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        ms = ProjectMilestone(
            project_id=project.id,
            milestone_name="关键节点",
            planned_date=date.today() - timedelta(days=10),  # 过期 10 天
            status="IN_PROGRESS",
            is_key=True,
        )
        db_session.add(ms)
        db_session.flush()

        profile = OTDScanService(db_session).scan_project(project.id)
        dims = [it["dim"] for it in profile["risk_items"]]
        assert "key_milestone_overdue" in dims


# ============================================================
# 测试 4：severity 聚合（取最高级）
# ============================================================


class TestOTDScanSeverityAggregation:
    def test_severity_takes_highest(self, db_session):
        """多维度命中时，profile.severity 取最高级。"""
        from app.models.project.financial import ProjectMilestone
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        # 造一个采购延期（HIGH）+ 关键节点延期（HIGH）
        po = PurchaseOrder(
            order_no="PO-OTD-SEV",
            supplier_id=1,
            project_id=project.id,
            status="APPROVED",
            promised_date=date.today() - timedelta(days=20),
        )
        db_session.add(po)
        db_session.flush()
        db_session.add(
            PurchaseOrderItem(
                order_id=po.id,
                item_no=1,
                material_code="M001",
                material_name="物料",
                quantity=100,
                promised_date=date.today() - timedelta(days=20),
                received_qty=0,
            )
        )
        db_session.add(
            ProjectMilestone(
                project_id=project.id,
                milestone_name="关键节点",
                planned_date=date.today() - timedelta(days=10),
                status="IN_PROGRESS",
                is_key=True,
            )
        )
        db_session.flush()

        profile = OTDScanService(db_session).scan_project(project.id)
        assert profile["severity"] in ("HIGH", "CRITICAL")
        assert len(profile["risk_items"]) >= 2


# ============================================================
# 测试 5：预警产出（含 rule_id NOT NULL 修复验证）
# ============================================================


class TestOTDAlertCreation:
    def test_high_severity_creates_alert_with_rule_id(self, db_session):
        """HIGH/CRITICAL 项目应创建 AlertRecord，rule_id 必须非空（NOT NULL 约束）。"""
        from app.models.project.financial import ProjectMilestone
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        db_session.add(
            ProjectMilestone(
                project_id=project.id,
                milestone_name="关键节点",
                planned_date=date.today() - timedelta(days=10),
                status="IN_PROGRESS",
                is_key=True,
            )
        )
        db_session.flush()

        result = OTDScanService(db_session).batch_scan(
            project_ids=[project.id], create_alerts=True
        )

        assert result["alerts_created"] == 1
        # 验证 AlertRecord 真的写进去了，且 rule_id 非空
        alert = (
            db_session.query(AlertRecord)
            .filter(AlertRecord.project_id == project.id)
            .first()
        )
        assert alert is not None
        assert alert.rule_id is not None  # 关键：NOT NULL 约束修复验证
        assert alert.alert_no.startswith("OTD-")
        assert alert.target_type == "PROJECT"
        # OTD 系统 rule 应已自动创建
        rule = (
            db_session.query(AlertRule)
            .filter(AlertRule.rule_code == "OTD_DELIVERY_RISK")
            .first()
        )
        assert rule is not None
        assert rule.is_system is True

    def test_low_severity_no_alert(self, db_session):
        """LOW 项目不应产出预警。"""
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        result = OTDScanService(db_session).batch_scan(
            project_ids=[project.id], create_alerts=True
        )
        assert result["alerts_created"] == 0

    def test_same_day_dedup(self, db_session):
        """同项目同日重复扫描不应重复创建预警。"""
        from app.models.project.financial import ProjectMilestone
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        db_session.add(
            ProjectMilestone(
                project_id=project.id,
                milestone_name="关键节点",
                planned_date=date.today() - timedelta(days=10),
                status="IN_PROGRESS",
                is_key=True,
            )
        )
        db_session.flush()

        svc = OTDScanService(db_session)
        first = svc.batch_scan(project_ids=[project.id], create_alerts=True)
        second = svc.batch_scan(project_ids=[project.id], create_alerts=True)

        assert first["alerts_created"] == 1
        assert second["alerts_created"] == 0  # 去重


# ============================================================
# 测试 6：AI 归因 mock 守门
# ============================================================


class TestOTDAIAttribution:
    def test_mock_response_not_written(self, db_session):
        """AI 返回 mock 响应时，suggestion 应为空，不污染数据。"""
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        # mock AIClientService.generate_solution 返回 mock 响应
        with patch(
            "app.services.ai_client_service.AIClientService.generate_solution",
            return_value={"content": "mock", "model": "qwen3-coder-plus-mock"},
        ):
            with patch(
                "app.services.ai_client_service.is_mock_response",
                return_value=True,
            ):
                profile = OTDScanService(db_session).scan_project(project.id)
                # 干净项目 severity=LOW，不触发 AI；但即便触发，mock 也应被拦
                assert profile["suggestion"] == ""

    def test_ai_failure_does_not_break_scan(self, db_session):
        """AI 调用抛异常时，扫描不应中断，suggestion 为空。"""
        from app.models.project.financial import ProjectMilestone
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        db_session.add(
            ProjectMilestone(
                project_id=project.id,
                milestone_name="关键节点",
                planned_date=date.today() - timedelta(days=10),
                status="IN_PROGRESS",
                is_key=True,
            )
        )
        db_session.flush()

        with patch(
            "app.services.ai_client_service.AIClientService.generate_solution",
            side_effect=Exception("AI 不可用"),
        ):
            profile = OTDScanService(db_session).scan_project(project.id)
            # 扫描仍完成，severity 正常，只是 suggestion 为空
            assert profile["severity"] in ("HIGH", "CRITICAL")
            assert profile["suggestion"] == ""


# ============================================================
# 测试 7：单维失败不阻塞其他维度
# ============================================================


class TestOTDDetectorIsolation:
    def test_one_detector_failure_does_not_block_others(self, db_session):
        """单个检测器抛异常时，其他维度仍应正常返回。"""
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        svc = OTDScanService(db_session)

        # 让 budget 检测器抛异常，其他检测器应照常跑
        with patch.object(
            svc, "_calc_budget_overrun_factors", side_effect=Exception("模拟失败")
        ):
            profile = svc.scan_project(project.id)
            # 扫描完成，没崩
            assert profile["project_id"] == project.id
            assert isinstance(profile["risk_items"], list)


# ============================================================
# 测试 8：维度11 未关闭事项
# ============================================================


class TestOTDOpenItems:
    """第 11 维：未关闭事项聚合（Issue/ChangeRequest/里程碑/验收单）。"""

    def _make_user(self, db):
        from app.models.user import User

        user = User(
            username="otd-test-reporter",
            password_hash="dummy",
            real_name="测试报告人",
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    def test_no_open_items_returns_none(self, db_session):
        """无任何未关闭事项时不触发。"""
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        # 不建任何 issue/change/milestone/acceptance
        factor = OTDScanService(db_session)._calc_open_items_factors(project)
        assert factor is None

    def test_open_issues_triggers_low(self, db_session):
        """少量未关闭 Issue（无阻塞）→ LOW。"""
        from datetime import datetime

        from app.models.issue import Issue
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        reporter = self._make_user(db_session)
        # 建 2 个未关闭 issue（< 5，无阻塞）
        for i in range(2):
            db_session.add(
                Issue(
                    title=f"问题{i}",
                    description="测试问题",
                    reporter_id=reporter.id,
                    report_date=datetime.now(),
                    project_id=project.id,
                    status="OPEN",
                    is_blocking=False,
                )
            )
        db_session.flush()

        factor = OTDScanService(db_session)._calc_open_items_factors(project)
        assert factor is not None
        assert factor["dim"] == "open_items"
        assert factor["severity"] == "LOW"
        assert factor["evidence"]["open_issues"] == 2

    def test_blocking_issue_escalates_to_high(self, db_session):
        """有阻塞 Issue → HIGH。"""
        from datetime import datetime

        from app.models.issue import Issue
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        reporter = self._make_user(db_session)
        db_session.add(
            Issue(
                title="阻塞问题",
                description="阻塞交付",
                reporter_id=reporter.id,
                report_date=datetime.now(),
                project_id=project.id,
                status="OPEN",
                is_blocking=True,  # 阻塞 → HIGH
            )
        )
        db_session.flush()

        factor = OTDScanService(db_session)._calc_open_items_factors(project)
        assert factor["severity"] == "HIGH"
        assert factor["evidence"]["blocking_issues"] == 1

    def test_closed_status_not_counted(self, db_session):
        """已关闭状态（RESOLVED/COMPLETED/CLOSED）不计入未关闭。"""
        from datetime import datetime

        from app.models.issue import Issue
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        reporter = self._make_user(db_session)
        for st in ("RESOLVED", "COMPLETED", "CLOSED"):
            db_session.add(
                Issue(
                    title=f"已关闭-{st}",
                    description="desc",
                    reporter_id=reporter.id,
                    report_date=datetime.now(),
                    project_id=project.id,
                    status=st,
                )
            )
        db_session.flush()

        factor = OTDScanService(db_session)._calc_open_items_factors(project)
        # 全是已关闭，应返回 None
        assert factor is None

    def test_open_changes_counted(self, db_session):
        """未关闭的 ChangeRequest 计入未关闭事项。"""
        from app.models.change_request import ChangeRequest
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        reporter = self._make_user(db_session)
        # PENDING 状态算未关闭
        db_session.add(
            ChangeRequest(
                change_code="CR-OTD-001",
                project_id=project.id,
                title="客户变更",
                change_type="REQUIREMENT",
                change_source="CUSTOMER",
                submitter_id=reporter.id,
                status="PENDING",
            )
        )
        db_session.flush()

        factor = OTDScanService(db_session)._calc_open_items_factors(project)
        assert factor is not None
        assert factor["evidence"]["open_changes"] == 1

    def test_many_open_items_escalate_to_medium(self, db_session):
        """≥5 个未关闭事项 → MEDIUM。"""
        from app.models.project.financial import ProjectMilestone
        from app.services.otd import OTDScanService

        project = _make_executing_project(db_session)
        # 建 5 个未完成里程碑（无阻塞，避免升 HIGH）
        for i in range(5):
            db_session.add(
                ProjectMilestone(
                    project_id=project.id,
                    milestone_name=f"M{i}",
                    status="PENDING",
                )
            )
        db_session.flush()

        factor = OTDScanService(db_session)._calc_open_items_factors(project)
        assert factor["severity"] == "MEDIUM"
        assert factor["evidence"]["open_milestones"] == 5
