# 融资管理模块数据生成总结

## 📋 概述

已成功创建完整的融资管理模块，包括数据模型、数据库迁移文件和测试数据生成脚本。

## ✅ 已完成内容

### 1. 数据模型 (`app/models/finance.py`)

创建了5个核心模型：

- **FundingRound（融资轮次）**: 管理种子轮、A轮、B轮、C轮、D轮等融资轮次
- **Investor（投资方）**: 管理VC、PE、天使投资人、战略投资方等信息
- **FundingRecord（融资记录）**: 记录每笔具体的投资，包括金额、持股比例、付款状态等
- **EquityStructure（股权结构）**: 记录每个轮次后的股权结构变化
- **FundingUsage（融资用途）**: 记录融资资金的使用计划和实际使用情况

### 2. 数据库迁移文件

- **MySQL迁移**: `migrations/20260120_finance_module_mysql.sql`
- **SQLite迁移**: `migrations/20260120_finance_module_sqlite.sql`

包含完整的表结构、索引和外键约束。

### 3. 数据生成脚本 (`scripts/generate_finance_data.py`)

自动生成完整的融资测试数据，包括：

#### 投资方数据（10个）
- 深创投（VC）
- 红杉资本中国基金（PE）
- IDG资本（VC）
- 真格基金（VC）
- 经纬中国（VC）
- 高瓴资本（PE）
- 腾讯投资（战略投资）
- 阿里巴巴创业投资（战略投资）
- 天使投资人-张总（天使）
- 天使投资人-李总（天使）

#### 融资轮次数据（5个）
1. **种子轮** (SEED)
   - 目标金额: 500万元
   - 投前估值: 2000万元
   - 投后估值: 2500万元
   - 状态: 已完成

2. **A轮** (A)
   - 目标金额: 3000万元
   - 投前估值: 8000万元
   - 投后估值: 1.1亿元
   - 状态: 已完成

3. **B轮** (B)
   - 目标金额: 8000万元
   - 投前估值: 3亿元
   - 投后估值: 3.8亿元
   - 状态: 已完成

4. **C轮** (C)
   - 目标金额: 1.5亿元
   - 投前估值: 8亿元
   - 投后估值: 9.5亿元
   - 状态: 已完成

5. **D轮** (D)
   - 目标金额: 3亿元
   - 投前估值: 20亿元
   - 投后估值: 23亿元
   - 状态: 进行中

#### 融资记录数据（23条）
- 每个轮次包含3-6个投资方
- 领投方占50%投资额，其他投资方平分剩余50%
- 包含完整的付款状态、合同信息等

#### 股权结构数据（43条）
- 记录每个轮次后的股权结构
- 包括创始人、员工期权池、各投资方的持股比例
- 考虑股权稀释效应

#### 融资用途数据（39条）
- 研发投入（35%）
- 市场推广（15%）
- 运营费用（4%）
- 设备采购（3%）
- 其他用途

## 📊 数据统计

```
投资方: 10 个
融资轮次: 5 个
融资记录: 23 条
股权结构: 43 条
融资用途: 39 条
```

## 🚀 使用方法

### 1. 运行数据库迁移

**SQLite:**
```bash
sqlite3 data/app.db < migrations/20260120_finance_module_sqlite.sql
```

**MySQL:**
```bash
mysql -u username -p database_name < migrations/20260120_finance_module_mysql.sql
```

### 2. 生成测试数据

```bash
python3 scripts/generate_finance_data.py
```

脚本会自动：
- 检查数据是否已存在，避免重复创建
- 生成完整的融资数据链
- 建立各表之间的关联关系

## 📁 文件清单

### 模型文件
- `app/models/finance.py` - 融资管理模块ORM模型

### 迁移文件
- `migrations/20260120_finance_module_mysql.sql` - MySQL迁移脚本
- `migrations/20260120_finance_module_sqlite.sql` - SQLite迁移脚本

### 数据生成脚本
- `scripts/generate_finance_data.py` - 测试数据生成脚本

### 模型导入
- `app/models/__init__.py` - 已添加融资模型导入

## 🔍 数据验证

### 查询投资方
```sql
SELECT investor_code, investor_name, investor_type, typical_ticket_size 
FROM investors 
ORDER BY investor_type, investor_name;
```

### 查询融资轮次
```sql
SELECT round_code, round_name, round_type, target_amount, actual_amount, status 
FROM funding_rounds 
ORDER BY round_order;
```

### 查询融资记录
```sql
SELECT 
    fr.record_code,
    i.investor_name,
    fr.round_code,
    fr.investment_amount,
    fr.share_percentage,
    fr.payment_status
FROM funding_records fr
JOIN investors i ON fr.investor_id = i.id
JOIN funding_rounds fr2 ON fr.funding_round_id = fr2.id
ORDER BY fr2.round_order, fr.investment_amount DESC;
```

### 查询股权结构
```sql
SELECT 
    fr.round_name,
    es.shareholder_name,
    es.shareholder_type,
    es.share_percentage
FROM equity_structures es
JOIN funding_rounds fr ON es.funding_round_id = fr.id
ORDER BY fr.round_order, es.share_percentage DESC;
```

### 查询融资用途
```sql
SELECT 
    fr.round_name,
    fu.usage_category,
    fu.usage_item,
    fu.planned_amount,
    fu.actual_amount,
    fu.percentage,
    fu.status
FROM funding_usages fu
JOIN funding_rounds fr ON fu.funding_round_id = fr.id
ORDER BY fr.round_order, fu.percentage DESC;
```

## 📝 数据特点

1. **完整性**: 覆盖从种子轮到D轮的完整融资历程
2. **真实性**: 投资方名称和投资金额参考真实市场情况
3. **关联性**: 所有数据表之间建立了完整的外键关联
4. **可扩展性**: 模型设计支持未来扩展更多融资相关功能

## 🔄 后续工作

1. **API端点**: 创建融资管理相关的API端点
2. **前端页面**: 开发融资管理的前端界面
3. **报表功能**: 实现融资数据统计和报表
4. **权限控制**: 添加融资数据的访问权限控制

## 📌 注意事项

1. 运行数据生成脚本前，确保已执行数据库迁移
2. 脚本会自动检查数据是否已存在，可安全重复运行
3. 如需清空数据重新生成，需要先删除相关表数据

---

**创建日期**: 2025-01-20  
**最后更新**: 2025-01-20
