# 电气工程师绩效评价体系设计

## 一、岗位特点分析

### 1.1 工作职责

| 职责领域 | 具体内容 |
|---------|---------|
| **电气设计** | 电气原理图设计、电气柜布局、线缆规格选型 |
| **PLC编程** | PLC程序开发、HMI界面设计、运动控制程序 |
| **选型配置** | 电气元器件选型、BOM编制、成本控制 |
| **现场调试** | 电气接线指导、程序调试、故障排查 |
| **技术支持** | 客户培训、远程支持、售后服务 |

### 1.2 技术栈要求

```
┌─────────────────────────────────────────────────────────────────┐
│                    电气工程师技术栈                               │
├─────────────────────────────────────────────────────────────────┤
│  设计工具                                                        │
│  ├─ EPLAN：电气原理图、端子图、线缆清单                          │
│  ├─ AutoCAD Electrical：电气图纸设计                            │
│  └─ Visio/亿图：电气柜布局图                                     │
│                                                                  │
│  PLC编程                                                         │
│  ├─ 西门子：TIA Portal、STEP 7、WinCC                           │
│  ├─ 三菱：GX Works、GT Designer                                 │
│  ├─ 欧姆龙：CX-Programmer、NB-Designer                          │
│  └─ 倍福：TwinCAT                                               │
│                                                                  │
│  运动控制                                                        │
│  ├─ 伺服驱动：参数调试、定位控制                                 │
│  ├─ 步进控制：脉冲控制、细分设置                                 │
│  └─ 机器人：ABB/KUKA/FANUC编程                                  │
│                                                                  │
│  通讯协议                                                        │
│  ├─ 现场总线：Profinet、EtherCAT、Modbus                        │
│  ├─ 串口通讯：RS232/RS485                                       │
│  └─ 工业以太网：OPC UA、MQTT                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、评价维度设计

### 2.1 五维评价体系

```
                        电气工程师评价维度
                              │
        ┌─────────┬─────────┼─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼
    ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
    │技术能力│ │项目执行│ │成本控制│ │知识沉淀│ │团队协作│
    │ 30%   │ │ 25%   │ │ 20%   │ │ 15%   │ │ 10%   │
    └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
        │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼
    设计一次通过  按时完成率  标准件使用  程序模块库  跨部门配合
    PLC程序质量  现场响应    选型准确率  技术文档    机械配合度
    调试效率    图纸交付    成本节约    技术分享    测试配合度
```

### 2.2 指标详细定义

#### 技术能力（权重30%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **图纸一次通过率** | 电气图纸首次审核通过比例 | 一次通过数 / 总提交数 × 100% | ≥85% |
| **PLC程序质量** | 程序首次调试成功率 | 一次调通数 / 总程序数 × 100% | ≥80% |
| **电气故障率** | 交付后电气相关故障 | 故障次数 / 交付项目数 | ≤0.2次/项目 |
| **调试效率** | 实际调试时间 vs 计划时间 | 计划时间 / 实际时间 × 100% | ≥90% |

#### 项目执行（权重25%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **任务按时完成率** | 在计划时间内完成任务比例 | 按时完成数 / 总任务数 × 100% | ≥90% |
| **图纸交付及时性** | 电气图纸按时提交率 | 按时交付数 / 总图纸数 × 100% | ≥95% |
| **现场响应速度** | 现场问题响应时间 | 4小时内响应率 | ≥90% |
| **设计变更响应** | ECN响应处理时间 | 平均响应时长 | ≤8小时 |

#### 成本控制（权重20%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **标准件使用率** | 使用标准型号元器件比例 | 标准件数 / 总元器件数 × 100% | ≥70% |
| **选型准确率** | 元器件选型无需更换比例 | 正确选型数 / 总选型数 × 100% | ≥95% |
| **成本节约贡献** | 优化设计降低成本 | 节约金额 / 原预算 × 100% | 记录统计 |
| **库存件优先使用** | 优先使用库存元器件 | 库存件使用数 / 可替代件数 | ≥60% |

#### 知识沉淀（权重15%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **PLC程序模块贡献** | 贡献到公共程序库的模块 | 模块数量 | ≥2个/季度 |
| **标准图纸模板** | 贡献标准化图纸模板 | 模板数量 | ≥1个/季度 |
| **技术文档** | 编写技术规范、操作手册 | 文档数量 | ≥2篇/季度 |
| **被复用次数** | 模块/模板被其他项目复用 | 复用次数 | 记录统计 |

#### 团队协作（权重10%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **机械配合评分** | 机械部门的协作评价 | 评分（1-5） | ≥4.0 |
| **测试配合评分** | 测试部门的协作评价 | 评分（1-5） | ≥4.0 |
| **接口文档完整性** | 提供给其他部门的接口说明 | 完整性评分 | ≥90% |
| **新人带教** | 指导新人效果 | 带教人数 × 效果系数 | 记录统计 |

---

## 三、数据库设计

### 3.1 电气任务扩展表

```sql
-- 在现有任务表基础上，为电气任务补充专用字段
ALTER TABLE project_task 
ADD COLUMN drawing_type ENUM('原理图','布局图','接线图','BOM','PLC程序','HMI') COMMENT '图纸/程序类型',
ADD COLUMN review_status ENUM('待审核','审核通过','需修改','重新提交') COMMENT '审核状态',
ADD COLUMN review_pass_first TINYINT(1) COMMENT '是否一次审核通过',
ADD COLUMN review_count INT DEFAULT 0 COMMENT '审核次数',
ADD COLUMN plc_brand VARCHAR(50) COMMENT 'PLC品牌(西门子/三菱/欧姆龙等)',
ADD COLUMN program_lines INT COMMENT 'PLC程序行数/步数',
ADD COLUMN io_points INT COMMENT 'IO点数';
```

### 3.2 电气图纸版本表

```sql
CREATE TABLE electrical_drawing_version (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    drawing_no VARCHAR(50) NOT NULL COMMENT '图纸编号',
    drawing_name VARCHAR(200) NOT NULL COMMENT '图纸名称',
    
    -- 图纸类型
    drawing_type ENUM('电气原理图','电气布局图','接线图','端子图','线缆清单','PLC程序','HMI画面') NOT NULL,
    
    -- 版本信息
    version VARCHAR(20) NOT NULL COMMENT '版本号',
    version_type ENUM('initial','revision','ecn') COMMENT '版本类型',
    
    -- 设计者信息
    designer_id BIGINT NOT NULL COMMENT '设计者ID',
    designer_name VARCHAR(50) COMMENT '设计者姓名',
    
    -- 审核信息
    reviewer_id BIGINT COMMENT '审核人ID',
    review_status ENUM('pending','approved','rejected') DEFAULT 'pending',
    review_pass_first BOOLEAN COMMENT '一次通过',
    review_count INT DEFAULT 0 COMMENT '审核次数',
    review_comments TEXT COMMENT '审核意见',
    review_time DATETIME COMMENT '审核时间',
    
    -- 图纸统计
    page_count INT COMMENT '页数',
    component_count INT COMMENT '元器件数量',
    
    -- 时间
    planned_date DATE COMMENT '计划完成日期',
    submit_date DATE COMMENT '实际提交日期',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_designer (designer_id),
    INDEX idx_drawing_no (drawing_no)
) COMMENT '电气图纸版本表';
```

### 3.3 PLC程序版本表

```sql
CREATE TABLE plc_program_version (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    program_name VARCHAR(200) NOT NULL COMMENT '程序名称',
    
    -- PLC信息
    plc_brand ENUM('西门子','三菱','欧姆龙','倍福','汇川','台达','其他') NOT NULL,
    plc_model VARCHAR(100) COMMENT 'PLC型号',
    program_type ENUM('主程序','功能块','子程序','HMI') COMMENT '程序类型',
    
    -- 版本信息
    version VARCHAR(20) NOT NULL,
    
    -- 开发者信息
    developer_id BIGINT NOT NULL,
    developer_name VARCHAR(50),
    
    -- 程序统计
    program_steps INT COMMENT '程序步数/行数',
    function_blocks INT COMMENT '功能块数量',
    io_points INT COMMENT 'IO点数',
    axis_count INT COMMENT '轴数(运动控制)',
    
    -- 调试信息
    first_debug_pass BOOLEAN COMMENT '一次调通',
    debug_hours DECIMAL(6,2) COMMENT '调试时长(小时)',
    planned_debug_hours DECIMAL(6,2) COMMENT '计划调试时长',
    
    -- 稳定性跟踪
    stability_30days DECIMAL(5,2) COMMENT '30天稳定性(%)',
    bug_count INT DEFAULT 0 COMMENT '发现Bug数',
    
    -- 部署
    deploy_date DATE,
    deploy_status ENUM('success','failed','rollback'),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_developer (developer_id),
    INDEX idx_plc_brand (plc_brand)
) COMMENT 'PLC程序版本表';
```

### 3.4 电气元器件选型记录表

```sql
CREATE TABLE electrical_component_selection (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL,
    bom_id BIGINT COMMENT '关联BOM ID',
    
    -- 元器件信息
    component_type ENUM('PLC','HMI','伺服驱动','伺服电机','变频器','继电器','接触器','断路器','开关电源','传感器','线缆','端子','其他') NOT NULL,
    component_name VARCHAR(200) NOT NULL,
    brand VARCHAR(100) COMMENT '品牌',
    model VARCHAR(100) COMMENT '型号',
    
    -- 选型信息
    selector_id BIGINT NOT NULL COMMENT '选型人',
    selector_name VARCHAR(50),
    
    -- 是否标准件
    is_standard BOOLEAN DEFAULT FALSE COMMENT '是否标准型号',
    is_stock BOOLEAN DEFAULT FALSE COMMENT '是否库存件',
    
    -- 选型结果
    selection_correct BOOLEAN COMMENT '选型是否正确',
    need_change BOOLEAN DEFAULT FALSE COMMENT '是否需要更换',
    change_reason VARCHAR(200) COMMENT '更换原因',
    
    -- 成本
    unit_price DECIMAL(10,2) COMMENT '单价',
    quantity INT COMMENT '数量',
    total_price DECIMAL(12,2) COMMENT '总价',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_selector (selector_id),
    INDEX idx_component_type (component_type)
) COMMENT '电气元器件选型记录表';
```

### 3.5 电气故障记录表

```sql
CREATE TABLE electrical_fault_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    fault_no VARCHAR(30) NOT NULL COMMENT '故障编号',
    project_id BIGINT NOT NULL,
    
    -- 故障信息
    fault_type ENUM('接线错误','选型错误','程序Bug','设计缺陷','元器件损坏','通讯故障','其他') NOT NULL,
    fault_title VARCHAR(200) NOT NULL,
    fault_description TEXT,
    severity ENUM('致命','严重','一般','轻微') NOT NULL,
    
    -- 责任信息
    responsible_id BIGINT COMMENT '责任人',
    responsible_name VARCHAR(50),
    is_design_fault BOOLEAN COMMENT '是否设计问题',
    
    -- 发现信息
    found_stage ENUM('内部调试','现场调试','客户验收','售后运行') COMMENT '发现阶段',
    reporter_id BIGINT,
    reported_at DATETIME,
    
    -- 解决信息
    resolver_id BIGINT,
    resolved_at DATETIME,
    resolve_hours DECIMAL(6,2) COMMENT '解决时长',
    solution TEXT COMMENT '解决方案',
    
    -- 状态
    status ENUM('新建','处理中','已解决','已关闭') DEFAULT '新建',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_responsible (responsible_id),
    INDEX idx_fault_type (fault_type)
) COMMENT '电气故障记录表';
```

### 3.6 PLC程序模块库表

```sql
CREATE TABLE plc_module_library (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    module_name VARCHAR(200) NOT NULL COMMENT '模块名称',
    
    -- 模块信息
    module_type ENUM('运动控制','IO处理','通讯','数据处理','报警处理','配方管理','工艺流程','通用工具') NOT NULL,
    plc_brand VARCHAR(50) NOT NULL COMMENT '适用PLC品牌',
    
    -- 功能描述
    description TEXT COMMENT '功能描述',
    usage_guide TEXT COMMENT '使用说明',
    
    -- 开发者
    author_id BIGINT NOT NULL,
    author_name VARCHAR(50),
    
    -- 统计
    reuse_count INT DEFAULT 0 COMMENT '复用次数',
    rating DECIMAL(3,1) COMMENT '评分(1-5)',
    
    -- 版本
    version VARCHAR(20),
    
    -- 状态
    status ENUM('draft','published','deprecated') DEFAULT 'draft',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_author (author_id),
    INDEX idx_module_type (module_type),
    INDEX idx_plc_brand (plc_brand)
) COMMENT 'PLC程序模块库';

-- 模块复用记录
CREATE TABLE plc_module_reuse (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    module_id BIGINT NOT NULL COMMENT '模块ID',
    project_id BIGINT NOT NULL COMMENT '使用项目',
    user_id BIGINT NOT NULL COMMENT '使用者',
    user_name VARCHAR(50),
    reuse_type ENUM('直接复用','修改复用','参考借鉴') COMMENT '复用类型',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_module (module_id),
    INDEX idx_project (project_id)
) COMMENT 'PLC模块复用记录';
```

### 3.7 电气工程师绩效汇总表

```sql
CREATE TABLE electrical_engineer_performance (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    engineer_id BIGINT NOT NULL,
    engineer_name VARCHAR(50),
    
    period_type ENUM('monthly','quarterly','yearly') NOT NULL,
    period_value VARCHAR(10) NOT NULL,
    
    -- 技术能力指标
    drawing_pass_rate DECIMAL(5,2) COMMENT '图纸一次通过率(%)',
    plc_debug_pass_rate DECIMAL(5,2) COMMENT 'PLC一次调通率(%)',
    fault_density DECIMAL(5,2) COMMENT '故障密度(次/项目)',
    debug_efficiency DECIMAL(5,2) COMMENT '调试效率(%)',
    
    -- 项目执行指标
    task_count INT COMMENT '完成任务数',
    on_time_rate DECIMAL(5,2) COMMENT '按时完成率(%)',
    drawing_delivery_rate DECIMAL(5,2) COMMENT '图纸交付及时率(%)',
    field_response_rate DECIMAL(5,2) COMMENT '现场4h响应率(%)',
    ecn_response_hours DECIMAL(6,2) COMMENT 'ECN平均响应时长',
    
    -- 成本控制指标
    standard_component_rate DECIMAL(5,2) COMMENT '标准件使用率(%)',
    selection_accuracy DECIMAL(5,2) COMMENT '选型准确率(%)',
    stock_usage_rate DECIMAL(5,2) COMMENT '库存件使用率(%)',
    cost_saving DECIMAL(12,2) COMMENT '成本节约金额',
    
    -- 知识沉淀指标
    plc_module_count INT COMMENT 'PLC模块贡献数',
    template_count INT COMMENT '标准模板贡献数',
    doc_count INT COMMENT '技术文档数',
    module_reuse_count INT COMMENT '模块被复用次数',
    
    -- 协作指标
    mechanical_collab_score DECIMAL(3,1) COMMENT '机械配合评分',
    test_collab_score DECIMAL(3,1) COMMENT '测试配合评分',
    interface_doc_score DECIMAL(5,2) COMMENT '接口文档完整性',
    mentee_count INT COMMENT '带教新人数',
    
    -- 维度得分
    technical_score DECIMAL(5,2),
    execution_score DECIMAL(5,2),
    cost_score DECIMAL(5,2),
    knowledge_score DECIMAL(5,2),
    collaboration_score DECIMAL(5,2),
    
    -- 综合结果
    total_score DECIMAL(5,2),
    grade ENUM('优秀','良好','合格','待改进'),
    department_rank INT,
    
    calculated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_engineer_period (engineer_id, period_type, period_value),
    INDEX idx_period (period_type, period_value)
) COMMENT '电气工程师绩效汇总表';
```

---

## 四、API接口设计

### 4.1 接口概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    电气工程师绩效 API                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  绩效查询接口                                                    │
│  ├─ GET  /api/electrical/performance/summary      部门绩效概览   │
│  ├─ GET  /api/electrical/performance/ranking      绩效排名       │
│  ├─ GET  /api/electrical/performance/{id}         个人绩效详情   │
│  └─ GET  /api/electrical/performance/{id}/trend   绩效趋势       │
│                                                                  │
│  指标数据接口                                                    │
│  ├─ GET  /api/electrical/drawings                 图纸列表       │
│  ├─ GET  /api/electrical/plc-programs             PLC程序列表    │
│  ├─ GET  /api/electrical/faults                   故障记录       │
│  ├─ GET  /api/electrical/components               选型记录       │
│  └─ GET  /api/electrical/modules                  模块库         │
│                                                                  │
│  数据录入接口                                                    │
│  ├─ POST /api/electrical/drawings                 提交图纸       │
│  ├─ POST /api/electrical/drawings/{id}/review     图纸审核       │
│  ├─ POST /api/electrical/plc-programs             提交PLC程序    │
│  ├─ POST /api/electrical/faults                   登记故障       │
│  └─ POST /api/electrical/modules                  贡献模块       │
│                                                                  │
│  计算接口                                                        │
│  ├─ POST /api/electrical/performance/calculate    触发计算       │
│  └─ GET  /api/electrical/performance/config       获取权重配置   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 接口详细定义

#### 4.2.1 部门绩效概览

```yaml
GET /api/electrical/performance/summary

Query Parameters:
  - period_type: string (monthly|quarterly)  # 周期类型
  - period_value: string                      # 周期值，如 2024-11 或 2024Q4

Response:
{
  "code": 200,
  "data": {
    "period": {
      "type": "monthly",
      "value": "2024-11",
      "start_date": "2024-11-01",
      "end_date": "2024-11-30"
    },
    "overview": {
      "engineer_count": 10,
      "avg_score": 82.5,
      "score_change": 2.3,
      "excellent_count": 3,
      "excellent_rate": 30,
      "need_improve_count": 1
    },
    "key_metrics": {
      "drawing_pass_rate": {
        "value": 86.5,
        "target": 85,
        "status": "good"
      },
      "plc_debug_pass_rate": {
        "value": 82.0,
        "target": 80,
        "status": "good"
      },
      "on_time_rate": {
        "value": 88.5,
        "target": 90,
        "status": "warning"
      },
      "standard_component_rate": {
        "value": 72.0,
        "target": 70,
        "status": "good"
      },
      "fault_density": {
        "value": 0.15,
        "target": 0.2,
        "status": "good"
      }
    },
    "dimension_avg": {
      "technical": 84.2,
      "execution": 82.5,
      "cost": 80.8,
      "knowledge": 75.5,
      "collaboration": 86.0
    },
    "plc_brand_distribution": [
      { "brand": "西门子", "count": 45, "percentage": 50 },
      { "brand": "三菱", "count": 27, "percentage": 30 },
      { "brand": "欧姆龙", "count": 18, "percentage": 20 }
    ],
    "fault_type_distribution": [
      { "type": "程序Bug", "count": 5, "percentage": 35 },
      { "type": "接线错误", "count": 4, "percentage": 28 },
      { "type": "选型错误", "count": 3, "percentage": 21 },
      { "type": "其他", "count": 2, "percentage": 16 }
    ]
  }
}
```

#### 4.2.2 绩效排名

```yaml
GET /api/electrical/performance/ranking

Query Parameters:
  - period_type: string
  - period_value: string
  - plc_brand: string (optional)  # 按PLC品牌筛选
  - page: int (default: 1)
  - page_size: int (default: 20)

Response:
{
  "code": 200,
  "data": {
    "total": 10,
    "list": [
      {
        "rank": 1,
        "engineer_id": 1001,
        "engineer_name": "王电气",
        "level": "高级",
        "primary_plc": "西门子",
        "scores": {
          "technical": 92,
          "execution": 88,
          "cost": 85,
          "knowledge": 82,
          "collaboration": 90
        },
        "total_score": 88.5,
        "grade": "优秀",
        "trend": "up",
        "key_metrics": {
          "drawing_pass_rate": 95,
          "plc_debug_pass_rate": 90,
          "on_time_rate": 92,
          "fault_count": 1
        }
      },
      // ... more engineers
    ]
  }
}
```

#### 4.2.3 个人绩效详情

```yaml
GET /api/electrical/performance/{engineer_id}

Query Parameters:
  - period_type: string
  - period_value: string

Response:
{
  "code": 200,
  "data": {
    "engineer": {
      "id": 1001,
      "name": "王电气",
      "level": "高级工程师",
      "department": "电气设计部",
      "primary_plc": ["西门子", "三菱"],
      "join_date": "2019-03-15"
    },
    "period": {
      "type": "monthly",
      "value": "2024-11"
    },
    "summary": {
      "total_score": 88.5,
      "grade": "优秀",
      "rank": 1,
      "rank_total": 10,
      "score_change": 3.2
    },
    "dimension_scores": {
      "technical": { "score": 92, "weight": 30, "weighted": 27.6 },
      "execution": { "score": 88, "weight": 25, "weighted": 22.0 },
      "cost": { "score": 85, "weight": 20, "weighted": 17.0 },
      "knowledge": { "score": 82, "weight": 15, "weighted": 12.3 },
      "collaboration": { "score": 90, "weight": 10, "weighted": 9.0 }
    },
    "detail_metrics": {
      "technical": {
        "drawing_pass_rate": { "value": 95, "target": 85, "status": "good" },
        "plc_debug_pass_rate": { "value": 90, "target": 80, "status": "good" },
        "fault_density": { "value": 0.1, "target": 0.2, "status": "good" },
        "debug_efficiency": { "value": 95, "target": 90, "status": "good" }
      },
      "execution": {
        "task_count": { "value": 15, "description": "完成任务数" },
        "on_time_rate": { "value": 92, "target": 90, "status": "good" },
        "drawing_delivery_rate": { "value": 96, "target": 95, "status": "good" },
        "field_response_rate": { "value": 88, "target": 90, "status": "warning" }
      },
      "cost": {
        "standard_component_rate": { "value": 75, "target": 70, "status": "good" },
        "selection_accuracy": { "value": 98, "target": 95, "status": "good" },
        "stock_usage_rate": { "value": 62, "target": 60, "status": "good" }
      },
      "knowledge": {
        "plc_module_count": { "value": 3, "target": 2, "status": "good" },
        "template_count": { "value": 1, "target": 1, "status": "good" },
        "doc_count": { "value": 2, "target": 2, "status": "good" },
        "module_reuse_count": { "value": 12, "description": "被复用次数" }
      },
      "collaboration": {
        "mechanical_collab_score": { "value": 4.5, "target": 4.0, "status": "good" },
        "test_collab_score": { "value": 4.3, "target": 4.0, "status": "good" },
        "interface_doc_score": { "value": 92, "target": 90, "status": "good" }
      }
    },
    "projects": [
      {
        "project_id": "P2024-156",
        "project_name": "XX检测设备",
        "role": "主设计",
        "status": "已验收",
        "plc_brand": "西门子",
        "drawing_count": 25,
        "program_score": 92,
        "fault_count": 0
      }
    ],
    "drawings_summary": {
      "total": 45,
      "passed_first": 43,
      "by_type": [
        { "type": "电气原理图", "count": 15 },
        { "type": "PLC程序", "count": 12 },
        { "type": "HMI画面", "count": 8 },
        { "type": "其他", "count": 10 }
      ]
    },
    "plc_programs": [
      {
        "project": "P2024-156",
        "program_name": "主控程序",
        "plc_brand": "西门子",
        "model": "S7-1500",
        "version": "V2.1",
        "first_debug_pass": true,
        "stability": 100,
        "deploy_date": "2024-11-15"
      }
    ],
    "module_contributions": [
      {
        "module_name": "伺服定位FB",
        "module_type": "运动控制",
        "plc_brand": "西门子",
        "reuse_count": 8,
        "rating": 4.8
      }
    ]
  }
}
```

#### 4.2.4 绩效趋势

```yaml
GET /api/electrical/performance/{engineer_id}/trend

Query Parameters:
  - period_type: string (monthly|quarterly)
  - count: int (default: 6)  # 返回多少个周期

Response:
{
  "code": 200,
  "data": {
    "engineer_id": 1001,
    "engineer_name": "王电气",
    "period_type": "monthly",
    "trends": [
      {
        "period": "2024-06",
        "total_score": 82.1,
        "department_avg": 80.5,
        "dimensions": {
          "technical": 85,
          "execution": 80,
          "cost": 82,
          "knowledge": 75,
          "collaboration": 88
        }
      },
      {
        "period": "2024-07",
        "total_score": 83.5,
        "department_avg": 81.0,
        "dimensions": { ... }
      },
      // ... more periods
    ],
    "metric_trends": {
      "drawing_pass_rate": [85, 87, 88, 90, 92, 95],
      "plc_debug_pass_rate": [78, 80, 82, 85, 88, 90],
      "on_time_rate": [88, 89, 90, 90, 91, 92]
    }
  }
}
```

#### 4.2.5 图纸提交

```yaml
POST /api/electrical/drawings

Request Body:
{
  "project_id": 156,
  "drawing_no": "ELE-156-001",
  "drawing_name": "主电源柜原理图",
  "drawing_type": "电气原理图",
  "version": "V1.0",
  "page_count": 15,
  "component_count": 85,
  "planned_date": "2024-11-15",
  "designer_id": 1001,
  "attachments": ["file_id_1", "file_id_2"]
}

Response:
{
  "code": 200,
  "data": {
    "id": 10001,
    "drawing_no": "ELE-156-001",
    "status": "pending",
    "message": "图纸已提交，等待审核"
  }
}
```

#### 4.2.6 图纸审核

```yaml
POST /api/electrical/drawings/{id}/review

Request Body:
{
  "reviewer_id": 2001,
  "status": "approved",  // approved | rejected
  "comments": "设计规范，符合要求",
  "review_items": [
    { "item": "图纸规范性", "pass": true },
    { "item": "元器件选型", "pass": true },
    { "item": "接线正确性", "pass": true },
    { "item": "标注完整性", "pass": true }
  ]
}

Response:
{
  "code": 200,
  "data": {
    "id": 10001,
    "review_status": "approved",
    "review_pass_first": true,
    "review_count": 1,
    "message": "审核通过"
  }
}
```

#### 4.2.7 PLC程序提交

```yaml
POST /api/electrical/plc-programs

Request Body:
{
  "project_id": 156,
  "program_name": "XX检测设备主控程序",
  "plc_brand": "西门子",
  "plc_model": "S7-1500 CPU1516",
  "program_type": "主程序",
  "version": "V1.0",
  "program_steps": 5800,
  "function_blocks": 25,
  "io_points": 128,
  "axis_count": 4,
  "developer_id": 1001,
  "planned_debug_hours": 24
}

Response:
{
  "code": 200,
  "data": {
    "id": 20001,
    "program_name": "XX检测设备主控程序",
    "status": "created",
    "message": "程序版本已创建"
  }
}
```

#### 4.2.8 调试结果更新

```yaml
PUT /api/electrical/plc-programs/{id}/debug-result

Request Body:
{
  "first_debug_pass": true,
  "debug_hours": 20,
  "deploy_date": "2024-11-15",
  "deploy_status": "success",
  "notes": "一次调试通过，运行稳定"
}

Response:
{
  "code": 200,
  "data": {
    "id": 20001,
    "first_debug_pass": true,
    "debug_efficiency": 120,  // 计划24h, 实际20h = 120%
    "message": "调试结果已更新"
  }
}
```

#### 4.2.9 故障登记

```yaml
POST /api/electrical/faults

Request Body:
{
  "project_id": 156,
  "fault_type": "程序Bug",
  "fault_title": "自动模式下伺服报警",
  "fault_description": "在连续运行100次后，3号轴出现超时报警",
  "severity": "一般",
  "found_stage": "客户验收",
  "responsible_id": 1001,
  "is_design_fault": true
}

Response:
{
  "code": 200,
  "data": {
    "id": 30001,
    "fault_no": "EF-2024-0125",
    "status": "新建",
    "message": "故障已登记"
  }
}
```

#### 4.2.10 贡献PLC模块

```yaml
POST /api/electrical/modules

Request Body:
{
  "module_name": "西门子伺服定位功能块",
  "module_type": "运动控制",
  "plc_brand": "西门子",
  "description": "支持绝对定位、相对定位、回原点，带超时和故障处理",
  "usage_guide": "1. 调用FB块... 2. 配置参数...",
  "author_id": 1001,
  "version": "V1.0",
  "attachments": ["file_id_1"]
}

Response:
{
  "code": 200,
  "data": {
    "id": 40001,
    "module_name": "西门子伺服定位功能块",
    "status": "draft",
    "message": "模块已提交，待审核发布"
  }
}
```

#### 4.2.11 触发绩效计算

```yaml
POST /api/electrical/performance/calculate

Request Body:
{
  "period_type": "monthly",
  "period_value": "2024-11",
  "engineer_ids": [1001, 1002]  // 可选，不传则计算全部
}

Response:
{
  "code": 200,
  "data": {
    "task_id": "calc-20241201-001",
    "status": "processing",
    "message": "绩效计算任务已提交",
    "estimated_time": 30  // 预计30秒完成
  }
}
```

#### 4.2.12 获取权重配置

```yaml
GET /api/electrical/performance/config

Response:
{
  "code": 200,
  "data": {
    "weights": {
      "technical": {
        "weight": 30,
        "sub_items": {
          "drawing_pass_rate": { "weight": 30, "target": 85 },
          "plc_debug_pass_rate": { "weight": 30, "target": 80 },
          "fault_density": { "weight": 25, "target": 0.2, "inverse": true },
          "debug_efficiency": { "weight": 15, "target": 90 }
        }
      },
      "execution": {
        "weight": 25,
        "sub_items": {
          "on_time_rate": { "weight": 40, "target": 90 },
          "drawing_delivery_rate": { "weight": 30, "target": 95 },
          "field_response_rate": { "weight": 30, "target": 90 }
        }
      },
      "cost": {
        "weight": 20,
        "sub_items": {
          "standard_component_rate": { "weight": 40, "target": 70 },
          "selection_accuracy": { "weight": 40, "target": 95 },
          "stock_usage_rate": { "weight": 20, "target": 60 }
        }
      },
      "knowledge": {
        "weight": 15,
        "sub_items": {
          "plc_module_count": { "weight": 40, "target": 2 },
          "template_count": { "weight": 20, "target": 1 },
          "doc_count": { "weight": 25, "target": 2 },
          "module_reuse_count": { "weight": 15, "target": 5 }
        }
      },
      "collaboration": {
        "weight": 10,
        "sub_items": {
          "mechanical_collab_score": { "weight": 35, "target": 4.0 },
          "test_collab_score": { "weight": 35, "target": 4.0 },
          "interface_doc_score": { "weight": 30, "target": 90 }
        }
      }
    },
    "grade_rules": [
      { "grade": "优秀", "min_score": 85 },
      { "grade": "良好", "min_score": 70 },
      { "grade": "合格", "min_score": 60 },
      { "grade": "待改进", "min_score": 0 }
    ]
  }
}
```

---

## 五、前端页面设计

### 5.1 页面结构

```
电气工程师绩效评价系统
├── 部门总览
│   ├── 统计卡片（平均分、一次通过率、调试效率等）
│   ├── 绩效排名表
│   ├── PLC品牌分布图
│   └── 故障类型分布图
├── 个人绩效
│   ├── 工程师选择器
│   ├── 综合得分卡片
│   ├── 五维雷达图
│   ├── 关键指标明细
│   ├── 图纸交付记录
│   ├── PLC程序列表
│   └── 跨部门协作评价
├── 图纸管理
│   ├── 图纸列表
│   ├── 审核状态跟踪
│   └── 版本历史
├── PLC模块库
│   ├── 模块列表
│   ├── 热门模块排行
│   ├── 贡献者排行
│   └── 品牌分类
└── 指标配置
    ├── 权重配置
    ├── 目标值设置
    └── 等级划分
```
