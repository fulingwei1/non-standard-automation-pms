# -*- coding: utf-8 -*-
"""
AlertEfficiencyService 综合单元测试

测试覆盖:
- calculate_basic_metrics: 计算基础效率指标
- calculate_project_metrics: 按项目统计处理效率
- calculate_handler_metrics: 按责任人统计处理效率
- calculate_type_metrics: 按类型统计处理效率
- generate_rankings: 生成效率排行榜
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestCalculateBasicMetrics:
    """测试 calculate_basic_metrics 函数"""

    def test_returns_zeros_when_no_alerts(self):
        """测试无预警时返回零值"""
        from app.services.alert_efficiency_service import calculate_basic_metrics

        mock_engine = MagicMock()

        result = calculate_basic_metrics([], mock_engine)

        assert result["processing_rate"] == 0
        assert result["timely_processing_rate"] == 0
        assert result["escalation_rate"] == 0
        assert result["duplicate_rate"] == 0

    def test_calculates_processing_rate(self):
        """测试计算处理率"""
        from app.services.alert_efficiency_service import calculate_basic_metrics

        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {"WARNING": 8}

        mock_alert1 = MagicMock()
        mock_alert1.status = "RESOLVED"
        mock_alert1.alert_level = "WARNING"
        mock_alert1.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert1.acknowledged_at = datetime.now()
        mock_alert1.is_escalated = False
        mock_alert1.rule_id = 1
        mock_alert1.target_type = "PROJECT"
        mock_alert1.target_id = 1

        mock_alert2 = MagicMock()
        mock_alert2.status = "PENDING"
        mock_alert2.is_escalated = False
        mock_alert2.rule_id = 2
        mock_alert2.target_type = "PROJECT"
        mock_alert2.target_id = 2
        mock_alert2.triggered_at = datetime.now()

        alerts = [mock_alert1, mock_alert2]

        result = calculate_basic_metrics(alerts, mock_engine)

        assert result["processing_rate"] == 0.5  # 1/2

    def test_calculates_timely_processing_rate(self):
        """测试计算及时处理率"""
        from app.services.alert_efficiency_service import calculate_basic_metrics

        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {"WARNING": 8, "CRITICAL": 4}

        # 及时处理的预警
        mock_alert1 = MagicMock()
        mock_alert1.status = "RESOLVED"
        mock_alert1.alert_level = "WARNING"
        mock_alert1.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert1.acknowledged_at = datetime.now() - timedelta(hours=1)
        mock_alert1.is_escalated = False
        mock_alert1.rule_id = 1
        mock_alert1.target_type = "PROJECT"
        mock_alert1.target_id = 1

        # 超时处理的预警
        mock_alert2 = MagicMock()
        mock_alert2.status = "CLOSED"
        mock_alert2.alert_level = "CRITICAL"
        mock_alert2.triggered_at = datetime.now() - timedelta(hours=10)
        mock_alert2.acknowledged_at = datetime.now()
        mock_alert2.is_escalated = False
        mock_alert2.rule_id = 2
        mock_alert2.target_type = "PROJECT"
        mock_alert2.target_id = 2

        alerts = [mock_alert1, mock_alert2]

        result = calculate_basic_metrics(alerts, mock_engine)

        assert result["timely_processing_rate"] == 0.5  # 1/2

    def test_calculates_escalation_rate(self):
        """测试计算升级率"""
        from app.services.alert_efficiency_service import calculate_basic_metrics

        mock_engine = MagicMock()

        mock_alert1 = MagicMock()
        mock_alert1.status = "PENDING"
        mock_alert1.is_escalated = True
        mock_alert1.rule_id = 1
        mock_alert1.target_type = "PROJECT"
        mock_alert1.target_id = 1
        mock_alert1.triggered_at = datetime.now()

        mock_alert2 = MagicMock()
        mock_alert2.status = "PENDING"
        mock_alert2.is_escalated = False
        mock_alert2.rule_id = 2
        mock_alert2.target_type = "PROJECT"
        mock_alert2.target_id = 2
        mock_alert2.triggered_at = datetime.now()

        alerts = [mock_alert1, mock_alert2]

        result = calculate_basic_metrics(alerts, mock_engine)

        assert result["escalation_rate"] == 0.5  # 1/2

    def test_calculates_duplicate_rate(self):
        """测试计算重复预警率"""
        from app.services.alert_efficiency_service import calculate_basic_metrics

        mock_engine = MagicMock()

        now = datetime.now()

        # 第一个预警
        mock_alert1 = MagicMock()
        mock_alert1.status = "PENDING"
        mock_alert1.is_escalated = False
        mock_alert1.rule_id = 1
        mock_alert1.target_type = "PROJECT"
        mock_alert1.target_id = 1
        mock_alert1.triggered_at = now - timedelta(hours=12)

        # 重复预警（同规则、同目标、24小时内）
        mock_alert2 = MagicMock()
        mock_alert2.status = "PENDING"
        mock_alert2.is_escalated = False
        mock_alert2.rule_id = 1  # 相同规则
        mock_alert2.target_type = "PROJECT"  # 相同类型
        mock_alert2.target_id = 1  # 相同目标
        mock_alert2.triggered_at = now

        # 不同规则的预警
        mock_alert3 = MagicMock()
        mock_alert3.status = "PENDING"
        mock_alert3.is_escalated = False
        mock_alert3.rule_id = 2
        mock_alert3.target_type = "PROJECT"
        mock_alert3.target_id = 1
        mock_alert3.triggered_at = now

        alerts = [mock_alert1, mock_alert2, mock_alert3]

        result = calculate_basic_metrics(alerts, mock_engine)

        # 1个重复 / 3个总数
        assert abs(result["duplicate_rate"] - 1/3) < 0.01


class TestCalculateProjectMetrics:
    """测试 calculate_project_metrics 函数"""

    def test_returns_empty_when_no_project_alerts(self):
        """测试无项目预警时返回空"""
        from app.services.alert_efficiency_service import calculate_project_metrics

        mock_db = MagicMock()
        mock_engine = MagicMock()

        mock_alert = MagicMock()
        mock_alert.project_id = None

        result = calculate_project_metrics([mock_alert], mock_db, mock_engine)

        assert result == {}

    def test_groups_by_project(self):
        """测试按项目分组"""
        from app.services.alert_efficiency_service import calculate_project_metrics

        mock_db = MagicMock()
        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {"WARNING": 8}

        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.status = "RESOLVED"
        mock_alert.alert_level = "WARNING"
        mock_alert.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert.acknowledged_at = datetime.now()
        mock_alert.is_escalated = False

        result = calculate_project_metrics([mock_alert], mock_db, mock_engine)

        assert "测试项目" in result
        assert result["测试项目"]["total"] == 1
        assert result["测试项目"]["processing_rate"] == 1.0

    def test_calculates_efficiency_score(self):
        """测试计算效率得分"""
        from app.services.alert_efficiency_service import calculate_project_metrics

        mock_db = MagicMock()
        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {"WARNING": 8}

        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.status = "RESOLVED"
        mock_alert.alert_level = "WARNING"
        mock_alert.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert.acknowledged_at = datetime.now() - timedelta(hours=1)
        mock_alert.is_escalated = False

        result = calculate_project_metrics([mock_alert], mock_db, mock_engine)

        # 效率得分 = 处理率*0.4 + 及时处理率*0.4 + (1-升级率)*0.2
        # = 1*0.4 + 1*0.4 + 1*0.2 = 1.0 * 100 = 100
        assert result["测试项目"]["efficiency_score"] == 100


class TestCalculateHandlerMetrics:
    """测试 calculate_handler_metrics 函数"""

    def test_returns_empty_when_no_handlers(self):
        """测试无责任人时返回空"""
        from app.services.alert_efficiency_service import calculate_handler_metrics

        mock_db = MagicMock()
        mock_engine = MagicMock()

        mock_alert = MagicMock()
        mock_alert.handler_id = None
        mock_alert.acknowledged_by = None

        result = calculate_handler_metrics([mock_alert], mock_db, mock_engine)

        assert result == {}

    def test_groups_by_handler(self):
        """测试按责任人分组"""
        from app.services.alert_efficiency_service import calculate_handler_metrics

        mock_db = MagicMock()
        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {"WARNING": 8}

        mock_user = MagicMock()
        mock_user.username = "张三"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_alert = MagicMock()
        mock_alert.handler_id = 1
        mock_alert.acknowledged_by = None
        mock_alert.status = "RESOLVED"
        mock_alert.alert_level = "WARNING"
        mock_alert.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert.acknowledged_at = datetime.now()
        mock_alert.is_escalated = False

        result = calculate_handler_metrics([mock_alert], mock_db, mock_engine)

        assert "张三" in result
        assert result["张三"]["total"] == 1

    def test_uses_acknowledged_by_when_no_handler(self):
        """测试无handler_id时使用acknowledged_by"""
        from app.services.alert_efficiency_service import calculate_handler_metrics

        mock_db = MagicMock()
        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {"WARNING": 8}

        mock_user = MagicMock()
        mock_user.username = "李四"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_alert = MagicMock()
        mock_alert.handler_id = None
        mock_alert.acknowledged_by = 2
        mock_alert.status = "RESOLVED"
        mock_alert.alert_level = "WARNING"
        mock_alert.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert.acknowledged_at = datetime.now()
        mock_alert.is_escalated = False

        result = calculate_handler_metrics([mock_alert], mock_db, mock_engine)

        assert "李四" in result


class TestCalculateTypeMetrics:
    """测试 calculate_type_metrics 函数"""

    def test_groups_by_rule_type(self):
        """测试按规则类型分组"""
        from app.services.alert_efficiency_service import calculate_type_metrics

        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {"WARNING": 8}

        mock_rule = MagicMock()
        mock_rule.rule_type = "PROGRESS_DELAY"

        mock_alert = MagicMock()
        mock_alert.rule = mock_rule
        mock_alert.status = "RESOLVED"
        mock_alert.alert_level = "WARNING"
        mock_alert.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert.acknowledged_at = datetime.now()
        mock_alert.is_escalated = False

        result = calculate_type_metrics([mock_alert], mock_engine)

        assert "PROGRESS_DELAY" in result
        assert result["PROGRESS_DELAY"]["total"] == 1

    def test_handles_unknown_rule_type(self):
        """测试处理未知规则类型"""
        from app.services.alert_efficiency_service import calculate_type_metrics

        mock_engine = MagicMock()
        mock_engine.RESPONSE_TIMEOUT = {}

        mock_alert = MagicMock()
        mock_alert.rule = None
        mock_alert.status = "PENDING"
        mock_alert.is_escalated = False

        result = calculate_type_metrics([mock_alert], mock_engine)

        assert "UNKNOWN" in result


class TestGenerateRankings:
    """测试 generate_rankings 函数"""

    def test_returns_empty_rankings_when_insufficient_data(self):
        """测试数据不足时返回空排行"""
        from app.services.alert_efficiency_service import generate_rankings

        project_metrics = {
            "项目A": {"project_id": 1, "total": 3, "efficiency_score": 80},  # 少于5个
        }
        handler_metrics = {
            "张三": {"user_id": 1, "total": 2, "efficiency_score": 90},  # 少于5个
        }

        result = generate_rankings(project_metrics, handler_metrics)

        assert result["best_projects"] == []
        assert result["worst_projects"] == []
        assert result["best_handlers"] == []
        assert result["worst_handlers"] == []

    def test_returns_top_5_best_and_worst(self):
        """测试返回前5名最佳和最差"""
        from app.services.alert_efficiency_service import generate_rankings

        project_metrics = {}
        for i in range(10):
            project_metrics[f"项目{i}"] = {
                "project_id": i,
                "total": 10,
                "efficiency_score": i * 10,
                "processing_rate": 0.8,
                "timely_processing_rate": 0.7,
            }

        handler_metrics = {}
        for i in range(10):
            handler_metrics[f"用户{i}"] = {
                "user_id": i,
                "total": 10,
                "efficiency_score": i * 10,
                "processing_rate": 0.8,
                "timely_processing_rate": 0.7,
            }

        result = generate_rankings(project_metrics, handler_metrics)

        assert len(result["best_projects"]) == 5
        assert len(result["worst_projects"]) == 5
        assert len(result["best_handlers"]) == 5
        assert len(result["worst_handlers"]) == 5

        # 最佳项目应该是效率得分最高的
        assert result["best_projects"][0]["efficiency_score"] == 90
        # 最差项目应该是效率得分最低的
        assert result["worst_projects"][0]["efficiency_score"] == 0

    def test_filters_by_minimum_alert_count(self):
        """测试按最小预警数筛选"""
        from app.services.alert_efficiency_service import generate_rankings

        project_metrics = {
            "项目A": {"project_id": 1, "total": 10, "efficiency_score": 90, "processing_rate": 0.9, "timely_processing_rate": 0.85},
            "项目B": {"project_id": 2, "total": 4, "efficiency_score": 95, "processing_rate": 0.95, "timely_processing_rate": 0.9},  # 少于5个
        }
        handler_metrics = {}

        result = generate_rankings(project_metrics, handler_metrics)

        # 只有项目A满足条件
        assert len(result["best_projects"]) == 1
        assert result["best_projects"][0]["project_name"] == "项目A"
