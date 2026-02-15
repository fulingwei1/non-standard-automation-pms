# WAF部署指南

> **版本**: 1.0.0  
> **日期**: 2026-02-15  
> **作者**: PMS Security Team  
> **目标**: 非标准自动化PMS - Nginx + ModSecurity WAF部署

---

## 📋 目录

1. [概述](#概述)
2. [系统要求](#系统要求)
3. [快速开始](#快速开始)
4. [详细部署步骤](#详细部署步骤)
5. [配置说明](#配置说明)
6. [SSL证书管理](#ssl证书管理)
7. [测试验证](#测试验证)
8. [监控与维护](#监控与维护)
9. [常见问题](#常见问题)
10. [最佳实践](#最佳实践)

---

## 概述

### 什么是WAF？

Web Application Firewall（WAF）是一种应用层防火墙,专门用于保护Web应用免受各种网络攻击,包括:

- **SQL注入** - 防止数据库被非法访问
- **跨站脚本(XSS)** - 防止恶意脚本注入
- **路径穿越** - 防止访问未授权文件
- **命令注入** - 防止执行系统命令
- **CSRF攻击** - 防止跨站请求伪造
- **恶意扫描** - 识别并阻止安全扫描工具

### 为什么选择ModSecurity？

- ✅ **开源免费** - 无需许可证费用
- ✅ **OWASP CRS** - 使用业界标准规则集
- ✅ **高性能** - 基于Nginx,性能优异
- ✅ **灵活配置** - 支持自定义规则
- ✅ **活跃社区** - 持续更新维护

### 架构图

```
Internet
    ↓
[Nginx + ModSecurity WAF]  ← 第一道防线
    ↓
[FastAPI Backend]          ← 应用层
    ↓
[PostgreSQL Database]      ← 数据层
```

---

## 系统要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 2GB | 4GB+ |
| 磁盘 | 10GB | 20GB+ |
| 网络 | 100Mbps | 1Gbps+ |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+) / macOS
- **Docker**: 20.10+
- **Docker Compose**: 1.29+ / Docker Compose Plugin
- **权限**: 需要sudo权限（用于证书管理）

### 端口要求

| 端口 | 协议 | 用途 |
|------|------|------|
| 80 | HTTP | HTTP请求（重定向到443） |
| 443 | HTTPS | HTTPS请求 |
| 8000 | HTTP | FastAPI后端（内部） |

---

## 快速开始

### 🚀 一键部署（5分钟）

```bash
# 1. 进入项目目录
cd /path/to/non-standard-automation-pms

# 2. 执行部署脚本
bash scripts/waf/deploy-waf.sh

# 3. 等待部署完成
# 脚本会自动：
#   - 检查系统要求
#   - 创建必要目录
#   - 生成环境变量文件
#   - 生成SSL证书（自签名）
#   - 创建错误页面
#   - 启动WAF容器
#   - 运行基础测试

# 4. 运行完整测试
bash scripts/waf/test-waf.sh

# 5. 启动监控
bash scripts/waf/monitor-waf.sh --watch
```

### ✅ 验证部署

```bash
# 检查容器状态
docker-compose -f docker-compose.waf.yml ps

# 测试健康检查
curl http://localhost/health

# 测试SQL注入拦截
curl "http://localhost/api/v1/users?id=1' OR '1'='1"
# 应返回: 403 Forbidden

# 查看日志
docker-compose -f docker-compose.waf.yml logs -f nginx-waf
```

---

## 详细部署步骤

### 步骤1: 环境准备

#### 1.1 安装Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**CentOS/RHEL:**
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS:**
```bash
brew install --cask docker
```

#### 1.2 验证安装

```bash
docker --version
docker-compose --version
```

### 步骤2: 配置环境变量

#### 2.1 创建环境变量文件

```bash
cp .env.waf.example .env.waf
```

#### 2.2 编辑配置

```bash
nano .env.waf  # 或使用vim/其他编辑器
```

**关键配置项:**

```bash
# 域名配置（生产环境必须修改）
DOMAIN=pms.yourdomain.com
WWW_DOMAIN=www.pms.yourdomain.com

# SSL证书类型
CERT_TYPE=selfsigned  # 开发: selfsigned, 生产: letsencrypt
LETSENCRYPT_EMAIL=admin@yourdomain.com

# ModSecurity模式
MODSEC_RULE_ENGINE=DetectionOnly  # 先用DetectionOnly测试,确认后改为On

# 偏执级别（1-4）
PARANOIA=1  # 建议从1开始,根据误报情况调整

# 速率限制
API_RATE_LIMIT=100  # 请求/分钟
LOGIN_RATE_LIMIT=5  # 登录请求/分钟

# 告警配置
ALERT_THRESHOLD=10
ALERT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

### 步骤3: 生成SSL证书

#### 3.1 开发环境（自签名证书）

```bash
cd docker/nginx/ssl
bash generate-cert.sh
```

**输出示例:**
```
===================================
SSL证书生成脚本
===================================
域名: pms.example.com
证书类型: selfsigned
===================================
生成自签名证书...
✅ 自签名证书生成成功！
   证书: /path/to/pms.crt
   私钥: /path/to/pms.key

⚠️  警告: 自签名证书仅用于开发/测试环境！
```

#### 3.2 生产环境（Let's Encrypt）

**前提条件:**
- 域名已解析到服务器IP
- 80端口未被占用
- 安装certbot

```bash
# 安装certbot
# Ubuntu/Debian
sudo apt-get install certbot

# CentOS/RHEL
sudo yum install certbot

# 生成证书
export CERT_TYPE=letsencrypt
export DOMAIN=pms.yourdomain.com
export EMAIL=admin@yourdomain.com
bash docker/nginx/ssl/generate-cert.sh
```

**自动续期:**
```bash
# 添加到crontab
sudo crontab -e

# 添加以下行（每天凌晨3点检查并续期）
0 3 * * * certbot renew --quiet --deploy-hook 'docker-compose -f /path/to/docker-compose.waf.yml restart nginx-waf'
```

### 步骤4: 启动WAF服务

#### 4.1 启动容器

```bash
docker-compose -f docker-compose.waf.yml up -d
```

#### 4.2 查看启动日志

```bash
docker-compose -f docker-compose.waf.yml logs -f nginx-waf
```

#### 4.3 验证服务状态

```bash
# 检查容器运行状态
docker-compose -f docker-compose.waf.yml ps

# 期望输出:
# Name           Command          State                    Ports
# -------------------------------------------------------------------------
# pms-waf        nginx -g ...     Up      0.0.0.0:80->80/tcp, :::80->80/tcp,
#                                         0.0.0.0:443->443/tcp, :::443->443/tcp
```

### 步骤5: 测试验证

#### 5.1 运行自动化测试

```bash
bash scripts/waf/test-waf.sh
```

**测试覆盖:**
- ✅ 基础功能（健康检查、HTTPS重定向）
- ✅ SQL注入防护（10+种攻击方式）
- ✅ XSS防护（5+种攻击方式）
- ✅ 路径穿越防护
- ✅ 敏感文件访问拦截
- ✅ 命令注入防护
- ✅ 恶意扫描器检测
- ✅ 速率限制
- ✅ SSRF防护

#### 5.2 手动测试

```bash
# 测试正常请求
curl -k https://localhost/health
# 期望: 200 OK

# 测试SQL注入拦截
curl "http://localhost/api/v1/users?id=1' OR '1'='1"
# 期望: 403 Forbidden

# 测试XSS拦截
curl "http://localhost/api/v1/search?q=<script>alert(1)</script>"
# 期望: 403 Forbidden

# 测试敏感文件拦截
curl http://localhost/.env
# 期望: 404 Not Found
```

---

## 配置说明

### Nginx配置结构

```
docker/nginx/
├── nginx.conf                 # Nginx主配置
├── conf.d/
│   └── pms.conf              # 站点配置
├── modsecurity/
│   ├── main.conf             # ModSecurity主配置
│   └── custom-rules.conf     # 自定义规则
├── ssl/
│   ├── pms.crt              # SSL证书
│   ├── pms.key              # SSL私钥
│   └── chain.pem            # 证书链
└── errors/
    ├── 403.html             # 403错误页面
    ├── 404.html             # 404错误页面
    └── 50x.html             # 50x错误页面
```

### ModSecurity规则级别

#### 偏执级别（PARANOIA）

| 级别 | 描述 | 误报率 | 适用场景 |
|------|------|--------|----------|
| 1 | 基础防护 | 低 | 生产环境推荐 |
| 2 | 增强防护 | 中 | 高安全要求 |
| 3 | 严格防护 | 高 | 极高安全要求 |
| 4 | 极度严格 | 很高 | 仅特殊场景 |

**建议**: 从级别1开始,观察1-2周后根据实际情况调整。

#### 异常评分阈值

- **入站阈值（ANOMALY_INBOUND）**: 默认5分
  - 每条匹配规则会增加评分
  - 超过阈值则拦截请求
  
- **出站阈值（ANOMALY_OUTBOUND）**: 默认4分
  - 检测响应内容异常
  - 防止信息泄露

### 速率限制配置

编辑 `docker/nginx/conf.d/pms.conf`:

```nginx
# 定义速率限制区域
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=general:10m rate=200r/m;

# 应用到特定location
location /api/ {
    limit_req zone=api burst=20 nodelay;
    limit_req_status 429;
    # ...
}
```

**参数说明:**
- `rate`: 速率限制（r/s = 每秒, r/m = 每分钟）
- `burst`: 突发请求数量
- `nodelay`: 不延迟处理突发请求

---

## SSL证书管理

### 自签名证书（开发环境）

**优点:**
- ✅ 快速生成,无需域名
- ✅ 离线可用

**缺点:**
- ❌ 浏览器警告
- ❌ 不适合生产环境

**生成命令:**
```bash
export CERT_TYPE=selfsigned
export DOMAIN=pms.example.com
bash docker/nginx/ssl/generate-cert.sh
```

### Let's Encrypt证书（生产环境）

**优点:**
- ✅ 免费
- ✅ 自动续期
- ✅ 浏览器信任

**前提条件:**
- ✅ 域名已解析
- ✅ 80端口可访问
- ✅ 安装certbot

**申请命令:**
```bash
export CERT_TYPE=letsencrypt
export DOMAIN=pms.yourdomain.com
export EMAIL=admin@yourdomain.com
bash docker/nginx/ssl/generate-cert.sh
```

**续期管理:**
```bash
# 手动续期
sudo certbot renew

# 自动续期（crontab）
0 3 * * * certbot renew --quiet --deploy-hook 'docker-compose restart nginx-waf'
```

**证书有效期检查:**
```bash
# 查看证书信息
openssl x509 -in docker/nginx/ssl/pms.crt -noout -dates

# 输出示例:
# notBefore=Feb 15 00:00:00 2026 GMT
# notAfter=May 16 00:00:00 2026 GMT  ← 90天后过期
```

---

## 测试验证

### 自动化测试

```bash
# 运行所有测试
bash scripts/waf/test-waf.sh

# 输出示例:
========================================
  WAF功能测试脚本
========================================

测试 #1: 健康检查
期望状态码: 200
实际状态码: 200
✅ 通过

测试 #2: SQL注入 - Union Select
期望状态码: 403
实际状态码: 403
✅ 通过

...

========================================
  测试总结
========================================
总测试数: 25
通过: 25
失败: 0
🎉 所有测试通过！WAF配置正确。
```

### 手动测试场景

#### 1. SQL注入测试

```bash
# 测试1: UNION SELECT
curl "http://localhost/api/v1/users?id=1' UNION SELECT * FROM users--"
# 期望: 403

# 测试2: OR条件绕过
curl "http://localhost/api/v1/users?id=1' OR '1'='1"
# 期望: 403

# 测试3: 盲注
curl "http://localhost/api/v1/users?id=1' AND SLEEP(5)--"
# 期望: 403
```

#### 2. XSS测试

```bash
# 测试1: Script标签
curl "http://localhost/api/v1/search?q=<script>alert('XSS')</script>"
# 期望: 403

# 测试2: 事件处理器
curl "http://localhost/api/v1/search?q=<img src=x onerror=alert(1)>"
# 期望: 403
```

#### 3. 路径穿越测试

```bash
# 测试: 访问/etc/passwd
curl "http://localhost/api/v1/../../etc/passwd"
# 期望: 403
```

---

## 监控与维护

### 实时监控

```bash
# 启动交互式监控
bash scripts/waf/monitor-waf.sh --watch

# 单次统计
bash scripts/waf/monitor-waf.sh --stats

# 导出报告
bash scripts/waf/monitor-waf.sh --report
```

### 日志文件

| 日志文件 | 路径 | 用途 |
|---------|------|------|
| 访问日志 | `logs/nginx/access.log` | 所有HTTP请求 |
| 错误日志 | `logs/nginx/error.log` | Nginx错误 |
| WAF拦截日志 | `logs/nginx/blocked.log` | 被拦截的请求 |
| ModSecurity审计日志 | `logs/nginx/modsec_audit.log` | 详细安全事件 |

### 查看日志

```bash
# 实时查看访问日志
tail -f logs/nginx/access.log

# 查看拦截日志
tail -f logs/nginx/blocked.log

# 查看ModSecurity日志
tail -f logs/nginx/modsec_audit.log

# 统计拦截次数（最近1小时）
grep "$(date -d '1 hour ago' '+%d/%b/%Y:%H')" logs/nginx/blocked.log | wc -l
```

### 告警配置

编辑 `.env.waf`:

```bash
# 告警阈值（每分钟拦截次数）
ALERT_THRESHOLD=10

# 企业微信Webhook
ALERT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY

# 或钉钉Webhook
# ALERT_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
```

**测试告警:**
```bash
# 触发大量拦截
for i in {1..15}; do
    curl "http://localhost/api/v1/users?id=1' OR '1'='1" &
done

# 检查是否收到告警
```

---

## 常见问题

### Q1: 部署后无法访问服务

**可能原因:**
1. 端口被占用
2. 防火墙拦截
3. 容器未正常启动

**排查步骤:**
```bash
# 1. 检查容器状态
docker-compose -f docker-compose.waf.yml ps

# 2. 查看日志
docker-compose -f docker-compose.waf.yml logs nginx-waf

# 3. 检查端口占用
sudo netstat -tlnp | grep -E '(80|443)'

# 4. 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS
```

### Q2: 正常请求被误拦截

**解决方案:**

1. **临时切换到检测模式**
   ```bash
   # 编辑 .env.waf
   MODSEC_RULE_ENGINE=DetectionOnly
   
   # 重启服务
   docker-compose -f docker-compose.waf.yml restart nginx-waf
   ```

2. **分析审计日志**
   ```bash
   tail -f logs/nginx/modsec_audit.log
   # 找到拦截规则ID
   ```

3. **排除误报规则**
   ```bash
   # 编辑 docker/nginx/modsecurity/main.conf
   # 添加排除规则
   SecRule REQUEST_URI "@beginsWith /api/v1/your-endpoint" \
       "id:1100,phase:1,nolog,pass,ctl:ruleRemoveById=920420"
   
   # 重新加载
   docker-compose -f docker-compose.waf.yml restart nginx-waf
   ```

### Q3: 性能下降明显

**优化建议:**

1. **调整偏执级别**
   ```bash
   # .env.waf
   PARANOIA=1  # 从2或3降到1
   ```

2. **禁用响应体检测**
   ```bash
   # docker/nginx/modsecurity/main.conf
   SecResponseBodyAccess Off
   ```

3. **增加资源**
   ```yaml
   # docker-compose.waf.yml
   services:
     nginx-waf:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

### Q4: SSL证书续期失败

**解决方案:**

```bash
# 1. 手动续期
sudo certbot renew --dry-run  # 测试续期
sudo certbot renew  # 实际续期

# 2. 检查域名解析
nslookup pms.yourdomain.com

# 3. 检查80端口可访问性
curl http://pms.yourdomain.com/.well-known/acme-challenge/test

# 4. 查看certbot日志
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Q5: 如何完全关闭WAF（紧急情况）

```bash
# 方法1: 切换到DetectionOnly模式（推荐）
# 编辑 .env.waf
MODSEC_RULE_ENGINE=DetectionOnly
docker-compose -f docker-compose.waf.yml restart nginx-waf

# 方法2: 完全关闭ModSecurity
# 编辑 docker/nginx/modsecurity/main.conf
SecRuleEngine Off
docker-compose -f docker-compose.waf.yml restart nginx-waf

# 方法3: 临时直连后端（不推荐）
# 修改防火墙规则,暴露后端端口8000
```

---

## 最佳实践

### 1. 分阶段部署

#### 阶段1: 检测模式（1-2周）
```bash
MODSEC_RULE_ENGINE=DetectionOnly
PARANOIA=1
```
- 观察误报情况
- 收集正常业务流量特征
- 调整规则

#### 阶段2: 拦截模式（低偏执级别）
```bash
MODSEC_RULE_ENGINE=On
PARANOIA=1
```
- 启用拦截
- 保持低偏执级别
- 持续监控

#### 阶段3: 逐步提高（可选）
```bash
MODSEC_RULE_ENGINE=On
PARANOIA=2
```
- 根据实际需求提高级别
- 密切关注误报

### 2. 白名单管理

**信任的IP段（内网/办公网）:**
```bash
# docker/nginx/modsecurity/main.conf
SecRule REMOTE_ADDR "@ipMatch 192.168.1.0/24,10.0.0.0/8" \
    "id:1000,phase:1,nolog,pass,ctl:ruleEngine=Off"
```

**信任的User-Agent:**
```bash
SecRule REQUEST_HEADERS:User-Agent "@contains YourMonitoringTool" \
    "id:1001,phase:1,nolog,pass,ctl:ruleEngine=Off"
```

### 3. 日志轮转

```bash
# 创建 /etc/logrotate.d/nginx-waf
cat > /etc/logrotate.d/nginx-waf <<'EOF'
/path/to/logs/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nginx nginx
    sharedscripts
    postrotate
        docker-compose -f /path/to/docker-compose.waf.yml exec nginx-waf nginx -s reopen
    endscript
}
EOF
```

### 4. 定期审计

**每周任务:**
- ✅ 查看拦截统计
- ✅ 分析TOP攻击IP
- ✅ 检查误报情况

**每月任务:**
- ✅ 更新OWASP CRS规则
- ✅ 检查SSL证书有效期
- ✅ 审查自定义规则

**每季度任务:**
- ✅ 完整安全测试
- ✅ 规则优化
- ✅ 性能评估

### 5. 备份策略

```bash
# 备份配置文件
#!/bin/bash
BACKUP_DIR="/backup/waf-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

cp -r docker/nginx "$BACKUP_DIR/"
cp .env.waf "$BACKUP_DIR/"
cp docker-compose.waf.yml "$BACKUP_DIR/"

tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### 6. 灾难恢复

**准备:**
1. 定期备份配置
2. 文档化自定义规则
3. 保存证书副本

**恢复步骤:**
```bash
# 1. 恢复配置文件
tar -xzf backup.tar.gz
cp -r backup/docker/nginx docker/
cp backup/.env.waf .

# 2. 重新部署
bash scripts/waf/deploy-waf.sh

# 3. 验证
bash scripts/waf/test-waf.sh
```

---

## 附录

### A. 完整文件清单

```
non-standard-automation-pms/
├── docker/
│   └── nginx/
│       ├── nginx.conf                 # Nginx主配置
│       ├── conf.d/
│       │   └── pms.conf              # 站点配置
│       ├── modsecurity/
│       │   ├── main.conf             # ModSecurity主配置
│       │   └── custom-rules.conf     # 自定义规则
│       ├── ssl/
│       │   ├── generate-cert.sh      # 证书生成脚本
│       │   ├── pms.crt              # SSL证书
│       │   ├── pms.key              # SSL私钥
│       │   └── chain.pem            # 证书链
│       └── errors/
│           ├── 403.html             # 403错误页面
│           ├── 404.html             # 404错误页面
│           └── 50x.html             # 50x错误页面
├── scripts/
│   └── waf/
│       ├── deploy-waf.sh            # 部署脚本
│       ├── test-waf.sh              # 测试脚本
│       └── monitor-waf.sh           # 监控脚本
├── docs/
│   └── security/
│       ├── WAF部署指南.md           # 本文档
│       ├── WAF规则配置手册.md
│       ├── WAF拦截日志分析指南.md
│       └── WAF故障排查手册.md
├── docker-compose.waf.yml           # Docker编排文件
├── Dockerfile.nginx                 # Nginx镜像构建
├── .env.waf.example                # 环境变量示例
└── .env.waf                        # 环境变量（实际）
```

### B. 相关链接

- [ModSecurity官方文档](https://github.com/SpiderLabs/ModSecurity)
- [OWASP CRS规则集](https://coreruleset.org/)
- [Nginx官方文档](https://nginx.org/en/docs/)
- [Let's Encrypt文档](https://letsencrypt.org/docs/)

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-15  
**维护者**: PMS Security Team
