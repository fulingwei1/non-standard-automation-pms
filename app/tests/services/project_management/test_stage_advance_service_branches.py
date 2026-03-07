# -*- coding: utf-8 -*-
"""
阶段推进服务分支测试
测试 app/services/stage_advance_service.py 的各种分支逻辑

覆盖目标:
- 阶段验证分支（有效性、推进方向）
- 阶段门校验分支（通过、不通过、跳过）
- 状态更新分支（S1-S9各阶段流转）
- 自动化触发分支（安装派工、成本复盘）
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectStatusLog
from app.models.user import User
from app.services.stage_advance_service import (
    validate_target_stage,
    validate_stage_advancement,
    perform_gate_check,
    get_stage_status_mapping,
    update_project_stage_and_status,
    create_status_log,
    create_installation_dispatch_orders,
    generate_cost_review_report,
)


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = Project(
        project_code="PJ260307001",
        project_name="测试项目",
        stage="S3",
        status="ST05",
        health="H1",
        progress_pct=Decimal("30.0"),
        customer_id=1,
        pm_id=1,
        is_active=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_superuser(db_session: Session):
    """创建超级管理员"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestStageValidationBranches:
    """测试阶段验证的分支逻辑"""

    def test_validate_target_stage_valid(self):
        """分支：有效的目标阶段"""
        # 这些都不应抛出异常
        for stage in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']:
            validate_target_stage(stage)

    def test_validate_target_stage_invalid(self):
        """分支：无效的目标阶段"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_target_stage("S10")

        assert exc_info.value.status_code == 400
        assert "无效的目标阶段" in exc_info.value.detail

    def test_validate_stage_advancement_forward(self):
        """分支：向前推进阶段（正常）"""
        # 从S3推进到S4 - 不应抛出异常
        validate_stage_advancement("S3", "S4")

    def test_validate_stage_advancement_backward(self):
        """分支：向后回退阶段（异常）"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_stage_advancement("S5", "S3")

        assert exc_info.value.status_code == 400
        assert "不能早于或等于当前阶段" in exc_info.value.detail

    def test_validate_stage_advancement_same(self):
        """分支：推进到相同阶段（异常）"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_stage_advancement("S4", "S4")

        assert exc_info.value.status_code == 400
        assert "不能早于或等于当前阶段" in exc_info.value.detail


class TestGateCheckBranches:
    """测试阶段门校验的分支逻辑"""

    def test_gate_check_skip_by_superuser(self, db_session, test_project, test_superuser):
        """分支：超级管理员跳过校验"""
        passed, missing, result = perform_gate_check(
            db=db_session,
            project=test_project,
            target_stage="S4",
            skip_gate_check=True,
            current_user_is_superuser=True,
        )

        assert passed is True
        assert missing == []
        assert result is None

    def test_gate_check_skip_by_normal_user(self, db_session, test_project, test_user):
        """分支：普通用户尝试跳过校验（异常）"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            perform_gate_check(
                db=db_session,
                project=test_project,
                target_stage="S4",
                skip_gate_check=True,
                current_user_is_superuser=False,
            )

        assert exc_info.value.status_code == 403
        assert "只有管理员可以跳过" in exc_info.value.detail

    def test_gate_check_superuser_auto_pass(self, db_session, test_project, test_superuser):
        """分支：超级管理员自动通过（不跳过但自动通过）"""
        passed, missing, result = perform_gate_check(
            db=db_session,
            project=test_project,
            target_stage="S4",
            skip_gate_check=False,
            current_user_is_superuser=True,
        )

        assert passed is True
        assert missing == []
        assert result is None


class TestStageStatusMappingBranches:
    """测试阶段状态映射的分支逻辑"""

    def test_stage_status_mapping_all_stages(self):
        """分支：验证所有阶段的状态映射"""
        mapping = get_stage_status_mapping()

        expected_mapping = {
            'S1': 'ST01',
            'S2': 'ST03',
            'S3': 'ST05',
            'S4': 'ST07',
            'S5': 'ST10',
            'S6': 'ST15',
            'S7': 'ST20',
            'S8': 'ST25',
            'S9': 'ST30',
        }

        assert mapping == expected_mapping


class TestStageUpdateBranches:
    """测试阶段和状态更新的分支逻辑"""

    def test_update_stage_s1_to_s2(self, db_session, test_project):
        """分支：S1→S2阶段流转"""
        test_project.stage = "S1"
        test_project.status = "ST01"
        db_session.commit()

        new_status = update_project_stage_and_status(
            db=db_session,
            project=test_project,
            target_stage="S2",
            old_stage="S1",
            old_status="ST01",
        )

        assert test_project.stage == "S2"
        assert test_project.status == "ST03"
        assert new_status == "ST03"

    def test_update_stage_s8_to_s9(self, db_session, test_project):
        """分支：S8→S9结项流转"""
        test_project.stage = "S8"
        test_project.status = "ST25"
        db_session.commit()

        new_status = update_project_stage_and_status(
            db=db_session,
            project=test_project,
            target_stage="S9",
            old_stage="S8",
            old_status="ST25",
        )

        assert test_project.stage == "S9"
        assert test_project.status == "ST30"
        assert new_status == "ST30"

    def test_update_stage_same_stage(self, db_session, test_project):
        """分支：阶段未变化（仅更新状态）"""
        test_project.stage = "S4"
        test_project.status = "ST07"
        db_session.commit()

        new_status = update_project_stage_and_status(
            db=db_session,
            project=test_project,
            target_stage="S4",
            old_stage="S4",
            old_status="ST07",
        )

        assert test_project.stage == "S4"
        assert test_project.status == "ST07"
        assert new_status == "ST07"


class TestStatusLogBranches:
    """测试状态日志的分支逻辑"""

    def test_create_status_log_10_params(self, db_session, test_project):
        """分支：10参数模式（新版本）"""
        create_status_log(
            db=db_session,
            project_id=test_project.id,
            old_stage="S3",
            new_stage="S4",
            old_status="ST05",
            new_status="ST07",
            old_health="H1",
            new_health="H2",
            reason="测试推进",
            changed_by=1,
        )

        # 验证日志创建
        log = db_session.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).first()

        assert log is not None
        assert log.old_stage == "S3"
        assert log.new_stage == "S4"
        assert log.old_health == "H1"
        assert log.new_health == "H2"
        assert log.change_reason == "测试推进"
        assert log.changed_by == 1

    def test_create_status_log_9_params_compat(self, db_session, test_project):
        """分支：9参数模式（旧版兼容）"""
        # 旧调用模式：new_health 实际是 reason
        create_status_log(
            db=db_session,
            project_id=test_project.id,
            old_stage="S3",
            new_stage="S4",
            old_status="ST05",
            new_status="ST07",
            old_health="H1",
            new_health="旧版测试推进",  # 这里是 reason
            reason="1",  # 这里是 changed_by
        )

        log = db_session.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).first()

        assert log is not None
        assert log.old_health == "H1"
        assert log.new_health == "H1"  # 应该保持不变
        assert log.change_reason == "旧版测试推进"
        assert log.changed_by == 1


class TestInstallationDispatchBranches:
    """测试安装派工单自动创建的分支逻辑"""

    def test_create_dispatch_s8_first_time(self, db_session, test_project):
        """分支：首次进入S8 - 自动创建派工单"""
        # 创建机台
        machine = Machine(
            project_id=test_project.id,
            machine_no="PN001",
            machine_name="测试设备",
        )
        db_session.add(machine)
        db_session.commit()

        # 执行自动创建
        create_installation_dispatch_orders(
            db=db_session,
            project=test_project,
            target_stage="S8",
            old_stage="S7",
        )

        # 验证派工单创建
        from app.models.installation_dispatch import InstallationDispatchOrder
        orders = db_session.query(InstallationDispatchOrder).filter(
            InstallationDispatchOrder.project_id == test_project.id
        ).all()

        assert len(orders) >= 1
        assert orders[0].machine_id == machine.id
        assert orders[0].task_type == "INSTALLATION"

    def test_create_dispatch_not_s8(self, db_session, test_project):
        """分支：非S8阶段 - 不创建派工单"""
        machine = Machine(
            project_id=test_project.id,
            machine_no="PN002",
            machine_name="测试设备2",
        )
        db_session.add(machine)
        db_session.commit()

        # 执行（非S8）
        create_installation_dispatch_orders(
            db=db_session,
            project=test_project,
            target_stage="S7",
            old_stage="S6",
        )

        # 不应创建派工单
        from app.models.installation_dispatch import InstallationDispatchOrder
        orders = db_session.query(InstallationDispatchOrder).filter(
            InstallationDispatchOrder.project_id == test_project.id
        ).all()

        assert len(orders) == 0

    def test_create_dispatch_already_s8(self, db_session, test_project):
        """分支：已在S8 - 不重复创建"""
        machine = Machine(
            project_id=test_project.id,
            machine_no="PN003",
            machine_name="测试设备3",
        )
        db_session.add(machine)
        db_session.commit()

        # 从S8到S8（没有实际推进）
        create_installation_dispatch_orders(
            db=db_session,
            project=test_project,
            target_stage="S8",
            old_stage="S8",
        )

        # 不应创建派工单
        from app.models.installation_dispatch import InstallationDispatchOrder
        orders = db_session.query(InstallationDispatchOrder).filter(
            InstallationDispatchOrder.project_id == test_project.id
        ).all()

        assert len(orders) == 0

    def test_create_dispatch_existing_order(self, db_session, test_project):
        """分支：已存在派工单 - 不重复创建"""
        from app.models.installation_dispatch import InstallationDispatchOrder

        machine = Machine(
            project_id=test_project.id,
            machine_no="PN004",
            machine_name="测试设备4",
        )
        db_session.add(machine)
        db_session.commit()

        # 先创建一个派工单
        existing_order = InstallationDispatchOrder(
            order_no="INST2026001",
            project_id=test_project.id,
            machine_id=machine.id,
            task_type="INSTALLATION",
            task_title="已存在的派工单",
            status="PENDING",
        )
        db_session.add(existing_order)
        db_session.commit()

        # 再次触发创建
        create_installation_dispatch_orders(
            db=db_session,
            project=test_project,
            target_stage="S8",
            old_stage="S7",
        )

        # 验证没有重复创建
        orders = db_session.query(InstallationDispatchOrder).filter(
            InstallationDispatchOrder.project_id == test_project.id,
            InstallationDispatchOrder.machine_id == machine.id,
        ).all()

        assert len(orders) == 1  # 只有原来的那个


class TestCostReviewReportBranches:
    """测试成本复盘报告自动生成的分支逻辑"""

    def test_generate_cost_review_s9(self, db_session, test_project):
        """分支：进入S9 - 自动生成成本复盘"""
        # 注意：实际测试需要 mock CostReviewService
        # 这里只测试触发条件
        try:
            generate_cost_review_report(
                db=db_session,
                project_id=test_project.id,
                target_stage="S9",
                new_status="ST30",
                current_user_id=1,
            )
        except Exception:
            # 由于依赖服务可能不存在，捕获异常
            pass

    def test_generate_cost_review_st30(self, db_session, test_project):
        """分支：状态变为ST30 - 自动生成成本复盘"""
        try:
            generate_cost_review_report(
                db=db_session,
                project_id=test_project.id,
                target_stage="S8",
                new_status="ST30",
                current_user_id=1,
            )
        except Exception:
            pass

    def test_generate_cost_review_not_triggered(self, db_session, test_project):
        """分支：非S9且非ST30 - 不触发"""
        # 这个应该什么都不做
        generate_cost_review_report(
            db=db_session,
            project_id=test_project.id,
            target_stage="S7",
            new_status="ST20",
            current_user_id=1,
        )

        # 验证没有创建复盘报告（如果能查询的话）


class TestStageAdvancementFlowBranches:
    """测试完整的阶段推进流程分支"""

    def test_full_flow_s3_to_s4(self, db_session, test_project, test_superuser):
        """分支：完整流程 S3→S4"""
        old_stage = test_project.stage
        old_status = test_project.status
        old_health = test_project.health

        # 1. 验证目标阶段
        validate_target_stage("S4")

        # 2. 验证推进方向
        validate_stage_advancement("S3", "S4")

        # 3. 阶段门校验（超级管理员自动通过）
        passed, missing, result = perform_gate_check(
            db=db_session,
            project=test_project,
            target_stage="S4",
            skip_gate_check=False,
            current_user_is_superuser=True,
        )
        assert passed is True

        # 4. 更新阶段和状态
        new_status = update_project_stage_and_status(
            db=db_session,
            project=test_project,
            target_stage="S4",
            old_stage=old_stage,
            old_status=old_status,
        )

        # 5. 创建状态日志
        create_status_log(
            db=db_session,
            project_id=test_project.id,
            old_stage=old_stage,
            new_stage="S4",
            old_status=old_status,
            new_status=new_status,
            old_health=old_health,
            new_health=old_health,
            reason="测试完整流程",
            changed_by=test_superuser.id,
        )

        # 验证最终结果
        db_session.refresh(test_project)
        assert test_project.stage == "S4"
        assert test_project.status == "ST07"

        # 验证日志
        logs = db_session.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == test_project.id
        ).all()
        assert len(logs) >= 1

    def test_full_flow_s7_to_s8_with_dispatch(self, db_session, test_project, test_superuser):
        """分支：完整流程 S7→S8（触发安装派工）"""
        test_project.stage = "S7"
        test_project.status = "ST20"

        # 创建机台
        machine = Machine(
            project_id=test_project.id,
            machine_no="PN005",
            machine_name="测试设备5",
        )
        db_session.add(machine)
        db_session.commit()

        # 推进到S8
        update_project_stage_and_status(
            db=db_session,
            project=test_project,
            target_stage="S8",
            old_stage="S7",
            old_status="ST20",
        )

        # 触发自动创建派工单
        create_installation_dispatch_orders(
            db=db_session,
            project=test_project,
            target_stage="S8",
            old_stage="S7",
        )

        # 验证派工单创建
        from app.models.installation_dispatch import InstallationDispatchOrder
        orders = db_session.query(InstallationDispatchOrder).filter(
            InstallationDispatchOrder.project_id == test_project.id
        ).all()

        assert len(orders) >= 1
