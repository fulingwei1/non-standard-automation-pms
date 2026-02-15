# WAF故障排查手册

> **版本**: 1.0.0  
> **日期**: 2026-02-15  
> **目标**: WAF故障诊断与快速恢复

---

## 目录

1. [常见故障](#常见故障)
2. [诊断流程](#诊断流程)
3. [故障排查工具](#故障排查工具)
4. [典型案例](#典型案例)
5. [紧急处理](#紧急处理)
6. [预防措施](#预防措施)

---

## 常见故障

### 1. 服务无法启动

#### 症状

```bash
$ docker-compose -f docker-compose.waf.yml up -d
ERROR: Container pms-waf exited with code 1
```

#### 可能原因

| 原因 | 检查方法 | 解决方案 |
|------|----------|----------|
| 端口被占用 | `netstat -tlnp \| grep 80` | 停止占用进程或更改端口 |
| 配置文件错误 | `nginx -t` | 修复语法错误 |
| SSL证书缺失 | `ls docker/nginx/ssl/` | 生成SSL证书 |
| 权限问题 | `ls -la logs/` | 修正目录权限 |

#### 排查步骤

```bash
# 1. 查看容器日志
docker-compose -f docker-compose.waf.yml logs nginx-waf

# 2. 测试Nginx配置
docker-compose -f docker-compose.waf.yml exec nginx-waf nginx -t

# 3. 检查端口占用
sudo netstat -tlnp | grep -E '(80|443)'

# 4. 检查SSL证书
ls -la docker/nginx/ssl/
openssl x509 -in docker/nginx/ssl/pms.crt -noout -text

# 5. 检查文件权限
ls -la docker/nginx/
ls -la logs/nginx/
```

---

### 2. 正常请求被误拦截

#### 症状

```
客户端收到: 403 Forbidden
日志显示: ModSecurity: Access denied with code 403
```

#### 诊断步骤

**步骤1: 确认误报**

```bash
# 查看最近的拦截日志
tail -100 logs/nginx/modsec_audit.log

# 搜索特定URL的拦截记录
grep "/api/v1/your-endpoint" logs/nginx/modsec_audit.log
```

**步骤2: 识别触发规则**

```bash
# 提取规则ID
grep "/api/v1/your-endpoint" logs/nginx/modsec_audit.log | \
    grep -oP '(?<=\[id ")[^"]+'

# 查看规则详情
grep -A 10 'id "920420"' docker/nginx/modsecurity/custom-rules.conf
```

**步骤3: 临时解决**

```apache
# 编辑 docker/nginx/modsecurity/main.conf
# 添加排除规则

# 方法1: 排除特定规则
SecRule REQUEST_URI "@beginsWith /api/v1/your-endpoint" \
    "id:90001,phase:1,nolog,pass,ctl:ruleRemoveById=920420"

# 方法2: 提高阈值
SecRule REQUEST_URI "@beginsWith /api/v1/your-endpoint" \
    "id:90002,phase:1,nolog,pass,setvar:tx.inbound_anomaly_score_threshold=10"

# 方法3: 完全跳过（不推荐）
SecRule REQUEST_URI "@beginsWith /api/v1/your-endpoint" \
    "id:90003,phase:1,nolog,pass,ctl:ruleEngine=Off"
```

**步骤4: 重新加载配置**

```bash
# 重启WAF服务
docker-compose -f docker-compose.waf.yml restart nginx-waf

# 或仅重新加载配置
docker-compose -f docker-compose.waf.yml exec nginx-waf nginx -s reload
```

**步骤5: 验证修复**

```bash
# 重新测试请求
curl -v "https://your-domain/api/v1/your-endpoint"

# 查看日志确认不再拦截
tail -f logs/nginx/access.log
```

---

### 3. 性能下降

#### 症状

- 响应时间显著增加（>100ms）
- CPU使用率持续高于80%
- 请求处理缓慢

#### 诊断步骤

**步骤1: 监控资源使用**

```bash
# 查看容器资源使用
docker stats pms-waf

# 输出示例:
# CONTAINER   CPU %   MEM USAGE / LIMIT   MEM %
# pms-waf     95%     1.8GB / 2GB        90%     ← 资源紧张
```

**步骤2: 分析慢查询**

```bash
# 查看响应时间超过1秒的请求
awk '$NF > 1 {print $0}' logs/nginx/access.log | tail -20

# 统计平均响应时间
awk '{sum+=$NF; count++} END {print "平均响应时间:", sum/count, "秒"}' logs/nginx/access.log
```

**步骤3: 检查WAF配置**

```bash
# 检查是否启用了响应体检查
grep "SecResponseBodyAccess" docker/nginx/modsecurity/main.conf

# 检查偏执级别
grep "PARANOIA" .env.waf
```

#### 优化方案

**方案1: 降低偏执级别**

```bash
# 编辑 .env.waf
PARANOIA=1  # 从2或3降到1

# 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf
```

**方案2: 禁用响应体检查**

```apache
# 编辑 docker/nginx/modsecurity/main.conf
SecResponseBodyAccess Off  # 改为Off

# 或仅针对静态资源
SecRule REQUEST_URI "@rx \.(jpg|png|css|js)$" \
    "id:90010,phase:1,nolog,pass,ctl:responseBodyAccess=Off"
```

**方案3: 增加资源**

```yaml
# 编辑 docker-compose.waf.yml
services:
  nginx-waf:
    deploy:
      resources:
        limits:
          cpus: '4'      # 增加到4核
          memory: 4G     # 增加到4GB
```

**方案4: 跳过部分检查**

```apache
# 静态文件不检查请求体
SecRule REQUEST_URI "@rx ^/static/" \
    "id:90011,phase:1,nolog,pass,ctl:requestBodyAccess=Off"
```

---

### 4. SSL证书问题

#### 症状

```
浏览器警告: ERR_CERT_DATE_INVALID
或
curl: (60) SSL certificate problem: certificate has expired
```

#### 诊断步骤

**步骤1: 检查证书有效期**

```bash
# 查看证书详情
openssl x509 -in docker/nginx/ssl/pms.crt -noout -dates

# 输出:
# notBefore=Feb 15 00:00:00 2026 GMT
# notAfter=Feb 14 23:59:59 2025 GMT  ← 已过期！
```

**步骤2: 检查证书链**

```bash
# 验证证书链完整性
openssl verify -CAfile docker/nginx/ssl/chain.pem docker/nginx/ssl/pms.crt
```

#### 解决方案

**自签名证书**:
```bash
# 重新生成证书
cd docker/nginx/ssl
bash generate-cert.sh
docker-compose -f docker-compose.waf.yml restart nginx-waf
```

**Let's Encrypt证书**:
```bash
# 手动续期
sudo certbot renew

# 复制新证书
sudo cp /etc/letsencrypt/live/pms.yourdomain.com/fullchain.pem docker/nginx/ssl/pms.crt
sudo cp /etc/letsencrypt/live/pms.yourdomain.com/privkey.pem docker/nginx/ssl/pms.key

# 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf
```

---

### 5. 日志文件过大

#### 症状

```bash
$ df -h
/dev/sda1   50G   48G   0   100% /
```

```bash
$ du -sh logs/nginx/*
15G    logs/nginx/access.log
8G     logs/nginx/modsec_audit.log
```

#### 解决方案

**紧急清理**:
```bash
# 截断日志文件（保留文件句柄）
truncate -s 0 logs/nginx/access.log
truncate -s 0 logs/nginx/modsec_audit.log

# 或手动归档
gzip logs/nginx/access.log
mv logs/nginx/access.log.gz logs/nginx/archive/
touch logs/nginx/access.log

# 重新打开日志文件
docker-compose -f docker-compose.waf.yml exec nginx-waf nginx -s reopen
```

**配置日志轮转**:
```bash
# 创建 /etc/logrotate.d/nginx-waf
sudo tee /etc/logrotate.d/nginx-waf <<'EOF'
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

# 测试配置
sudo logrotate -d /etc/logrotate.d/nginx-waf

# 手动执行
sudo logrotate -f /etc/logrotate.d/nginx-waf
```

---

### 6. 容器频繁重启

#### 症状

```bash
$ docker-compose -f docker-compose.waf.yml ps
NAME      STATUS
pms-waf   Restarting (1) 3 seconds ago
```

#### 诊断步骤

**步骤1: 查看重启日志**

```bash
# 查看最近的容器日志
docker logs pms-waf --tail 100

# 查看系统日志
sudo journalctl -u docker -n 50
```

**步骤2: 检查健康检查**

```bash
# 手动执行健康检查
docker exec pms-waf curl -f http://localhost/health

# 查看健康检查配置
docker inspect pms-waf | grep -A 10 Healthcheck
```

**步骤3: 检查内存限制**

```bash
# 查看容器资源限制
docker stats pms-waf --no-stream

# 检查OOM日志
dmesg | grep -i "out of memory"
sudo journalctl -k | grep -i "killed process"
```

#### 解决方案

**内存不足**:
```yaml
# 编辑 docker-compose.waf.yml
services:
  nginx-waf:
    deploy:
      resources:
        limits:
          memory: 4G  # 增加内存限制
```

**健康检查失败**:
```yaml
# 调整健康检查参数
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/health"]
  interval: 60s          # 增加检查间隔
  timeout: 20s           # 增加超时时间
  retries: 5             # 增加重试次数
  start_period: 120s     # 增加启动时间
```

---

## 诊断流程

### 标准诊断流程图

```
[故障发生]
    ↓
[收集现象]
    ├─ 错误信息
    ├─ 日志文件
    └─ 资源状态
    ↓
[初步判断]
    ├─ 服务层面? → [检查容器状态]
    ├─ 配置层面? → [验证配置文件]
    ├─ 性能层面? → [分析资源使用]
    └─ 规则层面? → [分析拦截日志]
    ↓
[定位根因]
    ↓
[实施修复]
    ↓
[验证结果]
    ↓
[记录文档]
```

### 快速诊断命令清单

```bash
#!/bin/bash
# WAF快速诊断脚本

echo "======================================"
echo "WAF快速诊断"
echo "======================================"

echo ""
echo "[1] 容器状态"
docker-compose -f docker-compose.waf.yml ps

echo ""
echo "[2] 容器资源使用"
docker stats pms-waf --no-stream

echo ""
echo "[3] 配置文件验证"
docker-compose -f docker-compose.waf.yml exec nginx-waf nginx -t

echo ""
echo "[4] 端口监听"
docker exec pms-waf netstat -tlnp

echo ""
echo "[5] 最近错误日志（最新20条）"
tail -20 logs/nginx/error.log

echo ""
echo "[6] 最近拦截（最新10条）"
tail -10 logs/nginx/blocked.log

echo ""
echo "[7] 磁盘使用"
df -h | grep -E '(Filesystem|/$)'

echo ""
echo "[8] 日志文件大小"
du -sh logs/nginx/*

echo "======================================"
```

---

## 故障排查工具

### 1. 日志查看工具

```bash
# 实时查看多个日志
tail -f logs/nginx/access.log logs/nginx/error.log logs/nginx/blocked.log

# 使用multitail（需安装）
multitail logs/nginx/access.log logs/nginx/error.log

# 使用less查看压缩日志
zless logs/nginx/access.log.gz
```

### 2. 网络诊断工具

```bash
# 测试连接
curl -v http://localhost/health
curl -v https://localhost/health --insecure

# 测试SSL
openssl s_client -connect localhost:443 -servername pms.example.com

# 查看DNS解析
nslookup pms.example.com
dig pms.example.com

# 追踪路由
traceroute pms.example.com
```

### 3. 配置验证工具

```bash
# Nginx配置测试
docker exec pms-waf nginx -t

# 查看生效的配置
docker exec pms-waf nginx -T

# ModSecurity规则测试
# 使用msc_test（需安装ModSecurity测试工具）
```

### 4. 性能分析工具

```bash
# Apache Bench压力测试
ab -n 1000 -c 10 http://localhost/health

# wrk压力测试
wrk -t4 -c100 -d30s http://localhost/api/v1/health

# 查看系统负载
top -p $(docker inspect -f '{{.State.Pid}}' pms-waf)
htop -p $(docker inspect -f '{{.State.Pid}}' pms-waf)
```

---

## 典型案例

### 案例1: 上传功能无法使用

#### 现象

```
客户端错误: 413 Request Entity Too Large
```

#### 排查过程

1. **检查Nginx配置**
   ```bash
   grep "client_max_body_size" docker/nginx/nginx.conf
   # 输出: client_max_body_size 10M;  ← 限制为10MB
   ```

2. **检查ModSecurity配置**
   ```bash
   grep "SecRequestBodyLimit" docker/nginx/modsecurity/main.conf
   # 输出: SecRequestBodyLimit 13107200  ← 约12.5MB
   ```

#### 解决方案

```nginx
# 方法1: 全局提高限制（不推荐）
# 编辑 docker/nginx/nginx.conf
client_max_body_size 50M;

# 方法2: 仅上传接口提高限制（推荐）
# 编辑 docker/nginx/conf.d/pms.conf
location /api/v1/upload {
    client_max_body_size 50M;
    # ...
}
```

```apache
# ModSecurity单独配置
SecRule REQUEST_URI "@beginsWith /api/v1/upload" \
    "id:90020,phase:1,nolog,pass,ctl:requestBodyLimit=52428800"
```

```bash
# 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf
```

---

### 案例2: 移动端APP无法访问

#### 现象

```
移动端APP显示: 网络错误
浏览器访问正常
```

#### 排查过程

1. **查看拦截日志**
   ```bash
   grep "403" logs/nginx/access.log | grep "MobileApp"
   ```

2. **发现User-Agent被拦截**
   ```
   [msg "Empty User-Agent Detected"]
   ```

3. **分析原因**
   - APP使用了自定义User-Agent
   - 或未设置User-Agent

#### 解决方案

```apache
# 白名单APP的User-Agent
SecRule REQUEST_HEADERS:User-Agent "@contains YourMobileApp" \
    "id:90030,phase:1,nolog,pass,ctl:ruleRemoveById=10100"

# 或允许空User-Agent（不推荐）
SecRuleRemoveById 10100
```

---

### 案例3: API网关集成失败

#### 现象

```
API网关错误: 502 Bad Gateway
直接访问后端正常
```

#### 排查过程

1. **检查反向代理配置**
   ```bash
   grep "proxy_pass" docker/nginx/conf.d/pms.conf
   ```

2. **测试后端连接**
   ```bash
   docker exec pms-waf curl http://127.0.0.1:8000/api/v1/health
   ```

3. **检查网络**
   ```bash
   docker network ls
   docker network inspect pms-network
   ```

#### 解决方案

```nginx
# 修正proxy_pass配置
# 错误: proxy_pass http://127.0.0.1:8000;
# 正确: proxy_pass http://backend:8000;  （使用Docker服务名）
```

```yaml
# 确保网络配置正确
# docker-compose.waf.yml
services:
  nginx-waf:
    networks:
      - pms-network
  backend:
    networks:
      - pms-network
```

---

## 紧急处理

### 紧急场景处理流程

#### 1. WAF导致业务中断

**立即行动**:
```bash
# 方法1: 切换到DetectionOnly模式（推荐）
# 编辑 .env.waf
MODSEC_RULE_ENGINE=DetectionOnly

# 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf

# 方法2: 完全关闭WAF（仅极端情况）
# 编辑 docker/nginx/modsecurity/main.conf
SecRuleEngine Off

# 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf
```

**恢复后续**:
1. 收集误报日志
2. 分析根本原因
3. 调整规则
4. 测试验证
5. 重新启用拦截模式

#### 2. 性能严重下降

**立即行动**:
```bash
# 1. 降低偏执级别
PARANOIA=1

# 2. 禁用响应体检查
SecResponseBodyAccess Off

# 3. 限制并发连接
limit_conn addr 50;  # 降低限制

# 4. 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf
```

#### 3. 证书过期

**立即行动**:
```bash
# 快速生成自签名证书（临时）
cd docker/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout pms.key -out pms.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=PMS/CN=pms.example.com"

# 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf

# 后续申请正式证书
export CERT_TYPE=letsencrypt
bash docker/nginx/ssl/generate-cert.sh
```

---

## 预防措施

### 1. 监控告警

```bash
# 设置监控脚本（每5分钟检查）
# crontab -e
*/5 * * * * /path/to/scripts/waf/health-check.sh
```

**health-check.sh**:
```bash
#!/bin/bash

# 检查容器状态
if ! docker ps | grep -q "pms-waf.*Up"; then
    echo "ALERT: WAF容器未运行"
    # 发送告警
    # curl -X POST "$WEBHOOK_URL" -d "{...}"
    exit 1
fi

# 检查健康端点
if ! curl -f http://localhost/health &> /dev/null; then
    echo "ALERT: WAF健康检查失败"
    # 发送告警
    exit 1
fi

# 检查磁盘空间
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 80 ]; then
    echo "ALERT: 磁盘使用率 ${disk_usage}%"
    # 发送告警
fi

echo "WAF健康检查通过"
```

### 2. 定期备份

```bash
#!/bin/bash
# 每日备份脚本

BACKUP_DIR="/backup/waf/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 备份配置文件
cp -r docker/nginx "$BACKUP_DIR/"
cp .env.waf "$BACKUP_DIR/"
cp docker-compose.waf.yml "$BACKUP_DIR/"

# 备份日志（最近7天）
find logs/nginx -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

# 压缩
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

# 清理旧备份（保留30天）
find /backup/waf -name "*.tar.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR.tar.gz"
```

### 3. 变更管理流程

```
[配置变更请求]
    ↓
[在测试环境验证]
    ↓
[备份当前配置]
    ↓
[在DetectionOnly模式下部署]
    ↓
[观察24小时]
    ↓
[切换到On模式]
    ↓
[持续监控]
```

### 4. 文档维护

- **变更日志**: 记录每次配置变更
- **故障记录**: 记录故障原因和解决方案
- **规则清单**: 维护自定义规则文档
- **联系人列表**: 维护应急联系人

---

## 附录: 常用命令速查

### Docker管理

```bash
# 启动服务
docker-compose -f docker-compose.waf.yml up -d

# 停止服务
docker-compose -f docker-compose.waf.yml down

# 重启服务
docker-compose -f docker-compose.waf.yml restart nginx-waf

# 查看日志
docker-compose -f docker-compose.waf.yml logs -f nginx-waf

# 进入容器
docker exec -it pms-waf sh

# 重新加载配置
docker exec pms-waf nginx -s reload
```

### 日志分析

```bash
# 查看实时日志
tail -f logs/nginx/access.log

# 统计状态码
awk '{print $9}' logs/nginx/access.log | sort | uniq -c

# 查找错误
grep "error" logs/nginx/error.log

# 统计拦截次数
wc -l logs/nginx/blocked.log
```

### 配置管理

```bash
# 测试配置
docker exec pms-waf nginx -t

# 查看生效配置
docker exec pms-waf nginx -T

# 备份配置
cp docker/nginx/nginx.conf docker/nginx/nginx.conf.bak

# 恢复配置
cp docker/nginx/nginx.conf.bak docker/nginx/nginx.conf
```

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-15  
**维护者**: PMS Security Team  
**紧急联系**: security@pms.example.com
