# -*- coding: utf-8 -*-
"""
双因素认证（2FA）服务层

功能：
  1. TOTP密钥生成和验证
  2. QR码生成（支持Google Authenticator / Microsoft Authenticator）
  3. 备用恢复码生成和验证
  4. 加密存储密钥
"""

import base64
import io
import logging
import secrets
from typing import Optional, Tuple, List

import pyotp
import qrcode
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session

from ..core.auth import get_password_hash, verify_password
from ..core.config import settings
from ..models.user import User
from ..models.two_factor import User2FASecret, User2FABackupCode

logger = logging.getLogger(__name__)

# 加密密钥（从配置中获取，或使用SECRET_KEY派生）
def _get_encryption_key() -> bytes:
    """获取加密密钥（从SECRET_KEY派生）"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"2fa_secret_salt_v1",  # 固定盐值（生产环境应使用配置）
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return key


class TwoFactorService:
    """双因素认证服务"""
    
    def __init__(self):
        self.encryption_key = _get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _encrypt_secret(self, secret: str) -> str:
        """加密TOTP密钥"""
        encrypted = self.fernet.encrypt(secret.encode())
        return encrypted.decode()
    
    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """解密TOTP密钥"""
        decrypted = self.fernet.decrypt(encrypted_secret.encode())
        return decrypted.decode()
    
    def generate_totp_secret(self) -> str:
        """生成TOTP密钥（32字符base32编码）"""
        return pyotp.random_base32()
    
    def generate_qr_code(
        self, 
        user: User, 
        secret: str,
        issuer_name: str = "非标项目管理系统"
    ) -> bytes:
        """
        生成TOTP二维码（PNG格式）
        
        Args:
            user: 用户对象
            secret: TOTP密钥
            issuer_name: 发行者名称
        
        Returns:
            PNG图片字节流
        """
        # 生成TOTP URI（兼容Google Authenticator / Microsoft Authenticator）
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.email or user.username,
            issuer_name=issuer_name
        )
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为字节流
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """
        验证TOTP码
        
        Args:
            secret: TOTP密钥
            code: 用户输入的6位数字
            window: 时间窗口（允许前后N个时间段的码，默认1=前后30秒）
        
        Returns:
            验证是否通过
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    
    def enable_2fa_for_user(
        self,
        db: Session,
        user: User,
        totp_code: str
    ) -> Tuple[bool, str, Optional[List[str]]]:
        """
        为用户启用2FA（验证TOTP码后启用）
        
        Args:
            db: 数据库会话
            user: 用户对象
            totp_code: 用户输入的TOTP验证码
        
        Returns:
            (是否成功, 消息, 备用码列表)
        """
        # 1. 查询用户的TOTP密钥
        secret_record = db.query(User2FASecret).filter(
            User2FASecret.user_id == user.id,
            User2FASecret.method == "totp",
            User2FASecret.is_active == True
        ).first()
        
        if not secret_record:
            return False, "未找到2FA配置，请先获取二维码", None
        
        # 2. 解密密钥
        secret = self._decrypt_secret(secret_record.secret_encrypted)
        
        # 3. 验证TOTP码
        if not self.verify_totp_code(secret, totp_code):
            return False, "验证码错误，请检查时间同步", None
        
        # 4. 生成备用码
        backup_codes = self._generate_backup_codes(db, user)
        
        # 5. 启用2FA
        user.two_factor_enabled = True
        user.two_factor_method = "totp"
        from datetime import datetime
        user.two_factor_verified_at = datetime.now()
        db.commit()
        
        logger.info(f"用户 {user.username} (ID:{user.id}) 已启用2FA")
        return True, "2FA已启用", backup_codes
    
    def disable_2fa_for_user(
        self,
        db: Session,
        user: User,
        password: str
    ) -> Tuple[bool, str]:
        """
        为用户禁用2FA（需要验证密码）
        
        Args:
            db: 数据库会话
            user: 用户对象
            password: 用户密码（用于验证）
        
        Returns:
            (是否成功, 消息)
        """
        # 1. 验证密码
        if not verify_password(password, user.password_hash):
            return False, "密码错误"
        
        # 2. 删除TOTP密钥
        db.query(User2FASecret).filter(User2FASecret.user_id == user.id).delete()
        
        # 3. 删除备用码
        db.query(User2FABackupCode).filter(User2FABackupCode.user_id == user.id).delete()
        
        # 4. 禁用2FA
        user.two_factor_enabled = False
        user.two_factor_method = None
        user.two_factor_verified_at = None
        db.commit()
        
        logger.info(f"用户 {user.username} (ID:{user.id}) 已禁用2FA")
        return True, "2FA已禁用"
    
    def setup_2fa_for_user(
        self,
        db: Session,
        user: User
    ) -> Tuple[str, bytes]:
        """
        为用户设置2FA（生成密钥和二维码）
        
        Args:
            db: 数据库会话
            user: 用户对象
        
        Returns:
            (TOTP密钥明文, QR码PNG字节流)
        """
        # 1. 生成TOTP密钥
        secret = self.generate_totp_secret()
        
        # 2. 加密存储
        encrypted_secret = self._encrypt_secret(secret)
        
        # 3. 删除旧配置（如果存在）
        db.query(User2FASecret).filter(
            User2FASecret.user_id == user.id,
            User2FASecret.method == "totp"
        ).delete()
        
        # 4. 保存新配置
        secret_record = User2FASecret(
            user_id=user.id,
            secret_encrypted=encrypted_secret,
            method="totp",
            is_active=True
        )
        db.add(secret_record)
        db.commit()
        
        # 5. 生成二维码
        qr_code = self.generate_qr_code(user, secret)
        
        logger.info(f"用户 {user.username} (ID:{user.id}) 生成2FA配置")
        return secret, qr_code
    
    def verify_2fa_code(
        self,
        db: Session,
        user: User,
        code: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        验证2FA码（支持TOTP码和备用码）
        
        Args:
            db: 数据库会话
            user: 用户对象
            code: 用户输入的验证码
            ip_address: 用户IP地址
        
        Returns:
            (是否成功, 消息)
        """
        if not user.two_factor_enabled:
            return False, "未启用2FA"
        
        # 1. 尝试验证TOTP码
        secret_record = db.query(User2FASecret).filter(
            User2FASecret.user_id == user.id,
            User2FASecret.method == "totp",
            User2FASecret.is_active == True
        ).first()
        
        if secret_record:
            secret = self._decrypt_secret(secret_record.secret_encrypted)
            if self.verify_totp_code(secret, code):
                logger.info(f"用户 {user.username} (ID:{user.id}) TOTP验证成功")
                return True, "验证成功"
        
        # 2. 尝试验证备用码
        backup_result = self._verify_backup_code(db, user, code, ip_address)
        if backup_result[0]:
            return backup_result
        
        logger.warning(f"用户 {user.username} (ID:{user.id}) 2FA验证失败")
        return False, "验证码错误"
    
    def _generate_backup_codes(
        self,
        db: Session,
        user: User,
        count: int = 10
    ) -> List[str]:
        """
        生成备用恢复码
        
        Args:
            db: 数据库会话
            user: 用户对象
            count: 生成数量（默认10个）
        
        Returns:
            备用码列表（明文）
        """
        # 删除旧备用码
        db.query(User2FABackupCode).filter(User2FABackupCode.user_id == user.id).delete()
        
        # 生成新备用码
        backup_codes = []
        for _ in range(count):
            # 生成8位数字备用码
            code = "".join([str(secrets.randbelow(10)) for _ in range(8)])
            backup_codes.append(code)
            
            # 哈希存储
            code_hash = get_password_hash(code)
            backup_code_record = User2FABackupCode(
                user_id=user.id,
                code_hash=code_hash,
                used=False
            )
            db.add(backup_code_record)
        
        db.commit()
        logger.info(f"用户 {user.username} (ID:{user.id}) 生成 {count} 个备用码")
        return backup_codes
    
    def _verify_backup_code(
        self,
        db: Session,
        user: User,
        code: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        验证备用码（一次性使用）
        
        Args:
            db: 数据库会话
            user: 用户对象
            code: 备用码
            ip_address: 用户IP地址
        
        Returns:
            (是否成功, 消息)
        """
        # 查询未使用的备用码
        backup_codes = db.query(User2FABackupCode).filter(
            User2FABackupCode.user_id == user.id,
            User2FABackupCode.used == False
        ).all()
        
        for backup_code in backup_codes:
            if verify_password(code, backup_code.code_hash):
                # 标记为已使用
                from datetime import datetime
                backup_code.used = True
                backup_code.used_at = datetime.now()
                backup_code.used_ip = ip_address
                db.commit()
                
                logger.info(f"用户 {user.username} (ID:{user.id}) 使用备用码")
                return True, "备用码验证成功"
        
        return False, "备用码无效或已使用"
    
    def get_backup_codes_info(
        self,
        db: Session,
        user: User
    ) -> dict:
        """
        获取备用码信息
        
        Args:
            db: 数据库会话
            user: 用户对象
        
        Returns:
            备用码统计信息
        """
        total = db.query(User2FABackupCode).filter(
            User2FABackupCode.user_id == user.id
        ).count()
        
        unused = db.query(User2FABackupCode).filter(
            User2FABackupCode.user_id == user.id,
            User2FABackupCode.used == False
        ).count()
        
        return {
            "total": total,
            "unused": unused,
            "used": total - unused
        }
    
    def regenerate_backup_codes(
        self,
        db: Session,
        user: User,
        password: str
    ) -> Tuple[bool, str, Optional[List[str]]]:
        """
        重新生成备用码（需要验证密码）
        
        Args:
            db: 数据库会话
            user: 用户对象
            password: 用户密码
        
        Returns:
            (是否成功, 消息, 新备用码列表)
        """
        if not user.two_factor_enabled:
            return False, "未启用2FA", None
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return False, "密码错误", None
        
        # 生成新备用码
        backup_codes = self._generate_backup_codes(db, user)
        
        logger.info(f"用户 {user.username} (ID:{user.id}) 重新生成备用码")
        return True, "备用码已重新生成", backup_codes


# 单例服务
_two_factor_service = None

def get_two_factor_service() -> TwoFactorService:
    """获取2FA服务单例"""
    global _two_factor_service
    if _two_factor_service is None:
        _two_factor_service = TwoFactorService()
    return _two_factor_service
