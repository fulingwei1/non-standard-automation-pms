# -*- coding: utf-8 -*-
"""
Tests for app/core/account_lockout.py (in-memory AccountLockout)
Standalone unit tests – no DB, no Redis, no fixtures needed.
"""
import time
import threading
import pytest

from app.core.account_lockout import AccountLockout, account_lockout


class TestAccountLockoutBasics:
    """Basic functionality tests."""

    def setup_method(self):
        self.lockout = AccountLockout()

    def test_initial_state_not_locked(self):
        locked, remaining = self.lockout.is_locked("user1")
        assert locked is False
        assert remaining == 0.0

    def test_remaining_attempts_initial(self):
        assert self.lockout.remaining_attempts("user1") == AccountLockout.MAX_FAILURES

    def test_single_failure_not_locked(self):
        result = self.lockout.record_failure("user1")
        assert result is False  # not yet locked

    def test_failure_decrements_remaining_attempts(self):
        self.lockout.record_failure("user1")
        assert self.lockout.remaining_attempts("user1") == AccountLockout.MAX_FAILURES - 1

    def test_reset_clears_failure_count(self):
        self.lockout.record_failure("user1")
        self.lockout.record_failure("user1")
        self.lockout.reset("user1")
        assert self.lockout.remaining_attempts("user1") == AccountLockout.MAX_FAILURES

    def test_reset_non_existent_user(self):
        # Should not raise
        self.lockout.reset("no_such_user")

    def test_is_locked_for_non_existent_user(self):
        locked, remaining = self.lockout.is_locked("no_such_user")
        assert locked is False
        assert remaining == 0.0


class TestAccountLockoutThreshold:
    """Test that reaching MAX_FAILURES triggers lockout."""

    def setup_method(self):
        self.lockout = AccountLockout()
        self.user = "test_user"

    def _reach_threshold(self):
        """Record MAX_FAILURES consecutive failures."""
        result = False
        for _ in range(AccountLockout.MAX_FAILURES):
            result = self.lockout.record_failure(self.user)
        return result

    def test_max_failures_triggers_lock(self):
        result = self._reach_threshold()
        assert result is True  # last call should trigger lockout

    def test_account_is_locked_after_threshold(self):
        self._reach_threshold()
        locked, remaining = self.lockout.is_locked(self.user)
        assert locked is True

    def test_remaining_seconds_positive_after_lock(self):
        self._reach_threshold()
        locked, remaining = self.lockout.is_locked(self.user)
        assert locked is True
        assert remaining > 0
        assert remaining <= AccountLockout.LOCKOUT_DURATION

    def test_remaining_attempts_zero_after_lock(self):
        self._reach_threshold()
        assert self.lockout.remaining_attempts(self.user) == 0

    def test_reset_after_lock_removes_lock(self):
        self._reach_threshold()
        self.lockout.reset(self.user)
        locked, remaining = self.lockout.is_locked(self.user)
        assert locked is False
        assert remaining == 0.0


class TestAccountLockoutExpiry:
    """Test that lockout expires automatically."""

    def test_expired_lock_clears_on_check(self):
        lockout = AccountLockout()
        user = "expire_user"

        # Trigger lockout
        for _ in range(AccountLockout.MAX_FAILURES):
            lockout.record_failure(user)

        # Manually override the locked_until to the past
        with lockout._lock:
            lockout._locked_until[user] = time.time() - 1  # already expired

        locked, remaining = lockout.is_locked(user)
        assert locked is False
        assert remaining == 0.0

        # The lock entry should have been cleaned up
        with lockout._lock:
            assert user not in lockout._locked_until


class TestAccountLockoutMultipleUsers:
    """Verify that different users are isolated."""

    def setup_method(self):
        self.lockout = AccountLockout()

    def test_different_users_isolated(self):
        for _ in range(AccountLockout.MAX_FAILURES):
            self.lockout.record_failure("user_a")

        locked_a, _ = self.lockout.is_locked("user_a")
        locked_b, _ = self.lockout.is_locked("user_b")
        assert locked_a is True
        assert locked_b is False

    def test_reset_user_a_doesnt_affect_user_b(self):
        for _ in range(AccountLockout.MAX_FAILURES):
            self.lockout.record_failure("user_a")
        self.lockout.record_failure("user_b")

        self.lockout.reset("user_a")
        assert self.lockout.is_locked("user_a")[0] is False
        assert self.lockout.remaining_attempts("user_b") == AccountLockout.MAX_FAILURES - 1


class TestAccountLockoutThreadSafety:
    """Thread-safety smoke test."""

    def test_concurrent_failures_dont_crash(self):
        lockout = AccountLockout()
        errors = []

        def do_failures():
            try:
                for _ in range(3):
                    lockout.record_failure("shared_user")
                    lockout.is_locked("shared_user")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_failures) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []


class TestGlobalSingleton:
    """Verify the module-level singleton works."""

    def test_singleton_is_account_lockout_instance(self):
        assert isinstance(account_lockout, AccountLockout)

    def test_singleton_record_and_check(self):
        # Use a unique username to avoid interference with other tests
        user = f"singleton_test_user_{id(self)}"
        account_lockout.record_failure(user)
        attempts = account_lockout.remaining_attempts(user)
        assert attempts == AccountLockout.MAX_FAILURES - 1
        account_lockout.reset(user)


class TestAccountLockoutWindowCleanup:
    """Failures older than LOCKOUT_DURATION should not count."""

    def test_old_failures_dont_count_towards_lockout(self):
        lockout = AccountLockout()
        user = "old_failures_user"

        # Inject stale failure timestamps manually
        old_time = time.time() - lockout.LOCKOUT_DURATION - 1
        with lockout._lock:
            lockout._failures[user] = [old_time] * (AccountLockout.MAX_FAILURES - 1)

        # One more failure (fresh) should not trigger lockout
        result = lockout.record_failure(user)
        assert result is False

    def test_remaining_attempts_ignores_old_failures(self):
        lockout = AccountLockout()
        user = "old_remaining_user"

        old_time = time.time() - lockout.LOCKOUT_DURATION - 1
        with lockout._lock:
            lockout._failures[user] = [old_time] * 3

        # All stale → remaining should be MAX_FAILURES - 0 = MAX_FAILURES
        # Actually after the stale record_failure, let's just call remaining_attempts
        remaining = lockout.remaining_attempts(user)
        # Stale records are cleaned up only on record_failure, not on remaining_attempts
        # remaining_attempts itself filters old records
        assert remaining == AccountLockout.MAX_FAILURES
