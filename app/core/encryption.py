"""
数据加密服务

使用 AES-256-GCM 算法加密敏感数据字段
"""

import os
import base64
import logging
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

logger = logging.getLogger(__name__)


class DataEncryption:
    """数据加密服务
    
    使用 AES-256-GCM 算法提供数据加密和解密功能
    - 自动生成随机 IV（初始化向量）
    - 支持认证标签（防篡改）
    - 密钥独立管理
    """
    
    def __init__(self):
        """初始化加密服务"""
        # 从环境变量加载加密密钥（32字节 = 256位）
        key_b64 = os.getenv("DATA_ENCRYPTION_KEY")
        
        if not key_b64:
            if settings.DEBUG:
                # 开发环境生成临时密钥
                self.key = AESGCM.generate_key(bit_length=256)
                logger.warning("⚠️  使用临时数据加密密钥（仅开发环境）")
            else:
                raise ValueError(
                    "❌ 生产环境必须设置 DATA_ENCRYPTION_KEY 环境变量！\n"
                    "请运行: python scripts/generate_encryption_key.py"
                )
        else:
            try:
                self.key = base64.urlsafe_b64decode(key_b64)
                logger.info("✅ 数据加密密钥加载成功")
            except Exception as e:
                raise ValueError(f"❌ 数据加密密钥格式错误: {e}")
        
        # 初始化 AES-GCM 加密器
        self.cipher = AESGCM(self.key)
    
    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        """
        加密数据
        
        Args:
            plaintext: 明文字符串
        
        Returns:
            加密后的Base64字符串（包含IV和密文）
            如果输入为空，则返回原值
        
        Example:
            >>> encryption = DataEncryption()
            >>> encrypted = encryption.encrypt("421002199001011234")
            >>> print(encrypted)
            'gAAAAABl...'  # Base64 编码的加密数据
        """
        if not plaintext:
            return plaintext
        
        try:
            # 生成随机IV（96位 = 12字节）
            iv = os.urandom(12)
            
            # 加密（AES-256-GCM）
            ciphertext = self.cipher.encrypt(
                iv,
                plaintext.encode('utf-8'),
                None  # 关联数据（可选，用于额外的认证数据）
            )
            
            # 组合 IV + 密文
            encrypted = iv + ciphertext
            
            # Base64编码（URL安全）
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        
        except Exception as e:
            logger.error(f"❌ 加密失败: {e}")
            raise ValueError(f"数据加密失败: {e}")
    
    def decrypt(self, ciphertext_b64: Optional[str]) -> Optional[str]:
        """
        解密数据
        
        Args:
            ciphertext_b64: 加密后的Base64字符串
        
        Returns:
            解密后的明文字符串
            如果输入为空，则返回原值
            如果解密失败，返回 "[解密失败]"
        
        Example:
            >>> encryption = DataEncryption()
            >>> decrypted = encryption.decrypt("gAAAAABl...")
            >>> print(decrypted)
            '421002199001011234'
        """
        if not ciphertext_b64:
            return ciphertext_b64
        
        try:
            # Base64解码
            encrypted = base64.urlsafe_b64decode(ciphertext_b64)
            
            # 分离 IV 和密文
            iv = encrypted[:12]
            ciphertext = encrypted[12:]
            
            # 解密
            plaintext_bytes = self.cipher.decrypt(iv, ciphertext, None)
            
            return plaintext_bytes.decode('utf-8')
        
        except Exception as e:
            logger.error(f"❌ 解密失败: {e}")
            return "[解密失败]"
    
    @staticmethod
    def generate_key() -> str:
        """
        生成新的加密密钥（Base64编码）
        
        Returns:
            Base64编码的256位加密密钥
        
        Example:
            >>> key = DataEncryption.generate_key()
            >>> print(key)
            'abc123...'  # 44字符的Base64字符串
        """
        key = AESGCM.generate_key(bit_length=256)
        return base64.urlsafe_b64encode(key).decode('utf-8')


# 全局加密实例（单例模式）
data_encryption = DataEncryption()
