# 文档清理计划

## 可以安全删除的文件

### 1. 列表文件（未被任何代码引用）
- ✅ `services_list.txt` - 服务列表，未被引用
- ✅ `unit_tests_list.txt` - 单元测试列表，未被引用

### 2. 重复文档
- ✅ `test-coverage-analysis.md` - 与 `TEST_COVERAGE_ANALYSIS.md` 重复，保留大写版本

## 可以归档的文件（历史记录）

### 总结类文档（已完成的工作）
这些是历史工作记录，可以移动到 `docs/archive/summaries/`：

- `engineer-performance-data-automation-summary.md`
- `engineer-performance-implementation-summary.md`
- `payment-management-refactoring-summary.md`
- `purchase-orders-refactoring-summary.md`
- `refactoring-session-summary.md`
- `sales-team-optimization-summary.md`
- `sales-team-refactoring-summary.md`
- `TEST_OPTIMIZATION_SUMMARY.md`

### 报告类文档（历史分析报告）
这些是历史分析报告，可以移动到 `docs/archive/reports/`：

- `TEST_AUTO_OPTIMIZATION_REPORT.md`
- `代码质量分析报告.md`（如果不再需要）

## 需要保留的文件

### 被引用的文档
- `INDEX.md` - 文档索引，引用了 `DOCUMENTATION_ORGANIZATION_REPORT.md`
- `DOCUMENTATION_ORGANIZATION_REPORT.md` - 被 INDEX.md 引用

### 可能有用的指南
- `服务测试编写指南.md` - 测试编写指南，可能有参考价值
- `CODE_STANDARDS.md` - 代码标准，可能有参考价值
- `PERFORMANCE_OPTIMIZATION.md` - 性能优化指南
- `TEST_AND_CI_CD_OPTIMIZATION.md` - 测试和CI/CD优化指南
- `N加1查询问题优化总结.md` - 性能优化参考

### 部署相关（已移动到 docs/guides/）
- `VERCEL_DEPLOYMENT.md`
- `VERCEL_FULLSTACK_DEPLOYMENT.md`

## 执行清理 ✅ 已完成

已执行的清理操作：

```bash
# ✅ 已删除无用文件
rm docs/services_list.txt
rm docs/unit_tests_list.txt
rm docs/test-coverage-analysis.md

# ✅ 已归档历史文档
mv docs/*summary*.md docs/archive/summaries/
mv docs/engineer-performance-*.md docs/archive/summaries/
mv docs/TEST_AUTO_OPTIMIZATION_REPORT.md docs/archive/reports/
```

### 清理结果

- **删除文件**: 3 个（列表文件2个 + 重复文档1个）
- **归档文件**: 15 个（总结文档14个 + 报告文档1个）
- **保留文档**: 13 个（有用的指南和索引文档）

## 注意事项

1. **删除前备份**：建议先备份整个 docs/ 目录
2. **检查引用**：确保没有代码或脚本引用这些文件
3. **保留索引**：INDEX.md 和其引用的文档需要保留
4. **归档而非删除**：历史文档建议归档而不是直接删除
