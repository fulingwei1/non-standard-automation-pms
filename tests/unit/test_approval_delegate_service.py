# -*- coding: utf-8 -*-
"""
Tests for ApprovalDelegateService (Simplified, Focused)
Covers: app/services/approval_engine/delegate.py
Coverage Target: 0% → 90%+
Current Coverage: 0%
File Size: 425 lines
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.services.approval_engine.delegate import ApprovalDelegateService
from app.models.approval import ApprovalDelegate
from app.models.user import User
from app.models.organization import Employee


@pytest.fixture
def delegate_service(db_session: Session):
    """Create ApprovalDelegateService instance"""
    return ApprovalDelegateService(db_session)


@pytest.fixture
def test_users(db_session: Session):
    """Create test users for delegation testing"""
    # Create employee for original approver
    original_employee = Employee(
        employee_code="EMP-001",
        name="Original Approver",
        department="Engineering",
        role="ENGINEER",
        employment_status="active",
        is_active=True,
    )
    db_session.add(original_employee)
    db_session.flush()

    # Create employee for delegate user
    delegate_employee = Employee(
        employee_code="EMP-002",
        name="Delegate User",
        department="Engineering",
        role="ENGINEER",
        employment_status="active",
        is_active=True,
    )
    db_session.add(delegate_employee)
    db_session.flush()

    # Create original approver
    original_user = User(
        employee_id=original_employee.id,
        username="original_approver",
        real_name="Original Approver",
        password_hash="hashed_password",
        is_active=True,
    )
    db_session.add(original_user)
    db_session.flush()

    # Create delegate user
    delegate_user = User(
        employee_id=delegate_employee.id,
        username="delegate_user",
        real_name="Delegate User",
        password_hash="hashed_password",
        is_active=True,
    )
    db_session.add(delegate_user)
    db_session.commit()
    db_session.refresh(original_user)
    db_session.refresh(delegate_user)

    return {"original": original_user, "delegate": delegate_user}


class TestApprovalDelegateService_GetActiveDelegate:
    """Test get_active_delegate method"""

    def test_get_active_delegate_none_configured(
        self, delegate_service: ApprovalDelegateService
    ):
        """Test when no delegate is configured for user"""
        result = delegate_service.get_active_delegate(user_id=999)
        assert result is None

    def test_get_active_delegate_all_scope(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test getting delegate with ALL scope"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create delegate with ALL scope
        delegate = ApprovalDelegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        scope="ALL",
        start_date=today,
        end_date=next_week,
        is_active=True,
        )
        db_session.add(delegate)
        db_session.commit()
        db_session.refresh(delegate)

        # Get active delegate
        result = delegate_service.get_active_delegate(user_id=test_users["original"].id)

        assert result is not None
        assert result.id == delegate.id
        assert result.scope == "ALL"

    def test_get_active_delegate_template_scope_match(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test getting delegate with TEMPLATE scope when template matches"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create delegate with TEMPLATE scope
        delegate = ApprovalDelegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        scope="TEMPLATE",
        template_ids=[100, 200, 300],
        start_date=today,
        end_date=next_week,
        is_active=True,
        )
        db_session.add(delegate)
        db_session.commit()

        # Get active delegate for matching template
        result = delegate_service.get_active_delegate(
        user_id=test_users["original"].id, template_id=200
        )

        assert result is not None
        assert result.id == delegate.id

    def test_get_active_delegate_template_scope_no_match(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test getting delegate with TEMPLATE scope when template doesn't match"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create delegate with TEMPLATE scope
        delegate = ApprovalDelegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        scope="TEMPLATE",
        template_ids=[100, 200],
        start_date=today,
        end_date=next_week,
        is_active=True,
        )
        db_session.add(delegate)
        db_session.commit()

        # Get active delegate for non-matching template
        result = delegate_service.get_active_delegate(
        user_id=test_users["original"].id, template_id=999
        )

        assert result is None

    def test_get_active_delegate_out_of_date_range(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test that expired delegates are not returned"""
        today = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)

        # Create expired delegate
        delegate = ApprovalDelegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        scope="ALL",
        start_date=yesterday,
        end_date=yesterday,
        is_active=True,
        )
        db_session.add(delegate)
        db_session.commit()

        # Get active delegate for today
        result = delegate_service.get_active_delegate(
        user_id=test_users["original"].id, check_date=today
        )

        assert result is None

    def test_get_active_delegate_inactive(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test that inactive delegates are not returned"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create inactive delegate
        delegate = ApprovalDelegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        scope="ALL",
        start_date=today,
        end_date=next_week,
        is_active=False,
        )
        db_session.add(delegate)
        db_session.commit()

        # Get active delegate
        result = delegate_service.get_active_delegate(user_id=test_users["original"].id)

        assert result is None


class TestApprovalDelegateService_CreateDelegate:
    """Test create_delegate method"""

    def test_create_delegate_success(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test creating a new delegate configuration"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        result = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        reason="Vacation",
        )

        assert result is not None
        assert result.user_id == test_users["original"].id
        assert result.delegate_id == test_users["delegate"].id
        assert result.scope == "ALL"
        assert result.reason == "Vacation"
        assert result.is_active is True

    def test_create_delegate_overlapping_dates(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test that creating overlapping delegates raises error"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create first delegate
        delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        )

        # Try to create overlapping delegate
        with pytest.raises(ValueError) as exc_info:
            delegate_service.create_delegate(
            user_id=test_users["original"].id,
            delegate_id=test_users["delegate"].id,
            start_date=date.fromordinal(today.toordinal() + 2),
            end_date=date.fromordinal(today.toordinal() + 10),
            scope="ALL",
            )

            assert "存在重叠" in str(exc_info.value)

    def test_create_delegate_with_template_ids(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test creating delegate with specific template IDs"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        result = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="TEMPLATE",
        template_ids=[100, 200, 300],
        )

        assert result.scope == "TEMPLATE"
        assert result.template_ids == [100, 200, 300]


class TestApprovalDelegateService_UpdateDelegate:
    """Test update_delegate method"""

    def test_update_delegate_success(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test updating an existing delegate"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create delegate
        created = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        )

        # Update reason
        updated = delegate_service.update_delegate(
        delegate_id=created.id, reason="Updated reason"
        )

        assert updated is not None
        assert updated.reason == "Updated reason"

    def test_update_delegate_not_found(self, delegate_service: ApprovalDelegateService):
        """Test updating non-existent delegate returns None"""
        result = delegate_service.update_delegate(delegate_id=99999, reason="test")
        assert result is None


class TestApprovalDelegateService_CancelDelegate:
    """Test cancel_delegate method"""

    def test_cancel_delegate_success(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test cancelling an active delegate"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create delegate
        created = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        )

        assert created.is_active is True

        # Cancel delegate
        result = delegate_service.cancel_delegate(delegate_id=created.id)

        # Commit the change to database
        db_session.commit()

        assert result is True

        # Verify it's marked inactive
        db_session.refresh(created)
        assert created.is_active is False

    def test_cancel_delegate_not_found(self, delegate_service: ApprovalDelegateService):
        """Test cancelling non-existent delegate returns False"""
        result = delegate_service.cancel_delegate(delegate_id=99999)
        assert result is False


class TestApprovalDelegateService_GetUserDelegates:
    """Test get_user_delegates method"""

    def test_get_user_delegates_active_only(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test getting active delegates for user"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )
        last_month = date(
        today.year, today.month - 1 if today.month > 1 else 12, today.day
        )

        # Create active delegate
        active_delegate = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        )

        # Create inactive delegate
        inactive_delegate = ApprovalDelegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        scope="ALL",
        start_date=last_month,
        end_date=date.fromordinal(last_month.toordinal() + 7),
        is_active=False,
        )
        db_session.add(inactive_delegate)
        db_session.commit()

        # Get only active delegates
        result = delegate_service.get_user_delegates(
        user_id=test_users["original"].id, include_inactive=False
        )

        assert len(result) == 1
        assert result[0].id == active_delegate.id

    def test_get_user_delegates_include_inactive(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test getting all delegates including inactive"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )
        last_month = date(
        today.year, today.month - 1 if today.month > 1 else 12, today.day
        )

        # Create active delegate
        active_delegate = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        )

        # Create inactive delegate
        inactive_delegate = ApprovalDelegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        scope="ALL",
        start_date=last_month,
        end_date=date.fromordinal(last_month.toordinal() + 7),
        is_active=False,
        )
        db_session.add(inactive_delegate)
        db_session.commit()

        # Get all delegates
        result = delegate_service.get_user_delegates(
        user_id=test_users["original"].id, include_inactive=True
        )

        assert len(result) == 2


class TestApprovalDelegateService_CleanupExpiredDelegates:
    """Test cleanup_expired_delegates method"""

    def test_cleanup_expired_delegates(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test that expired delegates are marked inactive"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )
        yesterday = date.fromordinal(today.toordinal() - 1)

        delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        )

        # Create expired delegate
        from app.models.approval import ApprovalDelegate

        expired_delegate = ApprovalDelegate(
        user_id=test_users["original"].id + 1,
        delegate_id=test_users["delegate"].id,
        scope="ALL",
        start_date=yesterday,
        end_date=yesterday,
        is_active=True,
        )
        db_session.add(expired_delegate)
        db_session.commit()

        assert expired_delegate.is_active is True

        # Cleanup expired
        delegate_service.cleanup_expired_delegates()

        # Verify expired is now inactive
        db_session.refresh(expired_delegate)
        assert expired_delegate.is_active is False

        # Verify active delegate is still active
        from app.models.approval import ApprovalDelegate

        active_delegates = (
        db_session.query(ApprovalDelegate)
        .filter(ApprovalDelegate.user_id == test_users["original"].id)
        .filter(ApprovalDelegate.is_active == True)
        .all()
        )
        assert len(active_delegates) == 1


class TestApprovalDelegateService_NotifyOriginalUser:
    """Test notify_original_user method"""

    def test_notify_original_user_without_config(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test notify original user without notify_original flag set"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create delegate WITHOUT notify_original
        delegate = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        notify_original=False,
        )

        # Create delegate log
        from app.models.approval import ApprovalDelegateLog

        log = ApprovalDelegateLog(
        delegate_config_id=delegate.id,
        task_id=999,
        instance_id=888,
        original_user_id=test_users["original"].id,
        delegate_user_id=test_users["delegate"].id,
        )
        db_session.add(log)
        db_session.commit()

        # Should not attempt to notify (no exception)
        delegate_service.notify_original_user(delegate_log_id=log.id)

        # Verify no notification was marked
        db_session.refresh(log)
        assert log.original_notified is False

    def test_notify_original_user_with_config(
        self,
        delegate_service: ApprovalDelegateService,
        db_session: Session,
        test_users: dict,
    ):
        """Test notify original user with notify_original flag set"""
        today = date.today()
        next_week = date(
        today.year, today.month + 1 if today.month < 12 else 1, today.day
        )

        # Create delegate WITH notify_original
        delegate = delegate_service.create_delegate(
        user_id=test_users["original"].id,
        delegate_id=test_users["delegate"].id,
        start_date=today,
        end_date=next_week,
        scope="ALL",
        notify_original=True,
        )

        # Create delegate log
        from app.models.approval import ApprovalDelegateLog

        log = ApprovalDelegateLog(
        delegate_config_id=delegate.id,
        task_id=999,
        instance_id=888,
        original_user_id=test_users["original"].id,
        delegate_user_id=test_users["delegate"].id,
        )
        db_session.add(log)
        db_session.commit()

        # Should attempt to notify
        delegate_service.notify_original_user(delegate_log_id=log.id)

        # Verify notification was marked
        db_session.refresh(log)
        assert log.original_notified is not None
