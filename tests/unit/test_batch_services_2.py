# -*- coding: utf-8 -*-
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.timesheet_aggregation_service import TimesheetAggregationService
from app.services.timesheet_quality_service import TimesheetQualityService
from app.services.timesheet_sync_service import TimesheetSyncService
from app.services.lead_priority_scoring_service import LeadPriorityScoringService
from app.services.work_log_auto_generator import WorkLogAutoGenerator
from app.services.wechat_alert_service import WeChatAlertService


class TestTimesheetAggregationService:
    """Tests for TimesheetAggregationService"""

    @patch(
        "app.services.timesheet_aggregation_service.TimesheetAggregationService.__init__",
        return_value=None,
    )
    def test_aggregate_monthly_timesheet_basic(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetAggregationService.__new__(TimesheetAggregationService)
        service.db = mock_db

        with patch.object(service, "db"):
            with patch(
                "app.services.timesheet_aggregation_service.calculate_month_range"
            ) as mock_range:
                mock_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))

                with patch(
                    "app.services.timesheet_aggregation_service.query_timesheets"
                ) as mock_query:
                    mock_query.return_value = []

                    with patch(
                        "app.services.timesheet_aggregation_service.calculate_hours_summary"
                    ) as mock_summary:
                        mock_summary.return_value = {
                            "total_hours": 40.0,
                            "normal_hours": 40.0,
                            "overtime_hours": 0.0,
                            "weekend_hours": 0.0,
                            "holiday_hours": 0.0,
                        }

                        with patch(
                            "app.services.timesheet_aggregation_service.build_project_breakdown"
                        ) as mock_project:
                            mock_project.return_value = {}

                            with patch(
                                "app.services.timesheet_aggregation_service.build_daily_breakdown"
                            ) as mock_daily:
                                mock_daily.return_value = {}

                                with patch(
                                    "app.services.timesheet_aggregation_service.build_task_breakdown"
                                ) as mock_task:
                                    mock_task.return_value = {}

                                    with patch(
                                        "app.services.timesheet_aggregation_service.get_or_create_summary"
                                    ) as mock_get_summary:
                                        mock_summary_obj = Mock()
                                        mock_summary_obj.id = 1
                                        mock_get_summary.return_value = mock_summary_obj

                                        result = service.aggregate_monthly_timesheet(
                                            2024, 1
                                        )

                                        assert result["success"] is True
                                        assert "summary_id" in result

    @patch(
        "app.services.timesheet_aggregation_service.TimesheetAggregationService.__init__",
        return_value=None,
    )
    def test_generate_hr_report(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetAggregationService.__new__(TimesheetAggregationService)
        service.db = mock_db

        mock_timesheet = Mock()
        mock_timesheet.user_id = 1
        mock_timesheet.user_name = "User One"
        mock_timesheet.department_id = 1
        mock_timesheet.department_name = "技术部"
        mock_timesheet.hours = 8.0
        mock_timesheet.overtime_type = "NORMAL"
        mock_timesheet.work_content = "Test work"

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.order_by.return_value = mock_query_instance
        mock_query_instance.all.return_value = [mock_timesheet]

        mock_db.query.return_value = mock_query_instance

        result = service.generate_hr_report(2024, 1)

        assert isinstance(result, list)
        assert len(result) > 0
        assert "user_id" in result[0]
        assert "total_hours" in result[0]

    @patch(
        "app.services.timesheet_aggregation_service.TimesheetAggregationService.__init__",
        return_value=None,
    )
    def test_generate_project_report_not_found(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetAggregationService.__new__(TimesheetAggregationService)
        service.db = mock_db

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.first.return_value = None
        mock_query_instance.order_by.return_value = mock_query_instance
        mock_query_instance.all.return_value = []

        mock_db.query.return_value = mock_query_instance

        result = service.generate_project_report(999)

        assert "error" in result
        assert result["error"] == "项目不存在"


class TestTimesheetQualityService:
    """Tests for TimesheetQualityService"""

    @patch(
        "app.services.timesheet_quality_service.TimesheetQualityService.__init__",
        return_value=None,
    )
    def test_detect_anomalies_excessive_daily_hours(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetQualityService.__new__(TimesheetQualityService)
        service.db = mock_db
        service.MAX_DAILY_HOURS = 16

        mock_timesheet = Mock()
        mock_timesheet.user_id = 1
        mock_timesheet.work_date = date(2024, 1, 1)
        mock_timesheet.hours = 20.0

        mock_user = Mock()
        mock_user.id = 1
        mock_user.real_name = "User One"
        mock_user.username = "user1"

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.all.return_value = [mock_timesheet]

        mock_db.query.return_value = mock_query_instance
        mock_db.query.return_value = mock_query_instance

        anomalies = service.detect_anomalies(user_id=1)

        assert len(anomalies) > 0
        assert anomalies[0]["type"] == "EXCESSIVE_DAILY_HOURS"

    @patch(
        "app.services.timesheet_quality_service.TimesheetQualityService.__init__",
        return_value=None,
    )
    def test_check_work_log_completeness(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetQualityService.__new__(TimesheetQualityService)
        service.db = mock_db

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [(date(2024, 1, 1), 1)]

        mock_log_query = Mock()
        mock_log_query.filter.return_value = mock_log_query
        mock_log_query.first.return_value = None

        mock_db.query.side_effect = [mock_query, Mock(), mock_log_query]

        result = service.check_work_log_completeness(
            user_id=1, start_date=date(2024, 1, 1), end_date=date(2024, 1, 31)
        )

        assert "missing_log_count" in result

    @patch(
        "app.services.timesheet_quality_service.TimesheetQualityService.__init__",
        return_value=None,
    )
    def test_check_labor_law_compliance(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetQualityService.__new__(TimesheetQualityService)
        service.db = mock_db

        mock_timesheet = Mock()
        mock_timesheet.user_id = 1
        mock_timesheet.hours = 5.0
        mock_timesheet.overtime_type = "OVERTIME"

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value = mock_query_instance
        mock_query_instance.all.return_value = [mock_timesheet, mock_timesheet]

        mock_db.query.return_value = mock_query_instance

        result = service.check_labor_law_compliance(1, 2024, 1)

        assert "is_compliant" in result
        assert "overtime_hours" in result


class TestTimesheetSyncService:
    """Tests for TimesheetSyncService"""

    @patch(
        "app.services.timesheet_sync_service.TimesheetSyncService.__init__",
        return_value=None,
    )
    def test_sync_to_finance_single_timesheet(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetSyncService.__new__(TimesheetSyncService)
        service.db = mock_db

        mock_timesheet = Mock()
        mock_timesheet.id = 1
        mock_timesheet.status = "APPROVED"
        mock_timesheet.project_id = 1
        mock_timesheet.hours = 8.0
        mock_timesheet.work_date = date(2024, 1, 1)
        mock_timesheet.work_content = "Test work"
        mock_timesheet.user_id = 1
        mock_timesheet.user_name = "User One"
        mock_timesheet.project_code = "PJ001"
        mock_timesheet.project_name = "Test Project"

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value.first.return_value = mock_timesheet
        mock_db.query.return_value = mock_query_instance

        with patch(
            "app.services.timesheet_sync_service.HourlyRateService"
        ) as mock_rate:
            mock_rate.get_user_hourly_rate.return_value = Decimal("100.00")

            with patch.object(
                service, "_create_financial_cost_from_timesheet"
            ) as mock_create:
                mock_create.return_value = {
                    "success": True,
                    "created": True,
                    "cost_id": 1,
                }

                result = service.sync_to_finance(timesheet_id=1)

                assert result["success"] is True

    @patch(
        "app.services.timesheet_sync_service.TimesheetSyncService.__init__",
        return_value=None,
    )
    def test_sync_to_finance_not_approved(self, mock_init):
        mock_db = Mock(spec=Session)
        service = TimesheetSyncService.__new__(TimesheetSyncService)
        service.db = mock_db

        mock_timesheet = Mock()
        mock_timesheet.id = 1
        mock_timesheet.status = "PENDING"

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value.first.return_value = mock_timesheet
        mock_db.query.return_value = mock_query_instance

        result = service.sync_to_finance(timesheet_id=1)

        assert result["success"] is False


class TestLeadPriorityScoringService:
    """Tests for LeadPriorityScoringService"""

    @patch(
        "app.services.lead_priority_scoring_service.LeadPriorityScoringService.__init__",
        return_value=None,
    )
    def test_calculate_lead_priority_basic(self, mock_init):
        mock_db = Mock(spec=Session)
        service = LeadPriorityScoringService.__new__(LeadPriorityScoringService)
        service.db = mock_db

        mock_lead = Mock()
        mock_lead.id = 1
        mock_lead.lead_code = "L001"
        mock_lead.completeness = 80
        mock_lead.next_action_at = None

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value.first.return_value = mock_lead
        mock_db.query.return_value = mock_query_instance

        result = service.calculate_lead_priority(1)

        assert "lead_id" in result
        assert "total_score" in result
        assert "priority_level" in result

    @patch(
        "app.services.lead_priority_scoring_service.LeadPriorityScoringService.__init__",
        return_value=None,
    )
    def test_calculate_lead_priority_not_found(self, mock_init):
        mock_db = Mock(spec=Session)
        service = LeadPriorityScoringService.__new__(LeadPriorityScoringService)
        service.db = mock_db

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query_instance

        with pytest.raises(ValueError):
            service.calculate_lead_priority(999)

    @patch(
        "app.services.lead_priority_scoring_service.LeadPriorityScoringService.__init__",
        return_value=None,
    )
    def test_determine_priority_level(self, mock_init):
        mock_db = Mock(spec=Session)
        service = LeadPriorityScoringService.__new__(LeadPriorityScoringService)
        service.db = mock_db

        level = service._determine_priority_level(85, 10)
        assert level == "P1"

        level = service._determine_priority_level(75, 5)
        assert level == "P2"

        level = service._determine_priority_level(50, 10)
        assert level == "P3"

        level = service._determine_priority_level(40, 3)
        assert level == "P4"

    @patch(
        "app.services.lead_priority_scoring_service.LeadPriorityScoringService.__init__",
        return_value=None,
    )
    def test_get_customer_score(self, mock_init):
        mock_db = Mock(spec=Session)
        service = LeadPriorityScoringService.__new__(LeadPriorityScoringService)
        service.db = mock_db

        mock_customer_a = Mock()
        mock_customer_a.credit_level = "A"
        score = service._get_customer_score(mock_customer_a)
        assert score == 20

        mock_customer_b = Mock()
        mock_customer_b.credit_level = "B"
        score = service._get_customer_score(mock_customer_b)
        assert score == 15

        score = service._get_customer_score(None)
        assert score == 5

    @patch(
        "app.services.lead_priority_scoring_service.LeadPriorityScoringService.__init__",
        return_value=None,
    )
    def test_get_amount_score(self, mock_init):
        mock_db = Mock(spec=Session)
        service = LeadPriorityScoringService.__new__(LeadPriorityScoringService)
        service.db = mock_db

        score = service._get_amount_score(1500000)
        assert score == 25

        score = service._get_amount_score(750000)
        assert score == 20

        score = service._get_amount_score(50000)
        assert score == 5


class TestWorkLogAutoGenerator:
    """Tests for WorkLogAutoGenerator"""

    @patch(
        "app.services.work_log_auto_generator.WorkLogAutoGenerator.__init__",
        return_value=None,
    )
    def test_generate_work_log_from_timesheet(self, mock_init):
        mock_db = Mock(spec=Session)
        generator = WorkLogAutoGenerator.__new__(WorkLogAutoGenerator)
        generator.db = mock_db

        mock_user = Mock()
        mock_user.id = 1
        mock_user.real_name = "User One"
        mock_user.username = "user1"

        mock_timesheet = Mock()
        mock_timesheet.user_id = 1
        mock_timesheet.work_date = date(2024, 1, 1)
        mock_timesheet.status = "APPROVED"
        mock_timesheet.hours = 8.0
        mock_timesheet.project_id = 1
        mock_timesheet.task_id = 1
        mock_timesheet.task_name = "Test Task"
        mock_timesheet.work_content = "Test work content"
        mock_timesheet.work_result = "Test result"
        mock_timesheet.progress_before = 10
        mock_timesheet.progress_after = 30

        mock_project = Mock()
        mock_project.id = 1
        mock_project.project_name = "Test Project"

        mock_log_query = Mock()
        mock_log_query.filter.return_value.first.return_value = None

        mock_ts_query = Mock()
        mock_ts_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_timesheet
        ]

        mock_user_query = Mock()
        mock_user_query.filter.return_value.first.return_value = mock_user

        mock_project_query = Mock()
        mock_project_query.filter.return_value.first.return_value = mock_project

        mock_db.query.side_effect = [
            mock_user_query,
            mock_log_query,
            mock_ts_query,
            mock_project_query,
        ]

        result = generator.generate_work_log_from_timesheet(1, date(2024, 1, 1))

        assert result is not None
        assert hasattr(result, "content")

    @patch(
        "app.services.work_log_auto_generator.WorkLogAutoGenerator.__init__",
        return_value=None,
    )
    def test_generate_work_log_no_timesheets(self, mock_init):
        mock_db = Mock(spec=Session)
        generator = WorkLogAutoGenerator.__new__(WorkLogAutoGenerator)
        generator.db = mock_db

        mock_user = Mock()
        mock_user.id = 1
        mock_user.real_name = "User One"

        mock_log_query = Mock()
        mock_log_query.filter.return_value.first.return_value = None

        mock_ts_query = Mock()
        mock_ts_query.filter.return_value.order_by.return_value.all.return_value = []

        mock_user_query = Mock()
        mock_user_query.filter.return_value.first.return_value = mock_user

        mock_db.query.side_effect = [mock_user_query, mock_log_query, mock_ts_query]

        result = generator.generate_work_log_from_timesheet(1, date(2024, 1, 1))

        assert result is None


class TestWeChatAlertService:
    """Tests for WeChatAlertService"""

    def test_send_shortage_alert_readiness_not_found(self):
        mock_db = Mock(spec=Session)

        mock_shortage = Mock()
        mock_shortage.readiness_id = 999

        mock_query_instance = Mock()
        mock_query_instance.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query_instance

        result = WeChatAlertService.send_shortage_alert(mock_db, mock_shortage, "L1")

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
