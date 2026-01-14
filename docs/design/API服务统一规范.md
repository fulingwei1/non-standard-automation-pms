# API服务统一规范

> **创建日期**：2026-01-14  
> **状态**：📋 规范文档

---

## 一、概述

本文档定义了API服务的统一规范，包括响应格式、错误处理、服务层结构等，旨在提高代码一致性和可维护性。

---

## 二、响应格式统一

### 2.1 标准响应格式

所有API应使用统一的响应格式：

```python
from app.schemas.common import ResponseModel

# 成功响应
ResponseModel(
    code=200,
    message="success",
    data={...}  # 实际数据
)

# 错误响应
ResponseModel(
    code=400,  # 或其他错误代码
    message="错误描述",
    data=None  # 或错误详情
)
```

### 2.2 分页响应格式

列表查询应使用分页响应：

```python
from app.schemas.common import PaginatedResponse

PaginatedResponse(
    items=[...],      # 数据列表
    total=100,        # 总记录数
    page=1,          # 当前页码
    page_size=20,     # 每页条数
    pages=5          # 总页数
)
```

### 2.3 使用BaseAPIService

推荐使用 `BaseAPIService` 创建统一响应：

```python
from app.api.base_service import BaseAPIService

class MyService(BaseAPIService):
    def get_item(self, item_id: int):
        # 成功响应
        return self.success_response(data=item)
        
        # 错误响应
        return self.error_response(message="错误信息", code=400)
        
        # 分页响应
        return self.paginated_response(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
```

---

## 三、错误处理统一

### 3.1 HTTP状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 正常请求成功 |
| 400 | 请求错误 | 参数错误、业务逻辑错误 |
| 401 | 未授权 | 未登录或token无效 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 资源不存在 |
| 500 | 服务器错误 | 系统内部错误 |

### 3.2 错误响应格式

```python
# 使用BaseAPIService抛出错误
BaseAPIService.raise_not_found("项目", project_id)
BaseAPIService.raise_bad_request("参数错误")
BaseAPIService.raise_forbidden("权限不足")
BaseAPIService.raise_unauthorized("未授权")

# 或直接使用HTTPException
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="项目不存在"
)
```

### 3.3 验证资源存在

```python
# 使用BaseAPIService验证
project = BaseAPIService.validate_exists(
    db=db,
    model_class=Project,
    id=project_id,
    resource_name="项目"
)
```

---

## 四、服务层结构

### 4.1 服务层职责

- **业务逻辑处理**：复杂的业务逻辑应在服务层实现
- **数据验证**：业务规则验证
- **数据转换**：模型与Schema之间的转换
- **事务管理**：复杂操作的事务控制

### 4.2 服务层示例

```python
# app/services/my_service.py
from app.api.base_service import BaseAPIService
from app.models.my_model import MyModel
from app.schemas.my_schema import MyCreate, MyUpdate, MyResponse

class MyService(BaseAPIService):
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: MyCreate) -> MyResponse:
        """创建资源"""
        # 业务逻辑验证
        if self._check_duplicate(data.name):
            self.raise_bad_request("名称已存在")
        
        # 创建模型
        instance = MyModel(**data.dict())
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        
        return MyResponse.from_orm(instance)
    
    def _check_duplicate(self, name: str) -> bool:
        """检查名称是否重复"""
        return self.db.query(MyModel).filter(
            MyModel.name == name
        ).first() is not None
```

### 4.3 API端点使用服务层

```python
# app/api/v1/endpoints/my_endpoint.py
from app.services.my_service import MyService

@router.post("/", response_model=ResponseModel[MyResponse])
def create_item(
    data: MyCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("my:create"))
):
    """创建资源"""
    service = MyService(db)
    result = service.create(data)
    return BaseAPIService.success_response(data=result)
```

---

## 五、迁移指南

### 5.1 现有API迁移步骤

1. **识别需要迁移的API**
   - 查找直接返回数据的API
   - 查找错误处理不统一的API

2. **创建服务层**
   - 将业务逻辑从端点移到服务层
   - 使用 `BaseAPIService` 作为基类

3. **更新端点**
   - 使用服务层方法
   - 使用统一的响应格式

4. **测试验证**
   - 确保功能正常
   - 确保响应格式一致

### 5.2 迁移示例

**迁移前：**
```python
@router.get("/{item_id}")
def get_item(item_id: int, db: Session = Depends(deps.get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    return item  # 直接返回模型
```

**迁移后：**
```python
@router.get("/{item_id}", response_model=ResponseModel[ItemResponse])
def get_item(item_id: int, db: Session = Depends(deps.get_db)):
    service = ItemService(db)
    item = service.get_by_id(item_id)
    return BaseAPIService.success_response(data=item)
```

---

## 六、最佳实践

### 6.1 响应格式

✅ **推荐：**
```python
return BaseAPIService.success_response(data=result)
```

❌ **不推荐：**
```python
return result  # 直接返回数据
return {"code": 200, "data": result}  # 手动构造响应
```

### 6.2 错误处理

✅ **推荐：**
```python
BaseAPIService.raise_not_found("项目", project_id)
```

❌ **不推荐：**
```python
raise HTTPException(status_code=404, detail="项目不存在")  # 消息不统一
return {"error": "项目不存在"}  # 不使用HTTP状态码
```

### 6.3 服务层

✅ **推荐：**
- 将复杂业务逻辑放在服务层
- 使用服务层方法复用代码
- 服务层方法应该是纯函数（可测试）

❌ **不推荐：**
- 在端点中写大量业务逻辑
- 直接操作数据库而不通过服务层
- 服务层方法依赖请求上下文

---

## 七、检查清单

在创建或修改API时，请确认：

- [ ] 使用 `ResponseModel` 或 `PaginatedResponse` 作为响应格式
- [ ] 使用 `BaseAPIService` 创建响应和抛出错误
- [ ] 错误消息清晰、统一
- [ ] HTTP状态码使用正确
- [ ] 复杂业务逻辑在服务层实现
- [ ] 资源验证使用 `validate_exists` 方法
- [ ] API文档（docstring）完整

---

## 八、相关文件

- `app/api/base_service.py` - API服务基类
- `app/schemas/common.py` - 通用响应模型
- `app/api/v1/endpoints/` - API端点示例

---

**文档版本**：v1.0  
**创建日期**：2026-01-14  
**最后更新**：2026-01-14
