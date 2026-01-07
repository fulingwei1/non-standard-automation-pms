# TODO/FIXME 标记处理总结

## 处理进度

### 已处理的 TODO/FIXME

#### 1. 通知功能实现 ✅

**文件**: `app/api/v1/endpoints/task_center.py`

- ✅ **任务转办通知** (行 604)
  - 实现：转办任务时发送通知给目标用户
  - 通知类型：`TASK_ASSIGNED`
  - 优先级：`HIGH`

- ✅ **转办拒绝通知** (行 694)
  - 实现：拒绝转办时通知原转办人
  - 通知类型：`TASK_TRANSFER_REJECTED`
  - 优先级：`NORMAL`

- ✅ **评论@用户通知** (行 737)
  - 实现：评论中@用户时发送通知
  - 通知类型：`TASK_MENTIONED`
  - 优先级：`NORMAL`
  - 支持多个用户同时@

#### 2. IP 地址获取 ✅

**文件**: `app/api/v1/endpoints/acceptance.py`

- ✅ **验收签字 IP 地址** (行 1210)
  - 实现：从 Request 对象获取客户端 IP 地址
  - 使用：`request.client.host if request and request.client else None`

## 待处理的 TODO/FIXME

### 高优先级（核心功能）

1. **报表中心功能** (`app/api/v1/endpoints/report_center.py`)
   - 行 97: 从数据库或配置读取权限矩阵
   - 行 123: 检查权限
   - 行 128: 根据报表类型和角色生成数据
   - 行 174: 生成预览数据
   - 行 196: 生成各角色视角的数据并对比
   - 行 223: 根据格式生成文件并返回下载链接
   - 行 298: 根据模板配置生成报表数据
   - 行 551: 从项目模块获取营业收入
   - 行 643: 根据报表类型生成Excel/PDF文件

2. **数据导入导出** (`app/schemas/data_import_export.py`)
   - 行 24: 支持文件上传

3. **缺料管理** (`app/api/v1/endpoints/shortage_alerts.py`)
   - 行 1568: 更新BOM中的物料信息
   - 行 1694: 查询调出项目的物料库存
   - 行 1833: 更新项目库存（从调出项目减少，调入项目增加）

### 中优先级（功能增强）

1. **任务分配** (`app/api/v1/endpoints/progress.py`)
   - 行 441: 根据角色查找用户并分配

2. **售前管理** (`app/api/v1/endpoints/presale.py`)
   - 行 1077: 解析cost_template JSON并创建PresaleSolutionCost记录

3. **工作量管理** (`app/api/v1/endpoints/workload.py`)
   - 行 541: 从WorkerSkill表获取技能

4. **PMO管理** (`app/api/v1/endpoints/pmo.py`)
   - 行 648: 可以添加推进到下一阶段的逻辑
   - 行 1659: 可以调用workload模块的API或复用其逻辑

5. **销售管理** (`app/api/v1/endpoints/sales.py`)
   - 行 1136: 实现更严格的权限检查

### 低优先级（前端占位符）

1. **前端 API 调用占位符**
   - 多个前端页面中的 TODO 标记，需要调用后端 API
   - 这些主要是前端实现，需要与后端 API 对接

2. **前端数据获取**
   - 销售统计页面：需要从合同、发票等获取实际数据
   - 售前工作台：需要从用户 API 获取团队信息
   - 物料分析：需要从采购订单获取数据

## 处理建议

### 短期（1-2周）

1. **完成报表中心核心功能**
   - 实现权限矩阵读取
   - 实现报表数据生成
   - 实现文件导出功能

2. **完善数据导入导出**
   - 实现文件上传功能
   - 完善 Excel 处理逻辑

### 中期（1个月）

1. **完善缺料管理功能**
   - 实现 BOM 更新逻辑
   - 实现项目库存调拨

2. **增强任务分配功能**
   - 实现基于角色的自动分配

### 长期（持续优化）

1. **前端功能对接**
   - 逐步将前端 TODO 标记替换为实际 API 调用
   - 实现数据获取和展示

2. **权限系统增强**
   - 实现更细粒度的权限控制

## 注意事项

1. **状态值 "TODO"**: 
   - `app/models/progress.py` 和 `app/api/v1/endpoints/progress.py` 中的 "TODO" 是任务状态值，不是待办事项，应保留

2. **通知失败处理**:
   - 所有通知功能都使用 try-except 包裹，确保通知失败不影响主流程

3. **向后兼容**:
   - 所有修改都保持向后兼容，不影响现有功能

## 统计

- **总 TODO/FIXME 数量**: 约 145 个
- **已处理**: 4 个（通知功能 3 个 + IP 地址 1 个）
- **待处理**: 约 141 个
- **处理进度**: 约 3%


