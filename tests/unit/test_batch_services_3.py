# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for batch 3 services
Tests 10 service modules using mock-based approach
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch
from sqlalchemy.orm import Query, Session

# Import services to test
from app.services.data_scope_service import DataScopeService
from app.services.project_evaluation_service import ProjectEvaluationService
from app.services.spec_match_service import (
    calculate_match_statistics,
)
from app.services.lead_priority_scoring_service import LeadPriorityScoringService
from app.services.staff_matching.matching import MatchingEngine
from app.services.staff_matching.score_calculators import (
    SkillScoreCalculator,
    DomainScoreCalculator,
    AttitudeScoreCalculator,
    QualityScoreCalculator,
    WorkloadScoreCalculator,
    SpecialScoreCalculator,
)
from app.services.unified_import.unified_importer import UnifiedImporter
from app.services.unified_import.base import ImportBase
from app.services.project_import_service import (
    validate_excel_file,
    parse_excel_data,
    validate_project_columns,
    get_column_value,
    parse_project_row,
    find_or_create_customer,
    find_project_manager,
    parse_date_value,
    parse_decimal_value,
)


# ==================== DataScopeService Tests ====================


class TestDataScopeService:
    """Tests for DataScopeService"""

    def test_get_user_data_scope_superuser(self, db_session_mock):
        """Test data scope for superuser"""
        user = Mock()
        user.is_superuser = True

        scope = DataScopeService.get_user_data_scope(db_session_mock, user)

        assert scope == "ALL"

    def test_get_user_data_scope_all_scope(self, db_session_mock):
        """Test data scope when user has ALL permission"""
        from app.models import DataScopeEnum

        user = Mock()
        user.is_superuser = False

        # Create mock roles
        role1 = Mock()
        role1.data_scope = DataScopeEnum.ALL.value
        role1.is_active = True

        user_role1 = Mock()
        user_role1.role = role1

        user.roles = [user_role1]

        scope = DataScopeService.get_user_data_scope(db_session_mock, user)

        assert scope == DataScopeEnum.ALL.value

    def test_get_user_project_ids(self, db_session_mock):
        """Test getting user's project IDs"""
        mock_query = Mock()
        db_session_mock.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [(1,), (2,), (3,)]

        project_ids = DataScopeService.get_user_project_ids(db_session_mock, 1)

        assert project_ids == {1, 2, 3}

    def test_get_subordinate_ids(self, db_session_mock):
        """Test getting subordinate IDs"""
        mock_query = Mock()
        db_session_mock.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [(5,), (6,)]

        subordinates = DataScopeService.get_subordinate_ids(db_session_mock, 1)

        assert subordinates == {5, 6}

    def test_filter_projects_by_scope_superuser(self, db_session_mock):
        """Test filtering projects for superuser"""
        user = Mock()
        user.is_superuser = True
        query = Mock()

        result = DataScopeService.filter_projects_by_scope(db_session_mock, query, user)

        assert result == query

    def test_check_project_access_superuser(self, db_session_mock):
        """Test checking project access for superuser"""
        user = Mock()
        user.is_superuser = True

        access = DataScopeService.check_project_access(db_session_mock, user, 1)

        assert access is True

    def test_check_customer_access_superuser(self, db_session_mock):
        """Test checking customer access for superuser"""
        user = Mock()
        user.is_superuser = True

        access = DataScopeService.check_customer_access(db_session_mock, user, 1)

        assert access is True


# ==================== ProjectEvaluationService Tests ====================


class TestProjectEvaluationService:
    """Tests for ProjectEvaluationService"""

    def test_initialization(self, db_session_mock):
        """Test service initialization"""
        service = ProjectEvaluationService(db_session_mock)
        assert service.db == db_session_mock

    def test_get_dimension_weights_default(self, db_session_mock):
        """Test getting default dimension weights"""
        db_session_mock.query.return_value.filter.return_value.all.return_value = []

        service = ProjectEvaluationService(db_session_mock)
        weights = service.get_dimension_weights()

        assert "novelty" in weights
        assert "new_tech" in weights
        assert "difficulty" in weights
        assert "workload" in weights
        assert "amount" in weights

    @patch.object(ProjectEvaluationService, "get_dimension_weights")
    def test_calculate_total_score(self, mock_get_weights, db_session_mock):
        """Test calculating total score"""
        mock_get_weights.return_value = ProjectEvaluationService.DEFAULT_WEIGHTS
        service = ProjectEvaluationService(db_session_mock)

        total = service.calculate_total_score(
            novelty_score=Decimal("8"),
            new_tech_score=Decimal("7"),
            difficulty_score=Decimal("6"),
            workload_score=Decimal("8"),
            amount_score=Decimal("9"),
        )

        assert isinstance(total, Decimal)
        assert 0 <= float(total) <= 100

    def test_determine_evaluation_level_s(self, db_session_mock):
        """Test determining evaluation level S"""
        service = ProjectEvaluationService(db_session_mock)

        level = service.determine_evaluation_level(Decimal("95"))

        assert level == "S"

    def test_determine_evaluation_level_a(self, db_session_mock):
        """Test determining evaluation level A"""
        service = ProjectEvaluationService(db_session_mock)

        level = service.determine_evaluation_level(Decimal("85"))

        assert level == "A"

    def test_determine_evaluation_level_d(self, db_session_mock):
        """Test determining evaluation level D"""
        service = ProjectEvaluationService(db_session_mock)

        level = service.determine_evaluation_level(Decimal("50"))

        assert level == "D"

    def test_auto_calculate_novelty_score_no_similar(self, db_session_mock):
        """Test auto calculating novelty score with no similar projects"""
        from app.models import Project

        project = Mock(spec=Project)
        project.id = 1
        project.project_type = "TEST"
        project.product_category = "TEST"
        project.industry = "TEST"

        db_session_mock.query.return_value.filter.return_value.all.return_value = []

        service = ProjectEvaluationService(db_session_mock)
        score = service.auto_calculate_novelty_score(project)

        assert score == Decimal("2.0")

    def test_auto_calculate_amount_score_large(self, db_session_mock):
        """Test auto calculating amount score for large project"""
        from app.models import Project

        project = Mock(spec=Project)
        project.contract_amount = Decimal("6000000")

        service = ProjectEvaluationService(db_session_mock)
        score = service.auto_calculate_amount_score(project)

        assert score == Decimal("2.0")

    def test_auto_calculate_amount_score_medium(self, db_session_mock):
        """Test auto calculating amount score for medium project"""
        from app.models import Project

        project = Mock(spec=Project)
        project.contract_amount = Decimal("300000")

        service = ProjectEvaluationService(db_session_mock)
        score = service.auto_calculate_amount_score(project)

        assert score == Decimal("9.5")

    def test_get_bonus_coefficient_s(self, db_session_mock):
        """Test getting bonus coefficient for S level"""
        from app.models import Project
        from app.models.project_evaluation import ProjectEvaluation

        project = Mock(spec=Project)
        project.id = 1

        evaluation = Mock(spec=ProjectEvaluation)
        evaluation.evaluation_level = "S"

        db_session_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation

        service = ProjectEvaluationService(db_session_mock)
        coefficient = service.get_bonus_coefficient(project)

        assert coefficient == Decimal("1.5")

    def test_get_bonus_coefficient_no_evaluation(self, db_session_mock):
        """Test getting bonus coefficient when no evaluation exists"""
        from app.models import Project

        project = Mock(spec=Project)
        project.id = 1

        db_session_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = ProjectEvaluationService(db_session_mock)
        coefficient = service.get_bonus_coefficient(project)

        assert coefficient == Decimal("1.0")


# ==================== SpecMatchService Tests ====================


class TestSpecMatchService:
    """Tests for spec_match_service functions"""

    def test_calculate_match_statistics(self):
        """Test calculating match statistics"""
        from app.schemas.technical_spec import SpecMatchResult

        results = [
            SpecMatchResult(
                spec_requirement_id=1,
                material_name="A",
                match_status="MATCHED",
                match_score=100,
                differences={},
            ),
            SpecMatchResult(
                spec_requirement_id=2,
                material_name="B",
                match_status="MISMATCHED",
                match_score=50,
                differences={"field": "diff"},
            ),
            SpecMatchResult(
                spec_requirement_id=3,
                material_name="C",
                match_status="UNKNOWN",
                match_score=0,
                differences={},
            ),
        ]

        stats = calculate_match_statistics(results)

        assert stats["total"] == 3
        assert stats["matched"] == 1
        assert stats["mismatched"] == 1
        assert stats["unknown"] == 1

    def test_calculate_match_statistics_empty(self):
        """Test calculating match statistics with empty results"""
        stats = calculate_match_statistics([])

        assert stats["total"] == 0
        assert stats["matched"] == 0
        assert stats["mismatched"] == 0
        assert stats["unknown"] == 0


# ==================== LeadPriorityScoringService Tests ====================


class TestLeadPriorityScoringService:
    """Tests for LeadPriorityScoringService"""

    def test_initialization(self, db_session_mock):
        """Test service initialization"""
        service = LeadPriorityScoringService(db_session_mock)
        assert service.db == db_session_mock

    def test_calculate_lead_priority_not_found(self, db_session_mock):
        """Test calculating priority for non-existent lead"""

        db_session_mock.query.return_value.filter.return_value.first.return_value = None

        service = LeadPriorityScoringService(db_session_mock)

        with pytest.raises(ValueError, match="线索 1 不存在"):
            service.calculate_lead_priority(1)

    @patch("app.services.lead_priority_scoring_service.date")
    def test_determine_priority_level_p1(self, mock_date):
        """Test determining priority level P1"""
        from app.services.lead_priority_scoring_service import (
            LeadPriorityScoringService,
        )

        service = LeadPriorityScoringService(Mock())

        level = service._determine_priority_level(85, 9)

        assert level == "P1"

    @patch("app.services.lead_priority_scoring_service.date")
    def test_determine_priority_level_p2(self, mock_date):
        """Test determining priority level P2"""
        from app.services.lead_priority_scoring_service import (
            LeadPriorityScoringService,
        )

        service = LeadPriorityScoringService(Mock())

        level = service._determine_priority_level(75, 5)

        assert level == "P2"

    @patch("app.services.lead_priority_scoring_service.date")
    def test_determine_importance_level_high(self, mock_date):
        """Test determining importance level HIGH"""
        from app.services.lead_priority_scoring_service import (
            LeadPriorityScoringService,
        )

        service = LeadPriorityScoringService(Mock())

        level = service._determine_importance_level(85)

        assert level == "HIGH"

    @patch("app.services.lead_priority_scoring_service.date")
    def test_determine_urgency_level_high(self, mock_date):
        """Test determining urgency level HIGH"""
        from app.services.lead_priority_scoring_service import (
            LeadPriorityScoringService,
        )

        service = LeadPriorityScoringService(Mock())

        level = service._determine_urgency_level(9)

        assert level == "HIGH"

    def test_calculate_contract_amount_score_large(self):
        """Test calculating contract amount score for large amount"""
        service = LeadPriorityScoringService(Mock())
        score = service._get_amount_score(1500000)
        assert score == 25

    def test_calculate_contract_amount_score_small(self):
        """Test calculating contract amount score for small amount"""
        service = LeadPriorityScoringService(Mock())
        score = service._get_amount_score(50000)
        assert score == 5

    def test_get_customer_score_a(self):
        """Test getting customer score for A level"""
        from app.models import Customer

        customer = Mock(spec=Customer)
        customer.credit_level = "A"

        service = LeadPriorityScoringService(Mock())
        score = service._get_customer_score(customer)

        assert score == 20

    def test_get_customer_score_none(self):
        """Test getting customer score for None"""
        service = LeadPriorityScoringService(Mock())
        score = service._get_customer_score(None)

        assert score == 5

    def test_get_win_rate_score_high(self):
        """Test getting win rate score for high probability"""
        service = LeadPriorityScoringService(Mock())
        score = service._get_win_rate_score(0.85)

        assert score == 20

    def test_get_win_rate_score_low(self):
        """Test getting win rate score for low probability"""
        service = LeadPriorityScoringService(Mock())
        score = service._get_win_rate_score(0.3)

        assert score == 5


# ==================== StaffMatching - MatchingEngine Tests ====================


class TestMatchingEngine:
    """Tests for MatchingEngine"""

    @patch("app.services.staff_matching.matching.HrAIMatchingLog")
    def test_match_candidates_not_found(self, mock_log_class, db_session_mock):
        """Test matching candidates when staffing need not found"""

        mock_query = Mock()
        db_session_mock.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="人员需求不存在: 1"):
            MatchingEngine.match_candidates(db_session_mock, 1)


# ==================== StaffMatching - ScoreCalculators Tests ====================


class TestScoreCalculators:
    """Tests for score calculators"""

    def test_skill_score_calculator_no_requirements(self, db_session_mock):
        """Test skill score calculator with no requirements"""
        result = SkillScoreCalculator.calculate_skill_score(
            db_session_mock, 1, None, [], []
        )

        assert result["score"] == 60.0
        assert result["matched"] == []
        assert result["missing"] == []

    def test_skill_score_calculator_with_requirements(self, db_session_mock):
        """Test skill score calculator with requirements"""
        from app.models.staff_matching import HrEmployeeTagEvaluation, HrTagDict

        # Mock tag evaluation
        tag_eval = Mock(spec=HrEmployeeTagEvaluation)
        tag_eval.employee_id = 1
        tag_eval.tag_id = 100
        tag_eval.score = 4.0
        tag_eval.is_valid = True

        tag = Mock(spec=HrTagDict)
        tag.tag_name = "Python"
        tag.tag_type = "SKILL"
        tag_eval.tag = tag

        db_session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = [
            tag_eval
        ]

        required_skills = [{"tag_id": 100, "tag_name": "Python", "min_score": 3}]

        result = SkillScoreCalculator.calculate_skill_score(
            db_session_mock, 1, None, required_skills, []
        )

        assert "score" in result
        assert 0 <= result["score"] <= 100

    def test_domain_score_calculator_no_requirements(self, db_session_mock):
        """Test domain score calculator with no requirements"""
        score = DomainScoreCalculator.calculate_domain_score(
            db_session_mock, 1, None, []
        )

        assert score == 60.0

    def test_attitude_score_calculator_with_profile(self, db_session_mock):
        """Test attitude score calculator with profile"""
        from app.models.staff_matching import HrEmployeeProfile

        profile = Mock(spec=HrEmployeeProfile)
        profile.attitude_score = Decimal("80")

        score = AttitudeScoreCalculator.calculate_attitude_score(
            db_session_mock, 1, profile, []
        )

        assert score == 80.0

    def test_attitude_score_calculator_no_profile(self, db_session_mock):
        """Test attitude score calculator without profile"""
        db_session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = []

        score = AttitudeScoreCalculator.calculate_attitude_score(
            db_session_mock, 1, None, []
        )

        assert score == 60.0

    def test_quality_score_calculator_no_performance(self, db_session_mock):
        """Test quality score calculator with no performance records"""
        db_session_mock.query.return_value.filter.return_value.all.return_value = []

        score = QualityScoreCalculator.calculate_quality_score(db_session_mock, 1)

        assert score == 60.0

    def test_quality_score_calculator_with_performance(self, db_session_mock):
        """Test quality score calculator with performance records"""
        from app.models.staff_matching import HrProjectPerformance

        perf = Mock(spec=HrProjectPerformance)
        perf.employee_id = 1
        perf.contribution_level = "CORE"
        perf.performance_score = Decimal("85")
        perf.quality_score = Decimal("90")
        perf.collaboration_score = Decimal("88")

        db_session_mock.query.return_value.filter.return_value.all.return_value = [perf]

        score = QualityScoreCalculator.calculate_quality_score(db_session_mock, 1)

        assert 0 <= score <= 100

    def test_workload_score_calculator_no_profile(self):
        """Test workload score calculator without profile"""
        score = WorkloadScoreCalculator.calculate_workload_score(None, 50)

        assert score == 80.0

    def test_workload_score_calculator_available(self):
        """Test workload score calculator when available"""
        from app.models.staff_matching import HrEmployeeProfile

        profile = Mock(spec=HrEmployeeProfile)
        profile.current_workload_pct = 30

        score = WorkloadScoreCalculator.calculate_workload_score(profile, 50)

        assert score == 100.0

    def test_workload_score_calculator_overloaded(self):
        """Test workload score calculator when overloaded"""
        from app.models.staff_matching import HrEmployeeProfile

        profile = Mock(spec=HrEmployeeProfile)
        profile.current_workload_pct = 80

        score = WorkloadScoreCalculator.calculate_workload_score(profile, 50)

        assert score < 50.0

    def test_special_score_calculator_no_special(self, db_session_mock):
        """Test special score calculator with no special abilities"""
        db_session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = []

        score = SpecialScoreCalculator.calculate_special_score(db_session_mock, 1, None)

        assert score == 50.0

    def test_special_score_calculator_with_special(self, db_session_mock):
        """Test special score calculator with special abilities"""
        from app.models.staff_matching import HrEmployeeTagEvaluation, HrTagDict

        tag_eval = Mock(spec=HrEmployeeTagEvaluation)
        tag_eval.employee_id = 1
        tag_eval.score = 5.0
        tag_eval.is_valid = True

        tag = Mock(spec=HrTagDict)
        tag.tag_type = "SPECIAL"
        tag_eval.tag = tag

        db_session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = [
            tag_eval
        ]

        score = SpecialScoreCalculator.calculate_special_score(db_session_mock, 1, None)

        assert score > 50.0


# ==================== UnifiedImporter Tests ====================


class TestUnifiedImporter:
    """Tests for UnifiedImporter"""

    @patch.object(ImportBase, "parse_file")
    @patch.object(ImportBase, "validate_file")
    @patch("app.services.unified_import.unified_importer.MaterialImporter")
    def test_import_data_material_success(
        self, mock_material_importer, mock_validate, mock_parse, db_session_mock
    ):
        """Test importing material data successfully"""
        import pandas as pd

        mock_df = Mock(spec=pd.DataFrame)
        mock_parse.return_value = mock_df
        mock_material_importer.import_material_data.return_value = (10, 2, [])

        result = UnifiedImporter.import_data(
            db_session_mock, b"fake content", "test.xlsx", "MATERIAL", 1
        )

        assert result["imported_count"] == 10
        assert result["updated_count"] == 2
        assert result["failed_count"] == 0

    @patch.object(ImportBase, "parse_file")
    @patch.object(ImportBase, "validate_file")
    def test_import_data_unsupported_type(
        self, mock_validate, mock_parse, db_session_mock
    ):
        """Test importing data with unsupported type"""
        from fastapi import HTTPException

        mock_validate.return_value = None

        with pytest.raises(HTTPException, match="不支持的模板类型"):
            UnifiedImporter.import_data(
                db_session_mock, b"fake content", "test.xlsx", "UNSUPPORTED", 1
            )


# ==================== ImportBase Tests ====================


class TestImportBase:
    """Tests for ImportBase"""

    def test_validate_file_success(self):
        """Test file validation with valid extension"""
        ImportBase.validate_file("test.xlsx")

    def test_validate_file_xls(self):
        """Test file validation with .xls extension"""
        ImportBase.validate_file("test.xls")

    def test_validate_file_invalid(self):
        """Test file validation with invalid extension"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException, match="只支持Excel文件"):
            ImportBase.validate_file("test.csv")

    @patch("pandas.read_excel")
    def test_parse_file_success(self, mock_read_excel):
        """Test file parsing success"""
        import pandas as pd

        mock_df = Mock(spec=pd.DataFrame)
        mock_df.dropna.return_value = mock_df
        mock_df.__len__ = Mock(return_value=5)
        mock_read_excel.return_value = mock_df

        result = ImportBase.parse_file(b"fake content")

        assert result is not None

    @patch("pandas.read_excel")
    def test_parse_file_empty(self, mock_read_excel):
        """Test file parsing with empty file"""
        from fastapi import HTTPException
        import pandas as pd

        mock_df = Mock(spec=pd.DataFrame)
        mock_df.dropna.return_value = mock_df
        mock_df.__len__ = Mock(return_value=0)
        mock_read_excel.return_value = mock_df

        with pytest.raises(HTTPException, match="文件中没有数据"):
            ImportBase.parse_file(b"fake content")

    def test_check_required_columns_all_present(self):
        """Test checking required columns when all present"""
        import pandas as pd

        df = Mock(spec=pd.DataFrame)
        df.columns = ["col1", "col2", "col3"]

        missing = ImportBase.check_required_columns(df, ["col1", "col2"])

        assert missing == []

    def test_check_required_columns_missing(self):
        """Test checking required columns with missing"""
        import pandas as pd

        df = Mock(spec=pd.DataFrame)
        df.columns = ["col1", "col2"]

        missing = ImportBase.check_required_columns(df, ["col1", "col3"])

        assert missing == ["col3"]

    def test_parse_work_date_datetime(self):
        """Test parsing work date from datetime"""
        test_date = datetime(2024, 1, 1, 12, 0)
        result = ImportBase.parse_work_date(test_date)

        assert result == date(2024, 1, 1)

    def test_parse_work_date_date(self):
        """Test parsing work date from date"""
        test_date = date(2024, 1, 1)
        result = ImportBase.parse_work_date(test_date)

        assert result == date(2024, 1, 1)

    def test_parse_hours_valid(self):
        """Test parsing valid hours"""
        result = ImportBase.parse_hours(8.5)

        assert result == 8.5

    def test_parse_hours_invalid_negative(self):
        """Test parsing invalid negative hours"""
        result = ImportBase.parse_hours(-1)

        assert result is None

    def test_parse_hours_invalid_large(self):
        """Test parsing invalid large hours"""
        result = ImportBase.parse_hours(25)

        assert result is None


# ==================== ProjectImportService Tests ====================


class TestProjectImportService:
    """Tests for project_import_service functions"""

    def test_validate_excel_file_success(self):
        """Test validating Excel file with valid extension"""
        validate_excel_file("test.xlsx")

    def test_validate_excel_file_invalid(self):
        """Test validating Excel file with invalid extension"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException, match="只支持Excel文件"):
            validate_excel_file("test.csv")

    @patch("pandas.read_excel")
    def test_parse_excel_data_success(self, mock_read_excel):
        """Test parsing Excel data successfully"""
        import pandas as pd

        mock_df = Mock(spec=pd.DataFrame)
        mock_df.dropna.return_value = mock_df
        mock_df.__len__ = Mock(return_value=5)
        mock_read_excel.return_value = mock_df

        result = parse_excel_data(b"fake content")

        assert result is not None

    def test_validate_project_columns_valid(self):
        """Test validating project columns with all required present"""
        import pandas as pd

        df = Mock(spec=pd.DataFrame)
        df.columns = ["项目编码*", "项目名称*", "客户名称"]

        validate_project_columns(df)

    def test_validate_project_columns_missing(self):
        """Test validating project columns with missing required"""
        from fastapi import HTTPException
        import pandas as pd

        df = Mock(spec=pd.DataFrame)
        df.columns = ["项目编码*", "客户名称"]

        with pytest.raises(HTTPException, match="Excel文件缺少必需的列"):
            validate_project_columns(df)

    def test_get_column_value_with_star(self):
        """Test getting column value with starred column name"""

        row = Mock()
        row.get = lambda x: "value" if x == "项目编码*" else None

        result = get_column_value(row, "项目编码*")

        assert result == "value"

    def test_get_column_value_without_star(self):
        """Test getting column value without star"""

        row = Mock()
        row.get = lambda x: "value" if x == "项目编码" else None

        result = get_column_value(row, "项目编码*", "项目编码")

        assert result == "value"

    def test_get_column_value_empty(self):
        """Test getting column value with empty value"""

        row = Mock()
        row.get = lambda x: "" if x == "项目编码*" else None

        result = get_column_value(row, "项目编码*", "项目编码")

        assert result is None

    def test_parse_project_row_valid(self):
        """Test parsing valid project row"""

        row = Mock()
        row.get = lambda x: {
            "项目编码*": "PJ001",
            "项目编码": "PJ001",
            "项目名称*": "Test Project",
            "项目名称": "Test Project",
        }.get(x)

        code, name, errors = parse_project_row(row, 0)

        assert code == "PJ001"
        assert name == "Test Project"
        assert len(errors) == 0

    def test_parse_project_row_missing_required(self):
        """Test parsing project row with missing required fields"""

        row = Mock()
        row.get = lambda x: "" if x else None

        code, name, errors = parse_project_row(row, 0)

        assert code is None
        assert name is None
        assert len(errors) > 0

    def test_find_or_create_customer_exists(self, db_session_mock):
        """Test finding existing customer"""
        from app.models import Customer

        customer = Mock(spec=Customer)
        db_session_mock.query.return_value.filter.return_value.first.return_value = (
            customer
        )

        result = find_or_create_customer(db_session_mock, "Test Customer")

        assert result == customer

    def test_find_or_create_customer_not_exists(self, db_session_mock):
        """Test finding non-existent customer"""
        db_session_mock.query.return_value.filter.return_value.first.return_value = None

        result = find_or_create_customer(db_session_mock, "Test Customer")

        assert result is None

    def test_find_project_manager_by_real_name(self, db_session_mock):
        """Test finding project manager by real name"""
        from app.models.user import User

        user = Mock(spec=User)
        db_session_mock.query.return_value.filter.return_value.first.return_value = user

        result = find_project_manager(db_session_mock, "John Doe")

        assert result == user

    def test_parse_date_value_datetime(self):
        """Test parsing date value from datetime"""
        test_date = datetime(2024, 1, 1)
        result = parse_date_value(test_date)

        assert result == date(2024, 1, 1)

    def test_parse_date_value_na(self):
        """Test parsing date value with NA"""
        import pandas as pd

        result = parse_date_value(pd.NA)

        assert result is None

    def test_parse_decimal_value_valid(self):
        """Test parsing valid decimal value"""
        result = parse_decimal_value("123.45")

        assert result == Decimal("123.45")

    def test_parse_decimal_value_na(self):
        """Test parsing decimal value with NA"""
        import pandas as pd

        result = parse_decimal_value(pd.NA)

        assert result is None

    def test_parse_decimal_value_invalid(self):
        """Test parsing invalid decimal value"""
        result = parse_decimal_value("invalid")

        assert result is None


# ==================== Fixtures ====================


@pytest.fixture
def db_session_mock():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_query():
    """Create a mock query object"""
    return Mock(spec=Query)


# ==================== Test Runner ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
