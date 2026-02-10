# 错误处理统一规范

## 概述

本文档定义了项目中所有 try-catch 块的统一处理标准，确保错误处理的一致性、可维护性和可观测性。

## 统计信息

- **前端 try-catch 块**: ~56 个
- **后端 try-catch 块**: ~512 个
- **总计**: ~568 个（用户提到的 2573 可能包含了嵌套的 try-catch）

## 核心原则

### 1. 统一性
- 所有错误处理必须遵循相同的模式和工具
- 禁止使用 `console.error` 直接输出（前端）或 `print`（后端）
- 禁止空的 catch 块

### 2. 可观测性
- 所有错误必须记录日志
- 错误信息必须包含足够的上下文
- 区分错误级别（ERROR, WARNING, INFO）

### 3. 用户体验
- 前端错误必须向用户展示友好的错误消息
- 区分可恢复错误和不可恢复错误
- 提供明确的错误恢复路径

### 4. 安全性
- 不向用户暴露敏感信息（如数据库错误详情）
- 记录详细错误信息到日志，但只显示通用消息给用户

---

## 前端错误处理规范

### 标准模式

```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
import { toast } from '@/components/ui/toast' // 或使用你的 toast 组件

async function fetchData() {
  try {
    setLoading(true)
    const res = await api.getData()
    setData(res.data)
  } catch (error) {
    // 使用统一的错误处理工具
    handleApiError(error, {
      onAuthError: () => {
        // 认证错误：重定向到登录页（默认行为，通常不需要自定义）
      },
      onPermissionError: () => {
        toast.error('没有权限访问此资源')
      },
      onNetworkError: () => {
        toast.error('网络连接失败，请检查网络设置')
      },
      onValidationError: (error, validationErrors) => {
        // 显示验证错误
        const message = getErrorMessage(error)
        toast.error(message)
        // 如果有字段级错误，可以设置表单错误状态
        setFieldErrors(validationErrors)
      },
      onOtherError: (error) => {
        // 其他错误：显示友好消息
        toast.error(getErrorMessage(error))
      }
    })
  } finally {
    setLoading(false)
  }
}
```

### 禁止的模式

❌ **禁止直接使用 console.error**
```javascript
catch (error) {
  console.error('Failed to fetch:', error) // ❌ 禁止
}
```

❌ **禁止直接使用 alert**
```javascript
catch (error) {
  alert(error.message) // ❌ 禁止，使用 toast
}
```

❌ **禁止空的 catch 块**
```javascript
catch (error) {
  // 忽略错误 // ❌ 禁止
}
```

❌ **禁止不完整的错误处理**
```javascript
catch (error) {
  console.error(error) // ❌ 缺少用户提示
}
```

### 特殊情况处理

#### 1. 静默失败（需要明确理由）
```javascript
catch (error) {
  // 仅在确实不需要用户感知的情况下使用
  // 例如：预加载非关键数据失败
  console.warn('预加载数据失败，不影响主流程:', error)
  // 必须记录警告日志
}
```

#### 2. 演示模式处理
```javascript
catch (error) {
  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
  if (isDemoAccount) {
    // 演示模式：使用 mock 数据
    setData(mockData)
    return
  }
  // 正常模式：使用统一错误处理
  handleApiError(error)
}
```

---

## 后端错误处理规范

### 标准模式

```python
from app.core.logging_config import get_logger
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)

@router.get("/items/{item_id}")
async def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        return item
    except HTTPException:
        # HTTPException 直接向上抛出，不需要捕获
        raise
    except SQLAlchemyError as e:
        # 数据库错误：记录详细日志，返回通用错误
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
        # 其他未预期错误：记录详细日志
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

### 服务层错误处理

```python
from app.core.logging_config import get_logger
from typing import Optional

logger = get_logger(__name__)

class MyService:
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
            # 业务逻辑错误：记录警告，返回 None
            logger.warning(
                f"数据处理失败: {e}",
                extra={"data": data}
            )
            return None
        except Exception as e:
            # 未预期错误：记录错误
            logger.error(
                f"数据处理异常: {e}",
                exc_info=True,
                extra={"data": data}
            )
            return None
```

### 禁止的模式

❌ **禁止捕获所有异常但不处理**
```python
except Exception as e:
    pass  # ❌ 禁止
```

❌ **禁止只打印错误**
```python
except Exception as e:
    print(f"Error: {e}")  # ❌ 禁止，使用 logger
```

❌ **禁止暴露敏感信息**
```python
except Exception as e:
    raise HTTPException(
        detail=f"Database error: {str(e)}"  # ❌ 禁止暴露数据库错误详情
    )
```

❌ **禁止不记录日志**
```python
except Exception as e:
    return None  # ❌ 缺少日志记录
```

### 特殊情况处理

#### 1. 降级处理（Redis/缓存失败）
```python
try:
    result = redis_client.get(key)
except Exception as e:
    logger.warning(f"Redis操作失败，降级到内存存储: {e}")
    # 降级到内存存储
    result = memory_cache.get(key)
```

#### 2. 可选功能失败（不影响主流程）
```python
try:
    send_notification(user_id, message)
except Exception as e:
    logger.warning(
        f"发送通知失败，不影响主流程 [user_id={user_id}]",
        exc_info=True
    )
    # 继续执行主流程
```

#### 3. 数据验证错误
```python
try:
    validate_data(data)
except ValueError as e:
    # 验证错误：直接抛出，由调用方处理
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e)
    )
```

---

## 错误分类

### 前端错误类型

| 错误类型 | HTTP 状态码 | 处理方式 | 用户提示 |
|---------|------------|---------|---------|
| 认证错误 | 401 | 清除 token，重定向登录 | "登录已过期，请重新登录" |
| 权限错误 | 403 | 显示权限错误 | "没有权限访问此资源" |
| 验证错误 | 400, 422 | 显示字段错误 | 显示具体验证错误信息 |
| 网络错误 | - | 显示网络错误 | "网络连接失败，请检查网络设置" |
| 服务器错误 | 500+ | 显示通用错误 | "服务器错误，请稍后重试" |
| 资源不存在 | 404 | 显示不存在提示 | "请求的资源不存在" |

### 后端错误类型

| 错误类型 | 日志级别 | 处理方式 | 返回状态码 |
|---------|---------|---------|-----------|
| HTTPException | - | 直接抛出 | 原状态码 |
| SQLAlchemyError | ERROR | 记录日志，返回通用错误 | 500 |
| ValueError | WARNING | 记录警告，返回验证错误 | 400 |
| 业务逻辑错误 | WARNING | 记录警告，返回业务错误 | 400 |
| 未预期错误 | ERROR | 记录详细日志，返回通用错误 | 500 |

---

## 日志规范

### 日志级别使用

- **ERROR**: 系统错误、数据库错误、未预期异常
- **WARNING**: 业务逻辑错误、降级处理、可选功能失败
- **INFO**: 正常业务流程（可选）
- **DEBUG**: 调试信息（开发环境）

### 日志格式

```python
logger.error(
    "操作失败描述",
    exc_info=True,  # 包含堆栈信息
    extra={
        "key1": value1,  # 关键上下文信息
        "key2": value2
    }
)
```

### 日志上下文信息

必须包含的关键信息：
- 用户ID（如果相关）
- 资源ID（如 project_id, item_id）
- 操作类型
- 错误类型

---

## 迁移计划

### 阶段 1: 工具准备（已完成）
- ✅ 前端错误处理工具 (`frontend/src/utils/errorHandler.js`)
- ⏳ 后端日志工具（需要创建）
- ⏳ 错误处理分析脚本

### 阶段 2: 逐步迁移
1. 优先迁移高频使用的 API 端点
2. 迁移关键业务流程
3. 迁移其他功能

### 阶段 3: 验证和优化
1. 代码审查
2. 错误处理测试
3. 日志监控

---

## 检查清单

### 前端代码审查

- [ ] 所有 catch 块都使用 `handleApiError` 或类似的统一工具
- [ ] 所有错误都向用户显示友好提示（toast/alert）
- [ ] 没有空的 catch 块
- [ ] 没有直接使用 `console.error` 作为主要错误处理
- [ ] 加载状态在 finally 块中重置

### 后端代码审查

- [ ] 所有异常都记录日志
- [ ] HTTPException 直接抛出，不捕获
- [ ] 数据库错误不暴露给用户
- [ ] 日志包含足够的上下文信息
- [ ] 使用正确的日志级别

---

## 参考资源

- 前端错误处理工具: `frontend/src/utils/errorHandler.js`
- 后端日志工具: `app/utils/logger.py` (待创建)
- FastAPI 错误处理: https://fastapi.tiangolo.com/tutorial/handling-errors/
