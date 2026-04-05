# 仓库清障体检报告

> 生成日期: 2026-03-25
> 扫描范围: 全仓库（排除 node_modules、.git、venv）

---

## 摘要

| 类别 | 文件数 | 占用空间 | 风险等级 |
|------|--------|----------|----------|
| .bak 备份文件（未跟踪） | ~1,734 | 大量 | 可安全删除 |
| .bak 备份文件（已跟踪） | 3 | 小 | 可安全删除 |
| __pycache__ 目录 | 322 | 中等 | 可安全删除 |
| coverage_report_unit/ | ~1,000+ HTML | 70 MB | 可安全删除 |
| htmlcov/ | ~1,000+ HTML | 135 MB | 可安全删除 |
| data/ 数据库备份（已跟踪） | 9 | ~54 MB | 可安全删除 |
| data/ 历史报告文件（已跟踪） | ~50+ | ~66 MB | 需人工确认 |
| reports/ 交付报告 | 77 (tracked) | 7.6 MB | 需人工确认 |
| 一次性修复脚本 | 28+ | 小 | 需人工确认 |
| 前端调试工具脚本 | 4 (tracked) | 小 | 可安全删除 |
| migrations/skip/ | 26 | 小 | 需人工确认 |
| 前端 test-results/ | 3 (tracked) | 小 | 可安全删除 |
| logs/ | 2 | 76 KB | 可安全删除 |

---

## 一、可安全删除

这些文件不影响任何功能，删除无风险。

### 1.1 `.bak` 备份文件（~1,737 个）

几乎整个 `frontend/src/` 都有对应的 `.bak` 副本，属于某次批量操作的遗留产物。

**已被 Git 跟踪的 .bak 文件（3 个，需 git rm）：**
- `app/models/report.py.bak3`
- `app/models/report.py.bak7`
- `app/services/presale_ai_template_service.py.bak5`

**未跟踪的 .bak 文件（~1,734 个）：** 分布在：
- `frontend/src/components/` — UI 组件备份（含 ui/、business-support/、administrative-manager-workstation/ 等）
- `frontend/src/pages/` — 页面文件备份
- `frontend/src/utils/` — 工具函数备份
- `frontend/src/context/` — Context 备份
- `frontend/src/config/` — 配置备份
- `frontend/src/services/` — 服务层备份
- `frontend/src/routes/` — 路由备份
- `frontend/src/test/` — 测试工具备份
- `app/api/v1/endpoints/timesheet/` — 后端接口备份（6 个）
- `app/models/` — 模型备份（2 个）
- `app/schemas/` — Schema 备份（1 个）

**清理命令：**
```bash
# 删除所有未跟踪的 .bak 文件
find . -name "*.bak" -not -path "./node_modules/*" -not -path "./.git/*" -not -path "./venv/*" -delete

# 移除已跟踪的 .bak 文件
git rm app/models/report.py.bak3 app/models/report.py.bak7 app/services/presale_ai_template_service.py.bak5
```

### 1.2 `__pycache__` 目录（322 个）

Python 字节码缓存，可随时重新生成。.gitignore 已配置忽略，未被 Git 跟踪。

```bash
find . -type d -name "__pycache__" -not -path "./node_modules/*" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null
```

### 1.3 覆盖率报告目录（~205 MB）

| 目录 | 大小 | Git 跟踪 |
|------|------|----------|
| `coverage_report_unit/` | 70 MB | 否 |
| `htmlcov/` | 135 MB | 否 |

这些是 pytest 生成的 HTML 覆盖率报告，可随时重新生成。

```bash
rm -rf coverage_report_unit/ htmlcov/
```

### 1.4 `data/` 中的数据库备份文件（已跟踪，~54 MB）

以下文件是 SQLite 数据库的历史备份/损坏副本，**已被提交到 Git 仓库**，这既浪费空间又存在数据泄露风险：

| 文件 | 大小 |
|------|------|
| `data/app.db.backup.20260214171440` | 7.3 MB |
| `data/app.db.backup_20260201_002013` | 7.1 MB |
| `data/app.db.backup_before_resign_cleanup` | 8.5 MB |
| `data/app.db.backup_readonly` | 8.2 MB |
| `data/app.db.corrupted.20260204230903` | 7.1 MB |
| `data/app.db.corrupted_20260131_190350` | 8.2 MB |
| `data/app.db.new_20260205144617` | 7.1 MB |
| `data/app_backup_20260131_190342.sql` | 932 KB |
| `data/backup_after_seeding.sql` | 676 KB |

```bash
git rm data/app.db.backup.* data/app.db.backup_* data/app.db.corrupted* data/app.db.new_* data/app_backup_*.sql data/backup_after_seeding.sql
# 建议同时在 .gitignore 中添加: data/*.db* 和 data/*.sql
```

### 1.5 前端调试工具脚本（已跟踪，4 个）

位于 `frontend/src/test/`，属于测试修复时的一次性调试工具：

- `frontend/src/test/fixDetailTests.js` — 批量修复 Detail 测试 hooks
- `frontend/src/test/smartFixDetailTests.js` — 智能修复测试
- `frontend/src/test/analyzeDetailHooks.js` — 分析 Detail hooks
- `frontend/src/test/revertDetailFixes.js` — 回滚测试修复

```bash
git rm frontend/src/test/fixDetailTests.js frontend/src/test/smartFixDetailTests.js frontend/src/test/analyzeDetailHooks.js frontend/src/test/revertDetailFixes.js
```

### 1.6 前端 test-results（已跟踪，3 个）

调试截图和测试元数据，不应提交：

- `frontend/test-results/.last-run.json`
- `frontend/test-results/contract-create-debug.png`
- `frontend/test-results/quote-page-debug.png`

```bash
git rm -r frontend/test-results/
echo "frontend/test-results/" >> .gitignore
```

### 1.7 日志文件（未跟踪）

- `logs/backend.log`
- `logs/frontend.log`

```bash
rm -rf logs/
# .gitignore 已配置忽略 *.log，但建议加上 logs/ 目录
```

### 1.8 后端 API 备份文件（已跟踪）

- `app/api/v1/api_original.py.backup` — 原始 API 路由备份
- `app/api/v1/api_minimal_backup.py` — 精简版 API 备份

```bash
git rm app/api/v1/api_original.py.backup app/api/v1/api_minimal_backup.py
```

---

## 二、需要人工确认再删

### 2.1 `data/` 中的历史报告和调试文件（已跟踪，~50 个）

这些文件看起来是各团队的交付报告、路由扫描结果、调试产物，大部分是历史价值文件：

**团队交付报告（可能有参考价值）：**
- `data/Team3_交付文件清单.txt`
- `data/Team3_任务完成总结.md`
- `data/Team3_权限矩阵文档.md`
- `data/Team3_认证授权修复方案.md`
- `data/Team3_认证授权测试报告.md`
- `data/Team4_Core_API_Test_Report.md`
- `data/Team4_Deliverables_Checklist.txt`
- `data/Team4_Final_Delivery_Summary.md`
- `data/Team7_SQLAlchemy修复总结.md`
- `data/Team_4_产能分析_交付清单.txt`
- `data/team2_deliverables.md`
- `data/team2_files_created.txt`
- `data/team2_final_report.md`
- `data/team2_progress_report.md`

**路由扫描/调试产物（一次性使用）：**
- `data/route_fix_plan.md`
- `data/route_scan_report.txt`
- `data/route_scan_results.json` (576 KB)
- `data/route_test_report.txt`
- `data/route_test_results.json` (188 KB)
- `data/extracted_routes.json` (172 KB)
- `data/sqlalchemy_fixes_applied.md`
- `data/sqlalchemy_relationship_issues.json` (144 KB)
- `data/sqlalchemy_relationship_issues.md`
- `data/api_error_analysis.md`
- `data/auth_test_report.json`
- `data/core_api_verification.txt`
- `data/tables_need_tenant_id.txt`
- `data/tenant_scan_report.md`
- `data/test_core_api_report.json`
- `data/test_core_api_report.md`
- `data/QUICK_FIX_GUIDE.md`
- `data/ROUTE_TESTING_GUIDE.md`

**业务模板数据（可能仍在使用）：**
- `data/ATE-人事档案系统.xlsx`
- `data/公司优势产品规划（宣传册产品）2025.xlsx`
- `data/技术部-202512月工时汇总表(1).xlsx`
- `data/user_import_template.csv`
- `data/user_import_template.xlsx`
- `data/presale_solution_templates_samples.json`
- `data/非标自动化变更类型清单.md`
- `data/demo/` 目录
- `data/quotation_samples/` 目录
- `data/scoring_rules/` 目录

### 2.2 `reports/` 目录（已跟踪，77 个文件，7.6 MB）

包含交付报告、回归测试报告、种子数据报告等：

- `reports/code_quality_report_20260131.md`
- `reports/final_delivery_report_2026-03-01.md`
- `reports/regression-task6-2026-03-01T12-*/` — 回归测试报告（含 JSON + MD）
- `reports/seed_data_report.md`
- `reports/test_report_20260301.md`
- `reports/verify_seed_data_report.md`
- `reports/tmp-1.png` ~ `reports/tmp-4.png` — 临时截图

**建议：** 将历史报告归档或迁移到 wiki，`tmp-*.png` 可直接删除。

### 2.3 一次性修复脚本（已跟踪，28+ 个）

这些脚本看起来是历史修复操作的产物，已完成使命：

**`scripts/` 目录（Python）：**
- `scripts/fix_contract_approval.py`
- `scripts/fix_dashboard_mock_data.py`
- `scripts/fix_frontend_mock_data.py`
- `scripts/fix_imports.py`
- `scripts/fix_manufacturing_dashboard.py`
- `scripts/fix_mock_data.py`
- `scripts/fix_pagination.py`
- `scripts/fix_single_file.py`
- `scripts/fix_sqlalchemy_relationships.py`
- `scripts/fix_state_initialization.py`
- `scripts/fix_superuser_data.py`
- `scripts/fix_syntax_errors.py`
- `scripts/fix_test_indents.py`
- `scripts/auto_fix_mock_data.py`
- `scripts/batch_fix_remaining_pages.py`
- `scripts/quick_fix.py`
- `scripts/quick_fix_high_priority.py`
- `scripts/repair_initiation_projects.py`

**`scripts/` 目录（Shell）：**
- `scripts/batch_fix_mock_data.sh`
- `scripts/fix_remaining_issues.sh`
- `scripts/fix_remaining_mock_data.sh`

**`frontend/` 根目录：**
- `frontend/fix-imports.sh`
- `frontend/fix-missing-mocks.sh`
- `frontend/fix-mocks-v2.py`
- `frontend/fix-mocks-v3.py`
- `frontend/fix-test-assertions.py`
- `frontend/fix-test-mocks.py`
- `frontend/add-missing-mock-methods.py`

**建议：** 确认这些修复已应用后可以安全删除。保留 `scripts/deployment/` 和 `scripts/install-hooks.sh` 等仍在使用的脚本。

### 2.4 `migrations/skip/` 目录（26 个迁移文件）

包含被标记为跳过的数据库迁移，需要确认是否已被其他迁移覆盖：

- 多个 `20250712_*` 早期迁移
- 多个 `20260120_*` ~ `20260127_*` 迁移
- `202601XX_*` 占位命名的迁移

**建议：** 确认主 `migrations/` 目录中是否已有替代版本后删除。

### 2.5 `eslint-report.json`（前端根目录，已跟踪）

- `frontend/eslint-report.json` — ESLint 检查报告，应在 CI 中生成而非提交。

### 2.6 后端 `app/models/engineer_performance/test.py`

文件名为 `test.py`，包含 `TestBugRecord` 等模型。需确认是测试模型还是误命名的生产模型。

---

## 三、不建议删除

### 3.1 Sales V2 模型

虽有 V1/V2 共存现象，但属于正常版本迭代：
- `app/models/sales/target_v2.py`
- `app/models/sales/lead_requirement_v2.py`

### 3.2 正在使用的 Shell 脚本

以下脚本有持续使用价值：
- `start.sh` / `start-dev.sh` / `sync-db.sh` — 开发环境启动
- `scripts/deployment/deploy.sh` — 部署脚本
- `scripts/install-hooks.sh` — Git hooks 安装
- `scripts/backup_database.sh` / `scripts/restore_database.sh` — 数据库备份恢复
- `tests/run_api_integration_tests.sh` — API 集成测试
- `docker/nginx/ssl/generate-cert.sh` — SSL 证书生成

### 3.3 `docs/` 中的设计文档

即使部分过时，设计文档有参考价值，不建议删除。

---

## 四、重复页面/废弃组件检查

### 4.1 疑似重复

| 文件 A | 文件 B | 说明 |
|--------|--------|------|
| `pages/FinancialReports.jsx` | `pages/FinancialReports/` 目录 | 页面重构为目录结构，旧文件可能已废弃 |
| `pages/ShortageReportDetail.jsx` | `pages/ShortageReportDetail/` 目录 | 同上 |
| `pages/DispatchManagement.jsx` | `pages/InstallationDispatchManagement.jsx` | 功能可能重叠，需确认 |
| `app/api/v1/endpoints/sales/targets.py` | `app/api/v1/endpoints/sales_targets.py` | 两套 SalesTarget API（V1 vs V2） |

### 4.2 历史修复报告堆积

`data/` 和 `reports/` 中累积了大量历史交付报告（Team2~Team7），建议归档到项目 wiki 或独立仓库。

---

## 五、后端 Pytest 运行指南

### 环境准备

```bash
cd /Users/fulingwei/.openclaw/workspace/non-standard-automation-pms
source venv/bin/activate
pip install -r api/requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock factory-boy faker httpx pytest-timeout email-validator
```

### 运行命令

```bash
# 全部测试（带覆盖率）
python -m pytest tests/ -o 'addopts=' -q --tb=short --cov=app --timeout=30

# 仅单元测试（最快）
pytest tests/unit/ -v

# 仅集成测试
pytest tests/integration/ -v

# 仅 API 测试
pytest tests/api/ -v

# 按标记运行
pytest -m "not slow" -v
pytest -m unit -v

# 单个文件
pytest tests/unit/test_stage_template_service.py -v
```

### 配置说明

- **数据库**: 默认使用内存 SQLite（无需 Docker）
- **Redis**: 测试中已 mock，无需启动
- **异步模式**: `asyncio_mode = auto`（自动处理 async 测试）
- **超时**: 建议加 `--timeout=30` 防止测试挂起
- **注意**: `pytest.ini` 默认带覆盖率参数，用 `-o 'addopts='` 可跳过

---

## 六、建议的 .gitignore 补充

```gitignore
# 备份文件
*.bak
*.bak[0-9]
*.backup

# 覆盖率报告
coverage_report_unit/
htmlcov/
.coverage

# 日志
logs/

# 测试产物
frontend/test-results/

# 数据库文件
data/*.db
data/*.db.*
data/*.sql

# ESLint 报告
frontend/eslint-report.json
```

---

## 七、清理优先级建议

1. **立即处理（高收益低风险）：** 更新 .gitignore → 删除未跟踪的 .bak 和 __pycache__ → 删除 coverage_report_unit/ 和 htmlcov/
2. **尽快处理（需 git rm）：** 移除已跟踪的数据库备份（data/*.db.*）、.bak 文件、test-results、debug 脚本
3. **确认后处理：** 归档 data/ 和 reports/ 中的历史报告、清理一次性修复脚本、处理 migrations/skip/
4. **长期治理：** 确认重复页面/API 的使用情况并统一
