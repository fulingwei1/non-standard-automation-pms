# AI客户情绪分析模块 - 用户使用手册

## 目录

1. [模块介绍](#模块介绍)
2. [核心功能](#核心功能)
3. [快速开始](#快速开始)
4. [功能详解](#功能详解)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)
7. [故障排查](#故障排查)

---

## 模块介绍

### 什么是AI客户情绪分析模块？

AI客户情绪分析模块是一个基于OpenAI GPT-4的智能分析系统，它能够：

- 📊 **自动分析客户情绪** - 识别客户沟通中的积极、中性、消极情绪
- 🎯 **评估购买意向** - 量化客户的购买意愿，评分0-100
- ⚠️ **预警流失风险** - 提前识别可能流失的客户
- ⏰ **推荐跟进时机** - 智能推荐最佳跟进时间和内容
- 📈 **追踪情绪趋势** - 记录并分析客户情绪变化曲线

### 适用场景

- 销售团队日常客户跟进
- 售前顾问客户沟通分析
- 客户成功团队流失预警
- 管理层客户健康度监控

---

## 核心功能

### 1. 购买意向识别

**功能说明**：分析客户沟通记录，识别购买信号并打分

**识别指标**：
- ✅ **积极信号**：询问价格、要求演示、提及预算、时间紧迫等
- 🔶 **中性信号**：了解功能、对比产品、咨询案例等
- ❌ **消极信号**：价格异议、功能不符、竞品倾向等

**评分标准**：
- 0-30分：低意向，可能只是初步了解
- 31-60分：中等意向，有兴趣但仍在考虑
- 61-80分：较高意向，大概率会购买
- 81-100分：高意向，建议立即促成

### 2. 客户流失预警

**功能说明**：识别流失风险信号，预测流失概率

**风险信号**：
- 🔴 **高风险**：长时间未联系、频繁抱怨、回复速度变慢、明确提及竞品
- 🟡 **中风险**：沟通频率降低、异议增多、态度冷淡
- 🟢 **低风险**：积极互动、按时回复、表现出兴趣

**预警等级**：
- **高风险 (High)**: 需要立即介入，制定挽回策略
- **中风险 (Medium)**: 需要关注，增加跟进频率
- **低风险 (Low)**: 保持现状，正常跟进

### 3. 跟进时机提醒

**功能说明**：基于客户情绪和行为，推荐最佳跟进时间

**优先级说明**：
- **高优先级 (High)**: 2小时内跟进
  - 客户购买意向高（>80分）
  - 客户有紧急需求
  - 流失风险突然升高
  
- **中优先级 (Medium)**: 1天内跟进
  - 客户情绪正常
  - 保持沟通节奏
  
- **低优先级 (Low)**: 3天内跟进
  - 客户暂无明确需求
  - 保持长期关系

### 4. 情绪趋势分析

**功能说明**：记录客户情绪变化，识别关键转折点

**趋势图示例**：
```
情绪 ^
     |     ●────────●
 80  |    /          \
     |   /            \
 50  |  ●              ●────●
     |
 20  |
     +─────────────────────> 时间
    1/1  1/5  1/10  1/15  1/20
```

**关键转折点**：
- **峰值 (Peak)**: 情绪或意向的高点，值得关注的积极时刻
- **谷值 (Valley)**: 情绪或意向的低点，可能是客户遇到问题

---

## 快速开始

### 步骤1: 环境配置

确保已配置OpenAI API密钥：

```bash
# 设置环境变量
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export OPENAI_MODEL="gpt-4"  # 可选，默认gpt-4
```

### 步骤2: 第一次情绪分析

```python
import requests

# API基础URL
BASE_URL = "http://your-api-domain.com/api/v1/presale/ai"

# 分析客户情绪
response = requests.post(
    f"{BASE_URL}/analyze-emotion",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "presale_ticket_id": 1,
        "customer_id": 100,
        "communication_content": "我对你们的产品很感兴趣，想了解一下详细的价格和功能配置"
    }
)

result = response.json()
print(f"情绪类型: {result['sentiment']}")
print(f"购买意向: {result['purchase_intent_score']}分")
print(f"流失风险: {result['churn_risk']}")
```

### 步骤3: 查看跟进建议

```python
# 获取跟进推荐
response = requests.post(
    f"{BASE_URL}/recommend-follow-up",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "presale_ticket_id": 1,
        "customer_id": 100
    }
)

reminder = response.json()
print(f"推荐时间: {reminder['recommended_time']}")
print(f"优先级: {reminder['priority']}")
print(f"建议内容: {reminder['follow_up_content']}")
print(f"理由: {reminder['reason']}")
```

---

## 功能详解

### 情绪分析实战

**场景1: 识别高意向客户**

客户消息:
> "我们公司正在寻找一款能够提升销售效率的系统，预算在10-15万之间，希望能在本月内完成采购。能否安排一次详细的产品演示？"

分析结果:
```json
{
  "sentiment": "positive",
  "purchase_intent_score": 92.0,
  "churn_risk": "low",
  "emotion_factors": {
    "positive_keywords": ["正在寻找", "预算", "本月内", "产品演示"],
    "urgency_signals": ["本月内"],
    "budget_mentioned": true
  }
}
```

**行动建议**: 高优先级，立即联系安排演示，准备报价方案

---

**场景2: 流失预警**

客户消息:
> "我们最近在考虑几家供应商的方案，你们的价格确实有点贵。另外，我看到你们的竞争对手XX公司的产品功能好像更全面一些。"

分析结果:
```json
{
  "sentiment": "negative",
  "purchase_intent_score": 35.0,
  "churn_risk": "high",
  "emotion_factors": {
    "concerns": ["价格", "功能"],
    "competitor_mentioned": "XX公司",
    "comparison_signals": true
  }
}
```

**行动建议**: 紧急跟进，准备价值对比材料，强调差异化优势

---

### 批量分析使用

**适用场景**：
- 每日定时分析所有活跃客户
- 周度客户健康度报告
- 月度流失风险排查

**示例代码**：

```python
# 批量分析100个客户
customer_ids = [100, 101, 102, ..., 199]

response = requests.post(
    f"{BASE_URL}/batch-analyze-customers",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "customer_ids": customer_ids,
        "analysis_type": "full"
    }
)

result = response.json()

# 筛选需要关注的客户
attention_needed = [
    summary for summary in result['summaries']
    if summary['needs_attention']
]

# 按流失风险排序
high_risk_customers = [
    summary for summary in attention_needed
    if summary['churn_risk'] == 'high'
]

print(f"需要关注的客户: {len(attention_needed)}个")
print(f"高流失风险: {len(high_risk_customers)}个")

# 生成行动列表
for customer in high_risk_customers:
    print(f"客户ID: {customer['customer_id']}")
    print(f"行动: {customer['recommended_action']}")
    print("---")
```

---

### 情绪趋势追踪

**查看客户情绪变化**：

```python
# 获取情绪趋势
response = requests.get(
    f"{BASE_URL}/emotion-trend/1",  # 工单ID=1
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

trend = response.json()

# 打印趋势数据
for point in trend['trend_data']:
    print(f"{point['date']}: {point['sentiment']} (意向: {point['intent_score']})")

# 关注关键转折点
for turning_point in trend['key_turning_points']:
    print(f"转折点 ({turning_point['type']}): {turning_point['date']}")
    print(f"  情绪: {turning_point['sentiment']}, 意向: {turning_point['intent_score']}")
```

**趋势解读**：

1. **持续上升**: 客户信心增强，购买意愿提升，保持现有策略
2. **持续下降**: 客户兴趣减弱，需要分析原因并调整策略
3. **波动频繁**: 客户处于犹豫期，需要提供更多决策依据
4. **突然下跌**: 可能遇到问题或竞品干扰，需要立即介入

---

## 最佳实践

### 1. 定期分析

**建议频率**：
- 活跃客户：每次沟通后立即分析
- 跟进中客户：每周批量分析1-2次
- 潜在流失客户：每天监控

### 2. 结合人工判断

AI分析是辅助工具，最终决策应结合：
- ✅ 客户历史行为
- ✅ 行业经验
- ✅ 具体沟通场景
- ✅ 业务实际情况

### 3. 优化沟通内容

**提高分析准确性**：
- 完整记录客户沟通内容
- 包含客户的原话而非总结
- 记录关键时间点和事件
- 保留情绪化表达

**示例对比**：

❌ **不好的记录**: "客户说考虑一下"

✅ **好的记录**: "客户原话：'你们的产品功能确实不错，但价格比我们预算高了20%左右。我需要和老板商量一下，可能还要对比其他几家供应商的方案。'"

### 4. 跟进提醒管理

**高效使用提醒**：
- 每天早上查看高优先级提醒
- 及时处理或忽略已过期提醒
- 根据实际情况调整跟进计划

```python
# 获取今日高优先级提醒
response = requests.get(
    f"{BASE_URL}/follow-up-reminders?status=pending&priority=high&limit=50",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

reminders = response.json()['reminders']

for reminder in reminders:
    # 判断是否需要立即处理
    if needs_immediate_action(reminder):
        handle_reminder(reminder)
    else:
        # 忽略不适用的提醒
        requests.post(
            f"{BASE_URL}/dismiss-reminder/{reminder['id']}",
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        )
```

### 5. 流失预警响应

**高风险客户处理流程**：

1. **确认风险**: 核实最近沟通情况
2. **分析原因**: 查看情绪因素和趋势数据
3. **制定策略**: 针对性解决客户疑虑
4. **立即行动**: 2小时内联系客户
5. **持续跟踪**: 每天监控情绪变化

**挽回策略模板**：

```
高风险因素: 价格异议
挽回策略:
1. 准备ROI分析材料，展示长期价值
2. 提供分期付款方案
3. 分享同行业成功案例
4. 限时优惠促进决策
```

---

## 常见问题

### Q1: 情绪分析不准确怎么办？

**A**: 可能的原因和解决方案：

1. **沟通内容太短**: 建议至少50字以上才能准确分析
2. **缺少上下文**: 提供更完整的对话记录
3. **特殊行业术语**: 可能需要微调AI模型
4. **多轮对话混淆**: 分别分析每次沟通

### Q2: 购买意向评分偏差较大？

**A**: 评分是相对参考值，建议：

- 不要过度依赖绝对分数
- 关注趋势变化而非单次评分
- 结合流失风险等多维度判断
- 根据行业特点调整判断标准

### Q3: 跟进时机推荐不合理？

**A**: 跟进时机基于以下因素：

- 客户情绪和意向评分
- 历史沟通频率
- 流失风险等级

如果不适用，可以：
- 忽略该提醒
- 自定义跟进计划
- 反馈给系统优化算法

### Q4: 批量分析速度慢？

**A**: 优化建议：

- 控制每批客户数量（建议≤50）
- 使用异步任务处理大批量
- 避免频繁调用，建议定时批量
- 考虑升级API套餐提高并发限制

### Q5: API调用超时？

**A**: OpenAI API响应时间可能较长：

- 设置合理的超时时间（建议30秒）
- 实现重试机制
- 监控API状态
- 考虑使用更快的模型（如gpt-3.5-turbo）

---

## 故障排查

### 问题1: API返回500错误

**排查步骤**：

1. 检查OpenAI API密钥是否正确
   ```bash
   echo $OPENAI_API_KEY
   ```

2. 检查API配额是否用尽
   - 登录OpenAI控制台查看用量

3. 查看服务日志
   ```bash
   tail -f logs/app.log | grep "ai_emotion"
   ```

4. 测试OpenAI连接
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

### 问题2: 数据库连接失败

**排查步骤**：

1. 检查数据库服务状态
   ```bash
   systemctl status mysql
   ```

2. 验证数据库连接配置
   ```bash
   # 查看环境变量
   env | grep DATABASE
   ```

3. 测试数据库连接
   ```bash
   mysql -h localhost -u user -p database
   ```

4. 检查表是否存在
   ```sql
   SHOW TABLES LIKE 'presale_ai%';
   ```

### 问题3: 情绪分析结果全部为默认值

**原因**: OpenAI API调用失败，系统使用了默认值

**解决方案**：

1. 检查网络连接
2. 验证API密钥权限
3. 查看详细错误日志
4. 尝试降级到备用模型

### 问题4: 批量分析部分失败

**正常现象**: 批量分析会跳过异常客户

**查看详细信息**：
```python
result = response.json()
print(f"成功: {result['success_count']}, 失败: {result['failed_count']}")

# 检查日志获取失败原因
```

---

## 技术支持

**遇到问题？**

1. 📖 查看[API文档](./ai_emotion_analysis_api.md)
2. 🔧 查看[模型调优文档](./ai_emotion_model_tuning.md)
3. 💬 联系技术支持团队
4. 📧 发送邮件到: support@example.com

**反馈建议？**

我们欢迎您的反馈，帮助我们改进系统：
- 分析准确性问题
- 功能改进建议
- 使用场景分享
- Bug报告

---

## 附录

### 术语表

| 术语 | 说明 |
|------|------|
| 情绪 (Sentiment) | 客户沟通中表现出的情感倾向 |
| 购买意向 (Purchase Intent) | 客户购买产品的意愿强度 |
| 流失风险 (Churn Risk) | 客户可能流失的概率 |
| 转折点 (Turning Point) | 客户情绪或意向发生显著变化的时刻 |
| 跟进时机 (Follow-up Timing) | 最适合联系客户的时间点 |

### 评分对照表

**购买意向评分**:
| 分数范围 | 等级 | 描述 | 建议行动 |
|---------|------|------|----------|
| 0-30 | 低 | 初步了解阶段 | 提供基础信息，培育需求 |
| 31-60 | 中 | 有兴趣但犹豫 | 提供案例，解答疑问 |
| 61-80 | 较高 | 认真考虑中 | 加快推进，提供试用/演示 |
| 81-100 | 高 | 准备购买 | 立即跟进，促成交易 |

**流失风险评分**:
| 分数范围 | 等级 | 描述 | 建议行动 |
|---------|------|------|----------|
| 0-40 | 低 | 关系稳定 | 保持现状，正常跟进 |
| 40-70 | 中 | 需要关注 | 增加沟通，了解需求变化 |
| 70-100 | 高 | 流失风险大 | 立即介入，制定挽回策略 |

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-15  
**适用版本**: AI客户情绪分析模块 v1.0.0
