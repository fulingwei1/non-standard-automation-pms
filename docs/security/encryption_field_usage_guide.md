# 加密字段使用指南

## 📖 快速开始

本指南帮助开发者快速上手使用加密字段保护敏感数据。

---

## 🚀 5分钟上手

### 1. 导入加密类型

```python
from app.models.encrypted_types import EncryptedString, EncryptedText, EncryptedNumeric
```

### 2. 定义模型

```python
from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    
    # 敏感字段使用加密类型
    id_card = Column(EncryptedString(200))  # 身份证号
    bank_account = Column(EncryptedString(200))  # 银行卡号
    salary = Column(EncryptedNumeric)  # 工资
```

### 3. 使用模型（完全透明）

```python
# 创建记录（自动加密）
employee = Employee(
    name="张三",
    id_card="421002199001011234",  # 明文输入
    bank_account="6217000010012345678",
    salary=15000.50
)
db.add(employee)
db.commit()

# 读取记录（自动解密）
employee = db.query(Employee).filter_by(name="张三").first()
print(employee.id_card)  # 输出: 421002199001011234（自动解密）

# 更新记录（自动加密）
employee.salary = 16000.00
db.commit()
```

就这么简单！✨

---

## 📚 详细教程

### 1. 加密类型选择

| 类型 | 用途 | 长度建议 | 示例 |
|-----|------|---------|------|
| `EncryptedString` | 短敏感信息 | 200字符 | 身份证、银行卡、手机号 |
| `EncryptedText` | 长敏感信息 | TEXT | 地址、备注、合同条款 |
| `EncryptedNumeric` | 敏感数字 | 200字符 | 工资、社保金额 |

### 2. 完整示例

#### 2.1 员工模型

```python
from sqlalchemy import Column, Integer, String, Date, Enum as SQLEnum
from datetime import date
import enum

from app.models.base import Base
from app.models.encrypted_types import EncryptedString, EncryptedText, EncryptedNumeric


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    RESIGNED = "resigned"


class Employee(Base):
    __tablename__ = "employees"
    
    # 基本信息（非敏感）
    id = Column(Integer, primary_key=True)
    employee_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    department = Column(String(100))
    position = Column(String(100))
    status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    hire_date = Column(Date, default=date.today)
    
    # 敏感字段（加密存储）
    id_card = Column(EncryptedString(200), comment="身份证号（加密）")
    bank_account = Column(EncryptedString(200), comment="银行卡号（加密）")
    phone = Column(EncryptedString(200), comment="手机号（加密）")
    address = Column(EncryptedText, comment="家庭住址（加密）")
    emergency_contact = Column(EncryptedText, comment="紧急联系人（加密）")
    salary = Column(EncryptedNumeric, comment="工资（加密）")
```

#### 2.2 CRUD操作

**创建**：
```python
from app.models.employee import Employee
from app.core.database import get_db

db = next(get_db())

employee = Employee(
    employee_code="EMP001",
    name="张三",
    email="zhangsan@example.com",
    department="研发部",
    position="高级工程师",
    id_card="421002199001011234",
    bank_account="6217000010012345678",
    phone="13800138000",
    address="湖北省武汉市洪山区珞瑜路1号",
    emergency_contact="李四，13900139000，配偶",
    salary=15000.50
)

db.add(employee)
db.commit()
db.refresh(employee)

print(f"员工 {employee.name} 创建成功，ID: {employee.id}")
```

**读取**：
```python
# 通过非敏感字段查询
employee = db.query(Employee).filter_by(employee_code="EMP001").first()

# 访问敏感字段（自动解密）
print(f"身份证号: {employee.id_card}")
print(f"银行卡号: {employee.bank_account}")
print(f"工资: {employee.salary}")
```

**更新**：
```python
employee = db.query(Employee).filter_by(employee_code="EMP001").first()

# 更新敏感字段（自动加密）
employee.salary = 16000.00
employee.phone = "13900139000"

db.commit()
```

**删除**：
```python
employee = db.query(Employee).filter_by(employee_code="EMP001").first()
db.delete(employee)
db.commit()
```

### 3. API返回脱敏

⚠️ **重要**：敏感数据在API返回时应该脱敏！

```python
class Employee(Base):
    # ... 模型定义 ...
    
    def to_dict(self, include_sensitive: bool = False):
        """
        转换为字典
        
        Args:
            include_sensitive: 是否包含敏感信息（默认不包含）
        """
        data = {
            "id": self.id,
            "employee_code": self.employee_code,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "position": self.position,
        }
        
        if include_sensitive:
            # 敏感信息脱敏显示
            data.update({
                "id_card": self._mask_id_card(self.id_card),
                "bank_account": self._mask_bank_account(self.bank_account),
                "phone": self._mask_phone(self.phone),
                "address": self.address[:10] + "***" if self.address else None,
                "salary": self.salary,  # 根据权限决定是否显示
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
```

**API路由**：
```python
@router.get("/employees/{employee_id}")
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter_by(id=employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    
    # 根据权限决定是否返回敏感信息
    include_sensitive = current_user.has_permission("view_sensitive_data")
    
    return employee.to_dict(include_sensitive=include_sensitive)
```

---

## ⚠️ 注意事项

### 1. 查询限制

❌ **错误**：无法通过加密字段直接查询
```python
# 这样查询不到结果！
employee = db.query(Employee).filter_by(id_card="421002199001011234").first()
```

✅ **正确**：通过非敏感字段查询，再验证敏感字段
```python
# 先查出所有可能的记录
employees = db.query(Employee).filter_by(department="研发部").all()

# 在应用层验证敏感字段
target_employee = None
for emp in employees:
    if emp.id_card == "421002199001011234":
        target_employee = emp
        break
```

### 2. 模糊查询

❌ **不支持**：加密字段无法模糊查询
```python
# 无法实现！
employees = db.query(Employee).filter(Employee.phone.like("138%")).all()
```

💡 **解决方案**：
- 方案1：对需要查询的字段不加密（权衡安全性和功能性）
- 方案2：建立搜索索引（如Elasticsearch）存储脱敏数据

### 3. 排序限制

❌ **不支持**：加密字段无法排序
```python
# 无法实现！
employees = db.query(Employee).order_by(Employee.salary.desc()).all()
```

💡 **解决方案**：
- 在应用层解密后排序
- 或者建立非敏感的薪资范围字段用于排序

### 4. 字段长度

⚠️ **重要**：加密后长度会增加约1.5-2倍

```python
# ❌ 错误：长度不足
id_card = Column(EncryptedString(18))  # 太短！加密后会截断

# ✅ 正确：预留足够空间
id_card = Column(EncryptedString(200))  # 推荐
```

### 5. NULL值处理

```python
# NULL值不会加密，保持为NULL
employee = Employee(name="张三", id_card=None)
db.add(employee)
db.commit()

# 读取时仍为NULL
assert employee.id_card is None
```

---

## 🔧 最佳实践

### 1. 分离敏感和非敏感字段

```python
# ✅ 好的设计
class Employee(Base):
    # 非敏感字段（用于查询、索引）
    employee_code = Column(String(50), unique=True, index=True)
    name = Column(String(100), index=True)
    department = Column(String(100), index=True)
    
    # 敏感字段（加密存储）
    id_card = Column(EncryptedString(200))
    bank_account = Column(EncryptedString(200))
```

### 2. 使用Pydantic Schema验证

```python
from pydantic import BaseModel, validator
import re

class EmployeeCreate(BaseModel):
    name: str
    id_card: str
    bank_account: str
    phone: str
    
    @validator('id_card')
    def validate_id_card(cls, v):
        # 18位数字或17位数字+X
        if not re.match(r'^\d{17}[\dXx]$', v):
            raise ValueError('身份证号格式错误')
        return v
    
    @validator('bank_account')
    def validate_bank_account(cls, v):
        # 16-19位数字
        if not re.match(r'^\d{16,19}$', v):
            raise ValueError('银行卡号格式错误')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        # 11位手机号
        if not re.match(r'^1[3-9]\d{9}$', v):
            raise ValueError('手机号格式错误')
        return v
```

### 3. 审计日志

```python
from app.utils.audit_log import log_sensitive_data_access

@router.get("/employees/{employee_id}/sensitive")
async def get_sensitive_data(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter_by(id=employee_id).first()
    
    # 记录敏感数据访问
    log_sensitive_data_access(
        user=current_user,
        resource="employee",
        resource_id=employee_id,
        action="view_sensitive"
    )
    
    return {
        "id_card": employee.id_card,
        "bank_account": employee.bank_account,
        "salary": employee.salary,
    }
```

---

## 🛠️ 故障排查

### 问题1：解密失败

**症状**：读取数据时显示 `[解密失败]`

**原因**：
- 密钥错误或丢失
- 数据库中数据已损坏
- 数据不是用当前密钥加密的

**解决**：
1. 检查环境变量 `DATA_ENCRYPTION_KEY` 是否正确
2. 验证密钥格式（44字符的Base64字符串）
3. 恢复密钥备份

### 问题2：性能慢

**症状**：查询大量加密数据时性能下降

**优化方案**：
1. 批量查询（减少数据库往返）
2. 使用事务
3. 添加非敏感字段索引
4. 分页查询

### 问题3：字段截断

**症状**：加密数据保存不完整

**解决**：
- 增加字段长度（建议200+）
- 检查数据库字段定义

---

## 📞 技术支持

遇到问题？参考以下资源：

1. **设计文档**：`docs/security/data_encryption_design.md`
2. **迁移手册**：`docs/security/data_migration_manual.md`
3. **密钥管理**：`docs/security/key_management_best_practices.md`
4. **单元测试**：`tests/test_data_encryption.py`

---

## 📝 更新日志

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
| v1.0 | 2026-02-15 | 初版发布 |
