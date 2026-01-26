# -*- coding: utf-8 -*-
"""
Tests for acceptance_report_service
Covers: app/services/acceptance_report_service.py
Coverage Target: 0% -> 50%+
"""

from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

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
        # 格式: FAT-YYYYMMDD-001
        parts = report_no.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # 日期部分
        assert parts[2].isdigit()  # 序号部分

    def test_generate_sat_report_no(self, db_session: Session):
        """测试生成SAT报告编号"""
        report_no = generate_report_no(db_session, "SAT")

        assert report_no is not None
        assert report_no.startswith("SAT-")

    def test_generate_other_report_no(self, db_session: Session):
        """测试生成其他类型报告编号"""
        report_no = generate_report_no(db_session, "OTHER")

        assert report_no is not None
        assert report_no.startswith("AR-")

    def test_generate_sequential_report_no(self, db_session: Session):
        """测试生成连续的报告编号"""
        report_no_1 = generate_report_no(db_session, "FAT")
        report_no_2 = generate_report_no(db_session, "FAT")

        # 两个编号应该不同（序号递增）
        assert report_no_1 != report_no_2


@pytest.mark.unit
class TestGetReportVersion:
    """报告版本号测试"""

    def test_get_first_version(self, db_session: Session):
        """测试获取第一个版本号"""
        # 不存在报告时，应返回版本1
        version = get_report_version(db_session, order_id=99999, report_type="FAT")
        assert version == 1

    def test_get_version_increments(self, db_session: Session):
        """测试版本号递增"""
        from app.models.acceptance import AcceptanceReport

        # 创建一个现有的报告
        existing_report = AcceptanceReport(
            report_no="FAT-TEST-001",
            order_id=12345,
            report_type="FAT",
            version=1,
            status="GENERATED",
        )
        db_session.add(existing_report)
        db_session.commit()

        # 获取下一个版本号
        version = get_report_version(db_session, order_id=12345, report_type="FAT")
        assert version == 2

        # 清理
        db_session.delete(existing_report)
        db_session.commit()


@pytest.mark.unit
class TestBuildReportContent:
    """报告内容构建测试"""

    @pytest.fixture
    def mock_order(self):
        """创建模拟的验收单"""
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

        # 项目和机台信息
        mock_project = Mock()
        mock_project.project_name = "测试项目"
        order.project = mock_project

        mock_machine = Mock()
        mock_machine.machine_name = "测试设备"
        order.machine = mock_machine

        return order

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户"""
        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.real_name = "测试用户"
        return user

    def test_build_report_content_basic(
        self, db_session: Session, mock_order, mock_user
    ):
        """测试构建基本报告内容"""
        with patch(
            "app.services.acceptance_report_service.func"
        ) as mock_func:
            # Mock 查询结果
            mock_func.count.return_value.scalar.return_value = 5

            content = build_report_content(
                db=db_session,
                order=mock_order,
                report_no="FAT-TEST-001",
                version=1,
                current_user=mock_user,
            )

            assert content is not None
            assert "验收报告" in content
            assert "FAT-TEST-001" in content
            assert "AO-TEST-001" in content
            assert "测试项目" in content
            assert "测试设备" in content

    def test_build_report_content_with_missing_project(
        self, db_session: Session, mock_user
    ):
        """测试缺少项目信息时的报告内容"""
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
        order.project = None
        order.machine = None

        with patch(
            "app.services.acceptance_report_service.func"
        ) as mock_func:
            mock_func.count.return_value.scalar.return_value = 0

            content = build_report_content(
                db=db_session,
                order=order,
                report_no="SAT-TEST-001",
                version=1,
                current_user=mock_user,
            )

            assert content is not None
            assert "N/A" in content  # 缺少的信息应显示为 N/A


@pytest.mark.unit
class TestReportlabAvailability:
    """Reportlab 可用性测试"""

    def test_reportlab_available_flag(self):
        """测试 REPORTLAB_AVAILABLE 标志"""
        from app.services.acceptance_report_service import REPORTLAB_AVAILABLE

        # 标志应该是布尔值
        assert isinstance(REPORTLAB_AVAILABLE, bool)


@pytest.mark.unit
class TestSaveReportFile:
    """报告文件保存测试"""

    @pytest.fixture
    def mock_order(self):
        """创建模拟的验收单"""
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

        mock_project = Mock()
        mock_project.project_name = "测试项目"
        order.project = mock_project

        mock_machine = Mock()
        mock_machine.machine_name = "测试设备"
        order.machine = mock_machine

        return order

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户"""
        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.real_name = "测试用户"
        return user

    def test_save_report_file_fallback_to_text(
        self, db_session: Session, mock_order, mock_user, tmp_path
    ):
        """测试 PDF 生成失败时回退到文本格式"""
        from app.services.acceptance_report_service import save_report_file

        report_content = "测试报告内容"

        with patch(
            "app.services.acceptance_report_service.settings"
        ) as mock_settings:
            mock_settings.UPLOAD_DIR = str(tmp_path)

            with patch(
                "app.services.acceptance_report_service.REPORTLAB_AVAILABLE", False
            ):
                with patch(
                    "app.services.acceptance_report_service.get_report_version",
                    return_value=1,
                ):
                    file_path, file_size, file_hash = save_report_file(
                        report_content=report_content,
                        report_no="FAT-TEST-001",
                        report_type="FAT",
                        include_signatures=False,
                        order=mock_order,
                        db=db_session,
                        current_user=mock_user,
                    )

                    assert file_path is not None
                    assert file_path.endswith(".txt")
                    assert file_size > 0
                    assert file_hash is not None
