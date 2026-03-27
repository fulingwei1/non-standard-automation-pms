# PROJECT_STAGE_RULE_ENGINE_PLAN

> 生成时间：2026-03-27
> 目标：把“阶段流转前置条件”从代码硬编码升级为**后台可配置的阶段规则引擎**，但保留不可突破的业务底线。

---

## 一、方案定位

这不是做一个“万能规则引擎”，而是先做一个：

# **项目阶段规则中心**

专门解决：
- 项目什么时候可以进入下一阶段
- 缺什么条件不能流转
- 哪些场景允许只警告不阻断
- 哪些场景必须走特批

---

## 二、设计原则

### 1. 规则可配置，底线不可取消
允许后台配置：
- 阶段前置条件
- 风险提示文案
- 阻断 / 警告 / 特批三档
- 适用项目类型
- 金额阈值
- 是否启用例外

不允许后台随便关闭：
- 审计记录
- 权限校验
- 核心合规底线（如正式采购门槛）

### 2. 不做脚本型 DSL，先做结构化规则
第一阶段不支持自由脚本，避免把后台变成低代码炸弹。

### 3. 所有阶段切换都走统一评估入口
禁止页面自己 if/else 判断能不能进入下一阶段。

### 4. 结果必须可解释
规则引擎返回的不是单纯 true/false，而是：
- 允许/拒绝/需特批/警告
- 缺失条件列表
- 命中规则列表
- 风险提示

---

## 三、第一阶段覆盖范围

## 先只管“项目阶段流转”
先不扩展到：
- 采购完整规则引擎
- 审批可见性规则
- 数据权限规则

第一阶段只处理：
- `from_stage -> to_stage` 的切换规则

建议先覆盖：
- S1 需求进入 → S2 方案设计
- S2 方案设计 → S3 商务确认 / 采购备料
- S3 → S4 执行 / 装配调试
- S4 → S5 验收交付
- S5 → S6 关闭/售后

---

## 四、规则模型设计

## 1. 阶段定义（可复用现有）
现有项目阶段仍保留，例如：
- S1 需求进入
- S2 方案设计
- S3 采购备料
- S4 装配调试
- S5 验收交付
- S6 关闭/售后

## 2. 阶段流转规则表 `project_stage_transition_rule`
建议字段：
- `id`
- `from_stage`
- `to_stage`
- `project_type`（可空，表示全局）
- `enabled`
- `priority`
- `mode`：
  - `hard_block`
  - `warn`
  - `require_approval`
- `name`
- `description`
- `condition_json`
- `warning_text`
- `approval_type`（可空）
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

## 3. 条件结构 `condition_json`
建议使用结构化 JSON：

```json
{
  "all": [
    {"field": "project.contract_signed", "op": "eq", "value": true},
    {"field": "project.bom_ready", "op": "eq", "value": true},
    {"field": "project.budget_approved", "op": "eq", "value": true}
  ]
}
```

支持最小操作符：
- `eq`
- `neq`
- `in`
- `not_in`
- `gt`
- `gte`
- `lt`
- `lte`
- `exists`

第二阶段再考虑：
- `any`
- 嵌套条件
- 数组长度/聚合条件

## 4. 例外机制 `project_stage_rule_exception`
建议字段：
- `rule_id`
- `project_id`
- `approval_id` / `approval_type`
- `reason`
- `approved_by`
- `effective_from`
- `effective_to`
- `once_only`
- `status`

如果当前系统暂时不做完整特批表，也至少保留接口/Provider 层：
- `ExemptionProvider`

---

## 五、评估引擎设计

统一入口：

```python
result = stage_rule_engine.evaluate(
    project=project,
    from_stage=from_stage,
    to_stage=to_stage,
    user=current_user,
)
```

返回结构建议：

```json
{
  "decision": "deny",
  "matched_rules": ["PROCUREMENT_CONTRACT_REQUIRED"],
  "missing": [
    "合同未签订",
    "BOM未确认"
  ],
  "warnings": [],
  "requires_approval": false,
  "approval_type": null
}
```

可能值：
- `allow`
- `warn`
- `deny`
- `require_approval`

---

## 六、前端后台页面设计

## 页面 1：阶段规则列表
功能：
- 查看规则列表
- 按阶段、项目类型、启用状态筛选
- 查看规则优先级和模式

## 页面 2：规则编辑器
编辑内容：
- 起始阶段
- 目标阶段
- 项目类型
- 条件配置器
- 模式（阻断/警告/特批）
- 文案

## 页面 3：规则模拟器（非常关键）
输入：
- 项目
- 当前阶段
- 目标阶段
- 用户

输出：
- 命中哪些规则
- 缺了什么
- 为什么被阻断/警告/要求特批

## 页面 4：例外/特批记录
功能：
- 查看当前项目有哪些阶段例外
- 谁批的、什么时候批的、到什么时候失效

---

## 七、接入点设计

## 1. 项目详情页
当用户点击“推进到下一阶段”时：
- 先调用规则评估
- 如果 `deny`：弹出阻断说明
- 如果 `warn`：显示黄色确认
- 如果 `require_approval`：跳转特批流程入口

## 2. 项目阶段组件
要显示：
- 当前阶段
- 可推进的目标阶段
- 规则命中提示

## 3. 审计日志
必须记录：
- 用户尝试切换阶段
- 命中的规则
- 最终是否放行
- 是否走了特批

---

## 八、与现有系统的关系

### 与采购门槛关系
采购门槛目前已开始形成：
- 立项在前
- 正式采购在后
- 合同已签 or 特批

阶段规则引擎可在第二阶段纳入：
- 例如：只有满足采购备料阶段条件后，才能进入采购相关流程

### 与模板关系
模板里可以带：
- 默认阶段顺序
- 建议规则集合
- 项目类型默认规则

### 与权限系统关系
只有有权限的用户才能尝试流转；
规则引擎不替代权限系统，只负责判断业务条件。

---

## 九、分阶段实施计划

## Phase 1（建议先做）
### 最小可用版
- 阶段规则表
- 结构化条件 JSON
- 阻断 / 警告 / 特批 三档
- 模拟器
- 项目详情接入

### 只覆盖 3 条关键流转
1. S1 → S2
2. S2 → S3（采购备料）
3. S4 → S5（验收交付）

## Phase 2
- 引入项目类型差异化
- 引入金额阈值
- 引入模板默认规则
- 引入例外记录持久化

## Phase 3
- 与采购门槛进一步联动
- 与审批流联动
- 规则统计分析
- 风险看板

---

## 十、风控建议

### 1. 先做“警告 + 阻断 + 特批”，不要先做自由脚本
### 2. 所有规则改动必须有版本、审计、可回滚
### 3. 默认 fail-closed
### 4. 核心合规底线不允许后台配置关闭

---

## 十一、最短实施建议

如果现在就要开始开发，建议优先做：

1. `PROJECT_STAGE_RULE_ENGINE_PLAN.md`（本文件）落地确认
2. 新建 `project_stage_transition_rule` 表
3. 写 `StageRuleEngine.evaluate()`
4. 项目详情页接“推进阶段”前评估
5. 做一个最小模拟器页面

---

## 最终结论

这个需求非常值得做，而且适合你当前系统。

因为它会让项目管理模块从：
- 会记录阶段

升级为：
# 会驱动阶段

这是项目管理系统真正的灵魂能力之一。
