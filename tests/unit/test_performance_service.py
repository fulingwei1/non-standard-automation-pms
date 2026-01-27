# -*- coding: utf-8 -*-
"""
performance_service 单元测试

测试绩效管理服务：
- 用户角色判断
- 可评价员工获取
- 评价任务创建
- 分数计算与等级映射
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.performance_service import PerformanceService


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_user(
    user_id=1,
    username="testuser",
    employee_id=1,
    is_active=True
):
    """创建模拟的用户"""
    mock = MagicMock()
    mock.id = user_id
    mock.username = username
    mock.employee_id = employee_id
    mock.is_active = is_active
    return mock


def create_mock_department(
    dept_id=1,
    dept_name="技术部",
    manager_id=1,
    is_active=True
):
    """创建模拟的部门"""
    mock = MagicMock()
    mock.id = dept_id
    mock.dept_name = dept_name
    mock.manager_id = manager_id
    mock.is_active = is_active
    return mock


def create_mock_employee(
    emp_id=1,
    emp_name="测试员工",
    department="技术部",
    is_active=True
):
    """创建模拟的员工"""
    mock = MagicMock()
    mock.id = emp_id
    mock.emp_name = emp_name
    mock.department = department
    mock.is_active = is_active
    return mock


def create_mock_project(
    project_id=1,
    project_name="测试项目",
    pm_id=1,
    is_active=True
):
    """创建模拟的项目"""
    mock = MagicMock()
    mock.id = project_id
    mock.project_name = project_name
    mock.pm_id = pm_id
    mock.is_active = is_active
    return mock


def create_mock_project_member(
    member_id=1,
    project_id=1,
    user_id=2,
    is_active=True,
    start_date=None,
    end_date=None
):
    """创建模拟的项目成员"""
    mock = MagicMock()
    mock.id = member_id
    mock.project_id = project_id
    mock.user_id = user_id
    mock.is_active = is_active
    mock.start_date = start_date
    mock.end_date = end_date
    return mock


def create_mock_summary(
    summary_id=1,
    employee_id=1,
    period="2024-12",
    status="COMPLETED"
):
    """创建模拟的工作总结"""
    mock = MagicMock()
    mock.id = summary_id
    mock.employee_id = employee_id
    mock.period = period
    mock.status = status
    return mock


def create_mock_assessment_record(
    record_id=1,
    summary_id=1,
    assessor_id=1,
    assessor_type="DEPT_MANAGER",
    project_id=None,
    project_weight=None,
    score=85,
    comment="良好",
    status="COMPLETED"
):
    """创建模拟的评价记录"""
    mock = MagicMock()
    mock.id = record_id
    mock.summary_id = summary_id
    mock.evaluator_id = assessor_id
    mock.evaluator_type = assessor_type
    mock.project_id = project_id
    mock.project_weight = project_weight
    mock.score = score
    mock.comment = comment
    mock.status = status
    mock.evaluated_at = None
    return mock


def create_mock_weight_config(
    dept_weight=60,
    project_weight=40,
    effective_date=date(2024, 1, 1)
):
    """创建模拟的权重配置"""
    mock = MagicMock()
    mock.dept_manager_weight = dept_weight
    mock.project_manager_weight = project_weight
    mock.effective_date = effective_date
    return mock


@pytest.mark.unit
class TestGetUserManagerRoles:
    """测试 get_user_manager_roles 方法"""

    def test_returns_default_when_no_roles(self):
        """测试无角色时返回默认值"""
        db = create_mock_db_session()
        user = create_mock_user(employee_id=None)
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []

        result = PerformanceService.get_user_manager_roles(db, user)

        assert result["is_dept_manager"] is False
        assert result["is_project_manager"] is False
        assert result["managed_dept_id"] is None
        assert result["managed_project_ids"] == []

    def test_identifies_dept_manager(self):
        """测试识别部门经理"""
        db = create_mock_db_session()
        user = create_mock_user(employee_id=1)
        dept = create_mock_department(dept_id=10, manager_id=1)

        call_count = [0]

        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_filter.first.return_value = dept
        else:
            mock_filter.all.return_value = []
            return mock_filter

            db.query.return_value.filter.side_effect = filter_side_effect

            result = PerformanceService.get_user_manager_roles(db, user)

            assert result["is_dept_manager"] is True
            assert result["managed_dept_id"] == 10

    def test_identifies_project_manager(self):
        """测试识别项目经理"""
        db = create_mock_db_session()
        user = create_mock_user(employee_id=None)
        projects = [
        create_mock_project(project_id=1, pm_id=1),
        create_mock_project(project_id=2, pm_id=1)
        ]

        db.query.return_value.filter.return_value.all.return_value = projects

        result = PerformanceService.get_user_manager_roles(db, user)

        assert result["is_project_manager"] is True
        assert 1 in result["managed_project_ids"]
        assert 2 in result["managed_project_ids"]

    def test_identifies_both_roles(self):
        """测试同时是部门经理和项目经理"""
        db = create_mock_db_session()
        user = create_mock_user(employee_id=1)
        dept = create_mock_department(dept_id=10, manager_id=1)
        projects = [create_mock_project(project_id=1, pm_id=1)]

        call_count = [0]

        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_filter.first.return_value = dept
        else:
            mock_filter.all.return_value = projects
            return mock_filter

            db.query.return_value.filter.side_effect = filter_side_effect

            result = PerformanceService.get_user_manager_roles(db, user)

            assert result["is_dept_manager"] is True
            assert result["is_project_manager"] is True


@pytest.mark.unit
class TestGetScoreLevel:
    """测试 get_score_level 方法"""

    def test_returns_a_plus_for_95_or_above(self):
        """测试95分及以上返回A+"""
        assert PerformanceService.get_score_level(95) == "A+"
        assert PerformanceService.get_score_level(100) == "A+"
        assert PerformanceService.get_score_level(97.5) == "A+"

    def test_returns_a_for_90_to_94(self):
        """测试90-94分返回A"""
        assert PerformanceService.get_score_level(90) == "A"
        assert PerformanceService.get_score_level(94.9) == "A"

    def test_returns_b_plus_for_85_to_89(self):
        """测试85-89分返回B+"""
        assert PerformanceService.get_score_level(85) == "B+"
        assert PerformanceService.get_score_level(89.9) == "B+"

    def test_returns_b_for_80_to_84(self):
        """测试80-84分返回B"""
        assert PerformanceService.get_score_level(80) == "B"
        assert PerformanceService.get_score_level(84.9) == "B"

    def test_returns_c_plus_for_75_to_79(self):
        """测试75-79分返回C+"""
        assert PerformanceService.get_score_level(75) == "C+"
        assert PerformanceService.get_score_level(79.9) == "C+"

    def test_returns_c_for_70_to_74(self):
        """测试70-74分返回C"""
        assert PerformanceService.get_score_level(70) == "C"
        assert PerformanceService.get_score_level(74.9) == "C"

    def test_returns_d_for_below_70(self):
        """测试70分以下返回D"""
        assert PerformanceService.get_score_level(69.9) == "D"
        assert PerformanceService.get_score_level(60) == "D"
        assert PerformanceService.get_score_level(0) == "D"


@pytest.mark.unit
class TestCalculateFinalScore:
    """测试 calculate_final_score 方法"""

    def test_returns_none_when_no_assessments(self):
        """测试无评价记录时返回None"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []

        result = PerformanceService.calculate_final_score(db, 1, "2024-12")

        assert result is None

    def test_uses_default_weights_when_no_config(self):
        """测试无配置时使用默认权重50:50"""
        db = create_mock_db_session()
        dept_record = create_mock_assessment_record(
        assessor_type="DEPT_MANAGER",
        score=80
        )
        proj_record = create_mock_assessment_record(
        assessor_type="PROJECT_MANAGER",
        score=90,
        project_id=1,
        project_weight=100
        )

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_query.filter.return_value.order_by.return_value.first.return_value = None
        else:
            mock_query.filter.return_value.all.return_value = [dept_record, proj_record]
            return mock_query

            db.query.side_effect = query_side_effect

            result = PerformanceService.calculate_final_score(db, 1, "2024-12")

            assert result is not None
            assert result["dept_weight"] == 50
            assert result["project_weight"] == 50

    def test_uses_configured_weights(self):
        """测试使用配置的权重"""
        db = create_mock_db_session()
        weight_config = create_mock_weight_config(dept_weight=60, project_weight=40)
        dept_record = create_mock_assessment_record(assessor_type="DEPT_MANAGER", score=80)

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_query.filter.return_value.order_by.return_value.first.return_value = weight_config
        else:
            mock_query.filter.return_value.all.return_value = [dept_record]
            return mock_query

            db.query.side_effect = query_side_effect

            result = PerformanceService.calculate_final_score(db, 1, "2024-12")

            assert result["dept_weight"] == 60
            assert result["project_weight"] == 40

    def test_calculates_weighted_score_correctly(self):
        """测试加权分数计算正确"""
        db = create_mock_db_session()
        weight_config = create_mock_weight_config(dept_weight=60, project_weight=40)
        dept_record = create_mock_assessment_record(assessor_type="DEPT_MANAGER", score=80)
        proj_record = create_mock_assessment_record(
        assessor_type="PROJECT_MANAGER",
        score=90,
        project_id=1,
        project_weight=100
        )

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_query.filter.return_value.order_by.return_value.first.return_value = weight_config
        else:
            mock_query.filter.return_value.all.return_value = [dept_record, proj_record]
            return mock_query

            db.query.side_effect = query_side_effect

            result = PerformanceService.calculate_final_score(db, 1, "2024-12")

            # 80 * 0.6 + 90 * 0.4 = 48 + 36 = 84
            assert result["final_score"] == 84.0

    def test_uses_100_percent_when_only_dept_assessment(self):
        """测试只有部门评价时使用100%"""
        db = create_mock_db_session()
        weight_config = create_mock_weight_config(dept_weight=60, project_weight=40)
        dept_record = create_mock_assessment_record(assessor_type="DEPT_MANAGER", score=85)

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_query.filter.return_value.order_by.return_value.first.return_value = weight_config
        else:
            mock_query.filter.return_value.all.return_value = [dept_record]
            return mock_query

            db.query.side_effect = query_side_effect

            result = PerformanceService.calculate_final_score(db, 1, "2024-12")

            assert result["final_score"] == 85.0

    def test_uses_100_percent_when_only_project_assessment(self):
        """测试只有项目评价时使用100%"""
        db = create_mock_db_session()
        weight_config = create_mock_weight_config(dept_weight=60, project_weight=40)
        proj_record = create_mock_assessment_record(
        assessor_type="PROJECT_MANAGER",
        score=90,
        project_id=1,
        project_weight=100
        )

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_query.filter.return_value.order_by.return_value.first.return_value = weight_config
        else:
            mock_query.filter.return_value.all.return_value = [proj_record]
            return mock_query

            db.query.side_effect = query_side_effect

            result = PerformanceService.calculate_final_score(db, 1, "2024-12")

            assert result["final_score"] == 90.0

    def test_calculates_project_weighted_average(self):
        """测试多项目加权平均"""
        db = create_mock_db_session()
        weight_config = create_mock_weight_config(dept_weight=0, project_weight=100)
        proj_record1 = create_mock_assessment_record(
        assessor_type="PROJECT_MANAGER",
        score=80,
        project_id=1,
        project_weight=60
        )
        proj_record2 = create_mock_assessment_record(
        assessor_type="PROJECT_MANAGER",
        score=90,
        project_id=2,
        project_weight=40
        )

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_query.filter.return_value.order_by.return_value.first.return_value = weight_config
        else:
            mock_query.filter.return_value.all.return_value = [proj_record1, proj_record2]
            return mock_query

            db.query.side_effect = query_side_effect

            result = PerformanceService.calculate_final_score(db, 1, "2024-12")

            # 项目加权平均: (80*60 + 90*40) / (60+40) = (4800+3600)/100 = 84
            assert result["project_score"] == 84.0


@pytest.mark.unit
class TestCalculateQuarterlyScore:
    """测试 calculate_quarterly_score 方法"""

    def test_returns_none_when_no_summaries(self):
        """测试无工作总结时返回None"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.all.return_value = []

        result = PerformanceService.calculate_quarterly_score(db, 1, "2024-12")

        assert result is None

    @patch.object(PerformanceService, "calculate_final_score")
    def test_returns_none_when_no_scores(self, mock_calc):
        """测试无有效分数时返回None"""
        db = create_mock_db_session()
        summaries = [
        create_mock_summary(summary_id=1, period="2024-12"),
        create_mock_summary(summary_id=2, period="2024-11"),
        create_mock_summary(summary_id=3, period="2024-10")
        ]
        db.query.return_value.filter.return_value.all.return_value = summaries
        mock_calc.return_value = None

        result = PerformanceService.calculate_quarterly_score(db, 1, "2024-12")

        assert result is None

    @patch.object(PerformanceService, "calculate_final_score")
    def test_calculates_average_of_three_months(self, mock_calc):
        """测试计算3个月平均分"""
        db = create_mock_db_session()
        summaries = [
        create_mock_summary(summary_id=1, period="2024-12"),
        create_mock_summary(summary_id=2, period="2024-11"),
        create_mock_summary(summary_id=3, period="2024-10")
        ]
        db.query.return_value.filter.return_value.all.return_value = summaries

        mock_calc.side_effect = [
        {"final_score": 80},
        {"final_score": 85},
        {"final_score": 90}
        ]

        result = PerformanceService.calculate_quarterly_score(db, 1, "2024-12")

        # 平均分: (80+85+90)/3 = 85
        assert result == 85.0

    @patch.object(PerformanceService, "calculate_final_score")
    def test_ignores_zero_scores(self, mock_calc):
        """测试忽略0分的月份"""
        db = create_mock_db_session()
        summaries = [
        create_mock_summary(summary_id=1, period="2024-12"),
        create_mock_summary(summary_id=2, period="2024-11")
        ]
        db.query.return_value.filter.return_value.all.return_value = summaries

        mock_calc.side_effect = [
        {"final_score": 80},
        {"final_score": 0}
        ]

        result = PerformanceService.calculate_quarterly_score(db, 1, "2024-12")

        assert result == 80.0


@pytest.mark.unit
class TestGetManageableEmployees:
    """测试 get_manageable_employees 方法"""

    @patch.object(PerformanceService, "get_user_manager_roles")
    def test_returns_empty_when_not_manager(self, mock_roles):
        """测试非经理返回空列表"""
        db = create_mock_db_session()
        user = create_mock_user()
        mock_roles.return_value = {
        "is_dept_manager": False,
        "is_project_manager": False,
        "managed_dept_id": None,
        "managed_project_ids": []
        }

        result = PerformanceService.get_manageable_employees(db, user)

        assert result == []

    @patch.object(PerformanceService, "get_user_manager_roles")
    def test_gets_dept_employees_for_dept_manager(self, mock_roles):
        """测试部门经理获取部门员工"""
        db = create_mock_db_session()
        user = create_mock_user()
        dept = create_mock_department(dept_id=1, dept_name="技术部")
        employees = [
        create_mock_employee(emp_id=1),
        create_mock_employee(emp_id=2)
        ]
        emp_users = [
        create_mock_user(user_id=10, employee_id=1),
        create_mock_user(user_id=11, employee_id=2)
        ]

        mock_roles.return_value = {
        "is_dept_manager": True,
        "is_project_manager": False,
        "managed_dept_id": 1,
        "managed_project_ids": []
        }

        call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                mock_query.get.return_value = dept
        elif call_count[0] == 2:
            mock_query.filter.return_value.all.return_value = employees
        else:
            idx = call_count[0] - 3
            if idx < len(emp_users):
                mock_query.filter.return_value.first.return_value = emp_users[idx]
        else:
            mock_query.filter.return_value.first.return_value = None
            return mock_query

            db.query.side_effect = query_side_effect

            result = PerformanceService.get_manageable_employees(db, user)

            assert 10 in result
            assert 11 in result

    @patch.object(PerformanceService, "get_user_manager_roles")
    def test_gets_project_members_for_project_manager(self, mock_roles):
        """测试项目经理获取项目成员"""
        db = create_mock_db_session()
        user = create_mock_user()
        members = [
        create_mock_project_member(user_id=10),
        create_mock_project_member(user_id=11)
        ]

        mock_roles.return_value = {
        "is_dept_manager": False,
        "is_project_manager": True,
        "managed_dept_id": None,
        "managed_project_ids": [1, 2]
        }

        db.query.return_value.filter.return_value.all.return_value = members

        result = PerformanceService.get_manageable_employees(db, user)

        assert 10 in result
        assert 11 in result


@pytest.mark.unit
class TestCreateAssessmentTasks:
    """测试 create_assessment_tasks 方法"""

    def test_returns_empty_when_employee_not_found(self):
        """测试员工不存在时返回空列表"""
        db = create_mock_db_session()
        summary = create_mock_summary()
        db.query.return_value.get.return_value = None

        result = PerformanceService.create_evaluation_tasks(db, summary)

        assert result == []

    def test_skips_existing_assessment_records(self):
        """测试跳过已存在的评价记录"""
        db = create_mock_db_session()
        summary = create_mock_summary()
        employee = create_mock_user(employee_id=1)
        emp_obj = create_mock_employee(department="技术部")
        dept = create_mock_department(manager_id=1)
        manager_emp = create_mock_employee(emp_id=1)
        manager_user = create_mock_user(user_id=2)
        existing_record = create_mock_assessment_record()

        call_count = [0]

        def get_side_effect(id):
            call_count[0] += 1
            if call_count[0] == 1:
                return employee
        elif call_count[0] == 2:
            return emp_obj
        elif call_count[0] == 3:
            return manager_emp
            return None

            db.query.return_value.get.side_effect = get_side_effect
            db.query.return_value.filter.return_value.first.side_effect = [
            dept,
            manager_user,
            existing_record
            ]
            db.query.return_value.filter.return_value.all.return_value = []

            result = PerformanceService.create_evaluation_tasks(db, summary)

            assert len(result) == 0
            db.add.assert_not_called()


@pytest.mark.unit
class TestGetHistoricalPerformance:
    """测试 get_historical_performance 方法"""

    @patch.object(PerformanceService, "calculate_final_score")
    def test_returns_empty_when_no_summaries(self, mock_calc):
        """测试无工作总结时返回空列表"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = PerformanceService.get_historical_performance(db, 1)

        assert result == []

    @patch.object(PerformanceService, "calculate_final_score")
    def test_returns_history_with_levels(self, mock_calc):
        """测试返回带等级的历史记录"""
        db = create_mock_db_session()
        summaries = [
        create_mock_summary(summary_id=1, period="2024-12"),
        create_mock_summary(summary_id=2, period="2024-11")
        ]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = summaries

        mock_calc.side_effect = [
        {"final_score": 92, "dept_score": 90, "project_score": 94},
        {"final_score": 85, "dept_score": 85, "project_score": None}
        ]

        result = PerformanceService.get_historical_performance(db, 1)

        assert len(result) == 2
        assert result[0]["period"] == "2024-12"
        assert result[0]["final_score"] == 92
        assert result[0]["level"] == "A"
        assert result[1]["level"] == "B+"

    @patch.object(PerformanceService, "calculate_final_score")
    def test_respects_months_parameter(self, mock_calc):
        """测试遵守months参数"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        PerformanceService.get_historical_performance(db, 1, months=6)

        db.query.return_value.filter.assert_called()
