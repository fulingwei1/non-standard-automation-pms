# PM介入策略 - 使用指南

## 📌 功能说明

自动判断项目是否需要PM提前介入，避免高风险项目承诺无法交付。

---

## 🎯 判断规则（符哥2026-02-15确认）

### 6大风险因素：

1. **大项目**：≥ 100万
2. **以前没做过**：首次承接该类型
3. **有失败经验**：相似项目有过失败案例
4. **经验不足**：相似项目 < 3个
5. **无标准方案**：无标准化方案模板
6. **技术创新**：涉及新技术研发

### 判断逻辑：

✅ **满足 ≥2个** → **PM提前介入**（技术评审/需求调研阶段）  
✅ **满足 <2个** → **PM签约后介入**（合同签订后）

---

## 🚀 使用方式

### 方式1：API调用（推荐）

**端点**：`POST /api/v1/pm-involvement/judge-pm-involvement`

**请求示例**：
```bash
curl -X POST "http://localhost:8000/api/v1/pm-involvement/judge-pm-involvement" \
  -H "Content-Type: application/json" \
  -d '{
    "项目金额": 150,
    "项目类型": "SMT贴片生产线",
    "行业": "汽车电子",
    "是否首次做": false,
    "历史相似项目数": 2,
    "失败项目数": 1,
    "是否有标准方案": false,
    "技术创新点": ["视觉检测新算法", "多工位协同"]
  }'
```

**响应示例**：
```json
{
  "建议": "PM提前介入",
  "介入阶段": "技术评审/需求调研阶段",
  "风险等级": "高",
  "风险因素数": 5,
  "原因": [
    "大型项目（150万）",
    "相似项目有失败经验（1次）",
    "相似项目经验不足（仅2个）",
    "无标准化方案模板",
    "涉及技术创新（2项）"
  ],
  "下一步行动": [
    "1. 立即通知PMO负责人安排PM",
    "2. 组织技术评审会（邀请PM参加）",
    "3. PM参与客户需求调研",
    "4. PM审核成本和工期估算"
  ],
  "需要PM审核": true,
  "紧急程度": "高"
}
```

---

### 方式2：Python代码调用

```python
from app.services.pm_involvement_service import PMInvolvementService

# 准备项目数据
project_data = {
    "项目金额": 150,
    "项目类型": "SMT贴片生产线",
    "行业": "汽车电子",
    "是否首次做": False,
    "历史相似项目数": 2,
    "失败项目数": 1,
    "是否有标准方案": False,
    "技术创新点": ["视觉检测新算法", "多工位协同"]
}

# 判断PM介入时机
result = PMInvolvementService.judge_pm_involvement_timing(project_data)

# 打印结果
print(f"建议：{result['建议']}")
print(f"风险等级：{result['风险等级']}")
print(f"原因：{', '.join(result['原因'])}")
```

---

### 方式3：售前系统集成

**集成点1**：工单创建时

```javascript
// 售前工程师创建工单时，系统自动评估
async function onCreatePresaleTicket(formData) {
  // 1. 提交工单数据
  const ticket = await createTicket(formData);
  
  // 2. 自动判断PM介入时机
  const pmResult = await fetch('/api/v1/pm-involvement/judge-pm-involvement', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      项目金额: formData.estimatedAmount,
      项目类型: formData.projectType,
      行业: formData.industry,
      是否首次做: formData.isFirstTime,
      历史相似项目数: formData.similarProjectCount,
      失败项目数: formData.failedProjectCount,
      是否有标准方案: formData.hasStandardSolution,
      技术创新点: formData.innovationPoints
    })
  }).then(res => res.json());
  
  // 3. 如果需要PM提前介入，弹窗提示
  if (pmResult.需要PM审核) {
    showAlert({
      type: 'warning',
      title: '⚠️ 该项目建议PM提前介入',
      message: `
        项目：${formData.projectName}
        金额：${formData.estimatedAmount}万
        
        风险因素（${pmResult.风险因素数}个）：
        ${pmResult.原因.map(r => '✗ ' + r).join('\n')}
        
        建议操作：
        ${pmResult.下一步行动.join('\n')}
      `,
      buttons: ['确认已通知PMO', '稍后处理']
    });
  }
}
```

**集成点2**：方案评审阶段

```javascript
// 方案设计完成后，提醒再次确认
async function onSolutionDesignComplete(ticketId) {
  const pmResult = await fetch(`/api/v1/pm-involvement/auto-judge/${ticketId}`)
    .then(res => res.json());
  
  if (pmResult.需要PM审核) {
    // 发送企业微信/钉钉通知给PMO负责人
    await sendNotificationToPMO({
      type: 'pm_involvement_required',
      ticketId: ticketId,
      message: pmResult
    });
  }
}
```

**集成点3**：报价前强制检查

```javascript
// 报价前，检查是否已PM审核
async function beforeQuotation(ticketId) {
  const ticket = await getTicket(ticketId);
  const pmResult = await fetch(`/api/v1/pm-involvement/auto-judge/${ticketId}`)
    .then(res => res.json());
  
  if (pmResult.需要PM审核 && !ticket.pmApproved) {
    // 阻断报价流程
    showError({
      title: '❌ 该项目需PM审核后才能报价',
      message: `
        请先完成以下步骤：
        1. 通知PMO安排PM
        2. 组织技术评审会
        3. PM审核成本和工期
        4. PM签字确认
      `
    });
    return false;
  }
  
  return true;
}
```

---

## 📊 数据追踪

系统会自动记录每个项目的PM介入时机，用于后续分析：

```sql
-- PM介入时机与项目成功率相关性分析
SELECT 
    pm_involvement_timing,
    COUNT(*) as 项目总数,
    SUM(CASE WHEN 项目状态='验收通过' THEN 1 ELSE 0 END) as 成功数,
    ROUND(AVG(毛利率), 2) as 平均毛利率,
    ROUND(AVG(工期偏差天数), 1) as 平均工期偏差
FROM projects
GROUP BY pm_involvement_timing;
```

**预期效果**：
- 高风险项目提前介入 → 成功率更高、工期偏差更小
- 低风险项目按时介入 → 资源利用率更高

---

## 🔔 通知机制

### 企业微信通知示例

```
⚠️ 【高风险项目】需PM提前介入

项目：SMT贴片生产线自动化改造
客户：某汽车电子公司
金额：150万

风险因素（5个）：
✗ 大型项目（150万）
✗ 相似项目有失败经验（1次）
✗ 相似项目经验不足（仅2个）
✗ 无标准化方案模板
✗ 涉及技术创新（2项）

建议行动：
1. 立即通知PMO负责人安排PM
2. 组织技术评审会（邀请PM参加）
3. PM参与客户需求调研
4. PM审核成本和工期估算

紧急程度：高
请PMO负责人尽快安排PM！
```

---

## 🎯 最佳实践

### 1. 售前工程师
- ✅ 创建工单时如实填写项目信息
- ✅ 看到提示后及时通知PMO
- ✅ 配合PM进行技术评审

### 2. PMO负责人
- ✅ 收到通知后优先安排PM
- ✅ 根据PM专长和负载合理分配
- ✅ 追踪PM介入效果

### 3. 项目经理
- ✅ 提前介入时重点评估技术可行性
- ✅ 审核成本和工期估算
- ✅ 识别关键风险点

---

## 📝 常见问题

**Q1：系统判断PM需要提前介入，但我认为不需要，怎么办？**

A：系统判断仅供参考，最终决策权在PMO负责人。可以记录"人工判定不需要"的原因，用于后续优化规则。

**Q2：风险因素阈值可以调整吗？**

A：可以。在 `PMInvolvementService` 中修改：
```python
LARGE_PROJECT_THRESHOLD = 100  # 大项目金额阈值（万元）
SIMILAR_PROJECT_MIN = 3        # 相似项目数量最低要求
RISK_FACTOR_THRESHOLD = 2      # 风险因素触发数
```

**Q3：如何优化判断准确率？**

A：定期分析数据，对比"系统判断 vs 实际结果"，持续调整规则。

---

## 📈 预期效果

1. **避免风险**：高风险项目100%提前介入
2. **提高效率**：低风险项目PM不过早介入，节约30%+资源
3. **决策透明**：AI自动判断，消除主观因素
4. **持续优化**：基于数据反馈，动态调整规则

---

**文档版本**：v1.0  
**最后更新**：2026-02-15  
**策略来源**：符哥确认的PM介入策略
