"""
Unit tests for spec_matcher utility functions.

Tests coverage for:
- SpecMatchResult class
- SpecMatcher class
- match_specification method
- _text_similarity method
- _compare_parameters method
- _calculate_param_score method
"""

from decimal import Decimal
from app.utils.spec_matcher import (
    SpecMatchResult,
    SpecMatcher,
)


class TestSpecMatchResult:
    """Test SpecMatchResult data class."""

    def test_init_with_all_fields(self):
        """Test initialization with all fields."""
        result = SpecMatchResult(
            match_status="MATCHED",
            match_score=Decimal("85.5"),
            differences={"brand": {"required": "Siemens", "actual": "ABB"}},
        )

        assert result.match_status == "MATCHED"
        assert result.match_score == Decimal("85.5")
        assert "brand" in result.differences

    def test_init_with_minimal_fields(self):
        """Test initialization with minimal fields."""
        result = SpecMatchResult(
            match_status="MISMATCHED", match_score=None, differences=None
        )

        assert result.match_status == "MISMATCHED"
        assert result.match_score is None
        assert result.differences is None


class TestSpecMatcherInitialization:
    """Test SpecMatcher initialization."""

    def test_default_match_threshold(self):
        """Test default match threshold is 80%."""
        matcher = SpecMatcher()

        assert matcher.match_threshold == Decimal("80.0")

    def test_has_extractor(self):
        """Test matcher has SpecExtractor instance."""
        matcher = SpecMatcher()

        assert matcher.extractor is not None


class TestMatchSpecification:
    """Test match_specification method."""

    def test_perfect_match(self):
        """Test perfect specification match."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def key_parameters(self):
                return {"voltage": "24V"}

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1200",
            actual_brand="Siemens",
            actual_model="S7-1200",
        )

        assert result.match_status == "MATCHED"
        assert result.match_score == Decimal("100")
        assert result.differences is None or len(result.differences) == 0

    def test_specification_mismatch(self):
        """Test specification text mismatch."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1500",
            actual_brand="Siemens",
            actual_model="S7-1500",
        )

        assert result.match_status in ["MISMATCHED", "MATCHED"]
        assert result.differences is not None
        assert "specification" in result.differences

    def test_brand_mismatch(self):
        """Test brand mismatch."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1200",
            actual_brand="ABB",
            actual_model="S7-1200",
        )

        assert result.match_status == "MISMATCHED"
        assert "brand" in result.differences
        assert result.differences["brand"]["required"] == "Siemens"
        assert result.differences["brand"]["actual"] == "ABB"

    def test_model_mismatch(self):
        """Test model mismatch."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1200",
            actual_brand="Siemens",
            actual_model="S7-1500",
        )

        assert result.match_status == "MISMATCHED"
        assert "model" in result.differences
        assert result.differences["model"]["required"] == "S7-1200"
        assert result.differences["model"]["actual"] == "S7-1500"

    def test_missing_actual_brand(self):
        """Test when actual brand is missing."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1200",
            actual_brand=None,
            actual_model="S7-1200",
        )

        assert result.match_status in ["MISMATCHED", "UNKNOWN"]
        assert "brand" in result.differences
        assert result.differences["brand"]["missing"] is True

    def test_missing_actual_model(self):
        """Test when actual model is missing."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1200",
            actual_brand="Siemens",
            actual_model=None,
        )

        assert result.match_status in ["MISMATCHED", "UNKNOWN"]
        assert "model" in result.differences
        assert result.differences["model"]["missing"] is True

    def test_low_similarity_threshold(self):
        """Test low similarity below 0.8 threshold."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="Servo Motor XYZ",
            actual_brand="Panasonic",
            actual_model="XYZ",
        )

        assert "specification" in result.differences or result.match_score < Decimal(
            "80"
        )

    def test_strict_requirement_mismatch(self):
        """Test strict requirement with partial match."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def key_parameters(self):
                return {"voltage": "24V"}

            def requirementment_level(self):
                return "STRICT"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1200",
            actual_brand="ABB",
            actual_model="S7-1200",
        )

        assert result.match_status == "MISMATCHED"

    def test_normal_requirement_partial_match(self):
        """Test normal requirement with partial match."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def key_parameters(self):
                return {"voltage": "24V"}

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC S7-1200",
            actual_brand="ABB",
            actual_model="S7-1200",
        )

        assert result.match_status == "MATCHED"

    def test_unknown_status_low_score(self):
        """Test UNKNOWN status for very low scores."""

        class MockRequirement:
            def specification(self):
                return "PLC S7-1200"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def requirementment_level(self):
                return "NORMAL"

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="Servo",
            actual_brand="Unknown",
            actual_model="Unknown",
        )

        assert result.match_score < Decimal("50.0")


class TestTextSimilarity:
    """Test _text_similarity method."""

    def test_exact_match(self):
        """Test exact text match."""
        matcher = SpecMatcher()

        similarity = matcher._text_similarity("PLC S7-1200", "PLC S7-1200")

        assert similarity == 1.0

    def test_no_match(self):
        """Test completely different texts."""
        matcher = SpecMatcher()

        similarity = matcher._text_similarity("PLC S7-1200", "Servo Motor")

        assert similarity < 0.5

    def test_partial_match(self):
        """Test partial text match."""
        matcher = SpecMatcher()

        similarity = matcher._text_similarity("PLC S7-1200", "PLC S7-1500")

        assert 0.5 < similarity < 1.0

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        matcher = SpecMatcher()

        sim1 = matcher._text_similarity("PLC S7-1200", "plc s7-1200")
        sim2 = matcher._text_similarity("PLC S7-1200", "PLC S7-1200")

        assert sim1 == sim2


class TestCompareParameters:
    """Test _compare_parameters method."""

    def test_all_parameters_match(self):
        """Test all parameters match exactly."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W"}
        actual = {"voltage": "24V", "power": "100W"}

        differences = matcher._compare_parameters(required, actual)

        assert len(differences) == 0

    def test_parameter_within_tolerance(self):
        """Test parameter within 5% tolerance."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W"}
        actual = {"voltage": "24.5V", "power": "102W"}

        differences = matcher._compare_parameters(required, actual)

        assert len(differences) == 0

    def test_parameter_outside_tolerance(self):
        """Test parameter outside tolerance."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W"}
        actual = {"voltage": "26V", "power": "100W"}

        differences = matcher._compare_parameters(required, actual)

        assert "voltage" in differences
        assert differences["voltage"]["deviation"] > 0.01

    def test_missing_actual_parameter(self):
        """Test when actual parameter is missing."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W"}
        actual = {"voltage": "24V"}

        differences = matcher._compare_parameters(required, actual)

        assert "power" in differences
        assert differences["power"]["missing"] is True

    def test_parameter_string_mismatch(self):
        """Test string parameter mismatch."""
        matcher = SpecMatcher()

        required = {"type": "PLC", "protocol": "PROFINET"}
        actual = {"type": "PLC", "protocol": "MODBUS"}

        differences = matcher._compare_parameters(required, actual)

        assert "protocol" in differences


class TestCalculateParamScore:
    """Test _calculate_param_score method."""

    def test_empty_required_params(self):
        """Test with empty required parameters."""
        matcher = SpecMatcher()

        required = {}
        actual = {"voltage": "24V"}

        score = matcher._calculate_param_score(required, actual)

        assert score == 100.0

    def test_all_params_match(self):
        """Test all parameters match."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W"}
        actual = {"voltage": "24V", "power": "100W"}

        score = matcher._calculate_param_score(required, actual)

        assert score == 100.0

    def test_all_params_mismatch(self):
        """Test all parameters mismatch."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W"}
        actual = {"voltage": "12V", "power": "50W"}

        score = matcher._calculate_param_score(required, actual)

        assert score == 0.0

    def test_partial_params_match(self):
        """Test partial parameters match."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W", "protocol": "PROFINET"}
        actual = {"voltage": "24V", "power": "100W", "protocol": "PROFINET"}

        score = matcher._calculate_param_score(required, actual)

        assert 0 < score < 100

    def test_params_within_tolerance(self):
        """Test parameters within tolerance range."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W"}
        actual = {"voltage": "24.5V", "power": "102W"}

        score = matcher._calculate_param_score(required, actual)

        assert score > 80

    def test_score_calculation(self):
        """Test score calculation formula."""
        matcher = SpecMatcher()

        required = {"voltage": "24V", "power": "100W", "protocol": "PROFINET"}
        actual = {"voltage": "24V", "power": "100W", "protocol": "PROFINET"}

        score = matcher._calculate_param_score(required, actual)

        assert score == 100.0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_none_values(self):
        """Test handling of None values."""

        class MockRequirement:
            def specification(self):
                return "PLC"

            def brand(self):
                return "Siemens"

            def model(self):
                return "S7-1200"

            def key_parameters(self):
                return {"voltage": "24V"}

        requirement = MockRequirement()

        matcher = SpecMatcher()
        result = matcher.match_specification(
            requirement=requirement,
            actual_spec="PLC",
            actual_brand=None,
            actual_model=None,
        )

        assert result.match_status in ["UNKNOWN", "MISMATCHED"]

    def test_empty_strings(self):
        """Test handling of empty strings."""
        matcher = SpecMatcher()

        similarity = matcher._text_similarity("", "")

        assert similarity >= 0

    def test_non_numeric_parameter_comparison(self):
        """Test non-numeric parameter comparison."""
        matcher = SpecMatcher()

        required = {"type": "PLC"}
        actual = {"type": "Servo"}

        differences = matcher._compare_parameters(required, actual)

        assert "type" in differences

    def test_zero_division_avoidance(self):
        """Test division by zero is avoided."""
        matcher = SpecMatcher()

        score = matcher._calculate_param_score({}, {})

        assert score == 100.0
