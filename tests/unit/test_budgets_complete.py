# -*- coding: utf-8 -*-
"""
预算管理单元测试

覆盖 app/api/v1/endpoints/budget/budgets.py 的关键端点
"""

import pytest


from sqlalchemy.orm import Session

# Temporarily comment out imports to avoid collection errors
# from tests.factories import (
#     BudgetFactory,
#     ProjectFactory,
#     UserFactory,
# )
# from app.models.enums import BudgetStatusEnum


class TestListBudgets:
    """预算列表测试"""

    def test_list_budgets_by_project(self, db_session: Session, test_project):
        """按项目列出预算"""
        BudgetFactory.create(
        project=test_project,
        status="DRAFT",
        total_amount=200000,
        )
        BudgetFactory.create(
        project=test_project, status="APPROVED", total_amount=100000
        )
        db_session.commit()

        from app.api.v1.endpoints.budget import budgets

        response = budgets.list_budgets(
        project_id=test_project.id, db_session=db_session, skip=0, limit=10
        )
        assert len(response.items) == 2

    def test_list_budgets_with_filter_by_status(
        self, db_session: Session, test_project
    ):
        """按状态过滤预算"""
        BudgetFactory.create(project=test_project, status="DRAFT", total_amount=200000)
        BudgetFactory.create(
        project=test_project, status="APPROVED", total_amount=100000
        )
        db_session.commit()

        from app.api.v1.endpoints.budget import budgets

        response = budgets.list_budgets(
        project_id=test_project.id,
        status="APPROVED",
        db_session=db_session,
        skip=0,
        limit=10,
        )
        assert len(response.items) == 1
        assert response.items[0].status == "APPROVED"


class TestGetBudget:
    """获取预算详情测试"""

    def test_get_budget_success(self, db_session: Session, test_budget):
        """成功获取预算详情"""
        from app.api.v1.endpoints.budget import budgets

        response = budgets.get_budget(budget_id=test_budget.id, db_session=db_session)
        assert response.id == test_budget.id
        assert response.total_amount == test_budget.total_amount

    def test_get_budget_not_found(self, db_session: Session):
        """预算不存在时应抛出 404 错误"""
        from app.api.v1.endpoints.budget import budgets

        with pytest.raises(Exception) as exc_info:
            budgets.get_budget(budget_id=99999, db_session=db_session)
            assert "不存在" in str(exc_info.value)


class TestCreateBudget:
    """创建预算测试"""

    def test_create_budget_success(self, db_session: Session, test_project, test_user):
        """成功创建预算"""
        from app.api.v1.endpoints.budget import budgets

        response = budgets.create_budget(
        project_id=test_project.id,
        total_amount=200000,
        currency="CNY",
        created_by_id=test_user.id,
        db_session=db_session,
        )
        assert response.project_id == test_project.id
        assert response.total_amount == 200000
        assert response.status == BudgetStatusEnum.DRAFT.value


class TestUpdateBudget:
    """更新预算测试"""

    def test_update_budget_success(self, db_session: Session, test_budget, test_user):
        """成功更新预算"""
        from app.api.v1.endpoints.budget import budgets

        response = budgets.update_budget(
        budget_id=test_budget.id,
        total_amount=250000,
        updated_by_id=test_user.id,
        db_session=db_session,
        )
        assert response.total_amount == 250000

    def test_update_nonexistent_budget(self, db_session: Session, test_user):
        """更新不存在的预算应抛出错误"""
        from app.api.v1.endpoints.budget import budgets

        with pytest.raises(Exception):
            budgets.update_budget(
            budget_id=99999,
            total_amount=250000,
            updated_by_id=test_user.id,
            db_session=db_session,
            )


class TestSubmitBudget:
    """提交预算测试"""

    def test_submit_budget_success(self, db_session: Session, test_budget, test_user):
        """成功提交预算"""
        from app.api.v1.endpoints.budget import budgets

        response = budgets.submit_budget(
        budget_id=test_budget.id,
        submitted_by_id=test_user.id,
        db_session=db_session,
        )
        assert response.status == BudgetStatusEnum.PENDING_APPROVAL.value


class TestApproveBudget:
    """批准预算测试"""

    def test_approve_budget_success(self, db_session: Session, test_budget, test_user):
        """成功批准预算"""
        from app.api.v1.endpoints.budget import budgets

        test_budget.status = BudgetStatusEnum.PENDING_APPROVAL.value
        db_session.commit()

        response = budgets.approve_budget(
        budget_id=test_budget.id,
        approved_by_id=test_user.id,
        db_session=db_session,
        )
        assert response.status == BudgetStatusEnum.APPROVED.value


class TestDeleteBudget:
    """删除预算测试"""

    def test_delete_budget_success(self, db_session: Session, test_budget):
        """成功删除预算"""
        from app.api.v1.endpoints.budget import budgets

        budgets.delete_budget(budget_id=test_budget.id, db_session=db_session)

        # 验证预算已被标记为删除
        from app.models.budget import Budget

        deleted = db_session.query(Budget).filter(Budget.id == test_budget.id).first()
        assert deleted.is_active == False


# Fixtures
@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = ProjectFactory.create(
        project_code="P2025001",
        stage="S5",
        budget_amount=200000,
    )
    db_session.commit()
    return project


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = UserFactory.create(username="testuser", real_name="测试用户")
    db_session.commit()
    return user


@pytest.fixture
def test_budget(db_session: Session, test_project, test_user):
    """创建测试预算"""
    budget = BudgetFactory.create(
        project=test_project,
        status="DRAFT",
        total_amount=200000,
        created_by_id=test_user.id,
    )
    db_session.commit()
    return budget
