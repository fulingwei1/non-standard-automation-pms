# -*- coding: utf-8 -*-
"""
LossDeepAnalysisService 单元测试
测试未中标深度原因分析服务的各项功能
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.enums import LeadOutcomeEnum, LossReasonEnum
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.loss_deep_analysis_service import LossDeepAnalysisService


class TestLossDeepAnalysisServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock(spec=Session)
        service = LossDeepAnalysisService(mock_db)
        assert service.db == mock_db
        assert service.hourly_rate_service is not None


class TestAnalyzeLostProjects:
    """测试分析未中标项目"""

    @patch.object(LossDeepAnalysisService, '_analyze_investment_stage')
    @patch.object(LossDeepAnalysisService, '_analyze_loss_reasons')
    @patch.object(LossDeepAnalysisService, '_analyze_investment_output')
    @patch.object(LossDeepAnalysisService, '_identify_patterns')
    def test_analyze_with_no_projects(
        self, mock_patterns, mock_output, mock_reasons, mock_stage
    ):
        """测试无项目时的分析"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_stage.return_value = {'statistics': {}, 'details': [], 'summary': {}}
        mock_reasons.return_value = {'statistics': {}, 'top_reasons': [], 'details': {}}
        mock_output.return_value = {'summary': {}, 'by_stage': {}, 'by_person': [], 'by_department': []}
        mock_patterns.return_value = {}

        service = LossDeepAnalysisService(mock_db)
        result = service.analyze_lost_projects()

        assert result['total_lost_projects'] == 0

    @patch.object(LossDeepAnalysisService, '_analyze_investment_stage')
    @patch.object(LossDeepAnalysisService, '_analyze_loss_reasons')
    @patch.object(LossDeepAnalysisService, '_analyze_investment_output')
    @patch.object(LossDeepAnalysisService, '_identify_patterns')
    def test_analyze_with_date_range(
        self, mock_patterns, mock_output, mock_reasons, mock_stage
    ):
        """测试带日期范围的分析"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.outcome = LeadOutcomeEnum.LOST.value

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [mock_project]
        mock_db.query.return_value = query_mock

        mock_stage.return_value = {'statistics': {}, 'details': [], 'summary': {}}
        mock_reasons.return_value = {'statistics': {}, 'top_reasons': [], 'details': {}}
        mock_output.return_value = {'summary': {}, 'by_stage': {}, 'by_person': [], 'by_department': []}
        mock_patterns.return_value = {}

        service = LossDeepAnalysisService(mock_db)
        result = service.analyze_lost_projects(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        assert result['analysis_period']['start_date'] == '2024-01-01'
        assert result['analysis_period']['end_date'] == '2024-12-31'


class TestDetermineInvestmentStage:
    """测试判断项目投入阶段"""

    def test_stage_s1_returns_requirement_only(self):
        """测试S1阶段返回需求调研"""
        mock_db = MagicMock(spec=Session)
        service = LossDeepAnalysisService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = 'S1'
        mock_project.id = 1

        result = service._determine_investment_stage(mock_project)
        assert result == 'requirement_only'

    def test_stage_s2_returns_design(self):
        """测试S2阶段返回方案设计"""
        mock_db = MagicMock(spec=Session)
        service = LossDeepAnalysisService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = 'S2'
        mock_project.id = 1

        result = service._determine_investment_stage(mock_project)
        assert result == 'design'

    def test_stage_s4_returns_detailed_design(self):
        """测试S4阶段返回详细设计"""
        mock_db = MagicMock(spec=Session)
        service = LossDeepAnalysisService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = 'S4'
        mock_project.id = 1

        result = service._determine_investment_stage(mock_project)
        assert result == 'detailed_design'

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    def test_no_stage_high_hours_returns_detailed_design(self, mock_hours):
        """测试无阶段但工时超过80小时返回详细设计"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 100.0

        service = LossDeepAnalysisService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = None
        mock_project.id = 1

        result = service._determine_investment_stage(mock_project)
        assert result == 'detailed_design'

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    def test_no_stage_medium_hours_returns_design(self, mock_hours):
        """测试无阶段工时40-80小时返回方案设计"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 60.0

        service = LossDeepAnalysisService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = None
        mock_project.id = 1

        result = service._determine_investment_stage(mock_project)
        assert result == 'design'

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    def test_no_stage_low_hours_returns_requirement(self, mock_hours):
        """测试无阶段工时小于40小时返回需求调研"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 20.0

        service = LossDeepAnalysisService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = None
        mock_project.id = 1

        result = service._determine_investment_stage(mock_project)
        assert result == 'requirement_only'

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    def test_no_stage_no_hours_returns_unknown(self, mock_hours):
        """测试无阶段无工时返回未知"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 0.0

        service = LossDeepAnalysisService(mock_db)

        mock_project = Mock(spec=Project)
        mock_project.stage = None
        mock_project.id = 1

        result = service._determine_investment_stage(mock_project)
        assert result == 'unknown'


class TestAnalyzeInvestmentStage:
    """测试投入阶段分析"""

    @patch.object(LossDeepAnalysisService, '_determine_investment_stage')
    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_analyze_empty_projects(self, mock_cost, mock_hours, mock_stage):
        """测试空项目列表的分析"""
        mock_db = MagicMock(spec=Session)
        service = LossDeepAnalysisService(mock_db)

        result = service._analyze_investment_stage([])

        assert result['statistics']['requirement_only'] == 0
        assert result['statistics']['detailed_design'] == 0
        assert result['details'] == []

    @patch.object(LossDeepAnalysisService, '_determine_investment_stage')
    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_analyze_multiple_projects(self, mock_cost, mock_hours, mock_stage):
        """测试多个项目的分析"""
        mock_db = MagicMock(spec=Session)

        mock_stage.side_effect = ['detailed_design', 'design', 'detailed_design']
        mock_hours.return_value = 50.0
        mock_cost.return_value = Decimal('5000')

        mock_project1 = Mock(spec=Project)
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"
        mock_project1.project_name = "项目1"
        mock_project1.loss_reason = "PRICE"
        mock_project1.loss_reason_detail = None

        mock_project2 = Mock(spec=Project)
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"
        mock_project2.project_name = "项目2"
        mock_project2.loss_reason = "COMPETITION"
        mock_project2.loss_reason_detail = None

        mock_project3 = Mock(spec=Project)
        mock_project3.id = 3
        mock_project3.project_code = "PJ003"
        mock_project3.project_name = "项目3"
        mock_project3.loss_reason = "PRICE"
        mock_project3.loss_reason_detail = None

        service = LossDeepAnalysisService(mock_db)
        result = service._analyze_investment_stage([mock_project1, mock_project2, mock_project3])

        assert result['statistics']['detailed_design'] == 2
        assert result['statistics']['design'] == 1
        assert len(result['details']) == 3


class TestAnalyzeLossReasons:
    """测试未中标原因分析"""

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_analyze_reasons_empty(self, mock_cost, mock_hours):
        """测试空项目列表的原因分析"""
        mock_db = MagicMock(spec=Session)
        service = LossDeepAnalysisService(mock_db)

        result = service._analyze_loss_reasons([])

        assert result['statistics'] == {}
        assert result['top_reasons'] == []

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_analyze_reasons_with_projects(self, mock_cost, mock_hours):
        """测试有项目的原因分析"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 50.0
        mock_cost.return_value = Decimal('5000')

        mock_project1 = Mock(spec=Project)
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"
        mock_project1.loss_reason = "PRICE"
        mock_project1.loss_reason_detail = "价格太高"

        mock_project2 = Mock(spec=Project)
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"
        mock_project2.loss_reason = "PRICE"
        mock_project2.loss_reason_detail = "竞争对手价格低"

        service = LossDeepAnalysisService(mock_db)
        result = service._analyze_loss_reasons([mock_project1, mock_project2])

        assert result['statistics']['PRICE'] == 2
        assert len(result['top_reasons']) == 1
        assert result['top_reasons'][0]['reason'] == 'PRICE'
        assert result['top_reasons'][0]['count'] == 2


class TestGetProjectHours:
    """测试获取项目工时"""

    def test_get_hours_returns_sum(self):
        """测试返回工时总和"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 80.5

        service = LossDeepAnalysisService(mock_db)
        result = service._get_project_hours(project_id=1)

        assert result == 80.5

    def test_get_hours_returns_zero_when_none(self):
        """测试无工时返回0"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        service = LossDeepAnalysisService(mock_db)
        result = service._get_project_hours(project_id=1)

        assert result == 0.0


class TestCalculateProjectCost:
    """测试计算项目成本"""

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    def test_calculate_cost_no_timesheets(self, mock_hours):
        """测试无工时记录的成本"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 0.0
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = LossDeepAnalysisService(mock_db)
        result = service._calculate_project_cost(project_id=1)

        assert result == Decimal('0')

    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch('app.services.loss_deep_analysis_service.HourlyRateService.get_user_hourly_rate')
    def test_calculate_cost_with_timesheets(self, mock_hourly_rate, mock_hours):
        """测试有工时记录的成本计算"""
        mock_db = MagicMock(spec=Session)
        mock_hours.return_value = 40.0
        mock_hourly_rate.return_value = Decimal('200')

        mock_ts = Mock(spec=Timesheet)
        mock_ts.hours = 40
        mock_ts.user_id = 1
        mock_ts.work_date = date(2024, 1, 15)

        mock_user = Mock(spec=User)
        mock_user.id = 1

        # 第一个查询返回工时记录
        query_ts = MagicMock()
        query_ts.filter.return_value.all.return_value = [mock_ts]

        # 第二个查询返回用户
        query_user = MagicMock()
        query_user.filter.return_value.first.return_value = mock_user

        mock_db.query.side_effect = [query_ts, query_user]

        service = LossDeepAnalysisService(mock_db)
        result = service._calculate_project_cost(project_id=1)

        # 40小时 * 200元/小时 = 8000
        assert result == Decimal('8000')


class TestIdentifyPatterns:
    """测试模式识别"""

    @patch.object(LossDeepAnalysisService, '_determine_investment_stage')
    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_identify_empty_patterns(self, mock_cost, mock_hours, mock_stage):
        """测试空项目的模式识别"""
        mock_db = MagicMock(spec=Session)
        service = LossDeepAnalysisService(mock_db)

        result = service._identify_patterns([])

        assert result['detailed_design_loss_patterns'] == []
        assert result['salesperson_patterns'] == []

    @patch.object(LossDeepAnalysisService, '_determine_investment_stage')
    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_identify_detailed_design_patterns(self, mock_cost, mock_hours, mock_stage):
        """测试识别详细设计后未中标模式"""
        mock_db = MagicMock(spec=Session)
        mock_stage.return_value = 'detailed_design'
        mock_hours.return_value = 100.0
        mock_cost.return_value = Decimal('10000')

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.loss_reason = "PRICE"
        mock_project.salesperson_id = None

        service = LossDeepAnalysisService(mock_db)
        result = service._identify_patterns([mock_project])

        assert len(result['detailed_design_loss_patterns']) == 1
        assert result['detailed_design_loss_patterns'][0]['reason'] == 'PRICE'


class TestAnalyzeByStage:
    """测试按阶段分析"""

    @patch.object(LossDeepAnalysisService, '_determine_investment_stage')
    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_analyze_specific_stage(self, mock_cost, mock_hours, mock_stage):
        """测试分析特定阶段"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "项目1"
        mock_project.loss_reason = "PRICE"
        mock_project.created_at = date(2024, 6, 1)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        mock_stage.return_value = 'detailed_design'
        mock_hours.return_value = 100.0
        mock_cost.return_value = Decimal('10000')

        service = LossDeepAnalysisService(mock_db)
        result = service.analyze_by_stage(stage='detailed_design')

        assert result['stage'] == 'detailed_design'
        assert result['total_projects'] == 1
        assert result['total_hours'] == 100.0

    @patch.object(LossDeepAnalysisService, '_determine_investment_stage')
    @patch.object(LossDeepAnalysisService, '_get_project_hours')
    @patch.object(LossDeepAnalysisService, '_calculate_project_cost')
    def test_analyze_stage_with_date_filter(self, mock_cost, mock_hours, mock_stage):
        """测试带日期过滤的阶段分析"""
        mock_db = MagicMock(spec=Session)

        mock_project1 = Mock(spec=Project)
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"
        mock_project1.project_name = "项目1"
        mock_project1.loss_reason = "PRICE"
        mock_project1.created_at = date(2024, 6, 1)

        mock_project2 = Mock(spec=Project)
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"
        mock_project2.project_name = "项目2"
        mock_project2.loss_reason = "COMPETITION"
        mock_project2.created_at = date(2023, 6, 1)  # 在日期范围之外

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project1, mock_project2]

        mock_stage.return_value = 'detailed_design'
        mock_hours.return_value = 50.0
        mock_cost.return_value = Decimal('5000')

        service = LossDeepAnalysisService(mock_db)
        result = service.analyze_by_stage(
            stage='detailed_design',
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )

        # 只有项目1在日期范围内
        assert result['total_projects'] == 1
