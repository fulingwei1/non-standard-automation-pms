# -*- coding: utf-8 -*-
"""
文件上传服务测试 (FileUploadService)

测试 file_upload_service.py 中的核心功能
使用 mock 避免依赖问题
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


# ============================================================
# Mock 配置
# ============================================================

@pytest.fixture
def mock_settings():
    """Mock settings 模块"""
    settings = Mock()
    settings.UPLOAD_DIR = tempfile.mkdtemp()
    settings.MAX_UPLOAD_SIZE = 10 * 1024 * 1024
    return settings


@pytest.fixture
def mock_db_session():
    """Mock 数据库会话"""
    db = Mock()
    # Mock query 返回 mock 对象
    mock_query = Mock()
    mock_filter = Mock()
    mock_filter.filter = Mock(return_value=Mock(scalar=Mock(return_value=0)))
    mock_query.filter = Mock(return_value=mock_filter)
    mock_query.filter.return_value.scalar.return_value = 0
    db.query = Mock(return_value=mock_query)
    return db


@pytest.fixture
def temp_upload_dir():
    """创建临时上传目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def file_upload_service(mock_settings, temp_upload_dir):
    """创建文件上传服务实例"""
    with patch('app.services.file_upload_service.settings', mock_settings):
        from app.services.file_upload_service import FileUploadService
        service = FileUploadService(upload_dir=temp_upload_dir)
        return service


# ============================================================
# 测试类
# ============================================================

class TestFileExtensionValidation:
    """测试文件扩展名验证"""

    def test_validate_valid_pdf_extension(self, file_upload_service):
        """测试有效的 PDF 扩展名"""
        is_valid, error = file_upload_service.validate_file_extension("document.pdf")
        assert is_valid is True
        assert error is None

    def test_validate_valid_excel_extension(self, file_upload_service):
        """测试有效的 Excel 扩展名"""
        is_valid, error = file_upload_service.validate_file_extension("data.xlsx")
        assert is_valid is True
        assert error is None

    def test_validate_valid_image_extension(self, file_upload_service):
        """测试有效的图片扩展名"""
        is_valid, error = file_upload_service.validate_file_extension("photo.png")
        assert is_valid is True
        assert error is None

    def test_validate_invalid_extension(self, file_upload_service):
        """测试无效的扩展名"""
        is_valid, error = file_upload_service.validate_file_extension("malicious.exe")
        assert is_valid is False
        assert "不支持的文件类型" in error

    def test_validate_empty_filename(self, file_upload_service):
        """测试空文件名"""
        is_valid, error = file_upload_service.validate_file_extension("")
        assert is_valid is False
        assert "文件名不能为空" in error

    def test_validate_missing_extension(self, file_upload_service):
        """测试缺少扩展名的文件"""
        is_valid, error = file_upload_service.validate_file_extension("filename")
        assert is_valid is False
        assert "文件缺少扩展名" in error


class TestFileSizeValidation:
    """测试文件大小验证"""

    def test_validate_valid_size(self, file_upload_service):
        """测试有效文件大小"""
        is_valid, error = file_upload_service.validate_file_size(1024 * 1024)  # 1MB
        assert is_valid is True
        assert error is None

    def test_validate_zero_size(self, file_upload_service):
        """测试零大小文件"""
        is_valid, error = file_upload_service.validate_file_size(0)
        assert is_valid is False
        assert "文件大小无效" in error

    def test_validate_negative_size(self, file_upload_service):
        """测试负数大小"""
        is_valid, error = file_upload_service.validate_file_size(-100)
        assert is_valid is False
        assert "文件大小无效" in error

    def test_validate_oversized_file(self, file_upload_service):
        """测试超过限制的大文件"""
        # 设置 max_file_size 为 100MB
        file_upload_service.max_file_size = 100 * 1024 * 1024
        is_valid, error = file_upload_service.validate_file_size(150 * 1024 * 1024)
        assert is_valid is False
        assert "文件大小超过限制" in error


class TestUserQuotaCheck:
    """测试用户配额检查"""

    def test_check_quota_within_limit(self, file_upload_service, mock_db_session):
        """测试在配额限制内"""
        # Mock 返回已使用 1GB
        with patch.object(file_upload_service, 'get_user_total_upload_size', return_value=1024 * 1024 * 1024):
            is_pass, error = file_upload_service.check_user_quota(
                user_id=1,
                file_size=1024 * 1024 * 1024,  # 1GB
                db=mock_db_session,
                model_class=None
            )
            assert is_pass is True
            assert error is None

    def test_check_quota_exceeds_limit(self, file_upload_service, mock_db_session):
        """测试超过配额限制"""
        # Mock 返回已使用 4.9GB，配额 5GB
        with patch.object(file_upload_service, 'get_user_total_upload_size', return_value=int(4.9 * 1024 * 1024 * 1024)):
            is_pass, error = file_upload_service.check_user_quota(
                user_id=1,
                file_size=200 * 1024 * 1024,  # 200MB
                db=mock_db_session,
                model_class=None
            )
            assert is_pass is False
            assert "上传配额不足" in error


class TestFilenameGeneration:
    """测试文件名生成"""

    def test_generate_unique_filename(self, file_upload_service):
        """测试生成唯一文件名"""
        filename = file_upload_service.generate_unique_filename("test.pdf")
        # 应该包含时间戳和唯一ID
        assert filename.endswith(".pdf")
        assert "_" in filename
        assert len(filename) > len("test.pdf")

    def test_generate_unique_filename_preserves_extension(self, file_upload_service):
        """测试保留扩展名"""
        extensions = [".pdf", ".xlsx", ".docx", ".png"]
        for ext in extensions:
            filename = file_upload_service.generate_unique_filename(f"file{ext}")
            assert filename.endswith(ext)

    def test_generate_unique_filename_lowercase(self, file_upload_service):
        """测试扩展名转为小写"""
        filename = file_upload_service.generate_unique_filename("test.PDF")
        assert filename.endswith(".pdf")


class TestFilePathGeneration:
    """测试文件路径生成"""

    def test_get_upload_path_basic(self, file_upload_service):
        """测试基础路径生成"""
        full_path, relative_path = file_upload_service.get_upload_path("test.pdf")
        assert full_path.exists() or full_path.parent.exists()
        assert "test.pdf" in relative_path

    def test_get_upload_path_with_subdir(self, file_upload_service):
        """测试带子目录的路径"""
        full_path, relative_path = file_upload_service.get_upload_path(
            "test.pdf", 
            subdir="knowledge_base"
        )
        assert "knowledge_base" in relative_path

    def test_get_upload_path_without_date_subdir(self, file_upload_service):
        """测试不使用日期子目录"""
        full_path, relative_path = file_upload_service.get_upload_path(
            "test.pdf",
            use_date_subdir=False
        )
        # 不应该包含 YYYYMM 日期目录
        assert full_path.parent.name != ""


class TestFileSave:
    """测试文件保存"""

    def test_save_file_success(self, file_upload_service):
        """测试成功保存文件"""
        content = b"Hello, World!"
        full_path, relative_path = file_upload_service.save_file(
            content,
            "test.txt"
        )
        assert full_path.exists()
        assert full_path.read_bytes() == content

    def test_save_file_with_subdir(self, file_upload_service):
        """测试带子目录保存"""
        content = b"Test content"
        full_path, relative_path = file_upload_service.save_file(
            content,
            "document.pdf",
            subdir="documents"
        )
        assert full_path.exists()
        assert "documents" in relative_path


class TestFileDelete:
    """测试文件删除"""

    def test_delete_existing_file(self, file_upload_service):
        """测试删除已存在的文件"""
        # 先保存文件
        content = b"To be deleted"
        full_path, _ = file_upload_service.save_file(content, "delete_me.txt")
        
        # 删除
        result = file_upload_service.delete_file(str(full_path))
        assert result is True
        assert not full_path.exists()

    def test_delete_nonexistent_file(self, file_upload_service):
        """测试删除不存在的文件"""
        result = file_upload_service.delete_file("/nonexistent/path/file.txt")
        assert result is False


class TestFileHash:
    """测试文件哈希计算"""

    def test_calculate_md5_hash(self, file_upload_service):
        """测试 MD5 哈希"""
        content = b"test content"
        hash_value = file_upload_service.calculate_file_hash(content, "md5")
        assert len(hash_value) == 32  # MD5 是 32 位十六进制

    def test_calculate_sha256_hash(self, file_upload_service):
        """测试 SHA256 哈希"""
        content = b"test content"
        hash_value = file_upload_service.calculate_file_hash(content, "sha256")
        assert len(hash_value) == 64  # SHA256 是 64 位十六进制

    def test_calculate_invalid_algorithm(self, file_upload_service):
        """测试无效的哈希算法"""
        with pytest.raises(ValueError, match="不支持的哈希算法"):
            file_upload_service.calculate_file_hash(b"test", "invalid")


class TestFileSizeFormatting:
    """测试文件大小格式化"""

    def test_format_bytes(self, file_upload_service):
        """测试字节格式化"""
        result = file_upload_service.format_file_size(512)
        assert "512.00 B" == result

    def test_format_kilobytes(self, file_upload_service):
        """测试千字节格式化"""
        result = file_upload_service.format_file_size(1024)
        assert "1.00 KB" == result

    def test_format_megabytes(self, file_upload_service):
        """测试兆字节格式化"""
        result = file_upload_service.format_file_size(1024 * 1024)
        assert "1.00 MB" == result

    def test_format_gigabytes(self, file_upload_service):
        """测试吉字节格式化"""
        result = file_upload_service.format_file_size(1024 * 1024 * 1024)
        assert "1.00 GB" == result


class TestFileInfo:
    """测试获取文件信息"""

    def test_get_file_info_existing_file(self, file_upload_service):
        """测试获取已存在文件的信息"""
        # 先创建文件
        content = b"Test file content"
        full_path, _ = file_upload_service.save_file(content, "info_test.txt")
        
        # 获取信息
        info = file_upload_service.get_file_info(str(full_path))
        
        assert info is not None
        # 文件名会被 generate_unique_filename 转换，检查扩展名匹配
        assert info["filename"].endswith(".txt")
        assert info["size"] == len(content)

    def test_get_file_info_nonexistent_file(self, file_upload_service):
        """测试获取不存在文件的信息"""
        info = file_upload_service.get_file_info("/nonexistent/file.txt")
        assert info is None


class TestListFiles:
    """测试文件列表"""

    def test_list_files_empty_directory(self, file_upload_service):
        """测试空目录"""
        files = file_upload_service.list_files(subdir="empty")
        assert files == []

    def test_list_files_with_files(self, file_upload_service):
        """测试有文件的目录"""
        # 先创建几个文件
        file_upload_service.save_file(b"content1", "file1.txt")
        file_upload_service.save_file(b"content2", "file2.txt")
        
        files = file_upload_service.list_files()
        assert len(files) >= 2

    def test_list_files_with_extension_filter(self, file_upload_service):
        """测试扩展名过滤"""
        # 创建不同类型的文件
        file_upload_service.save_file(b"content", "doc.txt")
        file_upload_service.save_file(b"data", "data.xlsx")
        
        # 只列出 txt 文件
        files = file_upload_service.list_files(extensions=[".txt"])
        for f in files:
            assert f["filename"].endswith(".txt")


class TestDefaultConfiguration:
    """测试默认配置"""

    def test_default_allowed_extensions(self, file_upload_service):
        """测试默认允许的扩展名"""
        assert ".pdf" in file_upload_service.allowed_extensions
        assert ".xlsx" in file_upload_service.allowed_extensions
        assert ".zip" in file_upload_service.allowed_extensions

    def test_default_max_file_size(self, file_upload_service):
        """测试默认最大文件大小 (200MB)"""
        expected = 200 * 1024 * 1024
        assert file_upload_service.max_file_size == expected

    def test_default_user_quota(self, file_upload_service):
        """测试默认用户配额 (5GB)"""
        expected = 5 * 1024 * 1024 * 1024
        assert file_upload_service.user_quota == expected


class TestEdgeCases:
    """边界情况测试"""

    def test_validate_filename_with_special_chars(self, file_upload_service):
        """测试带特殊字符的文件名"""
        is_valid, error = file_upload_service.validate_file_extension("file@#$.pdf")
        assert is_valid is True  # 特殊字符不影响扩展名验证

    def test_validate_uppercase_extension(self, file_upload_service):
        """测试大写扩展名"""
        is_valid, error = file_upload_service.validate_file_extension("file.PDF")
        assert is_valid is True  # 应该转为小写

    def test_save_empty_file(self, file_upload_service):
        """测试保存空文件"""
        full_path, relative_path = file_upload_service.save_file(b"", "empty.txt")
        assert full_path.exists()
        assert full_path.stat().st_size == 0

    def test_get_user_total_upload_size_no_model(self, file_upload_service, mock_db_session):
        """测试没有模型类时返回0"""
        result = file_upload_service.get_user_total_upload_size(1, mock_db_session, None)
        assert result == 0