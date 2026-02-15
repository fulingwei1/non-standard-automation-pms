# -*- coding: utf-8 -*-
"""
密钥管理器

提供安全的密钥管理机制，支持密钥轮转和多环境管理
"""

import os
import secrets
import base64
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

try:
    # 优先使用 PyJWT
    import jwt
    from jwt.exceptions import JWTError
except ImportError:
    # 回退到 python-jose
    from jose import jwt, JWTError

logger = logging.getLogger(__name__)


class SecretKeyManager:
    """密钥管理器
    
    功能:
    - 生成安全的随机密钥
    - 验证密钥强度
    - 支持密钥轮转
    - 多密钥向后兼容（旧Token验证）
    - 从环境变量或文件加载密钥
    """
    
    def __init__(self):
        self.current_key: Optional[str] = None
        self.old_keys: List[str] = []
        self.rotation_date: Optional[datetime] = None
        self.key_metadata: Dict[str, Any] = {}
        
    def generate_key(self, length: int = 32) -> str:
        """生成新的安全密钥
        
        Args:
            length: 密钥长度（字节数），默认32字节（256位）
            
        Returns:
            Base64 URL安全编码的密钥字符串
        """
        # 生成随机密钥（使用 secrets 模块确保加密安全）
        return secrets.token_urlsafe(length)
    
    def validate_key(self, key: str, min_length: int = 32) -> bool:
        """验证密钥强度
        
        Args:
            key: 待验证的密钥
            min_length: 最小长度要求（字符数）
            
        Returns:
            密钥是否有效
        """
        if not key:
            logger.error("密钥为空")
            return False
            
        if len(key) < min_length:
            logger.warning(f"密钥长度不足{min_length}字符，当前长度: {len(key)}")
            return False
            
        try:
            # 验证Base64编码（添加填充）
            # token_urlsafe 生成的字符串是 Base64 URL-safe 编码
            padding = '=' * (4 - len(key) % 4)
            base64.urlsafe_b64decode(key + padding)
            return True
        except Exception as e:
            logger.error(f"密钥格式无效: {e}")
            return False
    
    def load_keys_from_env(self) -> None:
        """从环境变量加载密钥
        
        环境变量:
        - SECRET_KEY: 当前密钥
        - OLD_SECRET_KEYS: 旧密钥列表（逗号分隔）
        - SECRET_KEY_FILE: 密钥文件路径（Docker Secrets）
        - OLD_SECRET_KEYS_FILE: 旧密钥文件路径
        """
        # 1. 尝试从文件加载（Docker Secrets优先）
        secret_key_file = os.getenv("SECRET_KEY_FILE")
        if secret_key_file and os.path.exists(secret_key_file):
            with open(secret_key_file, 'r') as f:
                self.current_key = f.read().strip()
            logger.info("从文件加载当前密钥成功")
        else:
            # 2. 从环境变量加载
            self.current_key = os.getenv("SECRET_KEY")
        
        # 验证当前密钥
        if not self.current_key:
            from app.core.config import settings
            if settings.DEBUG:
                logger.warning("未设置SECRET_KEY，生成临时密钥（仅用于开发环境）")
                self.current_key = self.generate_key()
            else:
                raise ValueError(
                    "生产环境必须设置SECRET_KEY环境变量或SECRET_KEY_FILE。"
                    "使用 'python scripts/manage_secrets.py generate' 生成安全密钥。"
                )
        
        if not self.validate_key(self.current_key):
            raise ValueError(
                f"当前SECRET_KEY无效（长度: {len(self.current_key)}）。"
                "密钥必须至少32字符且为Base64编码。"
            )
        
        # 加载旧密钥（用于向后兼容）
        old_keys_file = os.getenv("OLD_SECRET_KEYS_FILE")
        if old_keys_file and os.path.exists(old_keys_file):
            with open(old_keys_file, 'r') as f:
                old_keys_str = f.read().strip()
            self.old_keys = [k.strip() for k in old_keys_str.split(",") if k.strip()]
            logger.info(f"从文件加载{len(self.old_keys)}个旧密钥")
        else:
            old_keys_str = os.getenv("OLD_SECRET_KEYS", "")
            if old_keys_str:
                self.old_keys = [k.strip() for k in old_keys_str.split(",") if k.strip()]
        
        # 验证并过滤旧密钥
        valid_old_keys = []
        for key in self.old_keys:
            if self.validate_key(key):
                valid_old_keys.append(key)
            else:
                logger.warning(f"跳过无效的旧密钥（长度: {len(key)}）")
        
        self.old_keys = valid_old_keys
        logger.info(f"已加载 {len(self.old_keys)} 个有效的旧密钥")
    
    def rotate_key(self, new_key: Optional[str] = None) -> Dict[str, Any]:
        """轮转密钥
        
        Args:
            new_key: 新密钥（可选，不提供则自动生成）
        
        Returns:
            轮转结果字典，包含:
            - status: 状态
            - new_key: 新密钥
            - old_key: 旧密钥
            - rotation_date: 轮转时间
            - note: 操作说明
        
        Raises:
            ValueError: 新密钥无效时
        """
        if new_key is None:
            new_key = self.generate_key()
        
        if not self.validate_key(new_key):
            raise ValueError("新密钥无效（长度不足或格式错误）")
        
        # 保存旧密钥（保留最近3个）
        if self.current_key:
            self.old_keys.insert(0, self.current_key)
            # 只保留最近3个旧密钥（约90天的兼容期）
            self.old_keys = self.old_keys[:3]
        
        # 更新当前密钥
        old_key = self.current_key
        self.current_key = new_key
        self.rotation_date = datetime.now()
        
        # 记录元数据
        self.key_metadata = {
            "rotation_date": self.rotation_date.isoformat(),
            "old_keys_count": len(self.old_keys),
            "grace_period_days": 30,  # 旧密钥有效期
        }
        
        logger.info(f"密钥轮转成功，轮转时间: {self.rotation_date}")
        
        return {
            "status": "success",
            "new_key": new_key,
            "old_key": old_key,
            "rotation_date": self.rotation_date.isoformat(),
            "old_keys_count": len(self.old_keys),
            "note": "请更新环境变量 SECRET_KEY 并重启应用。旧密钥将在30天后失效。"
        }
    
    def verify_token_with_fallback(
        self, 
        token: str, 
        algorithms: List[str] = None,
        options: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """验证Token（尝试所有密钥）
        
        先用当前密钥验证，失败后尝试旧密钥（向后兼容）
        
        Args:
            token: JWT token
            algorithms: JWT算法列表，默认["HS256"]
            options: JWT验证选项
        
        Returns:
            解码后的payload，失败返回None
        """
        if algorithms is None:
            algorithms = ["HS256"]
        
        if options is None:
            options = {}
        
        # 1. 先用当前密钥验证
        try:
            payload = jwt.decode(
                token, 
                self.current_key, 
                algorithms=algorithms,
                options=options
            )
            logger.debug("使用当前密钥验证Token成功")
            return payload
        except JWTError as e:
            logger.debug(f"当前密钥验证失败: {e}")
        
        # 2. 用旧密钥验证（向后兼容）
        for idx, old_key in enumerate(self.old_keys):
            try:
                payload = jwt.decode(
                    token, 
                    old_key, 
                    algorithms=algorithms,
                    options=options
                )
                logger.warning(
                    f"使用旧密钥#{idx+1}验证Token成功。"
                    "建议用户重新登录以获取新Token。"
                )
                # 在payload中标记使用了旧密钥
                payload["_used_old_key"] = True
                payload["_old_key_index"] = idx
                return payload
            except JWTError:
                continue
        
        logger.error("所有密钥验证Token失败")
        return None
    
    def get_key_info(self) -> Dict[str, Any]:
        """获取密钥信息（隐藏敏感内容）
        
        Returns:
            密钥信息字典
        """
        return {
            "current_key_length": len(self.current_key) if self.current_key else 0,
            "current_key_preview": self.current_key[:10] + "..." if self.current_key else None,
            "old_keys_count": len(self.old_keys),
            "rotation_date": self.rotation_date.isoformat() if self.rotation_date else None,
            "metadata": self.key_metadata,
        }
    
    def cleanup_expired_keys(self, grace_period_days: int = 30) -> int:
        """清理过期的旧密钥
        
        Args:
            grace_period_days: 旧密钥保留期（天）
        
        Returns:
            清理的密钥数量
        """
        if not self.rotation_date:
            logger.info("无轮转记录，跳过清理")
            return 0
        
        # 计算过期时间
        expiry_date = self.rotation_date + timedelta(days=grace_period_days)
        
        if datetime.now() < expiry_date:
            logger.info(f"距离过期还有 {(expiry_date - datetime.now()).days} 天，跳过清理")
            return 0
        
        # 清理所有旧密钥
        cleaned_count = len(self.old_keys)
        self.old_keys = []
        
        logger.info(f"清理了 {cleaned_count} 个过期密钥")
        return cleaned_count


# 全局密钥管理器实例
_secret_manager_instance: Optional[SecretKeyManager] = None


def get_secret_manager() -> SecretKeyManager:
    """获取全局密钥管理器实例（单例模式）
    
    Returns:
        SecretKeyManager 实例
    """
    global _secret_manager_instance
    
    if _secret_manager_instance is None:
        _secret_manager_instance = SecretKeyManager()
        _secret_manager_instance.load_keys_from_env()
    
    return _secret_manager_instance


# 向后兼容：导出全局实例
secret_manager = get_secret_manager()
