# 项目复盘高级管理 API 测试指南

## 测试环境准备

1. 确保后端服务正在运行
2. 准备测试数据（至少1个已完成的项目复盘报告）
3. 准备认证 Token

---

## 测试用例

### 1. 经验教训高级管理测试

#### 1.1 跨项目搜索经验教训
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/projects/lessons-learned?keyword=进度&lesson_type=FAILURE&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期结果**: 返回包含关键词"进度"的失败教训列表

#### 1.2 获取经验教训统计
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/projects/lessons-learned/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期结果**: 返回统计信息，包括总数、分类统计、状态统计等

#### 1.3 获取经验教训分类列表
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/projects/lessons-learned/categories" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期结果**: 返回所有分类列表

#### 1.4 更新经验教训状态
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/projects/project-reviews/lessons/1/status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_status": "RESOLVED"}'
```

**预期结果**: 经验教训状态更新为RESOLVED，并自动设置解决日期

#### 1.5 批量更新经验教训
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/projects/project-reviews/lessons/batch-update" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_ids": [1, 2, 3],
    "update_data": {
      "status": "IN_PROGRESS",
      "priority": "HIGH"
    }
  }'
```

**预期结果**: 批量更新成功，返回更新数量

---

### 2. 最佳实践高级管理测试

#### 2.1 推荐最佳实践
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/projects/best-practices/recommend" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "ICT测试设备",
    "current_stage": "S3",
    "category": "流程",
    "limit": 10
  }'
```

**预期结果**: 返回推荐的最佳实践列表，包含匹配度分数和匹配原因

#### 2.2 获取项目推荐的最佳实践
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/projects/123/best-practices/recommend?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期结果**: 基于项目信息自动推荐最佳实践

#### 2.3 应用最佳实践到项目
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/projects/project-reviews/best-practices/1/apply" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_project_id": 123,
    "notes": "在采购阶段应用此最佳实践"
  }'
```

**预期结果**: 最佳实践应用成功，复用计数+1

#### 2.4 获取热门最佳实践
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/projects/best-practices/popular?category=流程&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期结果**: 返回按复用次数排序的热门最佳实践列表

---

## 测试检查清单

- [ ] 所有端点返回正确的HTTP状态码
- [ ] 权限控制正常工作（无权限用户无法访问）
- [ ] 分页功能正常
- [ ] 搜索和筛选功能正常
- [ ] 统计信息计算准确
- [ ] 推荐算法匹配度计算正确
- [ ] 批量操作功能正常
- [ ] 状态更新自动设置相关字段

---

## 常见问题

### Q1: 推荐最佳实践返回空列表？
**A**: 检查是否有已验证（VALIDATED）且可复用（is_reusable=True）的最佳实践

### Q2: 统计信息不准确？
**A**: 检查数据库中的经验教训数据是否完整，特别是分类、状态、优先级字段

### Q3: 批量更新失败？
**A**: 检查所有经验教训ID是否有效，以及用户是否有权限访问所有相关项目

---

## 性能测试建议

1. **搜索性能**: 测试大量数据下的搜索响应时间
2. **统计性能**: 测试统计查询的性能
3. **推荐性能**: 测试推荐算法的响应时间

---

## 下一步

完成测试后，可以：
1. 集成到前端页面
2. 添加更多业务逻辑
3. 优化查询性能
4. 添加缓存机制




