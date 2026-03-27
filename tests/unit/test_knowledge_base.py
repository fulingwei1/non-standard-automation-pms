# -*- coding: utf-8 -*-
"""
知识自动沉淀模块 — 单元测试
覆盖：提取服务、归纳服务、预警服务、检索服务
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ── Helper: 构造 Mock 对象 ──────────────────────────


def _make_project(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.project_code = kwargs.get("project_code", "P2026-001")
    p.project_name = kwargs.get("project_name", "测试项目")
    p.project_type = kwargs.get("project_type", "销售")
    p.product_category = kwargs.get("product_category", "激光设备")
    p.industry = kwargs.get("industry", "半导体")
    p.customer_id = kwargs.get("customer_id", 10)
    p.stage = kwargs.get("stage", "S9")
    return p


def _make_risk(**kwargs):
    r = MagicMock()
    r.id = kwargs.get("id", 100)
    r.risk_name = kwargs.get("risk_name", "关键部件供应延迟")
    r.description = kwargs.get("description", "供应商交期不稳定")
    r.risk_type = MagicMock(value="SCHEDULE")
    r.risk_level = kwargs.get("risk_level", "HIGH")
    r.is_occurred = kwargs.get("is_occurred", True)
    r.mitigation_plan = kwargs.get("mitigation_plan", "提前备货并寻找备选供应商")
    r.contingency_plan = kwargs.get("contingency_plan", "启用安全库存")
    r.actual_impact = kwargs.get("actual_impact", "项目延期2周")
    r.project_id = kwargs.get("project_id", 1)
    return r


def _make_issue(**kwargs):
    i = MagicMock()
    i.id = kwargs.get("id", 200)
    i.title = kwargs.get("title", "激光器功率不达标")
    i.description = kwargs.get("description", "激光器实测功率低于标称值10%")
    i.category = kwargs.get("category", "QUALITY")
    i.severity = kwargs.get("severity", "HIGH")
    i.status = kwargs.get("status", "RESOLVED")
    i.solution = kwargs.get("solution", "更换激光器并重新校准")
    i.root_cause = kwargs.get("root_cause", "MATERIAL_DEFECT")
    i.impact_scope = kwargs.get("impact_scope", "整机性能")
    i.project_id = kwargs.get("project_id", 1)
    return i


def _make_ecn(**kwargs):
    e = MagicMock()
    e.id = kwargs.get("id", 300)
    e.ecn_no = kwargs.get("ecn_no", "ECN-2026-001")
    e.ecn_type = kwargs.get("ecn_type", "DESIGN")
    e.change_reason = kwargs.get("change_reason", "客户需求变更")
    e.solution = kwargs.get("solution", "重新设计光路")
    e.root_cause_analysis = kwargs.get("root_cause_analysis", "初期需求不明确")
    e.cost_impact = kwargs.get("cost_impact", Decimal("5000"))
    e.schedule_impact_days = kwargs.get("schedule_impact_days", 3)
    e.status = kwargs.get("status", "CLOSED")
    e.project_id = kwargs.get("project_id", 1)
    return e


def _make_stage(**kwargs):
    s = MagicMock()
    s.id = kwargs.get("id", 400)
    s.stage_code = kwargs.get("stage_code", "S4")
    s.stage_name = kwargs.get("stage_name", "加工制造")
    s.planned_end_date = kwargs.get("planned_end_date", date(2026, 3, 1))
    s.actual_end_date = kwargs.get("actual_end_date", date(2026, 3, 15))
    s.project_id = kwargs.get("project_id", 1)
    return s


def _make_db():
    """返回一个可链式调用的 mock db session"""
    db = MagicMock()
    return db


# ── 测试 KnowledgeExtractionService ─────────────────


class TestKnowledgeExtractionService:
    """经验教训自动提取服务测试"""

    def setup_method(self):
        self.db = _make_db()
        # 延迟导入以确保模块可用
        from app.services.knowledge.extraction_service import KnowledgeExtractionService
        self.service = KnowledgeExtractionService(self.db)

    def test_extract_from_risks_creates_entries(self):
        """从已发生风险中提取知识"""
        project = _make_project()
        risk = _make_risk()

        # mock: 查询风险返回一条
        self.db.query.return_value.filter.return_value.all.return_value = [risk]
        # mock: 去重检查返回 None（无重复）
        self.db.query.return_value.filter.return_value.first.return_value = None

        entries = self.service._extract_from_risks(project, created_by=1)

        assert len(entries) >= 1
        entry = entries[0]
        assert "风险经验" in entry.title
        assert entry.source_record_type == "project_risks"
        assert entry.risk_type == "SCHEDULE"

    def test_extract_from_risks_skips_no_mitigation(self):
        """跳过无应对措施的风险"""
        project = _make_project()
        risk = _make_risk(mitigation_plan=None, contingency_plan=None)

        self.db.query.return_value.filter.return_value.all.return_value = [risk]
        self.db.query.return_value.filter.return_value.first.return_value = None

        entries = self.service._extract_from_risks(project, created_by=1)
        assert len(entries) == 0

    def test_extract_from_issues_creates_entries(self):
        """从已解决问题中提取知识"""
        project = _make_project()
        issue = _make_issue()

        self.db.query.return_value.filter.return_value.all.return_value = [issue]
        self.db.query.return_value.filter.return_value.first.return_value = None

        entries = self.service._extract_from_issues(project, created_by=1)

        assert len(entries) >= 1
        assert "问题方案" in entries[0].title
        assert entries[0].issue_category == "QUALITY"

    def test_extract_from_ecns_groups_by_type(self):
        """按变更类型聚合提取"""
        project = _make_project()
        ecn1 = _make_ecn(id=301)
        ecn2 = _make_ecn(id=302)

        self.db.query.return_value.filter.return_value.all.return_value = [ecn1, ecn2]

        entries = self.service._extract_from_ecns(project, created_by=1)

        assert len(entries) >= 1
        assert "变更分析" in entries[0].title
        assert "DESIGN" in entries[0].title

    def test_extract_from_stage_delays(self):
        """从阶段延误中提取知识"""
        project = _make_project()
        stage = _make_stage()

        self.db.query.return_value.filter.return_value.all.return_value = [stage]
        self.db.query.return_value.filter.return_value.first.return_value = None

        entries = self.service._extract_from_stage_delays(project, created_by=1)

        assert len(entries) >= 1
        assert "延误分析" in entries[0].title
        assert "14" in entries[0].summary or "S4" in entries[0].summary

    def test_extract_from_stage_skips_on_time(self):
        """跳过未延误的阶段"""
        project = _make_project()
        stage = _make_stage(
            planned_end_date=date(2026, 3, 15),
            actual_end_date=date(2026, 3, 10),  # 提前完成
        )

        self.db.query.return_value.filter.return_value.all.return_value = [stage]

        entries = self.service._extract_from_stage_delays(project, created_by=1)
        assert len(entries) == 0

    def test_generate_code_format(self):
        """知识编号格式 KE-YYYYMMDD-NNN"""
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        code = self.service._generate_code()
        assert code.startswith("KE-")
        parts = code.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 3  # NNN


# ── 测试 BestPracticeInductionService ────────────────


class TestBestPracticeInductionService:
    """最佳实践归纳服务测试"""

    def setup_method(self):
        self.db = _make_db()
        from app.services.knowledge.induction_service import BestPracticeInductionService
        self.service = BestPracticeInductionService(self.db)

    def test_score_project_on_time(self):
        """项目按时交付评分"""
        project = _make_project()

        # mock stages: 无延误
        stage = _make_stage(
            planned_end_date=date(2026, 3, 15),
            actual_end_date=date(2026, 3, 15),
        )
        self.db.query.return_value.filter.return_value.all.return_value = [stage]
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.scalar.return_value = 0

        score = self.service._score_project(project)
        assert score["on_time"] is True
        assert score["total_delay"] == 0


# ── 测试 PitfallAlertService ────────────────────────


class TestPitfallAlertService:
    """坑点预警服务测试"""

    def setup_method(self):
        self.db = _make_db()
        from app.services.knowledge.pitfall_alert_service import PitfallAlertService
        self.service = PitfallAlertService(self.db)

    def test_generate_alerts_for_project(self):
        """为新项目生成预警"""
        project = _make_project()
        self.db.query.return_value.filter.return_value.first.return_value = project
        self.db.query.return_value.filter.return_value.delete.return_value = 0

        # mock: 知识条目查询返回空
        self.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

        result = self.service.generate_alerts(project.id)

        assert result["target_project_id"] == project.id
        assert "alerts_generated" in result
        assert "alerts" in result

    def test_mark_read(self):
        """标记预警已读"""
        alert = MagicMock()
        alert.id = 1
        alert.is_read = False
        self.db.query.return_value.filter.return_value.first.return_value = alert

        result = self.service.mark_read(1)
        assert result.is_read is True

    def test_submit_feedback_adopted(self):
        """提交采纳反馈"""
        alert = MagicMock()
        alert.id = 1
        alert.knowledge_entry_id = 10
        entry = MagicMock()
        entry.cite_count = 0

        self.db.query.return_value.filter.return_value.first.side_effect = [alert, entry]

        result = self.service.submit_feedback(1, is_adopted=True, feedback="有帮助")
        assert result.is_adopted is True
        assert result.is_read is True


# ── 测试 KnowledgeSearchService ─────────────────────


class TestKnowledgeSearchService:
    """知识检索服务测试"""

    def setup_method(self):
        self.db = _make_db()
        from app.services.knowledge.search_service import KnowledgeSearchService
        self.service = KnowledgeSearchService(self.db)

    def test_search_returns_paginated(self):
        """检索返回分页结果"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.search(keyword="测试", page=1, page_size=10)

        assert "total" in result
        assert "items" in result
        assert result["page"] == 1

    def test_vote_updates_score(self):
        """投票更新评分"""
        entry = MagicMock()
        entry.id = 1
        entry.vote_count = 2
        entry.usefulness_score = 4.0
        self.db.query.return_value.filter.return_value.first.return_value = entry

        result = self.service.vote(1, score=5.0)
        assert result.vote_count == 3
        # (4.0 * 2 + 5.0) / 3 ≈ 4.33
        assert abs(result.usefulness_score - 4.33) < 0.01

    def test_get_by_id_increments_view(self):
        """获取详情自动增加查看次数"""
        entry = MagicMock()
        entry.id = 1
        entry.view_count = 5
        self.db.query.return_value.filter.return_value.first.return_value = entry

        result = self.service.get_by_id(1)
        assert result.view_count == 6

    def test_vote_nonexistent_raises(self):
        """对不存在的条目投票抛异常"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="不存在"):
            self.service.vote(999, score=3.0)
