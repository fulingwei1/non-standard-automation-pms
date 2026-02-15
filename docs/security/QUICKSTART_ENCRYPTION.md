# 数据加密功能 - 5分钟快速上手

## 🚀 快速开始

### 1️⃣ 生成加密密钥（30秒）

```bash
python3 scripts/generate_encryption_key.py
```

复制输出的密钥：
```
DATA_ENCRYPTION_KEY=F6HQSOEE099YokHXWDsBYdp4sGlsCpUSefYDIaxFEzg=
```

### 2️⃣ 配置环境变量（10秒）

```bash
# 添加到 .env 文件
echo 'DATA_ENCRYPTION_KEY=F6HQSOEE099YokHXWDsBYdp4sGlsCpUSefYDIaxFEzg=' >> .env
```

### 3️⃣ 验证功能（20秒）

```bash
# 运行快速验证
python3 scripts/verify_encryption.py
```

**预期输出**：
```
✅ 所有测试通过！数据加密功能正常！
```

### 4️⃣ 使用加密字段（2分钟）

**定义模型**：
```python
from app.models.encrypted_types import EncryptedString
from sqlalchemy import Column, Integer, String

class Employee(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    # 敏感字段使用加密类型
    id_card = Column(EncryptedString(200))  # 身份证号（自动加密）
    phone = Column(EncryptedString(200))     # 手机号（自动加密）
```

**使用模型**（完全透明）：
```python
# 创建记录（自动加密）
employee = Employee(
    name="张三",
    id_card="421002199001011234",  # 明文输入
    phone="13800138000"
)
db.add(employee)
db.commit()

# 读取记录（自动解密）
employee = db.query(Employee).filter_by(name="张三").first()
print(employee.id_card)  # 输出: 421002199001011234（自动解密）
```

**就这么简单！** ✨

---

## 📊 性能指标

运行性能测试：
```bash
python3 scripts/benchmark_encryption.py
```

**预期性能**：
- 加密: ~490,000 ops/sec
- 解密: ~820,000 ops/sec
- 影响: < 5%

---

## 📚 完整文档

| 文档 | 用途 |
|-----|------|
| [设计文档](data_encryption_design.md) | 了解加密原理和架构 |
| [使用指南](encryption_field_usage_guide.md) | 详细使用说明 |
| [迁移手册](data_migration_manual.md) | 现有数据迁移 |
| [密钥管理](key_management_best_practices.md) | 密钥安全管理 |

---

## 🛠️ 常见问题

### Q1: 数据库迁移？

```bash
# 新增加密字段
python3 migrations/versions/20260215_add_encrypted_fields.py

# 加密现有数据（先DRY RUN）
python3 scripts/encrypt_existing_data.py \
  --table employees \
  --columns id_card,phone \
  --dry-run
```

### Q2: 如何查询加密字段？

⚠️ 无法直接查询加密字段！

**正确方式**：先通过非敏感字段查询，再在应用层验证
```python
# ❌ 错误：无法查询
employee = db.query(Employee).filter_by(id_card="421002...").first()

# ✅ 正确：先查员工编号
employee = db.query(Employee).filter_by(employee_code="EMP001").first()
# 然后验证身份证
if employee.id_card == "421002199001011234":
    print("验证通过")
```

### Q3: API返回脱敏？

```python
def to_dict(self):
    return {
        "name": self.name,
        "id_card": self.id_card[:6] + "********" + self.id_card[-4:],  # 脱敏
        "phone": self.phone[:3] + "****" + self.phone[-4:],            # 脱敏
    }
```

---

## ⚠️ 重要提示

1. **密钥备份**：密钥丢失 = 数据永久丢失！
2. **不要提交**：`.env` 文件不要提交到 Git
3. **生产环境**：使用密钥管理服务（AWS KMS/Vault）

---

## 🎓 示例项目

完整示例：`app/models/employee_encrypted_example.py`

---

## 📞 需要帮助？

- 📖 **文档**: `docs/security/`
- 🐛 **问题**: GitHub Issues
- 📧 **联系**: security@example.com
