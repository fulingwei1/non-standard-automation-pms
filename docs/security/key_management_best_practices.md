# 密钥管理最佳实践

## 📋 概述

数据加密密钥（Data Encryption Key, DEK）是保护敏感数据的核心。本文档描述密钥管理的最佳实践。

⚠️ **核心原则**：密钥丢失 = 数据永久丢失！

---

## 🔑 密钥生命周期

```
生成 → 存储 → 使用 → 轮转 → 归档 → 销毁
 ↓      ↓      ↓      ↓      ↓      ↓
备份   加密    审计   迁移   保留   安全删除
```

---

## 1️⃣ 密钥生成

### 1.1 生成方式

**推荐方式**：使用官方脚本

```bash
# 生成256位加密密钥
python scripts/generate_encryption_key.py

# 输出：
# DATA_ENCRYPTION_KEY=abc123def456...（44字符）
```

**手动生成**（不推荐）：

```bash
# Linux/Mac
openssl rand -base64 32

# Python
python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### 1.2 密钥要求

- ✅ **长度**：256位（32字节）
- ✅ **随机性**：使用密码学安全的随机数生成器
- ✅ **唯一性**：每个环境独立生成（开发/测试/生产）
- ✅ **格式**：Base64 URL-safe 编码

### 1.3 验证密钥

```bash
# 验证密钥格式
python scripts/generate_encryption_key.py verify --key "abc123def456..."

# 输出：
# ✅ 密钥格式正确！
#    长度: 32 字节 (256位)
```

---

## 2️⃣ 密钥存储

### 2.1 开发环境

**方式1：.env 文件**（仅开发环境）

```bash
# .env
DATA_ENCRYPTION_KEY=abc123def456...
```

⚠️ **注意**：
- `.env` 文件必须在 `.gitignore` 中
- 不要提交到版本控制系统

**方式2：环境变量**

```bash
# ~/.bashrc 或 ~/.zshrc
export DATA_ENCRYPTION_KEY=abc123def456...

# 或临时设置
export DATA_ENCRYPTION_KEY=abc123def456...
python app/main.py
```

### 2.2 测试环境

**推荐**：使用配置管理工具

- Ansible Vault
- Chef Encrypted Data Bags
- Puppet Hiera

示例（Ansible Vault）：

```bash
# 加密密钥文件
ansible-vault encrypt secrets.yml

# 使用时解密
ansible-vault view secrets.yml
```

### 2.3 生产环境

**强烈推荐**：使用专业的密钥管理服务

| 服务 | 提供商 | 优点 |
|-----|--------|------|
| AWS KMS | Amazon | 自动轮转、审计日志、高可用 |
| Azure Key Vault | Microsoft | FIPS 140-2认证、托管HSM |
| Google Cloud KMS | Google | 全球分布、自动备份 |
| HashiCorp Vault | HashiCorp | 开源、自托管、多云支持 |

#### 示例：AWS KMS 集成

```python
# app/core/encryption.py

import boto3
import base64
from botocore.exceptions import ClientError

class DataEncryption:
    def __init__(self):
        if settings.USE_KMS:
            # 从 AWS KMS 获取密钥
            self.key = self._get_key_from_kms()
        else:
            # 从环境变量获取密钥
            key_b64 = os.getenv("DATA_ENCRYPTION_KEY")
            self.key = base64.urlsafe_b64decode(key_b64)
    
    def _get_key_from_kms(self):
        """从 AWS KMS 获取数据加密密钥"""
        kms_client = boto3.client('kms', region_name=settings.AWS_REGION)
        
        try:
            # 获取加密的数据密钥
            response = kms_client.decrypt(
                CiphertextBlob=base64.b64decode(settings.KMS_ENCRYPTED_KEY),
                KeyId=settings.KMS_KEY_ID
            )
            
            return response['Plaintext']
        
        except ClientError as e:
            logger.error(f"KMS 密钥获取失败: {e}")
            raise
```

#### 示例：HashiCorp Vault 集成

```python
import hvac

class DataEncryption:
    def __init__(self):
        if settings.USE_VAULT:
            self.key = self._get_key_from_vault()
        else:
            # 从环境变量获取
            ...
    
    def _get_key_from_vault(self):
        """从 HashiCorp Vault 获取密钥"""
        client = hvac.Client(url=settings.VAULT_URL)
        client.token = settings.VAULT_TOKEN
        
        # 读取密钥
        secret = client.secrets.kv.v2.read_secret_version(
            path='data-encryption-key',
            mount_point='secret'
        )
        
        key_b64 = secret['data']['data']['key']
        return base64.urlsafe_b64decode(key_b64)
```

---

## 3️⃣ 密钥备份

### 3.1 备份策略

**3-2-1 备份原则**：

- **3**份副本：原始 + 2个备份
- **2**种介质：云存储 + 物理存储
- **1**个异地：不同地理位置

### 3.2 备份方式

#### 方式1：加密备份文件

```bash
# 1. 导出密钥
echo "DATA_ENCRYPTION_KEY=abc123..." > key_backup.txt

# 2. 加密备份文件（使用GPG）
gpg --symmetric --cipher-algo AES256 key_backup.txt

# 3. 安全存储
# - 云存储（加密后）
aws s3 cp key_backup.txt.gpg s3://my-secure-bucket/keys/
# - 物理存储（USB、纸质）
```

#### 方式2：密钥分片（Shamir's Secret Sharing）

```python
# 将密钥分成5片，至少3片才能恢复
from secretsharing import PlaintextToHexSecretSharer

# 分片
shares = PlaintextToHexSecretSharer.split_secret(key, 3, 5)

# 恢复
recovered_key = PlaintextToHexSecretSharer.recover_secret(shares[0:3])
```

### 3.3 物理备份

**纸质备份**（最安全）：

```
┌──────────────────────────────────────────┐
│  数据加密密钥备份                          │
│                                          │
│  环境: 生产环境                           │
│  生成日期: 2026-02-15                     │
│  负责人: 张三                             │
│                                          │
│  密钥（请妥善保管）:                       │
│  ┌──────────────────────────────────────┐│
│  │ DATA_ENCRYPTION_KEY=                ││
│  │ abc123def456...                     ││
│  └──────────────────────────────────────┘│
│                                          │
│  恢复方法:                                │
│  1. export DATA_ENCRYPTION_KEY=...      │
│  2. 重启应用                              │
│                                          │
│  存放位置: 保险柜 #2                       │
│  备份编号: KEY-BACKUP-001                 │
└──────────────────────────────────────────┘
```

放入密封袋 → 存入保险柜 → 记录位置

---

## 4️⃣ 密钥轮转

### 4.1 轮转策略

**建议频率**：
- 生产环境：**每年1次**
- 测试环境：**每季度1次**
- 开发环境：**按需**

**触发条件**：
- 定期轮转（每年）
- 密钥泄露
- 员工离职
- 安全审计要求

### 4.2 轮转步骤

#### 步骤1：生成新密钥

```bash
# 生成新密钥（v2）
python scripts/generate_encryption_key.py --save --output .env.key_v2

# 输出：
# DATA_ENCRYPTION_KEY_V2=xyz789...
```

#### 步骤2：配置多版本密钥

```python
# app/core/encryption.py

class DataEncryption:
    def __init__(self):
        # 加载所有密钥版本
        self.keys = {
            "v1": self._load_key("DATA_ENCRYPTION_KEY"),
            "v2": self._load_key("DATA_ENCRYPTION_KEY_V2"),
        }
        
        # 当前版本（用于加密新数据）
        self.current_version = "v2"
    
    def encrypt(self, plaintext: str) -> str:
        """使用当前版本密钥加密"""
        # 添加版本前缀
        encrypted = self._encrypt_with_key(
            plaintext,
            self.keys[self.current_version]
        )
        return f"{self.current_version}:{encrypted}"
    
    def decrypt(self, ciphertext: str) -> str:
        """自动识别版本并解密"""
        if ":" in ciphertext:
            version, encrypted = ciphertext.split(":", 1)
            key = self.keys.get(version, self.keys["v1"])
        else:
            # 旧数据（无版本前缀）
            key = self.keys["v1"]
            encrypted = ciphertext
        
        return self._decrypt_with_key(encrypted, key)
```

#### 步骤3：重新加密数据

```bash
# 使用新密钥重新加密
python scripts/reencrypt_data.py \
  --old-version v1 \
  --new-version v2 \
  --table employees
```

#### 步骤4：停用旧密钥

```python
# 确认所有数据已迁移到v2后
# 删除v1密钥
del self.keys["v1"]
```

### 4.3 零停机轮转

```python
# 1. 添加新密钥（v2），保留旧密钥（v1）
# 2. 新数据用v2加密
# 3. 后台任务逐步重新加密旧数据
# 4. 所有数据迁移完成后，删除v1
```

---

## 5️⃣ 密钥访问控制

### 5.1 最小权限原则

| 角色 | 权限 | 说明 |
|-----|------|------|
| 开发人员 | 读（开发环境） | 可访问开发环境密钥 |
| 运维人员 | 读（所有环境） | 可访问但不能修改 |
| 安全管理员 | 读写 | 可生成、轮转、撤销密钥 |
| DBA | 无 | 不需要访问密钥 |
| 应用程序 | 读（运行时） | 仅运行时读取 |

### 5.2 审计日志

**记录内容**：
- 密钥访问时间
- 访问者身份
- 访问方式
- 操作类型（读取/写入/删除）

**示例（AWS CloudTrail）**：

```json
{
  "eventName": "Decrypt",
  "eventSource": "kms.amazonaws.com",
  "userIdentity": {
    "principalId": "AIDAI....",
    "arn": "arn:aws:iam::123456789012:user/admin"
  },
  "requestParameters": {
    "keyId": "arn:aws:kms:us-east-1:123456789012:key/..."
  },
  "responseElements": null,
  "eventTime": "2026-02-15T10:30:00Z"
}
```

---

## 6️⃣ 应急响应

### 6.1 密钥泄露

**立即行动**：

1. **隔离**：停止使用泄露的密钥
2. **轮转**：生成新密钥
3. **通知**：通知安全团队和管理层
4. **调查**：分析泄露原因和影响范围
5. **修复**：修复安全漏洞

```bash
# 紧急轮转密钥
./scripts/emergency_key_rotation.sh
```

### 6.2 密钥丢失

**恢复步骤**：

1. **检查备份**：尝试从备份恢复
2. **多地备份**：检查所有备份位置
3. **密钥分片**：如使用分片，收集足够的片段
4. **物理备份**：检查保险柜中的纸质备份

⚠️ **如果所有备份都丢失**：
- 数据将永久无法解密！
- 需要从业务层面重新采集数据

---

## 7️⃣ 合规性

### 7.1 法律法规

- **GDPR**：欧盟通用数据保护条例
- **等保2.0**：中国信息安全等级保护
- **PCI DSS**：支付卡行业数据安全标准
- **HIPAA**：健康保险流通与责任法案

### 7.2 合规要求

| 标准 | 密钥长度 | 轮转周期 | 备份 | 审计 |
|-----|---------|---------|------|------|
| GDPR | ≥128位 | 推荐 | 必须 | 必须 |
| 等保2.0 | ≥128位 | 必须 | 必须 | 必须 |
| PCI DSS | ≥128位 | 必须（≤1年） | 必须 | 必须 |
| HIPAA | ≥128位 | 推荐 | 必须 | 必须 |

---

## 8️⃣ 检查清单

### ✅ 日常检查

- [ ] 密钥环境变量正确配置
- [ ] 备份完整且可恢复
- [ ] 访问权限最小化
- [ ] 审计日志正常记录

### ✅ 月度检查

- [ ] 验证备份可用性
- [ ] 审查访问日志
- [ ] 检查密钥轮转计划
- [ ] 更新密钥管理文档

### ✅ 年度检查

- [ ] 密钥轮转
- [ ] 安全审计
- [ ] 合规性评估
- [ ] 应急演练

---

## 📚 参考资料

- [NIST SP 800-57: Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [AWS Key Management Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)

---

## 📞 联系方式

- **安全团队**：security@example.com
- **紧急联系**：+86-138-0013-8000
- **文档更新**：2026-02-15
