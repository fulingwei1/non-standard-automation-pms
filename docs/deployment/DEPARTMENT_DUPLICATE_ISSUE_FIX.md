# 部门重复问题修复说明

## 问题描述

在部门管理界面中发现以下问题：

1. **重复部门**：在"营销中心"下同时存在"商务部 (D003)"和"营销中心-商务部 (D004)"
2. **错误数据**：存在"海尔治县 (D012)"等明显错误的数据
3. **冗余命名**：多个部门名称包含父部门名称，造成视觉上的重复

## 问题原因分析

### 1. 缺少部门名称验证
- **原问题**：创建部门时只检查了部门编码(`dept_code`)的唯一性
- **影响**：允许在同一父部门下创建相同或相似的部门名称
- **位置**：`app/api/v1/endpoints/organization.py` 的 `create_department` 函数

### 2. 数据导入不规范
- **原问题**：导入脚本可能创建了包含父部门名称的部门（如"营销中心-商务部"）
- **影响**：导致部门树中出现冗余的命名
- **位置**：`scripts/import_employee_data_simple.py` 的 `import_departments` 函数

### 3. 测试数据未清理
- **原问题**：系统测试时创建的数据（如"测试部"、"海尔治县"）未在生产环境清理
- **影响**：污染了生产数据

## 修复方案

### 1. API 端点增强验证 ✅

**文件**：`app/api/v1/endpoints/organization.py`

**修改内容**：

#### 创建部门时 (`create_department`)
- ✅ 检查同一父部门下部门名称是否重复
- ✅ 检查部门名称是否包含父部门名称（避免冗余命名）
- ✅ 提供友好的错误提示和建议

#### 更新部门时 (`update_department`)
- ✅ 检查更新后的部门名称是否与同级部门重复
- ✅ 检查更新后的部门名称是否包含父部门名称

**验证逻辑**：
```python
# 检查同一父部门下部门名称是否重复
query = db.query(Department).filter(Department.dept_name == dept_in.dept_name)
if dept_in.parent_id:
    query = query.filter(Department.parent_id == dept_in.parent_id)
else:
    query = query.filter(Department.parent_id.is_(None))

existing_dept = query.first()
if existing_dept:
    raise HTTPException(
        status_code=400,
        detail=f"该部门名称已存在（{existing_dept.dept_code}）",
    )

# 检查部门名称是否包含父部门名称
if parent.dept_name in dept_in.dept_name and dept_in.dept_name != parent.dept_name:
    raise HTTPException(
        status_code=400,
        detail=f"部门名称不应包含父部门名称。建议使用：{suggested_name}",
    )
```

### 2. 数据清理脚本 ✅

**文件**：`scripts/cleanup_duplicate_departments.py`

**功能**：
1. **识别重复部门**：查找同一父部门下名称相同的部门
2. **识别冗余命名**：查找包含父部门名称的部门（如"营销中心-商务部"）
3. **识别错误数据**：查找明显的错误数据（如"海尔治县"、"测试"等）
4. **提供清理建议**：自动生成建议的部门名称
5. **执行清理**：支持模拟运行和实际执行

**使用方法**：
```bash
# 运行清理脚本
python3 scripts/cleanup_duplicate_departments.py

# 选项：
# 1. 仅查看报告（不执行清理）
# 2. 模拟运行（查看将执行的操作）
# 3. 执行清理（重命名冗余部门，禁用错误数据）
```

## 发现的问题数据

### 冗余命名部门（5个）
1. **营销中心-商务部 (D004)** → 建议重命名为：**商务部**
2. **PLC二组 (D028)** → 建议重命名为：**二组**
3. **PLC一组 (D029)** → 建议重命名为：**一组**
4. **制造中心-生产部 (D044)** → 建议重命名为：**生产部**
5. **制造中心-客服部 (D045)** → 建议重命名为：**客服部**

### 错误数据（3个）
1. **海尔治县 (D012)** - 疑似地名，非部门名称
2. **测试部 (D008)** - 测试数据
3. **研发中心-测试部 (D032)** - 测试数据

## 清理步骤

### 步骤 1：查看问题报告
```bash
python3 scripts/cleanup_duplicate_departments.py
# 选择选项 1：仅查看报告
```

### 步骤 2：模拟运行（可选）
```bash
python3 scripts/cleanup_duplicate_departments.py
# 选择选项 2：模拟运行
# 查看将执行的操作，确认无误
```

### 步骤 3：执行清理
```bash
python3 scripts/cleanup_duplicate_departments.py
# 选择选项 3：执行清理
# 输入 'y' 确认执行
```

**清理操作**：
- ✅ 自动重命名冗余命名的部门（移除父部门名称前缀）
- ✅ 禁用错误数据（设置 `is_active = 0`）

## 预防措施

### 1. 前端验证
建议在前端表单中添加实时验证：
- 输入部门名称时，检查是否与同级部门重复
- 提示用户不要包含父部门名称

### 2. 数据导入规范
- 导入部门数据时，自动清理部门名称中的父部门前缀
- 导入前验证数据质量

### 3. 定期检查
- 定期运行清理脚本检查数据质量
- 在系统维护时清理测试数据

## 注意事项

⚠️ **执行清理前请备份数据库**：
```bash
cp data/app.db data/app.db.backup
```

⚠️ **清理操作说明**：
- 重命名操作会修改部门名称，可能影响已关联的数据
- 禁用操作会将部门标记为不活跃，不会删除数据
- 建议在非业务时间执行清理

## 相关文件

- `app/api/v1/endpoints/organization.py` - 部门管理API端点
- `app/models/organization.py` - 部门数据模型
- `scripts/cleanup_duplicate_departments.py` - 数据清理脚本
- `scripts/import_employee_data_simple.py` - 数据导入脚本

## 更新日期

2025-01-20
