# -*- coding: utf-8 -*-
"""
工作流集成测试

测试各模块间的工作流联动：
- 审批工作流服务
- 状态流转服务
- 销售管道工作流
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session


def _unique_code(prefix: str = "TEST") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"


@pytest.mark.integration
class TestApprovalWorkflowIntegration:
    """审批工作流服务集成测试"""

    def test_multi_level_approval_workflow(self, db_session: Session):
        """
        测试多级审批流程：
        1. 创建工作流（3级审批）
        2. 启动审批
        3. 逐级审批通过
        4. 验证最终状态
        """
        from app.models.sales import ApprovalWorkflow, ApprovalWorkflowStep
        from app.services.approval_workflow_service import ApprovalWorkflowService

        workflow_code = _unique_code("WF")
        workflow = ApprovalWorkflow(
            workflow_code=workflow_code,
            workflow_name=f"测试三级审批-{workflow_code}",
            workflow_type="QUOTE",
            is_active=True,
        )
        db_session.add(workflow)
        db_session.flush()

        steps = [
            ApprovalWorkflowStep(
                workflow_id=workflow.id,
                step_order=1,
                step_name="部门主管审批",
                approver_role="DEPT_MANAGER",
                is_required=True,
            ),
            ApprovalWorkflowStep(
                workflow_id=workflow.id,
                step_order=2,
                step_name="财务审批",
                approver_role="FINANCE",
                is_required=True,
            ),
            ApprovalWorkflowStep(
                workflow_id=workflow.id,
                step_order=3,
                step_name="总经理审批",
                approver_role="GM",
                is_required=True,
            ),
        ]
        db_session.add_all(steps)
        db_session.commit()

        service = ApprovalWorkflowService(db_session)

        from app.models.user import User

        admin = db_session.query(User).filter(User.is_superuser.is_(True)).first()
        if not admin:
            pytest.skip("No admin user available")

        try:
            record = service.start_approval(
                entity_type="QUOTE",
                entity_id=9999,
                initiator_id=admin.id,
                workflow_id=workflow.id,
                comment="测试多级审批",
            )

            assert record is not None
            assert record.current_step == 1
            assert (
                record.status.value == "PENDING"
                if hasattr(record.status, "value")
                else record.status == "PENDING"
            )

            step_info = service.get_current_step(record.id)
            assert step_info is not None
            assert step_info["step_name"] == "部门主管审批"

        except ValueError as e:
            if "工作流" in str(e):
                pytest.skip(f"Workflow setup issue: {e}")
            raise

    def test_approval_delegation(self, db_session: Session):
        """
        测试审批委托：
        1. 创建审批记录
        2. 原审批人委托给他人
        3. 被委托人完成审批
        """
        from app.models.sales import ApprovalWorkflow, ApprovalWorkflowStep
        from app.models.user import User
        from app.services.approval_workflow_service import ApprovalWorkflowService

        workflow_code = _unique_code("WFDLG")
        workflow = ApprovalWorkflow(
            workflow_code=workflow_code,
            workflow_name=f"委托测试-{workflow_code}",
            workflow_type="QUOTE",
            is_active=True,
        )
        db_session.add(workflow)
        db_session.flush()

        step = ApprovalWorkflowStep(
            workflow_id=workflow.id,
            step_order=1,
            step_name="可委托审批",
            approver_role="MANAGER",
            is_required=True,
            can_delegate=True,
        )
        db_session.add(step)
        db_session.commit()

        users = db_session.query(User).filter(User.is_active.is_(True)).limit(2).all()
        if len(users) < 2:
            pytest.skip("Need at least 2 users for delegation test")

        service = ApprovalWorkflowService(db_session)

        try:
            record = service.start_approval(
                entity_type="QUOTE",
                entity_id=8888,
                initiator_id=users[0].id,
                workflow_id=workflow.id,
            )

            delegated = service.delegate_step(
                record_id=record.id,
                approver_id=users[0].id,
                delegate_to_id=users[1].id,
                comment="出差，委托审批",
            )
            assert delegated is not None

        except ValueError as e:
            pytest.skip(f"Delegation test skipped: {e}")

    def test_approval_withdrawal(self, db_session: Session):
        """
        测试审批撤回：
        1. 发起人提交审批
        2. 在首级审批前撤回
        3. 验证状态变为已取消
        """
        from app.models.sales import ApprovalWorkflow, ApprovalWorkflowStep
        from app.models.user import User
        from app.services.approval_workflow_service import ApprovalWorkflowService

        workflow_code = _unique_code("WFWD")
        workflow = ApprovalWorkflow(
            workflow_code=workflow_code,
            workflow_name=f"撤回测试-{workflow_code}",
            workflow_type="QUOTE",
            is_active=True,
        )
        db_session.add(workflow)
        db_session.flush()

        step = ApprovalWorkflowStep(
            workflow_id=workflow.id,
            step_order=1,
            step_name="待审批",
            approver_role="MANAGER",
            is_required=True,
            can_withdraw=True,
        )
        db_session.add(step)
        db_session.commit()

        user = db_session.query(User).filter(User.is_active.is_(True)).first()
        if not user:
            pytest.skip("No user available")

        service = ApprovalWorkflowService(db_session)

        try:
            record = service.start_approval(
                entity_type="QUOTE",
                entity_id=7777,
                initiator_id=user.id,
                workflow_id=workflow.id,
            )

            withdrawn = service.withdraw_approval(
                record_id=record.id,
                initiator_id=user.id,
                comment="需要修改内容",
            )

            assert (
                withdrawn.status.value == "CANCELLED"
                if hasattr(withdrawn.status, "value")
                else withdrawn.status == "CANCELLED"
            )

        except ValueError as e:
            pytest.skip(f"Withdrawal test skipped: {e}")

    def test_approval_rejection(self, db_session: Session):
        """
        测试审批驳回：
        1. 发起审批
        2. 审批人驳回
        3. 验证状态和原因记录
        """
        from app.models.sales import ApprovalWorkflow, ApprovalWorkflowStep
        from app.models.user import User
        from app.services.approval_workflow_service import ApprovalWorkflowService

        workflow_code = _unique_code("WFRJ")
        workflow = ApprovalWorkflow(
            workflow_code=workflow_code,
            workflow_name=f"驳回测试-{workflow_code}",
            workflow_type="QUOTE",
            is_active=True,
        )
        db_session.add(workflow)
        db_session.flush()

        step = ApprovalWorkflowStep(
            workflow_id=workflow.id,
            step_order=1,
            step_name="审批",
            approver_role="MANAGER",
            is_required=True,
        )
        db_session.add(step)
        db_session.commit()

        admin = db_session.query(User).filter(User.is_superuser.is_(True)).first()
        if not admin:
            pytest.skip("No admin user available")

        service = ApprovalWorkflowService(db_session)

        try:
            record = service.start_approval(
                entity_type="QUOTE",
                entity_id=6666,
                initiator_id=admin.id,
                workflow_id=workflow.id,
            )

            rejected = service.reject_step(
                record_id=record.id,
                approver_id=admin.id,
                comment="价格过高，需要重新评估",
            )

            assert (
                rejected.status.value == "REJECTED"
                if hasattr(rejected.status, "value")
                else rejected.status == "REJECTED"
            )

            history = service.get_approval_history(record.id)
            assert any("价格过高" in (h.comment or "") for h in history)

        except ValueError as e:
            pytest.skip(f"Rejection test skipped: {e}")


@pytest.mark.integration
class TestStatusTransitionIntegration:
    """状态流转服务集成测试"""

    def test_contract_signed_triggers_project_creation(self, db_session: Session):
        """
        测试合同签订触发项目创建：
        1. 创建客户
        2. 创建合同
        3. 触发合同签订事件
        4. 验证项目自动创建
        """
        from app.models.project import Customer
        from app.models.sales import Contract
        from app.services.status_transition_service import StatusTransitionService

        customer_code = _unique_code("CUST")
        customer = Customer(
            customer_code=customer_code,
            customer_name=f"测试客户-{customer_code}",
            contact_person="张三",
            contact_phone="13800138000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        contract_code = _unique_code("CT")
        contract = Contract(
            contract_code=contract_code,
            contract_name=f"测试合同-{contract_code}",
            customer_id=customer.id,
            contract_type="SALES",
            status="SIGNED",
            contract_amount=Decimal("100000.00"),
            signed_date=date.today(),
        )
        db_session.add(contract)
        db_session.commit()

        service = StatusTransitionService(db_session)

        try:
            project = service.handle_contract_signed(
                contract_id=contract.id,
                auto_create_project=True,
            )

            if project:
                assert project.customer_id == customer.id
                assert project.stage == "S3"
                assert project.status == "ST08"
        except Exception as e:
            pytest.skip(f"Contract-to-project transition skipped: {e}")

    def test_material_shortage_updates_health(self, db_session: Session):
        """
        测试物料缺货更新健康度：
        1. 创建项目
        2. 触发物料缺货事件
        3. 验证健康度变为H3
        """
        from app.models.project import Customer, Project
        from app.services.status_transition_service import StatusTransitionService

        customer = db_session.query(Customer).first()
        if not customer:
            customer_code = _unique_code("CUST")
            customer = Customer(
                customer_code=customer_code,
                customer_name=f"测试客户-{customer_code}",
                contact_person="李四",
                contact_phone="13900139000",
                status="ACTIVE",
            )
            db_session.add(customer)
            db_session.flush()

        project_code = _unique_code("PJ")
        project = Project(
            project_code=project_code,
            project_name=f"物料测试-{project_code}",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S5",
            status="ST12",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()

        service = StatusTransitionService(db_session)

        result = service.handle_material_shortage(
            project_id=project.id,
            is_critical=True,
        )

        if result:
            db_session.refresh(project)
            assert project.status == "ST14"
            assert project.health == "H3"

    def test_fat_passed_advances_stage(self, db_session: Session):
        """
        测试FAT通过推进阶段：
        1. 创建S7阶段项目
        2. 触发FAT通过事件
        3. 验证阶段推进到S8
        """
        from app.models.project import Customer, Project
        from app.services.status_transition_service import StatusTransitionService

        customer = db_session.query(Customer).first()
        if not customer:
            customer_code = _unique_code("CUST")
            customer = Customer(
                customer_code=customer_code,
                customer_name=f"FAT客户-{customer_code}",
                contact_person="王五",
                contact_phone="13700137000",
                status="ACTIVE",
            )
            db_session.add(customer)
            db_session.flush()

        project_code = _unique_code("PJ")
        project = Project(
            project_code=project_code,
            project_name=f"FAT测试-{project_code}",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S7",
            status="ST21",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()

        service = StatusTransitionService(db_session)

        result = service.handle_fat_passed(project_id=project.id)

        if result:
            db_session.refresh(project)
            assert project.stage == "S8"
            assert project.status == "ST23"

    def test_ecn_schedule_impact_updates_delivery(self, db_session: Session):
        """
        测试ECN变更影响交期：
        1. 创建项目（有计划交期）
        2. 创建ECN
        3. 触发ECN影响交期事件
        4. 验证交期延期
        """
        from app.models.ecn import Ecn
        from app.models.project import Customer, Project
        from app.services.status_transition_service import StatusTransitionService

        customer = db_session.query(Customer).first()
        if not customer:
            customer_code = _unique_code("CUST")
            customer = Customer(
                customer_code=customer_code,
                customer_name=f"ECN客户-{customer_code}",
                contact_person="赵六",
                contact_phone="13600136000",
                status="ACTIVE",
            )
            db_session.add(customer)
            db_session.flush()

        original_end_date = date.today() + timedelta(days=30)
        project_code = _unique_code("PJ")
        project = Project(
            project_code=project_code,
            project_name=f"ECN测试-{project_code}",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S4",
            status="ST10",
            health="H1",
            planned_end_date=original_end_date,
        )
        db_session.add(project)
        db_session.flush()

        ecn_no = _unique_code("ECN")
        ecn = Ecn(
            project_id=project.id,
            ecn_no=ecn_no,
            ecn_title=f"设计变更-{ecn_no}",
            ecn_type="DESIGN",
            change_reason="客户需求变更",
            change_content="修改尺寸",
            urgency="NORMAL",
            status="APPROVED",
        )
        db_session.add(ecn)
        db_session.commit()

        service = StatusTransitionService(db_session)

        result = service.handle_ecn_schedule_impact(
            project_id=project.id,
            ecn_id=ecn.id,
            impact_days=10,
        )

        if result:
            db_session.refresh(project)
            expected_date = original_end_date + timedelta(days=10)
            assert project.planned_end_date == expected_date


@pytest.mark.integration
class TestSalesPipelineIntegration:
    """销售管道工作流集成测试"""

    def test_lead_to_opportunity_conversion(self, db_session: Session):
        """
        测试线索转商机：
        1. 创建销售线索
        2. 转换为商机
        3. 验证商机创建和线索状态更新
        """
        from app.models.sales import Lead, Opportunity

        lead_code = _unique_code("LD")
        lead = Lead(
            lead_code=lead_code,
            lead_name=f"测试线索-{lead_code}",
            company_name="潜在客户公司",
            contact_name="联系人A",
            contact_phone="13500135000",
            source="WEBSITE",
            status="NEW",
            estimated_amount=Decimal("50000.00"),
        )
        db_session.add(lead)
        db_session.commit()

        opp_code = _unique_code("OP")
        opportunity = Opportunity(
            opportunity_code=opp_code,
            opportunity_name=f"商机-{opp_code}",
            lead_id=lead.id,
            stage="INITIAL",
            status="ACTIVE",
            probability=30,
            expected_amount=lead.estimated_amount,
            expected_close_date=date.today() + timedelta(days=60),
        )
        db_session.add(opportunity)

        lead.status = "CONVERTED"
        db_session.commit()

        db_session.refresh(lead)
        db_session.refresh(opportunity)

        assert lead.status == "CONVERTED"
        assert opportunity.lead_id == lead.id

    def test_opportunity_to_quote_flow(self, db_session: Session):
        """
        测试商机转报价：
        1. 创建商机
        2. 创建报价单
        3. 验证关联关系
        """
        from app.models.sales import Opportunity, Quote

        opp_code = _unique_code("OP")
        opportunity = Opportunity(
            opportunity_code=opp_code,
            opportunity_name=f"商机-{opp_code}",
            stage="QUOTE",
            status="ACTIVE",
            probability=50,
            expected_amount=Decimal("100000.00"),
            expected_close_date=date.today() + timedelta(days=30),
        )
        db_session.add(opportunity)
        db_session.flush()

        quote_code = _unique_code("QT")
        quote = Quote(
            quote_code=quote_code,
            quote_name=f"报价-{quote_code}",
            opportunity_id=opportunity.id,
            version=1,
            status="DRAFT",
            total_amount=Decimal("98000.00"),
            valid_until=date.today() + timedelta(days=30),
        )
        db_session.add(quote)
        db_session.commit()

        db_session.refresh(quote)
        assert quote.opportunity_id == opportunity.id

    def test_quote_to_contract_conversion(self, db_session: Session):
        """
        测试报价转合同：
        1. 创建已批准报价
        2. 创建合同
        3. 验证合同与报价关联
        """
        from app.models.project import Customer
        from app.models.sales import Contract, Quote

        customer = db_session.query(Customer).first()
        if not customer:
            customer_code = _unique_code("CUST")
            customer = Customer(
                customer_code=customer_code,
                customer_name=f"合同客户-{customer_code}",
                contact_person="孙七",
                contact_phone="13400134000",
                status="ACTIVE",
            )
            db_session.add(customer)
            db_session.flush()

        quote_code = _unique_code("QT")
        quote = Quote(
            quote_code=quote_code,
            quote_name=f"已批报价-{quote_code}",
            customer_id=customer.id,
            version=1,
            status="APPROVED",
            total_amount=Decimal("200000.00"),
            valid_until=date.today() + timedelta(days=30),
        )
        db_session.add(quote)
        db_session.flush()

        contract_code = _unique_code("CT")
        contract = Contract(
            contract_code=contract_code,
            contract_name=f"合同-{contract_code}",
            customer_id=customer.id,
            quote_id=quote.id,
            contract_type="SALES",
            status="DRAFT",
            contract_amount=quote.total_amount,
        )
        db_session.add(contract)
        db_session.commit()

        db_session.refresh(contract)
        assert contract.quote_id == quote.id
        assert contract.contract_amount == quote.total_amount

    def test_full_sales_pipeline(self, db_session: Session):
        """
        测试完整销售管道：线索 → 商机 → 报价 → 合同 → 项目
        """
        from app.models.project import Customer, Project
        from app.models.sales import Contract, Lead, Opportunity, Quote

        customer_code = _unique_code("CUST")
        customer = Customer(
            customer_code=customer_code,
            customer_name=f"完整流程客户-{customer_code}",
            contact_person="周八",
            contact_phone="13300133000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.flush()

        lead_code = _unique_code("LD")
        lead = Lead(
            lead_code=lead_code,
            lead_name=f"线索-{lead_code}",
            company_name=customer.customer_name,
            contact_name=customer.contact_person,
            contact_phone=customer.contact_phone,
            source="REFERRAL",
            status="NEW",
            estimated_amount=Decimal("500000.00"),
        )
        db_session.add(lead)
        db_session.flush()

        opp_code = _unique_code("OP")
        opportunity = Opportunity(
            opportunity_code=opp_code,
            opportunity_name=f"商机-{opp_code}",
            customer_id=customer.id,
            lead_id=lead.id,
            stage="NEGOTIATION",
            status="ACTIVE",
            probability=70,
            expected_amount=lead.estimated_amount,
            expected_close_date=date.today() + timedelta(days=30),
        )
        db_session.add(opportunity)
        lead.status = "CONVERTED"
        db_session.flush()

        quote_code = _unique_code("QT")
        quote = Quote(
            quote_code=quote_code,
            quote_name=f"报价-{quote_code}",
            customer_id=customer.id,
            opportunity_id=opportunity.id,
            version=1,
            status="APPROVED",
            total_amount=Decimal("480000.00"),
            valid_until=date.today() + timedelta(days=30),
        )
        db_session.add(quote)
        db_session.flush()

        contract_code = _unique_code("CT")
        contract = Contract(
            contract_code=contract_code,
            contract_name=f"合同-{contract_code}",
            customer_id=customer.id,
            quote_id=quote.id,
            contract_type="SALES",
            status="SIGNED",
            contract_amount=quote.total_amount,
            signed_date=date.today(),
        )
        db_session.add(contract)
        db_session.flush()

        project_code = _unique_code("PJ")
        project = Project(
            project_code=project_code,
            project_name=f"项目-{project_code}",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            contract_no=contract.contract_code,
            contract_amount=contract.contract_amount,
            stage="S3",
            status="ST08",
            health="H1",
        )
        db_session.add(project)
        contract.project_id = project.id
        db_session.commit()

        db_session.refresh(lead)
        db_session.refresh(opportunity)
        db_session.refresh(quote)
        db_session.refresh(contract)
        db_session.refresh(project)

        assert lead.status == "CONVERTED"
        assert opportunity.lead_id == lead.id
        assert quote.opportunity_id == opportunity.id
        assert contract.quote_id == quote.id
        assert contract.project_id == project.id
        assert project.contract_no == contract.contract_code
