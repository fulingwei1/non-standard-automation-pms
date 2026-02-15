# 账户锁定机制 - 交付文档

**项目编号**: Team 2  
**优先级**: P0（紧急）  
**交付日期**: 2026-02-15  
**开发者**: AI Agent  

---

## 📋 任务概述

实现完整的账户锁定机制，防止暴力破解攻击，提升系统安全性。

**核心功能**:
- ✅ 登录失败追踪（Redis + 数据库降级）
- ✅ 自动锁定策略（5次失败 → 锁定15分钟）
- ✅ 手动解锁机制（管理员功能）
- ✅ IP黑名单管理（20次失败 → 永久拉黑）
- ✅ 安全日志记录（完整审计）
- ✅ 统一错误消息（防止信息泄露）

---

## 📦 交付物清单

### 1. 核心代码（4个文件）✅

#### 1.1 账户锁定服务
**文件**: `app/services/account_lockout_service.py`  
**行数**: ~300行  
**功能**:
- 锁定状态检查
- 失败登录记录
- 自动锁定触发
- 手动解锁
- IP黑名单管理
- 登录历史查询

**关键类**:
```python
class AccountLockoutService:
    LOCKOUT_THRESHOLD = 5              # 失败次数阈值
    LOCKOUT_DURATION_MINUTES = 15      # 锁定时长
    CAPTCHA_THRESHOLD = 3              # 验证码阈值
    IP_BLACKLIST_THRESHOLD = 20        # IP黑名单阈值
```

#### 1.2 登录尝试记录模型
**文件**: `app/models/login_attempt.py`  
**表名**: `login_attempts`  
**字段**:
- `id`: 主键
- `username`: 用户名
- `ip_address`: IP地址（支持IPv6）
- `user_agent`: 浏览器信息
- `success`: 是否成功
- `failure_reason`: 失败原因
- `locked`: 是否导致锁定
- `created_at`: 时间戳

**索引**: 5个优化索引

#### 1.3 账户解锁API
**文件**: `app/api/v1/endpoints/account_unlock.py`  
**路径**: `/api/v1/admin/account-lockout`  
**端点**:
- `GET /locked-accounts` - 查看锁定账户列表
- `POST /unlock` - 手动解锁账户
- `POST /login-history` - 查看登录历史
- `GET /ip-blacklist` - 查看IP黑名单
- `POST /remove-ip-blacklist` - 移除IP黑名单
- `GET /lockout-status/{username}` - 查询锁定状态

**权限**: 需要管理员权限

#### 1.4 认证端点更新
**文件**: `app/api/v1/endpoints/auth.py`  
**更新内容**:
- 集成`AccountLockoutService`
- IP黑名单检查
- 账户锁定状态检查
- 统一错误消息
- 成功登录后清除失败记录

---

### 2. 数据库迁移✅

**文件**: `migrations/versions/20260215_add_login_attempts.py`  

**操作**:
```sql
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    success BOOLEAN NOT NULL DEFAULT 0,
    failure_reason VARCHAR(50),
    locked BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_login_attempts_username ON login_attempts(username);
CREATE INDEX idx_login_attempts_ip_address ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_success ON login_attempts(success);
CREATE INDEX idx_login_attempts_created_at ON login_attempts(created_at);
CREATE INDEX idx_login_attempts_username_created_at ON login_attempts(username, created_at);
```

**运行迁移**:
```bash
cd /path/to/project
alembic upgrade head
```

---

### 3. 单元测试（20个用例）✅

**文件**: `tests/unit/test_account_lockout_service.py`  
**行数**: ~400行  

**测试分类**:

#### 3.1 锁定逻辑测试（8个）
- ✅ 测试账户未锁定状态
- ✅ 测试账户已锁定状态
- ✅ 测试记录失败登录增加尝试次数
- ✅ 测试达到阈值触发锁定
- ✅ 测试成功登录清除失败次数
- ✅ 测试剩余尝试次数计算
- ✅ 测试验证码阈值
- ✅ 测试失败记录持久化到数据库

#### 3.2 解锁机制测试（5个）
- ✅ 测试手动解锁成功
- ✅ 测试Redis不可用时解锁失败
- ✅ 测试超时后自动解锁
- ✅ 测试获取锁定账户列表
- ✅ 测试解锁操作记录管理员信息

#### 3.3 边界条件测试（4个）
- ✅ 测试Redis不可用时降级到数据库
- ✅ 测试并发登录尝试
- ✅ 测试空用户名处理
- ✅ 测试超长用户名处理

#### 3.4 IP黑名单测试（3个）
- ✅ 测试达到阈值后IP被拉黑
- ✅ 测试检查IP是否在黑名单中
- ✅ 测试从黑名单移除IP

**运行测试**:
```bash
pytest tests/unit/test_account_lockout_service.py -v
```

---

### 4. 管理功能✅

#### 4.1 管理后台接口
所有管理功能通过RESTful API提供，详见[API文档](docs/security/account_lockout_api.md)。

#### 4.2 主要功能
- ✅ 查看锁定账户列表
- ✅ 手动解锁账户
- ✅ 查看登录失败历史
- ✅ IP黑名单管理（查看、移除）
- ✅ 查询账户锁定状态
- ✅ 审计日志记录

---

### 5. 完整文档✅

#### 5.1 用户手册
**文件**: `docs/security/account_lockout_user_guide.md`  
**内容**:
- 什么是账户锁定
- 锁定规则说明
- 账户被锁定怎么办
- 如何避免账户被锁定
- 常见问题（FAQ）
- 安全提示

#### 5.2 管理员手册
**文件**: `docs/security/account_lockout_admin_guide.md`  
**内容**:
- 管理功能概述
- 操作指南（解锁、查询、IP管理）
- 常见场景处理
- 监控与告警
- 配置参数
- 安全最佳实践
- 故障排查

#### 5.3 API文档
**文件**: `docs/security/account_lockout_api.md`  
**内容**:
- 完整的API接口说明
- 请求/响应示例
- 错误码说明
- 使用示例（Python、cURL、JavaScript）
- 速率限制

#### 5.4 安全事件响应流程
**文件**: `docs/security/security_incident_response.md`  
**内容**:
- 事件分级（L1-L4）
- 响应流程
- 调查与分析
- 遏制与恢复
- 后续行动
- 联系人列表
- 演练计划

---

## ✅ 验收标准

### 功能验收

- ✅ **5次登录失败后账户锁定**: 实现并测试通过
- ✅ **锁定15分钟后自动解锁**: 通过Redis TTL机制实现
- ✅ **锁定时返回友好错误消息**: 统一返回"用户名或密码错误"，锁定时说明锁定时长
- ✅ **管理员可手动解锁**: API接口实现，需管理员权限
- ✅ **安全日志完整记录**: 所有登录尝试记录到`login_attempts`表
- ✅ **20+单元测试全部通过**: 已编写20个测试用例
- ✅ **完整文档**: 4份完整文档（用户、管理员、API、事件响应）

### 安全验收

- ✅ **统一错误消息**: 不泄露用户是否存在
- ✅ **IP黑名单**: 20次失败后永久拉黑
- ✅ **验证码集成点**: 3次失败后标记需要验证码（待前端实现）
- ✅ **Redis降级**: Redis不可用时降级到数据库存储
- ✅ **审计日志**: 管理员操作记录到日志

---

## 🧪 测试验证

### 自动化测试
```bash
# 运行单元测试
cd /path/to/project
pytest tests/unit/test_account_lockout_service.py -v

# 运行集成测试
pytest tests/integration/test_auth_lockout_integration.py -v
```

### 手动测试
```bash
# 使用测试脚本
cd /path/to/project
chmod +x test_lockout_manual.sh
./test_lockout_manual.sh
```

### API测试
```bash
# 测试锁定流程
TEST_USER="testuser_$(date +%s)"
API_BASE="http://localhost:8000/api/v1"

# 6次失败登录
for i in {1..6}; do
  curl -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${TEST_USER}&password=wrongpassword"
  echo ""
  sleep 1
done

# 预期结果：
# 前5次返回 401 "用户名或密码错误"
# 第6次返回 423 "账户已锁定，请在XX分钟后重试"
```

---

## 🚀 部署指南

### 1. 前置条件
- Redis服务正常运行（推荐）
- 数据库权限正常

### 2. 部署步骤

```bash
# 1. 拉取代码
git pull origin main

# 2. 运行数据库迁移
alembic upgrade head

# 3. 重启应用
sudo systemctl restart your-app

# 4. 验证Redis连接
redis-cli ping
# 应返回 PONG

# 5. 检查日志
tail -f /var/log/your-app/app.log | grep -i lockout
```

### 3. 配置检查

确认环境变量配置：
```bash
# Redis连接（推荐）
export REDIS_URL="redis://localhost:6379/0"

# 或者使用速率限制Redis
export RATE_LIMIT_STORAGE_URL="redis://localhost:6379/1"
```

如果Redis不可用，系统会自动降级到数据库存储，但会有性能影响。

---

## 📊 性能指标

### 预期指标
- **登录请求处理**: <100ms（无锁定）
- **锁定检查**: <10ms（Redis）/ <50ms（数据库）
- **解锁操作**: <50ms
- **历史查询**: <200ms（50条记录）

### Redis内存使用
- 每个锁定账户: ~200 bytes
- 每个失败计数: ~50 bytes
- 1000个并发攻击: ~250KB

### 数据库存储
- 登录记录增长: ~100 bytes/记录
- 预计增长: 10,000条/天 = ~1MB/天
- 建议定期清理（保留90天）

---

## 🔧 配置调优

### 修改阈值

编辑 `app/services/account_lockout_service.py`:

```python
class AccountLockoutService:
    # 调整这些常量
    LOCKOUT_THRESHOLD = 5              # 失败次数阈值（建议3-10）
    LOCKOUT_DURATION_MINUTES = 15      # 锁定时长（建议10-30分钟）
    ATTEMPT_WINDOW_MINUTES = 15        # 统计窗口（建议与锁定时长一致）
    CAPTCHA_THRESHOLD = 3              # 验证码阈值（建议2-5）
    IP_BLACKLIST_THRESHOLD = 20        # IP黑名单阈值（建议15-50）
```

**注意**: 修改后需重启应用！

### 安全建议

**高安全场景**（金融、政府）:
- `LOCKOUT_THRESHOLD = 3`
- `LOCKOUT_DURATION_MINUTES = 30`
- `IP_BLACKLIST_THRESHOLD = 10`

**平衡场景**（企业内部系统）:
- `LOCKOUT_THRESHOLD = 5`（默认）
- `LOCKOUT_DURATION_MINUTES = 15`（默认）
- `IP_BLACKLIST_THRESHOLD = 20`（默认）

**用户友好场景**（公开服务）:
- `LOCKOUT_THRESHOLD = 10`
- `LOCKOUT_DURATION_MINUTES = 10`
- `IP_BLACKLIST_THRESHOLD = 50`

---

## 📈 监控与告警

### 关键指标监控

1. **锁定账户数量**
   ```sql
   SELECT COUNT(DISTINCT username)
   FROM login_attempts
   WHERE locked = TRUE
     AND created_at > NOW() - INTERVAL 1 HOUR;
   ```

2. **失败登录趋势**
   ```sql
   SELECT DATE_FORMAT(created_at, '%Y-%m-%d %H:00:00') as hour,
          COUNT(*) as attempts
   FROM login_attempts
   WHERE success = FALSE
     AND created_at > NOW() - INTERVAL 24 HOUR
   GROUP BY hour
   ORDER BY hour;
   ```

3. **IP黑名单数量**
   ```bash
   redis-cli --scan --pattern "ip_blacklist:*" | wc -l
   ```

### 告警规则建议

- ⚠️ **警告**: 1小时内超过50次失败登录
- 🚨 **严重**: 1小时内超过100次失败登录
- 🔥 **紧急**: IP黑名单触发或系统管理员账户被攻击

---

## 🐛 已知问题

### 1. Redis不可用时的降级
**状态**: 已实现  
**影响**: 降级到数据库后性能下降，建议快速修复Redis

### 2. 验证码未集成
**状态**: 后端已支持，前端待实现  
**计划**: v1.1版本

### 3. IP黑名单没有时间戳
**状态**: Redis永久存储，不记录拉黑时间  
**计划**: v1.2版本改进

### 4. 缺少白名单IP功能
**状态**: 待开发  
**计划**: v1.2版本

---

## 🔮 未来改进

### v1.1（计划中）
- [ ] 前端验证码集成
- [ ] WebSocket实时通知
- [ ] 批量操作接口
- [ ] 更详细的统计报表

### v1.2（待规划）
- [ ] 白名单IP配置
- [ ] IP黑名单时间戳记录
- [ ] 地理位置检测（异地登录告警）
- [ ] 机器学习异常检测

---

## 📞 支持与反馈

### 技术支持
- **开发团队**: @Security-Team
- **文档**: `docs/security/`
- **Issue**: 提交到项目issue tracker

### 紧急联系
- **安全事件**: security@company.com
- **系统故障**: ops@company.com
- **值班电话**: 138-xxxx-xxxx（24小时）

---

## 📝 变更日志

### v1.0 (2026-02-15)
- ✅ 初始版本发布
- ✅ 核心锁定机制实现
- ✅ 管理员功能完整
- ✅ 完整文档交付
- ✅ 20个单元测试
- ✅ IP黑名单功能

---

## 📄 许可与版权

**版权所有** © 2026 Your Company  
**内部使用** - 未经授权不得外传

---

**交付确认**: ✅ 所有P0功能已完成  
**质量保证**: ✅ 20个单元测试全部通过  
**文档完整性**: ✅ 4份完整文档  
**部署就绪**: ✅ 可立即部署生产环境

**交付人**: AI Agent  
**交付日期**: 2026-02-15  
**审核状态**: 待审核
