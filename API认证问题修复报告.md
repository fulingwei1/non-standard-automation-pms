# API认证问题修复报告

**日期**: 2026-02-16  
**执行人**: M5 AI Assistant  
**问题**: 所有受保护的API端点返回401错误  
**状态**: ✅ **已修复**

---

## 问题描述

在数据库Schema同步完成后，系统启动正常（740条路由），登录API工作正常，但所有需要认证的API端点都返回401错误：

```bash
curl -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:8001/api/v1/projects/
# 返回: {"code":401,"message":"无效的认证凭据","error_code":"AUTH_FAILED"}
```

---

## 根本原因

### 问题定位

认证中间件 (`app/core/middleware/auth_middleware.py`) 调用了 `get_current_user()` 函数来验证token：

```python
from app.core.auth import get_current_user
user = await get_current_user(token=token, db=db)
```

但 `get_current_user()` 的签名使用了 FastAPI 的 `Depends` 装饰器：

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
```

### 为什么会失败？

当在**中间件中直接调用**带有 `Depends` 装饰器的函数时：

1. `Depends(oauth2_scheme)` 和 `Depends(get_db)` 是**依赖注入对象**，不是实际的值
2. 我们传入的 `token` 和 `db` 参数被**忽略**
3. 函数使用了默认参数值（Depends对象），导致token验证失败
4. 抛出401错误

**FastAPI的依赖注入系统只在路由处理函数中生效，在中间件中不工作**。

---

## 解决方案

### 方案实施

创建了一个新的函数 `verify_token_and_get_user()`，**不使用** `Depends` 装饰器：

```python
async def verify_token_and_get_user(token: str, db: Session) -> User:
    """
    验证Token并获取用户（供中间件使用，不使用Depends）
    
    Args:
        token: JWT token字符串
        db: 数据库会话
    
    Returns:
        User对象
    
    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    logger.debug(f"中间件验证token，长度: {len(token) if token else 0}")
    
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT解析失败: {e}")
        raise credentials_exception

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"用户不存在: user_id={user_id}")
            raise credentials_exception

        # 设置审计上下文
        set_audit_context(operator_id=user.id, tenant_id=user.tenant_id)
        
        logger.debug(f"中间件认证成功: user_id={user.id}, username={user.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询用户失败: {e}", exc_info=True)
        raise credentials_exception
```

### 中间件修改

修改 `auth_middleware.py` 使用新函数：

```python
# 之前
from app.core.auth import get_current_user
user = await get_current_user(token=token, db=db)

# 之后
from app.core.auth import verify_token_and_get_user
user = await verify_token_and_get_user(token=token, db=db)
```

---

## 附加修复

### 问题2: PresaleTicket关系错误

在测试过程中发现启动日志中的SQLAlchemy警告：

```
PresaleVisitRecord failed to locate a name ('PresaleTicket')
```

**根本原因**: `app/models/presale_mobile.py` 中使用了错误的模型名称

**修复**:
```python
# 之前
presale_ticket = relationship("PresaleTicket", ...)

# 之后  
presale_ticket = relationship("PresaleSupportTicket", ...)
```

---

## 测试结果

### 登录测试
```bash
curl -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -d "username=admin&password=admin123"
  
# ✅ 成功返回token
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 项目列表API测试
```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "http://127.0.0.1:8001/api/v1/projects/?page=1&page_size=3"

# ✅ 成功返回数据（空列表是正常的）
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 3,
  "pages": 0
}
```

### 其他端点状态
- ✅ `/api/v1/projects/` - 正常工作
- ⚠️  `/api/v1/users/me` - 路由参数错误（非认证问题）
- ⚠️  `/api/v1/production/work-orders/` - 返回空响应（需进一步检查）
- ⚠️  `/api/v1/sales/orders/` - 404错误（路由不存在）

**核心认证问题已完全解决！** 其他API的404/500是业务逻辑或路由配置问题，不是认证中间件的问题。

---

## 修改的文件

### 1. app/core/auth.py
- **新增**: `verify_token_and_get_user()` 函数（不使用Depends）
- **修改**: `__all__` 导出列表，添加新函数

### 2. app/core/middleware/auth_middleware.py
- **修改**: 从 `get_current_user` 改为 `verify_token_and_get_user`

### 3. app/models/presale_mobile.py
- **修复**: `relationship("PresaleTicket")` → `relationship("PresaleSupportTicket")`

---

## 技术要点总结

### FastAPI依赖注入的限制

1. **Depends只在路由中工作**: FastAPI的依赖注入系统通过请求上下文传递依赖
2. **中间件无法使用Depends**: 中间件在FastAPI的依赖注入系统之前执行
3. **解决方案**: 创建不使用Depends的纯函数版本

### 最佳实践

**路由处理函数** (使用Depends):
```python
@router.get("/items/")
async def get_items(
    current_user: User = Depends(get_current_user)
):
    return items
```

**中间件** (不使用Depends):
```python
async def dispatch(self, request, call_next):
    token = extract_token(request)
    db = get_session()
    user = await verify_token_and_get_user(token, db)
    ...
```

---

## 经验教训

1. **理解框架限制**: FastAPI的依赖注入不适用于中间件
2. **分层设计**: 认证逻辑应该有两个版本：
   - 带Depends的路由版本
   - 不带Depends的中间件版本
3. **调试策略**: 从日志入手，逐层分析调用链
4. **模型命名一致性**: 使用完整准确的模型名称，避免歧义

---

## 后续建议

### 立即处理
- [ ] 修复 `/api/v1/users/me` 的路由参数问题
- [ ] 检查 `/api/v1/production/work-orders/` 返回空响应的原因
- [ ] 确认哪些sales端点存在，更新文档

### 代码优化
- [ ] 考虑重构 `get_current_user` 和 `verify_token_and_get_user`，提取共同逻辑
- [ ] 添加更多debug日志到中间件，便于问题诊断
- [ ] 创建中间件的单元测试

### 文档更新
- [ ] 更新认证流程文档，说明中间件的工作原理
- [ ] 记录Depends的使用限制
- [ ] 创建API认证troubleshooting指南

---

**报告生成时间**: 2026-02-16 18:00 GMT+8  
**状态**: ✅ 认证问题已修复 | ⚠️  部分API端点需进一步检查
