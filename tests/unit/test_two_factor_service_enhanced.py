# -*- coding: utf-8 -*-
"""
双因素认证服务增强单元测试

测试覆盖：
  - TOTP密钥生成和验证
  - QR码生成
  - 备用码生成和验证
  - 2FA启用/禁用流程
  - 加密/解密功能
  - 边界条件和异常处理
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime
import io
from typing import List

import pyotp
from PIL import Image

from app.services.two_factor_service import (
    TwoFactorService,
    _get_encryption_key,
    get_two_factor_service
)


class TestEncryptionKey(unittest.TestCase):
    """测试加密密钥生成"""
    
    @patch('app.services.two_factor_service.settings')
    def test_get_encryption_key_generates_valid_key(self, mock_settings):
        """测试生成有效的加密密钥"""
        mock_settings.SECRET_KEY = "test_secret_key_12345"
        key = _get_encryption_key()
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 44)  # Base64编码的32字节密钥
    
    @patch('app.services.two_factor_service.settings')
    def test_get_encryption_key_deterministic(self, mock_settings):
        """测试加密密钥生成的确定性"""
        mock_settings.SECRET_KEY = "test_secret_key_12345"
        key1 = _get_encryption_key()
        key2 = _get_encryption_key()
        self.assertEqual(key1, key2)
    
    @patch('app.services.two_factor_service.settings')
    def test_get_encryption_key_different_secrets(self, mock_settings):
        """测试不同SECRET_KEY生成不同密钥"""
        mock_settings.SECRET_KEY = "secret1"
        key1 = _get_encryption_key()
        
        mock_settings.SECRET_KEY = "secret2"
        key2 = _get_encryption_key()
        
        self.assertNotEqual(key1, key2)


class TestTwoFactorServiceInit(unittest.TestCase):
    """测试TwoFactorService初始化"""
    
    @patch('app.services.two_factor_service._get_encryption_key')
    def test_init_creates_encryption_key(self, mock_get_key):
        """测试初始化时创建加密密钥"""
        # 使用有效的Fernet密钥（32字节，base64编码）
        mock_get_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
        service = TwoFactorService()
        
        self.assertIsNotNone(service.encryption_key)
        self.assertIsNotNone(service.fernet)
        mock_get_key.assert_called_once()


class TestEncryptionDecryption(unittest.TestCase):
    """测试加密和解密功能"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
    
    def test_encrypt_secret(self):
        """测试加密TOTP密钥"""
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = self.service._encrypt_secret(secret)
        
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, secret)
        self.assertGreater(len(encrypted), len(secret))
    
    def test_decrypt_secret(self):
        """测试解密TOTP密钥"""
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = self.service._encrypt_secret(secret)
        decrypted = self.service._decrypt_secret(encrypted)
        
        self.assertEqual(decrypted, secret)
    
    def test_encrypt_decrypt_roundtrip(self):
        """测试加密解密往返"""
        original_secrets = [
            "JBSWY3DPEHPK3PXP",
            "ABCDEFGHIJKLMNOP",
            "1234567890ABCDEF",
            ""
        ]
        
        for secret in original_secrets:
            encrypted = self.service._encrypt_secret(secret)
            decrypted = self.service._decrypt_secret(encrypted)
            self.assertEqual(decrypted, secret)
    
    def test_decrypt_invalid_token(self):
        """测试解密无效token"""
        from cryptography.fernet import InvalidToken
        
        with self.assertRaises(InvalidToken):
            self.service._decrypt_secret("invalid_encrypted_data")


class TestTOTPGeneration(unittest.TestCase):
    """测试TOTP密钥生成"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
    
    def test_generate_totp_secret_format(self):
        """测试生成的TOTP密钥格式"""
        secret = self.service.generate_totp_secret()
        
        self.assertIsInstance(secret, str)
        self.assertEqual(len(secret), 32)
        # Base32字符集：A-Z, 2-7
        self.assertTrue(all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for c in secret))
    
    def test_generate_totp_secret_uniqueness(self):
        """测试生成的密钥唯一性"""
        secrets = [self.service.generate_totp_secret() for _ in range(10)]
        self.assertEqual(len(secrets), len(set(secrets)))


class TestQRCodeGeneration(unittest.TestCase):
    """测试二维码生成"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
    
    def test_generate_qr_code_returns_bytes(self):
        """测试生成二维码返回字节"""
        user = MagicMock()
        user.email = "test@example.com"
        user.username = "testuser"
        secret = "JBSWY3DPEHPK3PXP"
        
        qr_code = self.service.generate_qr_code(user, secret)
        
        self.assertIsInstance(qr_code, bytes)
        self.assertGreater(len(qr_code), 0)
    
    def test_generate_qr_code_valid_png(self):
        """测试生成的二维码是有效的PNG图片"""
        user = MagicMock()
        user.email = "test@example.com"
        user.username = "testuser"
        secret = "JBSWY3DPEHPK3PXP"
        
        qr_code = self.service.generate_qr_code(user, secret)
        
        # 验证PNG格式
        img = Image.open(io.BytesIO(qr_code))
        self.assertEqual(img.format, 'PNG')
    
    def test_generate_qr_code_custom_issuer(self):
        """测试自定义issuer名称"""
        user = MagicMock()
        user.email = "test@example.com"
        user.username = "testuser"
        secret = "JBSWY3DPEHPK3PXP"
        
        qr_code = self.service.generate_qr_code(user, secret, issuer_name="Custom App")
        
        self.assertIsInstance(qr_code, bytes)
        self.assertGreater(len(qr_code), 0)
    
    def test_generate_qr_code_username_fallback(self):
        """测试当email不存在时使用username"""
        user = MagicMock()
        user.email = None
        user.username = "testuser"
        secret = "JBSWY3DPEHPK3PXP"
        
        qr_code = self.service.generate_qr_code(user, secret)
        
        self.assertIsInstance(qr_code, bytes)
        self.assertGreater(len(qr_code), 0)


class TestTOTPVerification(unittest.TestCase):
    """测试TOTP验证"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
    
    def test_verify_totp_code_valid(self):
        """测试验证有效的TOTP码"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        result = self.service.verify_totp_code(secret, code)
        self.assertTrue(result)
    
    def test_verify_totp_code_invalid(self):
        """测试验证无效的TOTP码"""
        secret = pyotp.random_base32()
        
        result = self.service.verify_totp_code(secret, "000000")
        self.assertFalse(result)
    
    def test_verify_totp_code_wrong_format(self):
        """测试验证格式错误的TOTP码"""
        secret = pyotp.random_base32()
        
        result = self.service.verify_totp_code(secret, "12345")  # 只有5位
        self.assertFalse(result)
    
    def test_verify_totp_code_custom_window(self):
        """测试自定义时间窗口"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        result = self.service.verify_totp_code(secret, code, window=2)
        self.assertTrue(result)


class TestSetup2FA(unittest.TestCase):
    """测试2FA设置流程"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "testuser"
        self.user.email = "test@example.com"
    
    def test_setup_2fa_for_user_success(self):
        """测试成功设置2FA"""
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.delete.return_value = 0
        
        secret, qr_code = self.service.setup_2fa_for_user(self.db, self.user)
        
        self.assertIsInstance(secret, str)
        self.assertEqual(len(secret), 32)
        self.assertIsInstance(qr_code, bytes)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
    
    def test_setup_2fa_replaces_existing(self):
        """测试设置2FA时替换旧配置"""
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.delete.return_value = 1  # 删除了1条旧记录
        
        secret, qr_code = self.service.setup_2fa_for_user(self.db, self.user)
        
        mock_query.delete.assert_called_once()
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()


class TestEnable2FA(unittest.TestCase):
    """测试启用2FA"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "testuser"
    
    def test_enable_2fa_no_secret_record(self):
        """测试未找到2FA配置"""
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.first.return_value = None
        
        success, message, backup_codes = self.service.enable_2fa_for_user(
            self.db, self.user, "123456"
        )
        
        self.assertFalse(success)
        self.assertIn("未找到2FA配置", message)
        self.assertIsNone(backup_codes)
    
    @patch.object(TwoFactorService, 'verify_totp_code')
    @patch.object(TwoFactorService, '_generate_backup_codes')
    def test_enable_2fa_invalid_code(self, mock_gen_codes, mock_verify):
        """测试TOTP码错误"""
        secret_record = MagicMock()
        secret_record.secret_encrypted = self.service._encrypt_secret("JBSWY3DPEHPK3PXP")
        
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.first.return_value = secret_record
        mock_verify.return_value = False
        
        success, message, backup_codes = self.service.enable_2fa_for_user(
            self.db, self.user, "000000"
        )
        
        self.assertFalse(success)
        self.assertIn("验证码错误", message)
        self.assertIsNone(backup_codes)
    
    @patch.object(TwoFactorService, 'verify_totp_code')
    @patch.object(TwoFactorService, '_generate_backup_codes')
    def test_enable_2fa_success(self, mock_gen_codes, mock_verify):
        """测试成功启用2FA"""
        secret_record = MagicMock()
        secret_record.secret_encrypted = self.service._encrypt_secret("JBSWY3DPEHPK3PXP")
        
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.first.return_value = secret_record
        mock_verify.return_value = True
        mock_gen_codes.return_value = ["12345678", "87654321"]
        
        success, message, backup_codes = self.service.enable_2fa_for_user(
            self.db, self.user, "123456"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "2FA已启用")
        self.assertEqual(len(backup_codes), 2)
        self.assertTrue(self.user.two_factor_enabled)
        self.assertEqual(self.user.two_factor_method, "totp")
        self.assertIsNotNone(self.user.two_factor_verified_at)  # 验证时间已设置
        self.db.commit.assert_called_once()


class TestDisable2FA(unittest.TestCase):
    """测试禁用2FA"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "testuser"
        self.user.password_hash = "$2b$12$abc123"
    
    @patch('app.services.two_factor_service.verify_password')
    def test_disable_2fa_wrong_password(self, mock_verify_pwd):
        """测试密码错误"""
        mock_verify_pwd.return_value = False
        
        success, message = self.service.disable_2fa_for_user(
            self.db, self.user, "wrong_password"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "密码错误")
        self.db.commit.assert_not_called()
    
    @patch('app.services.two_factor_service.verify_password')
    def test_disable_2fa_success(self, mock_verify_pwd):
        """测试成功禁用2FA"""
        mock_verify_pwd.return_value = True
        
        mock_secret_query = self.db.query.return_value.filter.return_value
        mock_backup_query = self.db.query.return_value.filter.return_value
        
        success, message = self.service.disable_2fa_for_user(
            self.db, self.user, "correct_password"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "2FA已禁用")
        self.assertFalse(self.user.two_factor_enabled)
        self.assertIsNone(self.user.two_factor_method)
        self.assertIsNone(self.user.two_factor_verified_at)
        self.db.commit.assert_called_once()


class TestVerify2FACode(unittest.TestCase):
    """测试2FA验证"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "testuser"
    
    def test_verify_2fa_not_enabled(self):
        """测试未启用2FA"""
        self.user.two_factor_enabled = False
        
        success, message = self.service.verify_2fa_code(self.db, self.user, "123456")
        
        self.assertFalse(success)
        self.assertEqual(message, "未启用2FA")
    
    @patch.object(TwoFactorService, 'verify_totp_code')
    def test_verify_2fa_totp_success(self, mock_verify_totp):
        """测试TOTP验证成功"""
        self.user.two_factor_enabled = True
        
        secret_record = MagicMock()
        secret_record.secret_encrypted = self.service._encrypt_secret("JBSWY3DPEHPK3PXP")
        
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.first.return_value = secret_record
        mock_verify_totp.return_value = True
        
        success, message = self.service.verify_2fa_code(self.db, self.user, "123456")
        
        self.assertTrue(success)
        self.assertEqual(message, "验证成功")
    
    @patch.object(TwoFactorService, 'verify_totp_code')
    @patch.object(TwoFactorService, '_verify_backup_code')
    def test_verify_2fa_backup_code_success(self, mock_verify_backup, mock_verify_totp):
        """测试备用码验证成功"""
        self.user.two_factor_enabled = True
        
        secret_record = MagicMock()
        secret_record.secret_encrypted = self.service._encrypt_secret("JBSWY3DPEHPK3PXP")
        
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.first.return_value = secret_record
        mock_verify_totp.return_value = False
        mock_verify_backup.return_value = (True, "备用码验证成功")
        
        success, message = self.service.verify_2fa_code(
            self.db, self.user, "12345678", ip_address="192.168.1.1"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "备用码验证成功")
    
    @patch.object(TwoFactorService, 'verify_totp_code')
    @patch.object(TwoFactorService, '_verify_backup_code')
    def test_verify_2fa_all_failed(self, mock_verify_backup, mock_verify_totp):
        """测试所有验证方式都失败"""
        self.user.two_factor_enabled = True
        
        secret_record = MagicMock()
        secret_record.secret_encrypted = self.service._encrypt_secret("JBSWY3DPEHPK3PXP")
        
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.first.return_value = secret_record
        mock_verify_totp.return_value = False
        mock_verify_backup.return_value = (False, "备用码无效")
        
        success, message = self.service.verify_2fa_code(self.db, self.user, "000000")
        
        self.assertFalse(success)
        self.assertEqual(message, "验证码错误")


class TestGenerateBackupCodes(unittest.TestCase):
    """测试备用码生成"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "testuser"
    
    @patch('app.services.two_factor_service.get_password_hash')
    def test_generate_backup_codes_default_count(self, mock_hash):
        """测试默认生成10个备用码"""
        mock_hash.side_effect = lambda x: f"hash_{x}"
        
        codes = self.service._generate_backup_codes(self.db, self.user)
        
        self.assertEqual(len(codes), 10)
        self.assertEqual(self.db.add.call_count, 10)
        self.db.commit.assert_called_once()
    
    @patch('app.services.two_factor_service.get_password_hash')
    def test_generate_backup_codes_custom_count(self, mock_hash):
        """测试自定义数量"""
        mock_hash.side_effect = lambda x: f"hash_{x}"
        
        codes = self.service._generate_backup_codes(self.db, self.user, count=5)
        
        self.assertEqual(len(codes), 5)
        self.assertEqual(self.db.add.call_count, 5)
    
    @patch('app.services.two_factor_service.get_password_hash')
    def test_generate_backup_codes_format(self, mock_hash):
        """测试备用码格式（8位数字）"""
        mock_hash.side_effect = lambda x: f"hash_{x}"
        
        codes = self.service._generate_backup_codes(self.db, self.user)
        
        for code in codes:
            self.assertEqual(len(code), 8)
            self.assertTrue(code.isdigit())
    
    @patch('app.services.two_factor_service.get_password_hash')
    def test_generate_backup_codes_deletes_old(self, mock_hash):
        """测试删除旧备用码"""
        mock_hash.side_effect = lambda x: f"hash_{x}"
        mock_query = self.db.query.return_value.filter.return_value
        
        codes = self.service._generate_backup_codes(self.db, self.user)
        
        mock_query.delete.assert_called_once()


class TestVerifyBackupCode(unittest.TestCase):
    """测试备用码验证"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "testuser"
    
    @patch('app.services.two_factor_service.verify_password')
    def test_verify_backup_code_no_codes(self, mock_verify_pwd):
        """测试没有可用备用码"""
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.all.return_value = []
        
        success, message = self.service._verify_backup_code(
            self.db, self.user, "12345678"
        )
        
        self.assertFalse(success)
        self.assertIn("无效或已使用", message)
    
    @patch('app.services.two_factor_service.verify_password')
    def test_verify_backup_code_success(self, mock_verify_pwd):
        """测试备用码验证成功"""
        backup_code = MagicMock()
        backup_code.code_hash = "hash_12345678"
        
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.all.return_value = [backup_code]
        mock_verify_pwd.return_value = True
        
        success, message = self.service._verify_backup_code(
            self.db, self.user, "12345678", ip_address="192.168.1.1"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "备用码验证成功")
        self.assertTrue(backup_code.used)
        self.assertIsNotNone(backup_code.used_at)  # 验证时间已设置
        self.assertEqual(backup_code.used_ip, "192.168.1.1")
        self.db.commit.assert_called_once()
    
    @patch('app.services.two_factor_service.verify_password')
    def test_verify_backup_code_invalid(self, mock_verify_pwd):
        """测试备用码无效"""
        backup_code = MagicMock()
        backup_code.code_hash = "hash_12345678"
        
        mock_query = self.db.query.return_value.filter.return_value
        mock_query.all.return_value = [backup_code]
        mock_verify_pwd.return_value = False
        
        success, message = self.service._verify_backup_code(
            self.db, self.user, "00000000"
        )
        
        self.assertFalse(success)
        self.assertIn("无效或已使用", message)


class TestBackupCodesInfo(unittest.TestCase):
    """测试备用码信息查询"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
    
    def test_get_backup_codes_info(self):
        """测试获取备用码信息"""
        mock_total_query = MagicMock()
        mock_total_query.count.return_value = 10
        
        mock_unused_query = MagicMock()
        mock_unused_query.count.return_value = 7
        
        self.db.query.return_value.filter.return_value = mock_total_query
        # 第二次调用返回unused查询
        self.db.query.return_value.filter.side_effect = [mock_total_query, mock_unused_query]
        
        info = self.service.get_backup_codes_info(self.db, self.user)
        
        self.assertEqual(info['total'], 10)
        self.assertEqual(info['unused'], 7)
        self.assertEqual(info['used'], 3)
    
    def test_get_backup_codes_info_all_unused(self):
        """测试所有备用码未使用"""
        mock_total_query = MagicMock()
        mock_total_query.count.return_value = 10
        
        mock_unused_query = MagicMock()
        mock_unused_query.count.return_value = 10
        
        self.db.query.return_value.filter.side_effect = [mock_total_query, mock_unused_query]
        
        info = self.service.get_backup_codes_info(self.db, self.user)
        
        self.assertEqual(info['total'], 10)
        self.assertEqual(info['unused'], 10)
        self.assertEqual(info['used'], 0)


class TestRegenerateBackupCodes(unittest.TestCase):
    """测试重新生成备用码"""
    
    def setUp(self):
        with patch('app.services.two_factor_service._get_encryption_key') as mock_key:
            mock_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
            self.service = TwoFactorService()
        
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.username = "testuser"
        self.user.password_hash = "$2b$12$abc123"
    
    def test_regenerate_backup_codes_not_enabled(self):
        """测试未启用2FA时重新生成"""
        self.user.two_factor_enabled = False
        
        success, message, codes = self.service.regenerate_backup_codes(
            self.db, self.user, "password"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "未启用2FA")
        self.assertIsNone(codes)
    
    @patch('app.services.two_factor_service.verify_password')
    def test_regenerate_backup_codes_wrong_password(self, mock_verify_pwd):
        """测试密码错误"""
        self.user.two_factor_enabled = True
        mock_verify_pwd.return_value = False
        
        success, message, codes = self.service.regenerate_backup_codes(
            self.db, self.user, "wrong_password"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "密码错误")
        self.assertIsNone(codes)
    
    @patch('app.services.two_factor_service.verify_password')
    @patch.object(TwoFactorService, '_generate_backup_codes')
    def test_regenerate_backup_codes_success(self, mock_gen_codes, mock_verify_pwd):
        """测试成功重新生成备用码"""
        self.user.two_factor_enabled = True
        mock_verify_pwd.return_value = True
        mock_gen_codes.return_value = ["12345678", "87654321"]
        
        success, message, codes = self.service.regenerate_backup_codes(
            self.db, self.user, "correct_password"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "备用码已重新生成")
        self.assertEqual(len(codes), 2)
        mock_gen_codes.assert_called_once_with(self.db, self.user)


class TestGetTwoFactorService(unittest.TestCase):
    """测试单例服务"""
    
    @patch('app.services.two_factor_service._get_encryption_key')
    def test_get_two_factor_service_singleton(self, mock_get_key):
        """测试单例模式"""
        mock_get_key.return_value = b'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
        
        # 重置全局单例
        import app.services.two_factor_service
        app.services.two_factor_service._two_factor_service = None
        
        service1 = get_two_factor_service()
        service2 = get_two_factor_service()
        
        self.assertIsInstance(service1, TwoFactorService)
        self.assertIs(service1, service2)


if __name__ == '__main__':
    unittest.main()
