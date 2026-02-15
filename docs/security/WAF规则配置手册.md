# WAF规则配置手册

> **版本**: 1.0.0  
> **日期**: 2026-02-15  
> **目标**: ModSecurity规则深度配置指南

---

## 目录

1. [规则基础](#规则基础)
2. [OWASP CRS配置](#owasp-crs配置)
3. [自定义规则编写](#自定义规则编写)
4. [白名单与黑名单](#白名单与黑名单)
5. [规则调优](#规则调优)
6. [常见攻击防护](#常见攻击防护)
7. [规则测试](#规则测试)

---

## 规则基础

### ModSecurity规则语法

#### 基本结构

```apache
SecRule VARIABLES "OPERATOR" "ACTIONS"
```

**示例:**
```apache
SecRule REQUEST_URI "@contains admin" \
    "id:1001,phase:1,deny,status:403,log,msg:'Admin access blocked'"
```

#### 关键组件

1. **VARIABLES（变量）**
   - `REQUEST_URI` - 请求URI
   - `ARGS` - 所有参数
   - `REQUEST_HEADERS` - 请求头
   - `REQUEST_BODY` - 请求体
   - `REMOTE_ADDR` - 客户端IP

2. **OPERATOR（运算符）**
   - `@contains` - 包含
   - `@rx` - 正则表达式
   - `@eq` - 等于
   - `@gt` - 大于
   - `@ipMatch` - IP匹配

3. **ACTIONS（动作）**
   - `id` - 规则ID
   - `phase` - 执行阶段（1-5）
   - `deny` - 拒绝请求
   - `pass` - 继续处理
   - `log` - 记录日志
   - `msg` - 日志消息

### 执行阶段（Phase）

| 阶段 | 名称 | 时机 | 用途 |
|------|------|------|------|
| 1 | Request Headers | 请求头接收后 | IP/UA检查 |
| 2 | Request Body | 请求体接收后 | 参数检查 |
| 3 | Response Headers | 响应头生成后 | 响应头检查 |
| 4 | Response Body | 响应体生成后 | 信息泄露检测 |
| 5 | Logging | 日志记录前 | 日志处理 |

---

## OWASP CRS配置

### 1. 核心配置文件

**路径**: `docker/nginx/modsecurity/main.conf`

```apache
# 包含OWASP CRS
Include /usr/share/modsecurity-crs/crs-setup.conf
Include /usr/share/modsecurity-crs/rules/*.conf
```

### 2. 偏执级别配置

**编辑**: `crs-setup.conf`（通过环境变量控制）

```bash
# .env.waf
PARANOIA=1  # 1-4，级别越高规则越严格
```

**级别说明:**

#### Level 1（推荐）
- ✅ 基础防护
- ✅ 误报率低
- ✅ 适合大多数应用

**规则示例:**
- SQL注入基础模式
- XSS基础模式
- 常见路径穿越

#### Level 2
- ⚡ 增强防护
- ⚠️ 中等误报率
- 🎯 高安全要求

**额外规则:**
- SQL注入变体
- XSS编码变体
- 协议异常检测

#### Level 3
- 🔒 严格防护
- ⚠️⚠️ 高误报率
- 🎯 极高安全要求

**额外规则:**
- 深度内容检查
- 严格参数验证
- 敏感操作限制

#### Level 4
- 🚫 极度严格
- ⚠️⚠️⚠️ 很高误报率
- 🎯 特殊场景

**额外规则:**
- 最严格检查
- 几乎零容忍
- 需要大量白名单

### 3. 异常评分配置

```apache
# docker/nginx/modsecurity/main.conf
SecAction \
 "id:900110,\
  phase:1,\
  nolog,\
  pass,\
  t:none,\
  setvar:tx.inbound_anomaly_score_threshold=5,\
  setvar:tx.outbound_anomaly_score_threshold=4"
```

**工作原理:**
1. 每个匹配规则增加评分（1-5分）
2. 评分累加
3. 超过阈值则拦截

**评分示例:**
- SQL注入检测: +5分（严重）
- XSS检测: +5分（严重）
- 协议异常: +4分（警告）
- 可疑字符: +2分（注意）

**阈值建议:**
- 宽松: 10分
- 标准: 5分（默认）
- 严格: 3分

### 4. 规则排除（处理误报）

#### 4.1 排除特定规则

```apache
# 排除规则920420（URL编码滥用）
SecRule REQUEST_URI "@beginsWith /api/v1/upload" \
    "id:1100,phase:1,nolog,pass,ctl:ruleRemoveById=920420"
```

#### 4.2 排除规则标签

```apache
# 排除所有SQL注入规则
SecRule REQUEST_URI "@beginsWith /api/v1/debug" \
    "id:1101,phase:1,nolog,pass,ctl:ruleRemoveByTag=attack-sqli"
```

#### 4.3 降低规则等级

```apache
# 将规则从拦截改为警告
SecRuleUpdateActionById 942100 "pass,log"
```

---

## 自定义规则编写

### 1. SQL注入防护

```apache
# 检测UNION SELECT
SecRule ARGS "@rx (?i)union.*select" \
    "id:10001,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'SQL Injection - UNION SELECT',\
    severity:CRITICAL,\
    tag:'attack-sqli',\
    logdata:'Matched Data: %{MATCHED_VAR}'"

# 检测注释符号
SecRule ARGS "@rx (?:--|#|/\*)" \
    "id:10002,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'SQL Injection - Comment',\
    severity:CRITICAL,\
    tag:'attack-sqli'"

# 检测OR条件绕过
SecRule ARGS "@rx (?i)or\s+['\"]?1['\"]?\s*=\s*['\"]?1" \
    "id:10003,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'SQL Injection - OR Bypass',\
    severity:CRITICAL,\
    tag:'attack-sqli'"
```

### 2. XSS防护

```apache
# 检测Script标签
SecRule ARGS "@rx (?i)<script[^>]*>" \
    "id:10010,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'XSS - Script Tag',\
    severity:CRITICAL,\
    tag:'attack-xss'"

# 检测事件处理器
SecRule ARGS "@rx (?i)on(error|load|click|mouse)=" \
    "id:10011,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'XSS - Event Handler',\
    severity:CRITICAL,\
    tag:'attack-xss'"

# 检测JavaScript协议
SecRule ARGS "@rx (?i)javascript:" \
    "id:10012,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'XSS - JavaScript Protocol',\
    severity:CRITICAL,\
    tag:'attack-xss'"
```

### 3. 路径穿越防护

```apache
# 检测../ 模式
SecRule REQUEST_URI "@contains ../" \
    "id:10020,\
    phase:1,\
    deny,\
    status:403,\
    log,\
    msg:'Path Traversal',\
    severity:CRITICAL,\
    tag:'attack-traversal'"

# 检测编码变体
SecRule REQUEST_URI "@rx (?:%2e%2e[/\\]|\.\.[\\/])" \
    "id:10021,\
    phase:1,\
    deny,\
    status:403,\
    log,\
    msg:'Path Traversal - Encoded',\
    severity:CRITICAL,\
    tag:'attack-traversal'"
```

### 4. 敏感文件访问防护

```apache
# 防止访问.env文件
SecRule REQUEST_URI "@rx \.env$" \
    "id:10030,\
    phase:1,\
    deny,\
    status:404,\
    log,\
    msg:'Sensitive File Access - .env',\
    severity:CRITICAL,\
    tag:'attack-disclosure'"

# 防止访问版本控制文件
SecRule REQUEST_URI "@rx /\.(git|svn|hg)/" \
    "id:10031,\
    phase:1,\
    deny,\
    status:404,\
    log,\
    msg:'Version Control Access',\
    severity:CRITICAL,\
    tag:'attack-disclosure'"

# 防止访问备份文件
SecRule REQUEST_URI "@rx \.(bak|backup|old|tmp)$" \
    "id:10032,\
    phase:1,\
    deny,\
    status:404,\
    log,\
    msg:'Backup File Access',\
    severity:WARNING,\
    tag:'attack-disclosure'"
```

### 5. 命令注入防护

```apache
# 检测Shell命令
SecRule ARGS "@rx (?i)(cat|ls|wget|curl|nc|bash|sh)\s" \
    "id:10040,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'Command Injection',\
    severity:CRITICAL,\
    tag:'attack-injection'"

# 检测命令分隔符
SecRule ARGS "@rx [;|&`$()]" \
    "id:10041,\
    phase:2,\
    log,\
    pass,\
    msg:'Suspicious Command Characters',\
    severity:WARNING,\
    tag:'attack-injection'"
```

### 6. SSRF防护

```apache
# 检测本地地址访问
SecRule ARGS "@rx (?i)(localhost|127\.0\.0\.1|::1)" \
    "id:10050,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'SSRF - Local Address',\
    severity:CRITICAL,\
    tag:'attack-ssrf'"

# 检测危险协议
SecRule ARGS "@rx (?i)(file|gopher|dict)://" \
    "id:10051,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'SSRF - Dangerous Protocol',\
    severity:CRITICAL,\
    tag:'attack-ssrf'"
```

---

## 白名单与黑名单

### IP白名单

#### 1. 信任的内网IP

```apache
# 跳过WAF检查
SecRule REMOTE_ADDR "@ipMatch 192.168.1.0/24,10.0.0.0/8" \
    "id:11000,\
    phase:1,\
    nolog,\
    pass,\
    ctl:ruleEngine=Off"
```

#### 2. 信任的API客户端

```apache
# 根据IP白名单放行
SecRule REMOTE_ADDR "@ipMatchFromFile /etc/nginx/whitelist-ips.txt" \
    "id:11001,\
    phase:1,\
    nolog,\
    pass,\
    ctl:ruleEngine=Off"
```

**whitelist-ips.txt格式:**
```
203.0.113.1
203.0.113.2/32
203.0.113.0/24
```

### URL白名单

#### 1. 排除特定路径

```apache
# 健康检查接口
SecRule REQUEST_URI "@beginsWith /health" \
    "id:11010,\
    phase:1,\
    nolog,\
    pass,\
    ctl:ruleEngine=Off"

# 静态资源
SecRule REQUEST_URI "@beginsWith /static/" \
    "id:11011,\
    phase:1,\
    nolog,\
    pass,\
    ctl:ruleEngine=Off"
```

#### 2. 文件上传接口特殊处理

```apache
# 上传接口放宽body大小检查
SecRule REQUEST_URI "@beginsWith /api/v1/upload" \
    "id:11020,\
    phase:1,\
    nolog,\
    pass,\
    ctl:requestBodyLimit=52428800"  # 50MB
```

### User-Agent白名单

```apache
# 信任的监控工具
SecRule REQUEST_HEADERS:User-Agent "@contains Prometheus" \
    "id:11030,\
    phase:1,\
    nolog,\
    pass,\
    ctl:ruleEngine=Off"
```

### IP黑名单

#### 1. 已知恶意IP

```apache
SecRule REMOTE_ADDR "@ipMatch 198.51.100.1,203.0.113.0/24" \
    "id:12000,\
    phase:1,\
    deny,\
    status:403,\
    log,\
    msg:'Blocked IP',\
    severity:CRITICAL"
```

#### 2. 从文件加载黑名单

```apache
SecRule REMOTE_ADDR "@ipMatchFromFile /etc/nginx/blacklist-ips.txt" \
    "id:12001,\
    phase:1,\
    deny,\
    status:403,\
    log,\
    msg:'Blacklisted IP'"
```

### User-Agent黑名单

```apache
# 阻止已知扫描器
SecRule REQUEST_HEADERS:User-Agent "@rx (?i)(sqlmap|nikto|nmap|masscan)" \
    "id:12010,\
    phase:1,\
    deny,\
    status:403,\
    log,\
    msg:'Malicious Scanner Blocked'"
```

---

## 规则调优

### 1. 识别误报

#### 查看拦截日志

```bash
# 查看最近的拦截
tail -100 logs/nginx/modsec_audit.log

# 提取拦截规则ID
grep -oP '(?<=\[id ")[^"]+' logs/nginx/modsec_audit.log | sort | uniq -c | sort -rn
```

#### 分析单条拦截

```bash
# 查找特定规则ID的详细信息
grep -A 20 'id "920420"' logs/nginx/modsec_audit.log
```

### 2. 调整规则

#### 方法1: 完全排除规则

```apache
# 针对特定路径排除规则920420
SecRule REQUEST_URI "@beginsWith /api/v1/complex-query" \
    "id:13000,phase:1,nolog,pass,ctl:ruleRemoveById=920420"
```

#### 方法2: 降低规则严重性

```apache
# 将规则从deny改为pass（仅记录）
SecRuleUpdateActionById 920420 "pass,log"
```

#### 方法3: 提高阈值

```apache
# 提高异常评分阈值（针对特定路径）
SecRule REQUEST_URI "@beginsWith /api/v1/flexible" \
    "id:13010,\
    phase:1,\
    nolog,\
    pass,\
    setvar:tx.inbound_anomaly_score_threshold=10"
```

### 3. 性能优化

#### 跳过不必要的检查

```apache
# 静态资源不检查body
SecRule REQUEST_URI "@rx \.(jpg|png|css|js)$" \
    "id:13020,\
    phase:1,\
    nolog,\
    pass,\
    ctl:requestBodyAccess=Off"
```

#### 限制响应体检查大小

```apache
SecResponseBodyLimit 524288  # 512KB
SecResponseBodyLimitAction ProcessPartial
```

---

## 常见攻击防护

### 1. 暴力破解防护

#### 登录接口限制

```nginx
# nginx.conf
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

# pms.conf
location /api/v1/auth/login {
    limit_req zone=login burst=3 nodelay;
    limit_req_status 429;
    # ...
}
```

#### WAF规则记录登录失败

```apache
SecRule REQUEST_URI "@beginsWith /api/v1/auth/login" \
    "id:14000,\
    phase:2,\
    chain,\
    log,\
    pass,\
    msg:'Login Attempt'"
    SecRule RESPONSE_STATUS "@eq 401" \
        "setvar:ip.login_failed=+1,\
        expirevar:ip.login_failed=300"

# 超过5次失败则临时封禁
SecRule IP:LOGIN_FAILED "@gt 5" \
    "id:14001,\
    phase:1,\
    deny,\
    status:403,\
    log,\
    msg:'Too Many Failed Logins',\
    setvar:ip.blocked=1,\
    expirevar:ip.blocked=3600"
```

### 2. 文件上传限制

```apache
# 限制上传文件类型
SecRule FILES_TMPNAMES "@rx \.(php|exe|sh|bat)$" \
    "id:14010,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'Dangerous File Upload'"

# 检查文件内容（magic bytes）
SecRule FILES "@rx ^(?:\x4d\x5a|\x50\x4b)" \
    "id:14011,\
    phase:2,\
    deny,\
    status:403,\
    log,\
    msg:'Executable File Detected'"
```

### 3. API滥用防护

```apache
# 超大JSON请求
SecRule REQUEST_HEADERS:Content-Type "@contains application/json" \
    "id:14020,\
    phase:1,\
    chain"
    SecRule REQUEST_HEADERS:Content-Length "@gt 1048576" \
        "deny,\
        status:413,\
        log,\
        msg:'JSON Request Too Large'"
```

### 4. 协议异常检测

```apache
# 无效HTTP版本
SecRule REQUEST_PROTOCOL "!@rx ^HTTP/(1\.[01]|2)$" \
    "id:14030,\
    phase:1,\
    deny,\
    status:400,\
    log,\
    msg:'Invalid HTTP Protocol'"

# 无Host头
SecRule &REQUEST_HEADERS:Host "@eq 0" \
    "id:14031,\
    phase:1,\
    deny,\
    status:400,\
    log,\
    msg:'Missing Host Header'"
```

---

## 规则测试

### 1. 测试工具

#### cURL测试

```bash
# 测试SQL注入拦截
curl -v "http://localhost/api/v1/users?id=1' OR '1'='1"

# 测试XSS拦截
curl -v "http://localhost/api/v1/search?q=<script>alert(1)</script>"

# 测试路径穿越
curl -v "http://localhost/../../etc/passwd"
```

#### 自动化测试脚本

```bash
bash scripts/waf/test-waf.sh
```

### 2. 日志分析

```bash
# 查看拦截统计
grep "ModSecurity: Access denied" logs/nginx/error.log | wc -l

# 按规则ID统计
grep -oP '(?<=\[id ")[^"]+' logs/nginx/modsec_audit.log | \
    sort | uniq -c | sort -rn | head -10

# 查看拦截的URL
grep "ModSecurity: Access denied" logs/nginx/error.log | \
    grep -oP '(?<=uri ")[^"]+' | sort | uniq -c
```

### 3. 调试模式

```apache
# 启用详细调试日志
SecDebugLog /var/log/nginx/modsec_debug.log
SecDebugLogLevel 9  # 0-9，9为最详细

# 仅针对特定IP调试
SecRule REMOTE_ADDR "@ipMatch 192.168.1.100" \
    "id:15000,phase:1,pass,ctl:debugLogLevel=9"
```

---

## 规则管理最佳实践

### 1. 版本控制

```bash
# 将规则文件纳入Git管理
git add docker/nginx/modsecurity/
git commit -m "feat: add custom WAF rules"
```

### 2. 文档化

```apache
# 每条自定义规则添加注释
# ============================================
# 规则ID: 10001
# 用途: 防止SQL注入 - UNION SELECT
# 作者: Security Team
# 日期: 2026-02-15
# 测试: curl "http://localhost/api?id=1' UNION SELECT"
# ============================================
SecRule ARGS "@rx (?i)union.*select" \
    "id:10001,phase:2,deny,status:403"
```

### 3. 变更管理

```bash
# 变更前备份
cp docker/nginx/modsecurity/custom-rules.conf \
   docker/nginx/modsecurity/custom-rules.conf.bak.$(date +%Y%m%d)

# 测试变更
docker-compose -f docker-compose.waf.yml exec nginx-waf nginx -t

# 应用变更
docker-compose -f docker-compose.waf.yml restart nginx-waf
```

### 4. 定期审计

```bash
# 每月检查规则有效性
bash scripts/waf/test-waf.sh > audit-$(date +%Y%m).log

# 分析误报率
grep "FAILED" audit-*.log
```

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-15  
**维护者**: PMS Security Team
