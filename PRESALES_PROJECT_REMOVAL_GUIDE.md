# presales-project 文件夹删除指南

## 一、依赖检查结果

✅ **所有依赖都是可选的**，可以安全删除 `presales-project` 文件夹。

## 二、当前引用情况

### 1. `scripts/seed_scoring_rules.py`
- **引用**: `presales-project/presales-evaluation-system/scoring_rules_v2.0.json`
- **状态**: ✅ 已处理
- **说明**: 
  - 评分规则已导入到数据库（版本2.0，6995字符）
  - 脚本已更新，优先使用项目内的 `data/scoring_rules/scoring_rules_v2.0.json`
  - 如果文件不存在，会使用内置的默认规则

### 2. `scripts/migrate_presales_data.py`
- **引用**: `presales-project/presales-evaluation-system/prisma/dev.db`
- **状态**: ⚠️ 可选
- **说明**: 
  - 仅用于一次性迁移历史数据
  - 如果已完成数据迁移，不再需要此脚本
  - 如果未迁移，请先运行迁移脚本

## 三、删除前检查清单

### ✅ 已完成
- [x] 评分规则已导入到数据库
- [x] 评分规则JSON文件已复制到 `data/scoring_rules/`
- [x] `seed_scoring_rules.py` 已更新，不依赖 presales-project

### ⚠️ 需要确认
- [ ] 是否已完成历史数据迁移？
  - 如果已迁移：可以删除
  - 如果未迁移：先运行 `python3 scripts/migrate_presales_data.py`

## 四、删除步骤

### 步骤1: 确认数据迁移状态

```bash
# 检查是否有历史评估数据需要迁移
python3 scripts/migrate_presales_data.py --check-only
```

### 步骤2: 验证评分规则

```bash
# 确认评分规则已正确导入
python3 -c "
from app.models.base import get_session
from app.models.sales import ScoringRule
db = get_session()
rule = db.query(ScoringRule).filter(ScoringRule.is_active==True).first()
print('评分规则:', '已导入' if rule else '未导入')
if rule:
    print(f'版本: {rule.version}, 长度: {len(rule.rules_json)} 字符')
db.close()
"
```

### 步骤3: 备份（可选）

如果需要保留 presales-project 作为参考：

```bash
# 备份到其他位置
mv presales-project ~/backup/presales-project-backup-$(date +%Y%m%d)
```

### 步骤4: 删除

```bash
# 删除 presales-project 文件夹
rm -rf presales-project
```

## 五、删除后的影响

### ✅ 不受影响的功能
- 技术评估功能（完全独立）
- 评分规则管理（使用数据库中的规则）
- 所有API端点
- 前端页面

### ⚠️ 不再可用的功能
- 历史数据迁移（如果未迁移）
- 从 presales-project 读取评分规则JSON（已复制到项目内）

## 六、验证删除

删除后运行测试，确保一切正常：

```bash
# 1. 测试评分规则初始化（应该使用项目内的文件或默认规则）
python3 scripts/seed_scoring_rules.py

# 2. 测试评估功能
python3 scripts/quick_test_assessment.py

# 3. 检查是否有任何错误引用
grep -r "presales-project" . --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null
```

## 七、总结

### 可以安全删除的条件
1. ✅ 评分规则已导入到数据库
2. ✅ 评分规则JSON已复制到项目内
3. ✅ 已完成历史数据迁移（如需要）

### 删除命令
```bash
rm -rf presales-project
```

### 恢复方法（如需要）
如果删除后发现问题，可以从备份恢复或重新克隆 presales-project。

---

**检查脚本**: `scripts/check_presales_dependencies.py`
**最后更新**: 2026-01-07






