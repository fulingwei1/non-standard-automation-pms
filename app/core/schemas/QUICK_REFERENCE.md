# 统一响应格式和验证器 - 快速参考

> 快速查找常用代码片段

---

## 🚀 快速使用

### 响应格式

```python
from app.core.schemas.response import success_response, paginated_response

# 成功响应
return success_response(data=project_data, message="创建成功")

# 分页响应
return paginated_response(
    items=result["items"],
    total=result["total"],
    page=page,
    page_size=page_size
)
```

### 验证器

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

---

## 📋 常用验证器

| 验证器 | 用途 | 示例 |
|--------|------|------|
| `validate_project_code` | 项目编码 | `PJ250101001` |
| `validate_phone` | 手机号 | `13800138000` |
| `validate_email` | 邮箱 | `test@example.com` |
| `validate_positive_number` | 正数 | `10.5` |
| `validate_decimal` | Decimal数值 | `Decimal("10.50")` |
| `validate_non_empty_string` | 非空字符串 | `"项目名称"` |
| `validate_status` | 状态值 | `"ACTIVE"` |

---

## 📖 完整文档

- **详细指南**：`README.md`
- **架构说明**：`../../docs/统一响应格式和验证器架构说明.md`
- **使用规则**：`../../docs/统一响应格式和验证器使用规则.md`
