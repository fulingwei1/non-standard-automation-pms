# BOM版本管理和导入导出功能实现总结

## 概述

本文档总结了BOM版本管理、导入导出功能的 API 实现情况。

## 实现时间

2025-01-XX

## 1. BOM版本管理 API

### 1.1 发布BOM版本

**端点**: `POST /api/v1/bom/{bom_id}/release`

**功能**:
- 将BOM状态从 `DRAFT` 改为 `RELEASED`
- 标记为最新版本（`is_latest=True`）
- 将同一BOM编号的其他版本标记为非最新版本
- 记录审批人和审批时间

**请求参数**:
- `bom_id`: BOM ID（路径参数）
- `change_note`: 变更说明（查询参数，可选）

**响应**: `BomResponse`

**业务规则**:
- ✅ 只有草稿状态的BOM才能发布
- ✅ 必须有明细才能发布
- ✅ 自动更新版本标记

### 1.2 获取BOM版本列表

**端点**: `GET /api/v1/bom/{bom_id}/versions`

**功能**:
- 获取BOM的所有版本列表
- 基于BOM编号查找所有版本
- 按创建时间倒序排列

**响应**: `List[BomResponse]`

**注意**: 版本列表不包含明细，需要明细时调用详情接口。

### 1.3 BOM版本对比

**端点**: `GET /api/v1/bom/{bom_id}/versions/compare`

**功能**:
- 对比BOM的两个版本
- 识别新增、删除、修改的物料
- 提供详细的对比结果

**请求参数**:
- `bom_id`: BOM ID（路径参数）
- `version1_id`: 版本1的BOM ID（查询参数，可选）
- `version2_id`: 版本2的BOM ID（查询参数，可选）

**默认行为**: 如果不提供version1_id和version2_id，则对比当前版本和最新发布版本。

**响应**: `dict`

**响应结构**:
```json
{
  "version1": {
    "id": 1,
    "version": "1.0",
    "status": "RELEASED",
    "total_items": 50,
    "total_amount": 100000.00
  },
  "version2": {
    "id": 2,
    "version": "2.0",
    "status": "RELEASED",
    "total_items": 55,
    "total_amount": 120000.00
  },
  "comparison": {
    "added": [
      {
        "material_code": "MAT-003",
        "material_name": "新增物料",
        "quantity": 10,
        "unit_price": 5.0
      }
    ],
    "deleted": [
      {
        "material_code": "MAT-001",
        "material_name": "删除物料",
        "quantity": 5,
        "unit_price": 2.0
      }
    ],
    "modified": [
      {
        "material_code": "MAT-002",
        "material_name": "修改物料",
        "v1": {
          "quantity": 10,
          "unit_price": 3.0,
          "specification": "规格1"
        },
        "v2": {
          "quantity": 15,
          "unit_price": 3.5,
          "specification": "规格2"
        }
      }
    ],
    "unchanged": [
      {
        "material_code": "MAT-004",
        "material_name": "未变更物料",
        "quantity": 20
      }
    ],
    "summary": {
      "added_count": 1,
      "deleted_count": 1,
      "modified_count": 1,
      "unchanged_count": 1
    }
  }
}
```

## 2. BOM导入导出 API

### 2.1 从Excel导入BOM明细

**端点**: `POST /api/v1/bom/{bom_id}/import`

**功能**:
- 从Excel文件导入BOM明细
- 支持批量导入
- 自动验证数据格式
- 自动计算金额和行号

**请求参数**:
- `bom_id`: BOM ID（路径参数）
- `file`: Excel文件（multipart/form-data）

**Excel格式要求**:
- 必需列：物料编码、物料名称、数量
- 可选列：规格型号、单位、单价、来源类型、是否关键、备注

**响应**: `ResponseModel`

**响应数据**:
```json
{
  "code": 200,
  "message": "导入完成：成功50条，失败2条",
  "data": {
    "imported_count": 50,
    "error_count": 2,
    "errors": ["第3行：数据不完整", "第10行：数量无效"]
  }
}
```

**业务规则**:
- ✅ 只有草稿状态的BOM才能导入
- ✅ 自动验证必需列
- ✅ 自动匹配物料（如果物料编码存在）
- ✅ 自动计算行号和金额
- ✅ 自动更新BOM统计

**错误处理**:
- 记录每行的错误信息
- 返回前10个错误（避免响应过大）
- 部分成功时仍会提交已成功的数据

### 2.2 导出BOM到Excel

**端点**: `GET /api/v1/bom/{bom_id}/export`

**功能**:
- 导出BOM明细到Excel文件
- 包含完整的明细信息
- 自动设置列宽
- 生成带时间戳的文件名

**响应**: Excel文件流

**导出字段**:
- 行号
- 物料编码
- 物料名称
- 规格型号
- 图号
- 单位
- 数量
- 单价
- 金额
- 来源类型
- 需求日期
- 已采购数量
- 已到货数量
- 是否关键
- 备注

**文件名格式**: `BOM_{bom_no}_v{version}_{timestamp}.xlsx`

### 2.3 下载BOM导入模板

**端点**: `GET /api/v1/bom/template/download`

**功能**:
- 下载BOM导入Excel模板
- 包含示例数据
- 自动设置列宽

**响应**: Excel文件流

**文件名**: `BOM导入模板.xlsx`

**模板字段**:
- 物料编码（示例：MAT-001）
- 物料名称（示例：示例物料1）
- 规格型号（示例：规格1）
- 单位（示例：件）
- 数量（示例：10）
- 单价（示例：1.5）
- 来源类型（示例：PURCHASE）
- 是否关键（示例：False）
- 备注

## 3. 技术实现

### 3.1 Excel处理库

使用 `pandas` 和 `openpyxl` 库处理Excel文件：
- `pandas`: 用于读取和写入Excel
- `openpyxl`: Excel引擎

**依赖检查**:
- 如果库未安装，返回友好的错误提示
- 在 `requirements.txt` 中已包含这些依赖

### 3.2 文件处理

- **导入**: 使用 `UploadFile` 接收文件，异步读取
- **导出**: 使用 `StreamingResponse` 返回文件流
- **模板**: 使用 `StreamingResponse` 返回模板文件

### 3.3 数据验证

- ✅ 必需列验证
- ✅ 数据类型验证
- ✅ 数量有效性验证（>0）
- ✅ 物料编码格式验证

### 3.4 错误处理

- ✅ 逐行验证，记录错误
- ✅ 部分成功时提交已成功的数据
- ✅ 返回错误统计和错误列表
- ✅ 数据库事务回滚（如果全部失败）

## 4. 使用示例

### 4.1 发布BOM版本

```bash
POST /api/v1/bom/1/release?change_note=首次发布
```

**响应**:
```json
{
  "id": 1,
  "bom_no": "BOM-PJ202501-001",
  "status": "RELEASED",
  "is_latest": true,
  "approved_by": 1,
  "approved_at": "2025-01-XX 10:00:00"
}
```

### 4.2 导入BOM明细

```bash
POST /api/v1/bom/1/import
Content-Type: multipart/form-data

file: [Excel文件]
```

**响应**:
```json
{
  "code": 200,
  "message": "导入完成：成功50条，失败0条",
  "data": {
    "imported_count": 50,
    "error_count": 0,
    "errors": []
  }
}
```

### 4.3 导出BOM

```bash
GET /api/v1/bom/1/export
```

**响应**: Excel文件流，自动下载

### 4.4 版本对比

```bash
GET /api/v1/bom/1/versions/compare?version1_id=1&version2_id=2
```

**响应**: 对比结果（见1.3节）

## 5. 后续优化建议

1. **导入优化**:
   - 支持追加模式（不清空现有明细）
   - 支持更新模式（根据物料编码更新）
   - 支持批量验证后再导入

2. **导出优化**:
   - 支持导出多个BOM
   - 支持自定义导出字段
   - 支持导出为PDF

3. **版本管理优化**:
   - 支持创建新版本（基于旧版本）
   - 支持版本回滚
   - 支持版本快照（保存完整BOM数据）

4. **性能优化**:
   - 大文件导入时使用流式处理
   - 批量操作时使用批量插入
   - 添加导入进度反馈

5. **数据验证增强**:
   - 支持物料编码自动补全
   - 支持规格型号智能匹配
   - 支持重复物料检测

## 6. 相关文件

- `app/api/v1/endpoints/bom.py` - BOM管理API实现
- `app/models/material.py` - BomHeader, BomItem 模型定义
- `app/schemas/material.py` - BOM相关Schema定义
- `requirements.txt` - 依赖管理（pandas, openpyxl）

## 7. Excel格式说明

### 7.1 导入格式

| 列名 | 类型 | 必需 | 说明 |
|------|------|:----:|------|
| 物料编码 | 文本 | ✅ | 物料编码，如果存在会自动关联物料ID |
| 物料名称 | 文本 | ✅ | 物料名称 |
| 数量 | 数字 | ✅ | 需求数量，必须>0 |
| 规格型号 | 文本 | ❌ | 规格型号 |
| 单位 | 文本 | ❌ | 单位，默认"件" |
| 单价 | 数字 | ❌ | 单价，默认0 |
| 来源类型 | 文本 | ❌ | 来源类型，默认"PURCHASE" |
| 是否关键 | 布尔 | ❌ | 是否关键物料，默认False |
| 备注 | 文本 | ❌ | 备注 |

### 7.2 导出格式

导出文件包含所有BOM明细字段，详见2.2节。



