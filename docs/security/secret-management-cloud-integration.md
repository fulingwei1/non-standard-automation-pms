# 云端密钥管理集成指南

本指南介绍如何将应用与主流云端密钥管理服务集成。

## 📋 目录

- [为什么使用云端密钥管理](#为什么使用云端密钥管理)
- [AWS Secrets Manager](#aws-secrets-manager)
- [Azure Key Vault](#azure-key-vault)
- [Google Secret Manager](#google-secret-manager)
- [HashiCorp Vault](#hashicorp-vault)
- [对比和选择](#对比和选择)

---

## 为什么使用云端密钥管理

### 优势

✅ **集中管理**: 所有密钥在一个地方管理  
✅ **自动轮转**: 定期自动更换密钥  
✅ **访问控制**: 精细的IAM权限管理  
✅ **审计日志**: 完整的访问记录  
✅ **高可用**: 云服务保证99.9%+可用性  
✅ **加密存储**: 密钥本身也被加密  
✅ **版本控制**: 保留密钥历史版本

### 适用场景

- 生产环境部署
- 多环境管理（dev/staging/prod）
- 合规要求（PCI DSS, HIPAA等）
- 多区域部署
- 团队协作

---

## AWS Secrets Manager

### 特点

- **完全托管**: 无需维护基础设施
- **自动轮转**: 内置Lambda轮转
- **与AWS服务集成**: EC2, ECS, Lambda等
- **价格**: $0.40/密钥/月 + $0.05/10k API调用

### 设置步骤

#### 1. 创建密钥

```bash
# 使用AWS CLI创建密钥
aws secretsmanager create-secret \
  --name pms/production/secret-key \
  --description "PMS应用SECRET_KEY" \
  --secret-string '{
    "current_key": "your-secret-key-here",
    "old_keys": [],
    "rotation_date": "2025-02-15T00:00:00Z"
  }'
```

#### 2. 配置IAM权限

创建IAM策略 `pms-secrets-read.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:pms/production/secret-key-*"
    }
  ]
}
```

应用策略:

```bash
# 创建策略
aws iam create-policy \
  --policy-name PMSSecretsRead \
  --policy-document file://pms-secrets-read.json

# 附加到EC2实例角色
aws iam attach-role-policy \
  --role-name EC2-PMS-Backend \
  --policy-arn arn:aws:iam::123456789012:policy/PMSSecretsRead
```

#### 3. 集成代码

创建 `app/core/aws_secrets_integration.py`:

```python
# -*- coding: utf-8 -*-
"""AWS Secrets Manager 集成"""

import boto3
import json
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class AWSSecretsManager:
    """AWS Secrets Manager 客户端"""
    
    def __init__(self, secret_name: str, region: str = 'us-east-1'):
        self.secret_name = secret_name
        self.region = region
        self.client = boto3.client('secretsmanager', region_name=region)
    
    @lru_cache(maxsize=1)
    def get_secret(self, cache_ttl: int = 300) -> Dict[str, Any]:
        """获取密钥（带缓存）
        
        Args:
            cache_ttl: 缓存时间（秒），默认5分钟
        
        Returns:
            密钥字典
        """
        try:
            response = self.client.get_secret_value(SecretId=self.secret_name)
            secret_string = response['SecretString']
            return json.loads(secret_string)
        except Exception as e:
            logger.error(f"从AWS Secrets Manager获取密钥失败: {e}")
            raise
    
    def get_current_key(self) -> str:
        """获取当前密钥"""
        secret = self.get_secret()
        return secret['current_key']
    
    def get_old_keys(self) -> list:
        """获取旧密钥列表"""
        secret = self.get_secret()
        return secret.get('old_keys', [])
    
    def rotate_secret(self, new_key: str) -> None:
        """轮转密钥
        
        Args:
            new_key: 新密钥
        """
        from datetime import datetime
        
        # 获取当前配置
        current_secret = self.get_secret()
        current_key = current_secret['current_key']
        old_keys = current_secret.get('old_keys', [])
        
        # 构建新配置
        new_secret = {
            'current_key': new_key,
            'old_keys': [current_key] + old_keys[:2],  # 保留最近3个
            'rotation_date': datetime.utcnow().isoformat()
        }
        
        # 更新密钥
        try:
            self.client.put_secret_value(
                SecretId=self.secret_name,
                SecretString=json.dumps(new_secret)
            )
            
            # 清除缓存
            self.get_secret.cache_clear()
            
            logger.info(f"AWS Secrets Manager密钥轮转成功")
        except Exception as e:
            logger.error(f"轮转密钥失败: {e}")
            raise


# 使用示例
def load_secret_from_aws():
    """从AWS Secrets Manager加载密钥"""
    import os
    
    if not os.getenv('AWS_SECRETS_MANAGER_ENABLED'):
        return None
    
    secret_name = os.getenv('AWS_SECRET_NAME', 'pms/production/secret-key')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    manager = AWSSecretsManager(secret_name, region)
    return manager.get_current_key()
```

#### 4. 更新配置加载

修改 `app/core/secret_manager.py`:

```python
def load_keys_from_env(self) -> None:
    """从环境变量或AWS加载密钥"""
    
    # 1. 尝试从AWS Secrets Manager加载
    if os.getenv('AWS_SECRETS_MANAGER_ENABLED') == 'true':
        from app.core.aws_secrets_integration import load_secret_from_aws
        self.current_key = load_secret_from_aws()
        if self.current_key:
            logger.info("从AWS Secrets Manager加载密钥成功")
            return
    
    # 2. 从文件加载（Docker Secrets）
    # ... 现有代码 ...
```

#### 5. 环境变量配置

```bash
# .env (生产环境)
AWS_SECRETS_MANAGER_ENABLED=true
AWS_SECRET_NAME=pms/production/secret-key
AWS_REGION=us-east-1
```

#### 6. 配置自动轮转

创建Lambda函数 `lambda/rotate_secret.py`:

```python
import boto3
import json
import secrets
from datetime import datetime

def lambda_handler(event, context):
    """Lambda函数：自动轮转密钥"""
    
    secret_name = 'pms/production/secret-key'
    client = boto3.client('secretsmanager')
    
    # 生成新密钥
    new_key = secrets.token_urlsafe(32)
    
    # 获取当前密钥
    response = client.get_secret_value(SecretId=secret_name)
    current_secret = json.loads(response['SecretString'])
    
    # 构建新配置
    new_secret = {
        'current_key': new_key,
        'old_keys': [current_secret['current_key']] + current_secret.get('old_keys', [])[:2],
        'rotation_date': datetime.utcnow().isoformat()
    }
    
    # 更新密钥
    client.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps(new_secret)
    )
    
    # 触发ECS服务更新
    ecs = boto3.client('ecs')
    ecs.update_service(
        cluster='pms-production',
        service='backend',
        forceNewDeployment=True
    )
    
    return {'statusCode': 200, 'body': '密钥轮转成功'}
```

设置EventBridge规则:

```bash
# 每90天轮转一次
aws events put-rule \
  --name pms-secret-rotation \
  --schedule-expression "rate(90 days)"

aws events put-targets \
  --rule pms-secret-rotation \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:rotate-secret"
```

---

## Azure Key Vault

### 特点

- **与Azure集成**: VM, App Service, AKS等
- **访问策略**: 基于角色的访问控制
- **软删除**: 防止意外删除
- **价格**: $0.03/10k操作

### 设置步骤

#### 1. 创建Key Vault

```bash
# 使用Azure CLI
az keyvault create \
  --name pms-keyvault \
  --resource-group pms-production \
  --location eastus
```

#### 2. 添加密钥

```bash
az keyvault secret set \
  --vault-name pms-keyvault \
  --name secret-key \
  --value "your-secret-key-here"
```

#### 3. 配置访问策略

```bash
# 授予VM访问权限
az keyvault set-policy \
  --name pms-keyvault \
  --object-id <vm-identity-object-id> \
  --secret-permissions get list
```

#### 4. 集成代码

创建 `app/core/azure_keyvault_integration.py`:

```python
# -*- coding: utf-8 -*-
"""Azure Key Vault 集成"""

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class AzureKeyVaultManager:
    """Azure Key Vault 客户端"""
    
    def __init__(self, vault_url: str):
        self.vault_url = vault_url
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)
    
    @lru_cache(maxsize=1)
    def get_secret(self, secret_name: str) -> str:
        """获取密钥（带缓存）"""
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.error(f"从Azure Key Vault获取密钥失败: {e}")
            raise
    
    def get_current_key(self) -> str:
        """获取当前密钥"""
        return self.get_secret("secret-key")
    
    def rotate_secret(self, new_key: str) -> None:
        """轮转密钥"""
        try:
            # 保存旧密钥
            old_key = self.get_current_key()
            self.client.set_secret("secret-key-old-1", old_key)
            
            # 更新当前密钥
            self.client.set_secret("secret-key", new_key)
            
            # 清除缓存
            self.get_secret.cache_clear()
            
            logger.info("Azure Key Vault密钥轮转成功")
        except Exception as e:
            logger.error(f"轮转密钥失败: {e}")
            raise


# 使用示例
def load_secret_from_azure():
    """从Azure Key Vault加载密钥"""
    import os
    
    if not os.getenv('AZURE_KEYVAULT_ENABLED'):
        return None
    
    vault_url = os.getenv('AZURE_KEYVAULT_URL')
    if not vault_url:
        logger.error("未设置AZURE_KEYVAULT_URL")
        return None
    
    manager = AzureKeyVaultManager(vault_url)
    return manager.get_current_key()
```

#### 5. 环境变量配置

```bash
# .env
AZURE_KEYVAULT_ENABLED=true
AZURE_KEYVAULT_URL=https://pms-keyvault.vault.azure.net/
```

---

## Google Secret Manager

### 特点

- **全球分布**: 多区域复制
- **自动加密**: 默认加密存储
- **IAM集成**: 精细的权限控制
- **价格**: $0.06/10k访问

### 设置步骤

#### 1. 创建密钥

```bash
# 使用gcloud CLI
echo -n "your-secret-key-here" | \
  gcloud secrets create secret-key \
    --data-file=- \
    --replication-policy=automatic
```

#### 2. 配置IAM

```bash
# 授予服务账号访问权限
gcloud secrets add-iam-policy-binding secret-key \
  --member="serviceAccount:pms-backend@project-id.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### 3. 集成代码

创建 `app/core/gcp_secret_integration.py`:

```python
# -*- coding: utf-8 -*-
"""Google Secret Manager 集成"""

from google.cloud import secretmanager
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class GCPSecretManager:
    """Google Secret Manager 客户端"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
    
    @lru_cache(maxsize=1)
    def get_secret(self, secret_id: str, version: str = 'latest') -> str:
        """获取密钥（带缓存）"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.error(f"从Google Secret Manager获取密钥失败: {e}")
            raise
    
    def get_current_key(self) -> str:
        """获取当前密钥"""
        return self.get_secret("secret-key")
    
    def rotate_secret(self, new_key: str) -> None:
        """轮转密钥"""
        try:
            parent = f"projects/{self.project_id}/secrets/secret-key"
            
            # 添加新版本
            self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": new_key.encode('UTF-8')}
                }
            )
            
            # 清除缓存
            self.get_secret.cache_clear()
            
            logger.info("Google Secret Manager密钥轮转成功")
        except Exception as e:
            logger.error(f"轮转密钥失败: {e}")
            raise


# 使用示例
def load_secret_from_gcp():
    """从Google Secret Manager加载密钥"""
    import os
    
    if not os.getenv('GCP_SECRET_MANAGER_ENABLED'):
        return None
    
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        logger.error("未设置GCP_PROJECT_ID")
        return None
    
    manager = GCPSecretManager(project_id)
    return manager.get_current_key()
```

---

## HashiCorp Vault

### 特点

- **自建或托管**: HCP Vault（托管）或自建
- **动态密钥**: 可以生成临时密钥
- **多后端**: 支持多种存储后端
- **价格**: 开源免费，企业版需授权

### 设置步骤

#### 1. 安装Vault

```bash
# Docker方式
docker run -d --name=vault \
  --cap-add=IPC_LOCK \
  -p 8200:8200 \
  vault server -dev
```

#### 2. 初始化

```bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='<root-token>'

# 启用KV v2引擎
vault secrets enable -path=secret kv-v2
```

#### 3. 存储密钥

```bash
vault kv put secret/pms/production \
  current_key="your-secret-key-here" \
  old_keys="old-key-1,old-key-2"
```

#### 4. 集成代码

创建 `app/core/vault_integration.py`:

```python
# -*- coding: utf-8 -*-
"""HashiCorp Vault 集成"""

import hvac
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class VaultManager:
    """Vault 客户端"""
    
    def __init__(self, url: str, token: str):
        self.client = hvac.Client(url=url, token=token)
        
        if not self.client.is_authenticated():
            raise ValueError("Vault认证失败")
    
    @lru_cache(maxsize=1)
    def get_secret(self, path: str) -> dict:
        """获取密钥（带缓存）"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point='secret'
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"从Vault获取密钥失败: {e}")
            raise
    
    def get_current_key(self) -> str:
        """获取当前密钥"""
        secret = self.get_secret("pms/production")
        return secret['current_key']
    
    def get_old_keys(self) -> list:
        """获取旧密钥"""
        secret = self.get_secret("pms/production")
        old_keys_str = secret.get('old_keys', '')
        return [k.strip() for k in old_keys_str.split(',') if k.strip()]


# 使用示例
def load_secret_from_vault():
    """从Vault加载密钥"""
    import os
    
    if not os.getenv('VAULT_ENABLED'):
        return None
    
    vault_url = os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200')
    vault_token = os.getenv('VAULT_TOKEN')
    
    if not vault_token:
        logger.error("未设置VAULT_TOKEN")
        return None
    
    manager = VaultManager(vault_url, vault_token)
    return manager.get_current_key()
```

---

## 对比和选择

### 功能对比

| 功能 | AWS Secrets Manager | Azure Key Vault | Google Secret Manager | HashiCorp Vault |
|------|---------------------|-----------------|----------------------|-----------------|
| **自动轮转** | ✅ | ⚠️ (手动) | ⚠️ (手动) | ✅ |
| **多区域复制** | ✅ | ✅ | ✅ | ✅ (企业版) |
| **IAM集成** | ✅ | ✅ | ✅ | ✅ |
| **审计日志** | ✅ | ✅ | ✅ | ✅ |
| **价格** | $0.40/月 | $0.03/10k | $0.06/10k | 免费/企业版 |
| **易用性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### 选择建议

**AWS Secrets Manager** - 如果你的基础设施在AWS  
**Azure Key Vault** - 如果你的基础设施在Azure  
**Google Secret Manager** - 如果你的基础设施在GCP  
**HashiCorp Vault** - 如果你需要多云或混合云

### 成本估算

#### AWS Secrets Manager

```
每月成本 = $0.40 + ($0.05 × API调用次数 / 10000)

示例（100万次调用/月）:
$0.40 + ($0.05 × 1000000 / 10000) = $5.40/月
```

#### Azure Key Vault

```
每月成本 = $0.03 × API调用次数 / 10000

示例（100万次调用/月）:
$0.03 × 1000000 / 10000 = $3.00/月
```

#### Google Secret Manager

```
每月成本 = $0.06 × API调用次数 / 10000

示例（100万次调用/月）:
$0.06 × 1000000 / 10000 = $6.00/月
```

---

## 最佳实践

### 1. 使用缓存

```python
# 缓存密钥，减少API调用
@lru_cache(maxsize=1, ttl=300)  # 5分钟缓存
def get_secret_key():
    return secret_manager.get_current_key()
```

### 2. 错误处理

```python
try:
    secret_key = secret_manager.get_current_key()
except Exception as e:
    # 降级到本地密钥
    logger.warning(f"云端密钥获取失败，使用本地密钥: {e}")
    secret_key = os.getenv('SECRET_KEY_FALLBACK')
```

### 3. 多区域部署

```python
# 优先使用本区域密钥
regions = ['us-east-1', 'us-west-2', 'eu-west-1']
for region in regions:
    try:
        return get_secret_from_region(region)
    except:
        continue
```

### 4. 定期审计

```bash
# AWS CloudTrail查询
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=pms/production/secret-key \
  --max-results 100
```

---

## 迁移指南

### 从本地迁移到AWS

```bash
# 1. 创建密钥
CURRENT_KEY=$(grep SECRET_KEY .env | cut -d'=' -f2)
aws secretsmanager create-secret \
  --name pms/production/secret-key \
  --secret-string "{\"current_key\":\"$CURRENT_KEY\",\"old_keys\":[]}"

# 2. 更新代码
# (添加AWS集成代码)

# 3. 更新环境变量
# 删除: SECRET_KEY=...
# 添加: AWS_SECRETS_MANAGER_ENABLED=true

# 4. 重启应用
docker-compose restart backend

# 5. 验证
python scripts/verify_aws_integration.py
```

---

## 故障排除

### AWS: 权限不足

```bash
# 检查IAM角色
aws sts get-caller-identity

# 检查权限
aws iam simulate-principal-policy \
  --policy-source-arn <role-arn> \
  --action-names secretsmanager:GetSecretValue \
  --resource-arns <secret-arn>
```

### Azure: 认证失败

```bash
# 检查托管身份
az vm identity show --name pms-vm --resource-group pms

# 测试访问
az keyvault secret show --vault-name pms-keyvault --name secret-key
```

---

## 相关文档

- [密钥管理最佳实践](./secret-management-best-practices.md)
- [密钥轮转操作手册](./secret-rotation-manual.md)

---

## 参考资料

- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [Azure Key Vault](https://docs.microsoft.com/azure/key-vault/)
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [HashiCorp Vault](https://www.vaultproject.io/docs)
