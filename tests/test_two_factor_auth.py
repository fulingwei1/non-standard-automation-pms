# -*- coding: utf-8 -*-
"""
双因素认证（2FA）测试

测试覆盖：
  1. TOTP密钥生成和加密存储
  2. QR码生成
  3. TOTP验证码验证
  4. 2FA启用和禁用流程
  5. 备用码生成和使用
  6. 登录流程集成2FA
  7. API端点测试
"""

import base64
import io
import pytest
from datetime import datetime, timedelta
from PIL import Image
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash, verify_password
from app.models.user import User
from app.models.two_factor import User2FASecret, User2FABackupCode
from app.services.two_factor_service import TwoFactorService, get_two_factor_service


class TestTwoFactorService:
    """2FA服务层测试"""
    
    def test_generate_totp_secret(self):
        """测试生成TOTP密钥"""
        service = TwoFactorService()
        secret = service.generate_totp_secret()
        
        assert len(secret) == 32  # Base32编码，32字符
        assert secret.isalnum()  # 仅包含字母和数字
    
    def test_encrypt_decrypt_secret(self):
        """测试密钥加密和解密"""
        service = TwoFactorService()
        secret = "JBSWY3DPEHPK3PXP"
        
        # 加密
        encrypted = service._encrypt_secret(secret)
        assert encrypted != secret
        
        # 解密
        decrypted = service._decrypt_secret(encrypted)
        assert decrypted == secret
    
    def test_generate_qr_code(self, db: Session):
        """测试生成QR码"""
        service = TwoFactorService()
        
        # 创建测试用户
        user = User(
            username="test_qr",
            email="test_qr@example.com",
            password_hash=get_password_hash("password"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        # 生成QR码
        secret = "JBSWY3DPEHPK3PXP"
        qr_png = service.generate_qr_code(user, secret)
        
        # 验证PNG格式
        assert qr_png.startswith(b'\x89PNG')
        
        # 验证可以被PIL解析
        img = Image.open(io.BytesIO(qr_png))
        assert img.format == 'PNG'
        assert img.size[0] > 0 and img.size[1] > 0
    
    def test_verify_totp_code(self):
        """测试验证TOTP码"""
        import pyotp
        service = TwoFactorService()
        secret = "JBSWY3DPEHPK3PXP"
        
        # 生成当前时间的TOTP码
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # 验证应该成功
        assert service.verify_totp_code(secret, code) is True
        
        # 错误的码应该失败
        assert service.verify_totp_code(secret, "000000") is False
    
    def test_setup_2fa_for_user(self, db: Session):
        """测试为用户设置2FA"""
        service = TwoFactorService()
        
        # 创建测试用户
        user = User(
            username="test_setup",
            email="test_setup@example.com",
            password_hash=get_password_hash("password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        # 设置2FA
        secret, qr_code = service.setup_2fa_for_user(db, user)
        
        # 验证返回值
        assert len(secret) == 32
        assert qr_code.startswith(b'\x89PNG')
        
        # 验证数据库记录
        secret_record = db.query(User2FASecret).filter(
            User2FASecret.user_id == user.id
        ).first()
        assert secret_record is not None
        assert secret_record.method == "totp"
        assert secret_record.is_active is True
        
        # 验证可以解密
        decrypted = service._decrypt_secret(secret_record.secret_encrypted)
        assert decrypted == secret
    
    def test_enable_2fa_for_user_success(self, db: Session):
        """测试启用2FA（成功）"""
        import pyotp
        service = TwoFactorService()
        
        # 创建测试用户并设置2FA
        user = User(
            username="test_enable",
            email="test_enable@example.com",
            password_hash=get_password_hash("password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        secret, _ = service.setup_2fa_for_user(db, user)
        
        # 生成正确的TOTP码
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # 启用2FA
        success, message, backup_codes = service.enable_2fa_for_user(db, user, code)
        
        # 验证结果
        assert success is True
        assert "已启用" in message
        assert backup_codes is not None
        assert len(backup_codes) == 10
        
        # 验证用户状态
        db.refresh(user)
        assert user.two_factor_enabled is True
        assert user.two_factor_method == "totp"
        assert user.two_factor_verified_at is not None
        
        # 验证备用码
        backup_count = db.query(User2FABackupCode).filter(
            User2FABackupCode.user_id == user.id
        ).count()
        assert backup_count == 10
    
    def test_enable_2fa_for_user_wrong_code(self, db: Session):
        """测试启用2FA（错误验证码）"""
        service = TwoFactorService()
        
        # 创建测试用户并设置2FA
        user = User(
            username="test_enable_fail",
            email="test_enable_fail@example.com",
            password_hash=get_password_hash("password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        service.setup_2fa_for_user(db, user)
        
        # 使用错误的TOTP码
        success, message, backup_codes = service.enable_2fa_for_user(db, user, "000000")
        
        # 验证结果
        assert success is False
        assert "错误" in message
        assert backup_codes is None
        
        # 验证用户状态未改变
        db.refresh(user)
        assert user.two_factor_enabled is False
    
    def test_disable_2fa_for_user(self, db: Session):
        """测试禁用2FA"""
        import pyotp
        service = TwoFactorService()
        
        # 创建测试用户并启用2FA
        user = User(
            username="test_disable",
            email="test_disable@example.com",
            password_hash=get_password_hash("test_password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        secret, _ = service.setup_2fa_for_user(db, user)
        totp = pyotp.TOTP(secret)
        service.enable_2fa_for_user(db, user, totp.now())
        
        # 禁用2FA
        success, message = service.disable_2fa_for_user(db, user, "test_password")
        
        # 验证结果
        assert success is True
        assert "已禁用" in message
        
        # 验证用户状态
        db.refresh(user)
        assert user.two_factor_enabled is False
        assert user.two_factor_method is None
        
        # 验证数据已删除
        secret_count = db.query(User2FASecret).filter(
            User2FASecret.user_id == user.id
        ).count()
        assert secret_count == 0
        
        backup_count = db.query(User2FABackupCode).filter(
            User2FABackupCode.user_id == user.id
        ).count()
        assert backup_count == 0
    
    def test_verify_2fa_with_totp_code(self, db: Session):
        """测试使用TOTP码验证2FA"""
        import pyotp
        service = TwoFactorService()
        
        # 创建测试用户并启用2FA
        user = User(
            username="test_verify_totp",
            email="test_verify_totp@example.com",
            password_hash=get_password_hash("password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        secret, _ = service.setup_2fa_for_user(db, user)
        totp = pyotp.TOTP(secret)
        service.enable_2fa_for_user(db, user, totp.now())
        
        # 验证TOTP码
        code = totp.now()
        success, message = service.verify_2fa_code(db, user, code)
        
        assert success is True
        assert "成功" in message
    
    def test_verify_2fa_with_backup_code(self, db: Session):
        """测试使用备用码验证2FA"""
        import pyotp
        service = TwoFactorService()
        
        # 创建测试用户并启用2FA
        user = User(
            username="test_verify_backup",
            email="test_verify_backup@example.com",
            password_hash=get_password_hash("password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        secret, _ = service.setup_2fa_for_user(db, user)
        totp = pyotp.TOTP(secret)
        _, _, backup_codes = service.enable_2fa_for_user(db, user, totp.now())
        
        # 使用第一个备用码
        backup_code = backup_codes[0]
        success, message = service.verify_2fa_code(db, user, backup_code, "127.0.0.1")
        
        assert success is True
        assert "备用码" in message
        
        # 验证备用码已标记为已使用
        backup_record = db.query(User2FABackupCode).filter(
            User2FABackupCode.user_id == user.id,
            User2FABackupCode.used == True
        ).first()
        assert backup_record is not None
        assert backup_record.used_ip == "127.0.0.1"
        
        # 再次使用同一备用码应该失败
        success, message = service.verify_2fa_code(db, user, backup_code)
        assert success is False
    
    def test_get_backup_codes_info(self, db: Session):
        """测试获取备用码信息"""
        import pyotp
        service = TwoFactorService()
        
        # 创建测试用户并启用2FA
        user = User(
            username="test_backup_info",
            email="test_backup_info@example.com",
            password_hash=get_password_hash("password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        secret, _ = service.setup_2fa_for_user(db, user)
        totp = pyotp.TOTP(secret)
        _, _, backup_codes = service.enable_2fa_for_user(db, user, totp.now())
        
        # 使用一个备用码
        service.verify_2fa_code(db, user, backup_codes[0])
        
        # 获取备用码信息
        info = service.get_backup_codes_info(db, user)
        
        assert info["total"] == 10
        assert info["used"] == 1
        assert info["unused"] == 9
    
    def test_regenerate_backup_codes(self, db: Session):
        """测试重新生成备用码"""
        import pyotp
        service = TwoFactorService()
        
        # 创建测试用户并启用2FA
        user = User(
            username="test_regen_backup",
            email="test_regen_backup@example.com",
            password_hash=get_password_hash("test_password"),
            is_active=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        
        secret, _ = service.setup_2fa_for_user(db, user)
        totp = pyotp.TOTP(secret)
        _, _, old_backup_codes = service.enable_2fa_for_user(db, user, totp.now())
        
        # 重新生成备用码
        success, message, new_backup_codes = service.regenerate_backup_codes(
            db, user, "test_password"
        )
        
        assert success is True
        assert new_backup_codes is not None
        assert len(new_backup_codes) == 10
        
        # 验证新旧备用码不同
        assert set(old_backup_codes).isdisjoint(set(new_backup_codes))
        
        # 验证旧备用码已失效
        old_code_works, _ = service.verify_2fa_code(db, user, old_backup_codes[0])
        assert old_code_works is False
        
        # 验证新备用码可用
        new_code_works, _ = service.verify_2fa_code(db, user, new_backup_codes[0])
        assert new_code_works is True


class TestTwoFactorAPI:
    """2FA API端点测试"""
    
    def test_setup_2fa_endpoint(self, client, test_user, auth_headers):
        """测试获取2FA二维码端点"""
        response = client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code_url" in data
        assert data["qr_code_url"].startswith("data:image/png;base64,")
    
    def test_enable_2fa_endpoint(self, client, test_user, auth_headers, db):
        """测试启用2FA端点"""
        import pyotp
        
        # 先获取2FA配置
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers
        )
        secret = setup_response.json()["secret"]
        
        # 生成TOTP码
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # 启用2FA
        response = client.post(
            "/api/v1/auth/2fa/enable",
            headers=auth_headers,
            json={"totp_code": code}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 10
    
    def test_disable_2fa_endpoint(self, client, test_user_with_2fa, auth_headers_2fa):
        """测试禁用2FA端点"""
        response = client.post(
            "/api/v1/auth/2fa/disable",
            headers=auth_headers_2fa,
            json={"password": "test_password"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_backup_codes_info_endpoint(self, client, test_user_with_2fa, auth_headers_2fa):
        """测试获取备用码信息端点"""
        response = client.get(
            "/api/v1/auth/2fa/backup-codes",
            headers=auth_headers_2fa
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "unused" in data
        assert "used" in data
    
    def test_2fa_login_flow(self, client, test_user_with_2fa, db):
        """测试完整2FA登录流程"""
        import pyotp
        
        # 1. 第一步：用户名密码登录
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_with_2fa.username,
                "password": "test_password"
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get("requires_2fa") is True
        assert "temp_token" in login_data
        
        # 2. 获取用户的TOTP密钥
        secret_record = db.query(User2FASecret).filter(
            User2FASecret.user_id == test_user_with_2fa.id
        ).first()
        service = get_two_factor_service()
        secret = service._decrypt_secret(secret_record.secret_encrypted)
        
        # 3. 生成TOTP码
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # 4. 完成2FA登录
        verify_response = client.post(
            "/api/v1/auth/2fa/login",
            json={
                "temp_token": login_data["temp_token"],
                "code": code
            }
        )
        
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert "access_token" in verify_data
        assert "refresh_token" in verify_data
        assert verify_data["token_type"] == "bearer"


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def test_user(db: Session):
    """创建测试用户（未启用2FA）"""
    user = User(
        username="test_2fa_user",
        email="test_2fa@example.com",
        password_hash=get_password_hash("test_password"),
        is_active=True,
        two_factor_enabled=False
    )
    db.add(user)
    db.commit()
    yield user
    
    # 清理
    db.delete(user)
    db.commit()


@pytest.fixture
def test_user_with_2fa(db: Session):
    """创建已启用2FA的测试用户"""
    import pyotp
    
    user = User(
        username="test_2fa_enabled_user",
        email="test_2fa_enabled@example.com",
        password_hash=get_password_hash("test_password"),
        is_active=True,
        two_factor_enabled=False
    )
    db.add(user)
    db.commit()
    
    # 启用2FA
    service = get_two_factor_service()
    secret, _ = service.setup_2fa_for_user(db, user)
    totp = pyotp.TOTP(secret)
    service.enable_2fa_for_user(db, user, totp.now())
    
    yield user
    
    # 清理
    db.delete(user)
    db.commit()


@pytest.fixture
def auth_headers(client, test_user):
    """生成认证头（未启用2FA的用户）"""
    from app.core.auth import create_access_token
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_2fa(client, test_user_with_2fa):
    """生成认证头（已启用2FA的用户）"""
    from app.core.auth import create_access_token
    token = create_access_token(data={"sub": str(test_user_with_2fa.id)})
    return {"Authorization": f"Bearer {token}"}
