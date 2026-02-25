"""
员工模型（加密字段示例）

展示如何使用加密字段保护敏感信息
"""

from sqlalchemy import Column, Integer, String, Date, Enum as SQLEnum
from datetime import date
import enum

from app.models.base import Base
from app.models.encrypted_types import EncryptedString, EncryptedText, EncryptedNumeric


class EmployeeEncryptedExampleStatus(str, enum.Enum):
    """员工状态"""
    ACTIVE = "active"  # 在职
    ON_LEAVE = "on_leave"  # 休假
    RESIGNED = "resigned"  # 离职
    PROBATION = "probation"  # 试用期


class EmployeeEncryptedExample(Base):
    """员工模型（带加密字段）
    
    敏感字段加密存储:
    - 身份证号
    - 银行卡号
    - 手机号
    - 家庭住址
    - 紧急联系人信息
    - 工资薪酬
    
    【状态】示例代码 - 可删除"""
    __tablename__ = "employees"
    
    # 基本信息（非敏感）
    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, nullable=False, index=True, comment="员工工号")
    name = Column(String(100), nullable=False, comment="姓名")
    email = Column(String(255), unique=True, nullable=False, index=True, comment="邮箱")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.PROBATION, comment="状态")
    hire_date = Column(Date, default=date.today, comment="入职日期")
    
    # 敏感字段（加密存储）
    id_card = Column(EncryptedString(200), comment="身份证号（加密）")
    bank_account = Column(EncryptedString(200), comment="银行卡号（加密）")
    phone = Column(EncryptedString(200), comment="手机号（加密）")
    address = Column(EncryptedText, comment="家庭住址（加密）")
    emergency_contact = Column(EncryptedText, comment="紧急联系人信息（加密）")
    salary = Column(EncryptedNumeric, comment="工资（加密）")
    
    def __repr__(self):
        return f"<Employee {self.employee_code} - {self.name}>"
    
    def to_dict(self, include_sensitive: bool = False):
        """
        转换为字典
        
        Args:
            include_sensitive: 是否包含敏感信息（默认不包含）
        
        Returns:
            员工信息字典
        """
        data = {
            "id": self.id,
            "employee_code": self.employee_code,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "position": self.position,
            "status": self.status.value if self.status else None,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
        }
        
        if include_sensitive:
            # 敏感信息脱敏显示
            data.update({
                "id_card": self._mask_id_card(self.id_card),
                "bank_account": self._mask_bank_account(self.bank_account),
                "phone": self._mask_phone(self.phone),
                "address": self.address[:10] + "***" if self.address else None,
                "emergency_contact": "[敏感信息]",
                "salary": self.salary,
            })
        
        return data
    
    @staticmethod
    def _mask_id_card(id_card: str) -> str:
        """身份证号脱敏（前6后4）"""
        if not id_card or len(id_card) < 10:
            return id_card
        return id_card[:6] + "********" + id_card[-4:]
    
    @staticmethod
    def _mask_bank_account(bank_account: str) -> str:
        """银行卡号脱敏（前4后4）"""
        if not bank_account or len(bank_account) < 8:
            return bank_account
        return bank_account[:4] + "********" + bank_account[-4:]
    
    @staticmethod
    def _mask_phone(phone: str) -> str:
        """手机号脱敏（中间4位）"""
        if not phone or len(phone) < 11:
            return phone
        return phone[:3] + "****" + phone[-4:]


# 示例：如何使用加密字段
"""
# 1. 创建员工（自动加密）
employee = Employee(
    employee_code="EMP001",
    name="张三",
    email="zhangsan@example.com",
    id_card="421002199001011234",  # 明文输入
    bank_account="6217000010012345678",  # 明文输入
    phone="13800138000",  # 明文输入
    address="湖北省武汉市洪山区珞瑜路1号",  # 明文输入
    salary=15000.00  # 明文输入
)
db.add(employee)
db.commit()

# 数据库中存储的是加密后的值：
# id_card: "gAAAAABl..."
# bank_account: "gAAAAABl..."
# phone: "gAAAAABl..."

# 2. 读取员工（自动解密）
employee = db.query(Employee).filter_by(employee_code="EMP001").first()
print(employee.id_card)  # 输出: 421002199001011234（自动解密）
print(employee.bank_account)  # 输出: 6217000010012345678（自动解密）

# 3. 更新员工（自动加密）
employee.phone = "13900139000"  # 明文输入
db.commit()  # 自动加密后存储

# 4. API返回（脱敏）
return employee.to_dict(include_sensitive=True)
# {
#     "name": "张三",
#     "id_card": "421002********1234",
#     "bank_account": "6217********5678",
#     "phone": "138****8000"
# }
"""
