# -*- coding: utf-8 -*-
"""
验收管理单元测试

覆盖 app/api/v1/endpoints/acceptance/ 目录的核心功能
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.acceptance.utils import (
    generate_issue_no,
    generate_order_no,
    validate_acceptance_rules,
    validate_completion_rules,
    validate_edit_rules,
)


# ==================== Test Fixtures ====================


@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    from app.factories import ProjectFactory

    project = ProjectFactory.create(
        project_code="P2025001",
        stage="S5",
    )
    db_session.commit()
    return project


@pytest.fixture
def test_machine(db_session: Session, test_project):
    """创建测试设备"""
    from app.factories import MachineFactory

    machine = MachineFactory.create(
        project=test_project,
        machine_code="PN001",
        machine_name="测试机台",
        stage="S5",
    )
    db_session.commit()
    return machine


@pytest.fixture
def test_acceptance_order(db_session: Session, test_project, test_machine):
    """创建测试验收单"""
    from app.factories import AcceptanceOrderFactory

    order = AcceptanceOrderFactory.create(
        project=test_project,
        machine=test_machine,
        acceptance_type="FAT",
        order_no="FAT-P2025001-M01-001",
        status="IN_PROGRESS",
    )
    db_session.commit()
    return order


# ==================== Test validate_acceptance_rules ====================


class TestValidateAcceptanceRules:
    """验收约束规则验证测试"""

    def test_project_not_found(self, db_session: Session):
        """项目不存在应抛出 404 错误"""
        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(db_session, "FAT", project_id=999)
        assert exc_info.value.status_code == 404
        assert "项目不存在" in str(exc_info.value.detail)

    def test_fat_without_machine_id(self, db_session: Session, test_project):
        """FAT 验收必须指定设备 ID"""
        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(
                db_session, "FAT", project_id=test_project.id, machine_id=None
            )
        assert exc_info.value.status_code == 400
        assert "必须指定设备" in str(exc_info.value.detail)

    def test_fat_machine_not_found(self, db_session: Session, test_project):
        """FAT 验收指定的设备不存在应抛出 404"""
        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(
                db_session, "FAT", project_id=test_project.id, machine_id=99999
            )
        assert exc_info.value.status_code == 404
        assert "设备不存在" in str(exc_info.value.detail)

    def test_fat_machine_wrong_stage(
        self, db_session: Session, test_project, test_machine
    ):
        """设备未达到 S5 阶段时 FAT 验收应该抛出 400"""
        test_machine.stage = "S3"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(
                db_session,
                "FAT",
                project_id=test_project.id,
                machine_id=test_machine.id,
            )
        assert exc_info.value.status_code == 400
        assert "尚未完成调试" in str(exc_info.value.detail)
        assert "S5" in str(exc_info.value.detail)

    def test_fat_project_wrong_stage(
        self, db_session: Session, test_project, test_machine
    ):
        """项目未进入 S5 阶段时 FAT 验收应该抛出 400"""
        test_project.stage = "S4"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(
                db_session,
                "FAT",
                project_id=test_project.id,
                machine_id=test_machine.id,
            )
        assert exc_info.value.status_code == 400
        assert "尚未进入调试出厂阶段" in str(exc_info.value.detail)

    def test_fat_success(self, db_session: Session, test_project, test_machine):
        """设备在 S5 阶段，FAT 验收应该通过"""
        test_machine.stage = "S5"
        test_project.stage = "S5"
        db_session.commit()

        # 不应该抛出异常
        validate_acceptance_rules(
            db_session, "FAT", project_id=test_project.id, machine_id=test_machine.id
        )

    def test_sat_without_machine_id(self, db_session: Session, test_project):
        """SAT 验收必须指定设备 ID"""
        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(
                db_session, "SAT", project_id=test_project.id, machine_id=None
            )
        assert exc_info.value.status_code == 400
        assert "必须指定设备" in str(exc_info.value.detail)

    def test_sat_without_fat_completed(
        self, db_session: Session, test_project, test_machine
    ):
        """SAT 验收在 FAT 未通过时应该抛出 400"""
        test_machine.stage = "S7"
        test_project.stage = "S7"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(
                db_session,
                "SAT",
                project_id=test_project.id,
                machine_id=test_machine.id,
            )
        assert exc_info.value.status_code == 400
        assert "SAT验收必须在FAT验收通过后" in str(exc_info.value.detail)

    def test_sat_project_wrong_stage(
        self, db_session: Session, test_project, test_machine
    ):
        """项目未进入 S7 阶段时 SAT 验收应该抛出 400"""
        # 创建通过的 FAT 验收单
        from app.factories import AcceptanceOrderFactory

        fat_order = AcceptanceOrderFactory.create(
            project=test_project,
            machine=test_machine,
            acceptance_type="FAT",
            status="COMPLETED",
            overall_result="PASSED",
        )
        db_session.commit()

        test_project.stage = "S6"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(
                db_session,
                "SAT",
                project_id=test_project.id,
                machine_id=test_machine.id,
            )
        assert exc_info.value.status_code == 400
        assert "尚未进入现场安装阶段" in str(exc_info.value.detail)

    def test_sat_success_after_fat(
        self, db_session: Session, test_project, test_machine
    ):
        """SAT 验收在 FAT 通过后应该可以"""
        # 准备通过的 FAT 验收单
        from app.factories import AcceptanceOrderFactory

        fat_order = AcceptanceOrderFactory.create(
            project=test_project,
            machine=test_machine,
            acceptance_type="FAT",
            status="COMPLETED",
            overall_result="PASSED",
        )
        db_session.commit()

        test_machine.stage = "S7"
        test_project.stage = "S7"
        db_session.commit()

        # 不应该抛出异常
        validate_acceptance_rules(
            db_session, "SAT", project_id=test_project.id, machine_id=test_machine.id
        )

    def test_final_without_machines(self, db_session: Session, test_project):
        """终验收在项目没有设备时应该抛出 400"""
        test_project.stage = "S8"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(db_session, "FINAL", project_id=test_project.id)
        assert exc_info.value.status_code == 400
        assert "项目中没有设备" in str(exc_info.value.detail)

    def test_final_without_sat_completed(
        self, db_session: Session, test_project, test_machine
    ):
        """终验收在 SAT 未通过时应该抛出 400"""
        test_project.stage = "S8"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(db_session, "FINAL", project_id=test_project.id)
        assert exc_info.value.status_code == 400
        assert "尚未通过SAT验收" in str(exc_info.value.detail)

    def test_final_project_wrong_stage(
        self, db_session: Session, test_project, test_machine
    ):
        """项目未进入 S8 阶段时终验收应该抛出 400"""
        # 准备通过的 SAT 验收单
        from app.factories import AcceptanceOrderFactory

        sat_order = AcceptanceOrderFactory.create(
            project=test_project,
            machine=test_machine,
            acceptance_type="SAT",
            status="COMPLETED",
            overall_result="PASSED",
        )
        db_session.commit()

        test_project.stage = "S7"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_acceptance_rules(db_session, "FINAL", project_id=test_project.id)
        assert exc_info.value.status_code == 400
        assert "尚未进入验收结项阶段" in str(exc_info.value.detail)

    def test_final_success_after_all_sat(
        self, db_session: Session, test_project, test_machine
    ):
        """终验收在所有设备 SAT 通过后应该可以"""
        # 准备通过的 SAT 验收单
        from app.factories import AcceptanceOrderFactory

        sat_order = AcceptanceOrderFactory.create(
            project=test_project,
            machine=test_machine,
            acceptance_type="SAT",
            status="COMPLETED",
            overall_result="PASSED",
        )
        db_session.commit()

        test_project.stage = "S8"
        db_session.commit()

        # 不应该抛出异常
        validate_acceptance_rules(db_session, "FINAL", project_id=test_project.id)


# ==================== Test validate_completion_rules ====================


class TestValidateCompletionRules:
    """完成验收约束规则验证测试"""

    def test_order_not_found(self, db_session: Session):
        """验收单不存在时应该抛出 404 错误"""
        with pytest.raises(HTTPException) as exc_info:
            validate_completion_rules(db_session, order_id=99999)
        assert exc_info.value.status_code == 404
        assert "验收单不存在" in str(exc_info.value.detail)

    def test_blocking_open_issue(self, db_session: Session, test_acceptance_order):
        """存在未闭环的阻塞问题应该抛出 400 错误"""
        from app.factories import AcceptanceIssueFactory

        issue = AcceptanceIssueFactory.create(
            order=test_acceptance_order, is_blocking=True, status="OPEN"
        )
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_completion_rules(db_session, order_id=test_acceptance_order.id)
        assert exc_info.value.status_code == 400
        assert "未闭环的阻塞问题" in str(exc_info.value.detail)

    def test_blocking_processing_issue(
        self, db_session: Session, test_acceptance_order
    ):
        """处理中的阻塞问题应该抛出 400 错误"""
        from app.factories import AcceptanceIssueFactory

        issue = AcceptanceIssueFactory.create(
            order=test_acceptance_order, is_blocking=True, status="PROCESSING"
        )
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_completion_rules(db_session, order_id=test_acceptance_order.id)
        assert exc_info.value.status_code == 400

    def test_blocking_deferred_issue(self, db_session: Session, test_acceptance_order):
        """延期的阻塞问题应该抛出 400 错误"""
        from app.factories import AcceptanceIssueFactory

        issue = AcceptanceIssueFactory.create(
            order=test_acceptance_order, is_blocking=True, status="DEFERRED"
        )
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_completion_rules(db_session, order_id=test_acceptance_order.id)
        assert exc_info.value.status_code == 400

    def test_resolved_but_not_verified_blocking_issue(
        self, db_session: Session, test_acceptance_order
    ):
        """已解决但未验证的阻塞问题应该抛出 400 错误"""
        from app.factories import AcceptanceIssueFactory

        issue = AcceptanceIssueFactory.create(
            order=test_acceptance_order,
            is_blocking=True,
            status="RESOLVED",
            verified_result="PENDING",
        )
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_completion_rules(db_session, order_id=test_acceptance_order.id)
        assert exc_info.value.status_code == 400
        assert "未闭环的阻塞问题" in str(exc_info.value.detail)

    def test_verified_blocking_issue_allowed(
        self, db_session: Session, test_acceptance_order
    ):
        """已验证通过的阻塞问题应该允许完成验收"""
        from app.factories import AcceptanceIssueFactory

        issue = AcceptanceIssueFactory.create(
            order=test_acceptance_order,
            is_blocking=True,
            status="RESOLVED",
            verified_result="VERIFIED",
        )
        db_session.commit()

        # 不应该抛出异常
        validate_completion_rules(db_session, order_id=test_acceptance_order.id)

    def test_non_blocking_issue_allowed(
        self, db_session: Session, test_acceptance_order
    ):
        """非阻塞问题应该允许完成验收"""
        from app.factories import AcceptanceIssueFactory

        issue = AcceptanceIssueFactory.create(
            order=test_acceptance_order, is_blocking=False, status="OPEN"
        )
        db_session.commit()

        # 不应该抛出异常
        validate_completion_rules(db_session, order_id=test_acceptance_order.id)

    def test_no_blocking_issues_allowed(
        self, db_session: Session, test_acceptance_order
    ):
        """没有阻塞问题应该允许完成验收"""
        # 不应该抛出异常
        validate_completion_rules(db_session, order_id=test_acceptance_order.id)


# ==================== Test validate_edit_rules ====================


class TestValidateEditRules:
    """编辑验收单约束规则验证测试"""

    def test_order_not_found(self, db_session: Session):
        """验收单不存在时应该抛出 404 错误"""
        with pytest.raises(HTTPException) as exc_info:
            validate_edit_rules(db_session, order_id=99999)
        assert exc_info.value.status_code == 404
        assert "验收单不存在" in str(exc_info.value.detail)

    def test_customer_signed_not_editable(
        self, db_session: Session, test_acceptance_order
    ):
        """客户已签字后验收单不可修改"""
        test_acceptance_order.customer_signed_at = "2025-01-20"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_edit_rules(db_session, order_id=test_acceptance_order.id)
        assert exc_info.value.status_code == 400
        assert "客户已签字确认" in str(exc_info.value.detail)

    def test_customer_signer_not_editable(
        self, db_session: Session, test_acceptance_order
    ):
        """有客户签字人后验收单不可修改"""
        test_acceptance_order.customer_signer = "客户姓名"
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_edit_rules(db_session, order_id=test_acceptance_order.id)
        assert exc_info.value.status_code == 400
        assert "客户已签字确认" in str(exc_info.value.detail)

    def test_officially_completed_not_editable(
        self, db_session: Session, test_acceptance_order
    ):
        """验收单已正式完成（已上传客户签署文件）不可修改"""
        test_acceptance_order.is_officially_completed = True
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validate_edit_rules(db_session, order_id=test_acceptance_order.id)
        assert exc_info.value.status_code == 400
        assert "已正式完成" in str(exc_info.value.detail)

    def test_editable_when_not_signed(self, db_session: Session, test_acceptance_order):
        """未签字的验收单应该可以编辑"""
        test_acceptance_order.customer_signed_at = None
        test_acceptance_order.customer_signer = None
        test_acceptance_order.is_officially_completed = False
        db_session.commit()

        # 不应该抛出异常
        validate_edit_rules(db_session, order_id=test_acceptance_order.id)


# ==================== Test generate_order_no ====================


class TestGenerateOrderNo:
    """验收单编号生成测试"""

    def test_fat_order_no(self, db_session: Session, test_project, test_machine):
        """FAT 验收单编号格式正确"""
        order_no = generate_order_no(db_session, "FAT", test_project.project_code, 1)
        assert order_no.startswith("FAT-P2025001-M01-")
        assert order_no.endswith("-001")

    def test_sat_order_no(self, db_session: Session, test_project, test_machine):
        """SAT 验收单编号格式正确"""
        order_no = generate_order_no(db_session, "SAT", test_project.project_code, 2)
        assert order_no.startswith("SAT-P2025001-M02-")
        assert order_no.endswith("-001")

    def test_final_order_no(self, db_session: Session, test_project):
        """终验收单编号格式正确"""
        order_no = generate_order_no(db_session, "FINAL", test_project.project_code)
        assert order_no.startswith("FIN-P2025001-")
        assert order_no.endswith("-001")

    def test_order_no_increment(self, db_session: Session, test_project, test_machine):
        """验收单编号序号自动递增"""
        from app.factories import AcceptanceOrderFactory

        # 创建第一个验收单
        AcceptanceOrderFactory.create(
            project=test_project,
            machine=test_machine,
            acceptance_type="FAT",
            order_no="FAT-P2025001-M01-001",
        )
        db_session.commit()

        # 生成新的验收单号
        order_no = generate_order_no(db_session, "FAT", test_project.project_code, 1)
        assert order_no == "FAT-P2025001-M01-002"

    def test_fat_order_no_without_machine(self, db_session: Session):
        """FAT 验收单未提供设备序号时应该抛出错误"""
        with pytest.raises(ValueError) as exc_info:
            generate_order_no(db_session, "FAT", "P2025001", None)
        assert "必须提供设备序号" in str(exc_info.value)

    def test_unknown_type_order_no(self, db_session: Session, test_project):
        """未知类型验收单使用 AC 前缀"""
        order_no = generate_order_no(db_session, "UNKNOWN", test_project.project_code)
        assert order_no.startswith("AC-P2025001-")

    def test_machine_no_formatting(self, db_session: Session, test_project):
        """设备序号格式化为两位数字"""
        order_no = generate_order_no(db_session, "FAT", test_project.project_code, 1)
        assert "-M01-" in order_no

        order_no2 = generate_order_no(db_session, "FAT", test_project.project_code, 99)
        assert "-M99-" in order_no2

    def test_order_no_sequence_formatting(self, db_session: Session, test_project):
        """序号格式化为三位数字"""
        order_no = generate_order_no(db_session, "FINAL", test_project.project_code)
        assert order_no.endswith("-001")


# ==================== Test generate_issue_no ====================


class TestGenerateIssueNo:
    """问题编号生成测试"""

    def test_issue_no_from_fat_order(self, db_session: Session, test_acceptance_order):
        """FAT 验收单的问题编号格式正确"""
        test_acceptance_order.order_no = "FAT-P2025001-M01-001"
        db_session.commit()

        issue_no = generate_issue_no(db_session, test_acceptance_order.order_no)
        assert issue_no.startswith("AI-FAT001-")

    def test_issue_no_from_sat_order(self, db_session: Session, test_acceptance_order):
        """SAT 验收单的问题编号格式正确"""
        test_acceptance_order.order_no = "SAT-P2025001-M02-002"
        db_session.commit()

        issue_no = generate_issue_no(db_session, test_acceptance_order.order_no)
        assert issue_no.startswith("AI-SAT002-")

    def test_issue_no_from_final_order(
        self, db_session: Session, test_acceptance_order
    ):
        """终验收单的问题编号格式正确"""
        test_acceptance_order.order_no = "FIN-P2025001-001"
        db_session.commit()

        issue_no = generate_issue_no(db_session, test_acceptance_order.order_no)
        assert issue_no.startswith("AI-FIN001-")

    def test_issue_no_increment(self, db_session: Session, test_acceptance_order):
        """问题编号序号自动递增"""
        from app.factories import AcceptanceIssueFactory

        test_acceptance_order.order_no = "FAT-P2025001-M01-001"
        db_session.commit()

        # 创建第一个问题
        AcceptanceIssueFactory.create(
            order=test_acceptance_order, issue_no="AI-FAT001-001"
        )
        db_session.commit()

        # 生成新的问题号
        issue_no = generate_issue_no(db_session, test_acceptance_order.order_no)
        assert issue_no == "AI-FAT001-002"

    def test_issue_no_with_abnormal_format(
        self, db_session: Session, test_acceptance_order
    ):
        """异常格式的验收单号使用简化规则"""
        test_acceptance_order.order_no = "ABNORMAL"
        db_session.commit()

        issue_no = generate_issue_no(db_session, test_acceptance_order.order_no)
        assert issue_no.startswith("AI-")

    def test_issue_no_with_short_format(
        self, db_session: Session, test_acceptance_order
    ):
        """过短的验收单号使用简化规则"""
        test_acceptance_order.order_no = "AB"
        db_session.commit()

        issue_no = generate_issue_no(db_session, test_acceptance_order.order_no)
        assert len(issue_no) >= 3

    def test_issue_no_sequence_formatting(
        self, db_session: Session, test_acceptance_order
    ):
        """序号格式化为三位数字"""
        test_acceptance_order.order_no = "FAT-P2025001-M01-001"
        db_session.commit()

        issue_no = generate_issue_no(db_session, test_acceptance_order.order_no)
        assert issue_no.endswith("-001")
