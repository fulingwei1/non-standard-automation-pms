# 恢复操作手册

## ⚠️ 重要提示

**数据恢复是高风险操作，可能覆盖当前数据！**

在执行恢复前，请务必：
1. ✅ 备份当前数据
2. ✅ 验证恢复文件完整性
3. ✅ 在测试环境先执行验证
4. ✅ 获得必要的授权批准
5. ✅ 通知相关人员

---

## 🎯 恢复场景

### 场景1: 数据误删除
**症状**: 用户误删除了重要数据  
**恢复目标**: 从最近的备份恢复被删除的数据  
**RTO**: < 1小时

### 场景2: 数据库损坏
**症状**: 数据库无法启动或表损坏  
**恢复目标**: 完全恢复数据库  
**RTO**: < 2小时

### 场景3: 服务器故障
**症状**: 服务器硬件故障或系统崩溃  
**恢复目标**: 在新服务器上恢复完整系统  
**RTO**: < 4小时

### 场景4: 灾难恢复
**症状**: 机房断电、火灾等灾难  
**恢复目标**: 在异地恢复完整业务  
**RTO**: < 24小时

---

## 🔍 恢复前准备

### 1. 评估影响范围

```bash
# 检查当前数据库状态
mysql -u pms_user -p -e "SHOW DATABASES"
mysql -u pms_user -p pms -e "SHOW TABLES"

# 检查数据库大小
mysql -u pms_user -p -e "
SELECT 
  table_schema AS 'Database',
  ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'pms'
GROUP BY table_schema"
```

### 2. 选择恢复点

```bash
# 列出所有可用备份
ls -lh /var/backups/pms/pms_*.sql.gz

# 查看备份创建时间
stat /var/backups/pms/pms_20260215_020000.sql.gz

# 如果使用OSS，列出远程备份
ossutil ls oss://pms-backups/database/
```

### 3. 验证备份文件

```bash
# 验证备份完整性
bash scripts/verify_backup.sh /var/backups/pms/pms_20260215_020000.sql.gz

# 查看备份内容（前100行）
gunzip < /var/backups/pms/pms_20260215_020000.sql.gz | head -100

# 检查表结构
gunzip < /var/backups/pms/pms_20260215_020000.sql.gz | grep "CREATE TABLE"
```

### 4. 准备恢复环境

```bash
# 停止应用服务（避免写入冲突）
docker-compose down

# 或只停止应用容器
docker-compose stop app

# 检查数据库服务状态
docker-compose ps db
mysql -u pms_user -p -e "SELECT 1"
```

---

## 💾 数据库恢复步骤

### 方法1: 使用恢复脚本（推荐）

#### 步骤1: 选择备份文件
```bash
# 列出可用备份
ls -lh /var/backups/pms/pms_*.sql.gz

# 选择要恢复的文件
BACKUP_FILE=/var/backups/pms/pms_20260215_020000.sql.gz
```

#### 步骤2: 执行恢复
```bash
# 运行恢复脚本
bash scripts/restore_database.sh $BACKUP_FILE
```

#### 步骤3: 确认操作
```
⚠️⚠️⚠️  警告  ⚠️⚠️⚠️
此操作将恢复数据库，可能覆盖当前数据！
数据库: pms@localhost:3306
备份文件: /var/backups/pms/pms_20260215_020000.sql.gz

确认要恢复数据库吗？(输入 yes 继续): yes  # 输入 yes 确认
```

#### 步骤4: 等待完成
```bash
# 脚本会自动：
# 1. 备份当前数据库
# 2. 验证MD5
# 3. 执行恢复
# 4. 验证恢复结果

# 成功输出示例:
# ✅ 数据库恢复完成
#   备份文件: /var/backups/pms/pms_20260215_020000.sql.gz
#   当前数据备份至: /var/backups/pms/before_restore_20260215_143000.sql.gz
# ✅ 数据库表数量: 42
```

### 方法2: 手动恢复

#### 步骤1: 备份当前数据
```bash
mysqldump -u pms_user -p \
  --single-transaction \
  --databases pms \
  | gzip > /var/backups/pms/before_restore_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### 步骤2: 解压并导入
```bash
# 方式1: 一步完成
gunzip < pms_20260215_020000.sql.gz | mysql -u pms_user -p

# 方式2: 先解压再导入
gunzip pms_20260215_020000.sql.gz
mysql -u pms_user -p < pms_20260215_020000.sql
```

#### 步骤3: 验证恢复
```bash
mysql -u pms_user -p pms -e "SHOW TABLES"
mysql -u pms_user -p pms -e "SELECT COUNT(*) FROM users"
```

---

## 📁 文件恢复步骤

### 恢复上传文件

#### 步骤1: 选择备份
```bash
ls -lh /var/backups/pms/uploads_*.tar.gz
```

#### 步骤2: 执行恢复
```bash
bash scripts/restore_files.sh uploads_20260215_030000.tar.gz
```

#### 步骤3: 确认
```
确认要恢复 uploads 吗？(yes/no): yes
```

#### 步骤4: 验证
```bash
ls -lh /var/www/pms/uploads/
du -sh /var/www/pms/uploads/
```

### 恢复配置文件

⚠️ **警告**: 配置文件恢复会覆盖当前配置，可能导致服务异常！

```bash
# 备份当前配置
cp /var/www/pms/.env /var/www/pms/.env.current
cp /var/www/pms/docker-compose.yml /var/www/pms/docker-compose.yml.current

# 执行恢复
bash scripts/restore_files.sh configs_20260215_030000.tar.gz configs

# 检查恢复的配置
cat /var/www/pms/.env
cat /var/www/pms/docker-compose.yml

# 重启服务使配置生效
docker-compose restart
```

---

## 🔄 完整恢复流程

### 场景: 完全灾难恢复（新服务器）

#### 阶段1: 基础环境准备
```bash
# 1. 安装Docker
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

# 2. 克隆项目
git clone https://github.com/your-org/pms.git /var/www/pms
cd /var/www/pms

# 3. 创建备份目录
sudo mkdir -p /var/backups/pms /var/log/pms
sudo chown $USER:$USER /var/backups/pms /var/log/pms
```

#### 阶段2: 下载备份文件
```bash
# 从OSS下载最新备份
ossutil cp oss://pms-backups/full/pms_full_20260216_010000.tar.gz /tmp/

# 解压完整备份
cd /var/backups/pms
tar -xzf /tmp/pms_full_20260216_010000.tar.gz

# 或者只下载数据库备份
ossutil cp oss://pms-backups/database/pms_20260215_020000.sql.gz /var/backups/pms/
```

#### 阶段3: 恢复配置
```bash
# 解压配置文件
tar -xzf configs_20260215_030000.tar.gz -C /

# 修改配置（如有必要）
vim /var/www/pms/.env
```

#### 阶段4: 启动数据库
```bash
cd /var/www/pms
docker-compose up -d db

# 等待数据库就绪
sleep 10
docker-compose exec db mysql -u root -p -e "SELECT 1"
```

#### 阶段5: 恢复数据库
```bash
bash scripts/restore_database.sh /var/backups/pms/pms_20260215_020000.sql.gz
```

#### 阶段6: 恢复文件
```bash
bash scripts/restore_files.sh /var/backups/pms/uploads_20260215_030000.tar.gz
```

#### 阶段7: 启动应用
```bash
docker-compose up -d
docker-compose logs -f app
```

#### 阶段8: 验证
```bash
# 检查服务状态
docker-compose ps

# 访问应用
curl http://localhost:8000/api/v1/health

# 登录测试
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

---

## ✅ 恢复后验证

### 1. 数据库验证
```bash
# 连接数据库
mysql -u pms_user -p pms

# 检查表数量
SHOW TABLES;

# 检查关键表数据
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM tasks;

# 检查最新记录
SELECT * FROM users ORDER BY created_at DESC LIMIT 5;
```

### 2. 应用验证
```bash
# 访问首页
curl http://localhost:8000/

# 检查API
curl http://localhost:8000/api/v1/health

# 登录测试
# 使用浏览器访问 http://your-server:8000
# 尝试登录并操作
```

### 3. 功能验证
- [ ] 用户登录正常
- [ ] 数据查询正常
- [ ] 文件上传/下载正常
- [ ] 报表生成正常
- [ ] 权限控制正常

---

## 🔧 常见问题

### 问题1: 恢复后无法登录

**原因**: 密码可能已重置或不匹配

**解决**:
```bash
# 重置管理员密码
docker-compose exec app python reset_admin_password.py
```

### 问题2: 恢复后缺少数据

**原因**: 可能恢复了旧备份

**解决**:
1. 检查备份文件创建时间
2. 确认恢复的是正确的备份
3. 如需要，恢复更新的备份

### 问题3: 配置文件冲突

**原因**: 新旧配置不兼容

**解决**:
```bash
# 对比配置差异
diff /var/www/pms/.env.current /var/www/pms/.env

# 手动合并配置
vim /var/www/pms/.env

# 重启服务
docker-compose restart
```

### 问题4: 文件权限问题

**原因**: 恢复后文件所有者错误

**解决**:
```bash
# 修复权限
sudo chown -R www-data:www-data /var/www/pms/uploads
sudo chmod -R 755 /var/www/pms/uploads
```

---

## 📊 恢复时间估算

| 恢复类型 | 数据量 | 预计耗时 | 操作复杂度 |
|---------|--------|---------|----------|
| 单表恢复 | < 1GB | 5-10分钟 | 中等 |
| 数据库完整恢复 | ~500MB | 15-30分钟 | 中等 |
| 文件恢复 | ~2GB | 20-40分钟 | 简单 |
| 完整系统恢复 | ~3GB | 1-2小时 | 复杂 |
| 灾难恢复（新服务器） | ~3GB | 2-4小时 | 非常复杂 |

---

## 🚨 应急联系

### 紧急恢复流程
1. **评估**: 确认故障范围和影响
2. **通知**: 通知相关人员和用户
3. **隔离**: 隔离故障系统，防止扩大
4. **恢复**: 执行恢复操作
5. **验证**: 全面验证恢复结果
6. **通告**: 通知恢复完成

### 联系人
- **系统管理员**: admin@example.com / 135xxxx
- **DBA**: dba@example.com / 136xxxx
- **技术总监**: cto@example.com / 137xxxx
- **应急热线**: 400-xxx-xxxx

---

## 📝 恢复操作记录模板

```markdown
## 恢复操作记录

**操作时间**: 2026-02-15 14:30:00  
**操作人员**: 张三  
**故障原因**: 用户误删除项目数据  
**恢复范围**: projects表  
**备份文件**: pms_20260215_020000.sql.gz  
**恢复时长**: 25分钟  

**操作步骤**:
1. 14:30 - 备份当前数据库
2. 14:35 - 验证备份文件
3. 14:40 - 执行恢复
4. 14:55 - 验证恢复结果
5. 15:00 - 重启服务
6. 15:05 - 用户验证确认

**结果**: ✅ 恢复成功  
**数据丢失**: 2小时数据（最近备份为凌晨2点）  
**业务影响**: 系统暂停25分钟  
**后续改进**: 增加每4小时备份策略  
```

---

**相关文档**:
- [备份策略设计](./backup_strategy.md)
- [备份操作手册](./backup_operations.md)
- [灾难恢复计划](./disaster_recovery_plan.md)
