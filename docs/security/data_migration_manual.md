# 数据迁移操作手册

## 📋 概述

本手册指导如何将现有数据库中的明文敏感数据迁移为加密存储。

---

## ⚠️ 迁移前准备

### 1. 备份数据库

**必须先备份！** 迁移过程不可逆！

```bash
# MySQL备份
mysqldump -u root -p pms_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用项目脚本
./scripts/backup_database.sh
```

### 2. 生成加密密钥

```bash
# 生成新密钥
python scripts/generate_encryption_key.py

# 输出示例：
# DATA_ENCRYPTION_KEY=abc123def456...
```

### 3. 配置环境变量

```bash
# 添加到 .env 文件
echo 'DATA_ENCRYPTION_KEY=abc123def456...' >> .env

# 或设置环境变量
export DATA_ENCRYPTION_KEY=abc123def456...
```

### 4. 验证环境

```bash
# 运行测试，确保加密功能正常
pytest tests/test_data_encryption.py -v
```

---

## 🚀 迁移步骤

### 方案A：新增加密字段（推荐，安全）

**优点**：
- ✅ 保留原始数据（可回滚）
- ✅ 可以对比验证
- ✅ 风险小

**缺点**：
- ❌ 需要两倍存储空间（临时）
- ❌ 需要两步操作

#### 步骤1：新增加密字段

```bash
# 运行迁移脚本
python migrations/versions/20260215_add_encrypted_fields.py
```

**执行内容**：
- 在 `employees` 表添加加密字段：
  - `id_card_encrypted`
  - `bank_account_encrypted`
  - `phone_encrypted`
  - `address_encrypted`
  - `emergency_contact_encrypted`
  - `salary_encrypted`

#### 步骤2：加密现有数据

```bash
# 先DRY RUN（模拟运行，不实际修改）
python scripts/encrypt_existing_data.py \
  --table employees \
  --columns id_card,bank_account,phone,address,emergency_contact,salary \
  --dry-run

# 输出示例：
# 找到 100 条记录需要加密
# [DRY RUN] ID=1, id_card: 421002199... → 加密
# ...
# [DRY RUN] 将加密 600 个字段（未实际执行）
```

确认无误后，正式执行：

```bash
# 正式加密
python scripts/encrypt_existing_data.py \
  --table employees \
  --columns id_card,bank_account,phone,address,emergency_contact,salary
```

#### 步骤3：验证加密数据

```python
# 进入Python Shell
python

from app.core.database import get_db
from app.models.employee import Employee

db = next(get_db())

# 查询一条记录
employee = db.query(Employee).first()

# 验证加密字段
print(f"原始身份证号: {employee.id_card}")  # 明文
print(f"加密身份证号: {employee.id_card_encrypted}")  # 已解密（应该相同）

# 验证数据库存储（应该是密文）
from sqlalchemy import text
result = db.execute(text("SELECT id, id_card_encrypted FROM employees LIMIT 1")).fetchone()
print(f"数据库中的密文: {result[1][:50]}...")  # Base64密文
```

#### 步骤4：更新模型

```python
# app/models/employee.py

# ❌ 删除明文字段
# id_card = Column(String(18))

# ✅ 重命名加密字段
# id_card_encrypted → id_card
from app.models.encrypted_types import EncryptedString

id_card = Column(EncryptedString(200), comment="身份证号（加密）")
```

#### 步骤5：删除明文字段（可选）

⚠️ **警告**：此操作不可逆！确保数据已正确加密！

```sql
-- 手动执行SQL
ALTER TABLE employees DROP COLUMN id_card_old;  -- 假设重命名为 id_card_old
ALTER TABLE employees DROP COLUMN bank_account_old;
-- ...

-- 或使用迁移脚本
python migrations/versions/20260215_cleanup_plaintext_fields.py
```

---

### 方案B：原地加密（快速，风险高）

**优点**：
- ✅ 一步完成
- ✅ 不占用额外存储

**缺点**：
- ❌ 不可回滚
- ❌ 如果失败，数据损坏

⚠️ **仅适用于开发环境或小数据量！**

#### 步骤1：直接加密

```bash
# 务必先备份！
mysqldump -u root -p pms_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 原地加密
python scripts/encrypt_existing_data.py \
  --table employees \
  --columns id_card,bank_account \
  --in-place  # 危险操作！
```

---

## 📊 批量迁移（大数据量）

### 1. 分批迁移

```bash
# 每次处理1000条
python scripts/encrypt_existing_data.py \
  --table employees \
  --columns id_card,bank_account \
  --batch-size 1000 \
  --offset 0

# 第二批
python scripts/encrypt_existing_data.py \
  --table employees \
  --columns id_card,bank_account \
  --batch-size 1000 \
  --offset 1000
```

### 2. 后台任务

```python
# 使用Celery异步任务
from celery import Celery
from app.core.encryption import data_encryption

app = Celery('tasks')

@app.task
def encrypt_employee_data(batch_ids):
    """异步加密员工数据"""
    db = next(get_db())
    
    employees = db.query(Employee).filter(Employee.id.in_(batch_ids)).all()
    
    for employee in employees:
        # 加密敏感字段
        employee.id_card_encrypted = data_encryption.encrypt(employee.id_card)
        employee.bank_account_encrypted = data_encryption.encrypt(employee.bank_account)
    
    db.commit()
    
    return len(employees)
```

---

## 🔍 验证清单

### ✅ 迁移前检查

- [ ] 数据库已备份
- [ ] 加密密钥已生成并配置
- [ ] 环境变量已设置
- [ ] 单元测试通过
- [ ] DRY RUN 成功

### ✅ 迁移中检查

- [ ] 迁移脚本无错误
- [ ] 加密字段数据正确
- [ ] 性能影响可接受

### ✅ 迁移后检查

- [ ] 原始数据和加密数据一致
- [ ] API功能正常
- [ ] 查询性能正常
- [ ] 日志无异常错误

---

## 🛠️ 常见问题

### 问题1：迁移中断

**症状**：脚本执行到一半失败

**解决**：
```bash
# 检查已加密的记录
python scripts/check_encrypted_status.py --table employees

# 继续未完成的加密
python scripts/encrypt_existing_data.py \
  --table employees \
  --columns id_card,bank_account \
  --skip-encrypted  # 跳过已加密的记录
```

### 问题2：加密数据验证失败

**症状**：加密后数据与原始数据不一致

**解决**：
1. 检查密钥是否正确
2. 检查字段长度是否足够
3. 回滚到备份

```bash
# 恢复备份
mysql -u root -p pms_db < backup_20260215_120000.sql
```

### 问题3：性能问题

**症状**：迁移过程很慢

**优化**：
```bash
# 增加批量大小
python scripts/encrypt_existing_data.py \
  --batch-size 1000  # 默认100

# 多进程并行
python scripts/encrypt_existing_data.py \
  --workers 4  # 4个进程
```

---

## 📈 性能指标

### 预期性能

| 数据量 | 预计耗时 | 吞吐量 |
|-------|---------|--------|
| 1,000条 | ~10秒 | 100条/秒 |
| 10,000条 | ~2分钟 | 100条/秒 |
| 100,000条 | ~20分钟 | 100条/秒 |

### 影响因素

- 数据库性能
- 网络延迟
- 字段数量
- 数据长度

---

## 🔄 回滚方案

### 方案A迁移的回滚

```sql
-- 删除加密字段
ALTER TABLE employees DROP COLUMN id_card_encrypted;
ALTER TABLE employees DROP COLUMN bank_account_encrypted;
-- ...

-- 保留原始明文字段（无数据丢失）
```

### 方案B迁移的回滚

```bash
# 恢复备份（唯一方法）
mysql -u root -p pms_db < backup_20260215_120000.sql
```

---

## 📝 迁移记录模板

```markdown
# 数据加密迁移记录

**日期**：2026-02-15  
**操作人**：张三  
**环境**：生产环境

## 迁移信息

- **表名**：employees
- **字段**：id_card, bank_account, phone, address, emergency_contact, salary
- **记录数**：1,234
- **方案**：方案A（新增加密字段）

## 执行步骤

1. [x] 数据库备份（backup_20260215_120000.sql）
2. [x] 生成加密密钥（已保存到密钥管理系统）
3. [x] 新增加密字段（20260215_add_encrypted_fields.py）
4. [x] DRY RUN 验证（无错误）
5. [x] 正式加密（1,234条记录，耗时2分15秒）
6. [x] 数据验证（100%一致）
7. [x] 更新模型（employee.py）
8. [ ] 删除明文字段（待定）

## 验证结果

- 加密成功：1,234条
- 加密失败：0条
- 数据一致性：100%
- API测试：通过
- 性能测试：影响 < 5%

## 备注

- 备份保存位置：/backups/20260215_120000/
- 密钥保存位置：密钥管理系统 + 冷备份
- 原始明文字段暂时保留，计划1个月后删除
```

---

## 📞 技术支持

遇到问题？联系：

- **技术负责人**：张三（zhangsan@example.com）
- **DBA**：李四（lisi@example.com）
- **文档**：`docs/security/`

---

## 📚 参考资料

- 设计文档：`data_encryption_design.md`
- 使用指南：`encryption_field_usage_guide.md`
- 密钥管理：`key_management_best_practices.md`
