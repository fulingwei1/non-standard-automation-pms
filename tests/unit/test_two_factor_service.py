# -*- coding: utf-8 -*-
"""
双因素认证服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率70%+
"""

import base64
import unittest
from datetime import datetime
from unittest.mock import MagicMock, call, patch

from app.services.two_factor_service import (
    TwoFactorService,
    _get_encryption_key,
    get_two_factor_service,
)


class TestEncryptionKey(unittest.TestCase):
    """测试加密密钥生成"""

    def test_get_encryption_key(self):
        """测试获取加密密钥"""
        key = _get_encryption_key()
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 44)  # base64编码后的32字节密钥

    def test_get_encryption_key_deterministic(self):
        """测试密钥生成的确定性（相同配置应生成相同密钥）"""
        key1 = _get_encryption_key()
        key2 = _get_encryption_key()
        self.assertEqual(key1, key2)


class TestTwoFactorServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init(self):
        """测试服务初始化"""
        service = TwoFactorService()
        self.assertIsNotNone(service.encryption_key)
        self.assertIsNotNone(service.fernet)

    def test_singleton(self):
        """测试单例模式"""
        service1 = get_two_factor_service()
        service2 = get_two_factor_service()
        self.assertIs(service1, service2)


class TestEncryptionDecryption(unittest.TestCase):
    """测试加密/解密功能"""

    def setUp(self):
        self.service = TwoFactorService()

    def test_encrypt_secret(self):
        """测试加密密钥"""
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = self.service._encrypt_secret(secret)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, secret)
        self.assertTrue(len(encrypted) > 0)

    def test_decrypt_secret(self):
        """测试解密密钥"""
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = self.service._encrypt_secret(secret)
        decrypted = self.service._decrypt_secret(encrypted)
        self.assertEqual(decrypted, secret)

    def test_encrypt_decrypt_roundtrip(self):
        """测试加密解密往返"""
        original = "TEST123SECRET456"
        encrypted = self.service._encrypt_secret(original)
        decrypted = self.service._decrypt_secret(encrypted)
        self.assertEqual(original, decrypted)

    def test_decrypt_invalid_token(self):
        """测试解密无效token"""
        from cryptography.fernet import InvalidToken

        with self.assertRaises(InvalidToken):
            self.service._decrypt_secret("invalid_encrypted_data")


class TestTOTPGeneration(unittest.TestCase):
    """测试TOTP生成功能"""

    def setUp(self):
        self.service = TwoFactorService()

    def test_generate_totp_secret(self):
        """测试生成TOTP密钥"""
        secret = self.service.generate_totp_secret()
        self.assertIsInstance(secret, str)
        self.assertEqual(len(secret), 32)  # pyotp默认32字符
        # 验证是base32编码
        import base64

        try:
            base64.b32decode(secret)
        except Exception:
            self.fail("生成的密钥不是有效的base32编码")

    def test_generate_totp_secret_unique(self):
        """测试每次生成的密钥都不同"""
        secret1 = self.service.generate_totp_secret()
        secret2 = self.service.generate_totp_secret()
        self.assertNotEqual(secret1, secret2)


class TestQRCodeGeneration(unittest.TestCase):
    """测试QR码生成"""

    def setUp(self):
        self.service = TwoFactorService()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.email = "test@example.com"

    def test_generate_qr_code(self):
        """测试生成QR码"""
        secret = self.service.generate_totp_secret()
        qr_code = self.service.generate_qr_code(self.mock_user, secret)

        self.assertIsInstance(qr_code, bytes)
        self.assertTrue(len(qr_code) > 0)
        # 验证是PNG格式
        self.assertTrue(qr_code.startswith(b"\x89PNG"))

    def test_generate_qr_code_custom_issuer(self):
        """测试自定义发行者名称"""
        secret = self.service.generate_totp_secret()
        qr_code = self.service.generate_qr_code(self.mock_user, secret, issuer_name="测试系统")
        self.assertIsInstance(qr_code, bytes)
        self.assertTrue(len(qr_code) > 0)

    def test_generate_qr_code_no_email(self):
        """测试无邮箱时使用用户名"""
        self.mock_user.email = None
        secret = self.service.generate_totp_secret()
        qr_code = self.service.generate_qr_code(self.mock_user, secret)
        self.assertIsInstance(qr_code, bytes)


class TestTOTPVerification(unittest.TestCase):
    """测试TOTP验证"""

    def setUp(self):
        self.service = TwoFactorService()
        self.secret = self.service.generate_totp_secret()

    def test_verify_totp_code_valid(self):
        """测试验证有效的TOTP码"""
        import pyotp

        totp = pyotp.TOTP(self.secret)
        code = totp.now()

        result = self.service.verify_totp_code(self.secret, code)
        self.assertTrue(result)

    def test_verify_totp_code_invalid(self):
        """测试验证无效的TOTP码"""
        result = self.service.verify_totp_code(self.secret, "000000")
        self.assertFalse(result)

    def test_verify_totp_code_with_window(self):
        """测试时间窗口验证"""
        import pyotp

        totp = pyotp.TOTP(self.secret)
        code = totp.now()

        # 使用更大的窗口
        result = self.service.verify_totp_code(self.secret, code, window=2)
        self.assertTrue(result)


class TestSetup2FA(unittest.TestCase):
    """测试设置2FA"""

    def setUp(self):
        self.service = TwoFactorService()
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.email = "test@example.com"

    def test_setup_2fa_for_user(self):
        """测试为用户设置2FA"""
        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value.delete.return_value = None
        self.mock_db.query.return_value = mock_query

        secret, qr_code = self.service.setup_2fa_for_user(self.mock_db, self.mock_user)

        # 验证返回值
        self.assertIsInstance(secret, str)
        self.assertEqual(len(secret), 32)
        self.assertIsInstance(qr_code, bytes)

        # 验证数据库操作
        self.mock_db.query.assert_called()
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_setup_2fa_removes_old_config(self):
        """测试设置2FA时删除旧配置"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query

        self.service.setup_2fa_for_user(self.mock_db, self.mock_user)

        # 验证删除操作被调用
        mock_filter.delete.assert_called_once()


class TestEnable2FA(unittest.TestCase):
    """测试启用2FA"""

    def setUp(self):
        self.service = TwoFactorService()
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.two_factor_enabled = False

    def test_enable_2fa_success(self):
        """测试成功启用2FA"""
        # 生成有效的TOTP码
        secret = self.service.generate_totp_secret()
        encrypted_secret = self.service._encrypt_secret(secret)

        import pyotp

        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        # Mock数据库查询 - TOTP密钥
        mock_secret_record = MagicMock()
        mock_secret_record.secret_encrypted = encrypted_secret

        mock_query_totp = MagicMock()
        mock_query_totp.filter.return_value.first.return_value = mock_secret_record

        # Mock数据库查询 - 备用码（删除旧的）
        mock_query_backup = MagicMock()
        mock_query_backup.filter.return_value.delete.return_value = None

        def query_side_effect(model):
            if "User2FASecret" in str(model):
                return mock_query_totp
            else:  # User2FABackupCode
                return mock_query_backup

        self.mock_db.query.side_effect = query_side_effect

        # 执行
        success, message, backup_codes = self.service.enable_2fa_for_user(
            self.mock_db, self.mock_user, valid_code
        )

        # 验证
        self.assertTrue(success)
        self.assertEqual(message, "2FA已启用")
        self.assertIsNotNone(backup_codes)
        self.assertEqual(len(backup_codes), 10)
        self.assertTrue(self.mock_user.two_factor_enabled)
        self.assertEqual(self.mock_user.two_factor_method, "totp")

    def test_enable_2fa_no_secret_record(self):
        """测试未找到TOTP密钥"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        success, message, backup_codes = self.service.enable_2fa_for_user(
            self.mock_db, self.mock_user, "123456"
        )

        self.assertFalse(success)
        self.assertEqual(message, "未找到2FA配置，请先获取二维码")
        self.assertIsNone(backup_codes)

    def test_enable_2fa_invalid_code(self):
        """测试验证码错误"""
        secret = self.service.generate_totp_secret()
        encrypted_secret = self.service._encrypt_secret(secret)

        mock_secret_record = MagicMock()
        mock_secret_record.secret_encrypted = encrypted_secret

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_secret_record
        self.mock_db.query.return_value = mock_query

        success, message, backup_codes = self.service.enable_2fa_for_user(
            self.mock_db, self.mock_user, "000000"
        )

        self.assertFalse(success)
        self.assertEqual(message, "验证码错误，请检查时间同步")
        self.assertIsNone(backup_codes)


class TestDisable2FA(unittest.TestCase):
    """测试禁用2FA"""

    def setUp(self):
        self.service = TwoFactorService()
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.password_hash = "$2b$12$xyz"  # mock hash
        self.mock_user.two_factor_enabled = True

    @patch("app.services.two_factor_service.verify_password")
    def test_disable_2fa_success(self, mock_verify_password):
        """测试成功禁用2FA"""
        mock_verify_password.return_value = True

        mock_query = MagicMock()
        mock_query.filter.return_value.delete.return_value = None
        self.mock_db.query.return_value = mock_query

        success, message = self.service.disable_2fa_for_user(
            self.mock_db, self.mock_user, "correct_password"
        )

        self.assertTrue(success)
        self.assertEqual(message, "2FA已禁用")
        self.assertFalse(self.mock_user.two_factor_enabled)
        self.assertIsNone(self.mock_user.two_factor_method)
        self.assertIsNone(self.mock_user.two_factor_verified_at)

    @patch("app.services.two_factor_service.verify_password")
    def test_disable_2fa_wrong_password(self, mock_verify_password):
        """测试密码错误"""
        mock_verify_password.return_value = False

        success, message = self.service.disable_2fa_for_user(
            self.mock_db, self.mock_user, "wrong_password"
        )

        self.assertFalse(success)
        self.assertEqual(message, "密码错误")


class TestVerify2FACode(unittest.TestCase):
    """测试验证2FA码"""

    def setUp(self):
        self.service = TwoFactorService()
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.two_factor_enabled = True

    def test_verify_2fa_not_enabled(self):
        """测试未启用2FA"""
        self.mock_user.two_factor_enabled = False

        success, message = self.service.verify_2fa_code(self.mock_db, self.mock_user, "123456")

        self.assertFalse(success)
        self.assertEqual(message, "未启用2FA")

    def test_verify_2fa_totp_success(self):
        """测试TOTP验证成功"""
        secret = self.service.generate_totp_secret()
        encrypted_secret = self.service._encrypt_secret(secret)

        import pyotp

        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        mock_secret_record = MagicMock()
        mock_secret_record.secret_encrypted = encrypted_secret

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_secret_record
        self.mock_db.query.return_value = mock_query

        success, message = self.service.verify_2fa_code(self.mock_db, self.mock_user, valid_code)

        self.assertTrue(success)
        self.assertEqual(message, "验证成功")

    def test_verify_2fa_invalid_code(self):
        """测试验证码错误"""
        secret = self.service.generate_totp_secret()
        encrypted_secret = self.service._encrypt_secret(secret)

        mock_secret_record = MagicMock()
        mock_secret_record.secret_encrypted = encrypted_secret

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_secret_record
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        success, message = self.service.verify_2fa_code(self.mock_db, self.mock_user, "000000")

        self.assertFalse(success)
        self.assertEqual(message, "验证码错误")


class TestBackupCodes(unittest.TestCase):
    """测试备用码功能"""

    def setUp(self):
        self.service = TwoFactorService()
        self.mock_db = MagicMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"

    def test_generate_backup_codes(self):
        """测试生成备用码"""
        mock_query = MagicMock()
        mock_query.filter.return_value.delete.return_value = None
        self.mock_db.query.return_value = mock_query

        backup_codes = self.service._generate_backup_codes(self.mock_db, self.mock_user)

        self.assertEqual(len(backup_codes), 10)
        for code in backup_codes:
            self.assertIsInstance(code, str)
            self.assertEqual(len(code), 8)
            self.assertTrue(code.isdigit())

    def test_generate_backup_codes_custom_count(self):
        """测试自定义数量生成备用码"""
        mock_query = MagicMock()
        mock_query.filter.return_value.delete.return_value = None
        self.mock_db.query.return_value = mock_query

        backup_codes = self.service._generate_backup_codes(self.mock_db, self.mock_user, count=5)

        self.assertEqual(len(backup_codes), 5)

    @patch("app.services.two_factor_service.verify_password")
    def test_verify_backup_code_success(self, mock_verify_password):
        """测试验证备用码成功"""
        mock_verify_password.return_value = True

        mock_backup_code = MagicMock()
        mock_backup_code.code_hash = "hashed_code"
        mock_backup_code.used = False

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_backup_code]
        self.mock_db.query.return_value = mock_query

        success, message = self.service._verify_backup_code(
            self.mock_db, self.mock_user, "12345678", "192.168.1.1"
        )

        self.assertTrue(success)
        self.assertEqual(message, "备用码验证成功")
        self.assertTrue(mock_backup_code.used)
        self.assertIsNotNone(mock_backup_code.used_at)
        self.assertEqual(mock_backup_code.used_ip, "192.168.1.1")

    @patch("app.services.two_factor_service.verify_password")
    def test_verify_backup_code_invalid(self, mock_verify_password):
        """测试验证无效备用码"""
        mock_verify_password.return_value = False

        mock_backup_code = MagicMock()
        mock_backup_code.code_hash = "hashed_code"

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_backup_code]
        self.mock_db.query.return_value = mock_query

        success, message = self.service._verify_backup_code(
            self.mock_db, self.mock_user, "wrong_code"
        )

        self.assertFalse(success)
        self.assertEqual(message, "备用码无效或已使用")

    def test_verify_backup_code_no_codes(self):
        """测试没有可用备用码"""
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        success, message = self.service._verify_backup_code(
            self.mock_db, self.mock_user, "12345678"
        )

        self.assertFalse(success)
        self.assertEqual(message, "备用码无效或已使用")

    def test_get_backup_codes_info(self):
        """测试获取备用码信息"""
        mock_query_total = MagicMock()
        mock_query_total.filter.return_value.count.return_value = 10

        mock_query_unused = MagicMock()
        mock_query_unused.filter.return_value.count.return_value = 7

        def query_side_effect(model):
            # 第一次调用返回total，第二次返回unused
            if not hasattr(query_side_effect, "call_count"):
                query_side_effect.call_count = 0
            query_side_effect.call_count += 1

            if query_side_effect.call_count == 1:
                return mock_query_total
            else:
                return mock_query_unused

        self.mock_db.query.side_effect = query_side_effect

        info = self.service.get_backup_codes_info(self.mock_db, self.mock_user)

        self.assertEqual(info["total"], 10)
        self.assertEqual(info["unused"], 7)
        self.assertEqual(info["used"], 3)

    @patch("app.services.two_factor_service.verify_password")
    def test_regenerate_backup_codes_success(self, mock_verify_password):
        """测试重新生成备用码成功"""
        self.mock_user.two_factor_enabled = True
        mock_verify_password.return_value = True

        mock_query = MagicMock()
        mock_query.filter.return_value.delete.return_value = None
        self.mock_db.query.return_value = mock_query

        success, message, backup_codes = self.service.regenerate_backup_codes(
            self.mock_db, self.mock_user, "correct_password"
        )

        self.assertTrue(success)
        self.assertEqual(message, "备用码已重新生成")
        self.assertIsNotNone(backup_codes)
        self.assertEqual(len(backup_codes), 10)

    @patch("app.services.two_factor_service.verify_password")
    def test_regenerate_backup_codes_not_enabled(self, mock_verify_password):
        """测试未启用2FA时重新生成备用码"""
        self.mock_user.two_factor_enabled = False

        success, message, backup_codes = self.service.regenerate_backup_codes(
            self.mock_db, self.mock_user, "password"
        )

        self.assertFalse(success)
        self.assertEqual(message, "未启用2FA")
        self.assertIsNone(backup_codes)

    @patch("app.services.two_factor_service.verify_password")
    def test_regenerate_backup_codes_wrong_password(self, mock_verify_password):
        """测试密码错误时重新生成备用码"""
        self.mock_user.two_factor_enabled = True
        mock_verify_password.return_value = False

        success, message, backup_codes = self.service.regenerate_backup_codes(
            self.mock_db, self.mock_user, "wrong_password"
        )

        self.assertFalse(success)
        self.assertEqual(message, "密码错误")
        self.assertIsNone(backup_codes)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.service = TwoFactorService()

    def test_empty_secret_encryption(self):
        """测试加密空字符串"""
        encrypted = self.service._encrypt_secret("")
        decrypted = self.service._decrypt_secret(encrypted)
        self.assertEqual(decrypted, "")

    def test_special_characters_encryption(self):
        """测试加密特殊字符"""
        secret = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        encrypted = self.service._encrypt_secret(secret)
        decrypted = self.service._decrypt_secret(encrypted)
        self.assertEqual(decrypted, secret)

    def test_unicode_encryption(self):
        """测试加密Unicode字符"""
        secret = "密钥🔐测试"
        encrypted = self.service._encrypt_secret(secret)
        decrypted = self.service._decrypt_secret(encrypted)
        self.assertEqual(decrypted, secret)


if __name__ == "__main__":
    unittest.main()
