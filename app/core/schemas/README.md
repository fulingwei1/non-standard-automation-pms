# 统一响应格式和验证器使用指南

> 确保所有API响应和验证的一致性

---

## 📋 目录

1. [统一响应格式](#统一响应格式)
2. [统一验证器](#统一验证器)
3. [使用规则](#使用规则)
4. [最佳实践](#最佳实践)

---

## 一、统一响应格式

### 1.1 响应类型

#### SuccessResponse - 成功响应

用于所有成功的API操作。

```python
from app.core.schemas.response import SuccessResponse, success_response

# 方式1：使用类
@router.post("/projects", response_model=SuccessResponse[ProjectResponse])
async def create_project(project: ProjectCreate):
    project_data = await service.create(project)
    return SuccessResponse(
        code=200,
        message="项目创建成功",
        data=project_data
    )

# 方式2：使用便捷函数（推荐）
@router.post("/projects")
async def create_project(project: ProjectCreate):
    project_data = await service.create(project)
    return success_response(
        data=project_data,
        message="项目创建成功"
    )
```

**响应格式**：
```json
{
  "success": true,
  "code": 200,
  "message": "项目创建成功",
  "data": {
    "id": 1,
    "name": "测试项目",
    "code": "PJ250101001"
  }
}
```

#### ErrorResponse - 错误响应

用于所有失败的API操作（通常由异常处理器自动生成）。

```python
from app.core.schemas.response import ErrorResponse, error_response
from fastapi import HTTPException

# 方式1：抛出HTTPException（推荐，由异常处理器处理）
@router.get("/projects/{id}")
async def get_project(id: int):
    project = await service.get(id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail="项目不存在"
        )

# 方式2：直接返回错误响应
@router.get("/projects/{id}")
async def get_project(id: int):
    project = await service.get(id)
    if not project:
        return error_response(
            message="项目不存在",
            code=404
        )
```

#### PaginatedResponse - 分页响应

用于列表查询的分页响应。

```python
from app.core.schemas.response import PaginatedResponse, paginated_response

@router.get("/projects", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    result = await service.list(skip=(page-1)*page_size, limit=page_size)
    
    # 方式1：使用类
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=(result["total"] + page_size - 1) // page_size
    )
    
    # 方式2：使用便捷函数（推荐）
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size
    )
```

**响应格式**：
```json
{
  "items": [
    {"id": 1, "name": "项目1"},
    {"id": 2, "name": "项目2"}
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

#### ListResponse - 列表响应（无分页）

用于不需要分页的列表响应。

```python
from app.core.schemas.response import ListResponse

@router.get("/statuses", response_model=ListResponse[StatusResponse])
async def list_statuses():
    statuses = await service.get_all_statuses()
    return ListResponse(
        items=statuses,
        total=len(statuses)
    )
```

---

## 二、统一验证器

### 2.1 项目相关验证

#### validate_project_code - 验证项目编码

```python
from app.core.schemas.validators import validate_project_code
from pydantic import field_validator

class ProjectCreate(BaseModel):
    code: str
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_project_code(v)
```

#### validate_machine_code - 验证机台编码

```python
from app.core.schemas.validators import validate_machine_code

class MachineCreate(BaseModel):
    code: str
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_machine_code(v)
```

### 2.2 联系方式验证

#### validate_phone - 验证手机号

```python
from app.core.schemas.validators import validate_phone

class ContactCreate(BaseModel):
    phone: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_phone(v)
```

#### validate_email - 验证邮箱

```python
from app.core.schemas.validators import validate_email

class UserCreate(BaseModel):
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email(v)
```

### 2.3 数值验证

#### validate_positive_number - 验证正数

```python
from app.core.schemas.validators import validate_positive_number

class ProjectCreate(BaseModel):
    amount: float
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        return validate_positive_number(v, field_name="金额")
```

#### validate_decimal - 验证Decimal数值

```python
from app.core.schemas.validators import validate_decimal
from decimal import Decimal

class ProjectCreate(BaseModel):
    price: Decimal
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        return validate_decimal(
            v,
            min_value=Decimal("0"),
            max_value=Decimal("999999.99"),
            precision=2,
            field_name="价格"
        )
```

### 2.4 字符串验证

#### validate_non_empty_string - 验证非空字符串

```python
from app.core.schemas.validators import validate_non_empty_string

class ProjectCreate(BaseModel):
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_non_empty_string(
            v,
            field_name="项目名称",
            min_length=2,
            max_length=100
        )
```

### 2.5 状态验证

#### validate_status - 验证状态值

```python
from app.core.schemas.validators import validate_status

class ProjectUpdate(BaseModel):
    status: str
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        return validate_status(
            v,
            allowed_statuses=["ACTIVE", "INACTIVE", "COMPLETED"],
            field_name="项目状态"
        )
```

---

## 三、使用规则

### 3.1 响应格式规则

#### ✅ 必须遵循

1. **所有API响应必须使用统一格式**
   - 成功响应：使用 `SuccessResponse` 或 `success_response()`
   - 错误响应：使用 `HTTPException`（由异常处理器自动转换为统一格式）
   - 列表响应：使用 `PaginatedResponse` 或 `ListResponse`

2. **响应代码规范**
   - 200: 成功
   - 201: 创建成功
   - 400: 请求参数错误
   - 401: 未授权
   - 403: 无权限
   - 404: 资源不存在
   - 422: 验证错误
   - 500: 服务器错误

3. **消息规范**
   - 使用中文，清晰明确
   - 成功消息：简洁明了（如"创建成功"）
   - 错误消息：用户友好，包含解决建议

#### ❌ 禁止做法

1. **不要直接返回数据**
   ```python
   # ❌ 错误
   @router.get("/projects/{id}")
   async def get_project(id: int):
       return project_data
   
   # ✅ 正确
   @router.get("/projects/{id}")
   async def get_project(id: int):
       return success_response(data=project_data)
   ```

2. **不要混用响应格式**
   ```python
   # ❌ 错误：混用不同格式
   return {"data": project_data}  # 有时用这个
   return SuccessResponse(...)     # 有时用这个
   
   # ✅ 正确：统一使用SuccessResponse
   return success_response(data=project_data)
   ```

### 3.2 验证器规则

#### ✅ 必须遵循

1. **所有用户输入必须验证**
   - 使用Pydantic的 `@field_validator` 装饰器
   - 使用统一的验证器函数

2. **验证器应该抛出 `ValueError`**
   - 错误消息清晰明确
   - 包含字段名称（如果适用）

3. **验证器应该返回格式化后的值**
   - 自动去除空格
   - 统一大小写（如需要）
   - 格式化数据（如需要）

#### ❌ 禁止做法

1. **不要在业务逻辑中验证**
   ```python
   # ❌ 错误：在业务逻辑中验证
   async def create_project(project: ProjectCreate):
       if not project.code.startswith("PJ"):
           raise ValueError("...")
   
   # ✅ 正确：在Schema中验证
   class ProjectCreate(BaseModel):
       code: str
       
       @field_validator('code')
       @classmethod
       def validate_code(cls, v: str) -> str:
           return validate_project_code(v)
   ```

2. **不要重复验证**
   ```python
   # ❌ 错误：重复验证
   @field_validator('code')
   def validate_code(cls, v: str) -> str:
       if not v:
           raise ValueError("不能为空")
       if not v.startswith("PJ"):
           raise ValueError("必须以PJ开头")
       # ... 更多验证
   
   # ✅ 正确：使用统一验证器
   @field_validator('code')
   def validate_code(cls, v: str) -> str:
       return validate_project_code(v)  # 包含所有验证逻辑
   ```

---

## 四、最佳实践

### 4.1 响应格式最佳实践

#### 1. 使用便捷函数

```python
# ✅ 推荐：使用便捷函数
return success_response(data=project_data, message="创建成功")

# ⚠️ 可用：使用类
return SuccessResponse(code=200, message="创建成功", data=project_data)
```

#### 2. 统一消息模板

```python
# 定义消息常量
MESSAGES = {
    "CREATE_SUCCESS": "创建成功",
    "UPDATE_SUCCESS": "更新成功",
    "DELETE_SUCCESS": "删除成功",
}

# 使用
return success_response(data=project_data, message=MESSAGES["CREATE_SUCCESS"])
```

#### 3. 分页响应自动计算

```python
# ✅ 推荐：使用便捷函数自动计算pages
return paginated_response(
    items=result["items"],
    total=result["total"],
    page=page,
    page_size=page_size
)
```

### 4.2 验证器最佳实践

#### 1. 在Schema中集中验证

```python
class ProjectCreate(BaseModel):
    code: str
    name: str
    amount: Decimal
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_project_code(v)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_non_empty_string(v, field_name="项目名称", min_length=2, max_length=100)
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        return validate_decimal(v, min_value=Decimal("0"), precision=2, field_name="金额")
```

#### 2. 创建自定义验证器

```python
# app/core/schemas/validators.py
def validate_custom_field(value: str, **kwargs) -> str:
    """自定义验证器"""
    # 验证逻辑
    return value

# 在Schema中使用
@field_validator('custom_field')
@classmethod
def validate_custom_field(cls, v: str) -> str:
    return validate_custom_field(v)
```

#### 3. 组合验证器

```python
class ContactCreate(BaseModel):
    contact: str  # 可以是手机号或邮箱
    
    @field_validator('contact')
    @classmethod
    def validate_contact(cls, v: str) -> str:
        return validate_phone_or_email(v)
```

---

## 五、完整示例

### 5.1 完整的CRUD端点示例

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.core.schemas.validators import (
    validate_project_code,
    validate_non_empty_string,
)
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/", response_model=SuccessResponse[ProjectResponse])
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建项目"""
    service = ProjectService(db)
    project_data = await service.create(project)
    return success_response(
        data=project_data,
        message="项目创建成功"
    )

@router.get("/{id}", response_model=SuccessResponse[ProjectResponse])
async def get_project(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取项目"""
    service = ProjectService(db)
    project = await service.get(id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return success_response(data=project)

@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """列表查询项目"""
    service = ProjectService(db)
    result = await service.list(
        skip=(page-1)*page_size,
        limit=page_size,
        keyword=keyword,
        keyword_fields=["name", "code"]
    )
    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size
    )
```

### 5.2 完整的Schema验证示例

```python
from pydantic import BaseModel, field_validator
from decimal import Decimal
from app.core.schemas.validators import (
    validate_project_code,
    validate_non_empty_string,
    validate_decimal,
    validate_status,
)

class ProjectCreate(BaseModel):
    """项目创建Schema"""
    code: str
    name: str
    amount: Decimal
    status: str = "ACTIVE"
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        return validate_project_code(v)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_non_empty_string(
            v,
            field_name="项目名称",
            min_length=2,
            max_length=100
        )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        return validate_decimal(
            v,
            min_value=Decimal("0"),
            precision=2,
            field_name="项目金额"
        )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        return validate_status(
            v,
            allowed_statuses=["ACTIVE", "INACTIVE", "COMPLETED"],
            field_name="项目状态"
        )
```

---

## 六、常见问题

### Q1: 什么时候使用SuccessResponse，什么时候直接返回数据？

**A**: 所有API都应该使用统一响应格式。只有内部函数可以直接返回数据。

### Q2: 验证器应该放在哪里？

**A**: 验证器应该放在Schema的 `@field_validator` 中，而不是业务逻辑中。

### Q3: 如何添加自定义验证器？

**A**: 在 `app/core/schemas/validators.py` 中添加新函数，然后在Schema中使用。

### Q4: 错误响应如何处理？

**A**: 使用 `HTTPException`，异常处理器会自动转换为统一格式。

---

**最后更新**：2026-01-23  
**版本**：v1.0
