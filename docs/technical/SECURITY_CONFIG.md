# 安全配置说明

## 环境变量配置

应用启动前，必须配置以下环境变量。建议创建 `.env` 文件（不会被提交到版本控制）。

### 必须配置的环境变量

#### 1. SECRET_KEY
JWT密钥，用于签名和验证token。**必须设置，不允许使用默认值**。

**生成方式：**
```bash
# 使用 OpenSSL 生成
openssl rand -base64 42

# 或使用 Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**配置示例：**
```bash
export SECRET_KEY="your-generated-secret-key-here"
```

#### 2. CORS_ORIGINS
CORS允许的来源，多个用逗号分隔。**必须设置，不允许使用默认值**。

**配置示例：**
```bash
# 开发环境
export CORS_ORIGINS="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

# 生产环境（只配置实际的前端域名）
export CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

### 推荐配置的环境变量

#### 3. REDIS_URL
Redis连接URL，用于Token黑名单等功能。

**配置示例：**
```bash
# 本地Redis
export REDIS_URL="redis://localhost:6379/0"

# 带密码的Redis
export REDIS_URL="redis://:password@localhost:6379/0"

# 远程Redis
export REDIS_URL="redis://username:password@redis.example.com:6379/0"
```

**注意：** 如果不配置Redis，Token黑名单将使用内存存储，应用重启后黑名单会清空。

### 完整配置示例

创建 `.env` 文件：

```bash
# 安全配置（必须）
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Redis配置（推荐）
REDIS_URL=redis://localhost:6379/0

# 可选配置
DEBUG=False
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## 安全改进说明

### 1. SECRET_KEY 安全修复
- ✅ 移除了硬编码的默认值
- ✅ 必须从环境变量读取
- ✅ 启动时如果没有配置会显示明确的错误提示

### 2. CORS 来源限制
- ✅ 移除了DEBUG模式下的通配符 `*`
- ✅ 必须明确配置允许的来源
- ✅ 支持从环境变量读取逗号分隔的字符串

### 3. 依赖版本固定
- ✅ 所有依赖包都已固定到具体版本
- ✅ 确保部署环境的一致性
- ✅ 便于安全更新和回滚

### 4. Redis Token 黑名单
- ✅ 使用Redis存储Token黑名单，支持分布式部署
- ✅ 自动设置过期时间，与token过期时间一致
- ✅ Redis不可用时自动降级到内存存储
- ✅ 使用JTI (JWT ID) 作为键，提高效率

## 部署检查清单

在部署到生产环境前，请确认：

- [ ] SECRET_KEY 已设置为强随机字符串
- [ ] CORS_ORIGINS 只包含实际的前端域名
- [ ] REDIS_URL 已配置（推荐）
- [ ] 所有依赖版本已固定（requirements.txt）
- [ ] 环境变量通过安全方式管理（不使用硬编码）
- [ ] 生产环境 DEBUG=False

## 故障排查

### 启动时提示缺少环境变量

如果看到以下错误：
```
配置错误：缺少必要的环境变量
请设置以下环境变量：
  - SECRET_KEY: JWT密钥（必须）
  - CORS_ORIGINS: CORS允许的来源，多个用逗号分隔（必须）
```

**解决方法：**
1. 创建 `.env` 文件并配置上述变量
2. 或通过环境变量直接设置：
   ```bash
   export SECRET_KEY="your-secret-key"
   export CORS_ORIGINS="http://localhost:5173"
   ```

### Redis连接失败

如果看到警告：
```
Redis连接失败: ...，Token黑名单将使用内存存储（重启后失效）
```

**解决方法：**
1. 检查Redis服务是否运行
2. 检查REDIS_URL配置是否正确
3. 检查网络连接和防火墙设置

**注意：** Redis连接失败不会阻止应用启动，但Token黑名单功能会降级到内存存储。


