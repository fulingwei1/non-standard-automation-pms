# 客户管理模块 - 数据字典

## 概述

本文档描述客户管理模块相关的数据库表结构，包括：
- `customers` - 客户档案表
- `contacts` - 联系人表
- `customer_tags` - 客户标签表

**数据库**: MySQL 8.0+ / PostgreSQL 12+ / SQLite 3

**字符集**: UTF-8

**更新日期**: 2026-02-15

---

## 1. customers (客户档案表)

### 表说明
存储客户的基本信息、详细信息、财务信息和业务信息。

### 表结构

| 字段名 | 数据类型 | 长度/精度 | 可空 | 默认值 | 主键 | 唯一 | 索引 | 说明 |
|--------|---------|-----------|------|--------|------|------|------|------|
| id | INT | - | 否 | AUTO | 是 | 是 | 是 | 主键ID |
| customer_code | VARCHAR | 50 | 否 | - | 否 | 是 | 是 | 客户编码，格式：CUS + YYYYMMDD + 序号 |
| name | VARCHAR | 200 | 否 | - | 否 | 否 | 否 | 客户名称 |
| short_name | VARCHAR | 100 | 是 | NULL | 否 | 否 | 否 | 客户简称 |
| customer_type | ENUM | - | 是 | 'enterprise' | 否 | 否 | 否 | 客户类型：enterprise(企业)/individual(个人) |
| industry | VARCHAR | 100 | 是 | NULL | 否 | 否 | 是 | 所属行业 |
| scale | VARCHAR | 50 | 是 | NULL | 否 | 否 | 否 | 企业规模 |
| address | TEXT | - | 是 | NULL | 否 | 否 | 否 | 详细地址 |
| website | VARCHAR | 200 | 是 | NULL | 否 | 否 | 否 | 公司网址 |
| established_date | DATE | - | 是 | NULL | 否 | 否 | 否 | 成立日期 |
| customer_level | ENUM | - | 是 | 'D' | 否 | 否 | 是 | 客户等级：A/B/C/D |
| credit_limit | DECIMAL | 15,2 | 是 | 0 | 否 | 否 | 否 | 信用额度 |
| payment_terms | VARCHAR | 100 | 是 | NULL | 否 | 否 | 否 | 付款条件 |
| account_period | INT | - | 是 | 30 | 否 | 否 | 否 | 账期(天) |
| customer_source | VARCHAR | 100 | 是 | NULL | 否 | 否 | 否 | 客户来源 |
| sales_owner_id | INT | - | 是 | NULL | 否 | 否 | 是 | 负责销售人员ID，外键关联users.id |
| status | ENUM | - | 是 | 'potential' | 否 | 否 | 是 | 客户状态：potential/prospect/customer/lost |
| last_follow_up_at | DATETIME | - | 是 | NULL | 否 | 否 | 是 | 最后跟进时间 |
| annual_revenue | DECIMAL | 15,2 | 是 | 0 | 否 | 否 | 否 | 年成交额 |
| cooperation_years | INT | - | 是 | 0 | 否 | 否 | 否 | 合作年限 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | 否 | 否 | 是 | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | 否 | 否 | 否 | 更新时间 |

### 索引说明

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 主键索引 |
| idx_customer_code | 唯一 | customer_code | 客户编码唯一索引 |
| idx_customer_sales_owner | 普通 | sales_owner_id | 负责人索引，加速权限过滤 |
| idx_customer_level | 普通 | customer_level | 等级索引，加速筛选 |
| idx_customer_status | 普通 | status | 状态索引，加速筛选 |
| idx_customer_industry | 普通 | industry | 行业索引，加速筛选 |
| idx_customer_created_at | 普通 | created_at | 创建时间索引，加速排序 |
| idx_customer_last_follow_up | 普通 | last_follow_up_at | 最后跟进时间索引，加速排序 |

### 外键约束

| 约束名 | 外键字段 | 引用表 | 引用字段 | 删除规则 | 更新规则 |
|--------|----------|--------|----------|----------|----------|
| fk_customer_sales_owner | sales_owner_id | users | id | SET NULL | CASCADE |

### 枚举值说明

**customer_type**:
- `enterprise`: 企业客户
- `individual`: 个人客户

**customer_level** (自动计算):
- `A`: A级客户（年成交额>100万 且 合作>3年）
- `B`: B级客户（年成交额50-100万 且 合作1-3年）
- `C`: C级客户（年成交额10-50万）
- `D`: D级客户（年成交额<10万 或 潜在客户）

**status**:
- `potential`: 潜在客户
- `prospect`: 意向客户
- `customer`: 成交客户
- `lost`: 流失客户

### 业务规则

1. **客户编码生成**: 格式为 `CUS + YYYYMMDD + 0001`，如 `CUS202602150001`
2. **客户等级自动更新**: 创建或更新 `annual_revenue`、`cooperation_years` 时自动重算
3. **默认负责人**: 创建时若未指定，默认为创建人
4. **级联删除**: 删除客户时会级联删除其所有联系人和标签

### 示例数据

```sql
INSERT INTO customers (
    customer_code, name, short_name, customer_type, industry, 
    scale, address, website, credit_limit, payment_terms, 
    account_period, customer_source, sales_owner_id, status, 
    annual_revenue, cooperation_years, customer_level
) VALUES (
    'CUS202602150001', '上海示例科技有限公司', '示例科技', 
    'enterprise', '电子制造', '中型', 
    '上海市浦东新区张江高科技园区', 'https://example.com', 
    1000000.00, '月结30天', 30, '展会', 1, 'customer', 
    1500000.00, 4, 'A'
);
```

---

## 2. contacts (联系人表)

### 表说明
存储客户的联系人信息，一个客户可以有多个联系人。

### 表结构

| 字段名 | 数据类型 | 长度/精度 | 可空 | 默认值 | 主键 | 唯一 | 索引 | 说明 |
|--------|---------|-----------|------|--------|------|------|------|------|
| id | INT | - | 否 | AUTO | 是 | 是 | 是 | 主键ID |
| customer_id | INT | - | 否 | - | 否 | 否 | 是 | 所属客户ID，外键关联customers.id |
| name | VARCHAR | 100 | 否 | - | 否 | 否 | 否 | 联系人姓名 |
| position | VARCHAR | 100 | 是 | NULL | 否 | 否 | 否 | 职位 |
| department | VARCHAR | 100 | 是 | NULL | 否 | 否 | 否 | 部门 |
| mobile | VARCHAR | 20 | 是 | NULL | 否 | 否 | 是 | 手机号码 |
| phone | VARCHAR | 20 | 是 | NULL | 否 | 否 | 否 | 座机 |
| email | VARCHAR | 100 | 是 | NULL | 否 | 否 | 是 | 电子邮箱 |
| wechat | VARCHAR | 100 | 是 | NULL | 否 | 否 | 否 | 微信号 |
| birthday | DATE | - | 是 | NULL | 否 | 否 | 否 | 生日 |
| hobbies | TEXT | - | 是 | NULL | 否 | 否 | 否 | 兴趣爱好 |
| notes | TEXT | - | 是 | NULL | 否 | 否 | 否 | 备注 |
| is_primary | BOOLEAN | - | 是 | FALSE | 否 | 否 | 是 | 是否为主要联系人 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | 否 | 否 | 否 | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | 否 | 否 | 否 | 更新时间 |

### 索引说明

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 主键索引 |
| idx_contact_customer | 普通 | customer_id | 客户ID索引，加速查询 |
| idx_contact_primary | 普通 | is_primary | 主要联系人索引，加速排序 |
| idx_contact_mobile | 普通 | mobile | 手机号索引，加速搜索 |
| idx_contact_email | 普通 | email | 邮箱索引，加速搜索 |

### 外键约束

| 约束名 | 外键字段 | 引用表 | 引用字段 | 删除规则 | 更新规则 |
|--------|----------|--------|----------|----------|----------|
| fk_contact_customer | customer_id | customers | id | CASCADE | CASCADE |

### 业务规则

1. **主要联系人唯一性**: 每个客户只能有一个主要联系人
2. **设置主要联系人**: 设置新的主要联系人时，自动取消该客户其他联系人的主要标记
3. **级联删除**: 删除客户时会级联删除其所有联系人
4. **列表排序**: 主要联系人排在前面，其他按创建时间倒序

### 示例数据

```sql
INSERT INTO contacts (
    customer_id, name, position, department, 
    mobile, phone, email, wechat, is_primary
) VALUES (
    1, '李经理', '采购经理', '采购部', 
    '13800138000', '021-88888888', 
    'lijingli@example.com', 'lijingli_wx', TRUE
);
```

---

## 3. customer_tags (客户标签表)

### 表说明
存储客户的标签信息，支持多对多关系（一个客户可以有多个标签）。

### 表结构

| 字段名 | 数据类型 | 长度/精度 | 可空 | 默认值 | 主键 | 唯一 | 索引 | 说明 |
|--------|---------|-----------|------|--------|------|------|------|------|
| id | INT | - | 否 | AUTO | 是 | 是 | 是 | 主键ID |
| customer_id | INT | - | 否 | - | 否 | 否 | 是 | 客户ID，外键关联customers.id |
| tag_name | VARCHAR | 50 | 否 | - | 否 | 否 | 是 | 标签名称 |
| created_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | 否 | 否 | 否 | 创建时间 |
| updated_at | DATETIME | - | 否 | CURRENT_TIMESTAMP | 否 | 否 | 否 | 更新时间 |

### 索引说明

| 索引名 | 类型 | 字段 | 说明 |
|--------|------|------|------|
| PRIMARY | 主键 | id | 主键索引 |
| idx_customer_tag_customer | 普通 | customer_id | 客户ID索引 |
| idx_customer_tag_name | 普通 | tag_name | 标签名索引，加速筛选 |
| idx_customer_tag_unique | 唯一 | customer_id, tag_name | 联合唯一索引，防止重复标签 |

### 外键约束

| 约束名 | 外键字段 | 引用表 | 引用字段 | 删除规则 | 更新规则 |
|--------|----------|--------|----------|----------|----------|
| fk_customer_tag_customer | customer_id | customers | id | CASCADE | CASCADE |

### 预定义标签

系统提供以下预定义标签，也支持自定义标签：
- `重点客户`
- `战略客户`
- `普通客户`
- `流失客户`
- `高价值客户`
- `长期合作`
- `新客户`

### 业务规则

1. **标签唯一性**: 同一客户不能有重复的标签（通过联合唯一索引保证）
2. **级联删除**: 删除客户时会级联删除其所有标签
3. **批量添加**: 支持一次性为客户添加多个标签，自动过滤已存在的标签

### 示例数据

```sql
INSERT INTO customer_tags (customer_id, tag_name) VALUES
    (1, '重点客户'),
    (1, '长期合作'),
    (1, '高价值客户');
```

---

## 4. 表关系图

```
┌─────────────────┐
│    users        │
│  (用户表)       │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────────────────────┐
│    customers (客户档案表)       │
│  • id (PK)                      │
│  • customer_code (UNIQUE)       │
│  • name                         │
│  • customer_level (自动计算)    │
│  • sales_owner_id (FK)          │
│  • annual_revenue               │
│  • cooperation_years            │
└────────┬────────────────────────┘
         │ 1
         │
    ┌────┴────┐
    │         │
    │ N       │ N
┌───▼──────┐ ┌▼───────────────┐
│ contacts │ │ customer_tags  │
│(联系人表)│ │  (客户标签表)  │
│• id (PK) │ │ • id (PK)      │
│• customer│ │ • customer_id  │
│  _id(FK) │ │   (FK)         │
│• name    │ │ • tag_name     │
│• is_     │ └────────────────┘
│  primary │
└──────────┘
```

---

## 5. 数据迁移SQL

### MySQL

```sql
-- 客户表
CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_code VARCHAR(50) UNIQUE NOT NULL COMMENT '客户编码',
    name VARCHAR(200) NOT NULL COMMENT '客户名称',
    short_name VARCHAR(100) COMMENT '客户简称',
    customer_type ENUM('enterprise', 'individual') DEFAULT 'enterprise' COMMENT '客户类型',
    industry VARCHAR(100) COMMENT '所属行业',
    scale VARCHAR(50) COMMENT '企业规模',
    address TEXT COMMENT '详细地址',
    website VARCHAR(200) COMMENT '公司网址',
    established_date DATE COMMENT '成立日期',
    customer_level ENUM('A', 'B', 'C', 'D') DEFAULT 'D' COMMENT '客户等级',
    credit_limit DECIMAL(15,2) DEFAULT 0 COMMENT '信用额度',
    payment_terms VARCHAR(100) COMMENT '付款条件',
    account_period INT DEFAULT 30 COMMENT '账期(天)',
    customer_source VARCHAR(100) COMMENT '客户来源',
    sales_owner_id INT COMMENT '负责销售人员ID',
    status ENUM('potential', 'prospect', 'customer', 'lost') DEFAULT 'potential' COMMENT '客户状态',
    last_follow_up_at DATETIME COMMENT '最后跟进时间',
    annual_revenue DECIMAL(15,2) DEFAULT 0 COMMENT '年成交额',
    cooperation_years INT DEFAULT 0 COMMENT '合作年限',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_sales_owner (sales_owner_id),
    INDEX idx_customer_level (customer_level),
    INDEX idx_status (status),
    INDEX idx_industry (industry),
    INDEX idx_created_at (created_at),
    INDEX idx_last_follow_up (last_follow_up_at),
    FOREIGN KEY (sales_owner_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户档案表';

-- 联系人表
CREATE TABLE contacts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL COMMENT '所属客户ID',
    name VARCHAR(100) NOT NULL COMMENT '姓名',
    position VARCHAR(100) COMMENT '职位',
    department VARCHAR(100) COMMENT '部门',
    mobile VARCHAR(20) COMMENT '手机号码',
    phone VARCHAR(20) COMMENT '座机',
    email VARCHAR(100) COMMENT '电子邮箱',
    wechat VARCHAR(100) COMMENT '微信号',
    birthday DATE COMMENT '生日',
    hobbies TEXT COMMENT '兴趣爱好',
    notes TEXT COMMENT '备注',
    is_primary BOOLEAN DEFAULT FALSE COMMENT '是否为主要联系人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_customer (customer_id),
    INDEX idx_primary (is_primary),
    INDEX idx_mobile (mobile),
    INDEX idx_email (email),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='联系人表';

-- 客户标签表
CREATE TABLE customer_tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL COMMENT '客户ID',
    tag_name VARCHAR(50) NOT NULL COMMENT '标签名称',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_customer (customer_id),
    INDEX idx_tag_name (tag_name),
    UNIQUE INDEX idx_customer_tag_unique (customer_id, tag_name),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户标签表';
```

---

## 6. 性能优化建议

1. **索引优化**
   - 已为常用查询字段建立索引
   - 定期分析慢查询，根据实际情况调整索引

2. **分区策略**
   - 数据量超过100万条时，可考虑按年份分区

3. **归档策略**
   - 流失客户超过3年可归档到历史表
   - 定期清理无效联系人

4. **缓存策略**
   - 客户统计数据可使用Redis缓存
   - 预定义标签列表可缓存

---

**文档版本**: v1.0.0  
**更新日期**: 2026-02-15  
**维护部门**: 数据库管理组
