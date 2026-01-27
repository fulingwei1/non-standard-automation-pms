# -*- coding: utf-8 -*-
"""
状态处理器服务单元测试

测试覆盖:
- AcceptanceStatusHandler: 验收事件处理
- ContractStatusHandler: 合同状态处理
- MaterialStatusHandler: 物料状态处理
- ECNStatusHandler: ECN变更处理
- MilestoneStatusHandler: 里程碑状态处理
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.project import Project


class TestAcceptanceStatusHandler:
    """测试验收状态处理器"""

    @pytest.fixture
    def handler(self, db_session):
        """创建验收状态处理器"""
        from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler
        return AcceptanceStatusHandler(db_session)

    @pytest.fixture
    def test_project(self, db_session):
        """创建测试项目"""
        project = Project(
            project_code="PJ-STATUS-TEST",
            project_name="状态测试项目",
            stage="S7",
            status="ST20",
            health="H1",
        )
        db_session.add(project)
        db_session.flush()
        return project

    # FAT 通过测试
    def test_handle_fat_passed_success(self, handler, test_project, db_session):
        """测试FAT验收通过 - 成功"""
        # 设置项目在S7阶段
        test_project.stage = "S7"
        test_project.status = "ST20"
        db_session.flush()

        result = handler.handle_fat_passed(test_project.id)

        assert result is True

        # 刷新项目
        db_session.refresh(test_project)
        assert test_project.stage == "S8"
        assert test_project.status == "ST23"

    def test_handle_fat_passed_project_not_found(self, handler):
        """测试FAT验收通过 - 项目不存在"""
        result = handler.handle_fat_passed(99999)
        assert result is False

    def test_handle_fat_passed_wrong_stage(self, handler, test_project, db_session):
        """测试FAT验收通过 - 阶段不正确"""
        test_project.stage = "S5"  # 不是S7
        db_session.flush()

        result = handler.handle_fat_passed(test_project.id)
        assert result is False

    def test_handle_fat_passed_health_recovery(self, handler, test_project, db_session):
        """测试FAT验收通过 - 健康度恢复"""
        test_project.stage = "S7"
        test_project.health = "H2"  # 黄色预警
        db_session.flush()

        result = handler.handle_fat_passed(test_project.id)

        assert result is True
        db_session.refresh(test_project)
        assert test_project.health == "H1"  # 恢复为绿色

    # FAT 失败测试
    def test_handle_fat_failed_success(self, handler, test_project, db_session):
        """测试FAT验收不通过 - 成功"""
        test_project.stage = "S7"
        db_session.flush()

        result = handler.handle_fat_failed(test_project.id)

        assert result is True
        db_session.refresh(test_project)
        assert test_project.status == "ST22"
        assert test_project.health == "H2"

    def test_handle_fat_failed_with_issues(self, handler, test_project, db_session):
        """测试FAT验收不通过 - 带整改项"""
        test_project.stage = "S7"
        test_project.description = None
        db_session.flush()

        issues = ["问题1", "问题2", "问题3"]
        result = handler.handle_fat_failed(test_project.id, issues=issues)

        assert result is True
        db_session.refresh(test_project)
        assert "FAT验收不通过" in test_project.description
        assert "问题1" in test_project.description

    def test_handle_fat_failed_append_to_description(self, handler, test_project, db_session):
        """测试FAT验收不通过 - 追加到现有描述"""
        test_project.stage = "S7"
        test_project.description = "原有描述"
        db_session.flush()

        issues = ["新问题"]
        result = handler.handle_fat_failed(test_project.id, issues=issues)

        assert result is True
        db_session.refresh(test_project)
        assert "原有描述" in test_project.description
        assert "新问题" in test_project.description

    def test_handle_fat_failed_project_not_found(self, handler):
        """测试FAT验收不通过 - 项目不存在"""
        result = handler.handle_fat_failed(99999)
        assert result is False

    # SAT 通过测试
    def test_handle_sat_passed_success(self, handler, test_project, db_session):
        """测试SAT验收通过 - 成功"""
        test_project.stage = "S8"
        test_project.status = "ST24"
        db_session.flush()

        result = handler.handle_sat_passed(test_project.id)

        assert result is True
        db_session.refresh(test_project)
        assert test_project.status == "ST27"

    def test_handle_sat_passed_wrong_stage(self, handler, test_project, db_session):
        """测试SAT验收通过 - 阶段不正确"""
        test_project.stage = "S7"  # 不是S8
        db_session.flush()

        result = handler.handle_sat_passed(test_project.id)
        assert result is False

    def test_handle_sat_passed_project_not_found(self, handler):
        """测试SAT验收通过 - 项目不存在"""
        result = handler.handle_sat_passed(99999)
        assert result is False

    # SAT 失败测试
    def test_handle_sat_failed_success(self, handler, test_project, db_session):
        """测试SAT验收不通过 - 成功"""
        test_project.stage = "S8"
        db_session.flush()

        result = handler.handle_sat_failed(test_project.id)

        assert result is True
        db_session.refresh(test_project)
        assert test_project.status == "ST26"
        assert test_project.health == "H2"

    def test_handle_sat_failed_with_issues(self, handler, test_project, db_session):
        """测试SAT验收不通过 - 带整改项"""
        test_project.stage = "S8"
        test_project.description = None
        db_session.flush()

        issues = ["SAT问题1", "SAT问题2"]
        result = handler.handle_sat_failed(test_project.id, issues=issues)

        assert result is True
        db_session.refresh(test_project)
        assert "SAT验收不通过" in test_project.description

    def test_handle_sat_failed_project_not_found(self, handler):
        """测试SAT验收不通过 - 项目不存在"""
        result = handler.handle_sat_failed(99999)
        assert result is False

    # 终验收测试
    def test_handle_final_acceptance_passed_success(self, handler, test_project, db_session):
        """测试终验收通过 - 成功"""
        test_project.stage = "S8"
        db_session.flush()

        result = handler.handle_final_acceptance_passed(test_project.id)
        assert result is True

    def test_handle_final_acceptance_passed_wrong_stage(self, handler, test_project, db_session):
        """测试终验收通过 - 阶段不正确"""
        test_project.stage = "S7"  # 不是S8
        db_session.flush()

        result = handler.handle_final_acceptance_passed(test_project.id)
        assert result is False

    def test_handle_final_acceptance_passed_project_not_found(self, handler):
        """测试终验收通过 - 项目不存在"""
        result = handler.handle_final_acceptance_passed(99999)
        assert result is False

    # 状态变更日志测试
    def test_log_status_change_creates_log(self, handler, test_project, db_session):
        """测试状态变更日志创建"""
        handler._log_status_change(
            test_project.id,
            old_stage="S7",
            new_stage="S8",
            old_status="ST20",
            new_status="ST23",
            change_type="FAT_PASSED",
            change_reason="测试原因",
        )

        # 验证日志已添加到会话
        # db_session.add 应该被调用

    def test_log_status_change_with_callback(self, handler, test_project):
        """测试状态变更日志带回调"""
        callback = MagicMock()

        handler._log_status_change(
            test_project.id,
            old_stage="S7",
            new_stage="S8",
            change_type="TEST",
            log_status_change=callback,
        )

        callback.assert_called_once()


class TestStatusHandlersModule:
    """测试状态处理器模块"""

    def test_import_module(self):
        """测试导入模块"""
        from app.services.status_handlers import (
            get_acceptance_handler,
            get_contract_handler,
            get_ecn_handler,
            get_material_handler,
            get_milestone_handler,
            register_all_handlers,
        )

        assert get_acceptance_handler is not None
        assert get_contract_handler is not None
        assert get_ecn_handler is not None
        assert get_material_handler is not None
        assert get_milestone_handler is not None
        assert register_all_handlers is not None

    def test_get_acceptance_handler(self):
        """测试获取验收处理器类"""
        from app.services.status_handlers import get_acceptance_handler

        handler_class = get_acceptance_handler()
        assert handler_class is not None
        assert handler_class.__name__ == "AcceptanceStatusHandler"

    def test_get_contract_handler(self):
        """测试获取合同处理器类"""
        from app.services.status_handlers import get_contract_handler

        handler_class = get_contract_handler()
        assert handler_class is not None
        assert handler_class.__name__ == "ContractStatusHandler"

    def test_get_ecn_handler(self):
        """测试获取ECN处理器类"""
        from app.services.status_handlers import get_ecn_handler

        handler_class = get_ecn_handler()
        assert handler_class is not None
        assert handler_class.__name__ == "ECNStatusHandler"

    def test_get_material_handler(self):
        """测试获取物料处理器类"""
        from app.services.status_handlers import get_material_handler

        handler_class = get_material_handler()
        assert handler_class is not None
        assert handler_class.__name__ == "MaterialStatusHandler"

    def test_get_milestone_handler(self):
        """测试获取里程碑处理器类"""
        from app.services.status_handlers import get_milestone_handler

        handler_class = get_milestone_handler()
        assert handler_class is not None
        assert handler_class.__name__ == "MilestoneStatusHandler"

    def test_register_all_handlers(self):
        """测试注册所有处理器"""
        from app.services.status_handlers import register_all_handlers

        # 不应抛出异常
        register_all_handlers()
