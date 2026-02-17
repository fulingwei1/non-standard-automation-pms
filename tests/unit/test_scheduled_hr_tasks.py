# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：HR相关 (hr_tasks.py)
J2组覆盖率提升
"""
import sys
from unittest.mock import MagicMock, patch

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


def _make_db():
    return MagicMock()


# ================================================================
#  check_contract_expiry_reminder
# ================================================================

class TestCheckContractExpiryReminder:

    def _setup_db(self, contracts, existing_reminder=None):
        """构建 mock db"""
        db = _make_db()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "EmployeeContract" in name:
                # 代码: db.query(EmployeeContract).filter(cond1, cond2).all()  → 单次filter
                m.filter.return_value.all.return_value = contracts
            elif "ContractReminder" in name:
                m.filter.return_value.first.return_value = existing_reminder
            return m

        db.query.side_effect = q
        return db

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_no_active_contracts(self, mock_db_ctx):
        """无生效合同 → reminders_created=0"""
        db = self._setup_db(contracts=[])
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder
        result = check_contract_expiry_reminder()

        assert result["contracts_checked"] == 0
        assert result["reminders_created"] == 0

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_contract_expiring_in_two_months(self, mock_db_ctx):
        """合同在30~60天内到期 → 创建 two_months 提醒"""
        from datetime import date, timedelta

        contract = MagicMock()
        contract.id = 1
        contract.employee_id = 10
        contract.end_date = date.today() + timedelta(days=45)
        contract.reminder_sent = False

        db = self._setup_db(contracts=[contract], existing_reminder=None)
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder
        result = check_contract_expiry_reminder()

        assert result["reminders_created"] == 1
        assert db.add.called

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_contract_expiring_in_one_month(self, mock_db_ctx):
        """合同在14~30天内到期 → 创建 one_month 提醒"""
        from datetime import date, timedelta

        contract = MagicMock()
        contract.id = 2
        contract.employee_id = 11
        contract.end_date = date.today() + timedelta(days=20)

        db = self._setup_db(contracts=[contract], existing_reminder=None)
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder
        result = check_contract_expiry_reminder()

        assert result["reminders_created"] == 1

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_contract_expiring_in_two_weeks(self, mock_db_ctx):
        """合同在14天内到期 → 创建 two_weeks 提醒"""
        from datetime import date, timedelta

        contract = MagicMock()
        contract.id = 3
        contract.employee_id = 12
        contract.end_date = date.today() + timedelta(days=7)

        db = self._setup_db(contracts=[contract], existing_reminder=None)
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder
        result = check_contract_expiry_reminder()

        assert result["reminders_created"] == 1

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_contract_already_expired(self, mock_db_ctx):
        """合同已到期 → 创建 expired 提醒"""
        from datetime import date, timedelta

        contract = MagicMock()
        contract.id = 4
        contract.employee_id = 13
        contract.end_date = date.today() - timedelta(days=5)

        db = self._setup_db(contracts=[contract], existing_reminder=None)
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder
        result = check_contract_expiry_reminder()

        assert result["reminders_created"] == 1

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_reminder_already_exists_no_duplicate(self, mock_db_ctx):
        """已存在同类型提醒 → 不重复创建"""
        from datetime import date, timedelta

        contract = MagicMock()
        contract.id = 5
        contract.employee_id = 14
        contract.end_date = date.today() + timedelta(days=15)

        existing = MagicMock()  # 已存在提醒

        db = self._setup_db(contracts=[contract], existing_reminder=existing)
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder
        result = check_contract_expiry_reminder()

        assert result["reminders_created"] == 0

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        """异常时返回 error"""
        mock_db_ctx.return_value.__enter__.side_effect = Exception("DB连接失败")

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder
        result = check_contract_expiry_reminder()

        assert "error" in result


# ================================================================
#  check_employee_confirmation_reminder
# ================================================================

class TestCheckEmployeeConfirmationReminder:

    def _make_probation_employee(self, days_until_confirmation=5):
        from datetime import date, timedelta

        employee = MagicMock()
        employee.id = 1
        employee.name = "王小明"
        employee.employee_code = "EMP-001"

        profile = MagicMock()
        profile.probation_end_date = date.today() + timedelta(days=days_until_confirmation)

        return employee, profile

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_no_probation_employees(self, mock_db_ctx):
        """无试用期员工 → reminders_created=0"""
        db = _make_db()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Employee" in name and "Hr" not in name:
                m.join.return_value.filter.return_value.filter.return_value\
                 .filter.return_value.filter.return_value.filter.return_value.all.return_value = []
                m.filter.return_value.all.return_value = []
            elif "Role" in name:
                m.filter.return_value.all.return_value = []
                m.filter.return_value.filter.return_value.all.return_value = []
            elif "UserRole" in name:
                m.filter.return_value.all.return_value = []
            elif "User" in name:
                m.filter.return_value.filter.return_value.all.return_value = []
                m.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder
        result = check_employee_confirmation_reminder()

        assert result["employees_checked"] == 0
        assert result["reminders_created"] == 0

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_probation_employee_creates_transaction(self, mock_db_ctx):
        """试用期员工即将转正 → 创建转正事务"""
        from datetime import date, timedelta

        employee, profile = self._make_probation_employee(days_until_confirmation=5)

        db = _make_db()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Employee" in name and "Hr" not in name:
                # 代码: db.query(Employee).join(...).filter(cond1,...).all()  → 单次filter
                m.join.return_value.filter.return_value.all.return_value = [employee]
                m.filter.return_value.all.return_value = []
            elif "EmployeeHrProfile" in name:
                m.filter.return_value.first.return_value = profile
            elif "HrTransaction" in name:
                # 代码: .filter(cond1).filter(cond2).filter(cond3).first()
                m.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
            elif "Role" in name:
                m.filter.return_value.all.return_value = []
                m.filter.return_value.filter.return_value.all.return_value = []
            elif "UserRole" in name:
                m.filter.return_value.all.return_value = []
            elif "User" in name:
                m.filter.return_value.filter.return_value.all.return_value = []
                m.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch("app.common.query_filters.apply_keyword_filter", return_value=MagicMock(all=lambda: [])):
            from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder
            result = check_employee_confirmation_reminder()

        assert result["employees_checked"] == 1
        assert result["reminders_created"] == 1
        assert db.add.called

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_transaction_already_exists_skip(self, mock_db_ctx):
        """已有待处理转正事务 → 不重复创建"""
        from datetime import date, timedelta

        employee, profile = self._make_probation_employee(days_until_confirmation=5)
        existing_transaction = MagicMock()

        db = _make_db()

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Employee" in name and "Hr" not in name:
                m.join.return_value.filter.return_value.all.return_value = [employee]
                m.filter.return_value.all.return_value = []
            elif "EmployeeHrProfile" in name:
                m.filter.return_value.first.return_value = profile
            elif "HrTransaction" in name:
                m.filter.return_value.filter.return_value.filter.return_value.first.return_value = existing_transaction
            elif "Role" in name:
                m.filter.return_value.all.return_value = []
                m.filter.return_value.filter.return_value.all.return_value = []
            elif "UserRole" in name:
                m.filter.return_value.all.return_value = []
            elif "User" in name:
                m.filter.return_value.filter.return_value.all.return_value = []
                m.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch("app.common.query_filters.apply_keyword_filter", return_value=MagicMock(all=lambda: [])):
            from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder
            result = check_employee_confirmation_reminder()

        assert result["reminders_created"] == 0

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_hr_recipients_found_send_notification(self, mock_db_ctx):
        """找到 HR 接收人 → 调用 NotificationDispatcher"""
        from datetime import date, timedelta

        employee, profile = self._make_probation_employee(days_until_confirmation=3)

        db = _make_db()
        hr_role = MagicMock()
        hr_role.id = 100
        hr_user = MagicMock()
        hr_user.id = 200
        user_role = MagicMock()
        user_role.user_id = 200

        def q(model_cls):
            m = MagicMock()
            name = getattr(model_cls, "__name__", str(model_cls))
            if "Employee" in name and "Hr" not in name:
                m.join.return_value.filter.return_value.all.return_value = [employee]
                m.filter.return_value.all.return_value = []
            elif "EmployeeHrProfile" in name:
                m.filter.return_value.first.return_value = profile
            elif "HrTransaction" in name:
                m.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
            elif "Role" in name:
                filt = MagicMock()
                filt.all.return_value = [hr_role]
                filt.filter.return_value.all.return_value = [hr_role]
                m.filter.return_value = filt
            elif "UserRole" in name:
                m.filter.return_value.all.return_value = [user_role]
            elif "User" in name:
                m.filter.return_value.filter.return_value.all.return_value = [hr_user]
                m.filter.return_value.filter.return_value.filter.return_value.all.return_value = [hr_user]
            return m

        db.query.side_effect = q
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        mock_dispatcher = MagicMock()

        with patch("app.services.notification_dispatcher.NotificationDispatcher", return_value=mock_dispatcher):
            from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder
            result = check_employee_confirmation_reminder()

        assert result["reminders_created"] == 1

    @patch("app.utils.scheduled_tasks.hr_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        """异常时返回 error"""
        mock_db_ctx.return_value.__enter__.side_effect = Exception("HR任务失败")

        from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder
        result = check_employee_confirmation_reminder()

        assert "error" in result
