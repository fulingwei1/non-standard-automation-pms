# 错误处理快速参考

## 前端

### 标准模板

```javascript
import { handleApiError, getErrorMessage } from '@/utils/errorHandler'
import { toast } from '@/components/ui/toast'

try {
  setLoading(true)
  const res = await api.call()
  setData(res.data)
} catch (error) {
  handleApiError(error, {
    onOtherError: (err) => toast.error(getErrorMessage(err))
  })
} finally {
  setLoading(false)
}
```

### 错误类型处理

| 错误类型 | 处理方式 |
|---------|---------|
| 401 认证错误 | 自动重定向登录（演示账号除外） |
| 403 权限错误 | `onPermissionError` 回调 |
| 400/422 验证错误 | `onValidationError` 回调，显示字段错误 |
| 网络错误 | `onNetworkError` 回调 |
| 其他错误 | `onOtherError` 回调 |

### 禁止 ❌

- `console.error()` 作为主要错误处理
- `alert()` 直接使用
- 空的 catch 块
- 没有用户反馈的错误

---

## 后端

### 标准模板

```python
from app.utils.logger import get_logger
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)

try:
    # 业务逻辑
    result = db.query(Model).filter(...).first()
    if not result:
        raise HTTPException(status_code=404, detail="不存在")
    return result
except HTTPException:
    raise  # 直接抛出
except SQLAlchemyError as e:
    logger.error("数据库错误", exc_info=True, extra={"id": id})
    raise HTTPException(status_code=500, detail="查询失败")
except Exception as e:
    logger.error("未预期错误", exc_info=True, extra={"id": id})
    raise HTTPException(status_code=500, detail="服务器错误")
```

### 日志级别

- **ERROR**: 系统错误、数据库错误、未预期异常
- **WARNING**: 业务逻辑错误、降级处理
- **INFO**: 正常业务流程（可选）

### 禁止 ❌

- `print()` 输出错误
- 空的 except 块
- 暴露数据库错误详情给用户
- 不记录日志的异常

---

## 常见场景

### 前端：表单提交

```javascript
try {
  await api.create(data)
  toast.success('创建成功')
  onSuccess()
} catch (error) {
  handleApiError(error, {
    onValidationError: (err, validationErrors) => {
      toast.error(getErrorMessage(err))
      setFieldErrors(validationErrors)
    },
    onOtherError: (err) => toast.error(getErrorMessage(err))
  })
}
```

### 后端：服务层

```python
def process_data(self, data: dict) -> Optional[dict]:
    try:
        return self._do_process(data)
    except ValueError as e:
        logger.warning(f"验证失败: {e}", extra={"data_id": data.get("id")})
        return None
    except Exception as e:
        logger.error("处理异常", exc_info=True, extra={"data_id": data.get("id")})
        return None
```

### 降级处理（Redis）

```python
try:
    result = redis_client.get(key)
except Exception as e:
    logger.warning(f"Redis失败，降级 [key={key}]", extra={"key": key})
    result = memory_cache.get(key)
```

---

## 检查清单

### 前端
- [ ] 使用 `handleApiError`
- [ ] 用户看到友好提示
- [ ] 加载状态在 finally 中重置
- [ ] 没有 `console.error` 作为主要处理

### 后端
- [ ] 使用 `get_logger(__name__)`
- [ ] 所有异常都记录日志
- [ ] HTTPException 直接抛出
- [ ] 不暴露敏感信息

---

**更多详情**: 查看 [完整规范](./ERROR_HANDLING_STANDARD.md)
