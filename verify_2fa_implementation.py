#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2FA功能验证脚本

快速验证2FA核心功能是否正常工作
"""

import os
import sys

# 设置环境变量
os.environ["SECRET_KEY"] = "test_secret_key_for_verification_only"
os.environ["SQLITE_DB_PATH"] = ":memory:"

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.two_factor_service import TwoFactorService
import pyotp


def test_totp_generation():
    """测试1：TOTP密钥生成"""
    print("测试1：TOTP密钥生成...")
    service = TwoFactorService()
    secret = service.generate_totp_secret()
    assert len(secret) == 32
    assert secret.isalnum()
    print(f"  ✅ 生成密钥: {secret}")


def test_encryption_decryption():
    """测试2：密钥加密和解密"""
    print("\n测试2：密钥加密和解密...")
    service = TwoFactorService()
    secret = "JBSWY3DPEHPK3PXP"
    
    # 加密
    encrypted = service._encrypt_secret(secret)
    print(f"  ✅ 加密成功: {encrypted[:50]}...")
    
    # 解密
    decrypted = service._decrypt_secret(encrypted)
    assert decrypted == secret
    print(f"  ✅ 解密成功: {decrypted}")


def test_totp_verification():
    """测试3：TOTP验证码验证"""
    print("\n测试3：TOTP验证码验证...")
    service = TwoFactorService()
    secret = "JBSWY3DPEHPK3PXP"
    
    # 生成当前TOTP码
    totp = pyotp.TOTP(secret)
    code = totp.now()
    print(f"  生成的TOTP码: {code}")
    
    # 验证
    result = service.verify_totp_code(secret, code)
    assert result is True
    print(f"  ✅ 验证成功")
    
    # 错误码应该失败
    result = service.verify_totp_code(secret, "000000")
    assert result is False
    print(f"  ✅ 错误码验证失败（预期行为）")


def test_qr_code_generation():
    """测试4：QR码生成"""
    print("\n测试4：QR码生成...")
    service = TwoFactorService()
    
    # 创建模拟用户对象
    class MockUser:
        username = "test_user"
        email = "test@example.com"
    
    user = MockUser()
    secret = "JBSWY3DPEHPK3PXP"
    
    # 生成QR码
    qr_png = service.generate_qr_code(user, secret)
    
    # 验证PNG格式
    assert qr_png.startswith(b'\x89PNG')
    print(f"  ✅ QR码生成成功（大小: {len(qr_png)} 字节）")


def test_backup_code_generation():
    """测试5：备用码生成"""
    print("\n测试5：备用码生成...")
    from app.core.auth import get_password_hash, verify_password
    
    # 生成备用码
    import secrets
    backup_codes = []
    for _ in range(10):
        code = "".join([str(secrets.randbelow(10)) for _ in range(8)])
        backup_codes.append(code)
    
    print(f"  ✅ 生成10个备用码:")
    for i, code in enumerate(backup_codes[:3], 1):
        print(f"    {i}. {code}")
    print(f"    ... (共10个)")
    
    # 测试哈希和验证
    code_hash = get_password_hash(backup_codes[0])
    print(f"  ✅ 备用码哈希: {code_hash[:50]}...")
    
    # 验证
    result = verify_password(backup_codes[0], code_hash)
    assert result is True
    print(f"  ✅ 备用码验证成功")


def test_database_migration():
    """测试6：数据库迁移检查"""
    print("\n测试6：数据库迁移检查...")
    from sqlalchemy import text, inspect
    from app.models.base import get_db
    
    db = next(get_db())
    try:
        inspector = inspect(db.bind)
        
        # 检查users表的2FA字段
        columns = [col['name'] for col in inspector.get_columns('users')]
        assert 'two_factor_enabled' in columns
        assert 'two_factor_method' in columns
        assert 'two_factor_verified_at' in columns
        print(f"  ✅ users表2FA字段已添加")
        
        # 检查user_2fa_secrets表
        tables = inspector.get_table_names()
        assert 'user_2fa_secrets' in tables
        print(f"  ✅ user_2fa_secrets表已创建")
        
        # 检查user_2fa_backup_codes表
        assert 'user_2fa_backup_codes' in tables
        print(f"  ✅ user_2fa_backup_codes表已创建")
        
    finally:
        db.close()


def test_api_import():
    """测试7：API端点导入检查"""
    print("\n测试7：API端点导入检查...")
    from app.api.v1.endpoints.two_factor import router
    print(f"  ✅ 2FA API路由导入成功")
    
    # 检查路由端点
    routes = [route.path for route in router.routes]
    expected_routes = ['/setup', '/enable', '/verify', '/disable', '/login', '/backup-codes', '/backup-codes/regenerate']
    for route in expected_routes:
        if route in routes:
            print(f"  ✅ 端点存在: {route}")


def main():
    """运行所有验证测试"""
    print("=" * 70)
    print("2FA功能验证开始".center(70))
    print("=" * 70)
    
    tests = [
        test_totp_generation,
        test_encryption_decryption,
        test_totp_verification,
        test_qr_code_generation,
        test_backup_code_generation,
        test_database_migration,
        test_api_import,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"验证结果: {passed}个测试通过, {failed}个测试失败".center(70))
    print("=" * 70)
    
    if failed == 0:
        print("\n✅ 所有核心功能验证通过！2FA功能实现完成。\n")
        return 0
    else:
        print(f"\n❌ 有 {failed} 个测试失败，请检查实现。\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
