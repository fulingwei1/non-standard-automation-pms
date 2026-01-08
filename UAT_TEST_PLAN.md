# 工程师进度管理系统 - UAT测试计划

**测试环境：** 测试服务器
**测试周期：** 2026-01-08 至 2026-01-14
**测试负责人：** QA团队 + 业务用户代表
**系统版本：** v1.0.0

---

## 1. 测试目标

### 主要目标
1. ✅ 验证工程师进度管理核心功能是否满足业务需求
2. ✅ 确认系统解决了两大核心痛点
3. ✅ 评估用户体验和操作流畅性
4. ✅ 发现并记录系统缺陷

### 验收标准
- 所有核心业务场景测试通过率 ≥ 95%
- 无P0（严重阻塞）级别缺陷
- P1（主要功能）缺陷 ≤ 2个
- 用户满意度评分 ≥ 4.0/5.0

---

## 2. 测试环境准备

### 2.1 服务器配置

**开发/测试服务器：**
```
URL: http://localhost:8000 或 http://test-server:8000
数据库: SQLite (data/app.db)
API文档: http://localhost:8000/docs
```

**测试账号准备：**
| 角色 | 用户名 | 密码 | 所属部门 | 说明 |
|------|--------|------|----------|------|
| 工程师1 | engineer_mech | test123 | 机械部 | 机械工程师 |
| 工程师2 | engineer_elec | test123 | 电气部 | 电气工程师 |
| 工程师3 | engineer_test | test123 | 测试部 | 测试工程师 |
| PM | pm_zhang | test123 | PMO | 项目经理 |
| 部门经理 | manager_mech | test123 | 机械部 | 机械部经理 |

### 2.2 测试数据准备

**项目数据：**
- 项目1: ICT测试设备项目 (PJ260101001)
  - 当前阶段: S4 (加工制造)
  - 项目经理: pm_zhang
  - 项目成员: 机械部2人, 电气部2人, 测试部1人

**初始任务数据：**
- 15个任务（机械5个、电气5个、测试5个）
- 状态分布: PENDING(3), ACCEPTED(5), IN_PROGRESS(5), COMPLETED(2)
- 进度分布: 0%(3), 30%(2), 50%(3), 70%(3), 100%(2)

---

## 3. 测试用例清单

### 3.1 工程师端功能测试（9个场景）

#### TC001: 查看我的项目列表
**测试步骤：**
1. 以 engineer_mech 身份登录
2. 访问 `GET /api/v1/engineers/my-projects`
3. 验证响应数据

**预期结果：**
- ✅ 返回参与的所有项目
- ✅ 每个项目包含任务统计（总数、进行中、已完成、逾期等）
- ✅ 显示我在项目中的角色
- ✅ 显示分配比例

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC002: 创建一般任务（无需审批）
**测试步骤：**
1. 以 engineer_mech 身份登录
2. 创建任务:
```json
POST /api/v1/engineers/tasks
{
  "project_id": 1,
  "title": "设计夹具固定方案",
  "task_importance": "GENERAL",
  "priority": "HIGH",
  "estimated_hours": 16
}
```
3. 验证任务创建成功

**预期结果：**
- ✅ 任务创建成功，返回task_id
- ✅ 任务状态 = ACCEPTED（直接可执行）
- ✅ approval_required = False
- ✅ 无需PM审批

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC003: 创建重要任务（需要审批）
**测试步骤：**
1. 以 engineer_elec 身份登录
2. 创建重要任务:
```json
POST /api/v1/engineers/tasks
{
  "project_id": 1,
  "title": "变更电机选型方案",
  "task_importance": "IMPORTANT",
  "justification": "客户要求提高设备功率，需重新选型电机",
  "priority": "URGENT",
  "estimated_hours": 40
}
```
3. 验证任务进入审批流程

**预期结果：**
- ✅ 任务创建成功
- ✅ 任务状态 = PENDING_APPROVAL（待审批）
- ✅ approval_required = True
- ✅ 创建了 TaskApprovalWorkflow 记录
- ✅ approver_id = PM的ID

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC004: 更新任务进度（触发聚合）
**测试步骤：**
1. 以 engineer_mech 身份登录
2. 查找一个 status=ACCEPTED 的任务
3. 更新进度到50%:
```json
PUT /api/v1/engineers/tasks/{task_id}/progress
{
  "progress": 50,
  "actual_hours": 8,
  "progress_note": "夹具方案初稿完成"
}
```
4. 验证聚合效果

**预期结果：**
- ✅ 任务进度更新为50%
- ✅ 任务状态自动变为 IN_PROGRESS
- ✅ project_progress_updated = true（项目进度已更新）
- ✅ stage_progress_updated = true（阶段进度已更新）
- ✅ 查询项目进度，验证已重新计算

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC005: 上传完成证明
**测试步骤：**
1. 以 engineer_test 身份登录
2. 选择一个进行中的任务
3. 上传证明文件（准备一个PDF测试文件）:
```bash
POST /api/v1/engineers/tasks/{task_id}/completion-proofs/upload
Content-Type: multipart/form-data

file: test_report.pdf
proof_type: TEST_REPORT
description: 功能测试报告
```
4. 验证文件上传

**预期结果：**
- ✅ 文件上传成功
- ✅ 返回文件元数据（文件名、大小、类型）
- ✅ 文件保存在 `uploads/task_proofs/{task_id}/` 目录
- ✅ 数据库中创建 TaskCompletionProof 记录

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC006: 完成任务（验证证明材料）
**测试步骤：**
1. 以 engineer_mech 身份登录
2. 选择一个已上传证明的任务
3. 标记完成:
```json
PUT /api/v1/engineers/tasks/{task_id}/complete
{
  "completion_note": "夹具方案已完成并通过评审"
}
```
4. 验证完成逻辑

**预期结果：**
- ✅ 任务状态变为 COMPLETED
- ✅ 任务进度自动变为 100%
- ✅ actual_end_date 设置为今天
- ✅ 返回 proof_count（证明数量）

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC007: 完成任务（无证明 - 应失败）
**测试步骤：**
1. 以 engineer_elec 身份登录
2. 创建一个新任务
3. 不上传证明，直接尝试完成:
```json
PUT /api/v1/engineers/tasks/{task_id}/complete
{
  "completion_note": "任务已完成"
}
```

**预期结果：**
- ❌ 返回错误: "需要至少1个完成证明才能完成任务"
- ❌ 任务状态不变
- ✅ 可以通过 skip_proof_validation=true 跳过验证

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC008: 报告任务延期
**测试步骤：**
1. 以 engineer_elec 身份登录
2. 选择一个进行中的任务
3. 报告延期:
```json
POST /api/v1/engineers/tasks/{task_id}/report-delay
{
  "delay_reason": "客户需求变更导致电气方案需重新设计",
  "delay_responsibility": "客户需求变更",
  "delay_impact_scope": "PROJECT",
  "schedule_impact_days": 5,
  "cost_impact": 8000,
  "new_completion_date": "2026-01-20"
}
```
4. 验证延期记录

**预期结果：**
- ✅ 创建成功，返回 exception_event_id
- ✅ 任务is_delayed标记为True
- ✅ 项目健康度可能下降（H1→H2或H2→H3）
- ✅ 创建ExceptionEvent记录
- ✅ 返回通知发送数量（待实现）

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC009: 删除证明材料
**测试步骤：**
1. 以证明上传者身份登录
2. 上传一个测试文件
3. 删除刚上传的文件:
```
DELETE /api/v1/engineers/tasks/{task_id}/completion-proofs/{proof_id}
```

**预期结果：**
- ✅ 数据库记录删除
- ✅ 物理文件也被删除
- ✅ 返回成功消息

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

### 3.2 PM审批端功能测试（4个场景）

#### TC010: PM查看待审批任务列表
**测试步骤：**
1. 以 pm_zhang 身份登录
2. 访问 `GET /api/v1/engineers/tasks/pending-approval`

**预期结果：**
- ✅ 返回所有待审批的IMPORTANT任务
- ✅ 只显示该PM负责的项目的任务
- ✅ 任务按创建时间倒序排列

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC011: PM批准任务
**测试步骤：**
1. 以 pm_zhang 身份登录
2. 选择一个待审批任务
3. 批准:
```json
PUT /api/v1/engineers/tasks/{task_id}/approve
{
  "approval_note": "方案合理，同意执行"
}
```

**预期结果：**
- ✅ 任务approval_status变为APPROVED
- ✅ 任务status变为ACCEPTED（可以执行）
- ✅ approved_by = PM的ID
- ✅ approved_at = 当前时间
- ✅ TaskApprovalWorkflow更新

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC012: PM拒绝任务
**测试步骤：**
1. 以 pm_zhang 身份登录
2. 选择一个待审批任务
3. 拒绝:
```json
PUT /api/v1/engineers/tasks/{task_id}/reject
{
  "rejection_reason": "变更范围超出项目预算，建议缩小范围"
}
```

**预期结果：**
- ✅ 任务approval_status变为REJECTED
- ✅ 任务status变为CANCELLED
- ✅ rejection_reason被记录
- ✅ TaskApprovalWorkflow更新

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC013: 查看审批历史
**测试步骤：**
1. 以任意相关人员身份登录
2. 访问 `GET /api/v1/engineers/tasks/{task_id}/approval-history`

**预期结果：**
- ✅ 返回该任务的所有审批记录
- ✅ 包含提交人、审批人、时间、意见
- ✅ 按时间倒序排列

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

### 3.3 跨部门协作功能测试（3个场景）

#### TC014: 获取我的任务列表（带筛选）
**测试步骤：**
1. 以 engineer_mech 身份登录
2. 测试各种筛选条件:
```
GET /api/v1/engineers/tasks?status=IN_PROGRESS
GET /api/v1/engineers/tasks?priority=HIGH
GET /api/v1/engineers/tasks?is_delayed=true
GET /api/v1/engineers/tasks?project_id=1&page=1&page_size=10
```

**预期结果：**
- ✅ 筛选逻辑正确
- ✅ 分页正常工作
- ✅ 返回任务包含proof_count

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC015: 获取任务详情
**测试步骤：**
1. 以 engineer_elec 身份登录
2. 访问 `GET /api/v1/engineers/tasks/{task_id}`

**预期结果：**
- ✅ 返回任务完整信息
- ✅ 包含所有字段（基础+审批+延期+完成）
- ✅ proof_count准确

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC016: **跨部门进度可见性（核心功能）**
**测试步骤：**
1. 以 manager_mech（部门经理）身份登录
2. 访问 `GET /api/v1/engineers/projects/1/progress-visibility`
3. 验证响应数据的完整性

**预期结果：**
- ✅ 返回项目整体进度
- ✅ 返回所有部门的进度统计:
  - 部门名称
  - 总任务数、完成数、进行中、延期数
  - 部门进度百分比
  - 成员列表及各成员的任务统计
- ✅ 返回各阶段(S1-S9)进度
- ✅ 返回活跃延期列表（包含详细延期信息）
- ✅ **验证痛点1已解决：各部门可以看到彼此的进度**

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

### 3.4 实时进度聚合测试（2个场景）

#### TC017: 验证任务→项目进度聚合
**测试步骤：**
1. 记录项目当前进度
2. 更新一个任务进度从30%→80%
3. 再次查询项目进度
4. 计算预期进度 = (所有任务进度之和) / 任务数

**预期结果：**
- ✅ 项目进度自动重新计算
- ✅ 计算结果与手动计算一致
- ✅ **验证痛点2已解决：进度实时反馈到项目**

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

#### TC018: 验证健康度自动计算
**测试步骤：**
1. 创建10个任务
2. 标记其中3个为延期（30%）
3. 查询项目健康度

**预期结果：**
- ✅ 项目健康度自动降为H3（阻塞）
  - 因为延期率30% > 25%阈值
- ✅ 修复2个延期任务后，健康度恢复为H2（风险）
  - 延期率降为10%

**实际结果：** _待填写_
**状态：** ⏳ 待测试

---

## 4. 测试执行记录

### 4.1 缺陷记录模板

| 缺陷ID | 优先级 | 模块 | 标题 | 描述 | 重现步骤 | 状态 |
|--------|--------|------|------|------|----------|------|
| BUG001 | P1 | 进度更新 | ... | ... | ... | Open |

**缺陷优先级定义：**
- **P0 (Critical)**: 系统崩溃、数据丢失、安全漏洞
- **P1 (Major)**: 核心功能无法使用
- **P2 (Minor)**: 功能可用但有明显问题
- **P3 (Trivial)**: UI问题、文字错误

### 4.2 测试进度跟踪

| 日期 | 测试用例数 | 通过 | 失败 | 阻塞 | 待测试 | 通过率 |
|------|-----------|------|------|------|--------|--------|
| 2026-01-08 | 18 | 0 | 0 | 0 | 18 | 0% |
| 2026-01-09 | 18 | TBD | TBD | TBD | TBD | TBD |
| 2026-01-10 | 18 | TBD | TBD | TBD | TBD | TBD |

---

## 5. 测试数据准备脚本

### 5.1 创建测试用户

```sql
-- 插入测试用户
INSERT INTO users (username, real_name, password_hash, department, is_active) VALUES
('engineer_mech', '张工', '$hashed_password', '机械部', 1),
('engineer_elec', '李工', '$hashed_password', '电气部', 1),
('engineer_test', '王工', '$hashed_password', '测试部', 1),
('pm_zhang', '张经理', '$hashed_password', 'PMO', 1),
('manager_mech', '赵部长', '$hashed_password', '机械部', 1);
```

### 5.2 创建测试项目和任务

```python
# test_data_setup.py
# 创建测试项目和初始任务的Python脚本（待实现）
```

---

## 6. 验收标准检查清单

### 6.1 功能验收

- [ ] **TC001-TC009**: 工程师端9个功能全部测试通过
- [ ] **TC010-TC013**: PM审批端4个功能全部测试通过
- [ ] **TC014-TC016**: 跨部门协作3个功能全部测试通过
- [ ] **TC017-TC018**: 进度聚合2个场景验证通过

### 6.2 痛点解决验收

- [ ] **痛点1解决验证**: TC016测试通过，部门经理能够清楚看到所有部门的进度
- [ ] **痛点2解决验证**: TC017测试通过，任务进度更新立即反映到项目进度

### 6.3 质量验收

- [ ] 核心功能测试通过率 ≥ 95%
- [ ] 无P0级别缺陷
- [ ] P1级别缺陷 ≤ 2个
- [ ] 所有已知缺陷已记录并分类

### 6.4 性能验收

- [ ] API响应时间 < 1秒（90%请求）
- [ ] 文件上传 < 5秒（10MB文件）
- [ ] 跨部门进度视图查询 < 2秒

### 6.5 用户体验验收

- [ ] 用户满意度问卷平均分 ≥ 4.0/5.0
- [ ] 至少3个部门的用户参与测试
- [ ] 收集至少10条用户反馈

---

## 7. UAT测试检查表

### 测试前准备
- [ ] 测试环境已部署
- [ ] 数据库已迁移
- [ ] 测试账号已创建
- [ ] 测试数据已准备
- [ ] Swagger UI可访问
- [ ] 文件上传目录已创建

### 测试执行
- [ ] 所有18个测试用例已执行
- [ ] 缺陷已记录和分类
- [ ] 测试结果已记录
- [ ] 截图/录屏已保存（关键场景）

### 测试后整理
- [ ] 生成测试报告
- [ ] 缺陷修复计划制定
- [ ] 用户反馈整理
- [ ] 下一步计划确定

---

## 8. 联系方式

**技术支持：** 开发团队
**测试负责人：** QA团队
**业务负责人：** PMO

**测试问题报告：** [内部问题跟踪系统]

---

**文档版本：** 1.0
**创建日期：** 2026-01-07
**最后更新：** 2026-01-07
