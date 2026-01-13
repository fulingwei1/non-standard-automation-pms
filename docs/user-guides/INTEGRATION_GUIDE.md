# 重构代码集成指南

## 概述

本文档说明如何将重构后的组件集成到主页面文件中。

## 集成步骤

### 1. ECN 模块集成

#### 当前状态
- ✅ 重构后的组件已创建在 `frontend/src/components/ecn/`
- ✅ 重构后的主组件示例在 `frontend/src/components/ecn/ECNDetail.refactored.example.jsx`
- ⏳ 原始文件 `frontend/src/pages/ECNDetail.jsx` (2881行) 尚未替换

#### 集成方法

**选项 A：直接替换（推荐用于测试）**
```bash
# 备份原文件
cp frontend/src/pages/ECNDetail.jsx frontend/src/pages/ECNDetail.jsx.backup

# 复制重构后的文件
cp frontend/src/components/ecn/ECNDetail.refactored.example.jsx frontend/src/pages/ECNDetail.jsx

# 修复导入路径（从 components/ecn/ 改为相对路径）
# 需要将导入路径从：
# import { useECNDetail } from '../components/ecn/hooks/useECNDetail'
# 改为：
# import { useECNDetail } from '../components/ecn/hooks/useECNDetail'
```

**选项 B：手动集成（推荐用于生产）**
1. 打开 `frontend/src/pages/ECNDetail.jsx`
2. 替换整个文件内容为 `ECNDetail.refactored.example.jsx` 的内容
3. 确保导入路径正确（已在示例文件中修复）

#### 注意事项
- 重构后的文件使用相对路径导入，需要确保路径正确
- 所有 Tab 组件和 Hooks 已创建，确保它们都在正确的位置
- 测试所有 Tab 切换和功能是否正常

### 2. HR 模块集成

#### 当前状态
- ✅ 重构后的组件已创建在 `frontend/src/components/hr/`
- ✅ 重构后的主组件示例在 `frontend/src/components/hr/HRManagerDashboard.refactored.example.jsx`
- ⏳ 原始文件 `frontend/src/pages/HRManagerDashboard.jsx` (3047行) 尚未替换

#### 集成方法
与 ECN 模块类似，复制 `HRManagerDashboard.refactored.example.jsx` 到 `pages/HRManagerDashboard.jsx`

## 集成前检查清单

- [ ] 所有组件文件已创建
- [ ] 所有 Hooks 已创建
- [ ] 所有对话框组件已创建
- [ ] ESLint 检查通过
- [ ] 导入路径正确
- [ ] 备份了原始文件

## 集成后测试清单

- [ ] 页面可以正常加载
- [ ] 所有 Tab 可以正常切换
- [ ] 数据加载正常
- [ ] 所有按钮和操作功能正常
- [ ] 对话框可以正常打开和关闭
- [ ] 没有控制台错误
- [ ] 没有 ESLint 错误

## 回滚方法

如果集成后出现问题，可以快速回滚：

```bash
# 恢复 ECN 模块
cp frontend/src/pages/ECNDetail.jsx.backup frontend/src/pages/ECNDetail.jsx

# 恢复 HR 模块
cp frontend/src/pages/HRManagerDashboard.jsx.backup frontend/src/pages/HRManagerDashboard.jsx
```

## 后续工作

集成完成后，还需要：
1. 将 mock 数据替换为真实 API 调用
2. 完善错误处理
3. 添加加载状态
4. 优化性能
5. 编写单元测试
