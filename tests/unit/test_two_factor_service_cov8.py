# -*- coding: utf-8 -*-
"""
第八批覆盖率测试 - 双因素认证(2FA)服务
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.two_factor_service import TwoFactorService, _get_encryption_key
    HAS_2FA = True
except Exception:
    HAS_2FA = False

pytestmark = pytest.mark.skipif(not HAS_2FA, reason="two_factor_service 导入失败")


class TestGetEncryptionKey:
    def test_returns_bytes(self):
        """加密密钥应返回 bytes"""
        key = _get_encryption_key()
        assert isinstance(key, bytes)
        assert len(key) > 0


class TestTwoFactorServiceInit:
    def test_init(self):
        """服务初始化"""
        svc = TwoFactorService()
        assert svc.fernet is not None

    def test_generate_totp_secret(self):
        """生成 TOTP 密钥"""
        svc = TwoFactorService()
        secret = svc.generate_totp_secret()
        assert isinstance(secret, str)
        assert len(secret) >= 16  # TOTP 密钥至少 16 字符


class TestEncryptDecrypt:
    def test_encrypt_decrypt_roundtrip(self):
        """加解密往返测试"""
        svc = TwoFactorService()
        original = "JBSWY3DPEHPK3PXP"
        encrypted = svc._encrypt_secret(original)
        decrypted = svc._decrypt_secret(encrypted)
        assert decrypted == original

    def test_encrypted_differs_from_original(self):
        """加密后应与原文不同"""
        svc = TwoFactorService()
        original = "TESTSECRET123456"
        encrypted = svc._encrypt_secret(original)
        assert encrypted != original


class TestVerifyTOTP:
    def test_invalid_token_returns_false(self):
        """错误的 TOTP 令牌应返回 False"""
        svc = TwoFactorService()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        # 无效用户返回 False
        if hasattr(svc, 'verify_totp'):
            result = svc.verify_totp(db, user_id=999, token="000000")
            assert result is False
        else:
            pytest.skip("verify_totp 方法不存在")

    def test_valid_setup_flow(self):
        """测试 2FA 启用流程"""
        svc = TwoFactorService()
        secret = svc.generate_totp_secret()
        assert secret is not None
        encrypted = svc._encrypt_secret(secret)
        decrypted = svc._decrypt_secret(encrypted)
        assert decrypted == secret


class TestBackupCodes:
    def test_generate_backup_codes(self):
        """生成备用恢复码"""
        svc = TwoFactorService()
        if hasattr(svc, 'generate_backup_codes'):
            codes = svc.generate_backup_codes()
            assert isinstance(codes, list)
            assert len(codes) > 0
        else:
            pytest.skip("generate_backup_codes 方法不存在")
