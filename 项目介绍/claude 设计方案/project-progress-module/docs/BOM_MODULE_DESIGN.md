# BOM管理模块详细设计

## 一、模块概述

### 1.1 模块定位

BOM（Bill of Materials，物料清单）管理是非标自动化项目管理的核心模块，直接关系到：
- **缺料问题**：BOM不准确或发布晚是缺料的根源
- **成本控制**：BOM是成本预算的基础
- **采购协同**：BOM驱动采购需求
- **变更管理**：ECN变更的核心对象

### 1.2 核心功能

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BOM管理模块功能架构                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │    BOM创建      │  │    BOM导入      │  │    BOM版本      │             │
│  │                 │  │                 │  │                 │             │
│  │ • 手工录入      │  │ • Excel导入     │  │ • 版本发布      │             │
│  │ • 物料选择      │  │ • 模板下载      │  │ • 版本对比      │             │
│  │ • 批量添加      │  │ • 数据校验      │  │ • 历史追溯      │             │
│  │ • 机台分组      │  │ • 错误提示      │  │ • 版本回退      │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │    齐套分析      │  │    采购联动     │  │    BOM导出      │             │
│  │                 │  │                 │  │                 │             │
│  │ • 齐套率计算    │  │ • 生成采购需求  │  │ • Excel导出     │             │
│  │ • 缺料清单      │  │ • 订单关联      │  │ • 按类别导出    │             │
│  │ • 到货状态      │  │ • 到货更新      │  │ • 打印清单      │             │
│  │ • 预警提示      │  │ • 缺料预警      │  │ • 自定义格式    │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 业务流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BOM管理业务流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  设计完成 ──→ 创建BOM ──→ 评审确认 ──→ 版本发布 ──→ 采购需求                │
│     │           │           │           │           │                      │
│     ▼           ▼           ▼           ▼           ▼                      │
│  [设计图纸]  [录入物料]  [技术评审]  [V1.0发布]  [生成需求]                  │
│             [Excel导入]  [成本核算]  [通知采购]  [采购下单]                  │
│                                                                             │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────┐                                      │
│                    │    设计变更?     │                                      │
│                    └────────┬────────┘                                      │
│                        是 │    │ 否                                         │
│                           ▼    └──→ [齐套跟踪] ──→ [装配生产]               │
│                    ┌─────────────────┐                                      │
│                    │   创建ECN变更   │                                      │
│                    │   更新BOM版本   │                                      │
│                    │   调整采购订单  │                                      │
│                    └─────────────────┘                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、数据模型设计

### 2.1 实体关系

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   project    │ 1:N  │  bom_header  │ 1:N  │   bom_item   │
│   项目表     │─────→│  BOM头表     │─────→│  BOM明细表   │
└──────────────┘      └──────────────┘      └──────────────┘
                             │                     │
                             │ 1:N                 │ N:1
                             ▼                     ▼
                      ┌──────────────┐      ┌──────────────┐
                      │ bom_version  │      │   material   │
                      │  版本记录    │      │   物料表     │
                      └──────────────┘      └──────────────┘
```

### 2.2 表结构定义

#### 2.2.1 BOM头表 (bom_header)

```sql
CREATE TABLE `bom_header` (
    `bom_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'BOM ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `machine_no` VARCHAR(30) NOT NULL COMMENT '机台号',
    `machine_name` VARCHAR(100) NULL COMMENT '机台名称',
    `bom_type` VARCHAR(20) DEFAULT '整机' COMMENT 'BOM类型：整机/模块/备件',
    `current_version` VARCHAR(10) DEFAULT 'V1.0' COMMENT '当前版本',
    `status` VARCHAR(20) DEFAULT '草稿' COMMENT '状态：草稿/评审中/已发布/已冻结',
    `total_items` INT DEFAULT 0 COMMENT '物料总数',
    `total_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '预估总成本',
    `kit_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '齐套率%',
    `designer_id` BIGINT NOT NULL COMMENT '设计人ID',
    `designer_name` VARCHAR(50) NOT NULL COMMENT '设计人',
    `reviewer_id` BIGINT NULL COMMENT '审核人ID',
    `reviewer_name` VARCHAR(50) NULL COMMENT '审核人',
    `review_time` DATETIME NULL COMMENT '审核时间',
    `publish_time` DATETIME NULL COMMENT '发布时间',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`bom_id`),
    UNIQUE KEY `uk_project_machine` (`project_id`, `machine_no`),
    KEY `idx_bom_project` (`project_id`),
    KEY `idx_bom_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='BOM头表';
```

#### 2.2.2 BOM明细表 (bom_item)

```sql
CREATE TABLE `bom_item` (
    `item_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '明细ID',
    `bom_id` BIGINT NOT NULL COMMENT 'BOM ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `line_no` INT NOT NULL COMMENT '行号',
    `material_id` BIGINT NULL COMMENT '物料ID（标准物料）',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `category` VARCHAR(30) NOT NULL COMMENT '物料类别：ME/EL/PN/ST/OT/TR',
    `category_name` VARCHAR(50) NULL COMMENT '类别名称',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `quantity` DECIMAL(10,2) NOT NULL COMMENT '需求数量',
    `unit_price` DECIMAL(12,2) NULL COMMENT '单价',
    `amount` DECIMAL(12,2) NULL COMMENT '金额',
    `supplier_id` BIGINT NULL COMMENT '供应商ID',
    `supplier_name` VARCHAR(100) NULL COMMENT '供应商名称',
    `lead_time` INT NULL COMMENT '采购周期(天)',
    `is_long_lead` TINYINT DEFAULT 0 COMMENT '是否长周期',
    `is_key_part` TINYINT DEFAULT 0 COMMENT '是否关键件',
    `required_date` DATE NULL COMMENT '需求日期',
    `ordered_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '已下单数量',
    `received_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '已到货数量',
    `stock_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '库存可用',
    `shortage_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '缺料数量',
    `procurement_status` VARCHAR(20) DEFAULT '待采购' COMMENT '采购状态',
    `drawing_no` VARCHAR(50) NULL COMMENT '图纸号',
    `position_no` VARCHAR(50) NULL COMMENT '位置号',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `version` VARCHAR(10) DEFAULT 'V1.0' COMMENT '版本',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`item_id`),
    KEY `idx_item_bom` (`bom_id`),
    KEY `idx_item_project` (`project_id`),
    KEY `idx_item_material` (`material_id`),
    KEY `idx_item_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='BOM明细表';
```

#### 2.2.3 BOM版本表 (bom_version)

```sql
CREATE TABLE `bom_version` (
    `version_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '版本ID',
    `bom_id` BIGINT NOT NULL COMMENT 'BOM ID',
    `version` VARCHAR(10) NOT NULL COMMENT '版本号',
    `version_type` VARCHAR(20) NOT NULL COMMENT '版本类型：初始/变更/修订',
    `ecn_id` BIGINT NULL COMMENT '关联ECN ID',
    `ecn_code` VARCHAR(30) NULL COMMENT 'ECN编号',
    `change_summary` VARCHAR(500) NULL COMMENT '变更摘要',
    `total_items` INT DEFAULT 0 COMMENT '物料总数',
    `total_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '版本成本',
    `snapshot_data` LONGTEXT NULL COMMENT 'BOM快照JSON',
    `published_by` BIGINT NOT NULL COMMENT '发布人ID',
    `published_name` VARCHAR(50) NOT NULL COMMENT '发布人',
    `published_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    PRIMARY KEY (`version_id`),
    UNIQUE KEY `uk_bom_version` (`bom_id`, `version`),
    KEY `idx_version_bom` (`bom_id`),
    KEY `idx_version_ecn` (`ecn_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='BOM版本表';
```

#### 2.2.4 物料主数据表 (material)

```sql
CREATE TABLE `material` (
    `material_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '物料ID',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `brand` VARCHAR(50) NULL COMMENT '品牌',
    `category` VARCHAR(20) NOT NULL COMMENT '大类：ME/EL/PN/ST/OT/TR',
    `sub_category` VARCHAR(50) NULL COMMENT '子类别',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `reference_price` DECIMAL(12,2) NULL COMMENT '参考单价',
    `default_supplier_id` BIGINT NULL COMMENT '默认供应商ID',
    `default_supplier_name` VARCHAR(100) NULL COMMENT '默认供应商',
    `lead_time` INT DEFAULT 7 COMMENT '标准采购周期(天)',
    `min_order_qty` DECIMAL(10,2) DEFAULT 1 COMMENT '最小起订量',
    `is_standard` TINYINT DEFAULT 0 COMMENT '是否标准件',
    `status` VARCHAR(20) DEFAULT '启用' COMMENT '状态',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`material_id`),
    UNIQUE KEY `uk_material_code` (`material_code`),
    KEY `idx_material_category` (`category`),
    KEY `idx_material_name` (`material_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物料主数据表';
```

---

## 三、API接口设计

### 3.1 接口清单

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/bom/projects/{project_id} | 获取项目所有BOM |
| GET | /api/v1/bom/{bom_id} | 获取BOM详情 |
| POST | /api/v1/bom | 创建BOM |
| PUT | /api/v1/bom/{bom_id} | 更新BOM |
| DELETE | /api/v1/bom/{bom_id} | 删除BOM |
| GET | /api/v1/bom/{bom_id}/items | 获取BOM物料清单 |
| POST | /api/v1/bom/{bom_id}/items | 添加BOM物料 |
| PUT | /api/v1/bom/items/{item_id} | 更新BOM物料 |
| DELETE | /api/v1/bom/items/{item_id} | 删除BOM物料 |
| POST | /api/v1/bom/{bom_id}/items/batch | 批量添加物料 |
| POST | /api/v1/bom/{bom_id}/import | 导入Excel |
| GET | /api/v1/bom/{bom_id}/export | 导出Excel |
| GET | /api/v1/bom/template | 下载导入模板 |
| POST | /api/v1/bom/{bom_id}/publish | 发布BOM版本 |
| GET | /api/v1/bom/{bom_id}/versions | 获取版本列表 |
| GET | /api/v1/bom/{bom_id}/versions/{version}/compare | 版本对比 |
| GET | /api/v1/bom/{bom_id}/kit-status | 齐套状态 |
| GET | /api/v1/bom/{bom_id}/shortage | 缺料清单 |
| POST | /api/v1/bom/{bom_id}/generate-pr | 生成采购需求 |
| GET | /api/v1/materials | 物料列表（选择器用） |
| POST | /api/v1/materials | 新增物料 |

### 3.2 接口详细定义

#### 3.2.1 获取项目BOM列表

```yaml
GET /api/v1/bom/projects/{project_id}

Response:
{
    "code": 200,
    "data": {
        "project_id": 1,
        "project_code": "PJ250708001",
        "project_name": "某客户自动化测试设备",
        "machines": [
            {
                "bom_id": 1,
                "machine_no": "PJ250708001-PN001",
                "machine_name": "1号机台",
                "bom_type": "整机",
                "current_version": "V1.0",
                "status": "已发布",
                "total_items": 150,
                "total_cost": 125000.00,
                "kit_rate": 85.5,
                "designer_name": "张工",
                "publish_time": "2025-01-10 10:00:00"
            }
        ],
        "summary": {
            "total_machines": 3,
            "total_items": 450,
            "total_cost": 375000.00,
            "avg_kit_rate": 82.3
        }
    }
}
```

#### 3.2.2 获取BOM详情

```yaml
GET /api/v1/bom/{bom_id}

Response:
{
    "code": 200,
    "data": {
        "bom_id": 1,
        "project_id": 1,
        "project_code": "PJ250708001",
        "machine_no": "PJ250708001-PN001",
        "machine_name": "1号机台",
        "bom_type": "整机",
        "current_version": "V1.0",
        "status": "已发布",
        "total_items": 150,
        "total_cost": 125000.00,
        "kit_rate": 85.5,
        "designer_id": 1,
        "designer_name": "张工",
        "reviewer_name": "李经理",
        "review_time": "2025-01-09",
        "publish_time": "2025-01-10",
        "category_summary": [
            {"category": "ME", "category_name": "机械件", "count": 50, "cost": 45000},
            {"category": "EL", "category_name": "电气件", "count": 60, "cost": 55000},
            {"category": "PN", "category_name": "气动件", "count": 20, "cost": 15000},
            {"category": "ST", "category_name": "标准件", "count": 15, "cost": 8000},
            {"category": "OT", "category_name": "外协件", "count": 5, "cost": 2000}
        ],
        "kit_status": {
            "total": 150,
            "arrived": 128,
            "ordered": 15,
            "pending": 7,
            "kit_rate": 85.5
        }
    }
}
```

#### 3.2.3 获取BOM物料清单

```yaml
GET /api/v1/bom/{bom_id}/items
Query:
  - category: 物料类别筛选
  - status: 采购状态筛选
  - keyword: 关键字搜索
  - page: 页码
  - size: 每页数量

Response:
{
    "code": 200,
    "data": {
        "total": 150,
        "items": [
            {
                "item_id": 1,
                "line_no": 1,
                "material_code": "EL-02-03-0015-0001",
                "material_name": "光电传感器",
                "specification": "E3Z-D62 2M",
                "brand": "OMRON",
                "category": "EL",
                "category_name": "电气件",
                "unit": "pcs",
                "quantity": 10,
                "unit_price": 150.00,
                "amount": 1500.00,
                "supplier_name": "欧姆龙代理商",
                "lead_time": 7,
                "is_long_lead": false,
                "is_key_part": true,
                "required_date": "2025-01-20",
                "ordered_qty": 10,
                "received_qty": 8,
                "shortage_qty": 2,
                "procurement_status": "部分到货",
                "drawing_no": "E-001",
                "position_no": "ST1-1"
            }
        ]
    }
}
```

#### 3.2.4 添加BOM物料

```yaml
POST /api/v1/bom/{bom_id}/items

Request:
{
    "material_id": 100,  // 可选，选择已有物料
    "material_code": "EL-02-03-0015-0001",
    "material_name": "光电传感器",
    "specification": "E3Z-D62 2M",
    "category": "EL",
    "unit": "pcs",
    "quantity": 10,
    "unit_price": 150.00,
    "supplier_id": 5,
    "lead_time": 7,
    "is_key_part": true,
    "required_date": "2025-01-20",
    "drawing_no": "E-001",
    "position_no": "ST1-1",
    "remark": ""
}

Response:
{
    "code": 200,
    "message": "添加成功",
    "data": {
        "item_id": 151
    }
}
```

#### 3.2.5 批量添加物料

```yaml
POST /api/v1/bom/{bom_id}/items/batch

Request:
{
    "items": [
        {
            "material_code": "EL-02-03-0015-0001",
            "material_name": "光电传感器",
            "specification": "E3Z-D62 2M",
            "category": "EL",
            "quantity": 10,
            "unit_price": 150.00
        },
        {
            "material_code": "ME-01-02-0001-0001",
            "material_name": "导轨",
            "specification": "HGR20-500L",
            "category": "ME",
            "quantity": 4,
            "unit_price": 280.00
        }
    ]
}

Response:
{
    "code": 200,
    "message": "批量添加成功",
    "data": {
        "success_count": 2,
        "fail_count": 0,
        "items": [...]
    }
}
```

#### 3.2.6 导入Excel

```yaml
POST /api/v1/bom/{bom_id}/import
Content-Type: multipart/form-data

Request:
  - file: Excel文件
  - mode: append/replace (追加/替换)

Response:
{
    "code": 200,
    "message": "导入成功",
    "data": {
        "total_rows": 150,
        "success_count": 148,
        "fail_count": 2,
        "errors": [
            {"row": 25, "error": "物料编码格式不正确"},
            {"row": 67, "error": "数量必须大于0"}
        ]
    }
}
```

#### 3.2.7 发布BOM版本

```yaml
POST /api/v1/bom/{bom_id}/publish

Request:
{
    "version": "V1.0",  // 可选，自动递增
    "version_type": "初始",  // 初始/变更/修订
    "ecn_id": null,  // 关联ECN
    "change_summary": "初始版本发布",
    "notify_users": [10, 11, 12]  // 通知人员
}

Response:
{
    "code": 200,
    "message": "发布成功",
    "data": {
        "version_id": 1,
        "version": "V1.0",
        "published_time": "2025-01-10 10:00:00"
    }
}
```

#### 3.2.8 齐套状态

```yaml
GET /api/v1/bom/{bom_id}/kit-status

Response:
{
    "code": 200,
    "data": {
        "bom_id": 1,
        "machine_no": "PJ250708001-PN001",
        "kit_rate": 85.5,
        "summary": {
            "total": 150,
            "arrived": 128,
            "partial": 12,
            "ordered": 5,
            "pending": 5
        },
        "by_category": [
            {"category": "ME", "name": "机械件", "total": 50, "arrived": 45, "rate": 90.0},
            {"category": "EL", "name": "电气件", "total": 60, "arrived": 48, "rate": 80.0},
            {"category": "PN", "name": "气动件", "total": 20, "arrived": 18, "rate": 90.0},
            {"category": "ST", "name": "标准件", "total": 15, "arrived": 15, "rate": 100.0},
            {"category": "OT", "name": "外协件", "total": 5, "arrived": 2, "rate": 40.0}
        ],
        "shortage_items": [
            {
                "item_id": 15,
                "material_code": "EL-02-03-0015-0001",
                "material_name": "光电传感器",
                "quantity": 10,
                "received_qty": 8,
                "shortage_qty": 2,
                "expect_date": "2025-01-15",
                "impact_date": "2025-01-18",
                "alert_level": "黄"
            }
        ]
    }
}
```

#### 3.2.9 生成采购需求

```yaml
POST /api/v1/bom/{bom_id}/generate-pr

Request:
{
    "items": [1, 2, 3],  // 可选，指定物料ID；为空则全部
    "exclude_stocked": true,  // 排除有库存的
    "group_by_supplier": true  // 按供应商分组
}

Response:
{
    "code": 200,
    "message": "采购需求已生成",
    "data": {
        "pr_count": 3,
        "purchase_requests": [
            {
                "pr_id": 101,
                "supplier_id": 5,
                "supplier_name": "欧姆龙代理商",
                "item_count": 15,
                "total_amount": 25000.00
            }
        ]
    }
}
```

---

## 四、前端页面设计

### 4.1 页面结构

```
views/bom/
├── BomList.vue           # 项目BOM列表
├── BomDetail.vue         # BOM详情（物料清单）
├── BomEditor.vue         # BOM编辑器
├── BomImport.vue         # Excel导入
├── BomVersions.vue       # 版本管理
├── BomCompare.vue        # 版本对比
├── KitStatus.vue         # 齐套状态
└── components/
    ├── MaterialSelector.vue  # 物料选择器
    ├── BomTable.vue          # BOM表格
    ├── CategoryPie.vue       # 类别饼图
    └── KitProgress.vue       # 齐套进度条
```

### 4.2 页面原型

#### 4.2.1 项目BOM列表

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  项目: PJ250708001 - 某客户自动化测试设备                    [返回项目]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │  物料总数    │  │  预估成本    │  │  平均齐套率  │   [+ 新增BOM]          │
│  │    450      │  │  ¥375,000   │  │   82.3%     │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 机台号           │ 名称     │ 版本  │ 状态   │ 物料数│ 齐套率 │ 操作 │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ PJ250708001-PN001│ 1号机台  │ V1.2  │ 已发布 │  150  │ 85.5% │ ··· │   │
│  │ PJ250708001-PN002│ 2号机台  │ V1.0  │ 已发布 │  150  │ 78.0% │ ··· │   │
│  │ PJ250708001-PN003│ 3号机台  │ V1.0  │ 草稿   │  150  │ --    │ ··· │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.2.2 BOM详情/编辑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BOM: PJ250708001-PN001 - 1号机台                                           │
│  版本: V1.2 | 状态: 已发布 | 设计: 张工 | 发布: 2025-01-10                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [+ 添加物料] [批量添加] [导入Excel] [导出] [发布版本] [版本历史] [齐套状态] │
│                                                                             │
│  ┌──────────────────────────────┐  ┌────────────────────────────────────┐  │
│  │       物料类别分布            │  │         齐套状态                   │  │
│  │                              │  │                                    │  │
│  │   [饼图]                     │  │  ████████████████░░░░ 85.5%        │  │
│  │   ME 机械件: 50 (33%)        │  │  到货: 128 | 在途: 15 | 待采: 7    │  │
│  │   EL 电气件: 60 (40%)        │  │                                    │  │
│  │   PN 气动件: 20 (13%)        │  │  缺料物料: 5项 [查看详情]          │  │
│  │   其他: 20 (14%)             │  │                                    │  │
│  └──────────────────────────────┘  └────────────────────────────────────┘  │
│                                                                             │
│  筛选: [全部类别▼] [全部状态▼] [搜索物料...]           显示: 150 条         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ □ │行号│物料编码        │物料名称    │规格型号      │类别│数量│单价  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ □ │ 1 │EL-02-03-0015  │光电传感器  │E3Z-D62 2M   │电气│ 10 │150  │   │
│  │ □ │ 2 │ME-01-02-0001  │导轨        │HGR20-500L   │机械│  4 │280  │   │
│  │ □ │ 3 │PN-01-01-0005  │气缸        │CDQ2A32-50D  │气动│  6 │320  │   │
│  │ □ │ 4 │ST-01-01-0100  │螺丝        │M6x20        │标准│100 │0.5  │   │
│  │ ... │                                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                         1 / 8 页 [<] [>]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.2.3 物料选择器（弹窗）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  选择物料                                                          [×]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [类别] 全部▼  [品牌]▼  搜索: [________________] [搜索]                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ □ │物料编码        │物料名称      │规格型号      │品牌   │参考价    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ ☑ │EL-02-03-0015  │光电传感器    │E3Z-D62 2M   │OMRON │¥150     │   │
│  │ □ │EL-02-03-0016  │光电传感器    │E3Z-D81 2M   │OMRON │¥180     │   │
│  │ □ │EL-02-03-0017  │光纤传感器    │E32-DC200    │OMRON │¥220     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  已选择: 1 项                                                               │
│                                                                             │
│  [+ 新建物料]                                      [取消]  [确认添加]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4.2.4 Excel导入

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  导入BOM                                                           [×]      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 下载导入模板                                                            │
│     [下载Excel模板]                                                         │
│                                                                             │
│  2. 上传文件                                                                │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │                                                                 │    │
│     │         将Excel文件拖拽到此处，或 [点击上传]                     │    │
│     │                                                                 │    │
│     │         支持 .xlsx, .xls 格式，最大 10MB                        │    │
│     │                                                                 │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  3. 导入选项                                                                │
│     ○ 追加模式（保留现有数据，添加新数据）                                  │
│     ● 替换模式（清空现有数据，导入新数据）                                  │
│                                                                             │
│  4. 数据预览                                                                │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ 行号│物料编码      │物料名称    │数量│校验结果                   │    │
│     ├─────────────────────────────────────────────────────────────────┤    │
│     │  1 │EL-02-03-0015│光电传感器  │ 10 │ ✓ 通过                    │    │
│     │  2 │ME-01-02-0001│导轨        │  4 │ ✓ 通过                    │    │
│     │  3 │XX-00-00-0000│测试物料    │  1 │ ✗ 物料编码格式错误        │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  校验结果: 148 行通过, 2 行错误                                             │
│                                                                             │
│                                                      [取消]  [确认导入]     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 五、核心业务逻辑

### 5.1 齐套率计算

```python
def calculate_kit_rate(bom_id: int) -> dict:
    """
    计算BOM齐套率

    齐套率 = 已到货物料数 / BOM物料总数 × 100%

    物料到货状态判定：
    - 已到货：received_qty >= quantity
    - 部分到货：0 < received_qty < quantity
    - 未到货：received_qty = 0
    """
    items = get_bom_items(bom_id)

    total = len(items)
    arrived = 0
    partial = 0

    for item in items:
        if item.received_qty >= item.quantity:
            arrived += 1
        elif item.received_qty > 0:
            partial += 1

    kit_rate = (arrived / total * 100) if total > 0 else 0

    return {
        "total": total,
        "arrived": arrived,
        "partial": partial,
        "pending": total - arrived - partial,
        "kit_rate": round(kit_rate, 2)
    }
```

### 5.2 缺料预警检查

```python
def check_shortage_alert(bom_id: int) -> list:
    """
    检查缺料预警

    预警条件：
    - 红灯：预计到货日 > 需求日期 且 需求日期 <= 今天 + 3天
    - 黄灯：预计到货日 > 需求日期 且 需求日期 <= 今天 + 7天
    - 绿灯：其他
    """
    items = get_shortage_items(bom_id)
    alerts = []

    today = date.today()

    for item in items:
        if item.shortage_qty <= 0:
            continue

        # 获取预计到货日
        expect_date = get_expect_delivery_date(item)
        required_date = item.required_date

        if not required_date:
            continue

        days_to_required = (required_date - today).days

        if expect_date and expect_date > required_date:
            if days_to_required <= 3:
                alert_level = "红"
            elif days_to_required <= 7:
                alert_level = "黄"
            else:
                alert_level = "绿"

            alerts.append({
                "item_id": item.item_id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "shortage_qty": item.shortage_qty,
                "required_date": required_date,
                "expect_date": expect_date,
                "delay_days": (expect_date - required_date).days,
                "alert_level": alert_level
            })

    return alerts
```

### 5.3 版本发布逻辑

```python
def publish_bom_version(bom_id: int, data: dict, user_id: int) -> dict:
    """
    发布BOM版本

    流程：
    1. 校验BOM状态
    2. 生成版本号
    3. 创建版本快照
    4. 更新BOM状态
    5. 通知相关人员
    """
    bom = get_bom(bom_id)

    # 1. 校验状态
    if bom.status not in ["草稿", "已发布"]:
        raise BusinessError("当前状态不允许发布")

    # 2. 生成版本号
    if data.get("version"):
        new_version = data["version"]
    else:
        new_version = generate_next_version(bom.current_version)

    # 3. 创建版本快照
    snapshot = create_bom_snapshot(bom_id)

    version_record = BomVersion(
        bom_id=bom_id,
        version=new_version,
        version_type=data.get("version_type", "初始"),
        ecn_id=data.get("ecn_id"),
        change_summary=data.get("change_summary"),
        total_items=bom.total_items,
        total_cost=bom.total_cost,
        snapshot_data=json.dumps(snapshot),
        published_by=user_id,
        published_name=get_user_name(user_id)
    )
    save(version_record)

    # 4. 更新BOM状态
    bom.current_version = new_version
    bom.status = "已发布"
    bom.publish_time = datetime.now()
    save(bom)

    # 5. 通知相关人员
    if data.get("notify_users"):
        send_notification(
            users=data["notify_users"],
            title=f"BOM发布通知",
            content=f"{bom.machine_no} BOM {new_version} 已发布"
        )

    return {
        "version_id": version_record.version_id,
        "version": new_version
    }
```

### 5.4 Excel导入逻辑

```python
def import_bom_excel(bom_id: int, file: UploadFile, mode: str) -> dict:
    """
    导入Excel

    流程：
    1. 解析Excel文件
    2. 数据校验
    3. 物料匹配（已有物料自动关联）
    4. 批量插入/更新
    """
    # 1. 解析Excel
    df = pd.read_excel(file.file)

    # 必填列校验
    required_columns = ["物料编码", "物料名称", "类别", "数量"]
    for col in required_columns:
        if col not in df.columns:
            raise BusinessError(f"缺少必填列: {col}")

    # 2. 数据校验
    errors = []
    valid_items = []

    for idx, row in df.iterrows():
        line_no = idx + 2  # Excel行号从2开始

        # 校验物料编码格式
        if not validate_material_code(row["物料编码"]):
            errors.append({"row": line_no, "error": "物料编码格式不正确"})
            continue

        # 校验数量
        if not row["数量"] or row["数量"] <= 0:
            errors.append({"row": line_no, "error": "数量必须大于0"})
            continue

        # 尝试匹配已有物料
        material = find_material_by_code(row["物料编码"])

        valid_items.append({
            "material_id": material.material_id if material else None,
            "material_code": row["物料编码"],
            "material_name": row["物料名称"],
            "specification": row.get("规格型号", ""),
            "category": row["类别"],
            "unit": row.get("单位", "pcs"),
            "quantity": row["数量"],
            "unit_price": row.get("单价", 0),
            "supplier_name": row.get("供应商", ""),
            "lead_time": row.get("采购周期", 7),
            "remark": row.get("备注", "")
        })

    # 3. 批量操作
    if mode == "replace":
        delete_bom_items(bom_id)

    for idx, item_data in enumerate(valid_items):
        item_data["bom_id"] = bom_id
        item_data["line_no"] = idx + 1
        create_bom_item(item_data)

    # 4. 更新BOM汇总
    update_bom_summary(bom_id)

    return {
        "total_rows": len(df),
        "success_count": len(valid_items),
        "fail_count": len(errors),
        "errors": errors
    }
```

---

## 六、与其他模块的集成

### 6.1 与采购模块集成

```
BOM发布 ──→ 生成采购需求 ──→ 采购下单 ──→ 到货登记 ──→ 更新BOM到货状态
                                              │
                                              ▼
                                      更新齐套率、触发预警
```

### 6.2 与ECN变更模块集成

```
ECN变更申请 ──→ BOM变更明细 ──→ ECN审批 ──→ 执行变更 ──→ 更新BOM版本
                                              │
                                              ▼
                                      调整采购订单、通知相关人员
```

### 6.3 与项目管理集成

```
项目创建 ──→ 创建机台 ──→ 创建BOM ──→ BOM发布 ──→ 项目进入采购阶段
                                         │
                                         ▼
                                   更新项目物料状态
```

---

## 七、性能考虑

### 7.1 大数据量优化

- BOM物料分页查询，每页50条
- 使用索引优化查询：project_id, category, material_code
- 齐套率定时计算，缓存结果

### 7.2 并发控制

- BOM编辑时加乐观锁
- 版本发布时加分布式锁

### 7.3 缓存策略

- 物料主数据缓存（Redis）
- BOM齐套率缓存，5分钟过期

---

*文档版本：V1.0*
*编制日期：2025年1月*
