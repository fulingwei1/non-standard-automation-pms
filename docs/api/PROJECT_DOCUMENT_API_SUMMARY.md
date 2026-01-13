# 项目文档管理 API 实现总结

## 概述

本文档总结了项目文档管理功能的 API 实现情况。

## 实现时间

2025-01-XX

## 1. API 端点

### 1.1 文档记录列表

**端点**: `GET /api/v1/documents`

**功能**:
- 获取文档记录列表（支持分页、筛选）
- 支持多条件筛选

**请求参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大100）
- `project_id`: 项目ID筛选（可选）
- `machine_id`: 机台ID筛选（可选）
- `doc_type`: 文档类型筛选（可选）
- `doc_category`: 文档分类筛选（可选）
- `status`: 状态筛选（可选）

**响应**: `PaginatedResponse[ProjectDocumentResponse]`

### 1.2 项目文档列表

**端点**: `GET /api/v1/documents/projects/{project_id}/documents`

**功能**:
- 获取指定项目的文档记录列表
- 支持按机台和文档类型筛选

**请求参数**:
- `project_id`: 项目ID（路径参数）
- `machine_id`: 机台ID筛选（查询参数，可选）
- `doc_type`: 文档类型筛选（查询参数，可选）

**响应**: `List[ProjectDocumentResponse]`

### 1.3 获取文档详情

**端点**: `GET /api/v1/documents/{doc_id}`

**功能**:
- 获取文档记录详情

**响应**: `ProjectDocumentResponse`

### 1.4 创建文档记录

**端点**: `POST /api/v1/documents`

**功能**:
- 创建新的文档记录
- 自动设置上传人
- 验证机台是否属于项目

**请求体**: `ProjectDocumentCreate`

**响应**: `ProjectDocumentResponse`

**特性**:
- ✅ 自动设置上传人（`uploaded_by`）
- ✅ 验证项目存在性
- ✅ 验证机台归属（如果指定了机台）

### 1.5 为项目创建文档记录

**端点**: `POST /api/v1/documents/projects/{project_id}/documents`

**功能**:
- 为指定项目创建文档记录
- 自动确保project_id一致

**请求参数**:
- `project_id`: 项目ID（路径参数）

**请求体**: `ProjectDocumentCreate`

**响应**: `ProjectDocumentResponse`

### 1.6 更新文档记录

**端点**: `PUT /api/v1/documents/{doc_id}`

**功能**:
- 更新文档记录
- 支持部分更新

**请求体**: `ProjectDocumentUpdate`

**响应**: `ProjectDocumentResponse`

### 1.7 下载文档

**端点**: `GET /api/v1/documents/{doc_id}/download`

**功能**:
- 下载文档文件
- 返回文件流

**响应**: `FileResponse`

**特性**:
- ✅ 支持相对路径和绝对路径
- ✅ 自动设置文件名和媒体类型
- ✅ 文件不存在时返回404

**文件路径处理**:
- 如果 `file_path` 是相对路径，自动转换为 `uploads/documents/` 目录下的路径
- 如果 `file_path` 是绝对路径，直接使用

### 1.8 文档版本管理

**端点**: `GET /api/v1/documents/{doc_id}/versions`

**功能**:
- 获取文档的所有版本
- 基于文档编号（`doc_no`）或文档名称（`doc_name`）匹配

**响应**: `List[ProjectDocumentResponse]`

**版本匹配逻辑**:
1. 如果文档有 `doc_no`，按 `doc_no` 匹配同一项目的所有版本
2. 如果没有 `doc_no`，按 `doc_name` 匹配
3. 如果指定了机台，也按机台筛选
4. 按创建时间倒序排列（最新版本在前）

**注意**: 当前实现基于文档编号或名称匹配，后续可以优化为更精确的版本管理（如添加 `parent_doc_id` 字段）。

### 1.9 删除文档记录

**端点**: `DELETE /api/v1/documents/{doc_id}`

**功能**:
- 删除文档记录
- 注意：只删除数据库记录，不删除实际文件

**响应**: `ResponseModel`

**后续优化**: 可以添加选项来控制是否同时删除文件。

## 2. Schema 定义

### 2.1 ProjectDocumentCreate

```python
class ProjectDocumentCreate(BaseModel):
    """创建文档记录"""
    
    project_id: int
    machine_id: Optional[int] = None
    doc_type: str
    doc_category: Optional[str] = None
    doc_name: str
    doc_no: Optional[str] = None
    version: str = "1.0"
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
```

### 2.2 ProjectDocumentUpdate

```python
class ProjectDocumentUpdate(BaseModel):
    """更新文档记录"""
    
    machine_id: Optional[int] = None
    doc_type: Optional[str] = None
    doc_category: Optional[str] = None
    doc_name: Optional[str] = None
    doc_no: Optional[str] = None
    version: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
```

### 2.3 ProjectDocumentResponse

```python
class ProjectDocumentResponse(TimestampSchema):
    """文档记录响应"""
    
    id: int
    project_id: int
    machine_id: Optional[int] = None
    doc_type: str
    doc_category: Optional[str] = None
    doc_name: str
    doc_no: Optional[str] = None
    version: str
    file_path: str
    file_name: str
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[date] = None
    description: Optional[str] = None
    uploaded_by: Optional[int] = None
```

## 3. 实现特性

### 3.1 文件管理

- ✅ 文档上传目录：`uploads/documents/`
- ✅ 支持相对路径和绝对路径
- ✅ 文件下载功能
- ⚠️ 文件上传功能（需要前端配合，当前只记录文件路径）

### 3.2 数据验证

- ✅ 验证项目存在性
- ✅ 验证机台归属（如果指定了机台，确保机台属于该项目）
- ✅ 自动设置上传人

### 3.3 查询优化

- ✅ 支持多条件筛选
- ✅ 分页支持
- ✅ 按创建时间倒序排列

### 3.4 版本管理

- ✅ 基于文档编号或名称的版本匹配
- ✅ 支持查看所有版本
- ⚠️ 后续可以优化为更精确的版本管理（添加 `parent_doc_id` 字段）

## 4. 安全特性

- ✅ JWT 认证（所有端点）
- ✅ 用户权限检查
- ✅ 数据验证

## 5. 错误处理

- ✅ 404：项目/机台/文档记录不存在、文件不存在
- ✅ 400：机台不属于项目
- ✅ 401：未认证
- ✅ 403：无权限

## 6. 使用示例

### 6.1 创建文档记录

```bash
POST /api/v1/documents
Content-Type: application/json

{
  "project_id": 1,
  "machine_id": 1,
  "doc_type": "DRAWING",
  "doc_category": "MECHANICAL",
  "doc_name": "设备总装图",
  "doc_no": "DRW-001",
  "version": "1.0",
  "file_path": "documents/project_1/machine_1/drw-001-v1.0.pdf",
  "file_name": "drw-001-v1.0.pdf",
  "file_size": 1024000,
  "file_type": "application/pdf",
  "description": "设备总装图纸"
}
```

### 6.2 下载文档

```bash
GET /api/v1/documents/1/download
```

**响应**: 文件流，自动下载

### 6.3 获取文档版本

```bash
GET /api/v1/documents/1/versions
```

**响应**:
```json
[
  {
    "id": 3,
    "doc_no": "DRW-001",
    "version": "2.0",
    "doc_name": "设备总装图",
    "created_at": "2025-01-20T10:00:00"
  },
  {
    "id": 1,
    "doc_no": "DRW-001",
    "version": "1.0",
    "doc_name": "设备总装图",
    "created_at": "2025-01-15T10:00:00"
  }
]
```

## 7. 后续优化建议

1. **文件上传功能**: 实现真正的文件上传API（使用 `UploadFile`）
2. **版本管理优化**: 
   - 添加 `parent_doc_id` 字段，建立明确的版本关系
   - 支持版本比较功能
3. **文件存储优化**:
   - 使用对象存储（如OSS、S3）替代本地文件系统
   - 支持文件预览（PDF、图片等）
4. **权限控制**: 
   - 文档访问权限控制
   - 文档审批流程
5. **文档分类**: 
   - 更详细的文档分类体系
   - 文档标签功能
6. **搜索功能**: 
   - 全文搜索
   - 按内容搜索
7. **文档关联**: 
   - 文档与BOM关联
   - 文档与任务关联
8. **批量操作**: 
   - 批量上传
   - 批量下载
   - 批量删除

## 8. 相关文件

- `app/api/v1/endpoints/documents.py` - 文档管理API实现
- `app/models/project.py` - ProjectDocument 模型定义
- `app/schemas/project.py` - 文档相关Schema定义
- `app/core/config.py` - 配置文件（UPLOAD_DIR）
- `app/api/v1/api.py` - API路由注册

## 9. 文件存储

**上传目录**: `uploads/documents/`

**目录结构建议**:
```
uploads/
  documents/
    project_{project_id}/
      machine_{machine_id}/
        {doc_no}-v{version}.{ext}
```

**配置**:
- `UPLOAD_DIR`: 在 `app/core/config.py` 中配置，默认为 `uploads`
- `MAX_UPLOAD_SIZE`: 最大上传文件大小，默认10MB



