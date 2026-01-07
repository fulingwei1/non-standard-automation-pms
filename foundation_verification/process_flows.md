# 基础建设验收 - 核心流程设计

> 采用文本版 BPMN 说明，后续可导入到任何流程工具。  
> 覆盖范围：验收管理（FAT/SAT）、项目立项与模板准备。  
> 可执行验证：运行 `make bootstrap` 即可按此流程生成数据和执行用例。

## 1. 项目初始化流程

```
开始
  ↓
[检查数据库状态]
  ├─(不存在 data/app.db)─> 执行 init_db.py
  └─(存在)───────────────> 跳过
  ↓
[创建项目 P]
  - 生成编码：PJyymmddxxx
  - 写入 projects 表
  ↓
[初始化阶段/状态]
  - 调用 init_project_stages()
  - 为项目插入 9 个 stage + 状态
  ↓
结束
```

## 2. 验收管理流程（FAT 示例）

```
开始
  ↓
[准备模板]
  - 导入 foundation_verification/template_seed.sql
  - 模板编码 ACPT-TPL-BASE
  ↓
[创建验收单]
  - API: POST /acceptance-orders
  - 校验项目、机台、模板存在
  - 自动复制分类/检查项
  ↓
[启动验收]
  - API: PUT /acceptance-orders/{id}/start
  - 校验状态= DRAFT & total_items > 0
  ↓
[执行检查项]
  - API: PUT /acceptance-items/{item_id}
  - 更新 result_status & 统计字段
  ↓
[发现问题]
  - API: POST /acceptance-orders/{id}/issues
  - 生成编号 IS-yymmdd-xxx
  ↓
[整改 & 关闭]
  - API: PUT /acceptance-issues/{issue_id}
  - API: PUT /acceptance-issues/{issue_id}/close
  ↓
[完成验收]
  - API: PUT /acceptance-orders/{id}/complete
  - 校验所有必检项已完成
  ↓
[签字 & 报告]
  - API: POST /acceptance-orders/{id}/signatures (QA, CUSTOMER)
  - API: POST /acceptance-orders/{id}/report
  - API: GET /acceptance-reports/{report_id}/download
  ↓
结束
```

## 3. 自动化验证脚本

`foundation_verification/bootstrap.py` 按上图执行，关键节点：

1. 数据清理（确保环境可重复）；
2. 导入模板 SQL；
3. 调用 `test_acceptance_workflow.py` 执行全部 API；
4. 若任意步骤失败脚本退出非零状态。

运行：

```bash
make bootstrap
```

输出中会包含每个流程节点的成功/失败信息，可直接作为基础建设验收凭证。
