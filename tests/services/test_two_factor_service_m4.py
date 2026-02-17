# -*- coding: utf-8 -*-
"""TwoFactorService 单元测试（M4组补充） - mock TOTP/SMS验证码"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestTwoFactorServiceCore:
    """TwoFactorService 核心功能测试"""

    def _make_service(self):
        with patch("app.services.two_factor_service._get_encryption_key", return_value=b"A" * 32):
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            with patch("app.services.two_factor_service.Fernet") as mock_fernet_cls:
                from app.services.two_factor_service import TwoFactorService
                svc = TwoFactorService.__new__(TwoFactorService)
                from cryptography.fernet import Fernet as RealFernet
                real_key = RealFernet.generate_key()
                real_fernet = RealFernet(real_key)
                svc.encryption_key = real_key
                svc.fernet = real_fernet
                return svc

    # ---------- TOTP 密钥生成和验证 ----------

    def test_generate_totp_secret_length(self):
        """生成的 TOTP 密钥应为 32 字符 base32 字符串"""
        import pyotp
        with patch("app.services.two_factor_service._get_encryption_key"):
            with patch("app.core.config.settings"):
                from app.services.two_factor_service import TwoFactorService
                svc = TwoFactorService.__new__(TwoFactorService)
                from cryptography.fernet import Fernet as RealFernet
                key = RealFernet.generate_key()
                svc.encryption_key = key
                svc.fernet = RealFernet(key)
                secret = svc.generate_totp_secret()
                assert len(secret) == 32
                # 验证是有效的 base32 字符串（pyotp 能解析）
                totp = pyotp.TOTP(secret)
                code = totp.now()
                assert len(code) == 6

    def test_verify_totp_code_valid(self):
        """当前时间窗口内的 TOTP 码应验证通过"""
        import pyotp
        with patch("app.services.two_factor_service._get_encryption_key"):
            from app.services.two_factor_service import TwoFactorService
            svc = TwoFactorService.__new__(TwoFactorService)
            from cryptography.fernet import Fernet as RealFernet
            key = RealFernet.generate_key()
            svc.encryption_key = key
            svc.fernet = RealFernet(key)

            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            code = totp.now()
            assert svc.verify_totp_code(secret, code) is True

    def test_verify_totp_code_invalid(self):
        """错误的 TOTP 码应返回 False"""
        import pyotp
        with patch("app.services.two_factor_service._get_encryption_key"):
            from app.services.two_factor_service import TwoFactorService
            svc = TwoFactorService.__new__(TwoFactorService)
            from cryptography.fernet import Fernet as RealFernet
            key = RealFernet.generate_key()
            svc.encryption_key = key
            svc.fernet = RealFernet(key)

            secret = pyotp.random_base32()
            assert svc.verify_totp_code(secret, "000000") is False

    # ---------- 加密/解密 ----------

    def test_encrypt_decrypt_roundtrip(self):
        """加密后再解密应恢复原始字符串"""
        from app.services.two_factor_service import TwoFactorService
        from cryptography.fernet import Fernet as RealFernet
        svc = TwoFactorService.__new__(TwoFactorService)
        key = RealFernet.generate_key()
        svc.encryption_key = key
        svc.fernet = RealFernet(key)

        original = "JBSWY3DPEHPK3PXP"
        encrypted = svc._encrypt_secret(original)
        assert encrypted != original
        assert svc._decrypt_secret(encrypted) == original

    # ---------- disable_2fa ----------

    def test_disable_2fa_wrong_password(self):
        """密码错误时禁用 2FA 失败"""
        from app.services.two_factor_service import TwoFactorService
        from cryptography.fernet import Fernet as RealFernet

        with patch("app.services.two_factor_service.verify_password", return_value=False):
            svc = TwoFactorService.__new__(TwoFactorService)
            key = RealFernet.generate_key()
            svc.encryption_key = key
            svc.fernet = RealFernet(key)

            db = MagicMock()
            user = MagicMock(username="test", id=1, password_hash="hashed")
            success, msg = svc.disable_2fa_for_user(db, user, "wrong_password")
            assert success is False
            assert "密码错误" in msg

    def test_disable_2fa_correct_password(self):
        """密码正确时禁用 2FA 成功"""
        from app.services.two_factor_service import TwoFactorService
        from cryptography.fernet import Fernet as RealFernet

        with patch("app.services.two_factor_service.verify_password", return_value=True):
            svc = TwoFactorService.__new__(TwoFactorService)
            key = RealFernet.generate_key()
            svc.encryption_key = key
            svc.fernet = RealFernet(key)

            db = MagicMock()
            db.query.return_value.filter.return_value.delete.return_value = None
            user = MagicMock(username="test", id=1, password_hash="hashed",
                             two_factor_enabled=True, two_factor_method="totp")
            success, msg = svc.disable_2fa_for_user(db, user, "correct_password")
            assert success is True
            assert user.two_factor_enabled is False

    # ---------- get_backup_codes_info ----------

    def test_get_backup_codes_info(self):
        """备用码信息应返回 total/unused/used"""
        from app.services.two_factor_service import TwoFactorService
        from cryptography.fernet import Fernet as RealFernet

        svc = TwoFactorService.__new__(TwoFactorService)
        key = RealFernet.generate_key()
        svc.encryption_key = key
        svc.fernet = RealFernet(key)

        db = MagicMock()
        db.query.return_value.filter.return_value.count.side_effect = [10, 7]
        user = MagicMock(id=1)
        info = svc.get_backup_codes_info(db, user)
        assert info["total"] == 10
        assert info["unused"] == 7
        assert info["used"] == 3

    # ---------- verify_2fa_code: 未启用 ----------

    def test_verify_2fa_not_enabled(self):
        """未启用 2FA 时验证应失败并给出提示"""
        from app.services.two_factor_service import TwoFactorService
        from cryptography.fernet import Fernet as RealFernet

        svc = TwoFactorService.__new__(TwoFactorService)
        key = RealFernet.generate_key()
        svc.encryption_key = key
        svc.fernet = RealFernet(key)

        db = MagicMock()
        user = MagicMock(two_factor_enabled=False)
        success, msg = svc.verify_2fa_code(db, user, "123456")
        assert success is False
        assert "未启用" in msg
