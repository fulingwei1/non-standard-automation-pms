# -*- coding: utf-8 -*-
"""
Tests for status_transition_service
Covers: app/services/status_transition_service.py
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.status_transition_service import StatusTransitionService
from app.models.project import Project, ProjectStatusLog
from app.models.sales import Contract


@pytest.fixture
def status_transition_service(db_session: Session):
    """Create status_transition_service instance."""
    return StatusTransitionService(db_session)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        stage="S2",
        status="ST05",
        health="H1"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestStatusTransitionService:
    """Test suite for StatusTransitionService."""

    def test_init(self, db_session: Session):
        """Test service initialization."""
        service = StatusTransitionService(db_session)
        assert service.db is db_session
        # 验证 handler 已初始化
        assert service.contract_handler is not None
        assert service.material_handler is not None
        assert service.acceptance_handler is not None
        assert service.ecn_handler is not None

    # === 合同相关事件测试 ===

    def test_handle_contract_signed_not_found(self, status_transition_service):
        """测试处理合同签订 - 合同不存在"""
        with patch.object(status_transition_service.contract_handler, 'handle_contract_signed') as mock_handler:
            mock_handler.return_value = None
            result = status_transition_service.handle_contract_signed(99999)
            assert result is None
            mock_handler.assert_called_once()

    def test_handle_contract_signed_success(self, status_transition_service, test_project):
        """测试处理合同签订 - 成功场景"""
        with patch.object(status_transition_service.contract_handler, 'handle_contract_signed') as mock_handler:
            mock_handler.return_value = test_project
            result = status_transition_service.handle_contract_signed(1, auto_create_project=True)
            assert result is not None
            assert result == test_project
            mock_handler.assert_called_once_with(
                contract_id=1,
                auto_create_project=True,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_contract_signed_without_auto_create(self, status_transition_service, test_project):
        """测试处理合同签订 - 不自动创建项目"""
        with patch.object(status_transition_service.contract_handler, 'handle_contract_signed') as mock_handler:
            mock_handler.return_value = test_project
            result = status_transition_service.handle_contract_signed(1, auto_create_project=False)
            assert result is not None
            mock_handler.assert_called_once_with(
                contract_id=1,
                auto_create_project=False,
                log_status_change=status_transition_service._log_status_change
            )

    # === BOM和物料相关事件测试 ===

    def test_handle_bom_published_success(self, status_transition_service, test_project):
        """测试处理BOM发布 - 成功场景"""
        with patch.object(status_transition_service.material_handler, 'handle_bom_published') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_bom_published(test_project.id)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=None,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_bom_published_with_machine_id(self, status_transition_service, test_project):
        """测试处理BOM发布 - 带设备ID"""
        with patch.object(status_transition_service.material_handler, 'handle_bom_published') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_bom_published(test_project.id, machine_id=1)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=1,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_material_shortage_success(self, status_transition_service, test_project):
        """测试处理物料缺货 - 成功场景"""
        with patch.object(status_transition_service.material_handler, 'handle_material_shortage') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_material_shortage(test_project.id, is_critical=True)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                is_critical=True,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_material_shortage_non_critical(self, status_transition_service, test_project):
        """测试处理物料缺货 - 非关键物料"""
        with patch.object(status_transition_service.material_handler, 'handle_material_shortage') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_material_shortage(test_project.id, is_critical=False)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                is_critical=False,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_material_ready_success(self, status_transition_service, test_project):
        """测试处理物料齐套 - 成功场景"""
        with patch.object(status_transition_service.material_handler, 'handle_material_ready') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_material_ready(test_project.id)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                log_status_change=status_transition_service._log_status_change
            )

    # === 验收相关事件测试 ===

    def test_handle_fat_passed_success(self, status_transition_service, test_project):
        """测试处理FAT通过 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_fat_passed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_fat_passed(test_project.id)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=None,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_fat_passed_with_machine_id(self, status_transition_service, test_project):
        """测试处理FAT通过 - 带设备ID"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_fat_passed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_fat_passed(test_project.id, machine_id=1)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=1,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_fat_failed_success(self, status_transition_service, test_project):
        """测试处理FAT失败 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_fat_failed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_fat_failed(test_project.id)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=None,
                issues=None,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_fat_failed_with_issues(self, status_transition_service, test_project):
        """测试处理FAT失败 - 带问题列表"""
        issues = ["问题1", "问题2"]
        with patch.object(status_transition_service.acceptance_handler, 'handle_fat_failed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_fat_failed(test_project.id, machine_id=1, issues=issues)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=1,
                issues=issues,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_sat_passed_success(self, status_transition_service, test_project):
        """测试处理SAT通过 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_sat_passed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_sat_passed(test_project.id)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=None,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_sat_failed_success(self, status_transition_service, test_project):
        """测试处理SAT失败 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_sat_failed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_sat_failed(test_project.id)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                machine_id=None,
                issues=None,
                log_status_change=status_transition_service._log_status_change
            )

    def test_handle_final_acceptance_passed_success(self, status_transition_service, test_project):
        """测试处理终验收通过 - 成功场景"""
        with patch.object(status_transition_service.acceptance_handler, 'handle_final_acceptance_passed') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_final_acceptance_passed(test_project.id)
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                log_status_change=status_transition_service._log_status_change
            )

    # === ECN相关事件测试 ===

    def test_handle_ecn_schedule_impact_success(self, status_transition_service, test_project):
        """测试处理ECN影响交期 - 成功场景"""
        with patch.object(status_transition_service.ecn_handler, 'handle_ecn_schedule_impact') as mock_handler:
            mock_handler.return_value = True
            result = status_transition_service.handle_ecn_schedule_impact(
                project_id=test_project.id,
                ecn_id=1,
                impact_days=5
            )
            assert result is True
            mock_handler.assert_called_once_with(
                project_id=test_project.id,
                ecn_id=1,
                impact_days=5,
                log_status_change=status_transition_service._log_status_change
            )

    # === 阶段自动流转测试 ===

    def test_check_auto_stage_transition_project_not_found(self, status_transition_service):
        """测试检查阶段自动流转 - 项目不存在"""
        result = status_transition_service.check_auto_stage_transition(99999)
        assert result["can_advance"] is False
        assert result["message"] == "项目不存在"
        assert result["current_stage"] is None
        assert result["target_stage"] is None

    def test_check_auto_stage_transition_s3(self, status_transition_service, db_session):
        """测试检查阶段自动流转 - S3阶段"""
        project = Project(
            project_code="PJ002",
            project_name="测试项目2",
            stage="S3",
            status="ST08"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        with patch('app.services.stage_transition_checks.check_s3_to_s4_transition') as mock_check:
            mock_check.return_value = (True, "S4", [])
            result = status_transition_service.check_auto_stage_transition(project.id, auto_advance=False)
            assert result["can_advance"] is True
            assert result["target_stage"] == "S4"
            assert result["current_stage"] == "S3"

    def test_check_auto_stage_transition_s4(self, status_transition_service, db_session):
        """测试检查阶段自动流转 - S4阶段"""
        project = Project(
            project_code="PJ003",
            project_name="测试项目3",
            stage="S4",
            status="ST10"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        with patch('app.services.stage_transition_checks.check_s4_to_s5_transition') as mock_check:
            mock_check.return_value = (True, "S5", [])
            result = status_transition_service.check_auto_stage_transition(project.id, auto_advance=False)
            assert result["can_advance"] is True
            assert result["target_stage"] == "S5"

    def test_check_auto_stage_transition_s5(self, status_transition_service, db_session):
        """测试检查阶段自动流转 - S5阶段"""
        project = Project(
            project_code="PJ004",
            project_name="测试项目4",
            stage="S5",
            status="ST12"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        with patch('app.services.stage_transition_checks.check_s5_to_s6_transition') as mock_check:
            mock_check.return_value = (True, "S6", [])
            result = status_transition_service.check_auto_stage_transition(project.id, auto_advance=False)
            assert result["can_advance"] is True
            assert result["target_stage"] == "S6"

    def test_check_auto_stage_transition_s7(self, status_transition_service, db_session):
        """测试检查阶段自动流转 - S7阶段"""
        project = Project(
            project_code="PJ005",
            project_name="测试项目5",
            stage="S7",
            status="ST20"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        with patch('app.services.stage_transition_checks.check_s7_to_s8_transition') as mock_check:
            mock_check.return_value = (True, "S8", [])
            result = status_transition_service.check_auto_stage_transition(project.id, auto_advance=False)
            assert result["can_advance"] is True
            assert result["target_stage"] == "S8"

    def test_check_auto_stage_transition_s8(self, status_transition_service, db_session):
        """测试检查阶段自动流转 - S8阶段"""
        project = Project(
            project_code="PJ006",
            project_name="测试项目6",
            stage="S8",
            status="ST25"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        with patch('app.services.stage_transition_checks.check_s8_to_s9_transition') as mock_check:
            mock_check.return_value = (True, "S9", [])
            result = status_transition_service.check_auto_stage_transition(project.id, auto_advance=False)
            assert result["can_advance"] is True
            assert result["target_stage"] == "S9"

    def test_check_auto_stage_transition_with_auto_advance(self, status_transition_service, db_session):
        """测试检查阶段自动流转 - 自动推进"""
        project = Project(
            project_code="PJ007",
            project_name="测试项目7",
            stage="S3",
            status="ST08"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        with patch('app.services.stage_transition_checks.check_s3_to_s4_transition') as mock_check, \
             patch('app.services.stage_transition_checks.execute_stage_transition') as mock_execute:
            mock_check.return_value = (True, "S4", [])
            mock_execute.return_value = (True, {
                "can_advance": True,
                "auto_advanced": True,
                "current_stage": "S3",
                "target_stage": "S4",
                "message": "已自动推进至 S4 阶段"
            })
            
            result = status_transition_service.check_auto_stage_transition(project.id, auto_advance=True)
            assert result["can_advance"] is True
            assert result["target_stage"] == "S4"
            mock_execute.assert_called_once()

    def test_check_auto_stage_transition_no_transition(self, status_transition_service, db_session):
        """测试检查阶段自动流转 - 不满足流转条件"""
        project = Project(
            project_code="PJ008",
            project_name="测试项目8",
            stage="S1",
            status="ST01"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        result = status_transition_service.check_auto_stage_transition(project.id, auto_advance=False)
        assert result["can_advance"] is False
        assert result["message"] == "不满足自动推进条件"
        assert result["current_stage"] == "S1"

    # === 内部方法测试 ===

    def test_log_status_change(self, status_transition_service, test_project):
        """测试记录状态变更"""
        status_transition_service._log_status_change(
            project_id=test_project.id,
            old_stage="S2",
            new_stage="S3",
            old_status="ST05",
            new_status="ST08",
            old_health="H1",
            new_health="H1",
            change_type="MANUAL",
            change_reason="手动推进",
            changed_by=1
        )
        status_transition_service.db.commit()  # 提交事务以保存日志
        
        # 验证状态日志已创建
        logs = status_transition_service.db.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).all()
        
        assert len(logs) > 0
        log = logs[-1]
        assert log.project_id == test_project.id
        assert log.old_stage == "S2"
        assert log.new_stage == "S3"
        assert log.old_status == "ST05"
        assert log.new_status == "ST08"
        assert log.change_type == "MANUAL"
        assert log.change_reason == "手动推进"

    def test_log_status_change_minimal(self, status_transition_service, test_project):
        """测试记录状态变更 - 最小参数"""
        status_transition_service._log_status_change(
            project_id=test_project.id
        )
        status_transition_service.db.commit()  # 提交事务以保存日志
        
        logs = status_transition_service.db.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).all()
        
        assert len(logs) > 0
        log = logs[-1]
        assert log.project_id == test_project.id
        assert log.change_type == "AUTO_TRANSITION"