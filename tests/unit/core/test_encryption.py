# -*- coding: utf-8 -*-
"""
加密模块测试
"""

import base64
import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.encryption import DataEncryption, data_encryption


class TestDataEncryptionInit:
    """测试数据加密类初始化"""

    @patch.dict(
        os.environ,
        {
            "DATA_ENCRYPTION_KEY": base64.urlsafe_b64encode(
                AESGCM.generate_key(bit_length=256)
            ).decode()
        },
    )
    def test_init_with_env_key(self):
        """测试使用环境变量密钥初始化"""
        encryptor = DataEncryption()
        assert encryptor.key is not None
        assert len(encryptor.key) == 32  # 256 bits = 32 bytes
        assert encryptor.cipher is not None

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_init_debug_mode_no_key(self, mock_settings):
        """测试调试模式下无密钥时生成临时密钥"""
        mock_settings.DEBUG = True

        encryptor = DataEncryption()

        assert encryptor.key is not None
        assert len(encryptor.key) == 32

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_init_prod_mode_no_key_raises_error(self, mock_settings):
        """测试生产模式下无密钥时抛出错误"""
        mock_settings.DEBUG = False

        with pytest.raises(ValueError) as exc_info:
            DataEncryption()

        assert "DATA_ENCRYPTION_KEY" in str(exc_info.value)

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": "invalid_base64!!!"})
    def test_init_invalid_key_format(self):
        """测试无效的密钥格式"""
        with pytest.raises(ValueError) as exc_info:
            DataEncryption()

        assert "密钥格式错误" in str(exc_info.value)


class TestDataEncryptionEncrypt:
    """测试加密方法"""

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_encrypt_string(self, mock_settings):
        """测试加密字符串"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()
        plaintext = "sensitive data"

        encrypted = encryptor.encrypt(plaintext)

        assert encrypted is not None
        assert encrypted != plaintext
        assert isinstance(encrypted, str)
        # 验证是 Base64 编码
        try:
            base64.urlsafe_b64decode(encrypted)
        except:
            pytest.fail("Encrypted data is not valid Base64")

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_encrypt_none(self, mock_settings):
        """测试加密 None 值"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()

        result = encryptor.encrypt(None)

        assert result is None

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_encrypt_empty_string(self, mock_settings):
        """测试加密空字符串"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()

        result = encryptor.encrypt("")

        assert result == ""

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_encrypt_unicode(self, mock_settings):
        """测试加密 Unicode 字符"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()
        plaintext = "敏感数据 🔒"

        encrypted = encryptor.encrypt(plaintext)

        assert encrypted is not None
        assert encrypted != plaintext


class TestDataEncryptionDecrypt:
    """测试解密方法"""

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_decrypt_string(self, mock_settings):
        """测试解密字符串"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()
        plaintext = "sensitive data"

        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_decrypt_none(self, mock_settings):
        """测试解密 None 值"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()

        result = encryptor.decrypt(None)

        assert result is None

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_decrypt_empty_string(self, mock_settings):
        """测试解密空字符串"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()

        result = encryptor.decrypt("")

        assert result == ""

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_decrypt_invalid_data(self, mock_settings):
        """测试解密无效数据"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()

        result = encryptor.decrypt("invalid_encrypted_data")

        assert result == "[解密失败]"

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_decrypt_unicode(self, mock_settings):
        """测试解密 Unicode 字符"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()
        plaintext = "敏感数据 🔒"

        encrypted = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted)

        assert decrypted == plaintext

    @patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": ""}, clear=True)
    @patch("app.core.encryption.settings")
    def test_encrypt_decrypt_cycle(self, mock_settings):
        """测试加密解密循环"""
        mock_settings.DEBUG = True
        encryptor = DataEncryption()

        test_data = [
            "421002199001011234",  # 身份证号
            "13800138000",  # 手机号
            "test@example.com",  # 邮箱
            "Hello World 123",  # 普通文本
            "中文测试数据",  # 中文
        ]

        for plaintext in test_data:
            encrypted = encryptor.encrypt(plaintext)
            decrypted = encryptor.decrypt(encrypted)
            assert decrypted == plaintext, f"Failed for: {plaintext}"


class TestDataEncryptionGenerateKey:
    """测试密钥生成方法"""

    def test_generate_key(self):
        """测试生成密钥"""
        key = DataEncryption.generate_key()

        assert isinstance(key, str)
        assert len(key) > 0

        # 验证是有效的 Base64
        try:
            decoded = base64.urlsafe_b64decode(key)
            assert len(decoded) == 32  # 256 bits
        except:
            pytest.fail("Generated key is not valid Base64")

    def test_generate_unique_keys(self):
        """测试生成的密钥是唯一的"""
        key1 = DataEncryption.generate_key()
        key2 = DataEncryption.generate_key()

        assert key1 != key2

    def test_generated_key_works(self):
        """测试生成的密钥可用于加密"""
        key = DataEncryption.generate_key()

        # 设置环境变量并创建加密器
        with patch.dict(os.environ, {"DATA_ENCRYPTION_KEY": key}):
            encryptor = DataEncryption()
            plaintext = "test data"

            encrypted = encryptor.encrypt(plaintext)
            decrypted = encryptor.decrypt(encrypted)

            assert decrypted == plaintext


class TestDataEncryptionGlobalInstance:
    """测试全局加密实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert data_encryption is not None
        assert isinstance(data_encryption, DataEncryption)
