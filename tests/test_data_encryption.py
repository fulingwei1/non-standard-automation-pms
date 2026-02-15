"""
数据加密功能单元测试

包含25+测试用例，覆盖：
- 加密/解密基础功能（10个）
- SQLAlchemy加密类型（10个）
- 数据迁移工具（5个）
"""

import pytest
import os
import base64
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 导入加密模块
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.encryption import DataEncryption, data_encryption
from app.models.encrypted_types import EncryptedString, EncryptedText, EncryptedNumeric


# ==================== 测试基础 ====================

@pytest.fixture
def encryption_service():
    """加密服务实例"""
    return DataEncryption()


@pytest.fixture
def test_db():
    """测试数据库"""
    # 使用内存数据库
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    
    # 创建基础模型
    Base = declarative_base()
    
    class TestModel(Base):
        __tablename__ = "test_table"
        id = Column(Integer, primary_key=True)
        name = Column(String(100))
        id_card = Column(EncryptedString(200))
        address = Column(EncryptedText)
        salary = Column(EncryptedNumeric)
    
    Base.metadata.create_all(engine)
    
    return {
        "engine": engine,
        "session": Session(),
        "model": TestModel,
    }


# ==================== 加密/解密测试（10个） ====================

def test_encrypt_basic_string(encryption_service):
    """测试1：基础字符串加密"""
    plaintext = "421002199001011234"
    encrypted = encryption_service.encrypt(plaintext)
    
    assert encrypted is not None
    assert encrypted != plaintext
    assert len(encrypted) > len(plaintext)


def test_decrypt_basic_string(encryption_service):
    """测试2：基础字符串解密"""
    plaintext = "421002199001011234"
    encrypted = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_encrypt_decrypt_cycle(encryption_service):
    """测试3：加密/解密循环"""
    test_cases = [
        "421002199001011234",  # 身份证号
        "6217000010012345678",  # 银行卡号
        "13800138000",  # 手机号
        "湖北省武汉市洪山区珞瑜路1号",  # 地址
        "15000.50",  # 薪资
    ]
    
    for plaintext in test_cases:
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == plaintext, f"加密/解密失败: {plaintext}"


def test_encrypt_empty_string(encryption_service):
    """测试4：空字符串加密"""
    assert encryption_service.encrypt("") == ""
    assert encryption_service.encrypt(None) is None


def test_decrypt_empty_string(encryption_service):
    """测试5：空字符串解密"""
    assert encryption_service.decrypt("") == ""
    assert encryption_service.decrypt(None) is None


def test_encrypt_unicode(encryption_service):
    """测试6：Unicode字符加密"""
    unicode_texts = [
        "张三",
        "李四🎉",
        "测试数据 Test 123",
        "特殊字符：！@#￥%……&*（）",
    ]
    
    for text in unicode_texts:
        encrypted = encryption_service.encrypt(text)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == text


def test_encrypt_long_text(encryption_service):
    """测试7：长文本加密"""
    long_text = "这是一段很长的文本" * 100  # 约1000字
    encrypted = encryption_service.encrypt(long_text)
    decrypted = encryption_service.decrypt(long_text)
    
    assert decrypted == long_text


def test_encrypt_random_iv(encryption_service):
    """测试8：每次加密使用随机IV"""
    plaintext = "421002199001011234"
    encrypted1 = encryption_service.encrypt(plaintext)
    encrypted2 = encryption_service.encrypt(plaintext)
    
    # 相同明文，不同密文（因为IV随机）
    assert encrypted1 != encrypted2
    
    # 但解密结果相同
    assert encryption_service.decrypt(encrypted1) == plaintext
    assert encryption_service.decrypt(encrypted2) == plaintext


def test_decrypt_invalid_data(encryption_service):
    """测试9：解密无效数据"""
    invalid_data = [
        "invalid_base64_string",
        "abc123",
        "这不是加密数据",
    ]
    
    for data in invalid_data:
        result = encryption_service.decrypt(data)
        assert result == "[解密失败]"


def test_generate_key():
    """测试10：生成加密密钥"""
    key = DataEncryption.generate_key()
    
    # 验证是Base64字符串
    assert isinstance(key, str)
    assert len(key) > 0
    
    # 验证可以解码为32字节
    decoded = base64.urlsafe_b64decode(key)
    assert len(decoded) == 32  # 256位


# ==================== SQLAlchemy加密类型测试（10个） ====================

def test_encrypted_string_basic(test_db):
    """测试11：EncryptedString基础功能"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    record = TestModel(
        name="张三",
        id_card="421002199001011234"
    )
    session.add(record)
    session.commit()
    
    # 读取记录
    loaded = session.query(TestModel).filter_by(name="张三").first()
    assert loaded.id_card == "421002199001011234"


def test_encrypted_string_null(test_db):
    """测试12：EncryptedString空值处理"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录（id_card为空）
    record = TestModel(name="李四", id_card=None)
    session.add(record)
    session.commit()
    
    # 读取记录
    loaded = session.query(TestModel).filter_by(name="李四").first()
    assert loaded.id_card is None


def test_encrypted_text_basic(test_db):
    """测试13：EncryptedText基础功能"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    address = "湖北省武汉市洪山区珞瑜路1号华中科技大学"
    record = TestModel(name="王五", address=address)
    session.add(record)
    session.commit()
    
    # 读取记录
    loaded = session.query(TestModel).filter_by(name="王五").first()
    assert loaded.address == address


def test_encrypted_numeric_integer(test_db):
    """测试14：EncryptedNumeric整数"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    record = TestModel(name="赵六", salary=15000)
    session.add(record)
    session.commit()
    
    # 读取记录
    loaded = session.query(TestModel).filter_by(name="赵六").first()
    assert loaded.salary == 15000.0  # 转换为float


def test_encrypted_numeric_float(test_db):
    """测试15：EncryptedNumeric浮点数"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    record = TestModel(name="孙七", salary=15000.50)
    session.add(record)
    session.commit()
    
    # 读取记录
    loaded = session.query(TestModel).filter_by(name="孙七").first()
    assert loaded.salary == 15000.50


def test_encrypted_update(test_db):
    """测试16：更新加密字段"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    record = TestModel(name="周八", id_card="421002199001011234")
    session.add(record)
    session.commit()
    
    # 更新记录
    record.id_card = "421002199002022345"
    session.commit()
    
    # 读取记录
    loaded = session.query(TestModel).filter_by(name="周八").first()
    assert loaded.id_card == "421002199002022345"


def test_encrypted_multiple_records(test_db):
    """测试17：多条记录加密"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 批量创建
    records = [
        TestModel(name=f"员工{i}", id_card=f"42100219900101123{i}")
        for i in range(10)
    ]
    session.add_all(records)
    session.commit()
    
    # 验证
    for i in range(10):
        loaded = session.query(TestModel).filter_by(name=f"员工{i}").first()
        assert loaded.id_card == f"42100219900101123{i}"


def test_encrypted_unicode_text(test_db):
    """测试18：Unicode文本加密"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    address = "北京市朝阳区🏢建国门外大街1号国贸大厦"
    record = TestModel(name="Unicode测试", address=address)
    session.add(record)
    session.commit()
    
    # 读取记录
    loaded = session.query(TestModel).filter_by(name="Unicode测试").first()
    assert loaded.address == address


def test_encrypted_query_limitation(test_db):
    """测试19：加密字段查询限制"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    record = TestModel(name="查询测试", id_card="421002199001011234")
    session.add(record)
    session.commit()
    
    # ⚠️ 无法通过加密字段直接查询
    # 因为数据库中存储的是加密后的值
    result = session.query(TestModel).filter_by(id_card="421002199001011234").first()
    assert result is None  # 查询不到（这是预期行为）


def test_encrypted_rollback(test_db):
    """测试20：事务回滚"""
    session = test_db["session"]
    TestModel = test_db["model"]
    
    # 创建记录
    record = TestModel(name="回滚测试", id_card="421002199001011234")
    session.add(record)
    session.rollback()  # 回滚
    
    # 验证未保存
    loaded = session.query(TestModel).filter_by(name="回滚测试").first()
    assert loaded is None


# ==================== 数据迁移工具测试（5个） ====================

def test_migration_is_encrypted():
    """测试21：检测是否已加密"""
    from scripts.encrypt_existing_data import is_encrypted
    
    # 明文（未加密）
    assert not is_encrypted("421002199001011234")
    assert not is_encrypted("13800138000")
    assert not is_encrypted("短文本")
    
    # 加密后的数据
    encrypted = data_encryption.encrypt("421002199001011234")
    assert is_encrypted(encrypted)


def test_migration_batch_encrypt():
    """测试22：批量加密"""
    test_data = [
        "421002199001011234",
        "6217000010012345678",
        "13800138000",
    ]
    
    encrypted_data = [data_encryption.encrypt(d) for d in test_data]
    decrypted_data = [data_encryption.decrypt(e) for e in encrypted_data]
    
    assert decrypted_data == test_data


def test_migration_skip_encrypted():
    """测试23：跳过已加密数据"""
    from scripts.encrypt_existing_data import is_encrypted
    
    # 第一次加密
    plaintext = "421002199001011234"
    encrypted = data_encryption.encrypt(plaintext)
    
    # 检测到已加密，应跳过
    assert is_encrypted(encrypted)


def test_migration_error_handling():
    """测试24：错误处理"""
    # 尝试解密无效数据
    invalid_data = "invalid_encrypted_data"
    result = data_encryption.decrypt(invalid_data)
    
    assert result == "[解密失败]"


def test_migration_empty_handling():
    """测试25：空值处理"""
    # 空值应保持不变
    assert data_encryption.encrypt("") == ""
    assert data_encryption.encrypt(None) is None
    assert data_encryption.decrypt("") == ""
    assert data_encryption.decrypt(None) is None


# ==================== 性能测试（额外） ====================

def test_performance_encrypt_10000(encryption_service):
    """性能测试：10,000次加密"""
    import time
    
    plaintext = "421002199001011234"
    start = time.time()
    
    for _ in range(10000):
        encryption_service.encrypt(plaintext)
    
    elapsed = time.time() - start
    print(f"\n⏱️  10,000次加密耗时: {elapsed:.2f}秒")
    
    # 性能要求：10,000次加密 < 1秒
    assert elapsed < 1.0, f"性能不达标: {elapsed:.2f}秒"


def test_performance_decrypt_10000(encryption_service):
    """性能测试：10,000次解密"""
    import time
    
    plaintext = "421002199001011234"
    encrypted = encryption_service.encrypt(plaintext)
    
    start = time.time()
    
    for _ in range(10000):
        encryption_service.decrypt(encrypted)
    
    elapsed = time.time() - start
    print(f"\n⏱️  10,000次解密耗时: {elapsed:.2f}秒")
    
    # 性能要求：10,000次解密 < 1秒
    assert elapsed < 1.0, f"性能不达标: {elapsed:.2f}秒"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
