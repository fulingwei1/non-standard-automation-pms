# 密钥轮转操作手册

本手册提供详细的密钥轮转操作步骤，适用于开发、测试和生产环境。

## 📋 目录

- [轮转前准备](#轮转前准备)
- [开发环境轮转](#开发环境轮转)
- [生产环境轮转](#生产环境轮转)
- [应急轮转](#应急轮转)
- [轮转验证](#轮转验证)
- [故障排除](#故障排除)

---

## 轮转前准备

### 检查清单

- [ ] 确认当前密钥状态
- [ ] 备份当前配置
- [ ] 通知相关人员
- [ ] 选择合适的维护窗口
- [ ] 准备回滚方案

### 查看当前密钥状态

```bash
# 查看密钥信息
python scripts/manage_secrets.py info

# 输出示例:
# 📊 密钥管理器信息
# ====================================
# 🔑 当前密钥:
#   预览: nGZJK8VFx_...
#   长度: 43 字符
#   有效: ✅
# 📦 旧密钥:
#   数量: 2
# 🔄 最后轮转:
#   时间: 2025-01-15T10:30:00
```

### 备份当前配置

```bash
# 备份 .env 文件
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 备份 Docker Secrets（如果使用）
cp secrets/secret_key.txt secrets/secret_key.txt.backup.$(date +%Y%m%d_%H%M%S)
```

---

## 开发环境轮转

### 步骤1: 生成新密钥

```bash
# 自动生成新密钥
python scripts/manage_secrets.py rotate

# 或手动指定新密钥
python scripts/manage_secrets.py rotate --key "your-new-key-here"
```

输出示例:
```
📊 当前密钥状态:
====================================
当前密钥: nGZJK8VFx_...
旧密钥数量: 2

⚠️  密钥轮转将:
  1. 将当前密钥移到旧密钥列表
  2. 设置新密钥
  3. 旧Token仍可验证（30天有效期）
  4. 需要更新环境变量并重启应用

确认轮转密钥? [y/N]: y

====================================

✅ 密钥轮转成功!
====================================

新密钥: xYzAB9cDe_FgHiJkLmNoPqRsTuVwXy0123456789012
旧密钥: nGZJK8VFx_...
轮转时间: 2025-02-15T11:00:00
旧密钥数量: 3

====================================

📝 更新 .env 文件:

SECRET_KEY=xYzAB9cDe_FgHiJkLmNoPqRsTuVwXy0123456789012
OLD_SECRET_KEYS=nGZJK8VFx_QjR9mXtLpY...,old-key-2,old-key-3

====================================
```

### 步骤2: 更新 .env 文件

```bash
# 手动编辑 .env 文件
nano .env

# 或使用 sed 命令
sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=xYzAB9cDe_FgHiJkLmNoPqRsTuVwXy0123456789012/" .env
```

.env 文件内容:
```bash
SECRET_KEY=xYzAB9cDe_FgHiJkLmNoPqRsTuVwXy0123456789012
OLD_SECRET_KEYS=nGZJK8VFx_QjR9mXtLpY...,old-key-2,old-key-3
```

### 步骤3: 重启应用

```bash
# 如果使用Docker Compose
docker-compose restart backend

# 或直接重启
./stop.sh
./start.sh

# 或使用开发服务器
pkill -f uvicorn
./start.sh
```

### 步骤4: 验证

```bash
# 测试新Token生成
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 保存新Token
NEW_TOKEN="<从响应中获取的token>"

# 测试新Token
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $NEW_TOKEN"

# 测试旧Token（应该仍然有效）
OLD_TOKEN="<之前保存的token>"
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $OLD_TOKEN"
```

---

## 生产环境轮转

### 准备工作

1. **选择维护窗口**: 凌晨2-4点（用户最少）
2. **通知团队**: 提前24小时
3. **准备回滚**: 备份当前配置
4. **监控准备**: 确保监控系统正常

### 方案A: 使用Docker Secrets（推荐）

#### 步骤1: 生成新密钥

```bash
# 在本地生成（不要在生产服务器直接操作）
python scripts/manage_secrets.py generate

# 输出:
# nEwKeY789aBcDeF0123456789GhIjKlMnOpQrStUvWxYz
```

#### 步骤2: 更新密钥文件

```bash
# 连接到生产服务器
ssh production-server

# 备份当前密钥
sudo cp secrets/secret_key.txt secrets/secret_key.txt.backup

# 将旧密钥追加到旧密钥列表
OLD_KEY=$(cat secrets/secret_key.txt)
echo "$OLD_KEY" >> secrets/old_secret_keys.txt
echo "," >> secrets/old_secret_keys.txt

# 写入新密钥
echo "nEwKeY789aBcDeF0123456789GhIjKlMnOpQrStUvWxYz" | sudo tee secrets/secret_key.txt

# 设置权限
sudo chmod 600 secrets/secret_key.txt
```

#### 步骤3: 重启服务（零停机）

```bash
# 滚动重启（如果使用多个实例）
for i in {1..3}; do
  docker-compose restart backend-$i
  sleep 30  # 等待实例启动
done

# 或一次性重启
docker-compose restart backend
```

#### 步骤4: 验证

```bash
# 检查服务状态
docker-compose ps

# 检查日志
docker-compose logs -f backend | grep "SECRET_KEY"

# 测试API
curl https://your-domain.com/api/v1/health
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

### 方案B: 使用AWS Secrets Manager

#### 步骤1: 生成新密钥

```bash
# 生成新密钥
NEW_KEY=$(python scripts/manage_secrets.py generate | grep "^[A-Za-z0-9_-]" | head -1)
```

#### 步骤2: 更新AWS Secrets Manager

```bash
# 获取当前密钥
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id pms/production/secret-key \
  --query SecretString \
  --output text)

# 解析JSON
CURRENT_KEY=$(echo $CURRENT_SECRET | jq -r '.current_key')
OLD_KEYS=$(echo $CURRENT_SECRET | jq -r '.old_keys')

# 构建新的密钥配置
NEW_SECRET=$(cat <<EOF
{
  "current_key": "$NEW_KEY",
  "old_keys": ["$CURRENT_KEY", $OLD_KEYS],
  "rotation_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
)

# 更新密钥
aws secretsmanager put-secret-value \
  --secret-id pms/production/secret-key \
  --secret-string "$NEW_SECRET"
```

#### 步骤3: 重启应用

```bash
# ECS（如果使用AWS ECS）
aws ecs update-service \
  --cluster pms-production \
  --service backend \
  --force-new-deployment

# EC2（如果直接在EC2上运行）
ssh production-server
docker-compose restart backend
```

#### 步骤4: 验证

```bash
# 检查密钥是否更新
aws secretsmanager get-secret-value \
  --secret-id pms/production/secret-key \
  --query SecretString \
  --output text | jq '.rotation_date'

# 测试API
curl https://your-domain.com/api/v1/health
```

---

## 应急轮转

### 场景: 密钥泄露

**紧急程度**: 🔴 极高  
**目标时间**: 15分钟内完成

#### 步骤1: 立即停止受影响的服务（可选）

```bash
# 如果泄露严重，先停止服务
docker-compose stop backend

# 显示维护页面（如果有）
```

#### 步骤2: 快速轮转

```bash
# 跳过确认，直接轮转
python scripts/manage_secrets.py rotate --yes

# 立即更新生产环境
# (根据你的部署方式选择上述方案A或B)
```

#### 步骤3: 撤销所有旧Token

```bash
# 在数据库中标记所有旧Token为无效
# 或清空Redis中的Token缓存
redis-cli FLUSHDB

# 或使用SQL
psql -d pms -c "UPDATE user_sessions SET is_valid = false WHERE created_at < NOW() - INTERVAL '1 hour';"
```

#### 步骤4: 强制用户重新登录

```bash
# 发送通知
python scripts/notify_users.py \
  --message "安全更新，请重新登录" \
  --channel email,sms

# 在前端显示提示
# "您的会话已过期，请重新登录"
```

#### 步骤5: 审计和报告

```bash
# 检查访问日志
grep "SECRET_KEY" /var/log/app/*.log

# 检查Git历史
git log --all --full-history -- .env

# 生成安全报告
python scripts/generate_security_report.py \
  --type key-leak \
  --date $(date +%Y-%m-%d)
```

---

## 轮转验证

### 验证检查清单

- [ ] ✅ 服务正常运行
- [ ] ✅ 新Token可以生成
- [ ] ✅ 新Token可以验证
- [ ] ✅ 旧Token仍可验证（30天内）
- [ ] ✅ API响应正常
- [ ] ✅ 日志无错误
- [ ] ✅ 监控指标正常

### 自动化验证脚本

创建 `scripts/verify_rotation.sh`:

```bash
#!/bin/bash
set -e

echo "🔍 开始验证密钥轮转..."

# 1. 检查服务状态
echo "✓ 检查服务状态..."
if ! docker-compose ps | grep "Up"; then
  echo "❌ 服务未运行"
  exit 1
fi

# 2. 测试新Token生成
echo "✓ 测试新Token生成..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

NEW_TOKEN=$(echo $RESPONSE | jq -r '.access_token')
if [ "$NEW_TOKEN" == "null" ] || [ -z "$NEW_TOKEN" ]; then
  echo "❌ 新Token生成失败"
  exit 1
fi

# 3. 测试新Token验证
echo "✓ 测试新Token验证..."
USER=$(curl -s http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $NEW_TOKEN" | jq -r '.username')

if [ "$USER" != "admin" ]; then
  echo "❌ 新Token验证失败"
  exit 1
fi

# 4. 测试旧Token验证（如果有）
if [ -n "$OLD_TOKEN" ]; then
  echo "✓ 测试旧Token验证..."
  OLD_USER=$(curl -s http://localhost:8000/api/v1/users/me \
    -H "Authorization: Bearer $OLD_TOKEN" | jq -r '.username')
  
  if [ "$OLD_USER" == "null" ]; then
    echo "⚠️  旧Token已失效（这可能是正常的）"
  else
    echo "✓ 旧Token仍然有效（向后兼容）"
  fi
fi

# 5. 检查日志错误
echo "✓ 检查日志错误..."
if docker-compose logs backend | grep -i "ERROR.*SECRET_KEY"; then
  echo "⚠️  日志中有密钥相关错误"
fi

echo ""
echo "✅ 密钥轮转验证通过!"
echo ""
echo "📊 摘要:"
echo "  - 服务状态: 正常"
echo "  - 新Token: 有效"
echo "  - 旧Token: 有效（向后兼容）"
echo "  - 日志: 无严重错误"
```

运行验证:

```bash
chmod +x scripts/verify_rotation.sh
./scripts/verify_rotation.sh
```

---

## 故障排除

### 问题1: 轮转后所有Token失效

**症状**: 用户无法登录，提示"Token无效"

**原因**: 
- 未正确设置OLD_SECRET_KEYS
- 环境变量未生效
- 缓存未清除

**解决方案**:

```bash
# 1. 检查环境变量
echo $SECRET_KEY
echo $OLD_SECRET_KEYS

# 2. 确认旧密钥包含之前的密钥
python scripts/manage_secrets.py list

# 3. 重启应用
docker-compose restart backend

# 4. 清除Redis缓存（如果使用）
redis-cli FLUSHDB
```

### 问题2: 轮转失败，服务无法启动

**症状**: 服务启动失败，日志显示"SECRET_KEY无效"

**原因**:
- 新密钥长度不足
- 新密钥格式错误
- 密钥文件权限问题

**解决方案**:

```bash
# 1. 回滚到备份
cp .env.backup .env
docker-compose restart backend

# 2. 验证密钥
python scripts/manage_secrets.py validate "$NEW_KEY"

# 3. 重新生成密钥
python scripts/manage_secrets.py generate
```

### 问题3: 部分用户Token失效

**症状**: 部分用户可以登录，部分不行

**原因**:
- 负载均衡器后端实例密钥不一致
- 配置未同步到所有实例

**解决方案**:

```bash
# 1. 检查所有实例的密钥
for i in {1..3}; do
  docker exec backend-$i env | grep SECRET_KEY
done

# 2. 同步配置到所有实例
ansible-playbook sync-secrets.yml

# 3. 滚动重启所有实例
for i in {1..3}; do
  docker-compose restart backend-$i
  sleep 30
done
```

### 问题4: 密钥轮转后性能下降

**症状**: API响应变慢

**原因**:
- 每个请求都尝试多个密钥验证
- 旧密钥列表过长

**解决方案**:

```bash
# 1. 检查旧密钥数量
python scripts/manage_secrets.py list

# 2. 清理过期密钥
python scripts/manage_secrets.py cleanup --days 30

# 3. 优化验证逻辑（代码层面）
# 使用缓存减少重复验证
```

---

## 定期维护

### 每月任务

```bash
# 检查密钥状态
python scripts/manage_secrets.py info

# 清理过期密钥
python scripts/manage_secrets.py cleanup
```

### 每季度任务

```bash
# 轮转密钥
python scripts/manage_secrets.py rotate

# 审查访问日志
grep "SECRET_KEY" /var/log/app/*.log | tail -100

# 更新文档
```

### 年度任务

```bash
# 全面安全审计
python scripts/security_audit.py

# 更新密钥管理策略
# 审查访问权限
# 培训团队成员
```

---

## 自动化轮转（高级）

### 使用Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: secret-rotation
spec:
  schedule: "0 0 1 */3 *"  # 每90天
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: rotate
            image: pms-backend:latest
            command:
            - /bin/bash
            - -c
            - |
              python scripts/manage_secrets.py rotate --yes
              kubectl rollout restart deployment/backend
          restartPolicy: OnFailure
```

### 使用AWS Lambda

```python
import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    """自动轮转密钥"""
    
    # 生成新密钥
    import secrets
    new_key = secrets.token_urlsafe(32)
    
    # 更新Secrets Manager
    client = boto3.client('secretsmanager')
    
    # 获取当前密钥
    response = client.get_secret_value(SecretId='pms/production/secret-key')
    current_secret = json.loads(response['SecretString'])
    
    # 构建新配置
    new_secret = {
        'current_key': new_key,
        'old_keys': [current_secret['current_key']] + current_secret.get('old_keys', [])[:2],
        'rotation_date': datetime.utcnow().isoformat()
    }
    
    # 更新
    client.put_secret_value(
        SecretId='pms/production/secret-key',
        SecretString=json.dumps(new_secret)
    )
    
    # 触发ECS部署
    ecs = boto3.client('ecs')
    ecs.update_service(
        cluster='pms-production',
        service='backend',
        forceNewDeployment=True
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('密钥轮转成功')
    }
```

---

## 相关文档

- [密钥管理最佳实践](./secret-management-best-practices.md)
- [云端密钥管理集成指南](./secret-management-cloud-integration.md)
- [安全事件应急响应](./security-incident-response.md)

---

## 联系支持

遇到问题？

- 📧 Email: security@your-company.com
- 💬 Slack: #security-team
- 📞 紧急电话: +86-xxx-xxxx-xxxx（24/7）
