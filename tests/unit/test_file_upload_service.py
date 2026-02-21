# -*- coding: utf-8 -*-
"""
文件上传服务单元测试

Mock策略：
1. 只mock外部依赖（文件系统操作、数据库操作）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, mock_open
from pathlib import Path
from datetime import datetime
import hashlib
import uuid

from app.services.file_upload_service import FileUploadService


class TestFileUploadServiceInit(unittest.TestCase):
    """测试初始化"""
    
    @patch('app.services.file_upload_service.settings')
    def test_init_with_defaults(self, mock_settings):
        """测试使用默认参数初始化"""
        mock_settings.UPLOAD_DIR = "/tmp/uploads"
        
        service = FileUploadService()
        
        self.assertEqual(service.upload_dir, Path("/tmp/uploads"))
        self.assertEqual(service.allowed_extensions, FileUploadService.DEFAULT_ALLOWED_EXTENSIONS)
        self.assertEqual(service.max_file_size, FileUploadService.DEFAULT_MAX_FILE_SIZE)
        self.assertEqual(service.user_quota, FileUploadService.DEFAULT_USER_QUOTA)
    
    @patch('pathlib.Path.mkdir')
    def test_init_with_custom_params(self, mock_mkdir):
        """测试使用自定义参数初始化"""
        custom_dir = Path("/custom/upload")
        custom_extensions = {'.jpg', '.png'}
        custom_max_size = 10 * 1024 * 1024  # 10MB
        custom_quota = 1 * 1024 * 1024 * 1024  # 1GB
        
        service = FileUploadService(
            upload_dir=custom_dir,
            allowed_extensions=custom_extensions,
            max_file_size=custom_max_size,
            user_quota=custom_quota
        )
        
        self.assertEqual(service.upload_dir, custom_dir)
        self.assertEqual(service.allowed_extensions, custom_extensions)
        self.assertEqual(service.max_file_size, custom_max_size)
        self.assertEqual(service.user_quota, custom_quota)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestValidateFileExtension(unittest.TestCase):
    """测试文件扩展名验证"""
    
    def setUp(self):
        self.service = FileUploadService(
            upload_dir=Path("/tmp"),
            allowed_extensions={'.pdf', '.jpg', '.png'}
        )
    
    def test_valid_extension(self):
        """测试有效的文件扩展名"""
        is_valid, error = self.service.validate_file_extension("document.pdf")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_valid_extension_case_insensitive(self):
        """测试扩展名不区分大小写"""
        is_valid, error = self.service.validate_file_extension("image.PNG")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_invalid_extension(self):
        """测试无效的文件扩展名"""
        is_valid, error = self.service.validate_file_extension("script.exe")
        self.assertFalse(is_valid)
        self.assertIn("不支持的文件类型", error)
    
    def test_empty_filename(self):
        """测试空文件名"""
        is_valid, error = self.service.validate_file_extension("")
        self.assertFalse(is_valid)
        self.assertEqual(error, "文件名不能为空")
    
    def test_filename_without_extension(self):
        """测试没有扩展名的文件"""
        is_valid, error = self.service.validate_file_extension("noextension")
        self.assertFalse(is_valid)
        self.assertEqual(error, "文件缺少扩展名")


class TestValidateFileSize(unittest.TestCase):
    """测试文件大小验证"""
    
    def setUp(self):
        self.service = FileUploadService(
            upload_dir=Path("/tmp"),
            max_file_size=10 * 1024 * 1024  # 10MB
        )
    
    def test_valid_file_size(self):
        """测试有效的文件大小"""
        is_valid, error = self.service.validate_file_size(5 * 1024 * 1024)  # 5MB
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_file_size_at_limit(self):
        """测试恰好等于限制的文件大小"""
        is_valid, error = self.service.validate_file_size(10 * 1024 * 1024)  # 10MB
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_file_size_exceed_limit(self):
        """测试超过限制的文件大小"""
        is_valid, error = self.service.validate_file_size(15 * 1024 * 1024)  # 15MB
        self.assertFalse(is_valid)
        self.assertIn("文件大小超过限制", error)
        self.assertIn("10MB", error)
    
    def test_zero_file_size(self):
        """测试零大小文件"""
        is_valid, error = self.service.validate_file_size(0)
        self.assertFalse(is_valid)
        self.assertEqual(error, "文件大小无效")
    
    def test_negative_file_size(self):
        """测试负数文件大小"""
        is_valid, error = self.service.validate_file_size(-100)
        self.assertFalse(is_valid)
        self.assertEqual(error, "文件大小无效")


class TestCheckUserQuota(unittest.TestCase):
    """测试用户配额检查"""
    
    def setUp(self):
        self.service = FileUploadService(
            upload_dir=Path("/tmp"),
            user_quota=1 * 1024 * 1024 * 1024  # 1GB
        )
        self.mock_db = MagicMock()
    
    @patch.object(FileUploadService, 'get_user_total_upload_size')
    def test_quota_check_pass(self, mock_get_size):
        """测试配额检查通过"""
        mock_get_size.return_value = 500 * 1024 * 1024  # 已使用500MB
        
        is_valid, error = self.service.check_user_quota(
            user_id=1,
            file_size=100 * 1024 * 1024,  # 上传100MB
            db=self.mock_db
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    @patch.object(FileUploadService, 'get_user_total_upload_size')
    def test_quota_check_fail(self, mock_get_size):
        """测试配额检查失败"""
        mock_get_size.return_value = 950 * 1024 * 1024  # 已使用950MB
        
        is_valid, error = self.service.check_user_quota(
            user_id=1,
            file_size=100 * 1024 * 1024,  # 上传100MB
            db=self.mock_db
        )
        
        self.assertFalse(is_valid)
        self.assertIn("上传配额不足", error)
    
    @patch.object(FileUploadService, 'get_user_total_upload_size')
    def test_quota_check_at_limit(self, mock_get_size):
        """测试恰好达到配额限制"""
        mock_get_size.return_value = 1024 * 1024 * 1024  # 已使用1GB
        
        is_valid, error = self.service.check_user_quota(
            user_id=1,
            file_size=1,  # 上传1字节
            db=self.mock_db
        )
        
        self.assertFalse(is_valid)
        self.assertIn("上传配额不足", error)


class TestGetUserTotalUploadSize(unittest.TestCase):
    """测试获取用户上传总大小"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp"))
        self.mock_db = MagicMock()
    
    def test_get_total_size_no_model(self):
        """测试没有提供模型类时返回0"""
        result = self.service.get_user_total_upload_size(
            user_id=1,
            db=self.mock_db,
            model_class=None
        )
        self.assertEqual(result, 0)
    
    def test_get_total_size_with_data(self):
        """测试有数据时返回正确总和"""
        mock_model = MagicMock()
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = 1024 * 1024 * 100  # 100MB
        
        result = self.service.get_user_total_upload_size(
            user_id=1,
            db=self.mock_db,
            model_class=mock_model
        )
        
        self.assertEqual(result, 1024 * 1024 * 100)
    
    def test_get_total_size_no_data(self):
        """测试没有数据时返回0"""
        mock_model = MagicMock()
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.scalar.return_value = None
        
        result = self.service.get_user_total_upload_size(
            user_id=1,
            db=self.mock_db,
            model_class=mock_model
        )
        
        self.assertEqual(result, 0)


class TestGenerateUniqueFilename(unittest.TestCase):
    """测试生成唯一文件名"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp"))
    
    @patch('app.services.file_upload_service.uuid.uuid4')
    @patch('app.services.file_upload_service.datetime')
    def test_generate_unique_filename(self, mock_datetime, mock_uuid):
        """测试生成唯一文件名的格式"""
        # Mock datetime
        mock_now = MagicMock()
        mock_now.strftime.return_value = "20240101120000"
        mock_datetime.now.return_value = mock_now
        
        # Mock uuid
        mock_uuid_obj = MagicMock()
        mock_uuid_obj.hex = "abcdef123456789"
        mock_uuid.return_value = mock_uuid_obj
        
        result = self.service.generate_unique_filename("document.pdf")
        
        self.assertEqual(result, "20240101120000_abcdef12.pdf")
    
    def test_generate_unique_filename_preserves_extension(self):
        """测试保留原始扩展名"""
        result = self.service.generate_unique_filename("image.PNG")
        self.assertTrue(result.endswith(".png"))  # 转小写
    
    def test_generate_unique_filename_is_unique(self):
        """测试每次生成的文件名都不同"""
        result1 = self.service.generate_unique_filename("file.txt")
        result2 = self.service.generate_unique_filename("file.txt")
        
        # 由于包含时间戳和随机UUID，两次生成应该不同
        # 注意：这个测试在极端情况下可能失败（同一毫秒内生成且UUID碰撞）
        self.assertNotEqual(result1, result2)


class TestGetUploadPath(unittest.TestCase):
    """测试获取上传路径"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp/uploads"))
    
    @patch('app.services.file_upload_service.datetime')
    def test_get_upload_path_with_subdir_and_date(self, mock_datetime):
        """测试带子目录和日期目录"""
        mock_now = MagicMock()
        mock_now.strftime.return_value = "202401"
        mock_datetime.now.return_value = mock_now
        
        full_path, relative_path = self.service.get_upload_path(
            filename="test.pdf",
            subdir="knowledge_base",
            use_date_subdir=True
        )
        
        self.assertEqual(
            full_path,
            Path("/tmp/uploads/knowledge_base/202401/test.pdf")
        )
        self.assertEqual(relative_path, "knowledge_base/202401/test.pdf")
    
    def test_get_upload_path_without_date_subdir(self):
        """测试不使用日期子目录"""
        full_path, relative_path = self.service.get_upload_path(
            filename="test.pdf",
            subdir="documents",
            use_date_subdir=False
        )
        
        self.assertEqual(
            full_path,
            Path("/tmp/uploads/documents/test.pdf")
        )
        self.assertEqual(relative_path, "documents/test.pdf")
    
    def test_get_upload_path_no_subdir(self):
        """测试没有子目录"""
        full_path, relative_path = self.service.get_upload_path(
            filename="test.pdf",
            subdir=None,
            use_date_subdir=False
        )
        
        self.assertEqual(
            full_path,
            Path("/tmp/uploads/test.pdf")
        )
        self.assertEqual(relative_path, "test.pdf")


class TestSaveFile(unittest.TestCase):
    """测试保存文件"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp/uploads"))
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(FileUploadService, 'get_upload_path')
    @patch.object(FileUploadService, 'generate_unique_filename')
    def test_save_file(self, mock_generate, mock_get_path, mock_file):
        """测试保存文件"""
        mock_generate.return_value = "unique_file.pdf"
        mock_get_path.return_value = (
            Path("/tmp/uploads/docs/unique_file.pdf"),
            "docs/unique_file.pdf"
        )
        
        file_content = b"test content"
        
        full_path, relative_path = self.service.save_file(
            file_content=file_content,
            filename="original.pdf",
            subdir="docs",
            use_date_subdir=False
        )
        
        self.assertEqual(full_path, Path("/tmp/uploads/docs/unique_file.pdf"))
        self.assertEqual(relative_path, "docs/unique_file.pdf")
        
        # 验证文件写入
        mock_file.assert_called_once_with(Path("/tmp/uploads/docs/unique_file.pdf"), 'wb')
        mock_file().write.assert_called_once_with(file_content)


class TestDeleteFile(unittest.TestCase):
    """测试删除文件"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp/uploads"))
    
    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_delete_file_success(self, mock_exists, mock_is_file, mock_unlink):
        """测试成功删除文件"""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        result = self.service.delete_file("docs/test.pdf")
        
        self.assertTrue(result)
        mock_unlink.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_delete_file_not_exists(self, mock_exists):
        """测试删除不存在的文件"""
        mock_exists.return_value = False
        
        result = self.service.delete_file("nonexistent.pdf")
        
        self.assertFalse(result)
    
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_delete_file_is_directory(self, mock_exists, mock_is_file):
        """测试路径是目录而不是文件"""
        mock_exists.return_value = True
        mock_is_file.return_value = False
        
        result = self.service.delete_file("some_directory")
        
        self.assertFalse(result)
    
    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_delete_file_exception(self, mock_exists, mock_is_file, mock_unlink):
        """测试删除文件时发生异常"""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_unlink.side_effect = OSError("Permission denied")
        
        result = self.service.delete_file("protected.pdf")
        
        self.assertFalse(result)


class TestCalculateFileHash(unittest.TestCase):
    """测试计算文件哈希"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp"))
        self.test_content = b"test file content"
    
    def test_calculate_md5_hash(self):
        """测试计算MD5哈希"""
        expected = hashlib.md5(self.test_content).hexdigest()
        result = self.service.calculate_file_hash(self.test_content, 'md5')
        self.assertEqual(result, expected)
    
    def test_calculate_sha1_hash(self):
        """测试计算SHA1哈希"""
        expected = hashlib.sha1(self.test_content).hexdigest()
        result = self.service.calculate_file_hash(self.test_content, 'sha1')
        self.assertEqual(result, expected)
    
    def test_calculate_sha256_hash(self):
        """测试计算SHA256哈希"""
        expected = hashlib.sha256(self.test_content).hexdigest()
        result = self.service.calculate_file_hash(self.test_content, 'sha256')
        self.assertEqual(result, expected)
    
    def test_calculate_hash_unsupported_algorithm(self):
        """测试不支持的哈希算法"""
        with self.assertRaises(ValueError) as context:
            self.service.calculate_file_hash(self.test_content, 'unknown')
        
        self.assertIn("不支持的哈希算法", str(context.exception))


class TestGetFileInfo(unittest.TestCase):
    """测试获取文件信息"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp/uploads"))
    
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_get_file_info_success(self, mock_exists, mock_stat):
        """测试成功获取文件信息"""
        mock_exists.return_value = True
        
        # Mock stat结果
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_ctime = 1640000000.0
        mock_stat_result.st_mtime = 1640000100.0
        mock_stat.return_value = mock_stat_result
        
        result = self.service.get_file_info("docs/test.pdf")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['filename'], 'test.pdf')
        self.assertEqual(result['size'], 1024)
        self.assertIn('size_human', result)
        self.assertIn('created_at', result)
        self.assertIn('modified_at', result)
    
    @patch('pathlib.Path.exists')
    def test_get_file_info_not_exists(self, mock_exists):
        """测试文件不存在"""
        mock_exists.return_value = False
        
        result = self.service.get_file_info("nonexistent.pdf")
        
        self.assertIsNone(result)
    
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_get_file_info_exception(self, mock_exists, mock_stat):
        """测试获取信息时发生异常"""
        mock_exists.return_value = True
        mock_stat.side_effect = OSError("Permission denied")
        
        result = self.service.get_file_info("protected.pdf")
        
        self.assertIsNone(result)


class TestFormatFileSize(unittest.TestCase):
    """测试格式化文件大小"""
    
    def test_format_bytes(self):
        """测试字节格式化"""
        result = FileUploadService.format_file_size(500)
        self.assertEqual(result, "500.00 B")
    
    def test_format_kilobytes(self):
        """测试KB格式化"""
        result = FileUploadService.format_file_size(1024 * 5)
        self.assertEqual(result, "5.00 KB")
    
    def test_format_megabytes(self):
        """测试MB格式化"""
        result = FileUploadService.format_file_size(1024 * 1024 * 10)
        self.assertEqual(result, "10.00 MB")
    
    def test_format_gigabytes(self):
        """测试GB格式化"""
        result = FileUploadService.format_file_size(1024 * 1024 * 1024 * 2)
        self.assertEqual(result, "2.00 GB")
    
    def test_format_terabytes(self):
        """测试TB格式化"""
        result = FileUploadService.format_file_size(1024 * 1024 * 1024 * 1024 * 3)
        self.assertEqual(result, "3.00 TB")
    
    def test_format_zero(self):
        """测试零大小"""
        result = FileUploadService.format_file_size(0)
        self.assertEqual(result, "0.00 B")


class TestListFiles(unittest.TestCase):
    """测试列出文件"""
    
    def setUp(self):
        self.service = FileUploadService(upload_dir=Path("/tmp/uploads"))
    
    @patch('pathlib.Path.exists')
    def test_list_files_directory_not_exists(self, mock_exists):
        """测试目录不存在"""
        mock_exists.return_value = False
        
        result = self.service.list_files(subdir="nonexistent")
        
        self.assertEqual(result, [])
    
    @patch.object(FileUploadService, 'get_file_info')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_list_files_success(self, mock_exists, mock_rglob, mock_get_info):
        """测试成功列出文件"""
        mock_exists.return_value = True
        
        # Mock文件列表
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.suffix = '.pdf'
        
        mock_file2 = MagicMock()
        mock_file2.is_file.return_value = True
        mock_file2.suffix = '.jpg'
        
        mock_dir = MagicMock()
        mock_dir.is_file.return_value = False
        
        mock_rglob.return_value = [mock_file1, mock_file2, mock_dir]
        
        # Mock文件信息
        mock_get_info.side_effect = [
            {
                'filename': 'doc.pdf',
                'size': 1024,
                'modified_at': datetime(2024, 1, 2)
            },
            {
                'filename': 'image.jpg',
                'size': 2048,
                'modified_at': datetime(2024, 1, 1)
            }
        ]
        
        result = self.service.list_files()
        
        self.assertEqual(len(result), 2)
        # 应按修改时间倒序排序
        self.assertEqual(result[0]['filename'], 'doc.pdf')
        self.assertEqual(result[1]['filename'], 'image.jpg')
    
    @patch.object(FileUploadService, 'get_file_info')
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_list_files_with_extension_filter(self, mock_exists, mock_rglob, mock_get_info):
        """测试扩展名过滤"""
        mock_exists.return_value = True
        
        mock_pdf = MagicMock()
        mock_pdf.is_file.return_value = True
        mock_pdf.suffix = '.pdf'
        
        mock_jpg = MagicMock()
        mock_jpg.is_file.return_value = True
        mock_jpg.suffix = '.jpg'
        
        mock_rglob.return_value = [mock_pdf, mock_jpg]
        
        mock_get_info.return_value = {
            'filename': 'doc.pdf',
            'modified_at': datetime(2024, 1, 1)
        }
        
        result = self.service.list_files(extensions=['.pdf'])
        
        # 只应返回PDF文件
        self.assertEqual(len(result), 1)
        mock_get_info.assert_called_once()  # 只调用一次（jpg被过滤）
    
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_list_files_exception(self, mock_exists, mock_rglob):
        """测试列出文件时发生异常"""
        mock_exists.return_value = True
        mock_rglob.side_effect = OSError("Permission denied")
        
        result = self.service.list_files()
        
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
