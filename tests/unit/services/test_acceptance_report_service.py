"""
Acceptance Report Service unit tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.acceptance_report_service import (
    generate_report_no,
    build_report_content,
    get_report_version,
    save_report_file
)


def test_generate_report_no():
    """Test report number generation"""
    # Mock database session
    mock_db = Mock()
    
    # Mock query behavior
    mock_query = Mock()
    mock_query.scalar.return_value = 2  # Third report of the day
    mock_db.query.return_value = mock_query
    
    # Test report number generation
    result = generate_report_no(mock_db, "FAT")
    
    # Verify the database was queried correctly
    assert mock_db.query.called
    # Check that result follows expected format
    assert result.startswith("FAT-")
    assert len(result) >= 12  # FAT-YYYYMMDD-XXX format


def test_build_report_content():
    """Test building report content"""
    # Create mock objects
    mock_db = Mock()
    mock_order = Mock()
    mock_order.order_no = "ORDER-001"
    mock_order.acceptance_type = "FAT"
    mock_order.pass_rate = 95.5
    mock_order.total_items = 20
    mock_order.passed_items = 19
    mock_order.failed_items = 1
    mock_order.customer_signer = "John Doe"
    
    mock_user = Mock()
    mock_user.real_name = "Jane Smith"
    
    # Build report content
    content = build_report_content(mock_db, mock_order, "FAT-20231201-001", 1, mock_user)
    
    # Verify content contains expected elements
    assert "验收报告: FAT-20231201-001" in content
    assert "版本: V1" in content
    assert "验收单号: ORDER-001" in content
    assert "验收类型: FAT" in content
    assert "通过率: 95.5%" in content
    assert "客户签字: John Doe" in content
    assert "生成人: Jane Smith" in content


def test_get_report_version_first_report():
    """Test getting version for first report"""
    mock_db = Mock()
    
    # Mock query to return None (no existing reports)
    mock_query = Mock()
    mock_query.filter.return_value = mock_query  # Need to chain the filter call
    mock_query.order_by.return_value.first.return_value = None
    mock_db.query.return_value = mock_query
    
    result = get_report_version(mock_db, 123, "FAT")
    
    assert result == 1


def test_get_report_version_existing_report():
    """Test getting version for existing report"""
    mock_db = Mock()
    
    # Mock an existing report with version 2
    mock_existing_report = Mock()
    mock_existing_report.version = 2
    
    mock_query = Mock()
    mock_query.filter.return_value = mock_query  # Need to chain the filter call
    mock_query.order_by.return_value.first.return_value = mock_existing_report
    mock_db.query.return_value = mock_query
    
    result = get_report_version(mock_db, 123, "FAT")
    
    assert result == 3  # Next version should be 3


@patch('app.services.acceptance_report_service.os')
@patch('builtins.open', new_callable=MagicMock)
def test_save_report_file_txt_format(mock_open, mock_os):
    """Test saving report file in text format"""
    mock_os.path.join = lambda *args: '/'.join(args)
    mock_os.makedirs = Mock()
    
    content = "Test report content"
    order_no = "ORDER-001"
    report_type = "FAT"
    
    # Mock file operations
    mock_file = Mock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Test with use_pdf=False to ensure text format
    result = save_report_file(content, order_no, report_type, False, Mock(), Mock(), Mock())
    
    # Verify the file was saved as text
    assert result is not None
    assert result[1].endswith('.txt')  # Should be txt format
    mock_file.write.assert_called_once_with(content)


@patch('app.services.acceptance_report_service.REPORTLAB_AVAILABLE', True)
@patch('app.services.acceptance_report_service.os')
@patch('builtins.open', new_callable=MagicMock)
def test_save_report_file_pdf_format(mock_open, mock_os):
    """Test saving report file in PDF format when available"""
    mock_os.path.join = lambda *args: '/'.join(args)
    mock_os.makedirs = Mock()
    
    content = "Test report content"
    order_no = "ORDER-001"
    report_type = "SAT"
    
    # Mock file operations
    mock_file = Mock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Test with use_pdf=True and REPORTLAB_AVAILABLE=True
    result = save_report_file(content, order_no, report_type, True, Mock(), Mock(), Mock())
    
    # Verify the file was saved as pdf
    assert result is not None
    assert result[1].endswith('.pdf')  # Should be pdf format
    mock_file.write.assert_called_once_with(content)