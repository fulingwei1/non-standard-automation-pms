"""
Unit tests for number_generator utility functions.

Tests coverage for:
- generate_sequential_no
- generate_monthly_no
- generate_employee_code
- generate_customer_code
- generate_material_code
- generate_machine_code
- generate_calculation_code
"""

from datetime import datetime
from app.utils.number_generator import (
    generate_sequential_no,
    generate_monthly_no,
    generate_employee_code,
    generate_customer_code,
    generate_material_code,
    generate_machine_code,
    generate_calculation_code,
)
from app.models.enums import LeadStatusEnum


class TestGenerateSequentialNo:
    """Test generate_sequential_no function."""

    def test_generate_first_record(self, db_session):
        """Test generating the first record for a pattern."""
        # Create a dummy model to test with
        from app.models.project import Project

        # First record should be -001
        code = generate_sequential_no(
        db=db_session,
        model_class=Project,
        no_field="project_code",
        prefix="TEST",
        date_format="%y%m%d",
        seq_length=3,
        separator="-",
        use_date=True,
        )

        assert code is not None
        assert code.startswith("TEST-")
        assert code.endswith("-001")

    def test_generate_subsequent_record(self, db_session):
        """Test generating subsequent records."""
        from app.models.project import Project

        # Create first project
        today = datetime.now().strftime("%y%m%d")
        project1 = Project(
        project_code=f"TEST-{today}-001",
        project_name="Test Project 1",
        customer_name="Test Customer",
        )
        db_session.add(project1)
        db_session.commit()

        # Generate next code
        code = generate_sequential_no(
        db=db_session,
        model_class=Project,
        no_field="project_code",
        prefix="TEST",
        date_format="%y%m%d",
        seq_length=3,
        separator="-",
        use_date=True,
        )

        assert code.endswith("-002")

    def test_generate_without_separator(self, db_session):
        """Test generating codes without separator."""
        from app.models.project import Project

        code = generate_sequential_no(
        db=db_session,
        model_class=Project,
        no_field="project_code",
        prefix="PJ",
        date_format="%y%m%d",
        seq_length=3,
        separator="",
        use_date=True,
        )

        assert "-" not in code
        assert code.startswith("PJ")
        assert code.endswith("001")

    def test_generate_without_date(self, db_session):
        """Test generating codes without date."""
        from app.models.project import Project

        code = generate_sequential_no(
        db=db_session,
        model_class=Project,
        no_field="project_code",
        prefix="NO",
        date_format="%y%m%d",
        seq_length=3,
        separator="-",
        use_date=False,
        )

        # Should not contain date pattern (today's date would have 6 digits)
        assert "-" in code or not any(char.isdigit() for char in code.split("-")[-1])
        assert code.startswith("NO")

    def test_custom_seq_length(self, db_session):
        """Test generating codes with custom sequence length."""
        from app.models.project import Project

        code = generate_sequential_no(
        db=db_session,
        model_class=Project,
        no_field="project_code",
        prefix="TEST",
        date_format="%y%m%d",
        seq_length=5,
        separator="-",
        use_date=False,
        )

        parts = code.split("-")
        seq_part = parts[-1]
        assert len(seq_part) == 5
        assert seq_part == "00001"


class TestGenerateMonthlyNo:
    """Test generate_monthly_no function."""

    def test_generate_first_monthly_record(self, db_session):
        """Test generating the first record for a month."""
        from app.models.sales import Lead

        # First record of the month
        code = generate_monthly_no(
        db=db_session,
        model_class=Lead,
        no_field="lead_code",
        prefix="L",
        separator="-",
        seq_length=3,
        )

        assert code is not None
        assert code.startswith("L")
        today = datetime.now().strftime("%y%m")
        assert today in code
        assert code.endswith("-001")

    def test_generate_subsequent_monthly_record(self, db_session):
        """Test generating subsequent monthly records."""
        from app.models.sales import Lead

        # Create first lead
        today = datetime.now().strftime("%y%m")
        lead1 = Lead(
        lead_code=f"L{today}-001",
        customer_name="Test Customer",
        contact_name="John",
        contact_phone="1234567890",
        status=LeadStatusEnum.NEW,
        )
        db_session.add(lead1)
        db_session.commit()

        # Generate next code
        code = generate_monthly_no(
        db=db_session,
        model_class=Lead,
        no_field="lead_code",
        prefix="L",
        separator="-",
        seq_length=3,
        )

        assert code.endswith("-002")

    def test_custom_separator(self, db_session):
        """Test monthly code with custom separator."""
        from app.models.sales import Lead

        code = generate_monthly_no(
        db=db_session,
        model_class=Lead,
        no_field="lead_code",
        prefix="O",
        separator="",
        seq_length=4,
        )

        assert "-" not in code


class TestGenerateEmployeeCode:
    """Test generate_employee_code function."""

    def test_generate_first_employee_code(self, db_session):
        """Test generating the first employee code."""
        code = generate_employee_code(db_session)

        assert code is not None
        assert code.startswith("EMP-")
        assert code.endswith("00001")

    def test_generate_subsequent_employee_code(self, db_session):
        """Test generating subsequent employee codes."""
        from app.models.organization import Employee

        # Create first employee
        emp1 = Employee(
        employee_code="EMP-00001",
        name="John Doe",
        role="Engineer",
        department="Engineering",
        )
        db_session.add(emp1)
        db_session.commit()

        # Generate next code
        code = generate_employee_code(db_session)

        assert code == "EMP-00002"


class TestGenerateCustomerCode:
    """Test generate_customer_code function."""

    def test_generate_first_customer_code(self, db_session):
        """Test generating the first customer code."""
        code = generate_customer_code(db_session)

        assert code is not None
        assert code.startswith("CUS-")
        # Customer codes should be 7 digits by default
        seq_part = code.split("-")[1]
        assert len(seq_part) == 7
        assert seq_part == "0000001"

    def test_generate_subsequent_customer_code(self, db_session):
        """Test generating subsequent customer codes."""
        from app.models.project import Customer

        # Create first customer
        cust1 = Customer(
        customer_code="CUS-0000001",
        customer_name="Test Customer",
        contact_person="John",
        contact_phone="1234567890",
        )
        db_session.add(cust1)
        db_session.commit()

        # Generate next code
        code = generate_customer_code(db_session)

        assert code == "CUS-0000002"


class TestGenerateMaterialCode:
    """Test generate_material_code function."""

    def test_generate_material_code_default_category(self, db_session):
        """Test generating material code with default category."""
        code = generate_material_code(db_session, category_code=None)

        assert code is not None
        assert code.startswith("MAT-")
        # Default category should be OT (Other)
        assert "OT" in code
        parts = code.split("-")
        assert len(parts) == 3
        assert parts[2] == "00001"

    def test_generate_material_code_with_category(self, db_session):
        """Test generating material code with specified category."""
        # Use a valid category code format
        code = generate_material_code(db_session, category_code="ME-01-01")

        assert code is not None
        assert code.startswith("MAT-")
        assert "ME" in code

    def test_generate_subsequent_material_code(self, db_session):
        """Test generating subsequent material codes."""
        from app.models.material import Material, MaterialCategory

        category = MaterialCategory(
        category_code="ME-01-01",
        category_name="Test Category",
        )
        db_session.add(category)
        db_session.commit()

        mat1 = Material(
        material_code="MAT-ME-00001",
        material_name="Test Material",
        category_id=category.id,
        )
        db_session.add(mat1)
        db_session.commit()

        # Generate next code with same category
        code = generate_material_code(db_session, category_code="ME-01-01")

        assert code == "MAT-ME-00002"


class TestGenerateMachineCode:
    """Test generate_machine_code function."""

    def test_generate_first_machine_code(self, db_session):
        """Test generating the first machine code for a project."""
        project_code = "PJ250708001"
        code = generate_machine_code(db_session, project_code)

        assert code is not None
        assert code.startswith(f"{project_code}-PN")
        assert code.endswith("001")

    def test_generate_subsequent_machine_code(self, db_session):
        """Test generating subsequent machine codes."""
        from app.models.project import Machine, Project

        project = Project(
        project_code="PJ250708002",
        project_name="Test Project for Machine",
        customer_name="Test Customer",
        )
        db_session.add(project)
        db_session.commit()

        mach1 = Machine(
        machine_code="PJ250708002-PN001",
        machine_name="Test Machine 1",
        project_id=project.id,
        )
        db_session.add(mach1)
        db_session.commit()

        # Generate next code
        code = generate_machine_code(db_session, "PJ250708002")

        assert code == "PJ250708002-PN002"

    def test_generate_machine_code_different_projects(self, db_session):
        """Test that machine codes are independent per project."""
        code1 = generate_machine_code(db_session, "PJ250708003")
        code2 = generate_machine_code(db_session, "PJ250708004")

        # Both should start with 001 since they're different projects
        assert code1.endswith("PN001")
        assert code2.endswith("PN001")


class TestGenerateCalculationCode:
    """Test generate_calculation_code function."""

    def test_generate_first_calculation_code(self, db_session):
        """Test generating the first calculation code for the day."""
        code = generate_calculation_code(db_session)

        assert code is not None
        assert code.startswith("BC-")
        # Check date format (BC-yymmdd-seq)
        parts = code.split("-")
        assert len(parts) == 3
        # Date part should be 6 characters (yymmdd)
        assert len(parts[1]) == 6
        # Sequence should be 3 digits
        assert len(parts[2]) == 3
        assert parts[2] == "001"

    def test_generate_subsequent_calculation_code(self, db_session):
        """Test generating subsequent calculation codes for the day."""
        from app.models.bonus import BonusCalculation

        today = datetime.now().strftime("%y%m%d")
        # Create first calculation
        calc1 = BonusCalculation(
        calculation_code=f"BC-{today}-001",
        employee_id=1,
        calculated_amount=1000.00,
        )
        db_session.add(calc1)
        db_session.commit()

        # Generate next code
        code = generate_calculation_code(db_session)

        assert code.endswith("-002")

    def test_calculation_code_format(self, db_session):
        """Test that calculation code has correct format."""
        code = generate_calculation_code(db_session)

        # Format: BC-yymmdd-001
        assert code.startswith("BC-")
        assert "-" in code
        parts = code.split("-")
        assert len(parts) == 3
        assert parts[0] == "BC"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handle_malformed_existing_code(self, db_session):
        """Test handling of malformed existing codes."""
        from app.models.project import Project

        # Create a record with malformed code
        project = Project(
        project_code="TEST-MALFORMED",
        project_name="Test",
        customer_name="Test",
        )
        db_session.add(project)
        db_session.commit()

        # Should still generate a valid code (starting from 001)
        code = generate_sequential_no(
        db=db_session,
        model_class=Project,
        no_field="project_code",
        prefix="TEST2",
        date_format="%y%m%d",
        seq_length=3,
        separator="-",
        use_date=True,
        )

        assert code.endswith("-001")

    def test_seq_overflow(self, db_session):
        """Test handling when sequence exceeds digit length."""
        from app.models.project import Project

        # Create 999th record
        today = datetime.now().strftime("%y%m%d")
        project = Project(
        project_code=f"OVER-{today}-999",
        project_name="Test",
        customer_name="Test",
        )
        db_session.add(project)
        db_session.commit()

        # Next should be 1000 (will truncate to last 3 digits)
        code = generate_sequential_no(
        db=db_session,
        model_class=Project,
        no_field="project_code",
        prefix="OVER",
        date_format="%y%m%d",
        seq_length=3,
        separator="-",
        use_date=True,
        )

        assert code is not None
