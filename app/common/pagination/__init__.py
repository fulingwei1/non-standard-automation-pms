# Pagination Tools

分页工具模块，提供统一的分页逻辑，消除重复代码。

## 使用示例

```python
from app.common.pagination import PaginationHelper

# 基本分页
query = db.query(Project)
result = PaginationHelper.paginate(query, page=1, page_size=20)

# 返回结果
{
    "items": [...],      # 当前页数据
    "total": 100,        # 总记录数
    "page": 1,           # 当前页码
    "page_size": 20,      # 每页大小
    "total_pages": 5      # 总页数
}
```
