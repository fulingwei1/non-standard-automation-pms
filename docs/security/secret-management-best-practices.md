# 密钥管理最佳实践

本文档提供SECRET_KEY管理的安全最佳实践和建议。

## 📋 目录

- [为什么需要安全的密钥管理](#为什么需要安全的密钥管理)
- [密钥生成](#密钥生成)
- [密钥存储](#密钥存储)
- [密钥轮转](#密钥轮转)
- [环境隔离](#环境隔离)
- [访问控制](#访问控制)
- [审计和监控](#审计和监控)
- [常见错误](#常见错误)

---

## 为什么需要安全的密钥管理

SECRET_KEY 用于:
- 签名和验证JWT Token
- 加密敏感数据
- 生成CSRF Token
- 会话管理

**如果密钥泄露**:
- ⚠️ 攻击者可以伪造任何用户的Token
- ⚠️ 可以解密所有加密数据
- ⚠️ 可以绕过身份验证
- ⚠️ 完全控制系统

---

## 密钥生成

### ✅ 推荐做法

#### 使用提供的CLI工具

```bash
python scripts/manage_secrets.py generate
```

输出示例:
```
🔑 生成 1 个密钥（长度: 32 字节）

====================================
nGZJK8VFx_QjR9mXtLpY3N2cH6vB1sWfE7oA4uD0iKz

长度: 43 字符
有效: ✅
```

#### 使用Python

```python
import secrets

# 生成32字节（256位）的密钥
secret_key = secrets.token_urlsafe(32)
print(secret_key)
```

#### 使用命令行

```bash
# macOS/Linux
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 或使用 openssl
openssl rand -base64 32
```

### ❌ 禁止做法

```python
# 🚫 永远不要这样做!
SECRET_KEY = "my-secret-key"
SECRET_KEY = "12345678"
SECRET_KEY = "admin"
SECRET_KEY = hashlib.md5("password".encode()).hexdigest()  # 不够随机
```

### 密钥强度要求

- **最小长度**: 32字符（推荐43+字符）
- **编码**: Base64 URL-safe
- **熵**: 至少256位
- **字符集**: A-Z, a-z, 0-9, -, _

---

## 密钥存储

### 开发环境

#### .env 文件（推荐）

```bash
# .env
SECRET_KEY=nGZJK8VFx_QjR9mXtLpY3N2cH6vB1sWfE7oA4uD0iKz
OLD_SECRET_KEYS=old-key-1,old-key-2
```

⚠️ **重要**: 将 `.env` 添加到 `.gitignore`

```bash
# .gitignore
.env
.env.local
*.secret
```

### 生产环境

#### 1. Docker Secrets（推荐）

```bash
# 创建密钥文件
echo "your-secret-key" > secrets/secret_key.txt
chmod 600 secrets/secret_key.txt

# docker-compose.yml
services:
  backend:
    secrets:
      - secret_key
    environment:
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  secret_key:
    file: ./secrets/secret_key.txt
```

#### 2. AWS Secrets Manager

```python
import boto3
import json

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='pms/production/secret-key')
secret = json.loads(response['SecretString'])
current_key = secret['current_key']
```

环境变量配置:
```bash
AWS_SECRETS_MANAGER_ENABLED=true
AWS_SECRET_NAME=pms/production/secret-key
AWS_REGION=us-east-1
```

#### 3. Azure Key Vault

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)
secret = client.get_secret("secret-key")
current_key = secret.value
```

#### 4. HashiCorp Vault

```bash
# 获取密钥
vault kv get -field=current_key secret/pms/production
```

### ❌ 禁止做法

```python
# 🚫 永远不要这样做!

# 硬编码在代码中
SECRET_KEY = "hardcoded-secret-key"

# 提交到Git
git add .env
git commit -m "Add secret key"  # 危险!

# 明文日志
logging.info(f"Secret key: {SECRET_KEY}")  # 泄露!

# 暴露在错误消息中
raise Exception(f"Invalid key: {SECRET_KEY}")  # 危险!
```

---

## 密钥轮转

### 为什么需要轮转密钥

1. **限制密钥泄露影响**: 即使密钥泄露，影响范围有限
2. **合规要求**: 某些行业要求定期轮转（如PCI DSS）
3. **降低破解风险**: 限制攻击者的时间窗口
4. **员工离职**: 员工离职后更换密钥

### 推荐轮转周期

- **开发环境**: 每30天
- **生产环境**: 每90天
- **安全事件**: 立即轮转
- **员工离职**: 立即轮转

### 轮转流程

#### 1. 使用CLI工具轮转

```bash
# 自动生成新密钥并轮转
python scripts/manage_secrets.py rotate

# 使用指定密钥轮转
python scripts/manage_secrets.py rotate --key "new-key-here"
```

#### 2. 更新环境变量

```bash
# .env
SECRET_KEY=new-key-here
OLD_SECRET_KEYS=old-key-1,old-key-2,old-key-3
```

#### 3. 重启应用

```bash
# Docker
docker-compose restart backend

# 或直接重启
./start.sh
```

#### 4. 验证

```bash
# 检查新Token使用新密钥
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 验证旧Token仍可使用
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <old-token>"
```

#### 5. 通知用户（可选）

- 发送邮件通知用户重新登录
- 在应用中显示提示
- 30天后旧Token自动失效

### 自动轮转（生产环境）

#### 使用cron定时任务

```bash
# 每90天自动轮转
0 0 1 */3 * /app/scripts/rotate_secret_cron.sh
```

#### rotate_secret_cron.sh

```bash
#!/bin/bash
set -e

# 生成新密钥
NEW_KEY=$(python scripts/manage_secrets.py generate | grep "^[A-Za-z0-9_-]" | head -1)

# 更新密钥管理服务（如AWS Secrets Manager）
aws secretsmanager rotate-secret --secret-id pms/production/secret-key

# 发送通知
curl -X POST "https://api.slack.com/webhook" \
  -d '{"text": "密钥已轮转，请在30天内提醒用户重新登录"}'

# 记录日志
echo "$(date): 密钥轮转成功" >> /var/log/secret-rotation.log
```

---

## 环境隔离

### 为不同环境使用不同密钥

```bash
# 开发环境 (.env.dev)
SECRET_KEY=dev-key-here

# 测试环境 (.env.test)
SECRET_KEY=test-key-here

# 生产环境 (.env.prod)
SECRET_KEY=prod-key-here
```

### 禁止跨环境共享密钥

❌ **错误示例**:
```bash
# 所有环境使用同一个密钥
SECRET_KEY=same-key-everywhere  # 危险!
```

✅ **正确示例**:
```bash
# 每个环境独立密钥
# 开发
SECRET_KEY=dev-nGZJK8VFx_Qj...

# 生产
SECRET_KEY=prod-xYzAB9cDe_Fg...
```

---

## 访问控制

### 谁应该有权访问密钥

✅ **允许**:
- DevOps工程师（生产部署）
- 系统管理员（紧急情况）
- CI/CD系统（自动部署）

❌ **禁止**:
- 开发人员（除非必要）
- 外部承包商
- 第三方服务

### IAM策略示例（AWS）

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:region:account-id:secret:pms/production/secret-key-*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": ["10.0.0.0/16"]  # 限制IP范围
        }
      }
    }
  ]
}
```

### 最小权限原则

```yaml
# 应用只需要读取权限
permissions:
  - secretsmanager:GetSecretValue

# 不应该有写权限
# ❌ secretsmanager:PutSecretValue
# ❌ secretsmanager:DeleteSecret
```

---

## 审计和监控

### 记录密钥访问

```python
import logging

logger = logging.getLogger(__name__)

def load_secret():
    logger.info("加载SECRET_KEY", extra={
        "user": os.getenv("USER"),
        "timestamp": datetime.now().isoformat(),
        "source": "environment"
    })
    # 注意: 永远不要记录密钥本身!
```

### 监控指标

- 密钥访问频率
- 密钥轮转日期
- Token验证失败次数
- 使用旧密钥验证次数

### 告警规则

```yaml
alerts:
  - name: OldKeyUsageHigh
    condition: old_key_usage > 1000/hour
    action: notify_admin
    message: "旧密钥使用过多，建议提醒用户重新登录"
  
  - name: SecretKeyNotRotated
    condition: days_since_rotation > 90
    action: notify_admin
    message: "密钥超过90天未轮转"
  
  - name: TokenVerificationFailures
    condition: failures > 100/minute
    action: notify_security
    message: "Token验证失败过多，可能受到攻击"
```

---

## 常见错误

### 1. 密钥泄露到Git

❌ **问题**:
```bash
git log --all --full-history -- .env
# 发现 .env 被提交到历史记录
```

✅ **解决方案**:
```bash
# 1. 从历史记录中删除
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 2. 强制推送
git push origin --force --all

# 3. 立即轮转密钥
python scripts/manage_secrets.py rotate

# 4. 通知所有团队成员
```

### 2. 密钥太短

❌ **问题**:
```python
SECRET_KEY = "12345678"  # 只有8字符
```

✅ **解决方案**:
```bash
python scripts/manage_secrets.py generate
# 使用生成的43字符密钥
```

### 3. 在日志中暴露密钥

❌ **问题**:
```python
logging.error(f"Invalid SECRET_KEY: {settings.SECRET_KEY}")
```

✅ **解决方案**:
```python
logging.error(f"Invalid SECRET_KEY: {settings.SECRET_KEY[:5]}***")
# 只记录部分内容
```

### 4. 没有轮转密钥

❌ **问题**:
```bash
# 密钥已使用3年未更换
```

✅ **解决方案**:
```bash
# 立即轮转
python scripts/manage_secrets.py rotate

# 设置定期提醒
echo "0 0 1 */3 * /app/scripts/rotate_secret_cron.sh" | crontab -
```

### 5. 共享密钥给不该有权限的人

❌ **问题**:
```
开发者: "能把生产环境的SECRET_KEY发我吗？"
管理员: "好的，密钥是: xxx..."  # 危险!
```

✅ **解决方案**:
```
管理员: "请提交工单说明使用原因，审批后通过密钥管理系统获取"
```

---

## 检查清单

### 开发环境

- [ ] ✅ 使用CLI工具生成密钥
- [ ] ✅ 密钥长度≥32字符
- [ ] ✅ .env文件已添加到.gitignore
- [ ] ✅ 每个开发者使用独立密钥
- [ ] ✅ 定期（30天）轮转密钥

### 生产环境

- [ ] ✅ 使用Docker Secrets或云端密钥管理
- [ ] ✅ 密钥长度≥43字符
- [ ] ✅ 启用密钥轮转（90天周期）
- [ ] ✅ 配置访问控制（最小权限）
- [ ] ✅ 启用审计日志
- [ ] ✅ 配置告警规则
- [ ] ✅ 不同环境使用不同密钥
- [ ] ✅ 备份密钥（加密存储）
- [ ] ✅ 建立密钥泄露应急预案

### 团队协作

- [ ] ✅ 团队成员了解密钥管理政策
- [ ] ✅ 定期安全培训
- [ ] ✅ 密钥访问权限定期审查
- [ ] ✅ 员工离职时立即轮转密钥
- [ ] ✅ 建立密钥管理文档

---

## 相关文档

- [密钥轮转操作手册](./secret-rotation-manual.md)
- [云端密钥管理集成指南](./secret-management-cloud-integration.md)
- [安全事件应急响应](./security-incident-response.md)

---

## 参考资料

- [OWASP 密钥管理备忘单](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [NIST 密钥管理指南](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [AWS Secrets Manager 最佳实践](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [12-Factor App: 配置](https://12factor.net/config)
