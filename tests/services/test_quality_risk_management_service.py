# -*- coding: utf-8 -*-
"""
质量风险管理服务单元测试 (QualityRiskManagementService)
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _make_db():
    """创建模拟的数据库会话"""
    db = MagicMock()
    return db


def _make_detection(**kw):
    """创建模拟的质量风险检测记录"""
    detection = MagicMock()
    defaults = dict(
        id=1,
        project_id=10,
        module_name="电气测试",
        detection_date=date.today(),
        source_type="WORK_LOG",
        risk_signals=["测试时间不足", "反复修改"],
        risk_keywords={"高频": 5, "返工": 3},
        abnormal_patterns=["异常模式1"],
        risk_level="HIGH",
        risk_score=75.5,
        risk_category="进度风险",
        predicted_issues=["可能延期交付"],
        rework_probability=0.65,
        estimated_impact_days=5,
        ai_analysis="基于工作日志分析，发现多个风险信号",
        ai_confidence=0.82,
        analysis_model="gpt-4",
        status="DETECTED",
        created_by=1,
        confirmed_by=None,
        confirmed_at=None,
        resolution_note=None,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(detection, k, v)
    return detection


def _make_recommendation(**kw):
    """创建模拟的测试推荐记录"""
    recommendation = MagicMock()
    defaults = dict(
        id=1,
        project_id=10,
        detection_id=1,
        recommendation_date=date.today(),
        focus_areas=["电气安全测试", "功能验证"],
        priority_modules=["电源模块", "控制模块"],
        risk_modules=["通信模块"],
        test_types=["功能测试", "集成测试"],
        test_scenarios=["正常场景", "异常场景"],
        test_coverage_target=85,
        recommended_testers=["张三", "李四"],
        recommended_days=3,
        priority_level="HIGH",
        ai_reasoning="基于风险分析，推荐优先测试高风险模块",
        risk_summary="高风险项目，需要全面测试",
        status="PENDING",
        created_by=1,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(recommendation, k, v)
    return recommendation


def _make_timesheet(**kw):
    """创建模拟的工作日志记录"""
    timesheet = MagicMock()
    defaults = dict(
        id=1,
        project_id=10,
        user_id=1,
        user_name="测试用户",
        work_date=date.today() - timedelta(days=1),
        task_name="电气设计",
        work_content="完成电气原理图",
        work_result="已完成",
        hours=8.0,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(timesheet, k, v)
    return timesheet


class TestQualityRiskManagementService:
    """测试质量风险管理服务"""

    def test_analyze_work_logs_success(self):
        """测试分析工作日志成功场景"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        # 模拟工作日志查询返回数据
        timesheet = _make_timesheet()
        db.query.return_value.filter.return_value.all.return_value = [timesheet]

        # 模拟AI分析结果
        mock_analysis_result = {
            "risk_signals": ["测试时间不足"],
            "risk_keywords": {"返工": 3},
            "abnormal_patterns": [],
            "risk_level": "MEDIUM",
            "risk_score": 55.0,
            "risk_category": "质量风险",
            "predicted_issues": [],
            "rework_probability": 0.4,
            "estimated_impact_days": 2,
            "ai_analysis": "分析完成",
            "ai_confidence": 0.75,
            "analysis_model": "test-model",
        }

        with patch.object(
            service.analyzer, "analyze_work_logs", return_value=mock_analysis_result
        ):
            result = service.analyze_work_logs(
                project_id=10,
                start_date=None,
                end_date=None,
                module_name=None,
                user_ids=None,
                current_user_id=1,
            )

        assert result is not None
        assert result.project_id == 10
        assert result.risk_level == "MEDIUM"
        db.add.assert_called_once()
        db.commit.assert_called()

    def test_analyze_work_logs_no_logs_raises_error(self):
        """测试分析工作日志无数据时抛出异常"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        # 模拟查询返回空列表
        db.query.return_value.filter.return_value.all.return_value = []

        with pytest.raises(ValueError, match="未找到符合条件的工作日志"):
            service.analyze_work_logs(
                project_id=10,
                start_date=None,
                end_date=None,
                module_name=None,
                user_ids=None,
                current_user_id=1,
            )

    def test_list_detections_basic_filter(self):
        """测试查询检测记录列表（基本过滤）"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        detection = _make_detection()
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            detection
        ]

        result = service.list_detections(project_id=10)

        assert len(result) == 1
        assert result[0].project_id == 10

    def test_list_detections_with_risk_level_filter(self):
        """测试按风险等级过滤查询"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        detection = _make_detection(risk_level="HIGH")
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            detection
        ]

        result = service.list_detections(risk_level="HIGH")

        assert len(result) == 1
        assert result[0].risk_level == "HIGH"

    def test_get_detection_found(self):
        """测试获取检测详情（存在）"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        detection = _make_detection(id=5)
        db.query.return_value.filter.return_value.first.return_value = detection

        result = service.get_detection(5)

        assert result is not None
        assert result.id == 5

    def test_get_detection_not_found(self):
        """测试获取检测详情（不存在）"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_detection(999)

        assert result is None

    def test_update_detection_status(self):
        """测试更新检测状态"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        detection = _make_detection(id=1, status="DETECTED")
        db.query.return_value.filter.return_value.first.return_value = detection

        result = service.update_detection(
            detection_id=1, status="CONFIRMED", current_user_id=1
        )

        assert result is not None
        assert result.status == "CONFIRMED"
        assert result.confirmed_by == 1
        db.commit.assert_called()

    def test_update_detection_not_found(self):
        """测试更新不存在的检测"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        db.query.return_value.filter.return_value.first.return_value = None

        result = service.update_detection(detection_id=999, status="CONFIRMED")

        assert result is None


class TestGenerateTestRecommendation:
    """测试生成测试推荐"""

    def test_generate_recommendation_success(self):
        """测试成功生成测试推荐"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        detection = _make_detection(id=1, project_id=10)
        db.query.return_value.filter.return_value.first.return_value = detection

        mock_recommendation_data = {
            "focus_areas": ["功能测试"],
            "priority_level": "HIGH",
            "test_types": ["单元测试", "集成测试"],
        }

        with patch.object(
            service.recommendation_engine,
            "generate_recommendations",
            return_value=mock_recommendation_data,
        ):
            result = service.generate_test_recommendation(
                detection_id=1, current_user_id=1
            )

        assert result is not None
        db.add.assert_called()
        db.commit.assert_called()

    def test_generate_recommendation_detection_not_found(self):
        """测试检测记录不存在时返回None"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        db.query.return_value.filter.return_value.first.return_value = None

        result = service.generate_test_recommendation(
            detection_id=999, current_user_id=1
        )

        assert result is None


class TestListRecommendations:
    """测试查询推荐列表"""

    def test_list_recommendations_basic(self):
        """测试查询推荐列表基本功能"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        recommendation = _make_recommendation()
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            recommendation
        ]

        result = service.list_recommendations(project_id=10)

        assert len(result) == 1
        assert result[0].project_id == 10

    def test_list_recommendations_with_priority_filter(self):
        """测试按优先级过滤查询"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        recommendation = _make_recommendation(priority_level="HIGH")
        db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            recommendation
        ]

        result = service.list_recommendations(priority_level="HIGH")

        assert len(result) == 1
        assert result[0].priority_level == "HIGH"


class TestUpdateRecommendation:
    """测试更新推荐"""

    def test_update_recommendation_success(self):
        """测试成功更新推荐"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        recommendation = _make_recommendation(id=1, status="PENDING")
        db.query.return_value.filter.return_value.first.return_value = recommendation

        result = service.update_recommendation(1, {"status": "APPROVED"})

        assert result is not None
        db.commit.assert_called()

    def test_update_recommendation_not_found(self):
        """测试更新不存在的推荐"""
        from app.services.quality_risk_management.service import (
            QualityRiskManagementService,
        )

        db = _make_db()
        service = QualityRiskManagementService(db)

        db.query.return_value.filter.return_value.first.return_value = None

        result = service.update_recommendation(999, {"status": "APPROVED"})

        assert result is None