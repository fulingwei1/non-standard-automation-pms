# 错误处理统一化方案总结

## 问题描述

代码库中存在 **2573 个 try-catch 块**（可能包含嵌套），但处理方式不统一，导致：
- 错误处理不一致
- 用户体验差
- 难以追踪和调试问题
- 代码质量参差不齐

## 解决方案

### 1. 统一规范文档 ✅

创建了 `docs/ERROR_HANDLING_STANDARD.md`，包含：
- 前端和后端的统一错误处理规范
- 禁止的模式和推荐做法
- 错误分类和处理方式
- 日志规范

### 2. 工具支持 ✅

#### 前端工具
- **位置**: `frontend/src/utils/errorHandler.js`
- **功能**: 
  - `getErrorMessage()`: 统一提取错误消息
  - `handleApiError()`: 统一处理 API 错误
  - 支持认证、权限、网络、验证等错误类型

#### 后端工具
- **位置**: `app/utils/logger.py` (新建)
- **功能**:
  - `get_logger()`: 获取统一配置的日志记录器
  - `log_error_with_context()`: 记录带上下文的错误
  - `log_warning_with_context()`: 记录带上下文的警告

### 3. 分析工具 ✅

- **位置**: `scripts/analyze_error_handling.py`
- **功能**:
  - 分析代码库中所有 try-catch 块
  - 识别不符合规范的错误处理
  - 生成分析报告和 JSON 数据

### 4. 迁移指南 ✅

创建了 `docs/ERROR_HANDLING_MIGRATION_GUIDE.md`，包含：
- 详细的迁移步骤
- 前后端迁移示例
- 迁移检查清单
- 常见问题解答

## 核心原则

### 统一性
- 所有错误处理必须遵循相同的模式和工具
- 禁止使用 `console.error` 直接输出（前端）或 `print`（后端）
- 禁止空的 catch 块

### 可观测性
- 所有错误必须记录日志
- 错误信息必须包含足够的上下文
- 区分错误级别（ERROR, WARNING, INFO）

### 用户体验
- 前端错误必须向用户展示友好的错误消息
- 区分可恢复错误和不可恢复错误
- 提供明确的错误恢复路径

### 安全性
- 不向用户暴露敏感信息（如数据库错误详情）
- 记录详细错误信息到日志，但只显示通用消息给用户

## 使用示例

### 前端标准模式

```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
import { toast } from '@/components/ui/toast'

async function fetchData() {
  try {
    setLoading(true)
    const res = await api.getData()
    setData(res.data)
  } catch (error) {
    handleApiError(error, {
      onValidationError: (error, validationErrors) => {
        toast.error(getErrorMessage(error))
        setFieldErrors(validationErrors)
      },
      onOtherError: (error) => {
        toast.error(getErrorMessage(error))
      }
    })
  } finally {
    setLoading(false)
  }
}
```

### 后端标准模式

```python
from app.utils.logger import get_logger
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)

@router.get("/items/{item_id}")
async def get_item(item_id: int, db: Session = Depends(get_db)):
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        return item
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(
            f"数据库查询失败 [item_id={item_id}]",
            exc_info=True,
            extra={"item_id": item_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据查询失败，请稍后重试"
        )
    except Exception as e:
        logger.error(
            f"未预期的错误 [item_id={item_id}]",
            exc_info=True,
            extra={"item_id": item_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )
```

## 迁移计划

### 阶段 1: 工具准备 ✅
- ✅ 前端错误处理工具（已存在，已验证）
- ✅ 后端日志工具（已创建）
- ✅ 错误处理分析脚本（已创建）

### 阶段 2: 逐步迁移
1. **高优先级**（影响用户体验）
   - 用户登录/认证相关
   - 数据提交/保存操作
   - 关键业务流程

2. **中优先级**（影响可观测性）
   - 数据查询操作
   - 后台任务
   - 定时任务

3. **低优先级**（代码质量）
   - 工具函数
   - 辅助功能
   - 非关键路径

### 阶段 3: 验证和优化
1. 代码审查
2. 错误处理测试
3. 日志监控

## 文件清单

### 新建文件
- `docs/ERROR_HANDLING_STANDARD.md` - 错误处理规范文档
- `docs/ERROR_HANDLING_MIGRATION_GUIDE.md` - 迁移指南
- `app/utils/logger.py` - 后端统一日志工具
- `scripts/analyze_error_handling.py` - 错误处理分析脚本
- `ERROR_HANDLING_UNIFICATION_SUMMARY.md` - 本文档

### 现有文件（已验证）
- `frontend/src/utils/errorHandler.js` - 前端错误处理工具（已存在，功能完善）

## 下一步行动

1. **运行分析脚本**，了解当前代码库中的错误处理情况：
   ```bash
   python scripts/analyze_error_handling.py
   ```

2. **选择高优先级模块**开始迁移，例如：
   - 用户认证相关 API
   - 项目创建/更新 API
   - 关键业务流程

3. **代码审查**，确保新代码遵循规范

4. **定期检查**，运行分析脚本检查新引入的问题

## 时间估算

基于 568+ 个 try-catch 块：
- **快速迁移**（只改明显问题）: 2-3 天
- **完整迁移**（包括优化）: 1-2 周

## 注意事项

1. **渐进式迁移**: 不要一次性修改所有文件，按模块逐步迁移
2. **保持向后兼容**: 迁移时确保不影响现有功能
3. **测试验证**: 每个模块迁移后进行测试
4. **代码审查**: 确保新代码遵循规范

## 参考资源

- 错误处理规范: `docs/ERROR_HANDLING_STANDARD.md`
- 迁移指南: `docs/ERROR_HANDLING_MIGRATION_GUIDE.md`
- 前端工具: `frontend/src/utils/errorHandler.js`
- 后端工具: `app/utils/logger.py`
- 分析脚本: `scripts/analyze_error_handling.py`
