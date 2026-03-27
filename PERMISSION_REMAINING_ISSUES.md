# Permission Remaining Issues

> 生成时间：2026-03-26
> 范围：Sprint 1 ~ Sprint 8 权限系统重构后的剩余问题清单

## 当前总体判断

权限系统主干已完成：
- 统一权限引擎 ✅
- 动作权限补锁 ✅
- engineer_performance 数据范围控制 ✅
- sales 数据范围控制（核心 + 关键详情 + 导出/analytics + 列表尾巴）✅
- approvals participant/workflow visibility（核心 + P0/P1 + 部分 P2）✅
- 审计脚本 / unit / integration 护栏 ✅
- 系统总览 / changelog / hardening / seeds review 文档 ✅

当前已从“重构中”进入“主干完成，尾巴收口”阶段。

---

## 一、必须尽快确认（P0）

### 1. GitHub 主线同步状态最终确认
- 本地已执行 rebase / push 流程，但仍建议在下一次操作前确认：
  - `git status` 为空
  - `git rev-list --left-right --count origin/main...main` 为 `0 0`
- 这是发布收尾问题，不是架构问题。

### 2. 角色权限宽窄业务确认
根据 `PERMISSION_SEED_REVIEW.md`：
- SALES / ENGINEER 角色拥有 `approval:approve` 可能过宽
- 某些角色对新权限是否应默认继承，需要业务拍板

这类问题必须由业务负责人确认，不应靠工程默认猜。

---

## 二、本周建议处理（P1）

### 3. approvals 剩余 P2 / 聚合可见性尾巴
当前 approvals 已完成 participant/workflow visibility 主干，但仍建议继续清理：
- 某些 dashboard / summary / history / aggregate 接口
- 某些存在性推断（即使看不到详情，也可能猜到流程存在）
- 某些写操作虽然 engine 内已有 assignee 校验，但 endpoint 前置显式检查仍不够统一

### 4. sales 剩余边角 scope
当前 sales 已覆盖：
- 详情
- 导出
- analytics
- 列表尾巴
- 合同边角（payment plans / sign / costs）

仍建议继续扫：
- customers 列表 / 统计的剩余边角
- contracts 其他次级接口
- opportunities / quotes 更深层的批量或统计口径

### 5. 权限码命名进一步统一
仍存在历史不一致：
- `view` vs `read`
- `admin` vs `manage`
- `role:assign` vs `project_role:assign`

当前已能工作，但长期维护成本仍偏高。建议后续做一轮统一映射/弃用标记。

---

## 三、可放入后续迭代（P2）

### 6. 将权限审计纳入 CI 门槛
已有：
- 审计脚本
- unit 测试
- integration 测试
- hardening 报告

建议下一步：
- 将关键权限测试纳入 CI
- 对新接口缺少守卫的情况设置门槛
- 对新增权限码缺少种子/映射的情况给出 CI 警告或失败

### 7. 将 approvals participant_scope 做成更完整的复用层
目前已有核心能力与部分接入，后续可进一步抽象：
- 更统一的 visibility facade
- endpoint 侧更少重复调用
- remind/comment/terminate 等行为边界统一收口

### 8. 将 sales_scope / engperf_scope 进一步抽象共性
目前两者都已成型，但还未抽出“可复用范围模型框架”。
等业务模型稳定后，再考虑统一抽象，避免过早泛化。

---

## 四、建议不要现在做的事情

### 9. 不建议立即重构整个权限表结构
原因：
- 当前主干已可用
- 继续动表会放大风险
- 现阶段更值钱的是治理、CI、角色确认与边角收口

### 10. 不建议立即推倒现有角色体系重建
原因：
- 现有问题主要在宽窄与映射，不是角色体系完全失效
- 先做角色清单审计与业务确认更稳

---

## 五、建议的下一阶段主题

### 方案 A：治理化收尾（推荐）
适合现在做：
1. CI 权限门槛
2. 角色权限业务确认
3. approvals / sales 边角清尾
4. Git / 发布收口确认

### 方案 B：继续深挖架构抽象
不建议立刻做。容易从“收尾工程”重新变成“大重构”。

---

## 最终结论

当前权限系统已完成从 0 到 1 的重建，剩余问题主要是：
- 发布收尾确认
- 角色权限宽窄确认
- approvals / sales 边角继续收紧
- CI / 治理门槛建设

这已经不是“系统没做完”，而是“主干完成后的治理与收尾”。
