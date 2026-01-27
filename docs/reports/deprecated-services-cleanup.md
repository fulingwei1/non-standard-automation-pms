# 废弃报表服务清理说明

> **创建日期**: 2026-01-27  
> **状态**: ⚠️ **已标记为废弃，待完全移除**

---

## 📋 已标记为废弃的服务

以下报表服务已迁移到统一报表框架，但服务文件仍保留（因为适配器仍在使用部分函数）：

### 1. timesheet_report_service.py ⚠️

**状态**: 已废弃，但部分函数仍被适配器使用

**原因**: 
- API端点已迁移到统一报表框架
- 但适配器可能仍需要某些辅助函数

**建议**:
- 将仍需要的函数提取到适配器中
- 完全移除服务文件

---

### 2. sales_monthly_report_service.py ⚠️

**状态**: 已废弃，但函数仍被适配器使用

**原因**:
- API端点已迁移到统一报表框架
- `SalesReportAdapter` 仍在使用其中的函数（如 `calculate_contract_statistics`）

**建议**:
- 将函数逻辑迁移到适配器中
- 完全移除服务文件

---

### 3. acceptance_report_service.py ⚠️

**状态**: 已废弃，但部分函数仍被使用

**原因**:
- API端点已迁移到统一报表框架
- 但 `generate_report_no`, `save_report_file` 等函数仍被API端点使用

**建议**:
- 将这些辅助函数提取到工具模块
- 完全移除服务文件

---

### 4. meeting_report_service.py ⚠️

**状态**: 已废弃，但部分函数仍被使用（向后兼容）

**原因**:
- API端点已迁移到统一报表框架
- 但向后兼容逻辑仍在使用 `MeetingReportService.generate_*_report`

**建议**:
- 完全移除向后兼容逻辑后
- 完全移除服务文件

---

### 5. report_export_service.py ⚠️

**状态**: 已废弃，但部分函数仍被使用

**原因**:
- API端点已迁移到统一报表框架
- 但某些导出逻辑仍在使用旧服务

**建议**:
- 完全迁移到统一报表框架的渲染器
- 完全移除服务文件

---

## 🔧 清理步骤

### Phase 1: 标记为废弃 ✅

- ✅ 在所有服务文件顶部添加废弃警告
- ✅ 添加 `DeprecationWarning`
- ✅ 添加迁移指南注释

### Phase 2: 提取仍需要的函数

- ⏳ 将 `acceptance_report_service` 中的辅助函数提取到工具模块
- ⏳ 将 `sales_monthly_report_service` 中的函数逻辑迁移到适配器
- ⏳ 将 `meeting_report_service` 中的函数逻辑迁移到适配器

### Phase 3: 移除向后兼容逻辑

- ⏳ 移除API端点中的向后兼容代码
- ⏳ 确保所有功能都通过统一报表框架

### Phase 4: 完全移除服务文件

- ⏳ 删除 `timesheet_report_service.py`
- ⏳ 删除 `sales_monthly_report_service.py`
- ⏳ 删除 `acceptance_report_service.py`
- ⏳ 删除 `meeting_report_service.py`
- ⏳ 删除 `report_export_service.py`

---

## 📝 注意事项

1. **不要立即删除**: 这些服务文件仍被适配器或API端点使用
2. **逐步迁移**: 先将函数逻辑迁移到适配器或工具模块
3. **测试验证**: 每次迁移后都要运行完整测试
4. **向后兼容**: 确保移除后不影响现有功能

---

## ✅ 已完成

- ✅ 标记所有废弃服务为deprecated
- ✅ 添加废弃警告和迁移指南

---

## ⏳ 待完成

- ⏳ 提取仍需要的函数到适配器或工具模块
- ⏳ 移除向后兼容逻辑
- ⏳ 完全移除服务文件

---

**文档版本**: v1.0  
**创建日期**: 2026-01-27  
**状态**: ⚠️ 已标记为废弃，待完全移除
