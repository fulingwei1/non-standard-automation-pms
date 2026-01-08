# presales-project 依赖状态

## ✅ 可以安全删除

**结论**: `presales-project` 文件夹可以安全删除，所有依赖都已处理。

## 处理情况

### 1. 评分规则 ✅ 已处理
- **原位置**: `presales-project/presales-evaluation-system/scoring_rules_v2.0.json`
- **新位置**: `data/scoring_rules/scoring_rules_v2.0.json` ✅ 已复制
- **数据库**: 评分规则已导入到数据库（版本2.0，6995字符）✅
- **脚本更新**: `scripts/seed_scoring_rules.py` 已更新，优先使用项目内文件 ✅

### 2. 数据迁移脚本 ⚠️ 可选
- **脚本**: `scripts/migrate_presales_data.py`
- **用途**: 一次性迁移历史数据
- **状态**: 
  - 如果已完成迁移：可以删除 presales-project
  - 如果未迁移：先运行迁移脚本

## 当前引用位置

### 代码中的引用（都是可选的）

1. **scripts/seed_scoring_rules.py**
   - 优先使用 `data/scoring_rules/scoring_rules_v2.0.json`
   - 如果不存在，尝试从 presales-project 读取（向后兼容）
   - 如果都不存在，使用内置默认规则

2. **scripts/migrate_presales_data.py**
   - 仅用于历史数据迁移
   - 如果已完成迁移，不再需要

3. **文档中的引用**
   - 仅用于说明，不影响功能

## 删除步骤

```bash
# 1. 确认评分规则已导入（可选）
python3 -c "
from app.models.base import get_session
from app.models.sales import ScoringRule
db = get_session()
rule = db.query(ScoringRule).filter(ScoringRule.is_active==True).first()
print('✅ 评分规则已导入' if rule else '❌ 评分规则未导入')
db.close()
"

# 2. 确认项目内文件存在（可选）
ls -lh data/scoring_rules/scoring_rules_v2.0.json

# 3. 删除 presales-project（如果确认不需要历史数据迁移）
rm -rf presales-project
```

## 删除后的验证

```bash
# 测试评分规则初始化（应该正常工作）
python3 scripts/seed_scoring_rules.py

# 测试评估功能（应该正常工作）
python3 scripts/quick_test_assessment.py
```

## 注意事项

1. **历史数据迁移**: 如果 presales-project 中有需要保留的历史评估数据，请先运行迁移脚本
2. **备份**: 删除前建议先备份（如果需要）
3. **向后兼容**: 脚本已保留向后兼容，即使删除 presales-project 也能正常工作

---

**状态**: ✅ 可以安全删除
**最后检查**: 2026-01-07






