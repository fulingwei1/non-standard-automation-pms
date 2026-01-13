# 错误处理统一化迁移指南

## 概述

本指南帮助开发人员将现有的 try-catch 块迁移到统一的错误处理标准。

## 迁移步骤

### 步骤 1: 运行分析脚本

首先了解当前代码库中的错误处理情况：

```bash
python scripts/analyze_error_handling.py
```

这将生成：
- 控制台输出：统计摘要和问题列表
- `error_handling_analysis.json`：详细的分析数据

### 步骤 2: 优先级排序

按照以下优先级进行迁移：

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

---

## 前端迁移示例

### 示例 1: 简单数据获取

**迁移前：**
```javascript
const fetchProjects = async () => {
  try {
    const res = await projectApi.list({ page_size: 1000 })
    setProjects(res.data?.items || res.data || [])
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
}
```

**迁移后：**
```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
import { toast } from '@/components/ui/toast' // 或你的 toast 组件

const fetchProjects = async () => {
  try {
    setLoading(true)
    const res = await projectApi.list({ page_size: 1000 })
    setProjects(res.data?.items || res.data || [])
  } catch (error) {
    handleApiError(error, {
      onOtherError: (err) => {
        toast.error(getErrorMessage(err))
      }
    })
  } finally {
    setLoading(false)
  }
}
```

### 示例 2: 表单提交

**迁移前：**
```javascript
const handleCreateException = async () => {
  if (!newException.event_title) {
    alert('请填写异常标题')
    return
  }
  try {
    await exceptionApi.create(newException)
    setShowCreateDialog(false)
    setNewException({...})
    fetchExceptions()
  } catch (error) {
    console.error('Failed to create exception:', error)
    const errorMessage = error.response?.data?.detail || error.message || '创建异常失败，请稍后重试'
    alert(errorMessage)
  }
}
```

**迁移后：**
```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
import { toast } from '@/components/ui/toast'

const handleCreateException = async () => {
  if (!newException.event_title) {
    toast.error('请填写异常标题')
    return
  }
  try {
    await exceptionApi.create(newException)
    toast.success('创建成功')
    setShowCreateDialog(false)
    setNewException({...})
    fetchExceptions()
  } catch (error) {
    handleApiError(error, {
      onValidationError: (err, validationErrors) => {
        // 显示验证错误
        toast.error(getErrorMessage(err))
        // 如果有字段级错误，设置表单错误状态
        if (validationErrors) {
          setFieldErrors(validationErrors)
        }
      },
      onOtherError: (err) => {
        toast.error(getErrorMessage(err))
      }
    })
  }
}
```

### 示例 3: 演示模式处理

**迁移前：**
```javascript
const fetchExceptions = async () => {
  try {
    setLoading(true)
    const res = await exceptionApi.list(params)
    setExceptions(res.data?.items || res.data || [])
  } catch (error) {
    console.error('Failed to fetch exceptions:', error)
    const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
    if (isDemoAccount) {
      setExceptions([])
    } else {
      setExceptions([])
    }
  } finally {
    setLoading(false)
  }
}
```

**迁移后：**
```javascript
import { handleApiError } from '@/utils/errorHandler'

const fetchExceptions = async () => {
  try {
    setLoading(true)
    const res = await exceptionApi.list(params)
    setExceptions(res.data?.items || res.data || [])
  } catch (error) {
    // handleApiError 内部已经处理了演示账号的情况
    handleApiError(error, {
      onOtherError: () => {
        // 演示模式下，handleApiError 会静默处理，这里设置空数组
        setExceptions([])
      }
    })
  } finally {
    setLoading(false)
  }
}
```

---

## 后端迁移示例

### 示例 1: API 端点

**迁移前：**
```python
@router.get("/items/{item_id}")
async def get_item(item_id: int, db: Session = Depends(get_db)):
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="项目不存在")
        return item
    except Exception as e:
        print(f"Error: {e}")
        return None
```

**迁移后：**
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
        # HTTPException 直接向上抛出
        raise
    except SQLAlchemyError as e:
        logger.error(
            f"数据库查询失败 [item_id={item_id}]",
            exc_info=True,
            extra={"item_id": item_id, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据查询失败，请稍后重试"
        )
    except Exception as e:
        logger.error(
            f"未预期的错误 [item_id={item_id}]",
            exc_info=True,
            extra={"item_id": item_id, "error_type": type(e).__name__}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )
```

### 示例 2: 服务层

**迁移前：**
```python
def process_data(self, data: dict):
    try:
        result = self._do_process(data)
        return result
    except Exception as e:
        return None
```

**迁移后：**
```python
from app.utils.logger import get_logger, log_error_with_context

logger = get_logger(__name__)

def process_data(self, data: dict) -> Optional[dict]:
    try:
        result = self._do_process(data)
        return result
    except ValueError as e:
        logger.warning(
            f"数据处理失败: {e}",
            extra={"data_id": data.get("id")}
        )
        return None
    except Exception as e:
        log_error_with_context(
            logger,
            "数据处理异常",
            e,
            context={"data_id": data.get("id")}
        )
        return None
```

### 示例 3: 降级处理（Redis）

**迁移前：**
```python
try:
    result = redis_client.get(key)
except Exception as e:
    result = memory_cache.get(key)
```

**迁移后：**
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

try:
    result = redis_client.get(key)
except Exception as e:
    logger.warning(
        f"Redis操作失败，降级到内存存储 [key={key}]",
        extra={"key": key, "error_type": type(e).__name__}
    )
    result = memory_cache.get(key)
```

---

## 迁移检查清单

### 前端检查项

- [ ] 导入 `handleApiError` 和 `getErrorMessage`
- [ ] 移除 `console.error` 的直接使用
- [ ] 移除 `alert` 的直接使用，改用 toast
- [ ] 所有错误都通过 `handleApiError` 处理
- [ ] 加载状态在 `finally` 块中重置
- [ ] 验证错误正确显示给用户
- [ ] 网络错误有友好的提示

### 后端检查项

- [ ] 导入 `get_logger` 或使用 `logging.getLogger(__name__)`
- [ ] 移除 `print` 语句
- [ ] 所有异常都记录日志
- [ ] HTTPException 直接抛出，不捕获
- [ ] 数据库错误不暴露给用户
- [ ] 日志包含足够的上下文信息
- [ ] 使用正确的日志级别（ERROR/WARNING/INFO）

---

## 常见问题

### Q: 如果错误处理逻辑很复杂怎么办？

A: 将复杂逻辑提取到单独的函数中：

```javascript
const handleCreateError = (error) => {
  // 复杂的错误处理逻辑
  if (error.response?.status === 409) {
    // 处理冲突
  } else if (error.response?.status === 422) {
    // 处理验证错误
  }
  // ...
}

try {
  await api.create(data)
} catch (error) {
  handleApiError(error, {
    onOtherError: handleCreateError
  })
}
```

### Q: 某些错误需要静默处理怎么办？

A: 在 `handleApiError` 的 `onOtherError` 回调中处理，但必须记录警告日志：

```javascript
handleApiError(error, {
  onOtherError: (err) => {
    console.warn('预加载失败，不影响主流程:', err)
    // 静默处理
  }
})
```

### Q: 如何迁移大量相似的文件？

A: 使用查找替换 + 手动审查：

1. 查找模式：`catch\s*\([^)]+\)\s*\{[^}]*console\.error`
2. 替换为统一模式
3. 逐个文件审查和调整

---

## 工具支持

### 1. 分析脚本

```bash
# 分析整个代码库
python scripts/analyze_error_handling.py

# 分析特定目录
python scripts/analyze_error_handling.py app/api/v1/endpoints
```

### 2. ESLint 规则（可选）

可以添加 ESLint 规则来检测不符合规范的错误处理：

```javascript
// .eslintrc.js
rules: {
  'no-console': ['error', { allow: ['warn', 'error'] }],
  // 可以添加自定义规则检测空的 catch 块
}
```

---

## 迁移时间估算

- **单个文件迁移**: 5-15 分钟
- **简单 API 端点**: 10-20 分钟
- **复杂业务流程**: 20-40 分钟

**总计估算**（基于 568 个 try-catch 块）:
- 快速迁移（只改明显问题）: 2-3 天
- 完整迁移（包括优化）: 1-2 周

---

## 后续维护

迁移完成后：

1. **代码审查**: 确保新代码遵循规范
2. **定期检查**: 运行分析脚本检查新引入的问题
3. **文档更新**: 保持规范文档与代码同步
