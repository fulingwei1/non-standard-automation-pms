# -*- coding: utf-8 -*-
"""
部门经理评价服务单元测试
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestManagerEvaluationServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, db_session):
        """测试使用数据库会话初始化"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)
        assert service.db == db_session


class TestCheckManagerPermission:
    """测试检查部门经理权限"""

    def test_manager_not_found(self, db_session):
        """测试经理不存在"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)
        result = service.check_manager_permission(99999, 1)

        assert result is False

    def test_not_department_manager(self, db_session):
        """测试非部门经理"""
        from app.services.manager_evaluation_service import ManagerEvaluationService
        from app.models.user import User

        user = User(
        username="test_user",
        employee_id=1
        )
        db_session.add(user)
        db_session.flush()

        service = ManagerEvaluationService(db_session)
        result = service.check_manager_permission(user.id, 1)

        assert result is False


class TestCalculateLevel:
    """测试计算等级"""

    def test_level_s(self, db_session):
        """测试S等级（>=85分）"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        assert service._calculate_level(Decimal("90")) == "S"
        assert service._calculate_level(Decimal("85")) == "S"
        assert service._calculate_level(Decimal("100")) == "S"

    def test_level_a(self, db_session):
        """测试A等级（70-84分）"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        assert service._calculate_level(Decimal("70")) == "A"
        assert service._calculate_level(Decimal("75")) == "A"
        assert service._calculate_level(Decimal("84")) == "A"

    def test_level_b(self, db_session):
        """测试B等级（60-69分）"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        assert service._calculate_level(Decimal("60")) == "B"
        assert service._calculate_level(Decimal("65")) == "B"
        assert service._calculate_level(Decimal("69")) == "B"

    def test_level_c(self, db_session):
        """测试C等级（40-59分）"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        assert service._calculate_level(Decimal("40")) == "C"
        assert service._calculate_level(Decimal("50")) == "C"
        assert service._calculate_level(Decimal("59")) == "C"

    def test_level_d(self, db_session):
        """测试D等级（<40分）"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        assert service._calculate_level(Decimal("0")) == "D"
        assert service._calculate_level(Decimal("20")) == "D"
        assert service._calculate_level(Decimal("39")) == "D"


class TestAdjustPerformance:
    """测试调整绩效"""

    def test_empty_adjustment_reason(self, db_session):
        """测试空调整理由"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.adjust_performance(
            result_id=1,
            manager_id=1,
            adjustment_reason=""
            )

            assert "调整理由不能为空" in str(exc_info.value)

    def test_short_adjustment_reason(self, db_session):
        """测试调整理由过短"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.adjust_performance(
            result_id=1,
            manager_id=1,
            adjustment_reason="太短了"
            )

            assert "至少需要10个字符" in str(exc_info.value)

    def test_result_not_found(self, db_session):
        """测试绩效结果不存在"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.adjust_performance(
            result_id=99999,
            manager_id=1,
            adjustment_reason="这是一个有效的调整理由说明"
            )

            assert "绩效结果不存在" in str(exc_info.value)


class TestGetAdjustmentHistory:
    """测试获取调整历史"""

    def test_empty_history(self, db_session):
        """测试空调整历史"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)
        result = service.get_adjustment_history(99999)

        assert result == []


class TestGetEngineersForEvaluation:
    """测试获取可评价的工程师列表"""

    def test_no_engineers(self, db_session):
        """测试没有可评价的工程师"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)
        result = service.get_engineers_for_evaluation(99999)

        assert result == []


class TestGetManagerEvaluationTasks:
    """测试获取部门经理需要评价的任务"""

    def test_manager_not_found(self, db_session):
        """测试经理不存在"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)
        result = service.get_manager_evaluation_tasks(99999)

        assert result == []


class TestSubmitEvaluation:
    """测试提交评价"""

    def test_result_not_found(self, db_session):
        """测试绩效结果不存在"""
        from app.services.manager_evaluation_service import ManagerEvaluationService

        service = ManagerEvaluationService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.submit_evaluation(
            result_id=99999,
            manager_id=1,
            overall_comment="评价内容"
            )

            assert "绩效结果不存在" in str(exc_info.value)


            # pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
