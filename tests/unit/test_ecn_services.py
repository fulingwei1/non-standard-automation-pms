# -*- coding: utf-8 -*-
"""
ECN (Engineering Change Notice) 服务单元测试

测试内容：
- ECN自动分配服务
- ECN BOM影响分析服务
- ECN知识库服务
- ECN评估、审批、任务管理
- 受影响物料分析
"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.ecn import (
    Ecn,
    EcnAffectedMaterial,
    EcnApproval,
    EcnEvaluation,
    EcnTask,
)
from app.models import Project
from app.services.ecn_auto_assign_service import (
    auto_assign_approval,
    auto_assign_pending_evaluations,
    auto_assign_task,
    find_users_by_department,
    find_users_by_role,
)
from app.services.ecn_bom_analysis_service import EcnBomAnalysisService
from app.services.ecn_knowledge_service import EcnKnowledgeService


@pytest.mark.unit
class TestFindUsersByDepartment:
    """测试根据部门查找用户"""

    def test_find_users_by_department_empty(self, db_session: Session):
        """测试部门没有用户"""
        users = find_users_by_department(db_session, "不存在的部门")

        assert users == []


@pytest.mark.unit
class TestFindUsersByRole:
    """测试根据角色查找用户"""

    def test_find_users_by_role_no_role(self, db_session: Session):
        """测试角色不存在"""
        users = find_users_by_role(db_session, "不存在的角色")

        assert users == []


@pytest.mark.unit
class TestAutoAssignEvaluation:
    """测试自动分配评估任务"""


@pytest.mark.unit
class TestAutoAssignApproval:
    """测试自动分配审批任务"""

    def test_auto_assign_approval_no_role(self, db_session: Session):
        """测试角色不存在"""
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        ecn = Ecn(
            ecn_no="ECN-TEST-006",
            ecn_title="测试ECN6",
            ecn_type="DESIGN_CHANGE",
            source_type="MANUAL",
            project_id=project.id,
            change_reason="测试",
            change_description="测试",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(ecn)
        db_session.flush()

        approval = EcnApproval(
            ecn_id=ecn.id,
            approval_level=1,
            approval_role="不存在的角色",
            status="PENDING",
            approver_id=None,
        )
        db_session.add(approval)
        db_session.commit()

        approver_id = auto_assign_approval(db_session, ecn, approval)

        assert approver_id is None


@pytest.mark.unit
class TestAutoAssignTask:
    """测试自动分配执行任务"""

    def test_auto_assign_task_no_dept(self, db_session: Session):
        """测试任务部门为空"""
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        ecn = Ecn(
            ecn_no="ECN-TEST-008",
            ecn_title="测试ECN8",
            ecn_type="DESIGN_CHANGE",
            source_type="MANUAL",
            project_id=project.id,
            change_reason="测试",
            change_description="测试",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(ecn)
        db_session.flush()

        task = EcnTask(
            ecn_id=ecn.id,
            task_no=1,
            task_name="测试任务",
            task_dept=None,
            status="PENDING",
            assignee_id=None,
        )
        db_session.add(task)
        db_session.commit()

        assignee_id = auto_assign_task(db_session, ecn, task)

        assert assignee_id is None


@pytest.mark.unit
class TestAutoAssignPendingEvaluations:
    """测试批量分配待评估任务"""

    def test_auto_assign_pending_evaluations_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        assigned_count = auto_assign_pending_evaluations(db_session, 999999)

        assert assigned_count == 0


@pytest.mark.unit
class TestAutoAssignPendingApprovals:
    """测试批量分配待审批任务"""


@pytest.mark.unit
class TestAutoAssignPendingTasks:
    """测试批量分配待执行任务"""


@pytest.mark.unit
class TestEcnBomAnalysisService:
    """测试BOM影响分析服务"""

    def test_service_init(self, db_session: Session):
        """测试服务初始化"""
        service = EcnBomAnalysisService(db_session)
        assert service.db == db_session

    def test_analyze_bom_impact_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        service = EcnBomAnalysisService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.analyze_bom_impact(ecn_id=999999)

        assert "不存在" in str(exc_info.value)

    def test_analyze_bom_impact_no_affected_materials(self, db_session: Session):
        """测试没有受影响物料"""
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        from app.models import Machine

        machine = Machine(
            project_id=project.id,
            machine_code="M-TEST",
            machine_name="测试设备",
            machine_type="TEST",
            status="DESIGN",
        )
        db_session.add(machine)
        db_session.flush()

        ecn = Ecn(
            ecn_no="ECN-TEST-012",
            ecn_title="测试ECN12",
            ecn_type="DESIGN_CHANGE",
            source_type="MANUAL",
            project_id=project.id,
            machine_id=machine.id,
            change_reason="测试",
            change_description="测试",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(ecn)
        db_session.commit()

        service = EcnBomAnalysisService(db_session)
        result = service.analyze_bom_impact(ecn.id)

        assert result["has_impact"] is False
        assert "没有受影响的物料" in result["message"]

    def test_check_obsolete_risk_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        service = EcnBomAnalysisService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.check_obsolete_material_risk(ecn_id=999999)

        assert "不存在" in str(exc_info.value)


@pytest.mark.unit
class TestEcnKnowledgeService:
    """测试知识库服务"""

    def test_service_init(self, db_session: Session):
        """测试服务初始化"""
        service = EcnKnowledgeService(db_session)
        assert service.db == db_session

    def test_extract_solution_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        service = EcnKnowledgeService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.extract_solution(ecn_id=999999)

        assert "不存在" in str(exc_info.value)

    def test_find_similar_ecns_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        service = EcnKnowledgeService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.find_similar_ecns(ecn_id=999999)

        assert "不存在" in str(exc_info.value)

    def test_create_solution_template_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        service = EcnKnowledgeService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.create_solution_template(
                ecn_id=999999,
                template_data={},
                created_by=1,
            )

        assert "不存在" in str(exc_info.value)

    def test_recommend_solutions_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        service = EcnKnowledgeService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.recommend_solutions(ecn_id=999999)

        assert "不存在" in str(exc_info.value)

    def test_apply_solution_template_no_ecn(self, db_session: Session):
        """测试ECN不存在"""
        service = EcnKnowledgeService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.apply_solution_template(
                ecn_id=999999,
                template_id=1,
            )

        assert "不存在" in str(exc_info.value)

    def test_apply_solution_template_no_template(self, db_session: Session):
        """测试模板不存在"""
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        ecn = Ecn(
            ecn_no="ECN-TEST-015",
            ecn_title="测试ECN15",
            ecn_type="DESIGN_CHANGE",
            source_type="MANUAL",
            project_id=project.id,
            change_reason="测试",
            change_description="测试",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(ecn)
        db_session.commit()

        service = EcnKnowledgeService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.apply_solution_template(
                ecn_id=ecn.id,
                template_id=999999,
            )

        assert "不存在" in str(exc_info.value)


@pytest.mark.unit
class TestEcnEvaluationWorkflow:
    """测试ECN评估工作流"""

    def test_evaluation_creation_for_different_types(self, db_session: Session):
        """测试不同类型ECN的评估创建"""
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        change_types = [
            "DESIGN_CHANGE",
            "MATERIAL_CHANGE",
            "PROCESS_CHANGE",
            "SPECIFICATION_CHANGE",
            "PLAN_CHANGE",
        ]

        for ecn_type in change_types:
            ecn = Ecn(
                ecn_no=f"ECN-{ecn_type}-001",
                ecn_title=f"{ecn_type}测试",
                ecn_type=ecn_type,
                source_type="MANUAL",
                project_id=project.id,
                change_reason="测试",
                change_description="测试",
                status="DRAFT",
                created_by=1,
            )
            db_session.add(ecn)
            db_session.flush()

            evaluation = EcnEvaluation(
                ecn_id=ecn.id,
                eval_dept="工程部",
                impact_analysis="影响分析",
                cost_estimate=Decimal("1000"),
                schedule_estimate=5,
                status="COMPLETED",
            )
            db_session.add(evaluation)
            db_session.commit()

            assert evaluation.id is not None
            assert evaluation.ecn_id == ecn.id
            assert ecn.ecn_type == ecn_type


@pytest.mark.unit
class TestEcnApprovalWorkflow:
    """测试ECN审批工作流"""


@pytest.mark.unit
class TestEcnTaskManagement:
    """测试ECN任务管理"""


@pytest.mark.unit
class TestAffectedMaterialsAnalysis:
    """测试受影响物料分析"""

    def test_affected_materials_different_change_types(self, db_session: Session):
        """测试不同变更类型的受影响物料"""
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        ecn = Ecn(
            ecn_no="ECN-TEST-021",
            ecn_title="测试ECN21",
            ecn_type="DESIGN_CHANGE",
            source_type="MANUAL",
            project_id=project.id,
            change_reason="测试",
            change_description="测试",
            status="DRAFT",
            created_by=1,
        )
        db_session.add(ecn)
        db_session.flush()

        change_types = ["ADD", "DELETE", "UPDATE", "REPLACE"]

        for i, change_type in enumerate(change_types):
            mat = EcnAffectedMaterial(
                ecn_id=ecn.id,
                material_code=f"MAT-{i + 1:03d}",
                material_name=f"物料{i + 1}",
                change_type=change_type,
                old_quantity=Decimal("10")
                if change_type in ["UPDATE", "REPLACE"]
                else None,
                new_quantity=Decimal("20")
                if change_type in ["ADD", "UPDATE", "REPLACE"]
                else None,
                cost_impact=Decimal("100") * (i + 1),
            )
            db_session.add(mat)

        db_session.commit()

        affected_mats = (
            db_session.query(EcnAffectedMaterial)
            .filter(EcnAffectedMaterial.ecn_id == ecn.id)
            .all()
        )

        assert len(affected_mats) == 4
        assert set(m.change_type for m in affected_mats) == set(change_types)

    def test_impact_calculation(self, db_session: Session):
        """测试影响计算"""
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=1,
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
        )
        db_session.add(project)
        db_session.flush()

        ecn = Ecn(
            ecn_no="ECN-TEST-022",
            ecn_title="测试ECN22",
            ecn_type="DESIGN_CHANGE",
            source_type="MANUAL",
            project_id=project.id,
            change_reason="测试",
            change_description="测试",
            cost_impact=Decimal("10000"),
            schedule_impact_days=10,
            status="DRAFT",
            created_by=1,
        )
        db_session.add(ecn)
        db_session.flush()

        mat1 = EcnAffectedMaterial(
            ecn_id=ecn.id,
            material_code="MAT-001",
            material_name="物料1",
            change_type="UPDATE",
            old_quantity=Decimal("10"),
            new_quantity=Decimal("15"),
            cost_impact=Decimal("5000"),
        )
        mat2 = EcnAffectedMaterial(
            ecn_id=ecn.id,
            material_code="MAT-002",
            material_name="物料2",
            change_type="ADD",
            new_quantity=Decimal("20"),
            cost_impact=Decimal("8000"),
        )
        db_session.add_all([mat1, mat2])
        db_session.commit()

        total_impact = sum(m.cost_impact or Decimal("0") for m in [mat1, mat2])

        assert total_impact == Decimal("13000")
        assert ecn.cost_impact == Decimal("10000")
        assert ecn.schedule_impact_days == 10
