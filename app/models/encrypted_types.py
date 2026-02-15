"""
SQLAlchemy 加密字段类型

提供透明的加密/解密功能，对应用层完全透明
"""

from sqlalchemy.types import TypeDecorator, String, Text
from app.core.encryption import data_encryption


class EncryptedString(TypeDecorator):
    """
    加密字符串类型（用于较短的敏感信息）
    
    使用方法:
    ```python
    class Employee(Base):
        id_card = Column(EncryptedString(200))  # 身份证号
        bank_account = Column(EncryptedString(200))  # 银行卡号
        phone = Column(EncryptedString(200))  # 手机号
    ```
    
    特性:
    - 写入数据库前自动加密
    - 从数据库读取后自动解密
    - 对应用层完全透明
    - 支持索引（但注意：加密后无法用于模糊查询）
    
    注意:
    - 加密后数据长度会增加（约1.5-2倍），需要预留足够的字段长度
    - 建议字段长度至少为原始数据的2倍（如身份证18位 → 200字符）
    """
    
    impl = String
    cache_ok = True
    
    def __init__(self, length=None, **kwargs):
        """
        初始化加密字符串类型
        
        Args:
            length: 字段长度（建议至少为原始数据的2倍）
        """
        super().__init__(length=length, **kwargs)
    
    def process_bind_param(self, value, dialect):
        """
        写入数据库前加密
        
        Args:
            value: 明文字符串
            dialect: 数据库方言
        
        Returns:
            加密后的Base64字符串
        """
        if value is not None:
            return data_encryption.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        """
        从数据库读取后解密
        
        Args:
            value: 加密后的Base64字符串
            dialect: 数据库方言
        
        Returns:
            解密后的明文字符串
        """
        if value is not None:
            return data_encryption.decrypt(value)
        return value


class EncryptedText(TypeDecorator):
    """
    加密文本类型（用于较长的敏感信息）
    
    使用方法:
    ```python
    class Employee(Base):
        address = Column(EncryptedText)  # 家庭住址
        emergency_contact = Column(EncryptedText)  # 紧急联系人信息
    ```
    
    特性:
    - 适用于较长的敏感信息（如地址、备注等）
    - 写入数据库前自动加密
    - 从数据库读取后自动解密
    - 对应用层完全透明
    
    注意:
    - Text类型通常没有长度限制，但加密后长度会增加
    - 不建议用于超大文本（如文章内容），性能会受影响
    """
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """
        写入数据库前加密
        
        Args:
            value: 明文文本
            dialect: 数据库方言
        
        Returns:
            加密后的Base64字符串
        """
        if value is not None:
            return data_encryption.encrypt(value)
        return value
    
    def process_result_value(self, value, dialect):
        """
        从数据库读取后解密
        
        Args:
            value: 加密后的Base64字符串
            dialect: 数据库方言
        
        Returns:
            解密后的明文文本
        """
        if value is not None:
            return data_encryption.decrypt(value)
        return value


class EncryptedNumeric(TypeDecorator):
    """
    加密数字类型（用于敏感的数值信息）
    
    使用方法:
    ```python
    class Employee(Base):
        salary = Column(EncryptedNumeric)  # 工资（敏感）
    ```
    
    特性:
    - 将数字转换为字符串后加密
    - 读取时解密后转换回数字
    - 支持整数和浮点数
    
    注意:
    - 加密后无法用于数学运算和排序
    - 如需统计，请在应用层解密后计算
    """
    
    impl = String
    cache_ok = True
    
    def __init__(self, length=200, **kwargs):
        """
        初始化加密数字类型
        
        Args:
            length: 字段长度（默认200字符）
        """
        super().__init__(length=length, **kwargs)
    
    def process_bind_param(self, value, dialect):
        """
        写入数据库前加密（数字 → 字符串 → 加密）
        
        Args:
            value: 数字（int/float/Decimal）
            dialect: 数据库方言
        
        Returns:
            加密后的Base64字符串
        """
        if value is not None:
            return data_encryption.encrypt(str(value))
        return value
    
    def process_result_value(self, value, dialect):
        """
        从数据库读取后解密（解密 → 字符串 → 数字）
        
        Args:
            value: 加密后的Base64字符串
            dialect: 数据库方言
        
        Returns:
            解密后的数字（保留原始类型）
        """
        if value is not None:
            decrypted = data_encryption.decrypt(value)
            if decrypted and decrypted != "[解密失败]":
                try:
                    # 尝试转换为浮点数（兼容整数和小数）
                    return float(decrypted)
                except ValueError:
                    return decrypted  # 如果转换失败，返回字符串
        return value
