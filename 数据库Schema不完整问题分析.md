# 数据库Schema不完整问题分析

**日期**: 2026-02-16  
**发现人**: M5 AI Assistant  
**问题级别**: P1 (影响部分业务API)

---

## 问题描述

虽然我们已经成功创建了105个缺失的表，但**部分旧表的schema不完整**，缺少很多新增的列。

### 具体表现

在测试销售合同API (`/api/v1/sales/contracts`) 时发现连锁错误：

1. ✅ **Contract.owner问题** - 已修复 (改为sales_owner)
2. ❌ **contracts.contract_name缺失** - 已手动添加14个列
3. ❌ **contracts.quote_id缺失** - 已手动添加
4. ❌ **opportunities.expected_close_date缺失** - 未修复
5. ❓ **可能还有更多表的列缺失**

---

## 根本原因

### 表的创建方式差异

**新创建的105个表**:
- ✅ 使用 `CreateTable().compile()` 生成SQL
- ✅ 包含所有模型定义的列
- ✅ Schema完全匹配

**已存在的394个旧表**:
- ⚠️  创建时间早于最新模型定义
- ⚠️  缺少后续新增的列
- ⚠️  需要ALTER TABLE添加列

---

## 影响范围评估

### 核心系统 - 无影响 ✅
- ✅ 认证系统
- ✅ 用户管理
- ✅ 项目管理（基础功能）
- ✅ 生产工单（基础功能）

### 受影响的API - 部分影响 ⚠️
- ❌ 销售合同API (`/api/v1/sales/contracts`)
- ❓ 其他使用joinedload加载关联表的API
- ❓ 使用新增列的业务逻辑

---

## 识别问题表的方法

### 方法1: 对比SQLAlchemy模型与数据库

```python
from app.models.base import Base
import app.models

# 获取所有表的模型定义
for table_name, table in Base.metadata.tables.items():
    model_columns = {c.name for c in table.columns}
    db_columns = get_db_columns(table_name)  # 查询数据库
    missing = model_columns - db_columns
    if missing:
        print(f"{table_name}: 缺失 {missing}")
```

### 方法2: 捕获运行时错误

当API返回 `no such column: xxx` 错误时：
1. 记录表名和列名
2. 对比模型定义
3. 添加缺失的列

---

## 解决方案

### 方案A: 按需修复 (当前方法)
**优点**: 快速，只修复需要的表  
**缺点**: 需要逐个发现和修复  
**适用**: 快速上线，边用边修

**步骤**:
1. 运行API测试
2. 捕获 `no such column` 错误
3. 手动添加缺失的列
4. 重新测试

### 方案B: 系统性扫描和修复 (推荐)
**优点**: 一次性解决所有问题  
**缺点**: 需要时间（~30-60分钟）  
**适用**: 正式上线前的准备

**步骤**:
1. 创建扫描脚本，对比所有表
2. 生成ALTER TABLE SQL语句
3. 批量执行添加列操作
4. 验证所有表的schema

### 方案C: 重建数据库 (最彻底)
**优点**: 保证schema完全一致  
**缺点**: 会丢失所有数据  
**适用**: 开发环境，无重要数据时

**步骤**:
1. 备份关键数据（如果需要）
2. 删除旧数据库文件
3. 使用 `Base.metadata.create_all()` 重建
4. 恢复数据（如果需要）

---

## 当前状态

### 已修复的表
- ✅ `contracts` - 添加了14个列

### 待修复的表（已知）
- ❌ `opportunities` - 缺少expected_close_date等列
- ❓ 其他表（未测试）

### 修复脚本
- ✅ `fix_contracts_table.py` - 修复contracts表
- ⚠️  需要创建通用扫描脚本

---

## 建议行动方案

### 短期（今天）- 方案A
```bash
# 1. 测试关键API端点
# 2. 捕获错误并记录
# 3. 手动添加缺失的列
# 4. 重新测试验证

# 示例：修复opportunities表
sqlite3 data/app.db "ALTER TABLE opportunities ADD COLUMN expected_close_date DATE;"
```

### 中期（本周）- 方案B
```python
# 创建完整的schema同步脚本
python3 sync_all_table_schemas.py

# 输出：
# - 检查所有499个表
# - 生成完整的ALTER TABLE脚本
# - 批量执行修复
# - 生成验证报告
```

### 长期（下周）- 建立机制
1. 使用Alembic管理数据库迁移
2. 在CI/CD中添加schema验证
3. 禁止直接修改生产数据库schema

---

## 技术细节

### 为什么会出现这个问题？

1. **开发流程**:
   - 先创建数据库表（可能是早期版本）
   - 后续模型添加新字段
   - 但没有执行ALTER TABLE

2. **我们的修复**:
   - 创建了105个新表（包含所有列）
   - 但没有更新394个旧表

3. **SQLAlchemy行为**:
   - `create_all(checkfirst=True)` 只创建不存在的表
   - **不会**修改已存在表的schema
   - 需要手动ALTER TABLE或使用migration工具

### 预防措施

**使用Alembic**:
```python
# 自动生成migration
alembic revision --autogenerate -m "add new columns"

# 执行migration
alembic upgrade head
```

---

## 参考资料

### 已创建的文档
- `数据库Schema同步完成报告.md` - 105个新表创建
- `create_missing_tables_sql.py` - 创建表的脚本
- `fix_contracts_table.py` - 修复contracts表

### 需要创建的工具
- `sync_all_table_schemas.py` - 全面同步脚本
- `verify_schema_integrity.py` - Schema完整性验证

---

## 总结

✅ **核心功能正常** - 认证、项目、生产基础功能都正常  
⚠️  **部分业务API受影响** - 需要修复旧表的schema  
🔧 **两种修复路径**: 按需修复（快）vs 系统性修复（彻底）

**建议**: 
1. 短期使用方案A，快速修复关键API
2. 中期执行方案B，一次性解决所有问题
3. 长期建立Alembic migration机制

---

**报告时间**: 2026-02-16 18:15 GMT+8  
**当前优先级**: 中等（不影响核心功能，但影响部分业务API）
