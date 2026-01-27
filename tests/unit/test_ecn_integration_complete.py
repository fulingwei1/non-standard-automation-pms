# -*- coding: utf-8 -*-
"""
ECN集成服务完整测试

包含ECN自动分配、BOM分析、知识库服务的完整测试
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.ecn import (
    Ecn,
    EcnAffectedMaterial,
    EcnApproval,
    EcnBomImpact,
    EcnEvaluation,
    EcnSolutionTemplate,
)
from app.models.material import BomHeader, BomItem, Material
from app.models.organization import Department
from app.models.project import Machine, Project, ProjectMember
from app.models.user import Role, User, UserRole
from app.services.ecn_auto_assign_service import (
    auto_assign_approval,
    auto_assign_evaluation,
    find_users_by_department,
    find_users_by_role,
)
from app.services.ecn_bom_analysis_service import EcnBomAnalysisService
from app.services.ecn_knowledge_service import EcnKnowledgeService


@pytest.mark.unit
class TestFindUsersByDepartment:
    """测试根据部门查找用户"""

    def test_find_active_users(self, db_session: Session):
        """查找活跃用户"""
        # 创建部门
        dept = Department(
        dept_code="DEPT-001",
        dept_name="工程部",
        level=1,
        is_active=True,
        )
        db_session.add(dept)

        # 创建活跃和非活跃用户
        active_user = User(
        username="active_user",
        real_name="活跃用户",
        department="工程部",
        is_active=True,
        position="工程师",
        )
        inactive_user = User(
        username="inactive_user",
        real_name="非活跃用户",
        department="工程部",
        is_active=False,
        position="工程师",
        )
        db_session.add_all([active_user, inactive_user])
        db_session.commit()

        # 查找用户
        users = find_users_by_department(db_session, "工程部")

        # 应只返回活跃用户
        assert len(users) == 1
        assert users[0].username == "active_user"

    def test_find_no_users(self, db_session: Session):
        """部门没有用户时返回空列表"""
        users = find_users_by_department(db_session, "不存在的部门")
        assert users == []

    def test_find_multiple_users(self, db_session: Session):
        """查找多个用户"""
        # 创建部门
        dept = Department(
        dept_code="DEPT-002",
        dept_name="质量部",
        level=1,
        is_active=True,
        )
        db_session.add(dept)

        # 创建多个用户
        users_list = [
        User(
        username=f"user_{i}",
        real_name=f"用户{i}",
        department="质量部",
        is_active=True,
        position="质量工程师",
        )
        for i in range(3)
        ]
        db_session.add_all(users_list)
        db_session.commit()

        # 查找用户
        users = find_users_by_department(db_session, "质量部")

        # 应返回所有用户
        assert len(users) == 3


@pytest.mark.unit
class TestFindUsersByRole:
    """测试根据角色查找用户"""

    def test_find_users_with_role(self, db_session: Session):
        """查找拥有特定角色的用户"""
        # 创建角色
        role = Role(
        role_code="QUALITY_MANAGER",
        role_name="质量经理",
        is_active=True,
        )
        db_session.add(role)

        # 创建拥有该角色的用户
        user1 = User(
        username="manager1",
        real_name="经理1",
        is_active=True,
        )
        user2 = User(
        username="manager2",
        real_name="经理2",
        is_active=False,
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # 分配角色
        user_role1 = UserRole(user_id=user1.id, role_id=role.id)
        user_role2 = UserRole(user_id=user2.id, role_id=role.id)
        db_session.add_all([user_role1, user_role2])
        db_session.commit()

        # 查找用户
        users = find_users_by_role(db_session, "质量经理")

        # 应只返回活跃用户
        assert len(users) == 1
        assert users[0].username == "manager1"

    def test_find_no_role(self, db_session: Session):
        """角色不存在时返回空列表"""
        users = find_users_by_role(db_session, "不存在的角色")
        assert users == []

    def test_find_users_without_assignment(self, db_session: Session):
        """角色存在但没有用户拥有该角色"""
        role = Role(
        role_code="TEST_ROLE",
        role_name="测试角色",
        is_active=True,
        )
        db_session.add(role)
        db_session.commit()

        users = find_users_by_role(db_session, "测试角色")
        assert users == []


@pytest.mark.unit
@pytest.mark.integration
class TestAutoAssignEvaluation:
    """测试自动分配评估任务"""

    def test_assign_to_project_leader(self, db_session: Session):
        """优先分配给项目负责人"""
        # 创建部门
        dept = Department(
        dept_code="DEPT-001",
        dept_name="工程部",
        is_active=True,
        )
        db_session.add(dept)

        # 创建用户
        leader = User(
        username="leader",
        real_name="部门负责人",
        department="工程部",
        is_active=True,
        position="工程部负责人",
        )
        engineer = User(
        username="engineer",
        real_name="工程师",
        department="工程部",
        is_active=True,
        position="工程师",
        )
        db_session.add_all([leader, engineer])
        db_session.commit()

        # 创建项目
        project = Project(
        project_code="PJ-001",
        project_name="测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=leader.id,
        )
        db_session.add(project)

        # 创建项目成员（包含部门负责人）
        project_member = ProjectMember(
        project_id=project.id,
        user_id=leader.id,
        role_code="DEPT_LEAD",
        is_lead=True,
        allocation_pct=100,
        created_by=leader.id,
        )
        db_session.add(project_member)

        # 创建ECN
        ecn = Ecn(
        ecn_no="ECN-001",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        project_id=project.id,
        status="DRAFT",
        created_by=engineer.id,
        )
        db_session.add(ecn)

        # 创建评估任务
        evaluation = EcnEvaluation(
        ecn_id=ecn.id,
        eval_dept="工程部",
        eval_type="TECHNICAL",
        status="PENDING",
        )
        db_session.add(evaluation)
        db_session.commit()

        # 自动分配
        assigned_user_id = auto_assign_evaluation(db_session, ecn, evaluation)

        # 应分配给部门负责人（项目成员中的）
        assert assigned_user_id == leader.id

    def test_assign_to_dept_manager(self, db_session: Session):
        """项目成员中没有负责人时分配给部门经理"""
        # 创建部门
        dept = Department(
        dept_code="DEPT-002",
        dept_name="质量部",
        is_active=True,
        )
        db_session.add(dept)

        # 创建用户（部门经理）
        manager = User(
        username="manager",
        real_name="部门经理",
        department="质量部",
        is_active=True,
        position="质量部经理",
        )
        engineer = User(
        username="quality_eng",
        real_name="质量工程师",
        department="质量部",
        is_active=True,
        position="质量工程师",
        )
        db_session.add_all([manager, engineer])
        db_session.commit()

        # 创建ECN（不关联项目）
        ecn = Ecn(
        ecn_no="ECN-002",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        status="DRAFT",
        created_by=engineer.id,
        )
        db_session.add(ecn)

        # 创建评估任务
        evaluation = EcnEvaluation(
        ecn_id=ecn.id,
        eval_dept="质量部",
        eval_type="TECHNICAL",
        status="PENDING",
        )
        db_session.add(evaluation)
        db_session.commit()

        # 自动分配
        assigned_user_id = auto_assign_evaluation(db_session, ecn, evaluation)

        # 应分配给部门经理
        assert assigned_user_id == manager.id

    def test_no_assignable_user(self, db_session: Session):
        """没有可分配的用户时返回None"""
        # 创建用户（普通员工）
        engineer = User(
        username="eng1",
        real_name="工程师1",
        department="工程部",
        is_active=True,
        position="工程师",
        )
        db_session.add(engineer)

        # 创建ECN
        ecn = Ecn(
        ecn_no="ECN-003",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        status="DRAFT",
        created_by=engineer.id,
        )
        db_session.add(ecn)

        # 创建评估任务
        evaluation = EcnEvaluation(
        ecn_id=ecn.id,
        eval_dept="工程部",
        eval_type="TECHNICAL",
        status="PENDING",
        )
        db_session.add(evaluation)
        db_session.commit()

        # 自动分配
        assigned_user_id = auto_assign_evaluation(db_session, ecn, evaluation)

        # 应返回None（不分配给普通员工）
        assert assigned_user_id is None


@pytest.mark.unit
@pytest.mark.integration
class TestAutoAssignApproval:
    """测试自动分配审批任务"""

    def test_assign_to_project_role_lead(self, db_session: Session):
        """优先分配给项目中拥有该角色的用户"""
        # 创建角色
        role = Role(
        role_code="PROJECT_MANAGER",
        role_name="项目经理",
        is_active=True,
        )
        db_session.add(role)

        # 创建用户
        pm1 = User(
        username="pm1",
        real_name="项目经理1",
        is_active=True,
        )
        pm2 = User(
        username="pm2",
        real_name="项目经理2",
        is_active=False,
        )
        db_session.add_all([pm1, pm2])
        db_session.commit()

        # 分配角色给两个用户
        user_role1 = UserRole(user_id=pm1.id, role_id=role.id)
        user_role2 = UserRole(user_id=pm2.id, role_id=role.id)
        db_session.add_all([user_role1, user_role2])

        # 创建项目
        project = Project(
        project_code="PJ-003",
        project_name="测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=pm1.id,
        )
        db_session.add(project)

        # PM1是项目成员
        project_member = ProjectMember(
        project_id=project.id,
        user_id=pm1.id,
        role_code="PM",
        is_lead=True,
        allocation_pct=100,
        created_by=pm1.id,
        )
        db_session.add(project_member)

        # 创建ECN
        ecn = Ecn(
        ecn_no="ECN-004",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        project_id=project.id,
        status="EVALUATING",
        created_by=pm1.id,
        )
        db_session.add(ecn)

        # 创建审批任务
        approval = EcnApproval(
        ecn_id=ecn.id,
        approval_role="项目经理",
        status="PENDING",
        )
        db_session.add(approval)
        db_session.commit()

        # 自动分配
        assigned_user_id = auto_assign_approval(db_session, ecn, approval)

        # 应分配给项目中的PM
        assert assigned_user_id == pm1.id

    def test_assign_to_role_manager(self, db_session: Session):
        """项目成员中没有拥有该角色的用户时分配给角色经理"""
        # 创建角色
        role = Role(
        role_code="FINANCE_MANAGER",
        role_name="财务经理",
        is_active=True,
        )
        db_session.add(role)

        # 创建用户
        manager = User(
        username="fin_mgr",
        real_name="财务经理",
        is_active=True,
        )
        db_session.add(manager)
        db_session.commit()

        # 分配角色
        user_role = UserRole(user_id=manager.id, role_id=role.id)
        db_session.add(user_role)

        # 创建ECN（不关联项目）
        ecn = Ecn(
        ecn_no="ECN-005",
        ecn_title="测试ECN",
        ecn_type="COST",
        status="EVALUATING",
        created_by=manager.id,
        )
        db_session.add(ecn)

        # 创建审批任务
        approval = EcnApproval(
        ecn_id=ecn.id,
        approval_role="财务经理",
        status="PENDING",
        )
        db_session.add(approval)
        db_session.commit()

        # 自动分配
        assigned_user_id = auto_assign_approval(db_session, ecn, approval)

        # 应分配给拥有该角色的用户
        assert assigned_user_id == manager.id


@pytest.mark.unit
@pytest.mark.integration
class TestEcnBomAnalysisService:
    """测试ECN BOM影响分析服务"""

    def test_analyze_bom_impact_no_affected_materials(self, db_session: Session):
        """没有受影响物料时返回无影响"""
        # 创建项目、设备
        project = Project(
        project_code="PJ-010",
        project_name="测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        machine = Machine(
        project_id=project.id,
        machine_code="M-010",
        machine_name="测试设备",
        machine_type="TEST",
        status="DESIGN",
        )
        db_session.add(machine)

        # 创建ECN（没有受影响物料）
        ecn = Ecn(
        ecn_no="ECN-010",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        project_id=project.id,
        machine_id=machine.id,
        status="SUBMITTED",
        created_by=1,
        )
        db_session.add(ecn)
        db_session.commit()

        # 分析BOM影响
        service = EcnBomAnalysisService(db_session)
        result = service.analyze_bom_impact(ecn.id)

        # 应返回无影响
        assert result["has_impact"] is False
        assert "没有受影响的物料" in result["message"]

    def test_analyze_bom_impact_with_cost_impact(self, db_session: Session):
        """测试BOM影响中的成本影响计算"""
        # 创建项目、设备
        project = Project(
        project_code="PJ-011",
        project_name="测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        machine = Machine(
        project_id=project.id,
        machine_code="M-011",
        machine_name="测试设备",
        machine_type="TEST",
        status="DESIGN",
        )
        db_session.add(machine)

        # 创建物料
        material1 = Material(
        material_code="MAT-001",
        material_name="物料1",
        unit_price=Decimal("100.00"),
        )
        material2 = Material(
        material_code="MAT-002",
        material_name="物料2",
        unit_price=Decimal("50.00"),
        )
        db_session.add_all([material1, material2])

        # 创建BOM
        bom_header = BomHeader(
        machine_id=machine.id,
        bom_version="1.0",
        bom_name="测试BOM",
        status="RELEASED",
        is_latest=True,
        created_by=1,
        )
        db_session.add(bom_header)

        # 创建BOM项
        bom_item1 = BomItem(
        bom_id=bom_header.id,
        material_id=material1.id,
        quantity=10,
        unit_price=Decimal("100.00"),
        )
        bom_item2 = BomItem(
        bom_id=bom_header.id,
        material_id=material2.id,
        quantity=20,
        unit_price=Decimal("50.00"),
        )
        db_session.add_all([bom_item1, bom_item2])

        # 创建ECN和受影响物料
        ecn = Ecn(
        ecn_no="ECN-011",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        project_id=project.id,
        machine_id=machine.id,
        status="SUBMITTED",
        created_by=1,
        )
        db_session.add(ecn)

        affected_mat = EcnAffectedMaterial(
        ecn_id=ecn.id,
        material_id=material1.id,
        old_material_code="MAT-001",
        new_material_code="MAT-NEW",
        cost_delta=Decimal("20.00"),  # 新物料贵20元
        quantity=10,
        )
        db_session.add(affected_mat)
        db_session.commit()

        # 分析BOM影响
        service = EcnBomAnalysisService(db_session)
        result = service.analyze_bom_impact(ecn.id)

        # 验证成本影响计算
        assert result["has_impact"] is True
        assert result["total_affected_items"] == 1
        # 成本影响 = 20元差价 × 10数量 = 200元
        assert result["total_cost_impact"] == 200.0


@pytest.mark.unit
@pytest.mark.integration
class TestEcnKnowledgeService:
    """测试ECN知识库服务"""

    def test_extract_solution_auto(self, db_session: Session):
        """自动提取解决方案"""
        # 创建ECN
        ecn = Ecn(
        ecn_no="ECN-020",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        root_cause_category="设计缺陷",
        solution="更换为更坚固的材料",
        cost_impact=Decimal("1000.00"),
        schedule_impact_days=5,
        status="COMPLETED",
        created_by=1,
        )
        db_session.add(ecn)
        db_session.commit()

        # 提取解决方案
        service = EcnKnowledgeService(db_session)
        result = service.extract_solution(ecn.id, auto_extract=True)

        # 验证提取结果
        assert result["ecn_id"] == ecn.id
        assert "更换为更坚固的材料" in result["solution"]
        assert result["estimated_cost"] == 1000.00
        assert result["estimated_days"] == 5
        assert result["ecn_type"] == "DESIGN"
        assert result["root_cause_category"] == "设计缺陷"

    def test_find_similar_ecns(self, db_session: Session):
        """查找相似ECN"""
        # 创建已完成的ECN
        completed_ecns = [
        Ecn(
        ecn_no=f"ECN-02{i}",
        ecn_title=f"测试ECN-{i}",
        ecn_type="DESIGN",
        root_cause_category="设计缺陷",
        solution="解决方案内容",
        status="COMPLETED",
        created_by=1,
        )
        for i in range(3)
        ]
        db_session.add_all(completed_ecns)

        # 创建当前ECN
        current_ecn = Ecn(
        ecn_no="ECN-025",
        ecn_title="当前ECN",
        ecn_type="DESIGN",
        root_cause_category="设计缺陷",
        status="EVALUATING",
        created_by=1,
        )
        db_session.add(current_ecn)
        db_session.commit()

        # 查找相似ECN
        service = EcnKnowledgeService(db_session)
        similar_ecns = service.find_similar_ecns(current_ecn.id, top_n=2)

        # 验证返回结果
        assert len(similar_ecns) <= 2
        # 每个结果应包含必需字段
        for ecn in similar_ecns:
            assert "ecn_id" in ecn
            assert "ecn_no" in ecn
            assert "similarity_score" in ecn
            assert ecn["similarity_score"] >= 0.3

    def test_recommend_solutions(self, db_session: Session):
        """推荐解决方案模板"""
        # 创建ECN
        ecn = Ecn(
        ecn_no="ECN-030",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        root_cause_category="设计缺陷",
        status="EVALUATING",
        created_by=1,
        )
        db_session.add(ecn)

        # 创建解决方案模板
        template1 = EcnSolutionTemplate(
        template_code="TPL-001",
        template_name="设计缺陷解决方案",
        ecn_type="DESIGN",
        root_cause_category="设计缺陷",
        solution_content="标准解决方案：重新设计结构",
        is_active=True,
        )
        template2 = EcnSolutionTemplate(
        template_code="TPL-002",
        template_name="物料问题解决方案",
        ecn_type="MATERIAL",
        root_cause_category="物料缺陷",
        solution_content="更换物料",
        is_active=True,
        )
        db_session.add_all([template1, template2])
        db_session.commit()

        # 推荐解决方案
        service = EcnKnowledgeService(db_session)
        solutions = service.recommend_solutions(ecn.id, top_n=3)

        # 验证返回结果（应匹配类型和原因类别）
        assert len(solutions) > 0
        # 第一个结果应匹配设计缺陷
        assert solutions[0]["root_cause_category"] == "设计缺陷"
        assert "重新设计结构" in solutions[0]["solution_content"]


@pytest.mark.unit
@pytest.mark.integration
class TestEcnWorkflowIntegration:
    """集成测试：ECN完整工作流"""

    def test_ecn_create_to_approval_workflow(self, db_session: Session):
        """ECN创建到审批的完整流程"""
        # 创建必要数据
        project = Project(
        project_code="PJ-100",
        project_name="测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        machine = Machine(
        project_id=project.id,
        machine_code="M-100",
        machine_name="测试设备",
        machine_type="TEST",
        status="DESIGN",
        )
        db_session.add(machine)

        # 创建用户
        engineer = User(
        username="engineer",
        real_name="工程师",
        is_active=True,
        )
        manager = User(
        username="manager",
        real_name="经理",
        is_active=True,
        )
        db_session.add_all([engineer, manager])
        db_session.commit()

        # 创建ECN
        ecn = Ecn(
        ecn_no="ECN-100",
        ecn_title="设计变更ECN",
        ecn_type="DESIGN",
        project_id=project.id,
        machine_id=machine.id,
        status="DRAFT",
        created_by=engineer.id,
        )
        db_session.add(ecn)
        db_session.commit()

        # 创建评估任务（自动分配）
        evaluation = EcnEvaluation(
        ecn_id=ecn.id,
        eval_dept="工程部",
        eval_type="TECHNICAL",
        status="PENDING",
        )
        db_session.add(evaluation)
        db_session.commit()

        # 自动分配评估任务
        assigned_user_id = auto_assign_evaluation(db_session, ecn, evaluation)

        # 验证分配成功
        assert assigned_user_id is not None
        # 更新评估任务的负责人
        evaluation.assigned_to = assigned_user_id
        evaluation.status = "ASSIGNED"
        db_session.add(evaluation)

        # 模拟评估完成
        evaluation.status = "COMPLETED"
        evaluation.eval_result = "APPROVED"
        db_session.add(evaluation)

        # 提交ECN进入审批阶段
        ecn.status = "PENDING_APPROVAL"
        db_session.add(ecn)

        # 创建审批任务
        approval = EcnApproval(
        ecn_id=ecn.id,
        approval_role="项目经理",
        status="PENDING",
        )
        db_session.add(approval)
        db_session.commit()

        # 自动分配审批任务
        approval_assigned = auto_assign_approval(db_session, ecn, approval)

        # 验证分配成功
        assert approval_assigned is not None

        # 验证工作流状态
        db_session.refresh(ecn)
        assert ecn.status == "PENDING_APPROVAL"

    def test_ecn_with_bom_impact_analysis(self, db_session: Session):
        """ECN包含BOM影响分析的完整流程"""
        # 创建必要数据
        project = Project(
        project_code="PJ-101",
        project_name="测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        machine = Machine(
        project_id=project.id,
        machine_code="M-101",
        machine_name="测试设备",
        machine_type="TEST",
        status="DESIGN",
        )
        db_session.add(machine)

        # 创建物料
        material = Material(
        material_code="MAT-101",
        material_name="物料",
        unit_price=Decimal("100.00"),
        )
        db_session.add(material)

        # 创建BOM
        bom_header = BomHeader(
        machine_id=machine.id,
        bom_version="1.0",
        bom_name="测试BOM",
        status="RELEASED",
        is_latest=True,
        created_by=1,
        )
        db_session.add(bom_header)

        bom_item = BomItem(
        bom_id=bom_header.id,
        material_id=material.id,
        quantity=10,
        unit_price=Decimal("100.00"),
        )
        db_session.add(bom_item)

        # 创建ECN
        ecn = Ecn(
        ecn_no="ECN-101",
        ecn_title="物料变更ECN",
        ecn_type="MATERIAL",
        project_id=project.id,
        machine_id=machine.id,
        status="SUBMITTED",
        created_by=1,
        )
        db_session.add(ecn)

        # 创建受影响物料
        affected_mat = EcnAffectedMaterial(
        ecn_id=ecn.id,
        material_id=material.id,
        old_material_code="MAT-101",
        new_material_code="MAT-102",
        cost_delta=Decimal("50.00"),  # 新物料贵50元
        quantity=10,
        )
        db_session.add(affected_mat)
        db_session.commit()

        # 分析BOM影响
        service = EcnBomAnalysisService(db_session)
        impact_result = service.analyze_bom_impact(ecn.id)

        # 验证影响分析
        assert impact_result["has_impact"] is True
        assert impact_result["total_affected_items"] == 1
        # 成本影响 = 50元 × 10 = 500元
        assert impact_result["total_cost_impact"] == 500.0
        assert len(impact_result["bom_impacts"]) > 0

        # 验证BOM影响记录已保存
        bom_impacts = (
        db_session.query(EcnBomImpact).filter(EcnBomImpact.ecn_id == ecn.id).all()
        )
        assert len(bom_impacts) > 0

    def test_ecn_with_knowledge_extraction(self, db_session: Session):
        """ECN完成后提取知识到知识库"""
        # 创建ECN（已完成）
        ecn = Ecn(
        ecn_no="ECN-102",
        ecn_title="测试ECN",
        ecn_type="DESIGN",
        root_cause_category="设计缺陷",
        solution="重新设计结构，增加强度",
        cost_impact=Decimal("2000.00"),
        schedule_impact_days=7,
        status="COMPLETED",
        execution_end=datetime.now(),
        created_by=1,
        )
        db_session.add(ecn)
        db_session.commit()

        # 提取解决方案
        knowledge_service = EcnKnowledgeService(db_session)
        solution = knowledge_service.extract_solution(ecn.id, auto_extract=True)

        # 验证提取的解决方案
        assert solution["ecn_id"] == ecn.id
        assert "重新设计结构" in solution["solution"]
        assert solution["estimated_cost"] == 2000.00
        assert solution["estimated_days"] == 7

        # 查找相似ECN（用于知识推荐）
        similar_ecns = knowledge_service.find_similar_ecns(ecn.id, top_n=3)

        # 应能找到刚创建的ECN（如果数据库中还有其他相似的）
        assert isinstance(similar_ecns, list)
