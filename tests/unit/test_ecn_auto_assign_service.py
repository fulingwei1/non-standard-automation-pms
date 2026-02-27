# -*- coding: utf-8 -*-
"""
ECN自动分配服务单元测试

测试内容：
- find_users_by_department: 按部门查找用户
- find_users_by_role: 按角色查找用户
- auto_assign_evaluation: 自动分配评估任务
- auto_assign_approval: 自动分配审批任务
- auto_assign_task: 自动分配执行任务
- auto_assign_pending_*: 批量自动分配
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.services.ecn_auto_assign_service import (
    auto_assign_approval,
    auto_assign_evaluation,
    auto_assign_pending_approvals,
    auto_assign_pending_evaluations,
    auto_assign_pending_tasks,
    auto_assign_task,
    find_users_by_department,
    find_users_by_role,
)


# ============================================================================
# MockUser 辅助类
# ============================================================================


class MockUser:
    """模拟用户"""

    def __init__(
        self,
        user_id: int,
        department: str = None,
        position: str = None,
        is_active: bool = True,
    ):
        self.id = user_id
        self.department = department
        self.position = position
        self.is_active = is_active


class MockRole:
    """模拟角色"""

    def __init__(self, role_id: int, role_name: str, is_active: bool = True):
        self.id = role_id
        self.role_name = role_name
        self.is_active = is_active


class MockUserRole:
    """模拟用户角色关联"""

    def __init__(self, user_id: int, role_id: int):
        self.user_id = user_id
        self.role_id = role_id


class MockEcn:
    """模拟ECN"""

    def __init__(self, ecn_id: int, project_id: int = None):
        self.id = ecn_id
        self.project_id = project_id


class MockEcnEvaluation:
    """模拟ECN评估"""

    def __init__(
        self,
        eval_id: int,
        ecn_id: int,
        eval_dept: str = None,
        evaluator_id: int = None,
        status: str = "PENDING",
    ):
        self.id = eval_id
        self.ecn_id = ecn_id
        self.eval_dept = eval_dept
        self.evaluator_id = evaluator_id
        self.status = status


class MockEcnApproval:
    """模拟ECN审批"""

    def __init__(
        self,
        approval_id: int,
        ecn_id: int,
        approval_role: str = None,
        approver_id: int = None,
        status: str = "PENDING",
    ):
        self.id = approval_id
        self.ecn_id = ecn_id
        self.approval_role = approval_role
        self.approver_id = approver_id
        self.status = status


class MockEcnTask:
    """模拟ECN任务"""

    def __init__(
        self,
        task_id: int,
        ecn_id: int,
        task_dept: str = None,
        assignee_id: int = None,
        status: str = "PENDING",
    ):
        self.id = task_id
        self.ecn_id = ecn_id
        self.task_dept = task_dept
        self.assignee_id = assignee_id
        self.status = status


class MockProjectMember:
    """模拟项目成员"""

    def __init__(self, user_id: int, project_id: int, is_active: bool = True):
        self.user_id = user_id
        self.project_id = project_id
        self.is_active = is_active


# ============================================================================
# find_users_by_department 测试
# ============================================================================


@pytest.mark.unit
class TestFindUsersByDepartment:
    """测试按部门查找用户"""

    def test_find_users_by_department_success(self):
        """测试成功查找部门用户"""
        db = MagicMock(spec=Session)
        mock_users = [
        MockUser(1, "研发部", "工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "研发部", "高级工程师",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = find_users_by_department(db, "研发部")

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_find_users_by_department_empty(self):
        """测试部门无用户"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []

        result = find_users_by_department(db, "不存在的部门")

        assert result == []


# ============================================================================
# find_users_by_role 测试
# ============================================================================


@pytest.mark.unit
class TestFindUsersByRole:
    """测试按角色查找用户"""

    def test_find_users_by_role_success(self):
        """测试成功查找角色用户"""
        db = MagicMock(spec=Session)

        mock_role = MockRole(1, "项目经理")
        mock_user_roles = [MockUserRole(1, 1), MockUserRole(2, 1)]
        mock_users = [MockUser(1,
        password_hash="test_hash_123"
    ), MockUser(2,
        password_hash="test_hash_123"
    )]

        # 设置 query 链
        def mock_filter(*args, **kwargs):
            mock_result = MagicMock()
            return mock_result

            db.query.return_value.filter.return_value.first.return_value = mock_role
            db.query.return_value.filter.return_value.all.side_effect = [
            mock_user_roles,
            mock_users,
            ]

            result = find_users_by_role(db, "项目经理")

            # 检查返回的用户
            assert db.query.called

    def test_find_users_by_role_no_role(self):
        """测试角色不存在"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        result = find_users_by_role(db, "不存在的角色")

        assert result == []

    def test_find_users_by_role_no_users(self):
        """测试角色存在但无用户"""
        db = MagicMock(spec=Session)
        mock_role = MockRole(1, "项目经理")
        db.query.return_value.filter.return_value.first.return_value = mock_role
        db.query.return_value.filter.return_value.all.return_value = []

        result = find_users_by_role(db, "项目经理")

        assert result == []


# ============================================================================
# auto_assign_evaluation 测试
# ============================================================================


@pytest.mark.unit
class TestAutoAssignEvaluation:
    """测试自动分配评估任务"""

    def test_auto_assign_evaluation_no_dept(self):
        """测试无部门时返回None"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        evaluation = MockEcnEvaluation(1, 1, eval_dept=None)

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result is None

    def test_auto_assign_evaluation_no_users_in_dept(self):
        """测试部门无用户时返回None"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        evaluation = MockEcnEvaluation(1, 1, eval_dept="研发部")

        db.query.return_value.filter.return_value.all.return_value = []

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result is None

    def test_auto_assign_evaluation_select_leader(self):
        """测试优先选择负责人"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)  # 无项目关联
        evaluation = MockEcnEvaluation(1, 1, eval_dept="研发部")

        mock_users = [
        MockUser(1, "研发部", "工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "研发部", "部门负责人",
        password_hash="test_hash_123"
    ),
        MockUser(3, "研发部", "经理",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result == 2  # 选择负责人

    def test_auto_assign_evaluation_select_manager(self):
        """测试无负责人时选择经理"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        evaluation = MockEcnEvaluation(1, 1, eval_dept="研发部")

        mock_users = [
        MockUser(1, "研发部", "工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "研发部", "经理",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result == 2  # 选择经理

    def test_auto_assign_evaluation_select_supervisor(self):
        """测试无负责人和经理时选择主管"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        evaluation = MockEcnEvaluation(1, 1, eval_dept="研发部")

        mock_users = [
        MockUser(1, "研发部", "工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "研发部", "主管",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result == 2  # 选择主管

    def test_auto_assign_evaluation_no_leader_or_manager(self):
        """测试无负责人和经理时返回None"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        evaluation = MockEcnEvaluation(1, 1, eval_dept="研发部")

        mock_users = [
        MockUser(1, "研发部", "工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "研发部", "高级工程师",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result is None  # 不分配给普通用户

    def test_auto_assign_evaluation_with_project(self):
        """测试有项目关联时优先从项目成员中选择"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1, project_id=100)
        evaluation = MockEcnEvaluation(1, 1, eval_dept="研发部")

        # 项目成员
        mock_project_members = [
        MockProjectMember(1, 100),
        MockProjectMember(2, 100),
        ]

        # 项目成员中属于该部门的用户
        mock_project_dept_users = [
        MockUser(1, "研发部", "工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "研发部", "部门负责人",
        password_hash="test_hash_123"
    ),
        ]

        # 设置查询链
        db.query.return_value.filter.return_value.all.side_effect = [
        mock_project_members,  # 第一次查询项目成员
        mock_project_dept_users,  # 第二次查询项目中部门用户
        ]

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result == 2  # 选择项目成员中的负责人


# ============================================================================
# auto_assign_approval 测试
# ============================================================================


@pytest.mark.unit
class TestAutoAssignApproval:
    """测试自动分配审批任务"""

    def test_auto_assign_approval_no_role(self):
        """测试无角色时返回None"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        approval = MockEcnApproval(1, 1, approval_role=None)

        result = auto_assign_approval(db, ecn, approval)

        assert result is None

    def test_auto_assign_approval_no_users_with_role(self):
        """测试无拥有该角色的用户"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        approval = MockEcnApproval(1, 1, approval_role="审批员")

        # 角色不存在
        db.query.return_value.filter.return_value.first.return_value = None

        result = auto_assign_approval(db, ecn, approval)

        assert result is None

    def test_auto_assign_approval_select_leader(self):
        """测试优先选择负责人"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)  # 无项目关联
        approval = MockEcnApproval(1, 1, approval_role="审批员")

        mock_role = MockRole(1, "审批员")
        mock_user_roles = [MockUserRole(1, 1), MockUserRole(2, 1)]
        mock_users = [
        MockUser(1, position="普通审批员",
        password_hash="test_hash_123"
    ),
        MockUser(2, position="审批负责人",
        password_hash="test_hash_123"
    ),
        ]

        db.query.return_value.filter.return_value.first.return_value = mock_role
        db.query.return_value.filter.return_value.all.side_effect = [
        mock_user_roles,
        mock_users,
        ]

        result = auto_assign_approval(db, ecn, approval)

        assert result == 2  # 选择负责人


# ============================================================================
# auto_assign_task 测试
# ============================================================================


@pytest.mark.unit
class TestAutoAssignTask:
    """测试自动分配执行任务"""

    def test_auto_assign_task_no_dept(self):
        """测试无部门时返回None"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        task = MockEcnTask(1, 1, task_dept=None)

        result = auto_assign_task(db, ecn, task)

        assert result is None

    def test_auto_assign_task_select_leader(self):
        """测试优先选择负责人"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        task = MockEcnTask(1, 1, task_dept="生产部")

        mock_users = [
        MockUser(1, "生产部", "操作员",
        password_hash="test_hash_123"
    ),
        MockUser(2, "生产部", "生产负责人",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = auto_assign_task(db, ecn, task)

        assert result == 2  # 选择负责人


# ============================================================================
# auto_assign_pending_evaluations 测试
# ============================================================================


@pytest.mark.unit
class TestAutoAssignPendingEvaluations:
    """测试批量自动分配评估任务"""

    def test_auto_assign_pending_evaluations_ecn_not_found(self):
        """测试ECN不存在"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        result = auto_assign_pending_evaluations(db, 999)

        assert result == 0

    def test_auto_assign_pending_evaluations_no_pending(self):
        """测试无待分配的评估"""
        db = MagicMock(spec=Session)
        mock_ecn = MockEcn(1)

        # 第一次调用返回ECN，第二次返回空列表
        db.query.return_value.filter.return_value.first.return_value = mock_ecn
        db.query.return_value.filter.return_value.all.return_value = []

        result = auto_assign_pending_evaluations(db, 1)

        assert result == 0


# ============================================================================
# auto_assign_pending_approvals 测试
# ============================================================================


@pytest.mark.unit
class TestAutoAssignPendingApprovals:
    """测试批量自动分配审批任务"""

    def test_auto_assign_pending_approvals_ecn_not_found(self):
        """测试ECN不存在"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        result = auto_assign_pending_approvals(db, 999)

        assert result == 0


# ============================================================================
# auto_assign_pending_tasks 测试
# ============================================================================


@pytest.mark.unit
class TestAutoAssignPendingTasks:
    """测试批量自动分配执行任务"""

    def test_auto_assign_pending_tasks_ecn_not_found(self):
        """测试ECN不存在"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        result = auto_assign_pending_tasks(db, 999)

        assert result == 0


# ============================================================================
# 集成场景测试
# ============================================================================


@pytest.mark.unit
class TestEcnAutoAssignIntegration:
    """测试ECN自动分配集成场景"""

    def test_all_functions_callable(self):
        """测试所有函数可调用"""
        assert callable(find_users_by_department)
        assert callable(find_users_by_role)
        assert callable(auto_assign_evaluation)
        assert callable(auto_assign_approval)
        assert callable(auto_assign_task)
        assert callable(auto_assign_pending_evaluations)
        assert callable(auto_assign_pending_approvals)
        assert callable(auto_assign_pending_tasks)

    def test_position_priority_leader(self):
        """测试职位优先级 - 负责人优先"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        evaluation = MockEcnEvaluation(1, 1, eval_dept="测试部")

        mock_users = [
        MockUser(1, "测试部", "测试工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "测试部", "测试主管",
        password_hash="test_hash_123"
    ),
        MockUser(3, "测试部", "测试经理",
        password_hash="test_hash_123"
    ),
        MockUser(4, "测试部", "测试负责人",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = auto_assign_evaluation(db, ecn, evaluation)

        assert result == 4  # 负责人优先

    def test_position_priority_manager_fallback(self):
        """测试职位优先级 - 经理/主管兜底（先匹配到的优先）"""
        db = MagicMock(spec=Session)
        ecn = MockEcn(1)
        evaluation = MockEcnEvaluation(1, 1, eval_dept="测试部")

        mock_users = [
        MockUser(1, "测试部", "测试工程师",
        password_hash="test_hash_123"
    ),
        MockUser(2, "测试部", "测试主管",
        password_hash="test_hash_123"
    ),
        MockUser(3, "测试部", "测试经理",
        password_hash="test_hash_123"
    ),
        ]
        db.query.return_value.filter.return_value.all.return_value = mock_users

        result = auto_assign_evaluation(db, ecn, evaluation)

        # 主管和经理同等优先级，先匹配到的优先（user 2）
        assert result == 2
