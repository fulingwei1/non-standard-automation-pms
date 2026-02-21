"""
场景2：项目创建 → 执行 → 验收 完整生命周期

测试项目从启动、计划、执行、监控到交付验收的完整流程
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.project import Project, Customer, ProjectMember, Machine
from app.models.project.core import Milestone
from app.models.acceptance import AcceptanceOrder, AcceptanceTemplate
from app.models.task_center import TaskUnified


class TestProjectFullLifecycle:
    """项目完整生命周期测试"""

    @pytest.fixture
    def project_customer(self, db_session: Session):
        """创建项目客户"""
        customer = Customer(
            customer_code="CUST-PRJ-001",
            customer_name="项目测试客户",
            contact_person="李总",
            contact_phone="13900139000",
            status="ACTIVE",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    def test_01_create_project_from_contract(self, db_session: Session, project_customer: Customer):
        """测试1：从合同创建项目"""
        project = Project(
            project_code="PJ-2026-001",
            project_name="自动化产线改造项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S1",  # 启动阶段
            status="ST01",  # 待启动
            health="H1",  # 健康
            project_type="STANDARD",
            contract_amount=Decimal("2000000.00"),
            plan_start_date=date.today(),
            plan_end_date=date.today() + timedelta(days=180),
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        assert project.id is not None
        assert project.stage == "S1"
        assert project.status == "ST01"

    def test_02_assign_project_team(self, db_session: Session, project_customer: Customer):
        """测试2：分配项目团队"""
        # 创建项目
        project = Project(
            project_code="PJ-2026-002",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S1",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 分配项目经理
        pm = ProjectMember(
            project_id=project.id,
            user_id=1,
            role_code="PM",
            is_lead=True,
            allocation_pct=100,
            created_by=1,
        )
        db_session.add(pm)

        # 分配工程师
        engineer1 = ProjectMember(
            project_id=project.id,
            user_id=2,
            role_code="ENGINEER",
            allocation_pct=80,
            created_by=1,
        )
        db_session.add(engineer1)

        engineer2 = ProjectMember(
            project_id=project.id,
            user_id=3,
            role_code="ENGINEER",
            allocation_pct=60,
            created_by=1,
        )
        db_session.add(engineer2)
        db_session.commit()

        # 验证团队配置
        members = db_session.query(ProjectMember).filter(
            ProjectMember.project_id == project.id
        ).all()
        assert len(members) == 3
        assert sum(1 for m in members if m.is_lead) == 1

    def test_03_create_project_milestones(self, db_session: Session, project_customer: Customer):
        """测试3：创建项目里程碑"""
        project = Project(
            project_code="PJ-2026-003",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S2",  # 计划阶段
            plan_start_date=date.today(),
            plan_end_date=date.today() + timedelta(days=120),
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 创建里程碑
        milestones = [
            {
                "name": "需求确认",
                "plan_date": date.today() + timedelta(days=10),
                "weight": 10,
            },
            {
                "name": "设计评审",
                "plan_date": date.today() + timedelta(days=30),
                "weight": 15,
            },
            {
                "name": "出厂验收",
                "plan_date": date.today() + timedelta(days=90),
                "weight": 30,
            },
            {
                "name": "现场安装",
                "plan_date": date.today() + timedelta(days=110),
                "weight": 25,
            },
            {
                "name": "最终验收",
                "plan_date": date.today() + timedelta(days=120),
                "weight": 20,
            },
        ]

        for i, ms_data in enumerate(milestones):
            milestone = Milestone(
                project_id=project.id,
                milestone_code=f"MS-{project.project_code}-{i+1:02d}",
                milestone_name=ms_data["name"],
                plan_date=ms_data["plan_date"],
                weight=ms_data["weight"],
                status="PENDING",
                created_by=1,
            )
            db_session.add(milestone)
        
        db_session.commit()

        # 验证里程碑
        ms_list = db_session.query(Milestone).filter(
            Milestone.project_id == project.id
        ).all()
        assert len(ms_list) == 5
        assert sum(ms.weight for ms in ms_list) == 100

    def test_04_start_project_execution(self, db_session: Session, project_customer: Customer):
        """测试4：启动项目执行"""
        project = Project(
            project_code="PJ-2026-004",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S2",
            status="ST01",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 项目启动
        project.stage = "S3"  # 执行阶段
        project.status = "ST02"  # 进行中
        project.actual_start_date = date.today()
        db_session.commit()

        assert project.stage == "S3"
        assert project.actual_start_date is not None

    def test_05_create_and_assign_project_tasks(self, db_session: Session, project_customer: Customer):
        """测试5：创建并分配项目任务"""
        project = Project(
            project_code="PJ-2026-005",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S3",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 创建任务
        tasks = [
            TaskUnified(
                task_code=f"TASK-{project.project_code}-001",
                title="设计方案编制",
                project_id=project.id,
                project_code=project.project_code,
                task_type="PROJECT_WBS",
                assignee_id=2,
                status="IN_PROGRESS",
                estimated_hours=40,
                created_by=1,
            ),
            TaskUnified(
                task_code=f"TASK-{project.project_code}-002",
                title="采购清单确认",
                project_id=project.id,
                project_code=project.project_code,
                task_type="PROJECT_WBS",
                assignee_id=3,
                status="TODO",
                estimated_hours=16,
                created_by=1,
            ),
        ]
        
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # 验证任务
        task_list = db_session.query(TaskUnified).filter(
            TaskUnified.project_id == project.id
        ).all()
        assert len(task_list) == 2

    def test_06_update_project_progress(self, db_session: Session, project_customer: Customer):
        """测试6：更新项目进度"""
        project = Project(
            project_code="PJ-2026-006",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S3",
            progress=0,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 第一次更新进度
        project.progress = 25
        db_session.commit()

        # 第二次更新进度
        project.progress = 50
        db_session.commit()

        # 第三次更新进度
        project.progress = 75
        db_session.commit()

        assert project.progress == 75

    def test_07_complete_milestone(self, db_session: Session, project_customer: Customer):
        """测试7：完成里程碑"""
        project = Project(
            project_code="PJ-2026-007",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S3",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 创建里程碑
        milestone = Milestone(
            project_id=project.id,
            milestone_code="MS-TEST-01",
            milestone_name="设计评审",
            plan_date=date.today(),
            status="PENDING",
            created_by=1,
        )
        db_session.add(milestone)
        db_session.commit()

        # 完成里程碑
        milestone.status = "COMPLETED"
        milestone.actual_date = date.today()
        db_session.commit()

        assert milestone.status == "COMPLETED"
        assert milestone.actual_date is not None

    def test_08_create_machines_for_project(self, db_session: Session, project_customer: Customer):
        """测试8：为项目创建设备"""
        project = Project(
            project_code="PJ-2026-008",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S3",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 创建设备
        machines = [
            Machine(
                project_id=project.id,
                machine_code="M-001",
                machine_name="自动化生产线-工位1",
                machine_type="ASSEMBLY",
                status="DESIGN",
            ),
            Machine(
                project_id=project.id,
                machine_code="M-002",
                machine_name="自动化生产线-工位2",
                machine_type="ASSEMBLY",
                status="DESIGN",
            ),
        ]
        
        for machine in machines:
            db_session.add(machine)
        db_session.commit()

        # 验证设备
        machine_list = db_session.query(Machine).filter(
            Machine.project_id == project.id
        ).all()
        assert len(machine_list) == 2

    def test_09_conduct_factory_acceptance(self, db_session: Session, project_customer: Customer):
        """测试9：执行出厂验收（FAT）"""
        project = Project(
            project_code="PJ-2026-009",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S3",
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 创建设备
        machine = Machine(
            project_id=project.id,
            machine_code="M-FAT-001",
            machine_name="测试设备",
            machine_type="ASSEMBLY",
            status="PRODUCTION",
        )
        db_session.add(machine)
        db_session.commit()

        # 获取验收模板
        template = db_session.query(AcceptanceTemplate).filter(
            AcceptanceTemplate.acceptance_type == "FAT"
        ).first()

        if template:
            # 创建验收单
            acceptance = AcceptanceOrder(
                order_no="FAT-2026-001",
                project_id=project.id,
                machine_id=machine.id,
                acceptance_type="FAT",
                template_id=template.id,
                planned_date=date.today(),
                location="工厂",
                status="DRAFT",
                total_items=10,
                created_by=1,
            )
            db_session.add(acceptance)
            db_session.commit()

            # 执行验收
            acceptance.status = "IN_PROGRESS"
            acceptance.actual_date = date.today()
            db_session.commit()

            # 完成验收
            acceptance.status = "PASSED"
            acceptance.passed_items = 10
            db_session.commit()

            assert acceptance.status == "PASSED"

    def test_10_conduct_site_acceptance(self, db_session: Session, project_customer: Customer):
        """测试10：执行现场验收（SAT）"""
        project = Project(
            project_code="PJ-2026-010",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S4",  # 交付阶段
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        machine = Machine(
            project_id=project.id,
            machine_code="M-SAT-001",
            machine_name="测试设备",
            machine_type="ASSEMBLY",
            status="INSTALLED",
        )
        db_session.add(machine)
        db_session.commit()

        template = db_session.query(AcceptanceTemplate).filter(
            AcceptanceTemplate.acceptance_type == "FAT"
        ).first()

        if template:
            acceptance = AcceptanceOrder(
                order_no="SAT-2026-001",
                project_id=project.id,
                machine_id=machine.id,
                acceptance_type="SAT",
                template_id=template.id,
                planned_date=date.today(),
                location="客户现场",
                status="PASSED",
                total_items=15,
                passed_items=15,
                created_by=1,
            )
            db_session.add(acceptance)
            db_session.commit()

            # SAT通过后，设备状态更新
            machine.status = "ACCEPTED"
            db_session.commit()

            assert acceptance.status == "PASSED"
            assert machine.status == "ACCEPTED"

    def test_11_close_project(self, db_session: Session, project_customer: Customer):
        """测试11：项目收尾"""
        project = Project(
            project_code="PJ-2026-011",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S4",
            status="ST02",
            progress=95,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 项目收尾
        project.stage = "S5"  # 收尾阶段
        project.status = "ST03"  # 已完成
        project.progress = 100
        project.actual_end_date = date.today()
        db_session.commit()

        assert project.stage == "S5"
        assert project.status == "ST03"
        assert project.progress == 100

    def test_12_calculate_project_metrics(self, db_session: Session, project_customer: Customer):
        """测试12：计算项目指标"""
        project = Project(
            project_code="PJ-2026-012",
            project_name="测试项目",
            customer_id=project_customer.id,
            customer_name=project_customer.customer_name,
            stage="S5",
            status="ST03",
            contract_amount=Decimal("1000000.00"),
            plan_start_date=date.today() - timedelta(days=120),
            plan_end_date=date.today() - timedelta(days=10),
            actual_start_date=date.today() - timedelta(days=125),
            actual_end_date=date.today(),
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 计算项目指标
        planned_duration = (project.plan_end_date - project.plan_start_date).days
        actual_duration = (project.actual_end_date - project.actual_start_date).days
        schedule_variance = actual_duration - planned_duration

        # 验证指标
        assert planned_duration == 110
        assert actual_duration == 125
        assert schedule_variance == 15  # 延期15天
