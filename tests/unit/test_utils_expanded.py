# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for utils modules.
Target: 70-80% coverage per util module.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.utils.wechat_client import WeChatTokenCache, WeChatClient
from app.utils.project_utils import generate_project_code, init_project_stages
from app.utils.number_generator import (
    generate_sequential_no,
    generate_monthly_no,
    generate_employee_code,
    generate_customer_code,
    generate_material_code,
    generate_machine_code,
    generate_calculation_code,
)
from app.utils.code_config import (
    get_material_category_code,
    validate_material_category_code,
    CODE_PREFIX,
    SEQ_LENGTH,
    MATERIAL_CATEGORY_CODES,
)
from app.utils.pinyin_utils import (
    name_to_pinyin,
    name_to_pinyin_initials,
    generate_unique_username,
    generate_initial_password,
    batch_generate_pinyin_for_employees,
)
from app.utils.spec_extractor import SpecExtractor
from app.utils.spec_match_service import SpecMatchService
from app.utils.spec_matcher import SpecMatcher
from app.utils.redis_client import get_redis_client, close_redis_client


# =============================================================================
# wechat_client.py Tests (aiming for >70% coverage)
# =============================================================================


class TestWeChatTokenCache:
    """Tests for WeChatTokenCache class."""

    def setup_method(self):
        """Clear cache before each test."""
        WeChatTokenCache._cache.clear()

    def test_get_nonexistent_key(self):
        """Test getting a non-existent key."""
        result = WeChatTokenCache.get("nonexistent")
        assert result is None

    def test_get_expired_token(self):
        """Test getting an expired token."""
        expired_time = datetime.now() - timedelta(minutes=10)
        WeChatTokenCache._cache["test_key"] = {
            "token": "test_token",
            "expires_at": expired_time,
            "created_at": datetime.now(),
        }
        result = WeChatTokenCache.get("test_key")
        assert result is None

    def test_get_near_expired_token(self):
        """Test getting a token that expires in less than 5 minutes."""
        near_expired = datetime.now() + timedelta(minutes=4)
        WeChatTokenCache._cache["test_key"] = {
            "token": "test_token",
            "expires_at": near_expired,
            "created_at": datetime.now(),
        }
        result = WeChatTokenCache.get("test_key")
        assert result is None

    def test_get_valid_token(self):
        """Test getting a valid token."""
        valid_time = datetime.now() + timedelta(minutes=10)
        WeChatTokenCache._cache["test_key"] = {
            "token": "valid_token",
            "expires_at": valid_time,
            "created_at": datetime.now(),
        }
        result = WeChatTokenCache.get("test_key")
        assert result == "valid_token"

    def test_set_token(self):
        """Test setting a token in cache."""
        WeChatTokenCache.set("test_key", "new_token", 7200)
        assert "test_key" in WeChatTokenCache._cache
        assert WeChatTokenCache._cache["test_key"]["token"] == "new_token"
        assert isinstance(WeChatTokenCache._cache["test_key"]["expires_at"], datetime)

    def test_clear_specific_key(self):
        """Test clearing a specific key."""
        WeChatTokenCache._cache["key1"] = {"token": "t1", "expires_at": datetime.now()}
        WeChatTokenCache._cache["key2"] = {"token": "t2", "expires_at": datetime.now()}
        WeChatTokenCache.clear("key1")
        assert "key1" not in WeChatTokenCache._cache
        assert "key2" in WeChatTokenCache._cache

    def test_clear_all_keys(self):
        """Test clearing all keys."""
        WeChatTokenCache._cache["key1"] = {"token": "t1", "expires_at": datetime.now()}
        WeChatTokenCache._cache["key2"] = {"token": "t2", "expires_at": datetime.now()}
        WeChatTokenCache.clear()
        assert len(WeChatTokenCache._cache) == 0


class TestWeChatClient:
    """Tests for WeChatClient class."""

    @patch("app.utils.wechat_client.settings")
    def test_init_with_config(self, mock_settings):
        """Test initialization with settings."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"
        client = WeChatClient()
        assert client.corp_id == "test_corp_id"
        assert client.agent_id == "test_agent_id"
        assert client.secret == "test_secret"

    @patch("app.utils.wechat_client.settings")
    def test_init_with_parameters(self, mock_settings):
        """Test initialization with parameters."""
        client = WeChatClient(
            corp_id="custom_corp_id",
            agent_id="custom_agent_id",
            secret="custom_secret",
        )
        assert client.corp_id == "custom_corp_id"
        assert client.agent_id == "custom_agent_id"
        assert client.secret == "custom_secret"

    @patch("app.utils.wechat_client.settings")
    def test_init_missing_config(self, mock_settings):
        """Test initialization with missing config raises ValueError."""
        mock_settings.WECHAT_CORP_ID = None
        mock_settings.WECHAT_AGENT_ID = None
        mock_settings.WECHAT_SECRET = None
        with pytest.raises(ValueError, match="企业微信配置不完整"):
            WeChatClient()

    @patch("app.utils.wechat_client.settings")
    def test_get_access_token_from_cache(self, mock_settings):
        """Test getting access token from cache."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        WeChatTokenCache._cache["wechat_access_token"] = {
            "token": "cached_token",
            "expires_at": datetime.now() + timedelta(minutes=10),
            "created_at": datetime.now(),
        }

        client = WeChatClient()
        token = client.get_access_token()
        assert token == "cached_token"

    @patch("app.utils.wechat_client.requests.get")
    @patch("app.utils.wechat_client.settings")
    def test_get_access_token_from_api(self, mock_settings, mock_get):
        """Test getting access token from API."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errcode": 0,
            "access_token": "new_token",
            "expires_in": 7200,
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = WeChatClient()
        token = client.get_access_token(force_refresh=True)
        assert token == "new_token"
        assert WeChatTokenCache.get("wechat_access_token") == "new_token"

    @patch("app.utils.wechat_client.requests.get")
    @patch("app.utils.wechat_client.settings")
    def test_get_access_token_api_error(self, mock_settings, mock_get):
        """Test getting access token with API error."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errcode": 40001,
            "errmsg": "invalid credential",
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = WeChatClient()
        with pytest.raises(Exception, match="获取access_token失败"):
            client.get_access_token(force_refresh=True)

    @patch("app.utils.wechat_client.requests.get")
    @patch("app.utils.wechat_client.settings")
    def test_get_access_token_network_error(self, mock_settings, mock_get):
        """Test getting access token with network error."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        client = WeChatClient()
        with pytest.raises(Exception, match="请求企业微信API失败"):
            client.get_access_token(force_refresh=True)

    @patch("app.utils.wechat_client.settings")
    def test_send_message_empty_user_ids(self, mock_settings):
        """Test sending message with empty user IDs."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        client = WeChatClient()
        result = client.send_message(
            [], {"msgtype": "text", "text": {"content": "test"}}
        )
        assert result is False

    @patch("app.utils.wechat_client.requests.post")
    @patch("app.utils.wechat_client.settings")
    def test_send_text_message_success(self, mock_settings, mock_post):
        """Test sending text message successfully."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        # Mock token response
        with patch.object(WeChatClient, "get_access_token", return_value="test_token"):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            client = WeChatClient()
            result = client.send_text_message(["user1"], "Test message")
            assert result is True

    @patch("app.utils.wechat_client.requests.post")
    @patch("app.utils.wechat_client.settings")
    def test_send_template_card_success(self, mock_settings, mock_post):
        """Test sending template card successfully."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        with patch.object(WeChatClient, "get_access_token", return_value="test_token"):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            client = WeChatClient()
            card = {"card_type": "text_notice"}
            result = client.send_template_card(["user1"], card)
            assert result is True

    @patch("app.utils.wechat_client.requests.post")
    @patch("app.utils.wechat_client.settings")
    @patch("app.utils.wechat_client.time.sleep")
    def test_send_message_with_retry(self, mock_sleep, mock_settings, mock_post):
        """Test sending message with retry on failure."""
        mock_settings.WECHAT_CORP_ID = "test_corp_id"
        mock_settings.WECHAT_AGENT_ID = "test_agent_id"
        mock_settings.WECHAT_SECRET = "test_secret"

        with patch.object(WeChatClient, "get_access_token", return_value="test_token"):
            # First call fails, second succeeds
            mock_response_fail = Mock()
            mock_response_fail.status_code = 200
            mock_response_fail.json.return_value = {
                "errcode": -1,
                "errmsg": "system error",
            }
            mock_response_fail.raise_for_status = Mock()

            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"errcode": 0, "errmsg": "ok"}
            mock_response_success.raise_for_status = Mock()

            mock_post.side_effect = [mock_response_fail, mock_response_success]

            client = WeChatClient()
            result = client.send_message(["user1"], {"msgtype": "text"}, retry_times=2)
            assert result is True


# =============================================================================
# project_utils.py Tests (aiming for >70% coverage)
# =============================================================================


class TestProjectUtils:
    """Tests for project_utils module."""

    @patch("app.utils.project_utils.generate_sequential_no")
    def test_generate_project_code(self, mock_generate):
        """Test generating project code."""
        mock_generate.return_value = "PJ250708001"
        db_mock = Mock()

        code = generate_project_code(db_mock)
        assert code == "PJ250708001"

        # Verify the call parameters
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["prefix"] == "PJ"
        assert call_kwargs["date_format"] == "%y%m%d"
        assert call_kwargs["separator"] == ""
        assert call_kwargs["seq_length"] == 3

    @patch("app.utils.project_utils.db")
    @patch("app.utils.project_utils.ProjectStage")
    @patch("app.utils.project_utils.ProjectStatus")
    def test_init_project_stages(self, mock_status_class, mock_stage_class, mock_db):
        """Test initializing project stages."""
        mock_stage_instance = Mock()
        mock_stage_instance.id = 1
        mock_stage_class.return_value = mock_stage_instance

        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()

        init_project_stages(mock_db, project_id=123)

        # Should create 9 stages
        assert mock_stage_class.call_count == 9

        # Should create statuses for stages that have them
        assert mock_status_class.call_count == 26  # Total statuses across all stages

        # Verify commit was called
        mock_db.commit.assert_called_once()


# =============================================================================
# number_generator.py Tests (aiming for >70% coverage)
# =============================================================================


class TestNumberGenerator:
    """Tests for number_generator module."""

    @patch("app.utils.number_generator.datetime")
    def test_generate_sequential_no_first_record(self, mock_datetime):
        """Test generating sequential number for first record."""
        mock_datetime.now.return_value.strftime.return_value = "250708"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_sequential_no(
            db=db_mock,
            model_class=Mock,
            no_field="code",
            prefix="ECN",
            date_format="%y%m%d",
            separator="-",
            seq_length=3,
        )
        assert result == "ECN-250708-001"

    @patch("app.utils.number_generator.datetime")
    def test_generate_sequential_no_with_existing_records(self, mock_datetime):
        """Test generating sequential number with existing records."""
        mock_datetime.now.return_value.strftime.return_value = "250708"

        # Mock model class
        mock_model = Mock()
        mock_model.code = "ECN-250708-005"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = (
            mock_model
        )
        db_mock.query.return_value = mock_query

        result = generate_sequential_no(
            db=db_mock,
            model_class=Mock,
            no_field="code",
            prefix="ECN",
            date_format="%y%m%d",
            separator="-",
            seq_length=3,
        )
        assert result == "ECN-250708-006"

    @patch("app.utils.number_generator.datetime")
    def test_generate_sequential_no_without_separator(self, mock_datetime):
        """Test generating sequential number without separator."""
        mock_datetime.now.return_value.strftime.return_value = "250708"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_sequential_no(
            db=db_mock,
            model_class=Mock,
            no_field="code",
            prefix="PJ",
            date_format="%y%m%d",
            separator="",
            seq_length=3,
        )
        assert result == "PJ250708001"

    @patch("app.utils.number_generator.datetime")
    def test_generate_sequential_no_no_date(self, mock_datetime):
        """Test generating sequential number without date."""
        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_sequential_no(
            db=db_mock,
            model_class=Mock,
            no_field="code",
            prefix="PO",
            date_format="%y%m%d",
            separator="-",
            seq_length=3,
            use_date=False,
        )
        assert result == "PO-001"

    @patch("app.utils.number_generator.datetime")
    def test_generate_monthly_no_first_record(self, mock_datetime):
        """Test generating monthly number for first record."""
        mock_datetime.now.return_value.strftime.return_value = "2507"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_monthly_no(
            db=db_mock,
            model_class=Mock,
            no_field="code",
            prefix="L",
            separator="-",
            seq_length=3,
        )
        assert result == "L2507-001"

    @patch("app.utils.number_generator.datetime")
    def test_generate_monthly_no_with_existing(self, mock_datetime):
        """Test generating monthly number with existing records."""
        mock_datetime.now.return_value.strftime.return_value = "2507"

        mock_model = Mock()
        mock_model.code = "L2507-010"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = (
            mock_model
        )
        db_mock.query.return_value = mock_query

        result = generate_monthly_no(
            db=db_mock,
            model_class=Mock,
            no_field="code",
            prefix="L",
            separator="-",
            seq_length=3,
        )
        assert result == "L2507-011"

    @patch("app.utils.number_generator.CODE_PREFIX")
    @patch("app.utils.number_generator.SEQ_LENGTH")
    @patch("app.utils.number_generator.Employee")
    def test_generate_employee_code_first(
        self, mock_employee_class, mock_seq_length, mock_prefix
    ):
        """Test generating employee code for first employee."""
        mock_prefix.__getitem__ = Mock(return_value="EMP")
        mock_seq_length.__getitem__ = Mock(return_value=5)

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_employee_code(db_mock)
        assert result == "EMP-00001"

    @patch("app.utils.number_generator.CODE_PREFIX")
    @patch("app.utils.number_generator.SEQ_LENGTH")
    @patch("app.utils.number_generator.Employee")
    def test_generate_employee_code_with_existing(
        self, mock_employee_class, mock_seq_length, mock_prefix
    ):
        """Test generating employee code with existing records."""
        mock_prefix.__getitem__ = Mock(return_value="EMP")
        mock_seq_length.__getitem__ = Mock(return_value=5)

        mock_employee = Mock()
        mock_employee.employee_code = "EMP-00015"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = (
            mock_employee
        )
        db_mock.query.return_value = mock_query

        result = generate_employee_code(db_mock)
        assert result == "EMP-00016"

    @patch("app.utils.number_generator.CODE_PREFIX")
    @patch("app.utils.number_generator.SEQ_LENGTH")
    @patch("app.utils.number_generator.Customer")
    def test_generate_customer_code(
        self, mock_customer_class, mock_seq_length, mock_prefix
    ):
        """Test generating customer code."""
        mock_prefix.__getitem__ = Mock(return_value="CUS")
        mock_seq_length.__getitem__ = Mock(return_value=7)

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_customer_code(db_mock)
        assert result == "CUS-0000001"

    @patch("app.utils.number_generator.CODE_PREFIX")
    @patch("app.utils.number_generator.SEQ_LENGTH")
    @patch("app.utils.number_generator.get_material_category_code")
    @patch("app.utils.number_generator.Material")
    def test_generate_material_code(
        self, mock_material_class, mock_get_code, mock_seq_length, mock_prefix
    ):
        """Test generating material code."""
        mock_prefix.__getitem__ = Mock(return_value="MAT")
        mock_seq_length.__getitem__ = Mock(return_value=5)
        mock_get_code.return_value = "ME"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_material_code(db_mock, category_code="ME-01-01")
        assert result == "MAT-ME-00001"
        mock_get_code.assert_called_once_with("ME-01-01")

    @patch("app.utils.number_generator.CODE_PREFIX")
    @patch("app.utils.number_generator.SEQ_LENGTH")
    @patch("app.utils.number_generator.get_material_category_code")
    @patch("app.utils.number_generator.Material")
    def test_generate_material_code_default_category(
        self, mock_material_class, mock_get_code, mock_seq_length, mock_prefix
    ):
        """Test generating material code with default category."""
        mock_prefix.__getitem__ = Mock(return_value="MAT")
        mock_seq_length.__getitem__ = Mock(return_value=5)
        mock_get_code.return_value = "OT"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_material_code(db_mock)
        assert result == "MAT-OT-00001"

    @patch("app.utils.number_generator.Machine")
    def test_generate_machine_code(self, mock_machine_class):
        """Test generating machine code."""
        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_machine_code(db_mock, "PJ250708001")
        assert result == "PJ250708001-PN001"

    @patch("app.utils.number_generator.Machine")
    def test_generate_machine_code_with_existing(self, mock_machine_class):
        """Test generating machine code with existing machines."""
        mock_machine = Mock()
        mock_machine.machine_code = "PJ250708001-PN003"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = (
            mock_machine
        )
        db_mock.query.return_value = mock_query

        result = generate_machine_code(db_mock, "PJ250708001")
        assert result == "PJ250708001-PN004"

    @patch("app.utils.number_generator.datetime")
    @patch("app.utils.number_generator.BonusCalculation")
    def test_generate_calculation_code(self, mock_bonus_class, mock_datetime):
        """Test generating calculation code."""
        mock_datetime.now.return_value.strftime.return_value = "250716"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        result = generate_calculation_code(db_mock)
        assert result == "BC-250716-001"


# =============================================================================
# code_config.py Tests (aiming for >70% coverage)
# =============================================================================


class TestCodeConfig:
    """Tests for code_config module."""

    def test_get_material_category_code_valid(self):
        """Test extracting category code from valid category code."""
        assert get_material_category_code("ME-01-01") == "ME"
        assert get_material_category_code("EL-02-03") == "EL"
        assert get_material_category_code("PN-01-01") == "PN"
        assert get_material_category_code("ST-01-01") == "ST"
        assert get_material_category_code("OT-01-01") == "OT"
        assert get_material_category_code("TR-01-01") == "TR"

    def test_get_material_category_code_invalid(self):
        """Test extracting category code from invalid category code."""
        assert get_material_category_code("XX-01-01") == "OT"
        assert get_material_category_code("ABC-DEF") == "OT"

    def test_get_material_category_code_none(self):
        """Test extracting category code from None."""
        assert get_material_category_code(None) == "OT"
        assert get_material_category_code("") == "OT"

    def test_get_material_category_code_case_insensitive(self):
        """Test that category code extraction is case insensitive."""
        assert get_material_category_code("me-01-01") == "ME"
        assert get_material_category_code("el-02-03") == "EL"

    def test_validate_material_category_code_valid(self):
        """Test validating valid category codes."""
        assert validate_material_category_code("ME") is True
        assert validate_material_category_code("EL") is True
        assert validate_material_category_code("PN") is True
        assert validate_material_category_code("ST") is True
        assert validate_material_category_code("OT") is True
        assert validate_material_category_code("TR") is True

    def test_validate_material_category_code_invalid(self):
        """Test validating invalid category codes."""
        assert validate_material_category_code("XX") is False
        assert validate_material_category_code("ABC") is False
        assert validate_material_category_code("") is False

    def test_validate_material_category_code_case_insensitive(self):
        """Test that validation is case insensitive."""
        assert validate_material_category_code("me") is True
        assert validate_material_category_code("el") is True

    def test_code_prefix_dict(self):
        """Test CODE_PREFIX dictionary."""
        assert CODE_PREFIX["EMPLOYEE"] == "EMP"
        assert CODE_PREFIX["CUSTOMER"] == "CUS"
        assert CODE_PREFIX["MATERIAL"] == "MAT"
        assert CODE_PREFIX["PROJECT"] == "PJ"
        assert CODE_PREFIX["MACHINE"] == "PN"

    def test_seq_length_dict(self):
        """Test SEQ_LENGTH dictionary."""
        assert SEQ_LENGTH["EMPLOYEE"] == 5
        assert SEQ_LENGTH["CUSTOMER"] == 7
        assert SEQ_LENGTH["MATERIAL"] == 5
        assert SEQ_LENGTH["PROJECT"] == 3
        assert SEQ_LENGTH["MACHINE"] == 3

    def test_material_category_codes_dict(self):
        """Test MATERIAL_CATEGORY_CODES dictionary."""
        assert MATERIAL_CATEGORY_CODES["ME"] == "机械件"
        assert MATERIAL_CATEGORY_CODES["EL"] == "电气件"
        assert MATERIAL_CATEGORY_CODES["PN"] == "气动件"
        assert MATERIAL_CATEGORY_CODES["ST"] == "标准件"
        assert MATERIAL_CATEGORY_CODES["OT"] == "其他"
        assert MATERIAL_CATEGORY_CODES["TR"] == "贸易件"


# =============================================================================
# pinyin_utils.py Tests (aiming for >70% coverage)
# =============================================================================


class TestPinyinUtils:
    """Tests for pinyin_utils module."""

    def test_name_to_pinyin(self):
        """Test converting Chinese name to pinyin."""
        assert name_to_pinyin("姚洪") == "yaohong"
        assert name_to_pinyin("张三") == "zhangsan"

    def test_name_to_pinyin_empty(self):
        """Test converting empty string to pinyin."""
        assert name_to_pinyin("") == ""
        assert name_to_pinyin(None) == ""

    def test_name_to_pinyin_initials(self):
        """Test converting Chinese name to pinyin initials."""
        assert name_to_pinyin_initials("姚洪") == "YH"
        assert name_to_pinyin_initials("张三") == "ZS"

    def test_name_to_pinyin_initials_empty(self):
        """Test converting empty string to pinyin initials."""
        assert name_to_pinyin_initials("") == ""
        assert name_to_pinyin_initials(None) == ""

    @patch("app.utils.pinyin_utils.User")
    def test_generate_unique_username_available(self, mock_user_class):
        """Test generating unique username when name is available."""
        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        username = generate_unique_username("姚洪", db_mock)
        assert username == "yaohong"

    @patch("app.utils.pinyin_utils.User")
    def test_generate_unique_username_conflict(self, mock_user_class):
        """Test generating unique username when name conflicts."""
        db_mock = Mock()

        # Mock first query returns existing user, second query returns None
        existing_user = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [existing_user, None]
        db_mock.query.return_value = mock_query

        username = generate_unique_username("姚洪", db_mock)
        assert username == "yaohong2"

    @patch("app.utils.pinyin_utils.User")
    def test_generate_unique_username_with_existing_set(self, mock_user_class):
        """Test generating unique username with existing usernames set."""
        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        existing_usernames = {"yaohong", "yaohong2"}
        username = generate_unique_username("姚洪", db_mock, existing_usernames)
        assert username == "yaohong3"

    def test_generate_initial_password(self):
        """Test generating initial password."""
        # Test that password is generated and is a string
        password = generate_initial_password()
        assert isinstance(password, str)
        assert len(password) == 16  # base64url encoded 12 bytes = 16 chars

    def test_generate_initial_password_with_params(self):
        """Test generating initial password with deprecated parameters."""
        # Parameters should be ignored but still accepted
        password = generate_initial_password(
            username="testuser", id_card="123456", employee_code="EMP001"
        )
        assert isinstance(password, str)
        assert len(password) == 16

    @patch("app.utils.pinyin_utils.Employee")
    def test_batch_generate_pinyin_for_employees(self, mock_employee_class):
        """Test batch generating pinyin for employees."""
        # Create mock employees
        emp1 = Mock()
        emp1.id = 1
        emp1.name = "姚洪"
        emp1.pinyin_name = None

        emp2 = Mock()
        emp2.id = 2
        emp2.name = "张三"
        emp2.pinyin_name = ""

        emp3 = Mock()
        emp3.id = 3
        emp3.name = "李四"
        emp3.pinyin_name = "lisi"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [emp1, emp2, emp3]
        db_mock.query.return_value = mock_query

        count = batch_generate_pinyin_for_employees(db_mock)
        assert count == 2
        assert emp1.pinyin_name == "yaohong"
        assert emp2.pinyin_name == "zhangsan"
        assert emp3.pinyin_name == "lisi"  # Unchanged

    @patch("app.utils.pinyin_utils.Employee")
    def test_batch_generate_pinyin_for_employees_no_updates(self, mock_employee_class):
        """Test batch generating pinyin when no updates needed."""
        emp = Mock()
        emp.id = 1
        emp.name = "姚洪"
        emp.pinyin_name = "yaohong"

        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [emp]
        db_mock.query.return_value = mock_query

        count = batch_generate_pinyin_for_employees(db_mock)
        assert count == 0


# =============================================================================
# spec_extractor.py Tests (aiming for >70% coverage)
# =============================================================================


class TestSpecExtractor:
    """Tests for SpecExtractor class."""

    def setup_method(self):
        """Setup test instance."""
        self.extractor = SpecExtractor()

    @patch("app.utils.spec_extractor.ProjectDocument")
    def test_extract_from_document_not_found(self, mock_doc_class):
        """Test extracting from non-existent document."""
        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_mock.query.return_value = mock_query

        with pytest.raises(ValueError, match="文档.*不存在"):
            self.extractor.extract_from_document(
                db=db_mock,
                document_id=1,
                project_id=1,
                extracted_by=1,
            )

    @patch("app.utils.spec_extractor.ProjectDocument")
    def test_extract_from_document_manual_entry(self, mock_doc_class):
        """Test extracting from document for manual entry."""
        doc = Mock()
        doc.id = 1
        db_mock = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = doc
        db_mock.query.return_value = mock_query

        result = self.extractor.extract_from_document(
            db=db_mock,
            document_id=1,
            project_id=1,
            extracted_by=1,
            auto_extract=False,
        )
        assert result == []

    def test_extract_key_parameters_voltage(self):
        """Test extracting voltage parameter."""
        params = self.extractor.extract_key_parameters("220V")
        assert "voltage" in params
        assert params["voltage"] == "220"

    def test_extract_key_parameters_current(self):
        """Test extracting current parameter."""
        params = self.extractor.extract_key_parameters("5A")
        assert "current" in params
        assert params["current"] == "5"

    def test_extract_key_parameters_accuracy(self):
        """Test extracting accuracy parameter."""
        params = self.extractor.extract_key_parameters("精度: ±0.1%")
        assert "accuracy" in params
        assert params["accuracy"] == "0.1"

    def test_extract_key_parameters_temperature_range(self):
        """Test extracting temperature range."""
        params = self.extractor.extract_key_parameters("工作温度: -20~60℃")
        assert "temp_min" in params
        assert "temp_max" in params
        assert params["temp_min"] == "-20"
        assert params["temp_max"] == "60"

    def test_extract_key_parameters_power(self):
        """Test extracting power parameter."""
        params = self.extractor.extract_key_parameters("100W")
        assert "power" in params
        assert params["power"] == "100"

    def test_extract_key_parameters_frequency(self):
        """Test extracting frequency parameter."""
        params = self.extractor.extract_key_parameters("50Hz")
        assert "frequency" in params
        assert params["frequency"] == "50"

    def test_extract_key_parameters_size(self):
        """Test extracting size parameter."""
        params = self.extractor.extract_key_parameters("100x200x50mm")
        assert "length" in params
        assert "width" in params
        assert "height" in params

    def test_extract_key_parameters_empty(self):
        """Test extracting parameters from empty string."""
        params = self.extractor.extract_key_parameters("")
        assert params == {}

    def test_create_requirement(self):
        """Test creating a requirement."""
        db_mock = Mock()
        db_mock.add = Mock()
        db_mock.flush = Mock()

        with patch(
            "app.utils.spec_extractor.TechnicalSpecRequirement"
        ) as mock_req_class:
            mock_instance = Mock()
            mock_instance.id = 1
            mock_req_class.return_value = mock_instance

            result = self.extractor.create_requirement(
                db=db_mock,
                project_id=1,
                document_id=1,
                material_name="Test Material",
                specification="Test Spec",
                extracted_by=1,
            )

            assert result.id == 1
            db_mock.add.assert_called_once()
            db_mock.flush.assert_called_once()


# =============================================================================
# spec_match_service.py Tests (aiming for >70% coverage)
# =============================================================================


class TestSpecMatchService:
    """Tests for SpecMatchService class."""

    def setup_method(self):
        """Setup test instance."""
        self.service = SpecMatchService()

    @patch("app.utils.spec_match_service.db")
    @patch("app.utils.spec_match_service.TechnicalSpecRequirement")
    def test_check_po_item_spec_match_no_requirements(self, mock_req_class, mock_db):
        """Test checking PO item when no requirements exist."""
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = self.service.check_po_item_spec_match(
            db=mock_db,
            project_id=1,
            po_item_id=1,
            material_code="MAT001",
            specification="Spec",
        )
        assert result is None

    @patch("app.utils.spec_match_service.db")
    @patch("app.utils.spec_match_service.TechnicalSpecRequirement")
    def test_check_po_item_spec_match_material_code_mismatch(
        self, mock_req_class, mock_db
    ):
        """Test checking PO item when material code doesn't match."""
        req = Mock()
        req.id = 1
        req.material_code = "MAT002"
        req.material_name = "Test"
        req.specification = "Required Spec"

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [req]
        mock_db.query.return_value = mock_query

        result = self.service.check_po_item_spec_match(
            db=mock_db,
            project_id=1,
            po_item_id=1,
            material_code="MAT001",
            specification="Actual Spec",
        )
        # Should return None because material code doesn't match
        assert result is None

    @patch("app.utils.spec_match_service.SpecMatchRecord")
    @patch("app.utils.spec_match_service.db")
    @patch("app.utils.spec_match_service.TechnicalSpecRequirement")
    def test_check_po_item_spec_match_create_record(
        self, mock_req_class, mock_db, mock_match_class
    ):
        """Test checking PO item creates match record."""
        req = Mock()
        req.id = 1
        req.material_code = None
        req.material_name = "Test"
        req.specification = "Required Spec"

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [req]
        mock_db.query.return_value = mock_query

        mock_instance = Mock()
        mock_instance.id = 1
        mock_match_class.return_value = mock_instance

        result = self.service.check_po_item_spec_match(
            db=mock_db,
            project_id=1,
            po_item_id=1,
            material_code="MAT001",
            specification="Actual Spec",
        )

        assert result.id == 1
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @patch("app.utils.spec_match_service.SpecMatchRecord")
    @patch("app.utils.spec_match_service.AlertRecord")
    @patch("app.utils.spec_match_service.AlertRule")
    @patch("app.utils.spec_match_service.db")
    @patch("app.utils.spec_match_service.TechnicalSpecRequirement")
    def test_check_po_item_spec_match_mismatched_alert(
        self,
        mock_req_class,
        mock_db,
        mock_rule_class,
        mock_alert_class,
        mock_match_class,
    ):
        """Test checking PO item with mismatched spec creates alert."""
        req = Mock()
        req.id = 1
        req.material_code = None
        req.material_name = "Test"
        req.specification = "Required Spec"

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [req]
        mock_db.query.return_value = mock_query

        # Mock match result
        mock_match_result = Mock()
        mock_match_result.match_status = "MISMATCHED"
        mock_match_result.match_score = Decimal("50.0")
        mock_match_result.differences = {"spec": "diff"}

        mock_instance = Mock()
        mock_instance.id = 1
        mock_match_class.return_value = mock_instance

        with patch.object(
            self.service.matcher, "match_specification", return_value=mock_match_result
        ):
            self.service.check_po_item_spec_match(
                db=mock_db,
                project_id=1,
                po_item_id=1,
                material_code="MAT001",
                specification="Different Spec",
            )

        # Verify alert was created
        assert mock_alert_class.call_count >= 1


# =============================================================================
# spec_matcher.py Tests (aiming for >70% coverage)
# =============================================================================


class TestSpecMatcher:
    """Tests for SpecMatcher class."""

    def setup_method(self):
        """Setup test instance."""
        self.matcher = SpecMatcher()

    def test_match_specification_perfect_match(self):
        """Test matching with perfect specification match."""
        req = Mock()
        req.specification = "Test Spec"
        req.brand = None
        req.model = None
        req.key_parameters = None
        req.requirement_level = "REQUIRED"

        result = self.matcher.match_specification(
            requirement=req,
            actual_spec="Test Spec",
        )

        assert result.match_status == "MATCHED"
        assert result.match_score >= Decimal("80.0")

    def test_match_specification_with_brand_match(self):
        """Test matching with matching brand."""
        req = Mock()
        req.specification = "Test"
        req.brand = "BrandX"
        req.model = None
        req.key_parameters = None
        req.requirement_level = "REQUIRED"

        result = self.matcher.match_specification(
            requirement=req,
            actual_spec="Test",
            actual_brand="BrandX",
        )

        assert result.match_score >= Decimal("80.0")

    def test_match_specification_with_brand_mismatch(self):
        """Test matching with mismatched brand."""
        req = Mock()
        req.specification = "Test"
        req.brand = "BrandX"
        req.model = None
        req.key_parameters = None
        req.requirement_level = "REQUIRED"

        result = self.matcher.match_specification(
            requirement=req,
            actual_spec="Test",
            actual_brand="BrandY",
        )

        assert result.differences is not None
        assert "brand" in result.differences

    def test_match_specification_with_model_mismatch(self):
        """Test matching with mismatched model."""
        req = Mock()
        req.specification = "Test"
        req.brand = None
        req.model = "ModelX"
        req.key_parameters = None
        req.requirement_level = "REQUIRED"

        result = self.matcher.match_specification(
            requirement=req,
            actual_spec="Test",
            actual_model="ModelY",
        )

        assert result.differences is not None
        assert "model" in result.differences

    def test_match_specification_low_score(self):
        """Test matching with low score."""
        req = Mock()
        req.specification = "Test Spec A"
        req.brand = None
        req.model = None
        req.key_parameters = None
        req.requirement_level = "REQUIRED"

        result = self.matcher.match_specification(
            requirement=req,
            actual_spec="Completely Different",
        )

        assert result.match_status in ["MISMATCHED", "UNKNOWN"]

    def test_match_specification_strict_requirement(self):
        """Test matching with strict requirement level."""
        req = Mock()
        req.specification = "Test"
        req.brand = None
        req.model = None
        req.key_parameters = None
        req.requirement_level = "STRICT"

        # Create a match that has high score but has differences
        result = self.matcher.match_specification(
            requirement=req,
            actual_spec="Test Extra",  # Similar but not exact
        )

        # With STRICT level, differences should cause MISMATCHED
        if result.differences:
            assert result.match_status == "MISMATCHED"

    def test_text_similarity(self):
        """Test text similarity calculation."""
        similarity = self.matcher._text_similarity("hello", "hello")
        assert similarity == 1.0

        similarity = self.matcher._text_similarity("hello", "world")
        assert 0.0 <= similarity < 1.0

        similarity = self.matcher._text_similarity("", "")
        assert similarity == 1.0

    def test_compare_parameters(self):
        """Test parameter comparison."""
        required = {"voltage": "220", "current": "5"}
        actual = {"voltage": "220", "current": "5"}

        differences = self.matcher._compare_parameters(required, actual)
        assert len(differences) == 0

    def test_compare_parameters_with_differences(self):
        """Test parameter comparison with differences."""
        required = {"voltage": "220", "current": "5"}
        actual = {"voltage": "240", "current": "5"}

        differences = self.matcher._compare_parameters(required, actual)
        assert "voltage" in differences

    def test_compare_parameters_missing(self):
        """Test parameter comparison with missing values."""
        required = {"voltage": "220"}
        actual = {}

        differences = self.matcher._compare_parameters(required, actual)
        assert "voltage" in differences
        assert differences["voltage"]["missing"] is True

    def test_calculate_param_score(self):
        """Test parameter score calculation."""
        required = {"voltage": "220", "current": "5"}
        actual = {"voltage": "220", "current": "5"}

        score = self.matcher._calculate_param_score(required, actual)
        assert score == 100.0

    def test_calculate_param_score_partial(self):
        """Test parameter score calculation with partial match."""
        required = {"voltage": "220", "current": "5"}
        actual = {"voltage": "220"}

        score = self.matcher._calculate_param_score(required, actual)
        assert score == 50.0

    def test_calculate_param_score_empty(self):
        """Test parameter score calculation with empty requirements."""
        score = self.matcher._calculate_param_score({}, {})
        assert score == 100.0


# =============================================================================
# redis_client.py Tests (aiming for >70% coverage)
# =============================================================================


class TestRedisClient:
    """Tests for redis_client module."""

    def setup_method(self):
        """Clear redis client before each test."""
        from app.utils import redis_client

        redis_client._redis_client = None

    @patch("app.utils.redis_client.settings")
    @patch("app.utils.redis_client.redis")
    def test_get_redis_client_success(self, mock_redis, mock_settings):
        """Test getting redis client successfully."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.from_url.return_value = mock_client

        client = get_redis_client()
        assert client is not None
        assert client == mock_client

    @patch("app.utils.redis_client.settings")
    def test_get_redis_client_not_configured(self, mock_settings):
        """Test getting redis client when not configured."""
        mock_settings.REDIS_URL = None

        client = get_redis_client()
        assert client is None

    @patch("app.utils.redis_client.settings")
    @patch("app.utils.redis_client.redis")
    def test_get_redis_client_connection_error(self, mock_redis, mock_settings):
        """Test getting redis client with connection error."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        import redis as redis_module

        mock_redis.from_url.side_effect = redis_module.ConnectionError(
            "Connection failed"
        )

        client = get_redis_client()
        assert client is None

    @patch("app.utils.redis_client.settings")
    @patch("app.utils.redis_client.redis")
    def test_get_redis_client_cached(self, mock_redis, mock_settings):
        """Test getting redis client from cache."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.from_url.return_value = mock_client

        # First call
        client1 = get_redis_client()
        # Second call should return cached instance
        client2 = get_redis_client()

        assert client1 is not None
        assert client1 is client2  # Same instance
        assert mock_redis.from_url.call_count == 1

    @patch("app.utils.redis_client.settings")
    @patch("app.utils.redis_client.redis")
    def test_close_redis_client(self, mock_redis, mock_settings):
        """Test closing redis client."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.from_url.return_value = mock_client

        # Get client
        client = get_redis_client()
        assert client is not None

        # Close client
        close_redis_client()

        # Get client again should create new instance
        mock_redis.from_url.reset_mock()
        get_redis_client()

        assert mock_redis.from_url.call_count == 1
        mock_client.close.assert_called_once()

    @patch("app.utils.redis_client.settings")
    @patch("app.utils.redis_client.redis")
    def test_close_redis_client_no_client(self, mock_redis, mock_settings):
        """Test closing redis client when no client exists."""
        mock_settings.REDIS_URL = None

        # Should not raise error
        close_redis_client()
        assert True

    @patch("app.utils.redis_client.settings")
    @patch("app.utils.redis_client.redis")
    def test_close_redis_client_with_error(self, mock_redis, mock_settings):
        """Test closing redis client with error."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.close.side_effect = Exception("Close error")
        mock_redis.from_url.return_value = mock_client

        # Get client
        client = get_redis_client()
        assert client is not None

        # Close client should handle error gracefully
        close_redis_client()

        # Client should still be None
        assert get_redis_client() is None


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
