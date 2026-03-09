# 数据库同步指南

多电脑开发时保持数据一致的解决方案。

## 📋 工作流程

### 主电脑（有完整数据）

```bash
# 1. 导出数据库
./sync-db.sh export

# 2. 提交到 GitHub
git add db-backups/
git commit -m "sync: 更新数据库备份 $(date +%Y-%m-%d)"
git push
```

### 其他电脑（需要同步数据）

```bash
# 1. 拉取最新代码和数据
git pull

# 2. 导入数据库
./sync-db.sh import

# 3. 启动项目
./start-dev.sh
```

---

## 🛠️ 命令说明

### sync-db.sh 命令

| 命令 | 说明 |
|------|------|
| `./sync-db.sh export` | 导出当前数据库到 `db-backups/` |
| `./sync-db.sh import` | 从 `db-backups/` 导入数据库 |
| `./sync-db.sh auto` | 自动模式：检测变更并导出 |
| `./sync-db.sh status` | 显示数据库状态 |
| `./sync-db.sh clean` | 清理旧备份（保留最近5个） |

### start-dev.sh 自动同步

启动脚本会自动检测：
- ✅ 如果有新的备份，自动导入
- ✅ 如果是首次运行，自动导入备份
- ✅ 如果本地数据库最新，跳过导入

---

## 📁 文件说明

```
db-backups/
├── backup-latest.sql      # 最新备份（软链接）
├── backup-latest.zip      # 压缩备份
├── backup-20260309-143022.sql  # 带时间戳的备份
├── backup-20260309-143022.zip
└── backup-metadata.json   # 备份元数据
```

---

## ⚠️ 注意事项

1. **数据库文件不直接提交到 Git**
   - `data/app.db` 在 `.gitignore` 中
   - 只提交 `db-backups/*.sql` 导出文件

2. **定期清理旧备份**
   ```bash
   ./sync-db.sh clean
   ```

3. **冲突处理**
   - 如果两台电脑同时修改了数据，先在一台导出
   - 另一台导入后再进行修改

4. **Windows 用户**
   - 使用 `sync-db.bat` 代替 `sync-db.sh`
   - 需要安装 SQLite3 命令行工具

---

## 🔧 安装 SQLite3 (Windows)

1. 下载：https://sqlite.org/download.html
2. 解压到 `C:\Program Files\SQLite3\`
3. 添加到系统 PATH

或者使用 Python 方式（已内置在脚本中）

---

## 💡 最佳实践

1. **每天下班前导出一次**
   ```bash
   ./sync-db.sh export && git add db-backups/ && git commit -m "sync: 日备份" && git push
   ```

2. **重要数据变更后立即导出**
   - 添加了新客户/项目
   - 修改了系统配置
   - 更新了演示数据

3. **新电脑首次设置**
   ```bash
   git clone https://github.com/fulingwei1/non-standard-automation-pms.git
   cd non-standard-automation-pms
   ./sync-db.sh import  # 导入完整数据
   ./start-dev.sh       # 启动项目
   ```

---

## 🆘 故障排除

### 导入失败
```bash
# 检查备份文件是否存在
ls -la db-backups/

# 手动导入
sqlite3 data/app.db < db-backups/backup-latest.sql
```

### 数据库损坏
```bash
# 恢复备份
cp data/app.db.backup-xxx data/app.db
```

### Git LFS 问题
```bash
# 安装 Git LFS
git lfs install

# 拉取 LFS 文件
git lfs pull
```
