# -*- coding: utf-8 -*-
"""
I6 组：services 剩余核心文件单元测试

覆盖以下文件：
- app/services/evm_service.py         (EVMCalculator 纯数学计算)
- app/services/health_calculator.py   (HealthCalculator 健康度逻辑)
- app/services/notification_service.py (NotificationService 通知触发)
- app/services/session_service.py     (SessionService 会话工具)
- app/services/project_relations_service.py (关系发现 / 统计)
- app/services/report_service.py      (ReportService 报表生成)
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch


# ===========================================================================
# 一、evm_service.py — EVMCalculator 纯数学计算
# ===========================================================================

class TestEVMCalculator:
    """EVM 计算器测试 - 全为纯数学，无 DB 依赖"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.evm_service import EVMCalculator
        self.calc = EVMCalculator

    # ---- SV ----------------------------------------------------------------
    def test_schedule_variance_positive(self):
        """EV > PV => 进度超前，SV > 0"""
        sv = self.calc.calculate_schedule_variance(
            ev=Decimal("120"), pv=Decimal("100")
        )
        assert sv == Decimal("20.0000")

    def test_schedule_variance_negative(self):
        """EV < PV => 进度落后，SV < 0"""
        sv = self.calc.calculate_schedule_variance(
            ev=Decimal("80"), pv=Decimal("100")
        )
        assert sv == Decimal("-20.0000")

    def test_schedule_variance_zero(self):
        """EV == PV => SV == 0"""
        sv = self.calc.calculate_schedule_variance(
            ev=Decimal("100"), pv=Decimal("100")
        )
        assert sv == Decimal("0.0000")

    # ---- CV ----------------------------------------------------------------
    def test_cost_variance_positive(self):
        """EV > AC => 成本节约，CV > 0"""
        cv = self.calc.calculate_cost_variance(
            ev=Decimal("110"), ac=Decimal("100")
        )
        assert cv == Decimal("10.0000")

    def test_cost_variance_negative(self):
        """EV < AC => 成本超支，CV < 0"""
        cv = self.calc.calculate_cost_variance(
            ev=Decimal("90"), ac=Decimal("100")
        )
        assert cv == Decimal("-10.0000")

    # ---- SPI ---------------------------------------------------------------
    def test_spi_normal(self):
        """SPI = EV / PV"""
        spi = self.calc.calculate_schedule_performance_index(
            ev=Decimal("80"), pv=Decimal("100")
        )
        assert spi == Decimal("0.800000")

    def test_spi_pv_zero_returns_none(self):
        """PV=0 时 SPI 应返回 None"""
        spi = self.calc.calculate_schedule_performance_index(
            ev=Decimal("100"), pv=Decimal("0")
        )
        assert spi is None

    def test_spi_greater_than_one(self):
        """SPI > 1 表示进度超前"""
        spi = self.calc.calculate_schedule_performance_index(
            ev=Decimal("120"), pv=Decimal("100")
        )
        assert spi > Decimal("1")

    # ---- CPI ---------------------------------------------------------------
    def test_cpi_normal(self):
        """CPI = EV / AC"""
        cpi = self.calc.calculate_cost_performance_index(
            ev=Decimal("100"), ac=Decimal("80")
        )
        assert cpi == Decimal("1.250000")

    def test_cpi_ac_zero_returns_none(self):
        """AC=0 时 CPI 应返回 None"""
        cpi = self.calc.calculate_cost_performance_index(
            ev=Decimal("100"), ac=Decimal("0")
        )
        assert cpi is None

    # ---- EAC ---------------------------------------------------------------
    def test_eac_standard_formula(self):
        """EAC = AC + (BAC - EV) / CPI"""
        eac = self.calc.calculate_estimate_at_completion(
            bac=Decimal("1000"),
            ev=Decimal("400"),
            ac=Decimal("500"),
        )
        # CPI = 400/500 = 0.8; EAC = 500 + 600/0.8 = 500+750 = 1250
        assert eac == Decimal("1250.0000")

    def test_eac_simplified_when_cpi_unavailable(self):
        """AC=0 => CPI=None => 简化公式 EAC = AC + (BAC - EV)"""
        eac = self.calc.calculate_estimate_at_completion(
            bac=Decimal("1000"),
            ev=Decimal("300"),
            ac=Decimal("0"),
        )
        # EAC = 0 + (1000 - 300) = 700
        assert eac == Decimal("700.0000")

    # ---- VAC ---------------------------------------------------------------
    def test_vac_positive(self):
        """BAC > EAC => 预计节约"""
        vac = self.calc.calculate_variance_at_completion(
            bac=Decimal("1000"), eac=Decimal("900")
        )
        assert vac == Decimal("100.0000")

    def test_vac_negative(self):
        """BAC < EAC => 预计超支"""
        vac = self.calc.calculate_variance_at_completion(
            bac=Decimal("1000"), eac=Decimal("1100")
        )
        assert vac == Decimal("-100.0000")

    # ---- TCPI --------------------------------------------------------------
    def test_tcpi_bac_based(self):
        """TCPI(BAC) = (BAC-EV)/(BAC-AC)"""
        tcpi = self.calc.calculate_to_complete_performance_index(
            bac=Decimal("1000"),
            ev=Decimal("400"),
            ac=Decimal("500"),
        )
        # (1000-400)/(1000-500) = 600/500 = 1.2
        assert tcpi == Decimal("1.200000")

    def test_tcpi_denominator_zero_returns_none(self):
        """BAC-AC=0 => TCPI 应返回 None"""
        tcpi = self.calc.calculate_to_complete_performance_index(
            bac=Decimal("1000"),
            ev=Decimal("400"),
            ac=Decimal("1000"),
        )
        assert tcpi is None

    # ---- percent_complete --------------------------------------------------
    def test_percent_complete_normal(self):
        pct = self.calc.calculate_percent_complete(
            value=Decimal("50"), bac=Decimal("200")
        )
        assert pct == Decimal("25.00")

    def test_percent_complete_bac_zero_returns_none(self):
        pct = self.calc.calculate_percent_complete(
            value=Decimal("50"), bac=Decimal("0")
        )
        assert pct is None

    # ---- calculate_all_metrics ---------------------------------------------
    def test_calculate_all_metrics_keys(self):
        """calculate_all_metrics 返回字典包含所有预期键"""
        metrics = self.calc.calculate_all_metrics(
            pv=100, ev=90, ac=80, bac=500
        )
        expected_keys = {"sv", "cv", "spi", "cpi", "eac", "etc", "vac",
                         "tcpi", "planned_percent_complete", "actual_percent_complete"}
        assert expected_keys.issubset(set(metrics.keys()))

    def test_calculate_all_metrics_values_correct(self):
        """综合验证：计算结果与手算一致"""
        metrics = self.calc.calculate_all_metrics(
            pv=100, ev=80, ac=90, bac=500
        )
        assert metrics["sv"] == Decimal("-20.0000")   # 80-100
        assert metrics["cv"] == Decimal("-10.0000")   # 80-90
        # SPI = 80/100 = 0.8
        assert metrics["spi"] == Decimal("0.800000")
        # CPI = 80/90 ≈ 0.888889
        assert metrics["cpi"] is not None


# ===========================================================================
# 二、health_calculator.py — HealthCalculator
# ===========================================================================

class TestHealthCalculator:
    """健康度计算器测试 - mock DB"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.health_calculator import HealthCalculator
        self.db = MagicMock()
        self.calc = HealthCalculator(db=self.db)

    def _make_project(self, **kwargs):
        """构造最小化 mock 项目"""
        p = MagicMock()
        p.id = 1
        p.status = kwargs.get("status", "ST01")
        p.planned_start_date = kwargs.get("planned_start_date", None)
        p.planned_end_date = kwargs.get("planned_end_date", None)
        p.progress_pct = kwargs.get("progress_pct", Decimal("0"))
        p.customer_id = kwargs.get("customer_id", None)
        p.customer_name = kwargs.get("customer_name", None)
        p.pm_id = kwargs.get("pm_id", None)
        p.pm_name = kwargs.get("pm_name", None)
        return p

    # ---- _is_closed --------------------------------------------------------
    def test_is_closed_ST30(self):
        project = self._make_project(status="ST30")
        assert self.calc._is_closed(project) is True

    def test_is_closed_ST99(self):
        project = self._make_project(status="ST99")
        assert self.calc._is_closed(project) is True

    def test_is_closed_active(self):
        project = self._make_project(status="ST05")
        assert self.calc._is_closed(project) is False

    # ---- _is_blocked -------------------------------------------------------
    def test_blocked_by_status_ST14(self):
        """缺料阻塞状态 ST14 => blocked"""
        # 让 DB 查询返回 0（避免其他条件干扰）
        self.db.query.return_value.filter.return_value.count.return_value = 0
        project = self._make_project(status="ST14")
        assert self.calc._is_blocked(project) is True

    def test_blocked_by_status_ST19(self):
        """技术阻塞状态 ST19 => blocked"""
        self.db.query.return_value.filter.return_value.count.return_value = 0
        project = self._make_project(status="ST19")
        assert self.calc._is_blocked(project) is True

    def test_not_blocked_normal_status(self):
        """正常状态且无阻塞任务/问题/预警 => not blocked"""
        self.db.query.return_value.filter.return_value.count.return_value = 0
        self.db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        project = self._make_project(status="ST05")
        assert self.calc._is_blocked(project) is False

    def test_blocked_by_critical_tasks(self):
        """有阻塞关键任务 => blocked"""
        # count > 0 => _has_blocked_critical_tasks => True
        self.db.query.return_value.filter.return_value.count.return_value = 1
        project = self._make_project(status="ST05")
        assert self.calc._is_blocked(project) is True

    # ---- _is_deadline_approaching ------------------------------------------
    def test_deadline_approaching_within_7_days(self):
        today = date.today()
        project = self._make_project(planned_end_date=today + timedelta(days=3))
        assert self.calc._is_deadline_approaching(project, days=7) is True

    def test_deadline_not_approaching(self):
        today = date.today()
        project = self._make_project(planned_end_date=today + timedelta(days=30))
        assert self.calc._is_deadline_approaching(project, days=7) is False

    def test_deadline_no_end_date(self):
        project = self._make_project(planned_end_date=None)
        assert self.calc._is_deadline_approaching(project) is False

    # ---- _has_schedule_variance --------------------------------------------
    def test_schedule_variance_exceeds_threshold(self):
        """计划进度远高于实际进度 => variance > 10%"""
        today = date.today()
        project = self._make_project(
            planned_start_date=today - timedelta(days=50),
            planned_end_date=today + timedelta(days=50),
            progress_pct=Decimal("0"),  # 0% actual, ~50% planned
        )
        assert self.calc._has_schedule_variance(project, threshold=10) is True

    def test_schedule_variance_within_threshold(self):
        """实际进度和计划进度接近 => variance <= 10%"""
        today = date.today()
        project = self._make_project(
            planned_start_date=today - timedelta(days=50),
            planned_end_date=today + timedelta(days=50),
            progress_pct=Decimal("49"),  # ~49% actual, ~50% planned
        )
        assert self.calc._has_schedule_variance(project, threshold=10) is False

    # ---- calculate_health --------------------------------------------------
    def test_calculate_health_H4_closed(self):
        project = self._make_project(status="ST30")
        health = self.calc.calculate_health(project)
        assert health == "H4"

    def test_calculate_health_H3_blocked(self):
        self.db.query.return_value.filter.return_value.count.return_value = 0
        self.db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        project = self._make_project(status="ST14")
        health = self.calc.calculate_health(project)
        assert health == "H3"

    def test_calculate_health_H2_risk(self):
        """整改中状态 => H2（有风险）"""
        self.db.query.return_value.filter.return_value.count.return_value = 0
        self.db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        project = self._make_project(status="ST22")  # FAT整改中
        health = self.calc.calculate_health(project)
        assert health == "H2"

    def test_calculate_health_H1_normal(self):
        """无风险、无阻塞、未完结 => H1"""
        self.db.query.return_value.filter.return_value.count.return_value = 0
        self.db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        today = date.today()
        project = self._make_project(
            status="ST05",
            planned_start_date=today - timedelta(days=10),
            planned_end_date=today + timedelta(days=90),
            progress_pct=Decimal("10"),
        )
        health = self.calc.calculate_health(project)
        assert health == "H1"


# ===========================================================================
# 三、notification_service.py — NotificationService
# ===========================================================================

class TestNotificationService:
    """通知服务测试 - mock 掉统一服务"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.notification_service import NotificationService
        self.svc = NotificationService()
        self.db = MagicMock()

    def _make_unified_service_mock(self, success=True):
        """返回模拟统一服务"""
        unified = MagicMock()
        unified.send_notification.return_value = {"success": success, "notification_id": 1}
        return unified

    # ---- _get_enabled_channels ---------------------------------------------
    def test_enabled_channels_always_has_web(self):
        """站内通知 (WEB) 始终在启用渠道中"""
        from app.services.notification_service import NotificationChannel
        assert NotificationChannel.WEB in self.svc.enabled_channels

    # ---- _infer_category ---------------------------------------------------
    def test_infer_category_task(self):
        from app.services.notification_service import NotificationType
        cat = self.svc._infer_category(NotificationType.TASK_ASSIGNED)
        assert cat == "task"

    def test_infer_category_project(self):
        from app.services.notification_service import NotificationType
        cat = self.svc._infer_category(NotificationType.PROJECT_UPDATE)
        assert cat == "project"

    def test_infer_category_general_fallback(self):
        from app.services.notification_service import NotificationType
        cat = self.svc._infer_category(NotificationType.SYSTEM_ANNOUNCEMENT)
        assert cat == "general"

    # ---- _map_old_channel_to_new -------------------------------------------
    def test_map_channel_web_to_system(self):
        from app.services.notification_service import NotificationChannel
        from app.services.channel_handlers.base import NotificationChannel as UC
        mapped = self.svc._map_old_channel_to_new(NotificationChannel.WEB)
        assert mapped == UC.SYSTEM

    def test_map_channel_email(self):
        from app.services.notification_service import NotificationChannel
        from app.services.channel_handlers.base import NotificationChannel as UC
        mapped = self.svc._map_old_channel_to_new(NotificationChannel.EMAIL)
        assert mapped == UC.EMAIL

    # ---- send_notification -------------------------------------------------
    @patch("app.services.notification_service.get_notification_service")
    def test_send_notification_success(self, mock_get_svc):
        """send_notification 成功时返回 True"""
        from app.services.notification_service import NotificationType, NotificationPriority
        mock_unified = self._make_unified_service_mock(success=True)
        mock_get_svc.return_value = mock_unified

        result = self.svc.send_notification(
            db=self.db,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="新任务",
            content="你有新任务",
        )
        assert result is True
        mock_unified.send_notification.assert_called_once()

    @patch("app.services.notification_service.get_notification_service")
    def test_send_notification_failure(self, mock_get_svc):
        """统一服务返回 success=False 时应返回 False"""
        from app.services.notification_service import NotificationType
        mock_unified = self._make_unified_service_mock(success=False)
        mock_get_svc.return_value = mock_unified

        result = self.svc.send_notification(
            db=self.db,
            recipient_id=1,
            notification_type=NotificationType.PROJECT_UPDATE,
            title="项目更新",
            content="项目状态变更",
        )
        assert result is False

    def test_send_notification_no_db_returns_false(self):
        """未传入 db 时应直接返回 False"""
        from app.services.notification_service import NotificationType
        result = self.svc.send_notification(
            db=None,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="x",
            content="x",
        )
        assert result is False

    # ---- send_task_assigned_notification -----------------------------------
    @patch("app.services.notification_service.get_notification_service")
    def test_send_task_assigned_with_due_date(self, mock_get_svc):
        """发送任务分配通知时，截止日期应包含在 content 中"""
        mock_unified = self._make_unified_service_mock(success=True)
        mock_get_svc.return_value = mock_unified
        due = datetime(2026, 3, 31)

        self.svc.send_task_assigned_notification(
            db=self.db,
            assignee_id=42,
            task_name="测试任务",
            project_name="测试项目",
            task_id=1,
            due_date=due,
        )
        # 验证统一服务被调用，且 request.content 包含日期
        call_args = mock_unified.send_notification.call_args
        request = call_args[0][0]
        assert "2026-03-31" in request.content

    # ---- send_deadline_reminder -------------------------------------------
    @patch("app.services.notification_service.get_notification_service")
    def test_deadline_reminder_urgent_title(self, mock_get_svc):
        """剩余天数≤1 时标题应包含'紧急'"""
        mock_unified = self._make_unified_service_mock(success=True)
        mock_get_svc.return_value = mock_unified

        self.svc.send_deadline_reminder(
            db=self.db,
            recipient_id=1,
            task_name="紧急任务",
            due_date=datetime.now(),
            days_remaining=1,
        )
        call_args = mock_unified.send_notification.call_args
        request = call_args[0][0]
        assert "紧急" in request.title

    @patch("app.services.notification_service.get_notification_service")
    def test_deadline_reminder_normal_title(self, mock_get_svc):
        """剩余天数>1 时标题应包含'提醒'"""
        mock_unified = self._make_unified_service_mock(success=True)
        mock_get_svc.return_value = mock_unified

        self.svc.send_deadline_reminder(
            db=self.db,
            recipient_id=1,
            task_name="普通任务",
            due_date=datetime.now() + timedelta(days=5),
            days_remaining=5,
        )
        call_args = mock_unified.send_notification.call_args
        request = call_args[0][0]
        assert "提醒" in request.title


# ===========================================================================
# 四、session_service.py — SessionService 工具方法
# ===========================================================================

class TestSessionService:
    """会话服务测试 - 主要测试无 Redis 依赖的逻辑"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.session_service import SessionService
        self.svc = SessionService

    # ---- _parse_user_agent -------------------------------------------------
    def test_parse_user_agent_returns_dict(self):
        ua_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
        result = self.svc._parse_user_agent(ua_str)
        assert isinstance(result, dict)

    def test_parse_user_agent_invalid_returns_empty(self):
        result = self.svc._parse_user_agent("")
        assert isinstance(result, dict)

    # ---- get_user_sessions -------------------------------------------------
    def test_get_user_sessions_active_only(self):
        """active_only=True 时只查询活跃会话"""
        db = MagicMock()
        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = self.svc.get_user_sessions(db, user_id=1, active_only=True)
        assert result == []
        # 确保调用了 filter（包含 is_active 条件）
        db.query.assert_called_once()

    def test_get_user_sessions_marks_current(self):
        """current_jti 匹配时，会话 is_current 应被标记为 True"""
        db = MagicMock()

        # 创建两个 mock 会话
        sess1 = MagicMock()
        sess1.access_token_jti = "jti_current"
        sess2 = MagicMock()
        sess2.access_token_jti = "jti_other"

        mock_query = MagicMock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sess1, sess2]

        self.svc.get_user_sessions(db, user_id=1, current_jti="jti_current")
        assert sess1.is_current is True
        assert sess2.is_current is False

    # ---- get_session_by_jti ------------------------------------------------
    def test_get_session_by_jti_access(self):
        """根据 access token jti 查询会话"""
        db = MagicMock()
        mock_sess = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_sess

        result = self.svc.get_session_by_jti(db, jti="test_jti", token_type="access")
        assert result == mock_sess

    def test_get_session_by_jti_refresh(self):
        """根据 refresh token jti 查询会话"""
        db = MagicMock()
        mock_sess = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_sess

        result = self.svc.get_session_by_jti(db, jti="test_jti", token_type="refresh")
        assert result == mock_sess

    # ---- _assess_risk ------------------------------------------------------
    def test_assess_risk_new_user_zero_risk(self):
        """新用户无历史记录 => risk_score=0, not suspicious"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        is_suspicious, risk_score = self.svc._assess_risk(
            db, user_id=999, ip_address="1.2.3.4",
            device_info=None, location="上海"
        )
        assert is_suspicious is False
        assert risk_score == 0

    def test_assess_risk_new_ip_increases_score(self):
        """已有历史记录但 IP 从未出现过 => risk_score += 30"""
        db = MagicMock()
        old_sess = MagicMock()
        old_sess.ip_address = "192.168.1.1"
        old_sess.device_id = "device_old"
        old_sess.location = "北京"
        old_sess.login_at = datetime.utcnow() - timedelta(days=1)

        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [old_sess]

        _, risk_score = self.svc._assess_risk(
            db, user_id=1, ip_address="10.0.0.1",
            device_info=None, location="上海"
        )
        assert risk_score >= 30

    # ---- cleanup_expired_sessions ------------------------------------------
    def test_cleanup_expired_sessions_marks_inactive(self):
        """过期会话应被标记为非活跃"""
        db = MagicMock()

        expired_sess = MagicMock()
        expired_sess.is_active = True
        expired_sess.id = 1

        db.query.return_value.filter.return_value.all.return_value = [expired_sess]

        # patch Redis helper
        with patch.object(self.svc, "_remove_session_cache"):
            count = self.svc.cleanup_expired_sessions(db)

        assert count == 1
        assert expired_sess.is_active is False
        db.commit.assert_called_once()


# ===========================================================================
# 五、project_relations_service.py — 统计与发现函数
# ===========================================================================

class TestProjectRelationsService:
    """项目关联关系测试"""

    # ---- calculate_relation_statistics -------------------------------------
    def test_calculate_statistics_empty(self):
        from app.services.project_relations_service import calculate_relation_statistics
        stats = calculate_relation_statistics([])
        assert stats["total_relations"] == 0
        assert stats["by_strength"] == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    def test_calculate_statistics_counts(self):
        from app.services.project_relations_service import calculate_relation_statistics
        relations = [
            {"type": "MATERIAL_TRANSFER_OUT", "strength": "MEDIUM"},
            {"type": "MATERIAL_TRANSFER_IN",  "strength": "MEDIUM"},
            {"type": "SHARED_CUSTOMER",        "strength": "LOW"},
            {"type": "SHARED_RESOURCE",        "strength": "HIGH"},
        ]
        stats = calculate_relation_statistics(relations)
        assert stats["total_relations"] == 4
        assert stats["by_strength"]["HIGH"] == 1
        assert stats["by_strength"]["MEDIUM"] == 2
        assert stats["by_strength"]["LOW"] == 1
        assert stats["by_type"]["MATERIAL_TRANSFER_OUT"] == 1

    def test_calculate_statistics_by_type_aggregation(self):
        """同类型多条记录 by_type 应正确累加"""
        from app.services.project_relations_service import calculate_relation_statistics
        relations = [
            {"type": "SHARED_CUSTOMER", "strength": "LOW"},
            {"type": "SHARED_CUSTOMER", "strength": "LOW"},
        ]
        stats = calculate_relation_statistics(relations)
        assert stats["by_type"]["SHARED_CUSTOMER"] == 2

    # ---- discover_same_customer_relations ----------------------------------
    def test_discover_same_customer_no_customer_id(self):
        """项目无 customer_id 时，返回空列表"""
        from app.services.project_relations_service import discover_same_customer_relations
        db = MagicMock()
        project = MagicMock()
        project.customer_id = None
        result = discover_same_customer_relations(db, project, project_id=1)
        assert result == []

    def test_discover_same_customer_returns_relations(self):
        """相同客户的其他项目应被返回"""
        from app.services.project_relations_service import discover_same_customer_relations

        related = MagicMock()
        related.id = 2
        related.project_code = "PJ-002"
        related.project_name = "相关项目"

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [related]

        project = MagicMock()
        project.customer_id = 10
        project.customer_name = "客户A"

        result = discover_same_customer_relations(db, project, project_id=1)
        assert len(result) == 1
        assert result[0]["relation_type"] == "SAME_CUSTOMER"
        assert result[0]["related_project_id"] == 2

    # ---- discover_same_pm_relations ----------------------------------------
    def test_discover_same_pm_no_pm_id(self):
        """项目无 pm_id 时，返回空列表"""
        from app.services.project_relations_service import discover_same_pm_relations
        db = MagicMock()
        project = MagicMock()
        project.pm_id = None
        result = discover_same_pm_relations(db, project, project_id=1)
        assert result == []

    def test_discover_same_pm_returns_relations(self):
        """相同 PM 的其他项目应被返回"""
        from app.services.project_relations_service import discover_same_pm_relations

        related = MagicMock()
        related.id = 3
        related.project_code = "PJ-003"
        related.project_name = "同PM项目"

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [related]

        project = MagicMock()
        project.pm_id = 5
        project.pm_name = "张三"

        result = discover_same_pm_relations(db, project, project_id=1)
        assert len(result) == 1
        assert result[0]["relation_type"] == "SAME_PM"
        assert "张三" in result[0]["reason"]

    # ---- get_material_transfer_relations -----------------------------------
    def test_get_material_transfer_relations_wrong_type(self):
        """relation_type 不匹配时返回空列表"""
        from app.services.project_relations_service import get_material_transfer_relations
        db = MagicMock()
        result = get_material_transfer_relations(db, project_id=1, relation_type="SHARED_RESOURCE")
        assert result == []


# ===========================================================================
# 六、report_service.py — ReportService 报表生成
# ===========================================================================

class TestReportService:
    """工时报表服务测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.services.report_service import ReportService
        self.svc = ReportService

    # ---- get_active_monthly_templates --------------------------------------
    @patch("app.services.report_service.ReportTemplate")
    def test_get_active_monthly_templates_calls_db(self, MockTemplate):
        """get_active_monthly_templates 应查询 enabled+MONTHLY 模板"""
        db = MagicMock()
        mock_templates = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.all.return_value = mock_templates

        result = self.svc.get_active_monthly_templates(db)
        assert result == mock_templates
        db.query.assert_called_once_with(MockTemplate)

    @patch("app.services.report_service.ReportTemplate")
    def test_get_active_monthly_templates_empty(self, MockTemplate):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = self.svc.get_active_monthly_templates(db)
        assert result == []

    # ---- generate_report ---------------------------------------------------
    def test_generate_report_template_not_found(self):
        """模板不存在时应抛出 ValueError"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="报表模板不存在"):
            self.svc.generate_report(db, template_id=9999, period="2026-01")

    def test_generate_report_unsupported_type(self):
        """不支持的报表类型应抛出 ValueError"""
        db = MagicMock()
        template = MagicMock()
        template.id = 1
        template.report_type = "UNKNOWN_TYPE"
        db.query.return_value.filter.return_value.first.return_value = template

        with pytest.raises(ValueError, match="不支持的报表类型"):
            self.svc.generate_report(db, template_id=1, period="2026-01")

    @patch.object(
        __import__("app.services.report_service", fromlist=["ReportService"]).ReportService,
        "_generate_user_monthly_report",
        return_value={"rows": [], "summary": {}}
    )
    def test_generate_report_user_monthly(self, mock_gen):
        """USER_MONTHLY 类型应调用 _generate_user_monthly_report"""
        from app.models.report import ReportTypeEnum

        db = MagicMock()
        template = MagicMock()
        template.id = 1
        template.report_type = ReportTypeEnum.USER_MONTHLY.value
        db.query.return_value.filter.return_value.first.return_value = template

        result = self.svc.generate_report(db, template_id=1, period="2026-01")
        assert result["period"] == "2026-01"
        mock_gen.assert_called_once()

    def test_generate_report_period_parsing(self):
        """period 格式错误（无法解析）时应抛出异常"""
        db = MagicMock()
        template = MagicMock()
        template.id = 1
        template.report_type = "USER_MONTHLY"
        db.query.return_value.filter.return_value.first.return_value = template

        with pytest.raises(Exception):
            self.svc.generate_report(db, template_id=1, period="invalid-period")

    # ---- generate_report 验证 generated_by 字段 ---------------------------
    @patch.object(
        __import__("app.services.report_service", fromlist=["ReportService"]).ReportService,
        "_generate_dept_monthly_report",
        return_value={"rows": []}
    )
    def test_generate_report_sets_generated_by(self, _mock):
        """generate_report 返回的数据应包含 generated_by 字段"""
        from app.models.report import ReportTypeEnum

        db = MagicMock()
        template = MagicMock()
        template.id = 1
        template.report_type = ReportTypeEnum.DEPT_MONTHLY.value
        db.query.return_value.filter.return_value.first.return_value = template

        result = self.svc.generate_report(
            db, template_id=1, period="2026-02", generated_by="USER_42"
        )
        assert result["generated_by"] == "USER_42"
