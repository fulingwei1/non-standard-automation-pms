# 备份操作手册

## 📖 目的

本手册为系统管理员提供数据备份系统的日常操作指南，包括安装配置、手动备份、监控检查等操作步骤。

**适用人员**: 系统管理员、运维人员  
**前置条件**: 已部署PMS系统，具有服务器SSH访问权限

---

## 🚀 快速开始

### 1. 安装准备

#### 检查系统要求
```bash
# 检查MySQL客户端
mysql --version
# 输出示例: mysql  Ver 8.0.32

# 检查磁盘空间（至少40GB）
df -h /var/backups
```

#### 创建备份目录
```bash
sudo mkdir -p /var/backups/pms
sudo mkdir -p /var/log/pms
sudo chown $USER:$USER /var/backups/pms /var/log/pms
```

#### 赋予脚本执行权限
```bash
cd /var/www/pms
chmod +x scripts/*.sh
```

### 2. 配置环境变量

#### 复制配置模板
```bash
cp .env.backup .env.backup.local
vim .env.backup.local
```

#### 修改关键配置
```bash
# 数据库密码
MYSQL_PASSWORD=your_actual_password

# OSS配置（如果使用）
OSS_BUCKET=pms-backups
OSS_ACCESS_KEY_ID=your_key_id
OSS_ACCESS_KEY_SECRET=your_secret

# 通知配置
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY
```

#### 加载环境变量
```bash
source .env.backup.local

# 或追加到主 .env 文件
cat .env.backup.local >> .env
```

### 3. 配置定时任务

#### 编辑crontab
```bash
crontab -e
```

#### 粘贴定时任务
```bash
# 数据库备份（每天凌晨2点）
0 2 * * * cd /var/www/pms && /var/www/pms/scripts/backup_database.sh >> /var/log/pms/backup.log 2>&1

# 文件备份（每天凌晨3点）
0 3 * * * cd /var/www/pms && /var/www/pms/scripts/backup_files.sh >> /var/log/pms/backup.log 2>&1

# 完整备份（每周日凌晨1点）
0 1 * * 0 cd /var/www/pms && /var/www/pms/scripts/backup_full.sh >> /var/log/pms/backup.log 2>&1

# 备份监控（每4小时）
0 */4 * * * cd /var/www/pms && /var/www/pms/scripts/monitor_backup.sh >> /var/log/pms/backup-monitor.log 2>&1

# 恢复测试（每周一凌晨5点）
0 5 * * 1 cd /var/www/pms && /var/www/pms/scripts/test_restore.sh >> /var/log/pms/restore-test.log 2>&1
```

#### 验证crontab
```bash
crontab -l
```

---

## 💾 手动备份操作

### 数据库备份

#### 基本用法
```bash
cd /var/www/pms
bash scripts/backup_database.sh
```

#### 指定备份目录
```bash
BACKUP_DIR=/custom/path bash scripts/backup_database.sh
```

#### 查看输出
```bash
# 成功输出示例:
# [2026-02-15 14:30:00] ========== 开始数据库备份 ==========
# [2026-02-15 14:30:00] 数据库: pms@localhost:3306
# [2026-02-15 14:30:00] 备份文件: /var/backups/pms/pms_20260215_143000.sql.gz
# [2026-02-15 14:30:15] ✅ 数据库备份完成
# [2026-02-15 14:30:15]   文件: /var/backups/pms/pms_20260215_143000.sql.gz
# [2026-02-15 14:30:15]   大小: 95MB
# [2026-02-15 14:30:15]   MD5: a1b2c3d4e5f6...
```

### 文件备份

```bash
bash scripts/backup_files.sh
```

### 完整备份

```bash
bash scripts/backup_full.sh
```

---

## 🔍 备份验证

### 验证最新备份
```bash
bash scripts/verify_backup.sh
```

### 验证指定备份
```bash
bash scripts/verify_backup.sh /var/backups/pms/pms_20260215_020000.sql.gz
```

### 验证输出解读
```bash
# 成功输出示例:
# [2026-02-15 14:35:00] ========== 备份验证工具 ==========
# [2026-02-15 14:35:00] 验证文件: /var/backups/pms/pms_20260215_020000.sql.gz
# [2026-02-15 14:35:00] 1️⃣  文件大小检查
# [2026-02-15 14:35:00]   ✅ 通过: 95MB
# [2026-02-15 14:35:01] 2️⃣  MD5完整性检查
# [2026-02-15 14:35:01]   ✅ 通过: MD5校验成功
# [2026-02-15 14:35:02] 3️⃣  GZIP格式检查
# [2026-02-15 14:35:02]   ✅ 通过: GZIP格式正确
# [2026-02-15 14:35:03] 4️⃣  SQL内容检查
# [2026-02-15 14:35:03]   ✅ 通过: 有效的MySQL导出文件
# [2026-02-15 14:35:05] 5️⃣  数据库表检查
# [2026-02-15 14:35:05]   ✅ 通过: 包含 42 个表
# [2026-02-15 14:35:06] 6️⃣  数据内容检查
# [2026-02-15 14:35:06]   ✅ 通过: 包含 1523 条INSERT语句
# [2026-02-15 14:35:06] ✅ 备份验证通过！
```

---

## 📊 监控检查

### 执行监控检查
```bash
bash scripts/monitor_backup.sh
```

### 监控输出示例
```bash
# [2026-02-15 10:00:00] ========== 备份监控检查 ==========
# [2026-02-15 10:00:00] 1️⃣  检查备份目录
# [2026-02-15 10:00:00]   ✅ 备份目录正常
# [2026-02-15 10:00:00] 2️⃣  检查数据库备份
# [2026-02-15 10:00:00]   ✅ 最新备份: 8小时前
# [2026-02-15 10:00:00]   ✅ 备份大小正常: 95MB
# [2026-02-15 10:00:00] 3️⃣  检查文件备份
# [2026-02-15 10:00:00]   ✅ 文件备份正常: 9小时前
# [2026-02-15 10:00:00] 4️⃣  检查备份数量
# [2026-02-15 10:00:00]   数据库备份数量: 7
# [2026-02-15 10:00:00] 5️⃣  检查磁盘空间
# [2026-02-15 10:00:00]   磁盘使用率: 45%
# [2026-02-15 10:00:00]   可用空间: 25G
# [2026-02-15 10:00:00] ✅ 所有检查通过，备份系统运行正常
```

---

## 🔧 常见操作

### 列出所有备份
```bash
ls -lh /var/backups/pms/pms_*.sql.gz
```

### 查看备份大小
```bash
du -sh /var/backups/pms/*
```

### 查看最新备份
```bash
ls -lt /var/backups/pms/pms_*.sql.gz | head -1
```

### 手动清理旧备份
```bash
# 删除7天前的备份
find /var/backups/pms -name "pms_*.sql.gz" -mtime +7 -delete
```

### 查看备份日志
```bash
# 实时查看
tail -f /var/log/pms/backup.log

# 查看最近50行
tail -50 /var/log/pms/backup.log

# 搜索错误
grep -i "error\|failed" /var/log/pms/backup.log
```

---

## ☁️ OSS远程存储操作

### 配置ossutil
```bash
# 安装ossutil
wget https://gosspublic.alicdn.com/ossutil/1.7.16/ossutil64
chmod +x ossutil64
sudo mv ossutil64 /usr/local/bin/ossutil

# 配置
cp scripts/ossutil.config.example ~/.ossutilconfig
vim ~/.ossutilconfig  # 修改AccessKey和Endpoint
```

### 上传备份到OSS
```bash
# 上传单个文件
ossutil cp /var/backups/pms/pms_20260215_020000.sql.gz oss://pms-backups/database/

# 批量上传
ossutil cp /var/backups/pms/ oss://pms-backups/database/ -r --include "pms_*.sql.gz"
```

### 从OSS下载备份
```bash
# 列出远程备份
ossutil ls oss://pms-backups/database/

# 下载指定文件
ossutil cp oss://pms-backups/database/pms_20260215_020000.sql.gz /tmp/
```

### 清理OSS旧备份
```bash
# 列出旧文件（30天前）
ossutil ls oss://pms-backups/database/ | grep $(date -d '30 days ago' +%Y%m)

# 删除（谨慎操作！）
ossutil rm oss://pms-backups/database/pms_20260115_*.sql.gz
```

---

## 📈 使用API管理备份

### 创建备份
```bash
curl -X POST http://localhost:8000/api/v1/backups \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "full"}'
```

### 列出备份
```bash
curl http://localhost:8000/api/v1/backups?backup_type=database \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 获取备份统计
```bash
curl http://localhost:8000/api/v1/backups/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 检查备份健康
```bash
curl http://localhost:8000/api/v1/backups/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ⚠️ 故障排查

### 备份失败

#### 症状
```
❌ 错误: 数据库备份失败
```

#### 排查步骤
1. **检查数据库连接**
   ```bash
   mysql -u pms_user -p -e "SELECT 1"
   ```

2. **检查磁盘空间**
   ```bash
   df -h /var/backups
   ```

3. **检查权限**
   ```bash
   ls -ld /var/backups/pms
   # 应该显示可写权限
   ```

4. **查看详细错误**
   ```bash
   tail -100 /var/log/pms/backup.log
   ```

### OSS上传失败

#### 症状
```
⚠️  警告: OSS上传失败，但本地备份已完成
```

#### 排查步骤
1. **检查ossutil配置**
   ```bash
   ossutil ls oss://pms-backups/
   ```

2. **检查网络连接**
   ```bash
   ping oss-cn-hangzhou.aliyuncs.com
   ```

3. **检查AccessKey权限**
   - 登录阿里云控制台
   - 检查RAM用户权限是否包含OSS写入

### 磁盘空间不足

#### 症状
```
🚨 告警: 磁盘空间严重不足: 95%
```

#### 解决方案
1. **手动清理旧备份**
   ```bash
   find /var/backups/pms -name "*.sql.gz" -mtime +3 -delete
   ```

2. **上传到OSS后删除本地**
   ```bash
   # 上传
   ossutil cp /var/backups/pms/ oss://pms-backups/archive/ -r
   
   # 验证后删除
   rm /var/backups/pms/pms_202601*.sql.gz
   ```

3. **扩容磁盘**（根据实际情况）

---

## 📝 操作检查清单

### 每日检查
- [ ] 查看备份日志，确认昨晚备份成功
- [ ] 检查磁盘空间使用率
- [ ] 查看告警通知

### 每周检查
- [ ] 查看恢复测试日志
- [ ] 验证最新完整备份
- [ ] 检查OSS存储用量

### 每月检查
- [ ] 执行一次完整恢复演练
- [ ] 审查备份策略是否需要调整
- [ ] 检查备份成本

---

## 📞 联系支持

如遇到无法解决的问题，请联系：

- **系统管理员**: admin@example.com
- **技术支持**: support@example.com
- **紧急电话**: 400-xxx-xxxx

---

**下一步**: 阅读 [恢复操作手册](./restore_operations.md)
