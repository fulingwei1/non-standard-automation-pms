# 物料与BOM管理 API 实现总结

## 概述

本文档总结了物料主数据和BOM管理功能的 API 实现情况。

## 实现时间

2025-01-XX

## 1. 物料主数据 API (`/api/v1/materials`)

### 已实现的端点

1. **GET `/materials`** - 获取物料列表（支持分页、搜索、筛选）
   - 分页参数：`page`, `page_size`
   - 搜索参数：`keyword`（物料编码/名称）
   - 筛选参数：`category_id`, `material_type`, `is_key_material`, `is_active`
   - 返回：`PaginatedResponse[MaterialResponse]`

2. **GET `/materials/{material_id}`** - 获取物料详情
   - 返回：`MaterialResponse`

3. **POST `/materials`** - 创建物料
   - 请求体：`MaterialCreate`
   - 返回：`MaterialResponse`
   - 特性：
     - ✅ 检查物料编码唯一性
     - ✅ 验证分类存在性
     - ✅ 验证默认供应商存在性
     - ✅ 自动设置创建人

4. **PUT `/materials/{material_id}`** - 更新物料
   - 请求体：`MaterialUpdate`
   - 返回：`MaterialResponse`
   - 特性：
     - ✅ 验证分类和供应商存在性

5. **GET `/materials/categories/`** - 获取物料分类列表
   - 查询参数：`parent_id`（父分类ID，为空则返回顶级分类），`is_active`
   - 返回：`List[MaterialCategoryResponse]`（树形结构）

6. **GET `/materials/{material_id}/suppliers`** - 获取物料的供应商列表
   - 返回：供应商列表（包含价格、交期等信息）

### 特性

- ✅ 分页支持
- ✅ 关键词搜索
- ✅ 多条件筛选
- ✅ 树形分类结构
- ✅ 物料供应商关联查询
- ✅ 认证和权限检查

## 2. BOM 管理 API (`/api/v1/bom`)

### 已实现的端点

1. **GET `/bom/machines/{machine_id}/bom`** - 获取机台的BOM列表
   - 返回：`List[BomResponse]`（包含明细）

2. **POST `/bom/machines/{machine_id}/bom`** - 为机台创建BOM
   - 请求体：`BomCreate`（包含明细列表）
   - 返回：`BomResponse`
   - 特性：
     - ✅ 自动生成BOM编号（BOM-PJxxx-xxx）
     - ✅ 自动计算总金额和物料数量
     - ✅ 验证机台存在性

3. **GET `/bom/{bom_id}`** - 获取BOM详情
   - 返回：`BomResponse`（包含明细列表）

4. **PUT `/bom/{bom_id}`** - 更新BOM
   - 请求体：`BomUpdate`
   - 返回：`BomResponse`
   - 特性：
     - ✅ 只有草稿状态才能更新

5. **GET `/bom/{bom_id}/items`** - 获取BOM明细列表
   - 返回：`List[BomItemResponse]`

6. **POST `/bom/{bom_id}/items`** - 添加BOM明细
   - 请求体：`BomItemCreate`
   - 返回：`BomItemResponse`
   - 特性：
     - ✅ 只有草稿状态才能添加明细
     - ✅ 自动计算行号和金额
     - ✅ 自动更新BOM统计（总金额、物料数量）

7. **PUT `/bom/items/{item_id}`** - 更新BOM明细
   - 请求体：`BomItemCreate`
   - 返回：`BomItemResponse`
   - 特性：
     - ✅ 只有草稿状态才能更新明细
     - ✅ 自动更新BOM总金额

8. **DELETE `/bom/items/{item_id}`** - 删除BOM明细
   - 返回：`ResponseModel`
   - 特性：
     - ✅ 只有草稿状态才能删除明细
     - ✅ 自动更新BOM统计

### 特性

- ✅ BOM编号自动生成
- ✅ 自动计算总金额和物料数量
- ✅ 状态控制（只有草稿状态才能修改）
- ✅ 明细行号自动管理
- ✅ 认证和权限检查

### BOM编号生成规则

格式：`BOM-{项目编码前缀}-{序号}`

例如：
- `BOM-PJ202501-001`
- `BOM-PJ202501-002`

## 3. 待实现功能

### 3.1 BOM版本管理

- **POST `/bom/{bom_id}/release`** - 发布BOM版本
  - 将BOM状态从草稿改为已发布
  - 创建新版本（如果需要）

- **GET `/bom/{bom_id}/versions`** - 获取BOM版本列表
  - 返回所有历史版本

- **GET `/bom/{bom_id}/versions/{version}/compare`** - 版本对比
  - 对比两个版本的差异

### 3.2 BOM导入导出

- **POST `/bom/{bom_id}/import`** - 从Excel导入BOM
  - 支持批量导入BOM明细

- **GET `/bom/{bom_id}/export`** - 导出BOM到Excel
  - 导出BOM明细为Excel文件

- **GET `/bom/template`** - 下载导入模板
  - 下载Excel导入模板

### 3.3 从BOM生成采购需求

- **POST `/bom/{bom_id}/generate-pr`** - 从BOM生成采购需求
  - 根据BOM明细生成采购订单或采购需求

## 4. Schema 定义

### 4.1 Material相关

- `MaterialCreate` - 创建物料
- `MaterialUpdate` - 更新物料
- `MaterialResponse` - 物料响应
- `MaterialCategoryCreate` - 创建分类
- `MaterialCategoryResponse` - 分类响应（支持树形结构）

### 4.2 BOM相关

- `BomCreate` - 创建BOM（包含明细列表）
- `BomUpdate` - 更新BOM
- `BomResponse` - BOM响应（包含明细列表）
- `BomItemCreate` - 创建BOM明细
- `BomItemResponse` - BOM明细响应

## 5. 实现特性

### 5.1 数据验证

- ✅ 物料编码唯一性检查
- ✅ 分类和供应商存在性验证
- ✅ BOM状态控制（只有草稿状态才能修改）
- ✅ 机台存在性验证

### 5.2 自动计算

- ✅ BOM总金额自动计算
- ✅ BOM物料数量自动统计
- ✅ BOM明细行号自动管理
- ✅ BOM编号自动生成

### 5.3 查询优化

- ✅ 分页支持
- ✅ 关键词搜索
- ✅ 多条件筛选
- ✅ 树形分类结构

## 6. 安全特性

- ✅ JWT 认证（所有端点）
- ✅ 用户权限检查
- ✅ 数据验证

## 7. 错误处理

- ✅ 404：物料/BOM/明细不存在
- ✅ 400：物料编码重复、BOM状态不允许操作
- ✅ 401：未认证
- ✅ 403：无权限

## 8. 使用示例

### 8.1 创建物料

```bash
POST /api/v1/materials
Content-Type: application/json

{
  "material_code": "MAT-001",
  "material_name": "螺栓M8x20",
  "category_id": 1,
  "specification": "M8x20",
  "unit": "件",
  "standard_price": 0.5,
  "lead_time_days": 7,
  "is_key_material": false
}
```

### 8.2 创建BOM

```bash
POST /api/v1/bom/machines/1/bom
Content-Type: application/json

{
  "bom_name": "设备1-BOM",
  "version": "1.0",
  "items": [
    {
      "material_id": 1,
      "material_code": "MAT-001",
      "material_name": "螺栓M8x20",
      "quantity": 10,
      "unit_price": 0.5,
      "unit": "件",
      "is_key_item": false
    }
  ]
}
```

### 8.3 添加BOM明细

```bash
POST /api/v1/bom/1/items
Content-Type: application/json

{
  "material_id": 2,
  "material_code": "MAT-002",
  "material_name": "垫圈",
  "quantity": 10,
  "unit_price": 0.1,
  "unit": "件"
}
```

## 9. 后续优化建议

1. **BOM版本管理**:
   - 实现版本发布功能
   - 版本历史记录
   - 版本对比功能

2. **BOM导入导出**:
   - Excel导入功能
   - Excel导出功能
   - 导入模板下载

3. **从BOM生成采购需求**:
   - 根据BOM明细自动生成采购订单
   - 支持批量生成

4. **物料替代关系**:
   - 物料替代关系管理
   - 替代物料推荐

5. **齐套率计算**:
   - 基于BOM的齐套率计算
   - 缺料清单生成

6. **批量操作**:
   - 批量添加BOM明细
   - 批量更新BOM明细

## 10. 相关文件

- `app/api/v1/endpoints/materials.py` - 物料管理API实现
- `app/api/v1/endpoints/bom.py` - BOM管理API实现
- `app/models/material.py` - 物料和BOM模型定义
- `app/schemas/material.py` - 物料和BOM相关Schema定义
- `app/api/v1/api.py` - API路由注册



