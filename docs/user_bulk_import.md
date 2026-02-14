# 用户批量导入功能文档

## 功能概述

用户批量导入功能允许管理员通过 Excel 或 CSV 文件快速批量创建用户账号，支持数据验证、去重检查、角色分配等功能。

## 主要特性

- ✅ 支持 Excel (.xlsx, .xls) 和 CSV 格式
- ✅ 支持字段映射（中文/英文列名）
- ✅ 完整的数据验证（格式、去重、必填）
- ✅ 事务处理（全部成功或全部回滚）
- ✅ 导入结果详细报告
- ✅ 模板文件下载
- ✅ 数据预览功能
- ✅ 单次限制 500 条（防止性能问题）

## API 端点

### 1. 下载导入模板

**请求方式**: `GET /api/v1/users/import/template`

**参数**:
- `format`: 文件格式，可选 `xlsx` (默认) 或 `csv`

**示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/users/import/template?format=xlsx" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output user_template.xlsx
```

**响应**: 返回模板文件（包含示例数据）

---

### 2. 预览导入数据

**请求方式**: `POST /api/v1/users/import/preview`

**功能**: 上传文件后验证数据，但不实际导入

**参数**:
- `file`: 上传的 Excel 或 CSV 文件（multipart/form-data）

**示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/users/import/preview" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@users.xlsx"
```

**响应示例**:
```json
{
  "code": 200,
  "message": "数据预览：共 10 条，验证通过",
  "data": {
    "total": 10,
    "is_valid": true,
    "preview": [
      {
        "row": 2,
        "username": "zhangsan",
        "real_name": "张三",
        "email": "zhangsan@example.com",
        "department": "技术部",
        "position": "工程师",
        "roles": "普通用户"
      }
    ],
    "errors": []
  }
}
```

---

### 3. 批量导入用户

**请求方式**: `POST /api/v1/users/import`

**功能**: 实际执行批量导入

**参数**:
- `file`: 上传的 Excel 或 CSV 文件（multipart/form-data）

**示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/users/import" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@users.xlsx"
```

**响应示例（成功）**:
```json
{
  "code": 200,
  "message": "导入完成：成功 10 条，失败 0 条",
  "data": {
    "total": 10,
    "success_count": 10,
    "failed_count": 0,
    "errors": [],
    "success_users": [
      {
        "username": "zhangsan",
        "real_name": "张三",
        "email": "zhangsan@example.com"
      }
    ]
  }
}
```

**响应示例（部分失败）**:
```json
{
  "code": 200,
  "message": "导入完成：成功 0 条，失败 10 条",
  "data": {
    "total": 10,
    "success_count": 0,
    "failed_count": 10,
    "errors": [
      {
        "row": 3,
        "error": "第3行: 邮箱 'duplicate@example.com' 已存在于系统中"
      },
      {
        "row": 5,
        "error": "第5行: 用户名长度必须在3-50个字符之间"
      }
    ],
    "success_users": []
  }
}
```

## 文件格式说明

### 支持的字段

| 中文列名 | 英文列名 | 内部字段名 | 是否必填 | 说明 |
|---------|---------|-----------|---------|------|
| 用户名 | Username | username | ✅ 是 | 长度 3-50，唯一 |
| 密码 | Password | password | ❌ 否 | 留空则使用默认密码 123456 |
| 真实姓名 | Real Name | real_name | ✅ 是 | 用户真实姓名 |
| 邮箱 | Email | email | ✅ 是 | 唯一，需符合邮箱格式 |
| 手机号 | Phone | phone | ❌ 否 | 11位数字 |
| 工号 | Employee No | employee_no | ❌ 否 | 员工工号 |
| 部门 | Department | department | ❌ 否 | 所属部门 |
| 职位 | Position | position | ❌ 否 | 职位名称 |
| 角色 | Roles | roles | ❌ 否 | 多个角色用逗号分隔 |
| 是否启用 | Is Active | is_active | ❌ 否 | 是/否，true/false，1/0 |

### Excel 示例

| 用户名 | 密码 | 真实姓名 | 邮箱 | 手机号 | 工号 | 部门 | 职位 | 角色 | 是否启用 |
|--------|------|---------|------|--------|------|------|------|------|---------|
| zhangsan | 123456 | 张三 | zhangsan@example.com | 13800138000 | EMP001 | 技术部 | 工程师 | 普通用户 | 是 |
| lisi | 123456 | 李四 | lisi@example.com | 13800138001 | EMP002 | 销售部 | 销售经理 | 销售经理,普通用户 | 是 |
| wangwu |  | 王五 | wangwu@example.com |  | EMP003 | 市场部 | 市场专员 | 普通用户 | 否 |

### CSV 示例

```csv
用户名,密码,真实姓名,邮箱,手机号,工号,部门,职位,角色,是否启用
zhangsan,123456,张三,zhangsan@example.com,13800138000,EMP001,技术部,工程师,普通用户,是
lisi,123456,李四,lisi@example.com,13800138001,EMP002,销售部,销售经理,"销售经理,普通用户",是
wangwu,,王五,wangwu@example.com,,EMP003,市场部,市场专员,普通用户,否
```

## 数据验证规则

### 1. 格式验证
- **用户名**: 长度 3-50 字符
- **邮箱**: 必须包含 @ 和 .
- **手机号**: 11 位数字（可选）

### 2. 唯一性验证
- **用户名**: 文件内唯一 + 系统内唯一
- **邮箱**: 文件内唯一 + 系统内唯一

### 3. 必填字段
- 用户名
- 真实姓名
- 邮箱

### 4. 角色验证
- 角色名称必须在系统中存在
- 多个角色用英文逗号分隔
- 不存在的角色会被跳过，并记录警告

## 事务处理

- ✅ **全部成功或全部回滚**: 如果任何一条数据导入失败，整个批次都会回滚
- ✅ **数据一致性**: 保证不会出现部分导入的情况
- ❌ **失败后不会保留**: 失败后需要修正数据重新导入

## 性能限制

- **单次最大数量**: 500 条
- **建议分批导入**: 超过 500 条建议拆分多个文件
- **超时保护**: 避免大文件导致服务器超时

## 使用流程

### 方式一：直接导入

1. 下载模板文件
2. 填写用户数据
3. 直接上传导入
4. 查看导入结果

### 方式二：预览后导入（推荐）

1. 下载模板文件
2. 填写用户数据
3. **先使用预览接口验证**
4. 修正错误数据
5. 再使用导入接口
6. 查看导入结果

## 常见问题

### Q1: 密码为空会怎样？
**A**: 系统会自动使用默认密码 `123456`，用户首次登录后应修改密码。

### Q2: 角色不存在会报错吗？
**A**: 不会报错，但会跳过该角色并记录警告日志。建议先在系统中创建角色。

### Q3: 导入失败后数据会保留吗？
**A**: 不会。采用事务处理，失败后会回滚，不会有任何数据残留。

### Q4: 可以更新已存在的用户吗？
**A**: 当前版本不支持更新，只能创建新用户。重复用户名或邮箱会导致验证失败。

### Q5: 支持哪些角色分隔符？
**A**: 只支持英文逗号 `,`。例如: `销售经理,普通用户`

### Q6: 文件编码有要求吗？
**A**: CSV 文件建议使用 `UTF-8 with BOM` 编码，Excel 无编码问题。

## 权限要求

- 下载模板: `user:read` 权限
- 预览数据: `user:read` 权限
- 批量导入: `user:create` 权限

## 错误码说明

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 成功（可能部分失败，需查看 data.errors） |
| 400 | 请求错误（文件格式、数据验证失败） |
| 401 | 未授权（未登录） |
| 403 | 权限不足 |
| 500 | 服务器内部错误 |

## 安全建议

1. ✅ 导入前先使用预览功能
2. ✅ 小批量测试后再大批量导入
3. ✅ 设置强密码策略
4. ✅ 导入后通知用户修改默认密码
5. ✅ 定期审计导入日志

## 更新日志

### v1.0.0 (2026-02-14)
- ✅ 初始版本发布
- ✅ 支持 Excel/CSV 导入
- ✅ 支持数据验证和预览
- ✅ 支持事务处理
- ✅ 支持角色分配
