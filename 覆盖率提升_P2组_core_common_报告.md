# 覆盖率提升报告 - P2组：core + common 模块

**时间**: 2026-02-17  
**负责人**: P2 子代理  
**测试文件**: `tests/unit/test_core_common_coverage.py`  
**测试数量**: 138 个测试，全部通过 ✅

---

## 执行结果摘要

```
======================= 138 passed, 5 warnings in 0.30s ========================
```

---

## 覆盖率改善详情

| 文件 | 语句数 | 覆盖前 | 覆盖后 | 提升 |
|------|--------|--------|--------|------|
| `app/core/permissions/tenant_access.py` | 51 | 0% | **100%** | +100% ✅ |
| `app/common/statistics/helpers.py` | 33 | 0% | **100%** | +100% ✅ |
| `app/common/pagination.py` | 33 | - | **97%** | +97% ✅ |
| `app/core/encryption.py` | 49 | 0% | **81%** | +81% ✅ |
| `app/core/secret_manager.py` | 122 | 0% | **75%** | +75% ✅ |
| `app/core/api_key_auth.py` | 60 | 0% | **73%** | +73% ✅ |
| `app/core/request_signature.py` | 57 | 0% | **79%** | +79% ✅ |
| `app/common/dashboard/base.py` | 75 | 46% | **59%** | +13% ✅ |
| `app/common/reports/renderers.py` | 104 | 0% | **29%** | +29% ⚠️ |
| `app/common/statistics/base.py` | 122 | 0% | **19%** | +19% ⚠️ |

---

## 测试类别说明

### ✅ 完全覆盖文件

#### `app/core/permissions/tenant_access.py` → 100%
- `TestCheckTenantAccess` (7 个测试)：超管访问、普通用户访问、跨租户拒绝、系统级资源等
- `TestValidateTenantMatch` (6 个测试)：空参数、相同 tenant、不同 tenant、系统级混入
- `TestEnsureTenantConsistency` (5 个测试)：自动设置、越权拒绝、自定义字段
- `TestCheckBulkAccess` (4 个测试)：批量检查正常/异常情形

#### `app/common/statistics/helpers.py` → 100%
- `TestFormatCurrency` (5 个测试)：None/零/大金额/万元格式化
- `TestFormatHours` (5 个测试)：None/整数/浮点/自定义精度
- `TestFormatPercentage` (4 个测试)：None/正常/100%/0%
- `TestCreateStatCard` (5 个测试)：基础卡片/可选字段
- `TestCreateStatsResponse` (2 个测试)：空/非空列表
- `TestCalculateTrend` (5 个测试)：正/负趋势、零除数、类型保留

### ✅ 高覆盖文件（>70%）

#### `app/core/request_signature.py` → 79%
- `TestRequestSignatureVerifier` (8 个测试)：签名计算、过期时间戳、无效格式、错误签名、Query 参数
- `TestGenerateClientSignature` (4 个测试)：返回类型、时间戳近期性、Base64 验证

#### `app/core/api_key_auth.py` → 73%
- `TestAPIKeyAuth` (11 个测试)：生成/哈希/验证 API Key，过期/IP 白名单/ImportError 场景
- `TestRequireApiKeyScope` (1 个测试)：返回可调用对象

#### `app/core/secret_manager.py` → 75%
- `TestSecretKeyManager` (14 个测试)：生成/验证密钥、密钥轮转、旧密钥管理、环境变量加载

#### `app/core/encryption.py` → 81%
- `TestDataEncryption` (8 个测试)：加密/解密往返、None/空字符串、每次密文不同、generate_key

### ⚠️ 受限文件（依赖第三方库）

#### `app/common/reports/renderers.py` → 29%
- `TestBaseRenderer` (3 个测试)：抽象类保护、具体实现、模板存储
- `TestExcelRenderer` (2 个测试)：无依赖报错、mock 依赖调用
- `TestWordRenderer`, `TestPDFRenderer` (各 1 个测试)：缺少 reportlab/python-docx 时报 ImportError

> **注**：PDF/Excel/Word 渲染核心逻辑依赖 `reportlab`、`pandas`、`openpyxl`、`python-docx` 第三方库，在不安装依赖情况下无法直接覆盖渲染主体代码。

#### `app/common/statistics/base.py` → 19%
- `TestBaseStatisticsService` (4 个测试)：初始化、无效字段错误、无效周期错误、分布计算

> **注**：`BaseStatisticsService` 的核心方法都是 `async` 且需要真实数据库（`AsyncSession`），需要与 DB fixtures 配合才能进一步提升覆盖率。目前仅测试了结构和错误路径。

---

## 测试技术要点

1. **settings 懒加载处理**：`pagination.py` 和 `secret_manager.py` 在函数内部 `from app.core.config import settings`，需要 patch `app.core.config.settings` 而非模块属性。

2. **加密实例化**：`DataEncryption` 有模块级单例，测试时直接构造内部属性绕开环境变量依赖。

3. **APIKey 模型**：`app.models.api_key` 未实现，通过 `patch.dict("sys.modules", ...)` 模拟 ImportError 行为。

4. **异步测试**：`BaseStatisticsService` 的测试使用 `@pytest.mark.asyncio`，通过 mock `count_by_field` 协程函数。

5. **抽象类测试**：验证 `ABC` 不能直接实例化，然后测试具体子类的正常行为。

---

## Git Commit

```
commit 012442aa
test(core/common): add coverage tests for core and common modules
```

---

## 文件列表

- 新增测试文件：`tests/unit/test_core_common_coverage.py`（138 个测试，~470 行）
