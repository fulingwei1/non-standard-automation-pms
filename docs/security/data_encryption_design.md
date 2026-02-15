# 数据加密设计文档

## 📋 概述

本文档描述了非标自动化项目管理系统（PMS）的敏感数据加密方案，采用 **AES-256-GCM** 算法对数据库中的敏感字段进行加密存储，确保数据安全。

---

## 🎯 设计目标

### 1. 安全性
- ✅ 使用业界公认的加密算法（AES-256-GCM）
- ✅ 每次加密使用随机IV（防止重放攻击）
- ✅ 支持认证标签（防篡改）
- ✅ 密钥独立管理（与JWT密钥分离）

### 2. 性能
- ✅ 加密/解密操作高效（10,000次 < 1秒）
- ✅ 对应用层透明（自动加解密）
- ✅ 最小化性能影响（< 10%）

### 3. 易用性
- ✅ SQLAlchemy无缝集成
- ✅ 模型定义简单（只需更改字段类型）
- ✅ 现有数据迁移工具完善

---

## 🏗️ 架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     应用层 (API/Service)                  │
│  - 读写敏感数据（明文）                                    │
│  - 无需关心加密细节                                        │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  透明加解密层       │
        │  (SQLAlchemy)      │
        │  - EncryptedString │
        │  - EncryptedText   │
        │  - EncryptedNumeric│
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │   加密服务层        │
        │  DataEncryption    │
        │  - encrypt()       │
        │  - decrypt()       │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  加密算法层         │
        │  AES-256-GCM       │
        │  - 随机IV          │
        │  - 认证标签        │
        └─────────┬─────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                     数据库层 (MySQL)                       │
│  - 存储加密后的数据（密文）                                 │
│  - Base64编码                                              │
└─────────────────────────────────────────────────────────┘
```

### 2. 加密流程

```
明文数据 (plaintext)
    ↓
生成随机IV (12字节)
    ↓
AES-256-GCM 加密
    ↓
IV + 密文 + 认证标签
    ↓
Base64 编码
    ↓
存储到数据库
```

### 3. 解密流程

```
从数据库读取密文
    ↓
Base64 解码
    ↓
分离 IV 和密文
    ↓
AES-256-GCM 解密
    ↓
验证认证标签
    ↓
返回明文数据
```

---

## 🔐 加密算法详解

### AES-256-GCM

**选择理由**：
- **安全性**：256位密钥，足够抵御暴力破解
- **完整性**：GCM模式内置认证标签，可检测篡改
- **性能**：硬件加速支持（AES-NI），性能优异
- **标准化**：NIST标准，广泛应用

**关键参数**：
- **密钥长度**：256位（32字节）
- **IV长度**：96位（12字节）
- **认证标签长度**：128位（16字节）
- **加密模式**：GCM（Galois/Counter Mode）

---

## 🗂️ 敏感字段分类

### 1. 个人身份信息（PII）
- 身份证号：`EncryptedString(200)`
- 护照号：`EncryptedString(200)`
- 驾驶证号：`EncryptedString(200)`

### 2. 金融信息
- 银行卡号：`EncryptedString(200)`
- 工资薪酬：`EncryptedNumeric`
- 社保账号：`EncryptedString(200)`

### 3. 联系信息（可选）
- 手机号：`EncryptedString(200)`
- 家庭住址：`EncryptedText`
- 紧急联系人：`EncryptedText`

### 4. 其他敏感信息
- 健康信息：`EncryptedText`
- 背景调查：`EncryptedText`
- 合同条款：`EncryptedText`

---

## 📊 数据库Schema设计

### 示例：员工表

```sql
CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department VARCHAR(100),
    
    -- 敏感字段（加密存储）
    id_card VARCHAR(200) COMMENT '身份证号（加密）',
    bank_account VARCHAR(200) COMMENT '银行卡号（加密）',
    phone VARCHAR(200) COMMENT '手机号（加密）',
    address TEXT COMMENT '家庭住址（加密）',
    emergency_contact TEXT COMMENT '紧急联系人（加密）',
    salary VARCHAR(200) COMMENT '工资（加密）',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**字段长度说明**：
- 加密后数据长度约为原始长度的 **1.5-2倍**
- 建议字段长度至少为原始长度的 **2倍**
- 例如：身份证18位 → 200字符（预留足够空间）

---

## 🔑 密钥管理

### 1. 密钥存储

**开发环境**：
```bash
# .env 文件
DATA_ENCRYPTION_KEY=abc123...（44字符的Base64字符串）
```

**生产环境**（推荐）：
- AWS KMS（Key Management Service）
- Azure Key Vault
- HashiCorp Vault
- 云服务商密钥管理服务

### 2. 密钥轮转

支持多版本密钥共存，实现平滑轮转：

```python
# 未来扩展：密钥版本管理
class DataEncryption:
    def __init__(self):
        self.keys = {
            "v1": load_key("DATA_ENCRYPTION_KEY_V1"),
            "v2": load_key("DATA_ENCRYPTION_KEY_V2"),  # 新密钥
        }
        self.current_version = "v2"
```

### 3. 密钥备份

⚠️ **重要提示**：密钥丢失将导致数据无法解密！

备份方案：
1. **多地备份**：至少3个独立位置
2. **离线存储**：冷备份（USB、纸质密码箱）
3. **加密备份**：备份文件本身也要加密
4. **定期验证**：确保备份可用

---

## 📈 性能影响评估

### 1. 理论性能

| 操作类型 | 10,000次耗时 | 单次耗时 | 吞吐量 |
|---------|-------------|---------|--------|
| 加密     | ~0.5秒      | ~50μs   | 20,000 ops/s |
| 解密     | ~0.5秒      | ~50μs   | 20,000 ops/s |
| 加密+解密 | ~1.0秒      | ~100μs  | 10,000 ops/s |

### 2. 实际影响

- **API响应时间**：+5-10ms（单条记录）
- **批量查询**：+50-100ms（100条记录）
- **整体性能影响**：< 10%（验收标准）

### 3. 优化建议

1. **批量操作**：使用事务减少数据库往返
2. **缓存策略**：对频繁访问的敏感数据使用安全缓存
3. **异步处理**：大批量加密任务使用后台任务
4. **索引策略**：避免对加密字段建立索引（无意义且降低性能）

---

## 🛡️ 安全考虑

### 1. 防止信息泄露

- ✅ API返回时脱敏（如：`421002********1234`）
- ✅ 日志中不记录敏感明文
- ✅ 错误信息不暴露加密细节

### 2. 访问控制

- ✅ 敏感字段需要额外权限
- ✅ 审计日志记录访问行为
- ✅ 多因素认证（2FA）保护关键操作

### 3. 传输安全

- ✅ HTTPS强制加密（TLS 1.2+）
- ✅ API请求签名验证
- ✅ 防重放攻击（timestamp + nonce）

---

## 📝 合规性

### 1. 法律法规

- **GDPR**：欧盟通用数据保护条例
- **个人信息保护法**：中国个人信息保护法
- **ISO 27001**：信息安全管理体系

### 2. 数据权利

- **知情权**：告知用户数据加密存储
- **访问权**：用户可查看自己的敏感数据
- **删除权**：用户可要求删除数据
- **更正权**：用户可更正错误数据

---

## 🔄 版本历史

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
| v1.0 | 2026-02-15 | 初版发布，支持AES-256-GCM加密 |

---

## 📚 参考资料

- [NIST SP 800-38D: GCM Mode](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [Python Cryptography Library](https://cryptography.io/en/latest/)
