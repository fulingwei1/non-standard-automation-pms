# -*- coding: utf-8 -*-
"""
进度预测服务单元测试
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.schedule_prediction_service import SchedulePredictionService
from app.models.project.schedule_prediction import (
    ProjectSchedulePrediction,
    CatchUpSolution,
    ScheduleAlert,
)


class TestSchedulePredictionService:
    """进度预测服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query.return_value = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return SchedulePredictionService(mock_db)

    def test_extract_features(self, service):
        """测试特征提取"""
        features = service._extract_features(
            project_id=1,
            current_progress=45.5,
            planned_progress=60.0,
            remaining_days=30,
            team_size=5,
            project_data={"days_elapsed": 40, "complexity": "high"},
        )

        assert features["current_progress"] == 45.5
        assert features["planned_progress"] == 60.0
        assert features["progress_deviation"] == -14.5
        assert features["remaining_days"] == 30
        assert features["remaining_progress"] == 54.5
        assert features["team_size"] == 5
        assert features["complexity"] == "high"
        assert "avg_daily_progress" in features
        assert "required_daily_progress" in features
        assert "velocity_ratio" in features

    def test_predict_linear_on_track(self, service):
        """测试线性预测 - 进度正常"""
        features = {
            "velocity_ratio": 1.2,  # 速度快于计划
            "remaining_days": 30,
        }

        prediction = service._predict_linear(features)

        assert prediction["delay_days"] == 0
        assert prediction["confidence"] == 0.8
        assert isinstance(prediction["predicted_date"], date)

    def test_predict_linear_delayed(self, service):
        """测试线性预测 - 进度延迟"""
        features = {
            "velocity_ratio": 0.6,  # 速度低于计划
            "remaining_days": 30,
        }

        prediction = service._predict_linear(features)

        assert prediction["delay_days"] > 0
        assert prediction["confidence"] == 0.7
        assert isinstance(prediction["predicted_date"], date)

    def test_assess_risk_level(self, service):
        """测试风险等级评估"""
        assert service._assess_risk_level(-5) == "low"  # 提前完成
        assert service._assess_risk_level(0) == "low"
        assert service._assess_risk_level(3) == "low"
        assert service._assess_risk_level(7) == "medium"
        assert service._assess_risk_level(14) == "high"
        assert service._assess_risk_level(20) == "critical"

    @patch.object(SchedulePredictionService, "_predict_with_ai")
    def test_predict_completion_date_with_ai(
        self, mock_predict_ai, service, mock_db
    ):
        """测试使用AI预测完成日期"""
        # 模拟AI预测结果
        mock_predict_ai.return_value = {
            "predicted_date": date.today() + timedelta(days=45),
            "delay_days": 15,
            "confidence": 0.85,
            "details": {
                "risk_factors": ["进度偏差大"],
                "recommendations": ["增加人力"],
            },
        }

        # 模拟数据库操作
        mock_prediction_record = MagicMock()
        mock_prediction_record.id = 1
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        result = service.predict_completion_date(
            project_id=1,
            current_progress=45.5,
            planned_progress=60.0,
            remaining_days=30,
            team_size=5,
            use_ai=True,
        )

        assert result["project_id"] == 1
        assert "prediction" in result
        assert result["prediction"]["delay_days"] == 15
        assert result["prediction"]["confidence"] == 0.85
        assert result["prediction"]["risk_level"] == "high"
        mock_predict_ai.assert_called_once()

    def test_generate_default_solutions(self, service):
        """测试生成默认赶工方案"""
        solutions = service._generate_default_solutions(
            delay_days=15, project_data=None
        )

        assert len(solutions) >= 3
        assert all("name" in sol for sol in solutions)
        assert all("type" in sol for sol in solutions)
        assert all("actions" in sol for sol in solutions)
        assert all("estimated_catch_up" in sol for sol in solutions)
        assert all("additional_cost" in sol for sol in solutions)
        assert all("risk" in sol for sol in solutions)
        assert all("success_rate" in sol for sol in solutions)

        # 验证方案类型
        types = [sol["type"] for sol in solutions]
        assert "overtime" in types
        assert "process" in types
        assert "manpower" in types

    def test_create_alert(self, service, mock_db):
        """测试创建预警"""
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        with patch("app.services.schedule_prediction_service.ScheduleAlert") as MockAlert:
            MockAlert.return_value = mock_alert

            alert = service.create_alert(
                project_id=1,
                prediction_id=1,
                alert_type="delay_warning",
                severity="high",
                title="延期预警",
                message="项目预计延期15天",
                notify_users=[1, 2, 3],
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_check_and_create_alerts_delay(self, service, mock_db):
        """测试检查并创建延期预警"""
        with patch.object(service, "create_alert") as mock_create:
            mock_create.return_value = MagicMock()

            alerts = service.check_and_create_alerts(
                project_id=1,
                prediction_id=1,
                delay_days=15,
                progress_deviation=-5.0,
            )

            # 应该创建延期预警
            assert mock_create.call_count >= 1
            call_args = mock_create.call_args_list[0]
            assert call_args[1]["alert_type"] == "delay_warning"
            assert call_args[1]["severity"] == "high"

    def test_check_and_create_alerts_deviation(self, service, mock_db):
        """测试检查并创建进度偏差预警"""
        with patch.object(service, "create_alert") as mock_create:
            mock_create.return_value = MagicMock()

            alerts = service.check_and_create_alerts(
                project_id=1,
                prediction_id=1,
                delay_days=2,  # 不触发延期预警
                progress_deviation=-15.0,  # 触发偏差预警
            )

            # 应该创建偏差预警
            assert mock_create.call_count >= 1
            call_args = mock_create.call_args_list[0]
            assert call_args[1]["alert_type"] == "velocity_drop"

    def test_parse_ai_prediction_valid_json(self, service):
        """测试解析有效的AI响应"""
        ai_response = """
        {
            "delay_days": 10,
            "confidence": 0.85,
            "risk_factors": ["进度慢"],
            "recommendations": ["加班"]
        }
        """

        features = {"remaining_days": 30}
        result = service._parse_ai_prediction(ai_response, features)

        assert result["delay_days"] == 10
        assert result["confidence"] == 0.85
        assert isinstance(result["predicted_date"], date)
        assert "details" in result

    def test_parse_ai_prediction_invalid_json(self, service):
        """测试解析无效的AI响应（应降级到线性预测）"""
        ai_response = "This is not a valid JSON response"

        features = {
            "remaining_days": 30,
            "velocity_ratio": 0.8,
        }

        with patch.object(service, "_predict_linear") as mock_linear:
            mock_linear.return_value = {
                "predicted_date": date.today(),
                "delay_days": 5,
                "confidence": 0.7,
            }

            result = service._parse_ai_prediction(ai_response, features)

            # 应该调用线性预测作为降级
            mock_linear.assert_called_once()

    def test_get_risk_overview(self, service, mock_db):
        """测试获取风险概览"""
        # 模拟预测记录
        mock_predictions = [
            MagicMock(
                project_id=1,
                risk_level="high",
                delay_days=15,
                predicted_completion_date=date.today(),
            ),
            MagicMock(
                project_id=2,
                risk_level="low",
                delay_days=0,
                predicted_completion_date=date.today(),
            ),
            MagicMock(
                project_id=3,
                risk_level="critical",
                delay_days=25,
                predicted_completion_date=date.today(),
            ),
        ]

        with patch.object(mock_db, "query") as mock_query:
            mock_query.return_value.join.return_value.all.return_value = (
                mock_predictions
            )

            overview = service.get_risk_overview()

            assert overview["total_projects"] == 3
            assert overview["at_risk"] >= 2  # high + critical
            assert overview["critical"] == 1
            assert len(overview["projects"]) >= 2  # high和critical项目


class TestSchedulePredictionIntegration:
    """进度预测集成测试"""

    def test_full_prediction_workflow(self, mock_db):
        """测试完整预测工作流"""
        service = SchedulePredictionService(mock_db)

        # 模拟数据库操作
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        def mock_refresh(obj):
            if isinstance(obj, ProjectSchedulePrediction):
                obj.id = 1

        mock_db.refresh.side_effect = mock_refresh

        # 执行预测（使用线性模式以避免AI调用）
        with patch.object(service, "_get_similar_projects_stats") as mock_stats:
            mock_stats.return_value = {
                "avg_duration": 90,
                "delay_rate": 0.3,
                "avg_delay": 10,
            }

            result = service.predict_completion_date(
                project_id=1,
                current_progress=45.5,
                planned_progress=60.0,
                remaining_days=30,
                team_size=5,
                use_ai=False,  # 使用线性预测
            )

            # 验证结果
            assert "prediction_id" in result
            assert result["project_id"] == 1
            assert "prediction" in result
            assert "features" in result

            # 验证数据库操作
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
