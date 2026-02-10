# 错误处理统一化文档索引

## 📚 文档概览

本文档索引帮助您快速找到所需的错误处理相关文档和工具。

## 📖 核心文档

### 1. [错误处理规范](./ERROR_HANDLING_STANDARD.md) ⭐ 必读
**完整的技术规范和标准**

包含：
- 核心原则（统一性、可观测性、用户体验、安全性）
- 前端错误处理规范（标准模式、禁止模式、特殊情况）
- 后端错误处理规范（API端点、服务层、禁止模式、特殊情况）
- 错误分类表
- 日志规范
- 迁移计划
- 检查清单

**适合**: 需要了解完整规范的开发人员

---

### 2. [快速参考](./ERROR_HANDLING_QUICK_REFERENCE.md) ⚡ 快速查阅
**常用模式和代码模板**

包含：
- 前端标准模板
- 后端标准模板
- 常见场景示例
- 检查清单

**适合**: 日常开发时快速查阅

---

### 3. [迁移指南](./ERROR_HANDLING_MIGRATION_GUIDE.md) 📋 迁移步骤
**详细的迁移步骤和策略**

包含：
- 迁移步骤
- 优先级排序
- 前端迁移示例（3个场景）
- 后端迁移示例（3个场景）
- 迁移检查清单
- 常见问题解答
- 工具支持
- 时间估算

**适合**: 准备迁移现有代码的开发人员

---

### 4. [迁移示例](./ERROR_HANDLING_EXAMPLES.md) 💡 实际案例
**真实的代码迁移案例**

包含：
- 前端迁移示例（4个实际案例）
- 后端迁移示例（4个实际案例）
- 常见模式迁移
- 迁移检查清单

**适合**: 需要参考实际迁移案例的开发人员

---

### 5. [实施总结](./ERROR_HANDLING_IMPLEMENTATION_SUMMARY.md) 📊 项目状态
**项目整体实施情况**

包含：
- 已完成的工作
- 当前状态分析
- 使用指南
- 下一步行动
- 相关文档链接

**适合**: 项目负责人和技术负责人

---

## 🛠️ 工具和脚本

### 1. 前端错误处理工具
**位置**: `frontend/src/utils/errorHandler.js`

**功能**:
- `getErrorMessage()` - 提取友好错误消息
- `isAuthError()` - 判断认证错误
- `isPermissionError()` - 判断权限错误
- `isValidationError()` - 判断验证错误
- `isNetworkError()` - 判断网络错误
- `getValidationErrors()` - 提取验证错误详情
- `handleApiError()` - 统一错误处理入口

**使用**:
```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
```

---

### 2. 后端日志工具
**位置**: `app/utils/logger.py`

**功能**:
- `get_logger(name)` - 获取统一配置的日志记录器
- `log_error_with_context()` - 记录错误并包含上下文
- `log_warning_with_context()` - 记录警告并包含上下文
- `log_info_with_context()` - 记录信息并包含上下文

**使用**:
```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)
```

---

### 3. 错误处理分析脚本
**位置**: `scripts/analyze_error_handling.py`

**功能**:
- 自动扫描前端和后端代码
- 识别问题模式（空 catch、只有 console.error、没有日志等）
- 生成分析报告（Markdown + JSON）

**使用**:
```bash
python scripts/analyze_error_handling.py
```

**输出**:
- 控制台：统计摘要和问题列表
- `error_handling_analysis.json`：详细的分析数据

---

## 🗺️ 使用路径

### 路径 1: 新功能开发
1. 阅读 [快速参考](./ERROR_HANDLING_QUICK_REFERENCE.md)
2. 参考 [迁移示例](./ERROR_HANDLING_EXAMPLES.md) 中的标准模式
3. 使用工具进行错误处理

### 路径 2: 迁移现有代码
1. 运行分析脚本了解当前状态
2. 阅读 [迁移指南](./ERROR_HANDLING_MIGRATION_GUIDE.md)
3. 参考 [迁移示例](./ERROR_HANDLING_EXAMPLES.md)
4. 按照优先级逐步迁移
5. 使用检查清单验证

### 路径 3: 了解完整规范
1. 阅读 [错误处理规范](./ERROR_HANDLING_STANDARD.md)
2. 查看 [实施总结](./ERROR_HANDLING_IMPLEMENTATION_SUMMARY.md)
3. 参考实际代码示例

---

## 📋 快速检查清单

### 前端代码审查
- [ ] 使用 `handleApiError` 处理所有 API 错误
- [ ] 用户能看到友好的错误提示（toast/alert）
- [ ] 没有空的 catch 块
- [ ] 没有直接使用 `console.error` 作为主要错误处理
- [ ] 加载状态在 `finally` 块中重置

### 后端代码审查
- [ ] 使用 `get_logger(__name__)` 获取日志记录器
- [ ] 所有异常都记录日志
- [ ] HTTPException 直接抛出，不捕获
- [ ] 数据库错误不暴露给用户
- [ ] 日志包含足够的上下文信息（user_id, project_id 等）

---

## 🔗 相关资源

### 项目文档
- [项目开发规范](../.cursorrules)
- [API 文档](./API_QUICK_REFERENCE.md)

### 外部资源
- [FastAPI 错误处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [React 错误边界](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)

---

## 📞 支持

如有问题或建议：
1. 查阅相关文档
2. 查看代码示例
3. 运行分析脚本诊断问题
4. 联系技术负责人

---

**最后更新**: 2025-01-20  
**版本**: 1.0.0
