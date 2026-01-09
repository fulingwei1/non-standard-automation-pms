# 错误处理迁移示例

本文档提供实际的代码迁移示例，展示如何将现有代码迁移到统一的错误处理标准。

## 前端迁移示例

### 示例 1: ExceptionManagement.jsx - 数据获取

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
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
import { toast } from '@/components/ui/toast' // 或使用你的 toast 组件

const fetchProjects = async () => {
  try {
    const res = await projectApi.list({ page_size: 1000 })
    setProjects(res.data?.items || res.data || [])
  } catch (error) {
    // 项目列表加载失败不影响主功能，静默处理但记录警告
    handleApiError(error, {
      onOtherError: () => {
        // handleApiError 内部已处理演示账号，这里只需设置空数组
        setProjects([])
      }
    })
  }
}

const fetchExceptions = async () => {
  try {
    setLoading(true)
    const res = await exceptionApi.list(params)
    setExceptions(res.data?.items || res.data || [])
  } catch (error) {
    handleApiError(error, {
      onOtherError: () => {
        // 演示账号或网络错误时，设置空数组
        setExceptions([])
      }
    })
  } finally {
    setLoading(false)
  }
}
```

### 示例 2: ExceptionManagement.jsx - 表单提交

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
    toast.success('异常创建成功')
    setShowCreateDialog(false)
    setNewException({...})
    fetchExceptions()
  } catch (error) {
    handleApiError(error, {
      onValidationError: (err, validationErrors) => {
        toast.error(getErrorMessage(err))
        // 如果有字段级错误，可以设置表单错误状态
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

### 示例 3: PermissionManagement.jsx - 复杂错误处理

**迁移前：**
```javascript
const loadPermissions = async () => {
  try {
    setLoading(true)
    const response = await permissionApi.list({ page_size: 1000 })
    setPermissions(response.data.items || [])
  } catch (error) {
    console.error('[权限管理] ❌ 加载权限列表失败:', error)
    const errorDetail = error.response?.data?.detail || error.message
    const statusCode = error.response?.status
    
    if (statusCode === 401 || statusCode === 403) {
      console.error('[权限管理] 认证失败，清除token并跳转登录页')
      alert('认证失败，请重新登录')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/'
    } else {
      let errorMessage = errorDetail
      if (typeof errorDetail === 'object') {
        errorMessage = JSON.stringify(errorDetail, null, 2)
      }
      alert('加载权限列表失败: ' + errorMessage)
    }
  } finally {
    setLoading(false)
  }
}
```

**迁移后：**
```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
import { toast } from '@/components/ui/toast'

const loadPermissions = async () => {
  try {
    setLoading(true)
    const response = await permissionApi.list({ page_size: 1000 })
    setPermissions(response.data.items || [])
  } catch (error) {
    handleApiError(error, {
      onAuthError: () => {
        // handleApiError 默认会处理 401，这里可以自定义
        toast.error('认证失败，请重新登录')
        // handleApiError 会自动清除 token 并跳转
      },
      onPermissionError: () => {
        toast.error('没有权限访问权限管理')
      },
      onOtherError: (err) => {
        toast.error('加载权限列表失败: ' + getErrorMessage(err))
      }
    })
  } finally {
    setLoading(false)
  }
}
```

### 示例 4: MobileExceptionReport.jsx - 移动端错误处理

**迁移前：**
```javascript
try {
  setLoading(true)
  setError('')
  await productionApi.exceptions.create({...})
  setSuccess(true)
  setTimeout(() => {
    navigate('/mobile/tasks')
  }, 1500)
} catch (error) {
  console.error('Failed to report exception:', error)
  setError('异常上报失败: ' + (error.response?.data?.detail || error.message))
} finally {
  setLoading(false)
}
```

**迁移后：**
```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'

try {
  setLoading(true)
  setError('')
  await productionApi.exceptions.create({...})
  setSuccess(true)
  setTimeout(() => {
    navigate('/mobile/tasks')
  }, 1500)
} catch (error) {
  handleApiError(error, {
    onValidationError: (err, validationErrors) => {
      setError('异常上报失败: ' + getErrorMessage(err))
    },
    onOtherError: (err) => {
      setError('异常上报失败: ' + getErrorMessage(err))
    }
  })
} finally {
  setLoading(false)
}
```

---

## 后端迁移示例

### 示例 1: API 端点 - 简单查询

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

### 示例 2: 服务层 - 数据处理

**迁移前：**
```python
class DataService:
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
from typing import Optional

logger = get_logger(__name__)

class DataService:
    def process_data(self, data: dict) -> Optional[dict]:
        """
        处理数据
        
        Returns:
            处理结果，失败时返回 None
        """
        try:
            result = self._do_process(data)
            return result
        except ValueError as e:
            # 业务逻辑错误：记录警告
            logger.warning(
                f"数据处理失败: {e}",
                extra={"data_id": data.get("id"), "data_type": type(data).__name__}
            )
            return None
        except Exception as e:
            # 未预期错误：记录详细日志
            log_error_with_context(
                logger,
                "数据处理异常",
                e,
                context={"data_id": data.get("id"), "data_type": type(data).__name__}
            )
            return None
```

### 示例 3: 降级处理 - Redis 缓存

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

### 示例 4: 定时任务错误处理

**迁移前：**
```python
def scheduled_task():
    try:
        # 执行任务
        process_data()
    except Exception as e:
        print(f"Task failed: {e}")
```

**迁移后：**
```python
from app.utils.logger import get_logger

logger = get_logger(__name__)

def scheduled_task():
    try:
        # 执行任务
        process_data()
        logger.info("定时任务执行成功")
    except ValueError as e:
        # 业务逻辑错误
        logger.warning(
            f"定时任务执行失败: {e}",
            extra={"task": "scheduled_task"}
        )
    except Exception as e:
        # 未预期错误
        logger.error(
            f"定时任务执行异常",
            exc_info=True,
            extra={"task": "scheduled_task", "error_type": type(e).__name__}
        )
```

---

## 常见模式迁移

### 模式 1: 静默失败（需要明确理由）

**迁移前：**
```javascript
catch (error) {
  // 忽略错误
}
```

**迁移后：**
```javascript
catch (error) {
  // 仅在确实不需要用户感知的情况下使用
  // 例如：预加载非关键数据失败
  console.warn('预加载数据失败，不影响主流程:', error)
  // 必须记录警告日志
}
```

### 模式 2: 演示模式处理

**迁移前：**
```javascript
catch (error) {
  console.error('Failed:', error)
  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
  if (isDemoAccount) {
    setData(mockData)
  }
}
```

**迁移后：**
```javascript
catch (error) {
  handleApiError(error, {
    onOtherError: () => {
      // handleApiError 内部已处理演示账号
      // 演示模式下，设置 mock 数据
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        setData(mockData)
      }
    }
  })
}
```

### 模式 3: 复杂错误处理逻辑

**迁移前：**
```javascript
catch (error) {
  if (error.response?.status === 401) {
    // 处理 401
  } else if (error.response?.status === 403) {
    // 处理 403
  } else if (error.response?.status === 422) {
    // 处理 422
  } else {
    // 处理其他错误
  }
}
```

**迁移后：**
```javascript
catch (error) {
  handleApiError(error, {
    onAuthError: () => {
      // 处理 401
    },
    onPermissionError: () => {
      // 处理 403
    },
    onValidationError: (err, validationErrors) => {
      // 处理 422
    },
    onOtherError: (err) => {
      // 处理其他错误
    }
  })
}
```

---

## 迁移检查清单

迁移完成后，请确认：

### 前端
- [ ] 移除了所有 `console.error` 作为主要错误处理
- [ ] 移除了所有 `alert` 直接使用
- [ ] 所有错误都通过 `handleApiError` 处理
- [ ] 用户能看到友好的错误提示
- [ ] 加载状态在 `finally` 块中重置
- [ ] 演示账号特殊处理已迁移

### 后端
- [ ] 移除了所有 `print` 语句
- [ ] 所有异常都记录日志
- [ ] HTTPException 直接抛出，不捕获
- [ ] 数据库错误不暴露给用户
- [ ] 日志包含足够的上下文信息
- [ ] 使用正确的日志级别

---

**更多示例**: 查看实际代码文件中的迁移案例
