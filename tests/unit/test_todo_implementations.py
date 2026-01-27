# -*- coding: utf-8 -*-
"""
TODO实现功能的单元测试

测试内容：
1. 任务负责人自动分配（根据角色）
2. 设备保养通知接收人逻辑
3. 项目评价等级阈值配置
4. 工时统计模块集成
5. 财务数据查询
6. 节假日服务
7. 时薪配置服务

运行测试：
    pytest tests/unit/test_todo_implementations.py -v
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.models.user import User, Role, UserRole
from app.models.project import Project, ProjectCost
from app.models.production import Equipment, Workshop
from app.models.timesheet import Timesheet
from app.models.project_evaluation import ProjectEvaluationDimension
from app.models.enums import ProjectEvaluationLevelEnum
from app.models.holiday import Holiday, HolidayService
from app.models.hourly_rate import HourlyRateConfig


@pytest.mark.unit
class TestTaskOwnerAssignment:
    """测试任务负责人自动分配功能"""

    def test_assign_owner_by_role_code(self, db_session: Session):
        """测试根据角色编码分配任务负责人"""
        # 创建角色
        role = Role(
        role_code="ENGINEER",
        role_name="工程师",
        is_active=True
        )
        db_session.add(role)
        db_session.flush()

        # 创建用户
        user = User(
        username="test_engineer",
        hashed_password="test",
        is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # 创建用户角色关联
        user_role = UserRole(
        user_id=user.id,
        role_id=role.id
        )
        db_session.add(user_role)
        db_session.commit()

        # 测试查询逻辑
        found_role = db_session.query(Role).filter(
        Role.role_code == "ENGINEER",
        Role.is_active == True
        ).first()

        assert found_role is not None
        assert found_role.role_code == "ENGINEER"

        # 查找拥有该角色的用户
        found_user_role = db_session.query(UserRole).filter(
        UserRole.role_id == found_role.id
        ).join(User).filter(User.is_active == True).first()

        assert found_user_role is not None
        assert found_user_role.user_id == user.id

    def test_no_matching_role(self, db_session: Session):
        """测试没有匹配角色的情况"""
        found_role = db_session.query(Role).filter(
        Role.role_code == "NON_EXISTENT_ROLE",
        Role.is_active == True
        ).first()

        assert found_role is None


@pytest.mark.unit
class TestEquipmentMaintenanceRecipients:
    """测试设备保养通知接收人逻辑"""

    def test_get_workshop_manager(self, db_session: Session):
        """测试获取车间主管作为接收人"""
        # 创建车间主管用户
        manager = User(
        username="workshop_manager",
        hashed_password="test",
        is_active=True
        )
        db_session.add(manager)
        db_session.flush()

        # 创建车间
        workshop = Workshop(
        workshop_code="WS001",
        workshop_name="装配车间",
        workshop_type="ASSEMBLY",
        manager_id=manager.id,
        is_active=True
        )
        db_session.add(workshop)
        db_session.flush()

        # 创建设备
        equipment = Equipment(
        equipment_code="EQ001",
        equipment_name="测试设备",
        workshop_id=workshop.id,
        is_active=True,
        next_maintenance_date=date.today()
        )
        db_session.add(equipment)
        db_session.commit()

        # 测试获取车间主管
        found_workshop = db_session.query(Workshop).filter(
        Workshop.id == equipment.workshop_id
        ).first()

        assert found_workshop is not None
        assert found_workshop.manager_id == manager.id

        found_manager = db_session.query(User).filter(
        User.id == found_workshop.manager_id,
        User.is_active == True
        ).first()

        assert found_manager is not None
        assert found_manager.username == "workshop_manager"

    def test_equipment_without_workshop(self, db_session: Session):
        """测试设备没有关联车间的情况"""
        equipment = Equipment(
        equipment_code="EQ002",
        equipment_name="独立设备",
        workshop_id=None,
        is_active=True
        )
        db_session.add(equipment)
        db_session.commit()

        # 无车间时返回None
        assert equipment.workshop_id is None


@pytest.mark.unit
class TestProjectEvaluationLevelThresholds:
    """测试项目评价等级阈值配置"""

    def test_get_default_thresholds(self, db_session: Session):
        """测试获取默认阈值"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        service = ProjectEvaluationService(db_session)
        thresholds = service.get_level_thresholds()

        assert thresholds[ProjectEvaluationLevelEnum.S] == Decimal('90')
        assert thresholds[ProjectEvaluationLevelEnum.A] == Decimal('80')
        assert thresholds[ProjectEvaluationLevelEnum.B] == Decimal('70')
        assert thresholds[ProjectEvaluationLevelEnum.C] == Decimal('60')
        assert thresholds[ProjectEvaluationLevelEnum.D] == Decimal('0')

    def test_get_custom_thresholds_from_config(self, db_session: Session):
        """测试从配置表获取自定义阈值"""
        # 创建等级配置
        level_config = ProjectEvaluationDimension(
        dimension_code="LEVEL_CONFIG",
        dimension_name="等级阈值配置",
        dimension_type="CONFIG",
        scoring_rules={
        "thresholds": {
        "S": 95,
        "A": 85,
        "B": 75,
        "C": 65,
        "D": 0
        }
        },
        is_active=True
        )
        db_session.add(level_config)
        db_session.commit()

        from app.services.project_evaluation_service import ProjectEvaluationService

        service = ProjectEvaluationService(db_session)
        thresholds = service.get_level_thresholds()

        assert thresholds[ProjectEvaluationLevelEnum.S] == Decimal('95')
        assert thresholds[ProjectEvaluationLevelEnum.A] == Decimal('85')
        assert thresholds[ProjectEvaluationLevelEnum.B] == Decimal('75')
        assert thresholds[ProjectEvaluationLevelEnum.C] == Decimal('65')


@pytest.mark.unit
class TestWorkloadScoreCalculation:
    """测试工作量得分计算"""

    def test_calculate_score_from_timesheet(self, db_session: Session):
        """测试从工时记录计算工作量得分"""
        # 创建项目
        project = Project(
        project_code="TEST-WL-001",
        project_name="工作量测试项目",
        customer_name="测试客户",
        stage="S4",
        health="H1",
        is_active=True
        )
        db_session.add(project)
        db_session.flush()

        # 创建工时记录（总计160小时 = 20人天，应该得9.5分）
        for i in range(8):
            timesheet = Timesheet(
            user_id=1,
            project_id=project.id,
            work_date=date.today(),
            hours=Decimal('20'),  # 每条20小时
            status='APPROVED'
            )
            db_session.add(timesheet)
            db_session.commit()

            from app.services.project_evaluation_service import ProjectEvaluationService

            service = ProjectEvaluationService(db_session)
            score = service.auto_calculate_workload_score(project)

            # 160小时 / 8 = 20人天，< 200人天，应该得9.5分
            assert score == Decimal('9.5')

    def test_calculate_score_large_workload(self, db_session: Session):
        """测试大工作量项目得分"""
        project = Project(
        project_code="TEST-WL-002",
        project_name="大工作量项目",
        customer_name="测试客户",
        stage="S4",
        health="H1",
        is_active=True
        )
        db_session.add(project)
        db_session.flush()

        # 创建工时记录（总计8800小时 = 1100人天，应该得2分）
        for i in range(88):
            timesheet = Timesheet(
            user_id=1,
            project_id=project.id,
            work_date=date.today(),
            hours=Decimal('100'),
            status='APPROVED'
            )
            db_session.add(timesheet)
            db_session.commit()

            from app.services.project_evaluation_service import ProjectEvaluationService

            service = ProjectEvaluationService(db_session)
            score = service.auto_calculate_workload_score(project)

            # 8800小时 / 8 = 1100人天，> 1000人天，应该得2分
            assert score == Decimal('2.0')

    def test_no_timesheet_returns_none(self, db_session: Session):
        """测试无工时记录时返回None"""
        project = Project(
        project_code="TEST-WL-003",
        project_name="无工时项目",
        customer_name="测试客户",
        stage="S4",
        health="H1",
        is_active=True
        )
        db_session.add(project)
        db_session.commit()

        from app.services.project_evaluation_service import ProjectEvaluationService

        service = ProjectEvaluationService(db_session)
        score = service.auto_calculate_workload_score(project)

        assert score is None


@pytest.mark.unit
class TestFinancialMetricsCalculation:
    """测试财务指标计算"""

    def test_calculate_total_cost(self, db_session: Session):
        """测试计算总成本"""
        # 创建项目
        project = Project(
        project_code="TEST-FIN-001",
        project_name="财务测试项目",
        customer_name="测试客户",
        contract_amount=Decimal('1000000'),
        stage="S4",
        health="H1",
        is_active=True
        )
        db_session.add(project)
        db_session.flush()

        # 创建成本记录
        costs = [
        ProjectCost(
        project_id=project.id,
        cost_type="MATERIAL",
        cost_category="材料费",
        amount=Decimal('200000'),
        cost_date=date.today()
        ),
        ProjectCost(
        project_id=project.id,
        cost_type="LABOR",
        cost_category="人工费",
        amount=Decimal('150000'),
        cost_date=date.today()
        ),
        ]
        for cost in costs:
            db_session.add(cost)
            db_session.commit()

            # 查询总成本
            from sqlalchemy import func
            total_cost = db_session.query(func.sum(ProjectCost.amount)).filter(
            ProjectCost.project_id == project.id
            ).scalar()

            assert total_cost == Decimal('350000')

    def test_calculate_profit_margin(self):
        """测试计算毛利率"""
        revenue = 1000000.0
        cost = 700000.0
        profit = revenue - cost

        gross_margin_rate = 0.0
        if revenue > 0:
            gross_margin_rate = round((profit / revenue) * 100, 2)

            assert gross_margin_rate == 30.0

    def test_zero_revenue_handling(self):
        """测试零收入情况的处理"""
        revenue = 0.0
        cost = 100000.0

        gross_margin_rate = 0.0
        if revenue > 0:
            gross_margin_rate = round(((revenue - cost) / revenue) * 100, 2)

            # 零收入时毛利率应为0，避免除零错误
            assert gross_margin_rate == 0.0


@pytest.mark.unit
class TestHolidayService:
    """测试节假日服务"""

    def test_is_holiday(self, db_session: Session):
        """测试节假日判断"""
        # 创建节假日
        holiday = Holiday(
        holiday_date=date(2025, 1, 1),
        year=2025,
        holiday_type="HOLIDAY",
        name="元旦",
        is_active=True
        )
        db_session.add(holiday)
        db_session.commit()

        # 测试节假日判断
        result = HolidayService.is_holiday(db_session, date(2025, 1, 1))
        assert result is True

        # 测试非节假日
        result = HolidayService.is_holiday(db_session, date(2025, 1, 2))
        assert result is False

    def test_is_workday_override(self, db_session: Session):
        """测试调休工作日（周末需要上班）"""
        # 创建调休工作日（假设2025-01-25是周六，但需要调休上班）
        workday = Holiday(
        holiday_date=date(2025, 1, 25),
        year=2025,
        holiday_type="WORKDAY",
        name="春节调休",
        is_active=True
        )
        db_session.add(workday)
        db_session.commit()

        # 测试调休工作日判断
        result = HolidayService.is_workday(db_session, date(2025, 1, 25))
        assert result is True

        # 测试普通日期不是调休
        result = HolidayService.is_workday(db_session, date(2025, 1, 20))
        assert result is False

    def test_get_work_type_holiday(self, db_session: Session):
        """测试获取工作类型 - 节假日"""
        holiday = Holiday(
        holiday_date=date(2025, 10, 1),
        year=2025,
        holiday_type="HOLIDAY",
        name="国庆节",
        is_active=True
        )
        db_session.add(holiday)
        db_session.commit()

        work_type = HolidayService.get_work_type(db_session, date(2025, 10, 1))
        assert work_type == "HOLIDAY"

    def test_get_work_type_workday_override(self, db_session: Session):
        """测试获取工作类型 - 调休工作日（周末变工作日）"""
        # 2025-01-26是周日，但配置为调休工作日
        workday = Holiday(
        holiday_date=date(2025, 1, 26),
        year=2025,
        holiday_type="WORKDAY",
        name="春节调休上班",
        is_active=True
        )
        db_session.add(workday)
        db_session.commit()

        work_type = HolidayService.get_work_type(db_session, date(2025, 1, 26))
        assert work_type == "NORMAL"

    def test_get_work_type_weekend(self, db_session: Session):
        """测试获取工作类型 - 普通周末"""
        # 2025-01-18是周六，没有特殊配置
        work_type = HolidayService.get_work_type(db_session, date(2025, 1, 18))
        assert work_type == "WEEKEND"

    def test_get_work_type_normal(self, db_session: Session):
        """测试获取工作类型 - 普通工作日"""
        # 2025-01-20是周一
        work_type = HolidayService.get_work_type(db_session, date(2025, 1, 20))
        assert work_type == "NORMAL"

    def test_get_holiday_name(self, db_session: Session):
        """测试获取节假日名称"""
        holiday = Holiday(
        holiday_date=date(2025, 5, 1),
        year=2025,
        holiday_type="HOLIDAY",
        name="劳动节",
        is_active=True
        )
        db_session.add(holiday)
        db_session.commit()

        name = HolidayService.get_holiday_name(db_session, date(2025, 5, 1))
        assert name == "劳动节"

        # 非节假日返回None
        name = HolidayService.get_holiday_name(db_session, date(2025, 5, 2))
        assert name is None


@pytest.mark.unit
class TestHourlyRateService:
    """测试时薪配置服务"""

    def test_get_user_personal_rate(self, db_session: Session):
        """测试获取用户个人时薪配置"""
        from app.services.hourly_rate_service import HourlyRateService

        # 创建用户
        user = User(
        username="test_user_rate",
        hashed_password="test",
        is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # 创建用户个人时薪配置
        config = HourlyRateConfig(
        config_type="USER",
        user_id=user.id,
        hourly_rate=Decimal("150"),
        is_active=True
        )
        db_session.add(config)
        db_session.commit()

        # 获取时薪
        rate = HourlyRateService.get_user_hourly_rate(db_session, user.id)
        assert rate == Decimal("150")

    def test_get_role_based_rate(self, db_session: Session):
        """测试获取角色级别时薪配置"""
        from app.services.hourly_rate_service import HourlyRateService

        # 创建角色
        role = Role(
        role_code="SENIOR_ENGINEER",
        role_name="高级工程师",
        is_active=True
        )
        db_session.add(role)
        db_session.flush()

        # 创建用户
        user = User(
        username="test_senior_eng",
        hashed_password="test",
        is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # 创建用户角色关联
        user_role = UserRole(
        user_id=user.id,
        role_id=role.id
        )
        db_session.add(user_role)

        # 创建角色时薪配置
        config = HourlyRateConfig(
        config_type="ROLE",
        role_id=role.id,
        hourly_rate=Decimal("120"),
        is_active=True
        )
        db_session.add(config)
        db_session.commit()

        # 获取时薪（用户没有个人配置，应该使用角色配置）
        rate = HourlyRateService.get_user_hourly_rate(db_session, user.id)
        assert rate == Decimal("120")

    def test_user_rate_priority_over_role(self, db_session: Session):
        """测试用户个人配置优先于角色配置"""
        from app.services.hourly_rate_service import HourlyRateService

        # 创建角色
        role = Role(
        role_code="DEVELOPER",
        role_name="开发工程师",
        is_active=True
        )
        db_session.add(role)
        db_session.flush()

        # 创建用户
        user = User(
        username="test_dev",
        hashed_password="test",
        is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # 创建用户角色关联
        user_role = UserRole(
        user_id=user.id,
        role_id=role.id
        )
        db_session.add(user_role)

        # 创建角色时薪配置（100元）
        role_config = HourlyRateConfig(
        config_type="ROLE",
        role_id=role.id,
        hourly_rate=Decimal("100"),
        is_active=True
        )
        db_session.add(role_config)

        # 创建用户个人时薪配置（180元）
        user_config = HourlyRateConfig(
        config_type="USER",
        user_id=user.id,
        hourly_rate=Decimal("180"),
        is_active=True
        )
        db_session.add(user_config)
        db_session.commit()

        # 获取时薪 - 应该返回用户个人配置的180元
        rate = HourlyRateService.get_user_hourly_rate(db_session, user.id)
        assert rate == Decimal("180")

    def test_default_rate_fallback(self, db_session: Session):
        """测试默认时薪配置兜底"""
        from app.services.hourly_rate_service import HourlyRateService

        # 创建用户（没有任何时薪配置）
        user = User(
        username="test_no_config",
        hashed_password="test",
        is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # 创建默认时薪配置
        default_config = HourlyRateConfig(
        config_type="DEFAULT",
        hourly_rate=Decimal("80"),
        is_active=True
        )
        db_session.add(default_config)
        db_session.commit()

        # 获取时薪 - 应该返回默认配置的80元
        rate = HourlyRateService.get_user_hourly_rate(db_session, user.id)
        assert rate == Decimal("80")

    def test_hardcoded_default_fallback(self, db_session: Session):
        """测试硬编码默认值兜底（无任何配置）"""
        from app.services.hourly_rate_service import HourlyRateService

        # 创建用户（没有任何时薪配置，数据库也没有默认配置）
        user = User(
        username="test_hardcoded",
        hashed_password="test",
        is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 获取时薪 - 应该返回硬编码默认值100元
        rate = HourlyRateService.get_user_hourly_rate(db_session, user.id)
        assert rate == HourlyRateService.DEFAULT_HOURLY_RATE
        assert rate == Decimal("100")

    def test_batch_get_users_hourly_rates(self, db_session: Session):
        """测试批量获取多个用户时薪"""
        from app.services.hourly_rate_service import HourlyRateService

        # 创建两个用户
        user1 = User(username="batch_user1", hashed_password="test", is_active=True)
        user2 = User(username="batch_user2", hashed_password="test", is_active=True)
        db_session.add_all([user1, user2])
        db_session.flush()

        # 用户1有个人配置
        config1 = HourlyRateConfig(
        config_type="USER",
        user_id=user1.id,
        hourly_rate=Decimal("200"),
        is_active=True
        )
        db_session.add(config1)
        db_session.commit()

        # 批量获取
        rates = HourlyRateService.get_users_hourly_rates(
        db_session, [user1.id, user2.id]
        )

        assert rates[user1.id] == Decimal("200")
        assert rates[user2.id] == Decimal("100")  # 默认值

    def test_rate_effective_date(self, db_session: Session):
        """测试时薪配置的生效日期"""
        from app.services.hourly_rate_service import HourlyRateService

        # 创建用户
        user = User(
        username="test_date_user",
        hashed_password="test",
        is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # 创建未来生效的时薪配置
        future_config = HourlyRateConfig(
        config_type="USER",
        user_id=user.id,
        hourly_rate=Decimal("250"),
        effective_date=date.today() + timedelta(days=30),
        is_active=True
        )
        db_session.add(future_config)

        # 创建当前有效的时薪配置
        current_config = HourlyRateConfig(
        config_type="USER",
        user_id=user.id,
        hourly_rate=Decimal("150"),
        effective_date=date.today() - timedelta(days=30),
        is_active=True
        )
        db_session.add(current_config)
        db_session.commit()

        # 查询今天的时薪 - 应该返回当前有效的150元
        rate = HourlyRateService.get_user_hourly_rate(db_session, user.id, date.today())
        assert rate == Decimal("150")
