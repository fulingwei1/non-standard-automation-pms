# 账户锁定管理员手册

## 概述

账户锁定机制是系统安全防护的第一道防线，用于防止暴力破解攻击。作为管理员，您需要了解如何管理锁定账户、处理用户请求和应对安全事件。

## 管理功能

### 1. 查看锁定账户列表

**API**: `GET /api/v1/admin/account-lockout/locked-accounts`

**权限**: 需要管理员权限

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "locked_accounts": [
      {
        "username": "john.doe",
        "locked_until": "2026-02-15T15:30:00",
        "attempts": 5
      }
    ],
    "total": 1
  }
}
```

**Web界面**:
1. 登录管理后台
2. 进入"系统管理" → "安全管理" → "锁定账户"

### 2. 手动解锁账户

**API**: `POST /api/v1/admin/account-lockout/unlock`

**请求体**:
```json
{
  "username": "john.doe"
}
```

**使用场景**:
- 用户忘记密码多次尝试
- 紧急情况需要立即访问
- 误触发锁定

**注意事项**:
- 解锁操作会被记录在审计日志中
- 解锁后，失败次数归零
- 建议在解锁前核实用户身份

### 3. 查看登录历史

**API**: `POST /api/v1/admin/account-lockout/login-history`

**请求体**:
```json
{
  "username": "john.doe",
  "limit": 50
}
```

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "history": [
      {
        "id": 12345,
        "username": "john.doe",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "success": false,
        "failure_reason": "wrong_password",
        "locked": true,
        "created_at": "2026-02-15T14:15:23"
      }
    ],
    "total": 50
  }
}
```

### 4. IP黑名单管理

#### 查看黑名单

**API**: `GET /api/v1/admin/account-lockout/ip-blacklist`

**响应示例**:
```json
{
  "code": 200,
  "data": {
    "blacklisted_ips": [
      {
        "ip": "203.0.113.45",
        "created_at": null
      }
    ],
    "total": 1
  }
}
```

#### 移除IP黑名单

**API**: `POST /api/v1/admin/account-lockout/remove-ip-blacklist`

**请求体**:
```json
{
  "ip": "203.0.113.45"
}
```

### 5. 查询账户锁定状态

**API**: `GET /api/v1/admin/account-lockout/lockout-status/{username}`

**使用场景**:
- 用户报告登录问题时快速诊断
- 安全审计
- 数据分析

## 常见场景处理

### 场景1：用户报告"账户被锁定"

**处理流程：**

1. **验证用户身份**
   - 确认用户工号
   - 验证联系方式
   - 询问最后一次登录时间

2. **检查锁定状态**
   ```bash
   curl -X GET "http://your-domain/api/v1/admin/account-lockout/lockout-status/john.doe" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   ```

3. **查看登录历史**
   - 检查失败原因
   - 确认IP地址是否正常
   - 判断是否为恶意攻击

4. **决策**
   - **正常情况**：告知用户等待15分钟自动解锁
   - **紧急情况**：手动解锁并记录原因
   - **异常情况**：拒绝解锁，上报安全团队

5. **后续建议**
   - 提醒用户重置密码
   - 建议检查密码管理器
   - 发送安全提示邮件

### 场景2：检测到暴力破解攻击

**识别特征：**
- 短时间内大量失败尝试
- 来自同一IP或IP段
- 尝试多个不同用户名
- 使用常见密码字典

**应对措施：**

1. **立即行动**
   ```bash
   # 检查可疑IP
   curl -X GET "http://your-domain/api/v1/admin/account-lockout/ip-blacklist" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   ```

2. **临时措施**
   - IP已自动拉黑（20次失败）
   - 通知受影响用户
   - 启用临时WAF规则

3. **长期防护**
   - 分析攻击模式
   - 更新防护规则
   - 强制重置弱密码

4. **事件报告**
   - 记录攻击时间、来源
   - 统计受影响账户
   - 提交安全事件报告

### 场景3：合法用户被误拉黑

**情况：**
- 用户在多个设备上登录失败
- 公司内部NAT导致IP共享
- 用户真的忘记密码

**处理流程：**

1. **确认合法性**
   - 核实用户身份
   - 检查历史登录记录
   - 确认最近是否有密码更改

2. **解除限制**
   ```bash
   # 解锁账户
   curl -X POST "http://your-domain/api/v1/admin/account-lockout/unlock" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -d '{"username": "john.doe"}'
   
   # 如果IP被拉黑
   curl -X POST "http://your-domain/api/v1/admin/account-lockout/remove-ip-blacklist" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -d '{"ip": "192.168.1.100"}'
   ```

3. **重置密码**
   - 强制用户重置密码
   - 确保新密码符合复杂度要求

4. **教育用户**
   - 解释锁定机制
   - 提供密码管理建议
   - 发送安全手册链接

## 监控与告警

### 告警触发条件

系统会在以下情况自动发送告警：

1. **账户锁定**
   - 通知方式：企业微信、邮件
   - 内容：用户名、IP、失败次数

2. **IP拉黑**
   - 通知方式：企业微信、邮件、短信（严重）
   - 内容：IP地址、尝试次数、时间范围

3. **大规模攻击**
   - 条件：1小时内超过100次失败尝试
   - 通知：安全团队、运维团队、管理层

### 日志查询

所有登录尝试都记录在`login_attempts`表中：

```sql
-- 查询最近1小时的失败登录
SELECT username, ip_address, COUNT(*) as attempts
FROM login_attempts
WHERE success = FALSE
  AND created_at > NOW() - INTERVAL 1 HOUR
GROUP BY username, ip_address
ORDER BY attempts DESC;

-- 查询被锁定的账户
SELECT DISTINCT username
FROM login_attempts
WHERE locked = TRUE
  AND created_at > NOW() - INTERVAL 1 DAY;

-- 查询可疑IP（多账户尝试）
SELECT ip_address, COUNT(DISTINCT username) as target_users
FROM login_attempts
WHERE success = FALSE
  AND created_at > NOW() - INTERVAL 1 HOUR
GROUP BY ip_address
HAVING COUNT(DISTINCT username) > 5;
```

## 配置参数

系统默认配置位于`app/services/account_lockout_service.py`：

```python
LOCKOUT_THRESHOLD = 5              # 失败次数阈值
LOCKOUT_DURATION_MINUTES = 15      # 锁定时长（分钟）
ATTEMPT_WINDOW_MINUTES = 15        # 失败次数统计窗口（分钟）
CAPTCHA_THRESHOLD = 3              # 需要验证码的失败次数阈值
IP_BLACKLIST_THRESHOLD = 20        # IP黑名单阈值（15分钟内）
```

**修改配置后需要重启服务！**

## 安全最佳实践

### ✅ 应该做的

1. **定期审计**
   - 每周检查锁定账户列表
   - 每月分析登录失败趋势
   - 每季度审查黑名单IP

2. **快速响应**
   - 及时处理用户解锁请求
   - 立即调查异常登录模式
   - 迅速应对安全告警

3. **用户教育**
   - 定期发送安全提示
   - 培训密码安全知识
   - 分享案例警示

### ❌ 不应该做的

1. **盲目解锁**
   - 不验证身份就解锁
   - 频繁为同一用户解锁
   - 解锁后不跟进

2. **忽略告警**
   - 关闭或忽略安全告警
   - 不记录解锁原因
   - 不分析攻击模式

3. **配置不当**
   - 阈值设置过高（降低安全性）
   - 阈值设置过低（频繁误锁）
   - 不定期审查配置

## 故障排查

### 问题1：Redis不可用，锁定机制失效

**症状**：
- 用户报告可以无限次尝试登录
- 日志显示"Redis连接失败"

**解决方案**：
1. 检查Redis服务状态：`redis-cli ping`
2. 系统会自动降级到数据库存储
3. 修复Redis后重启应用

### 问题2：用户无法解锁

**症状**：
- 调用解锁API后仍然锁定
- 15分钟后仍无法登录

**排查步骤**：
1. 检查Redis key是否删除：`redis-cli GET "lockout:username"`
2. 检查时间是否同步（NTP）
3. 查看应用日志

### 问题3：IP黑名单误伤

**症状**：
- 大量用户报告无法登录
- 都来自同一网段

**原因**：
- 公司NAT/代理导致共享出口IP
- VPN出口IP被拉黑

**临时解决**：
```bash
# 移除IP黑名单
curl -X POST "http://your-domain/api/v1/admin/account-lockout/remove-ip-blacklist" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{"ip": "公司出口IP"}'
```

**长期解决**：
- 配置白名单IP（待实现）
- 调整IP黑名单阈值
- 改进检测算法

## 审计与合规

### 记录保留

- **登录尝试记录**: 保留90天
- **审计日志**: 保留1年
- **安全事件**: 永久保留

### 报告要求

定期向安全团队提交：

1. **周报**
   - 锁定账户数量
   - 解锁请求处理情况
   - 异常事件摘要

2. **月报**
   - 安全事件统计
   - 攻击趋势分析
   - 改进建议

## 附录

### API完整列表

| API | 方法 | 说明 |
|-----|------|------|
| `/api/v1/admin/account-lockout/locked-accounts` | GET | 查看锁定账户列表 |
| `/api/v1/admin/account-lockout/unlock` | POST | 手动解锁账户 |
| `/api/v1/admin/account-lockout/login-history` | POST | 查看登录历史 |
| `/api/v1/admin/account-lockout/ip-blacklist` | GET | 查看IP黑名单 |
| `/api/v1/admin/account-lockout/remove-ip-blacklist` | POST | 移除IP黑名单 |
| `/api/v1/admin/account-lockout/lockout-status/{username}` | GET | 查询锁定状态 |

### 相关文档

- [用户手册 - 账户被锁定怎么办](./account_lockout_user_guide.md)
- [API文档](./account_lockout_api.md)
- [安全事件响应流程](./security_incident_response.md)

---

**最后更新**: 2026年2月15日  
**版本**: v1.0  
**维护者**: 系统安全团队
