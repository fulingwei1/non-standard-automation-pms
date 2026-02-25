# CI Ruff Lint Failures - 758 Errors

**Created:** 2026-02-25 12:00  
**Priority:** High  
**Type:** Code Quality  
**Status:** Open

## Problem

GitHub CI workflow失败，Ruff检测到758个代码质量问题：
- 634个可自动修复的问题
- 119个需要unsafe-fixes的问题

## Error Details

主要问题类型：
1. **F401** - 未使用的导入 (imported but unused)
2. **F841** - 未使用的变量 (assigned to but never used)

### 高频问题文件

**Services:**
- `app/services/bom_attributes/bom_attributes_service.py` - 多处unused variable `bom`
- `app/services/change_impact_ai_service.py` - unused imports (os, Tuple)
- `app/services/cost_*.py` - 大量unused imports
- `app/services/presale_ai_*.py` - 大量unused imports
- `app/services/production/` - 多个文件有unused imports

**Tests:**
- `app/tests/services/` - 很多测试文件有unused imports (MagicMock等)

## Recommended Actions

### 自动修复 (优先)
```bash
ruff check --fix app/
```

### 审查不安全修复
```bash
ruff check --unsafe-fixes app/
```

### CI修复验证
```bash
gh run watch
```

## Impact
- ❌ CI/CD Pipeline被阻塞
- ⚠️ 代码质量下降
- 📦 可能影响部署

## Next Steps
1. [ ] 运行自动修复
2. [ ] 提交修复commit
3. [ ] 验证CI通过
4. [ ] 考虑添加pre-commit hook避免再次引入

## Related
- CI Run: https://github.com/fulingwei1/non-standard-automation-pms/actions
- Last failed: 2026-02-25 03:44 UTC
