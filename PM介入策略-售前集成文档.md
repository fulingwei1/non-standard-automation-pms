# PM介入策略 - 售前工单集成文档

**集成完成时间**: 2026-02-15  
**集成范围**: 售前支持工单创建流程  
**状态**: ✅ 后端已完成，前端待实现

---

## 📋 集成概述

PM介入策略已成功集成到售前工单创建流程中。当售前工程师创建工单时，系统会自动判断项目是否需要PM提前介入，并在前端显示提示。

---

## 🎯 核心功能

### 自动判断逻辑

系统会根据以下6个风险因素自动判断：

1. ✅ **大项目**：项目金额 ≥ 100万
2. ✅ **以前没做过**：首次承接该类型项目
3. ✅ **有失败经验**：相似项目有过失败案例
4. ✅ **经验不足**：相似项目 < 3个
5. ✅ **无标准方案**：无标准化方案模板
6. ✅ **技术创新**：涉及新技术研发

**判断规则**：满足 ≥2个 → **PM提前介入**

---

## 🔄 工作流程

### 售前工程师创建工单

```
1. 填写工单基本信息（标题、描述等）
   ↓
2. 填写PM介入判断所需字段：
   - 预估项目金额（万元）
   - 客户行业
   - 是否首次承接该类型
   - 是否有标准化方案
   - 技术创新点（可选）
   ↓
3. 提交工单
   ↓
4. 系统自动判断PM介入需求
   ↓
5. 返回判断结果给前端
   ↓
6. 前端显示提示（如果需要PM介入）
```

### PMO收到通知（自动）

如果系统判断需要PM提前介入：

```
1. 系统记录判断结果到数据库
   ↓
2. 发送通知给PMO（企业微信/钉钉）
   ↓
3. PMO负责人安排PM
   ↓
4. PM参与技术评审和需求调研
```

---

## 🛠️ 后端实现细节

### 1. 数据库字段（已添加）

在 `presale_support_ticket` 表中新增字段：

| 字段名 | 类型 | 说明 |
|-------|------|------|
| `pm_involvement_required` | Boolean | 是否需要PM提前介入 |
| `pm_involvement_risk_level` | String(20) | 风险等级（高/低） |
| `pm_involvement_risk_factors` | JSON | 风险因素列表 |
| `pm_involvement_checked_at` | DateTime | PM介入检查时间 |
| `pm_assigned` | Boolean | PM是否已分配 |
| `pm_user_id` | Integer | 分配的PM用户ID |
| `pm_assigned_at` | DateTime | PM分配时间 |

### 2. API接口（已更新）

#### POST /api/v1/presale/tickets

**请求体**（新增字段）:
```json
{
  "title": "SMT贴片生产线自动化项目",
  "ticket_type": "TECHNICAL_SUPPORT",
  "description": "客户需求...",
  "customer_name": "某汽车电子公司",
  
  // 新增：PM介入判断所需字段
  "estimated_amount": 150,
  "industry": "汽车电子",
  "is_first_time": false,
  "has_standard_solution": false,
  "innovation_points": ["视觉检测新算法", "多工位协同"]
}
```

**响应体**（新增字段）:
```json
{
  "id": 1,
  "ticket_no": "PS202602150001",
  "title": "SMT贴片生产线自动化项目",
  "status": "PENDING",
  
  // 新增：PM介入判断结果
  "pm_involvement_required": true,
  "pm_involvement_risk_level": "高",
  "pm_involvement_risk_factors": [
    "大型项目（150万）",
    "相似项目有失败经验（1次）",
    "相似项目经验不足（仅2个）",
    "无标准化方案模板",
    "涉及技术创新（2项）"
  ],
  "pm_involvement_checked_at": "2026-02-15T13:46:00",
  "pm_assigned": false,
  "pm_user_id": null,
  "pm_assigned_at": null,
  
  "created_at": "2026-02-15T13:46:00",
  ...
}
```

### 3. 核心服务

使用 `app/services/pm_involvement_service.py` 中的 `PMInvolvementService`：

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
    "技术创新点": ["视觉检测新算法"]
}

# 调用判断服务
result = PMInvolvementService.judge_pm_involvement_timing(project_data)

# 结果示例
{
    "建议": "PM提前介入",
    "介入阶段": "技术评审/需求调研阶段",
    "风险等级": "高",
    "风险因素数": 5,
    "原因": [...],
    "下一步行动": [...],
    "需要PM审核": True,
    "紧急程度": "高"
}
```

---

## 💻 前端集成指南

### 1. 工单创建表单（需添加字段）

在工单创建表单中添加以下字段：

```jsx
// 售前工单创建表单
<Form>
  {/* 原有字段 */}
  <FormField name="title" label="工单标题" />
  <FormField name="description" label="详细描述" />
  <FormField name="customer_name" label="客户名称" />
  
  {/* 新增：PM介入判断所需字段 */}
  <FormField 
    name="estimated_amount" 
    label="预估项目金额（万元）" 
    type="number"
    placeholder="例如：150"
    help="用于判断是否需要PM提前介入"
  />
  
  <FormField 
    name="industry" 
    label="客户行业" 
    type="select"
    options={["汽车电子", "消费电子", "医疗器械", "..."]}
  />
  
  <FormField 
    name="is_first_time" 
    label="是否首次承接该类型项目" 
    type="checkbox"
  />
  
  <FormField 
    name="has_standard_solution" 
    label="是否有标准化方案" 
    type="checkbox"
  />
  
  <FormField 
    name="innovation_points" 
    label="技术创新点（可选）" 
    type="tags"
    placeholder="例如：视觉检测新算法"
  />
</Form>
```

### 2. 创建成功后显示提示

当工单创建成功后，检查 `pm_involvement_required` 字段：

```jsx
const handleCreateTicket = async (formData) => {
  const response = await api.post('/api/v1/presale/tickets', formData);
  
  // 检查是否需要PM提前介入
  if (response.data.pm_involvement_required) {
    // 显示警告提示
    Modal.warning({
      title: '⚠️ 该项目建议PM提前介入',
      content: (
        <div>
          <p>项目：{response.data.title}</p>
          <p>客户：{response.data.customer_name}</p>
          <p>金额：{formData.estimated_amount}万</p>
          <br />
          <p><strong>风险因素（{response.data.pm_involvement_risk_factors.length}个）：</strong></p>
          <ul>
            {response.data.pm_involvement_risk_factors.map((factor, i) => (
              <li key={i}>✗ {factor}</li>
            ))}
          </ul>
          <br />
          <p><strong>建议操作：</strong></p>
          <ol>
            <li>立即通知PMO负责人安排PM</li>
            <li>组织技术评审会（邀请PM参加）</li>
            <li>PM参与客户需求调研</li>
            <li>PM审核成本和工期估算</li>
          </ol>
        </div>
      ),
      width: 600,
      okText: '我已知悉',
      onOk: () => {
        // 跳转到工单详情页
        navigate(`/presale/tickets/${response.data.id}`);
      }
    });
  } else {
    // 常规成功提示
    message.success('工单创建成功');
    navigate(`/presale/tickets/${response.data.id}`);
  }
};
```

### 3. 工单列表显示标记

在工单列表中，对需要PM介入的工单添加视觉标记：

```jsx
<Table
  dataSource={tickets}
  columns={[
    {
      title: '工单编号',
      dataIndex: 'ticket_no',
      render: (text, record) => (
        <div>
          {record.pm_involvement_required && (
            <Tag color="orange" style={{ marginRight: 8 }}>
              ⚠️ 需PM介入
            </Tag>
          )}
          {text}
        </div>
      )
    },
    // 其他列...
  ]}
/>
```

### 4. 工单详情页显示PM介入信息

在工单详情页添加PM介入信息卡片：

```jsx
{ticket.pm_involvement_required && (
  <Alert
    message="⚠️ 该项目需要PM提前介入"
    description={
      <div>
        <p><strong>风险等级：</strong>{ticket.pm_involvement_risk_level}</p>
        <p><strong>风险因素：</strong></p>
        <ul>
          {ticket.pm_involvement_risk_factors.map((factor, i) => (
            <li key={i}>{factor}</li>
          ))}
        </ul>
        <Divider />
        <p><strong>PM分配状态：</strong>
          {ticket.pm_assigned ? (
            <Tag color="success">已分配</Tag>
          ) : (
            <Tag color="warning">待分配</Tag>
          )}
        </p>
        {ticket.pm_assigned && (
          <p><strong>分配时间：</strong>{formatDateTime(ticket.pm_assigned_at)}</p>
        )}
      </div>
    }
    type="warning"
    showIcon
    style={{ marginBottom: 16 }}
  />
)}
```

---

## 📲 通知机制（待实现）

### 企业微信通知

当判断需要PM提前介入时，系统会发送企业微信通知：

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

### TODO: 通知集成

需要在 `app/api/v1/endpoints/presale/tickets/crud.py` 中添加实际的通知调用：

```python
# 当前是TODO状态
# TODO: 调用企业微信/钉钉通知接口
# send_wechat_notification(notification_message)

# 需要替换为：
from app.utils.wechat import send_wechat_notification
send_wechat_notification(
    message=notification_message,
    mentioned_list=['PMO负责人']  # 或具体的企业微信用户ID
)
```

---

## 🧪 测试验证

### 1. 数据库迁移

```bash
cd ~/.openclaw/workspace/non-standard-automation-pms

# 运行迁移
alembic upgrade head

# 或使用Python
python -c "from app.models.base import engine, Base; Base.metadata.create_all(engine)"
```

### 2. API测试

```bash
# 创建工单（高风险项目）
curl -X POST http://localhost:8000/api/v1/presale/tickets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "SMT贴片生产线自动化项目",
    "ticket_type": "TECHNICAL_SUPPORT",
    "description": "客户需求详细描述",
    "customer_name": "某汽车电子公司",
    "estimated_amount": 150,
    "industry": "汽车电子",
    "is_first_time": false,
    "has_standard_solution": false,
    "innovation_points": ["视觉检测新算法", "多工位协同"]
  }'

# 预期响应包含：
# "pm_involvement_required": true
# "pm_involvement_risk_level": "高"
# "pm_involvement_risk_factors": [...]
```

### 3. 前端测试

1. 登录系统
2. 进入"售前支持" → "创建工单"
3. 填写工单信息（包含PM介入判断字段）
4. 提交
5. 查看是否显示PM介入提示弹窗

---

## 📊 数据流程图

```
┌─────────────────┐
│ 售前工程师      │
│ 创建工单        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 前端表单                            │
│ - 基本信息                          │
│ - PM介入判断字段（新增）            │
│   * 预估金额                        │
│   * 客户行业                        │
│   * 是否首次做                      │
│   * 是否有标准方案                  │
│   * 技术创新点                      │
└────────┬────────────────────────────┘
         │ POST /api/v1/presale/tickets
         ▼
┌─────────────────────────────────────┐
│ 后端API                             │
│ 1. 验证基本信息                     │
│ 2. 调用PMInvolvementService判断     │
│ 3. 保存工单+判断结果                │
│ 4. 发送通知（如需PM介入）           │
└────────┬────────────────────────────┘
         │
         ├─────────────┬──────────────┐
         ▼             ▼              ▼
    ┌────────┐   ┌─────────┐   ┌──────────┐
    │ 数据库 │   │ 企业微信│   │ 返回前端 │
    │ 保存   │   │ 通知PMO │   │ 显示提示 │
    └────────┘   └─────────┘   └──────────┘
```

---

## ✅ 集成检查清单

### 后端（已完成）
- [x] ✅ 数据库模型更新（添加PM介入字段）
- [x] ✅ 数据库迁移文件
- [x] ✅ Schema更新（TicketCreate + TicketResponse）
- [x] ✅ API集成（工单创建时调用判断）
- [x] ✅ PM介入判断服务
- [ ] ⏳ 通知机制集成（企业微信/钉钉）

### 前端（待实现）
- [ ] ⏳ 工单创建表单添加PM介入判断字段
- [ ] ⏳ 创建成功后显示PM介入提示弹窗
- [ ] ⏳ 工单列表显示PM介入标记
- [ ] ⏳ 工单详情页显示PM介入信息
- [ ] ⏳ PM分配功能（PMO使用）

---

## 📚 相关文档

- `PM介入策略设计.md` - 完整的策略设计文档
- `PM介入策略-使用指南.md` - 使用指南
- `app/services/pm_involvement_service.py` - 核心服务代码
- `app/api/v1/endpoints/pm_involvement.py` - 独立API端点

---

## 💡 后续优化建议

1. **历史数据完善**
   - 查询历史相似项目数量
   - 查询失败项目数量
   - 更精准的判断

2. **通知渠道**
   - 集成企业微信API
   - 集成钉钉API
   - 邮件通知备选

3. **PM分配功能**
   - PMO管理界面
   - PM负载查看
   - 一键分配PM

4. **数据分析**
   - PM介入效果跟踪
   - 成功率对比
   - 持续优化规则

---

**集成完成时间**: 2026-02-15 13:50  
**文档作者**: AI Assistant  
**状态**: ✅ 后端完成，前端待实现
