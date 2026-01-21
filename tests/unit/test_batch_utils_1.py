# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for utils directory modules.
Tests cover: code_config, number_generator, permission_helpers, pinyin_utils,
redis_client, scheduler, scheduler_metrics, spec_extractor, spec_match_service, spec_matcher
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

# ============================================================================
# Tests for code_config.py
# ============================================================================

from app.utils.code_config import (
    CODE_PREFIX,
    SEQ_LENGTH,
    MATERIAL_CATEGORY_CODES,
    VALID_MATERIAL_CATEGORY_CODES,
    get_material_category_code,
    validate_material_category_code,
)


class TestCodeConfig:
    """Test code_config utilities"""

    def test_code_prefix_dict(self):
        """Test CODE_PREFIX has correct structure"""
        assert "EMPLOYEE" in CODE_PREFIX
        assert "CUSTOMER" in CODE_PREFIX
        assert "MATERIAL" in CODE_PREFIX
        assert "PROJECT" in CODE_PREFIX
        assert "MACHINE" in CODE_PREFIX

    def test_seq_length_dict(self):
        """Test SEQ_LENGTH has correct structure"""
        assert "EMPLOYEE" in SEQ_LENGTH
        assert "CUSTOMER" in SEQ_LENGTH
        assert "MATERIAL" in SEQ_LENGTH
        assert "PROJECT" in SEQ_LENGTH
        assert "MACHINE" in SEQ_LENGTH

    def test_material_category_codes_dict(self):
        """Test MATERIAL_CATEGORY_CODES has correct structure"""
        assert "ME" in MATERIAL_CATEGORY_CODES
        assert "EL" in MATERIAL_CATEGORY_CODES
        assert "PN" in MATERIAL_CATEGORY_CODES
        assert "ST" in MATERIAL_CATEGORY_CODES
        assert "OT" in MATERIAL_CATEGORY_CODES

    def test_valid_material_category_codes_is_set(self):
        """Test VALID_MATERIAL_CATEGORY_CODES is a set"""
        assert isinstance(VALID_MATERIAL_CATEGORY_CODES, set)
        assert len(VALID_MATERIAL_CATEGORY_CODES) > 0

    def test_get_material_category_code_with_valid_code(self):
        """Test extracting category code from valid full code"""
        assert get_material_category_code("ME-01-01") == "ME"
        assert get_material_category_code("EL-02-03") == "EL"
        assert get_material_category_code("PN-01-01") == "PN"

    def test_get_material_category_code_with_lowercase(self):
        """Test extracting category code with lowercase input"""
        assert get_material_category_code("me-01-01") == "ME"
        assert get_material_category_code("el-02-03") == "EL"

    def test_get_material_category_code_with_empty_input(self):
        """Test extracting category code with empty input"""
        assert get_material_category_code("") == "OT"
        assert get_material_category_code(None) == "OT"

    def test_get_material_category_code_with_invalid_code(self):
        """Test extracting category code with invalid code"""
        assert get_material_category_code("XX-01-01") == "OT"
        assert get_material_category_code("INVALID") == "OT"

    def test_validate_material_category_code_valid(self):
        """Test validating valid category codes"""
        assert validate_material_category_code("ME") is True
        assert validate_material_category_code("EL") is True
        assert validate_material_category_code("PN") is True

    def test_validate_material_category_code_invalid(self):
        """Test validating invalid category codes"""
        assert validate_material_category_code("XX") is False
        assert validate_material_category_code("INVALID") is False

    def test_validate_material_category_code_case_insensitive(self):
        """Test validating category codes is case insensitive"""
        assert validate_material_category_code("me") is True
        assert validate_material_category_code("el") is True


# ============================================================================
# Tests for number_generator.py
# ============================================================================

from app.utils.number_generator import (
    generate_sequential_no,
    generate_monthly_no,
    generate_employee_code,
    generate_customer_code,
    generate_material_code,
    generate_machine_code,
    generate_calculation_code,
)


class TestNumberGenerator:
    """Test number_generator utilities"""

    @patch("app.utils.number_generator.datetime")
    def test_generate_sequential_no_with_date(self, mock_datetime):
        """Test generating sequential number with date"""
        mock_datetime.now.return_value.strftime.return_value = "250115"

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        result = generate_sequential_no(
            mock_db,
            Mock(),
            "ecn_no",
            "ECN",
            date_format="%y%m%d",
            separator="-",
            seq_length=3,
        )

        assert "ECN-250115-001" in result

    @patch("app.utils.number_generator.datetime")
    def test_generate_sequential_no_without_date(self, mock_datetime):
        """Test generating sequential number without date"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        result = generate_sequential_no(
            mock_db, Mock(), "code", "PRJ", use_date=False, separator="-", seq_length=3
        )

        assert result == "PRJ-001"

    @patch("app.utils.number_generator.datetime")
    def test_generate_sequential_no_increment(self, mock_datetime):
        """Test generating sequential number with increment"""
        mock_datetime.now.return_value.strftime.return_value = "250115"

        mock_max_record = Mock()
        mock_max_record.ecn_no = "ECN-250115-005"

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_max_record

        result = generate_sequential_no(
            mock_db,
            Mock(),
            "ecn_no",
            "ECN",
            date_format="%y%m%d",
            separator="-",
            seq_length=3,
        )

        assert "ECN-250115-006" in result

    @patch("app.utils.number_generator.datetime")
    def test_generate_monthly_no(self, mock_datetime):
        """Test generating monthly number"""
        mock_datetime.now.return_value.strftime.return_value = "2507"

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        result = generate_monthly_no(mock_db, Mock(), "lead_code", "L")

        assert result == "L2507-001"

    def test_generate_employee_code(self):
        """Test generating employee code"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.number_generator.Employee"):
            result = generate_employee_code(mock_db)
            assert result == "EMP-00001"

    def test_generate_customer_code(self):
        """Test generating customer code"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.number_generator.Customer"):
            result = generate_customer_code(mock_db)
            assert result == "CUS-0000001"

    def test_generate_material_code_with_category(self):
        """Test generating material code with category"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.number_generator.Material"):
            result = generate_material_code(mock_db, "ME-01-01")
            assert result == "MAT-ME-00001"

    def test_generate_material_code_without_category(self):
        """Test generating material code without category"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.number_generator.Material"):
            result = generate_material_code(mock_db)
            assert result == "MAT-OT-00001"

    def test_generate_machine_code(self):
        """Test generating machine code"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.number_generator.Machine"):
            result = generate_machine_code(mock_db, "PJ250708001")
            assert result == "PJ250708001-PN001"

    @patch("app.utils.number_generator.datetime")
    def test_generate_calculation_code(self, mock_datetime):
        """Test generating calculation code"""
        mock_datetime.now.return_value.strftime.return_value = "250716"

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.number_generator.BonusCalculation"):
            result = generate_calculation_code(mock_db)
            assert result == "BC-250716-001"


# ============================================================================
# Tests for permission_helpers.py
# ============================================================================

from app.utils.permission_helpers import (
    check_project_access_or_raise,
    filter_projects_by_scope,
)


class TestPermissionHelpers:
    """Test permission_helpers utilities"""

    def test_check_project_access_project_not_found(self):
        """Test check_project_access raises 404 when project not found"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.permission_helpers.Project"):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                check_project_access_or_raise(mock_db, Mock(), 999)

            assert exc_info.value.status_code == 404

    def test_check_project_access_denied(self):
        """Test check_project_access raises 403 when access denied"""
        mock_project = Mock()
        mock_project.id = 1

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project

        with patch("app.utils.permission_helpers.DataScopeService") as mock_service:
            mock_service.check_project_access.return_value = False

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                check_project_access_or_raise(mock_db, Mock(), 1)

            assert exc_info.value.status_code == 403

    def test_check_project_access_granted(self):
        """Test check_project_access returns project when access granted"""
        mock_project = Mock()
        mock_project.id = 1

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project

        with patch("app.utils.permission_helpers.DataScopeService") as mock_service:
            mock_service.check_project_access.return_value = True

            result = check_project_access_or_raise(mock_db, Mock(), 1)

            assert result == mock_project

    def test_filter_projects_by_scope(self):
        """Test filter_projects_by_scope delegates to service"""
        mock_db = Mock()
        mock_query = Mock()
        mock_user = Mock()

        with patch("app.utils.permission_helpers.DataScopeService") as mock_service:
            mock_service.filter_projects_by_scope.return_value = mock_query

            result = filter_projects_by_scope(mock_db, mock_query, mock_user)

            mock_service.filter_projects_by_scope.assert_called_once()
            assert result == mock_query


# ============================================================================
# Tests for pinyin_utils.py
# ============================================================================

from app.utils.pinyin_utils import (
    name_to_pinyin,
    name_to_pinyin_initials,
    generate_unique_username,
    generate_initial_password,
    batch_generate_pinyin_for_employees,
)


class TestPinyinUtils:
    """Test pinyin_utils utilities"""

    def test_name_to_pinyin_chinese(self):
        """Test converting Chinese name to pinyin"""
        result = name_to_pinyin("姚洪")
        assert result == "yaohong"

    def test_name_to_pinyin_empty(self):
        """Test converting empty name to pinyin"""
        assert name_to_pinyin("") == ""
        assert name_to_pinyin(None) == ""

    def test_name_to_pinyin_initials_chinese(self):
        """Test converting Chinese name to initials"""
        result = name_to_pinyin_initials("姚洪")
        assert result == "YH"

    def test_name_to_pinyin_initials_empty(self):
        """Test converting empty name to initials"""
        assert name_to_pinyin_initials("") == ""
        assert name_to_pinyin_initials(None) == ""

    def test_generate_unique_username_no_conflict(self):
        """Test generating unique username without conflict"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.pinyin_utils.User"):
            result = generate_unique_username("姚洪", mock_db)
            assert result == "yaohong"

    def test_generate_unique_username_with_conflict(self):
        """Test generating unique username with conflict"""
        mock_user = Mock()
        mock_user.username = "yaohong"

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # First call returns existing user, second returns None
        mock_query.first.side_effect = [mock_user, None]

        with patch("app.utils.pinyin_utils.User"):
            result = generate_unique_username("姚洪", mock_db)
            assert result == "yaohong2"

    def test_generate_unique_username_with_existing_set(self):
        """Test generating unique username with existing set"""
        mock_db = Mock()
        existing_usernames = {"yaohong", "yaohong2"}

        with patch("app.utils.pinyin_utils.User"):
            result = generate_unique_username("姚洪", mock_db, existing_usernames)
            assert result == "yaohong3"

    def test_generate_unique_username_empty_name(self):
        """Test generating unique username with empty name"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch("app.utils.pinyin_utils.User"):
            result = generate_unique_username("", mock_db)
            assert result == "user"

    @patch("app.utils.pinyin_utils.secrets.token_urlsafe")
    def test_generate_initial_password(self, mock_token_urlsafe):
        """Test generating initial password"""
        mock_token_urlsafe.return_value = "AbCd1234EfGh5678"

        result = generate_initial_password("username", "id123", "EMP001")

        assert len(result) == 16
        mock_token_urlsafe.assert_called_once_with(12)

    def test_batch_generate_pinyin_for_employees(self):
        """Test batch generating pinyin for employees"""
        mock_emp1 = Mock()
        mock_emp1.name = "姚洪"
        mock_emp1.pinyin_name = None

        mock_emp2 = Mock()
        mock_emp2.name = "张三"
        mock_emp2.pinyin_name = ""

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_emp1, mock_emp2]

        with patch("app.utils.pinyin_utils.Employee"):
            result = batch_generate_pinyin_for_employees(mock_db)

            assert result == 2
            mock_emp1.pinyin_name = "yaohong"
            mock_emp2.pinyin_name = "zhangsan"
            mock_db.commit.assert_called_once()

    def test_batch_generate_pinyin_for_employees_none(self):
        """Test batch generating pinyin returns 0 when no employees"""
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        with patch("app.utils.pinyin_utils.Employee"):
            result = batch_generate_pinyin_for_employees(mock_db)

            assert result == 0
            mock_db.commit.assert_not_called()


# ============================================================================
# Tests for redis_client.py
# ============================================================================

from app.utils.redis_client import (
    get_redis_client,
    close_redis_client,
)


class TestRedisClient:
    """Test redis_client utilities"""

    def setup_method(self):
        """Reset global redis client before each test"""
        import app.utils.redis_client as redis_module

        redis_module._redis_client = None

    def test_get_redis_client_not_configured(self):
        """Test get_redis_client returns None when not configured"""
        with patch("app.utils.redis_client.settings") as mock_settings:
            mock_settings.REDIS_URL = None

            result = get_redis_client()

            assert result is None

    @patch("app.utils.redis_client.redis")
    def test_get_redis_client_connection_success(self, mock_redis):
        """Test get_redis_client returns client on success"""
        with patch("app.utils.redis_client.settings") as mock_settings:
            mock_settings.REDIS_URL = "redis://localhost:6379"

            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_redis.from_url.return_value = mock_client

            result = get_redis_client()

            assert result == mock_client

    @patch("app.utils.redis_client.redis")
    def test_get_redis_client_connection_failure(self, mock_redis):
        """Test get_redis_client returns None on connection failure"""
        with patch("app.utils.redis_client.settings") as mock_settings:
            mock_settings.REDIS_URL = "redis://localhost:6379"

            from redis.exceptions import ConnectionError

            mock_redis.from_url.side_effect = ConnectionError("Connection failed")

            result = get_redis_client()

            assert result is None

    def test_get_redis_client_cached(self):
        """Test get_redis_client returns cached client"""
        import app.utils.redis_client as redis_module

        with patch("app.utils.redis_client.settings") as mock_settings:
            mock_settings.REDIS_URL = None

            redis_module._redis_client = Mock()
            result = get_redis_client()

            assert result is not None

    def test_close_redis_client(self):
        """Test close_redis_client closes connection"""
        import app.utils.redis_client as redis_module

        mock_client = Mock()
        redis_module._redis_client = mock_client

        close_redis_client()

        mock_client.close.assert_called_once()
        assert redis_module._redis_client is None

    def test_close_redis_client_none(self):
        """Test close_redis_client with no client"""
        import app.utils.redis_client as redis_module

        redis_module._redis_client = None

        # Should not raise exception
        close_redis_client()


# ============================================================================
# Tests for scheduler.py
# ============================================================================

from app.utils.scheduler import (
    _resolve_callable,
    _wrap_job_callable,
    _load_task_config_from_db,
    init_scheduler,
    shutdown_scheduler,
)


class TestScheduler:
    """Test scheduler utilities"""

    def test_resolve_callable(self):
        """Test resolving callable from task config"""
        task = {"module": "os.path", "callable": "join"}

        result = _resolve_callable(task)

        assert callable(result)

    @patch("app.utils.scheduler.time.time")
    def test_wrap_job_callable_success(self, mock_time):
        """Test wrapping job callable on success"""
        mock_time.side_effect = [0.0, 0.5]

        task = {
            "id": "test_job",
            "name": "Test Job",
            "owner": "admin",
            "category": "test",
        }

        test_func = Mock(return_value="success")

        with patch("app.utils.scheduler.record_job_success"):
            wrapper = _wrap_job_callable(test_func, task)
            result = wrapper()

            assert result == "success"

    @patch("app.utils.scheduler.time.time")
    def test_wrap_job_callable_failure(self, mock_time):
        """Test wrapping job callable on failure"""
        mock_time.side_effect = [0.0, 0.5]

        task = {
            "id": "test_job",
            "name": "Test Job",
            "owner": "admin",
            "category": "test",
        }

        test_func = Mock(side_effect=Exception("Test error"))

        with patch("app.utils.scheduler.record_job_failure"):
            wrapper = _wrap_job_callable(test_func, task)

            with pytest.raises(Exception):
                wrapper()

    def test_load_task_config_from_db_not_enabled(self):
        """Test loading task config when not enabled"""
        with patch("app.utils.scheduler.get_db_session") as mock_get_db:
            mock_db = Mock()
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None

            mock_get_db.return_value.__enter__.return_value = mock_db

            result = _load_task_config_from_db("test_task")

            assert result is None

    def test_load_task_config_from_db_enabled(self):
        """Test loading task config when enabled"""
        with patch("app.utils.scheduler.get_db_session") as mock_get_db:
            mock_config = Mock()
            mock_config.is_enabled = True
            mock_config.cron_config = {"hour": 2}

            mock_db = Mock()
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_config

            mock_get_db.return_value.__enter__.return_value = mock_db

            result = _load_task_config_from_db("test_task")

            assert result is not None
            assert result["enabled"] is True
            assert result["cron"] == {"hour": 2}

    def test_load_task_config_from_db_exception(self):
        """Test loading task config on exception"""
        with patch("app.utils.scheduler.get_db_session") as mock_get_db:
            mock_get_db.side_effect = Exception("DB error")

            result = _load_task_config_from_db("test_task")

            assert result is None

    @patch("app.utils.scheduler.scheduler")
    @patch("app.utils.scheduler.SCHEDULER_TASKS", [])
    def test_init_scheduler_no_tasks(self, mock_scheduler):
        """Test initializing scheduler with no tasks"""
        result = init_scheduler()

        mock_scheduler.add_listener.assert_called_once()
        mock_scheduler.start.assert_called_once()
        assert result == mock_scheduler

    @patch("app.utils.scheduler.scheduler")
    @patch(
        "app.utils.scheduler.SCHEDULER_TASKS",
        [
            {
                "id": "test_job",
                "name": "Test Job",
                "enabled": False,
                "cron": {},
                "module": "os.path",
                "callable": "join",
            }
        ],
    )
    def test_init_scheduler_task_disabled(self, mock_scheduler):
        """Test initializing scheduler with disabled task"""
        result = init_scheduler()

        assert result == mock_scheduler
        mock_scheduler.add_job.assert_not_called()

    @patch("app.utils.scheduler.scheduler")
    @patch(
        "app.utils.scheduler.SCHEDULER_TASKS",
        [
            {
                "id": "test_job",
                "name": "Test Job",
                "enabled": True,
                "cron": {"hour": 2},
                "module": "os.path",
                "callable": "join",
            }
        ],
    )
    def test_init_scheduler_task_enabled(self, mock_scheduler):
        """Test initializing scheduler with enabled task"""
        result = init_scheduler()

        assert result == mock_scheduler
        mock_scheduler.add_job.assert_called_once()

    @patch("app.utils.scheduler.scheduler")
    def test_shutdown_scheduler(self, mock_scheduler):
        """Test shutting down scheduler"""
        mock_scheduler.running = True

        shutdown_scheduler()

        mock_scheduler.shutdown.assert_called_once()


# ============================================================================
# Tests for scheduler_metrics.py
# ============================================================================

from app.utils.scheduler_metrics import (
    SchedulerMetrics,
    METRICS,
    record_job_success,
    record_job_failure,
    record_notification_success,
    record_notification_failure,
    get_metrics_snapshot,
)


class TestSchedulerMetrics:
    """Test scheduler_metrics utilities"""

    def setup_method(self):
        """Reset metrics before each test"""
        METRICS.reset()

    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = SchedulerMetrics()

        assert metrics._max_history_size == 1000
        assert len(metrics._data) == 0
        assert len(metrics._duration_history) == 0

    def test_record_success(self):
        """Test recording successful job"""
        METRICS.record_success("job1", 150.5, "2025-01-19T00:00:00Z")

        data = METRICS.snapshot()["jobs"]
        assert "job1" in data
        assert data["job1"]["success_count"] == 1
        assert data["job1"]["last_duration_ms"] == 150.5

    def test_record_failure(self):
        """Test recording failed job"""
        METRICS.record_failure("job1", 200.0, "2025-01-19T00:00:00Z")

        data = METRICS.snapshot()["jobs"]
        assert "job1" in data
        assert data["job1"]["failure_count"] == 1
        assert data["job1"]["last_status"] == "failed"

    def test_record_notification_success(self):
        """Test recording successful notification"""
        METRICS.record_notification("EMAIL", True)

        stats = METRICS.snapshot()["notifications"]
        assert "EMAIL" in stats
        assert stats["EMAIL"]["success_count"] == 1

    def test_record_notification_failure(self):
        """Test recording failed notification"""
        METRICS.record_notification("EMAIL", False)

        stats = METRICS.snapshot()["notifications"]
        assert "EMAIL" in stats
        assert stats["EMAIL"]["failure_count"] == 1

    def test_record_notification_case_insensitive(self):
        """Test recording notification with case insensitive channel"""
        METRICS.record_notification("email", True)

        stats = METRICS.snapshot()["notifications"]
        assert "EMAIL" in stats

    def test_reset(self):
        """Test resetting metrics"""
        METRICS.record_success("job1", 100.0, "2025-01-19T00:00:00Z")
        METRICS.reset()

        snapshot = METRICS.snapshot()
        assert len(snapshot["jobs"]) == 0
        assert len(snapshot["notifications"]) == 0

    def test_get_statistics_empty(self):
        """Test getting statistics for job with no history"""
        stats = METRICS.get_statistics("job1")

        assert stats["avg_duration_ms"] is None
        assert stats["sample_count"] == 0

    def test_get_statistics_with_data(self):
        """Test getting statistics with data"""
        METRICS.record_success("job1", 100.0, "2025-01-19T00:00:00Z")
        METRICS.record_success("job1", 200.0, "2025-01-19T00:00:00Z")
        METRICS.record_success("job1", 300.0, "2025-01-19T00:00:00Z")

        stats = METRICS.get_statistics("job1")

        assert stats["avg_duration_ms"] == 200.0
        assert stats["min_duration_ms"] == 100.0
        assert stats["max_duration_ms"] == 300.0
        assert stats["sample_count"] == 3

    def test_get_all_statistics(self):
        """Test getting statistics for all jobs"""
        METRICS.record_success("job1", 100.0, "2025-01-19T00:00:00Z")
        METRICS.record_success("job2", 200.0, "2025-01-19T00:00:00Z")

        all_stats = METRICS.get_all_statistics()

        assert "job1" in all_stats
        assert "job2" in all_stats

    def test_module_level_functions(self):
        """Test module-level metric functions"""
        record_job_success("job1", 100.0, "2025-01-19T00:00:00Z")
        record_job_failure("job2", 200.0, "2025-01-19T00:00:00Z")
        record_notification_success("EMAIL")
        record_notification_failure("SMS")

        snapshot = get_metrics_snapshot()
        assert "job1" in snapshot["jobs"]
        assert "job2" in snapshot["jobs"]
        assert "EMAIL" in snapshot["notifications"]
        assert "SMS" in snapshot["notifications"]


# ============================================================================
# Tests for spec_extractor.py
# ============================================================================

from app.utils.spec_extractor import (
    SpecExtractor,
)


class TestSpecExtractor:
    """Test spec_extractor utilities"""

    def test_spec_extractor_initialization(self):
        """Test SpecExtractor initialization"""
        extractor = SpecExtractor()
        assert extractor is not None

    def test_extract_key_parameters_voltage(self):
        """Test extracting voltage parameter"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("电压220V")

        assert "voltage" in result
        assert result["voltage"] == "220"

    def test_extract_key_parameters_current(self):
        """Test extracting current parameter"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("电流5A")

        assert "current" in result
        assert result["current"] == "5"

    def test_extract_key_parameters_accuracy(self):
        """Test extracting accuracy parameter"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("精度±0.1%")

        assert "accuracy" in result
        assert result["accuracy"] == "0.1"

    def test_extract_key_parameters_temperature(self):
        """Test extracting temperature range"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("温度范围-20~60℃")

        assert "temp_min" in result
        assert "temp_max" in result
        assert result["temp_min"] == "-20"
        assert result["temp_max"] == "60"

    def test_extract_key_parameters_power(self):
        """Test extracting power parameter"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("功率100W")

        assert "power" in result
        assert result["power"] == "100"

    def test_extract_key_parameters_frequency(self):
        """Test extracting frequency parameter"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("频率50Hz")

        assert "frequency" in result
        assert result["frequency"] == "50"

    def test_extract_key_parameters_size(self):
        """Test extracting size parameters"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("尺寸100x200x50mm")

        assert "length" in result
        assert "width" in result
        assert "height" in result
        assert result["length"] == "100"
        assert result["width"] == "200"
        assert result["height"] == "50"

    def test_extract_key_parameters_empty(self):
        """Test extracting parameters from empty string"""
        extractor = SpecExtractor()

        result = extractor.extract_key_parameters("")

        assert len(result) == 0

    def test_extract_from_document_manual_mode(self):
        """Test extracting from document in manual mode"""
        extractor = SpecExtractor()

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        mock_document = Mock()
        mock_document.id = 1
        mock_document.project_id = 1
        mock_document.file_type = None
        mock_document.file_path = "/path/to/file.xlsx"

        with patch("app.utils.spec_extractor.ProjectDocument"):
            result = extractor.extract_from_document(
                mock_db, 1, 1, 1, auto_extract=False
            )

            assert result == []

    def test_create_requirement(self):
        """Test creating requirement"""
        extractor = SpecExtractor()

        mock_db = Mock()
        mock_db.flush = Mock()

        with patch("app.utils.spec_extractor.TechnicalSpecRequirement") as MockReq:
            mock_req = Mock()
            MockReq.return_value = mock_req

            result = extractor.create_requirement(
                mock_db, 1, 1, "test_material", "test_spec", 1
            )

            assert result is not None
            mock_db.add.assert_called_once_with(mock_req)


# ============================================================================
# Tests for spec_match_service.py
# ============================================================================

from app.utils.spec_match_service import (
    SpecMatchService,
)


class TestSpecMatchService:
    """Test spec_match_service utilities"""

    def test_service_initialization(self):
        """Test SpecMatchService initialization"""
        service = SpecMatchService()

        assert service.matcher is not None

    def test_check_po_item_spec_match_no_requirements(self):
        """Test checking PO item when no requirements exist"""
        service = SpecMatchService()

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = service.check_po_item_spec_match(mock_db, 1, 1, "MAT001", "spec123")

        assert result is None

    def test_check_po_item_spec_match_with_requirement(self):
        """Test checking PO item with matching requirement"""
        service = SpecMatchService()

        mock_req = Mock()
        mock_req.id = 1
        mock_req.material_code = None
        mock_req.specification = "spec123"
        mock_req.brand = None
        mock_req.model = None
        mock_req.key_parameters = {}

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_req]

        with patch.object(service.matcher, "match_specification") as mock_match:
            mock_result = Mock()
            mock_result.match_status = "MATCHED"
            mock_result.match_score = Decimal("90")
            mock_result.differences = {}
            mock_match.return_value = mock_result

            with patch("app.utils.spec_match_service.SpecMatchRecord") as MockRecord:
                mock_record = Mock()
                mock_record.id = 1
                MockRecord.return_value = mock_record

                result = service.check_po_item_spec_match(
                    mock_db, 1, 1, "MAT001", "spec123"
                )

                assert result is not None

    def test_check_bom_item_spec_match_no_requirements(self):
        """Test checking BOM item when no requirements exist"""
        service = SpecMatchService()

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = service.check_bom_item_spec_match(mock_db, 1, 1, "MAT001", "spec123")

        assert result is None

    def test_check_bom_item_spec_match_with_requirement(self):
        """Test checking BOM item with matching requirement"""
        service = SpecMatchService()

        mock_req = Mock()
        mock_req.id = 1
        mock_req.material_code = None
        mock_req.specification = "spec123"
        mock_req.brand = None
        mock_req.model = None
        mock_req.key_parameters = {}
        mock_req.material_name = "Test Material"

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_req]

        with patch.object(service.matcher, "match_specification") as mock_match:
            mock_result = Mock()
            mock_result.match_status = "MISMATCHED"
            mock_result.match_score = Decimal("60")
            mock_result.differences = {"specification": "diff"}
            mock_match.return_value = mock_result

            with patch("app.utils.spec_match_service.SpecMatchRecord") as MockRecord:
                mock_record = Mock()
                mock_record.id = 1
                MockRecord.return_value = mock_record

                with patch.object(service, "_create_alert"):
                    result = service.check_bom_item_spec_match(
                        mock_db, 1, 1, "MAT001", "spec456"
                    )

                    assert result is not None

    def test_create_alert_creates_rule(self):
        """Test _create_alert creates rule if not exists"""
        service = SpecMatchService()

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        mock_req = Mock()
        mock_req.id = 1
        mock_req.material_name = "Test Material"

        mock_result = Mock()
        mock_result.match_score = Decimal("60")
        mock_result.differences = {}

        with patch("app.utils.spec_match_service.AlertRule"):
            with patch("app.utils.spec_match_service.AlertRecord"):
                service._create_alert(mock_db, 1, 1, mock_req, mock_result)

                # Should add both rule and alert
                assert mock_db.add.call_count >= 1


# ============================================================================
# Tests for spec_matcher.py
# ============================================================================

from app.utils.spec_matcher import (
    SpecMatchResult,
    SpecMatcher,
)


class TestSpecMatcher:
    """Test spec_matcher utilities"""

    def test_spec_match_result_initialization(self):
        """Test SpecMatchResult initialization"""
        result = SpecMatchResult(
            match_status="MATCHED", match_score=Decimal("90"), differences={}
        )

        assert result.match_status == "MATCHED"
        assert result.match_score == Decimal("90")
        assert result.differences == {}

    def test_spec_matcher_initialization(self):
        """Test SpecMatcher initialization"""
        matcher = SpecMatcher()

        assert matcher.extractor is not None
        assert matcher.match_threshold == Decimal("80.0")

    def test_text_similarity(self):
        """Test text similarity calculation"""
        matcher = SpecMatcher()

        similarity = matcher._text_similarity("test spec", "test spec")

        assert similarity == 1.0

    def test_text_similarity_different(self):
        """Test text similarity with different strings"""
        matcher = SpecMatcher()

        similarity = matcher._text_similarity("test spec", "other spec")

        assert 0 < similarity < 1

    def test_match_specification_perfect_match(self):
        """Test matching specification with perfect match"""
        matcher = SpecMatcher()

        mock_req = Mock()
        mock_req.specification = "220V 5A"
        mock_req.brand = None
        mock_req.model = None
        mock_req.key_parameters = {}
        mock_req.requirement_level = "REQUIRED"

        result = matcher.match_specification(mock_req, "220V 5A", None, None)

        assert result.match_status == "MATCHED"
        assert result.match_score >= matcher.match_threshold

    def test_match_specification_brand_mismatch(self):
        """Test matching specification with brand mismatch"""
        matcher = SpecMatcher()

        mock_req = Mock()
        mock_req.specification = "220V"
        mock_req.brand = "SIEMENS"
        mock_req.model = None
        mock_req.key_parameters = {}
        mock_req.requirement_level = "REQUIRED"

        result = matcher.match_specification(mock_req, "220V", "ABB", None)

        assert result.match_status == "MISMATCHED"
        assert result.differences is not None
        assert "brand" in result.differences

    def test_match_specification_model_mismatch(self):
        """Test matching specification with model mismatch"""
        matcher = SpecMatcher()

        mock_req = Mock()
        mock_req.specification = "220V"
        mock_req.brand = None
        mock_req.model = "S7-1200"
        mock_req.key_parameters = {}
        mock_req.requirement_level = "REQUIRED"

        result = matcher.match_specification(mock_req, "220V", None, "S7-1500")

        assert result.match_status == "MISMATCHED"
        assert "model" in result.differences

    def test_compare_parameters_empty(self):
        """Test comparing parameters with empty dicts"""
        matcher = SpecMatcher()

        result = matcher._compare_parameters({}, {})

        assert len(result) == 0

    def test_compare_parameters_missing(self):
        """Test comparing parameters with missing actual value"""
        matcher = SpecMatcher()

        result = matcher._compare_parameters({"voltage": "220"}, {})

        assert "voltage" in result
        assert result["voltage"]["missing"] is True

    def test_compare_parameters_match(self):
        """Test comparing parameters with matching values"""
        matcher = SpecMatcher()

        result = matcher._compare_parameters({"voltage": "220"}, {"voltage": "220"})

        assert len(result) == 0

    def test_compare_parameters_numeric_diff(self):
        """Test comparing parameters with numeric difference"""
        matcher = SpecMatcher()

        result = matcher._compare_parameters({"voltage": "220"}, {"voltage": "230"})

        assert "voltage" in result
        assert "deviation" in result["voltage"]

    def test_calculate_param_score_empty(self):
        """Test calculating parameter score with empty required"""
        matcher = SpecMatcher()

        score = matcher._calculate_param_score({}, {})

        assert score == 100.0

    def test_calculate_param_score_all_match(self):
        """Test calculating parameter score with all matches"""
        matcher = SpecMatcher()

        score = matcher._calculate_param_score(
            {"voltage": "220", "current": "5"}, {"voltage": "220", "current": "5"}
        )

        assert score == 100.0

    def test_calculate_param_score_partial_match(self):
        """Test calculating parameter score with partial matches"""
        matcher = SpecMatcher()

        score = matcher._calculate_param_score(
            {"voltage": "220", "current": "5"}, {"voltage": "220"}
        )

        assert score == 50.0

    def test_match_specification_with_parameters(self):
        """Test matching specification with parameters"""
        matcher = SpecMatcher()

        mock_req = Mock()
        mock_req.specification = "220V 5A"
        mock_req.brand = None
        mock_req.model = None
        mock_req.key_parameters = {"voltage": "220", "current": "5"}
        mock_req.requirement_level = "REQUIRED"

        with patch.object(matcher.extractor, "extract_key_parameters") as mock_extract:
            mock_extract.return_value = {"voltage": "220", "current": "5"}

            result = matcher.match_specification(mock_req, "220V 5A", None, None)

            assert result.match_status == "MATCHED"

    def test_match_specification_low_score(self):
        """Test matching specification with low score"""
        matcher = SpecMatcher()

        mock_req = Mock()
        mock_req.specification = "220V 5A"
        mock_req.brand = None
        mock_req.model = None
        mock_req.key_parameters = {}
        mock_req.requirement_level = "REQUIRED"

        result = matcher.match_specification(
            mock_req, "completely different spec", None, None
        )

        assert result.match_score < Decimal("50.0")
        assert result.match_status == "UNKNOWN"
