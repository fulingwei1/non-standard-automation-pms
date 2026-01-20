# 测试覆盖率提升进度报告

**生成时间**: 2026-01-20 22:05:44

---

## 📊 总体覆盖率

- **总体覆盖率**: 39.30%
- **总代码语句数**: 74,831
- **已覆盖语句数**: 29,409
- **未覆盖语句数**: 45,422

---

## 🔧 服务层覆盖率

- **服务文件总数**: 210
- **已覆盖文件数**: 90
- **零覆盖率文件数**: 120
- **服务层覆盖率**: 9.09%
- **服务层总语句数**: 20,526
- **服务层已覆盖语句数**: 1,866

---

## 📈 进度对比


- **总体覆盖率变化**: 39.30% → 39.30% (+0.00%)
- **服务层覆盖率变化**: 9.09% → 9.09% (+0.00%)

---

## 🎯 零覆盖率服务文件

当前还有 **120** 个服务文件覆盖率为 0%

### 前20个最大零覆盖率服务:

 1. `notification_dispatcher` - 309 行
 2. `timesheet_report_service` - 290 行
 3. `status_transition_service` - 219 行
 4. `sales_team_service` - 200 行
 5. `win_rate_prediction_service` - 200 行
 6. `report_data_generation_service` - 193 行
 7. `report_export_service` - 193 行
 8. `resource_waste_analysis_service` - 193 行
 9. `pipeline_health_service` - 191 行
10. `hr_profile_import_service` - 187 行
11. `docx_content_builders` - 186 行
12. `metric_calculation_service` - 181 行
13. `cost_collection_service` - 180 行
14. `invoice_auto_service` - 179 行
15. `collaboration_rating_service` - 172 行
16. `timesheet_reminder_service` - 172 行
17. `template_report_service` - 171 行
18. `timesheet_sync_service` - 171 行
19. `scheduling_suggestion_service` - 164 行
20. `excel_export_service` - 160 行

---

## 📝 下一步行动

1. **继续生成测试文件**: 
   ```bash
   python3 scripts/generate_service_tests_batch.py --batch-size 20 --start 20
   ```

2. **实现测试用例**: 为已生成的测试文件实现具体测试逻辑

3. **运行测试验证**: 
   ```bash
   pytest tests/unit/ -v --cov=app/services --cov-report=term-missing
   ```

4. **检查覆盖率提升**: 定期运行此脚本跟踪进度

---

## 💡 建议

- 优先处理代码量大的服务文件（前30个）
- 每个服务至少达到 60% 覆盖率
- 重点关注核心业务逻辑的测试覆盖
