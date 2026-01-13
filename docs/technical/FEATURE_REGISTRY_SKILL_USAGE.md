# 功能注册维护技能使用指南

> 技能名称：`feature-registry-maintenance`  
> 触发词：新增功能、更新功能表、生成功能报告

## 🎯 技能功能

当您说"新增功能"时，这个技能会自动执行以下步骤：

1. ✅ **扫描系统功能** - 运行 `scan_system_features.py` 更新功能表
2. ✅ **生成功能报告** - 运行 `generate_feature_report.py` 生成状态报告
3. ✅ **分析缺失项** - 查看报告，识别缺失权限和前端的功能
4. ✅ **创建权限迁移脚本** - 为缺失权限的功能创建迁移脚本
5. ✅ **执行权限迁移** - 将权限定义添加到数据库
6. ✅ **添加权限检查** - 在API端点中添加权限检查
7. ✅ **评估前端需求** - 评估缺失前端的功能是否需要前端页面
8. ✅ **生成总结报告** - 生成维护总结报告

---

## 📝 使用方法

### 触发技能

只需说以下任一短语：

- **"新增功能"**
- **"更新功能表"**
- **"生成功能报告"**
- **"检查功能状态"**
- **"维护功能注册表"**

### 示例对话

**用户：** "新增功能"

**AI：** 将自动执行：
1. 扫描系统功能
2. 生成功能报告
3. 分析缺失项
4. 创建权限迁移脚本（如需要）
5. 提供维护建议

---

## 🔍 技能执行流程

### 步骤1：扫描功能

```bash
python3 scripts/scan_system_features.py
```

**输出：**
- 功能统计
- 缺失权限列表
- 缺失前端列表

### 步骤2：生成报告

```bash
python3 scripts/generate_feature_report.py
```

**输出：**
- `docs/SYSTEM_FEATURES_REPORT.md` - 完整功能状态报告

### 步骤3：分析缺失项

从报告中提取：
- 缺失权限的功能（按优先级排序）
- 缺失前端的功能（评估是否需要）

### 步骤4：创建权限迁移脚本

为缺失权限的功能创建迁移脚本：
- `migrations/YYYYMMDD_missing_permissions_batch_sqlite.sql`
- `migrations/YYYYMMDD_missing_permissions_batch_mysql.sql`

### 步骤5：执行迁移（如需要）

如果创建了迁移脚本，执行它们：
```bash
sqlite3 data/app.db < migrations/YYYYMMDD_missing_permissions_batch_sqlite.sql
```

### 步骤6：添加权限检查

为高优先级功能添加权限检查到API端点。

### 步骤7：评估前端

评估缺失前端的功能是否需要前端页面。

### 步骤8：生成总结

生成维护总结报告，包括：
- 已完成的工作
- 剩余工作
- 下一步建议

---

## 📊 输出示例

执行技能后，您将看到：

```
✅ 功能扫描完成
   - 总功能数: 44
   - 有API: 44
   - 有权限: 14
   - 有前端: 38

✅ 功能报告已生成: docs/SYSTEM_FEATURES_REPORT.md

⚠️  缺失权限: 29 个功能
   - business-support (42个端点) - 高优先级
   - service (39个端点) - 高优先级
   - ...

⚠️  缺失前端: 6 个功能
   - audits
   - data-import-export
   - ...

✅ 已创建权限迁移脚本: migrations/20260110_missing_permissions_batch_sqlite.sql

💡 建议：
   1. 执行权限迁移脚本
   2. 为高优先级功能添加权限检查
   3. 评估缺失前端的功能
```

---

## 📚 相关文档

- `docs/FEATURE_REGISTRY_SYSTEM.md` - 功能注册系统完整文档
- `docs/FEATURE_REGISTRY_QUICK_GUIDE.md` - 快速参考指南
- `docs/SYSTEM_FEATURES_REPORT.md` - 功能状态报告（自动生成）

---

## ✅ 技能已创建

技能位置：`/Users/flw/.claude/skills/feature-registry-maintenance/`

**包含内容：**
- `SKILL.md` - 技能主文档
- `references/workflow.md` - 工作流程文档
- `references/permission_patterns.md` - 权限编码模式

**打包文件：** `feature-registry-maintenance.skill`

下次您说"新增功能"时，技能会自动触发并执行所有维护步骤！
