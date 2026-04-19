# -*- coding: utf-8 -*-
"""
Tests for acceptance_report_service
Covers: app/services/acceptance_report_service.py
Coverage Target: 0% -> 50%+
"""

from datetime import date
from unittest.mock import Mock, mock_open, patch

import pytest
from sqlalchemy.orm import Session

# Skip this module if the service doesn't exist yet
pytest.importorskip("app.services.acceptance_report_service")

from app.services.acceptance_report_service import (
    build_report_content,
    generate_report_no,
    get_report_version,
)


@pytest.mark.unit
class TestGenerateReportNo:
    """报告编号生成测试"""

    def test_generate_fat_report_no(self, db_session: Session):
        """测试生成FAT报告编号"""
        report_no = generate_report_no(db_session, "FAT")

        assert report_no is not None
        assert report_no.startswith("FAT-")
        parts = report_no.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8
        assert parts[2].isdigit()

    def test_generate_sat_report_no(self, db_session: Session):
        """测试生成SAT报告编号"""
        report_no = generate_report_no(db_session, "SAT")

        assert report_no is not None
        assert report_no.startswith("SAT-")

    def test_generate_other_report_no(self, db_session: Session):
        """测试生成其他类型报告编号"""
        report_no = generate_report_no(db_session, "OTHER")

        assert report_no is not None
        assert report_no.startswith("OTHER-")

    def test_generate_sequential_report_no(self, db_session: Session):
        """测试生成连续的报告编号"""
        from app.models.acceptance import AcceptanceReport

        report_no_1 = generate_report_no(db_session, "FAT")
        db_session.add(
            AcceptanceReport(
                report_no=report_no_1,
                order_id=1,
                report_type="FAT",
                version=1,
            )
        )
        db_session.commit()

        report_no_2 = generate_report_no(db_session, "FAT")
        assert report_no_1 != report_no_2


@pytest.mark.unit
class TestGetReportVersion:
    """报告版本号测试"""

    def test_get_first_version(self, db_session: Session):
        """测试获取第一个版本号"""
        version = get_report_version(db_session, order_id=99999, report_type="FAT")
        assert version == 1

    def test_get_version_increments(self, db_session: Session):
        """测试版本号递增"""
        from app.models.acceptance import AcceptanceReport

        existing_report = AcceptanceReport(
            report_no="FAT-TEST-001",
            order_id=12345,
            report_type="FAT",
            version=1,
        )
        db_session.add(existing_report)
        db_session.commit()

        version = get_report_version(db_session, order_id=12345, report_type="FAT")
        assert version == 2

        db_session.delete(existing_report)
        db_session.commit()


@pytest.mark.unit
class TestBuildReportContent:
    """报告内容构建测试"""

    @pytest.fixture
    def mock_order(self):
        order = Mock()
        order.order_no = "AO-TEST-001"
        order.acceptance_type = "FAT"
        order.status = "COMPLETED"
        order.actual_end_date = date.today()
        order.pass_rate = 95.0
        order.total_items = 20
        order.passed_items = 19
        order.failed_items = 1
        order.qa_signer_id = None
        order.customer_signer = "客户签字人"
        order.id = 1
        return order

    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.real_name = "测试用户"
        return user

    def test_build_report_content_basic(self, db_session: Session, mock_order, mock_user):
        content = build_report_content(
            db=db_session,
            order=mock_order,
            report_no="FAT-TEST-001",
            version=1,
            user=mock_user,
        )

        assert content is not None
        assert "验收报告" in content
        assert "FAT-TEST-001" in content
        assert "AO-TEST-001" in content
        assert "验收类型: FAT" in content
        assert "通过率: 95.0%" in content
        assert "客户签字: 客户签字人" in content
        assert "生成人: 测试用户" in content

    def test_build_report_content_with_missing_project(self, db_session: Session, mock_user):
        order = Mock()
        order.order_no = "AO-TEST-002"
        order.acceptance_type = "SAT"
        order.status = "IN_PROGRESS"
        order.actual_end_date = None
        order.pass_rate = 0
        order.total_items = 0
        order.passed_items = 0
        order.failed_items = 0
        order.qa_signer_id = None
        order.customer_signer = None
        order.id = 2

        content = build_report_content(
            db=db_session,
            order=order,
            report_no="SAT-TEST-001",
            version=1,
            user=mock_user,
        )

        assert content is not None
        assert "SAT-TEST-001" in content
        assert "验收类型: SAT" in content
        assert "通过率: 0%" in content


@pytest.mark.unit
class TestReportlabAvailability:
    """Reportlab 可用性测试"""

    def test_reportlab_available_flag(self):
        from app.services.acceptance_report_service import REPORTLAB_AVAILABLE

        assert isinstance(REPORTLAB_AVAILABLE, bool)


@pytest.mark.unit
class TestSaveReportFile:
    """报告文件保存测试"""

    @pytest.fixture
    def mock_order(self):
        order = Mock()
        order.id = 1
        order.order_no = "AO-TEST-001"
        order.acceptance_type = "FAT"
        order.status = "COMPLETED"
        order.actual_end_date = date.today()
        order.pass_rate = 100.0
        order.total_items = 10
        order.passed_items = 10
        order.failed_items = 0
        return order

    @pytest.fixture
    def mock_user(self):
        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.real_name = "测试用户"
        return user

    def test_save_report_file_fallback_to_text(
        self, db_session: Session, mock_order, mock_user, tmp_path
    ):
        from app.services.acceptance_report_service import save_report_file

        report_content = "测试报告内容"

        with patch("app.services.acceptance_report_service.os.makedirs"):
            with patch("builtins.open", mock_open()) as mocked_file:
                file_path, filename = save_report_file(
                    content=report_content,
                    order_no="AO-TEST-001",
                    report_type="FAT",
                    use_pdf=False,
                    order=mock_order,
                    db=db_session,
                    user=mock_user,
                )

                assert file_path is not None
                assert file_path.endswith(".txt")
                assert filename.endswith(".txt")
                mocked_file().write.assert_called_once_with(report_content)
