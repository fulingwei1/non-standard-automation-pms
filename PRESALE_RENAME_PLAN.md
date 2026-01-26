# 售前模块重命名方案

## 问题诊断

### 当前状态

| 模块名称 | 路由前缀 | 职责 | 问题 |
|---------|---------|------|------|
| `presale` | ` ` (无) | 售前业务管理 | 名称清晰 ✅ |
| `presales_integration` | `/presale-integration` | 售前数据分析 | 命名混淆 ❌ |

### 混淆点

1. **模块名**: `presale` vs `presales_integration`
   - 名称过于相似
   - `presales` 中的 's' 容易混淆

2. **路由前缀**: (无) vs `/presale-integration`
   - `presale-integration` 和 `presale` 很难区分

3. **职责边界**:
   - `presale`: 日常业务操作（工单、方案、投标）
   - `presales_integration`: 数据分析与洞察（中标率、资源分析、绩效）
   - 职责清晰，但命名不体现差异

## 重命名方案

### 新命名

```
presale            → presale          (保持不变)
presales_integration → presale_analytics (新名称)
```

### 路由对比

| 旧路由 | 新路由 |
|-------|-------|
| `/presale/tickets/` | `/presale/tickets/` (保持) |
| `/presale/proposals/` | `/presale/proposals/` (保持) |
| `/presale/bids/` | `/presale/bids/` (保持) |
| `/presale-integration/lead-conversion/` | `/presale-analytics/lead-conversion/` ✨ |
| `/presale-integration/win-rate/` | `/presale-analytics/win-rate/` ✨ |
| `/presale-integration/resource-analysis/` | `/presale-analytics/resource-analysis/` ✨ |
| `/presale-integration/salesperson/` | `/presale-analytics/salesperson/` ✨ |
| `/presale-integration/dashboard/` | `/presale-analytics/dashboard/` ✨ |

### 命名优势

✅ **清晰的职责区分**:
- `presale` = 业务管理（Management）
- `presale_analytics` = 数据分析（Analytics）

✅ **一致的前缀**:
- 都使用 `presale` 前缀，表明同一领域
- 后缀 `analytics` 明确表示分析功能

✅ **避免混淆**:
- `presale` vs `presale_analytics` 一目了然
- 路由也更清晰：`/presale/` vs `/presale-analytics/`

## 重命名步骤

### Phase 1: 目录重命名

```bash
# 重命名目录
mv app/api/v1/endpoints/presales_integration \
   app/api/v1/endpoints/presale_analytics
```

### Phase 2: 更新模块内部

更新 `presale_analytics/__init__.py`:
```python
# 更新模块文档字符串
"""
售前数据分析模块

提供售前业务的数据分析与决策支持：
- lead_conversion: 线索转项目分析
- win_rate: 中标率预测
- resource_analysis: 资源投入分析
- salesperson: 销售人员绩效
- dashboard: 售前分析仪表板
"""
```

### Phase 3: 更新导入引用

#### 3.1 主API路由 (app/api/v1/api.py)

```python
# 旧导入
from app.api.v1.endpoints import presales_integration

api_router.include_router(
    presales_integration.router,
    prefix="/presale-integration",
    tags=["presale-integration"]
)

# 新导入
from app.api.v1.endpoints import presale_analytics

api_router.include_router(
    presale_analytics.router,
    prefix="/presale-analytics",
    tags=["presale-analytics"]
)
```

#### 3.2 查找所有引用

```bash
grep -r "presales_integration" app/ --include="*.py" | grep -v __pycache__
```

### Phase 4: 更新文档和注释

- API文档标签
- OpenAPI描述
- 代码注释
- README/文档

### Phase 5: 验证

```bash
# 语法检查
python3 -m py_compile app/api/v1/endpoints/presale_analytics/__init__.py

# 导入测试
python3 -c "from app.api.v1.endpoints.presale_analytics import router; print('✅ 导入成功')"

# 路由测试
python3 -c "from app.api.v1.api import api_router; print(f'✅ API路由包含 {len(api_router.routes)} 个端点')"
```

## 影响范围评估

### 后端影响

| 影响范围 | 数量 | 风险 |
|---------|------|------|
| Python 导入语句 | ~5处 | 🟡 中 |
| 路由注册 | 1处 | 🟢 低 |
| API端点URL | 5个 | 🔴 高 |

### 前端影响

⚠️ **重要**: 如果前端硬编码了 `/presale-integration/` URL，需要同步更新

需要检查的前端文件：
```bash
grep -r "presale-integration" frontend/ --include="*.ts" --include="*.tsx" --include="*.js"
grep -r "presales.integration" frontend/ --include="*.ts" --include="*.tsx"
```

### 文档影响

需要更新：
- API文档 (OpenAPI/Swagger)
- 开发者文档
- 使用说明

## 向后兼容方案（可选）

如果需要保持向后兼容，可以添加路由别名：

```python
# 新路由
api_router.include_router(
    presale_analytics.router,
    prefix="/presale-analytics",
    tags=["presale-analytics"]
)

# 兼容旧路由（带deprecation警告）
api_router.include_router(
    presale_analytics.router,
    prefix="/presale-integration",  # 旧路由
    tags=["presale-integration"],
    deprecated=True
)
```

## 建议

### 推荐方案: 立即重命名

✅ **原因**:
1. 命名混淆是严重的技术债务
2. 越早修复，影响范围越小
3. 提升代码可维护性

### 实施时间

- **开发环境**: 立即执行
- **生产环境**: 与前端团队协调后执行
- **预计工作量**: 2-3小时（包括测试）

### 风险控制

1. **前端协调**: 提前通知前端团队更新API调用
2. **灰度发布**: 先保持旧路由兼容，1-2个版本后移除
3. **充分测试**: 完整的端到端测试

---

**制定时间**: 2026-01-25
**制定人**: Claude Code
**状态**: 待审批
