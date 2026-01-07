# 基础建设验收 - 编码规范文档

> 版本：v1.0  
> 适用范围：内部测试与验收环境  
> 验收方式：执行 `make bootstrap` 后，运行 `foundation_verification/bootstrap.py` 将自动验证以下编码规则是否可以生成正确编号。

## 1. 总则

1. 所有业务编号均由系统生成，不允许手工输入。
2. 编号格式统一使用 **前缀 + 日期（或月份） + 三位顺序号**，日期格式 `yymmdd`，月份格式 `yymm`。
3. 顺序号从 `001` 开始，按当日（或当月）已有最大号 + 1 计算。
4. 当天/当月无记录时，默认从 `001` 开始。
5. 生成逻辑须在数据库事务内完成，避免并发冲突；如出现重复，数据库唯一索引应阻止写入。

## 2. 编码明细

| 类型 | 文件位置 | 函数 | 格式 | 示例 |
|------|----------|------|------|------|
| 验收单 | `app/api/v1/endpoints/acceptance.py` | `generate_order_no` | `AC-yymmdd-xxx` | `AC-260106-001` |
| 验收问题 | 同上 | `generate_issue_no` | `IS-yymmdd-xxx` | `IS-260106-001` |
| 项目 | `app/utils/project_utils.py`（项目初始化） | `generate_project_code`（待补） | `PJyymmddxxx` | `PJ250901001` |
| 线索 | `app/api/v1/endpoints/sales.py` | `generate_lead_code` | `Lyymm-xxx` | `L2509-001` |
| 商机 | 同上 | `generate_opportunity_code` | `Oyymm-xxx` | `O2509-001` |
| 报价 | 同上 | `generate_quote_code` | `Qyymm-xxx` | `Q2509-001` |
| 合同 | 同上 | `generate_contract_code` | `HTyymm-xxx` | `HT2509-001` |
| 缺料上报 | `app/api/v1/endpoints/shortage.py` | `generate_report_no` | `SR-yymmdd-xxx` | `SR-250901-001` |
| 到货跟踪 | 同上 | `generate_arrival_no` | `ARR-yymmdd-xxx` | `ARR-250901-001` |
| 替代单 | 同上 | `generate_substitution_no` | `SUB-yymmdd-xxx` | `SUB-250901-001` |
| 服务请求 | `app/api/v1/endpoints/service.py` | `generate_service_ticket_no`（待补） | `SV-yymmdd-xxx` | `SV-250901-001` |

> 说明：若在代码中尚未实现 `generate_project_code`、`generate_service_ticket_no` 等函数，则必须在上线前补充并编写相应测试。

## 3. 验收测试

运行 `make bootstrap` 会自动执行以下验证：

1. 运行 `foundation_verification/data_cleanup.py` 清理旧数据；
2. 执行 `foundation_verification/template_seed.sql` 初始化基础模板；
3. 调用 `test_acceptance_workflow.py`，在执行过程中自动生成 `AC-...`、`IS-...` 等编号；
4. 嵌入式断言确保这些编号满足上述规范。

如需单独验证某类编号，可运行：

```bash
python3 - <<'PY'
from app.api.v1.endpoints.acceptance import generate_order_no
from app.models.base import get_session
print(generate_order_no(get_session()))
PY
```

若返回值格式正确且数据库中无重复记录，则视为通过。
