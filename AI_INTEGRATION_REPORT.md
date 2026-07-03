# AI 集成报告（阿里百炼 Coding Plan / 通义千问）

**日期**：2026-07-02
**目标**：接入阿里百炼 Coding Plan，完善特色 AI 功能并测试

## 一、根因修复：密钥此前根本到不了 AI 服务
- **发现**：全项目无 `load_dotenv`，AI 服务用 `os.getenv` 读密钥，但 `.env/.env.local` 只被 pydantic Settings 读取、**不进 `os.environ`** → 所有 AI 密钥（Kimi/智谱/百炼）在运行时读不到，**AI 一直跑 mock**。
- **修复**：`app/core/config.py` 增加 `_preload_env_files()`（无依赖，导入时把 .env/.env.local 灌入 `os.environ`，`setdefault` 不覆盖已导出变量）。这是让任何 AI 密钥真正生效的地基。

## 二、接入百炼 Coding Plan（专属端点）
- **关键**：Coding Plan 有**专属 Base URL** `https://coding.dashscope.aliyuncs.com/v1`（非标准 `dashscope.../compatible-mode/v1`，用错端点会报 "Incorrect API key"）。模型：`qwen3.7-plus`（推理+视觉）、`qwen3-coder-plus`（编程）。
- **配置**：`.env.local` 增加 `ALIBABA_API_KEY / ALIBABA_BASE_URL / ALIBABA_MODEL`；`Settings` 增加对应字段。
- **ai_client_service**：新增 `_call_qwen`（OpenAI 兼容协议）+ qwen 路由；默认模型在配置了百炼时自动切为 `qwen3.7-plus`；**未配置 gpt/glm/kimi 厂商密钥时自动回退到通义千问**（`_fallback_qwen_or`），使现有功能不改调用处即可用上。
- **ai_assessment_service**：Base URL 改为可配（`ALIBABA_BASE_URL`），默认走 Coding 端点。
- **sales_ai_assistant_service**：`_has_live_ai()` 补入 qwen 判断（原来漏了，导致配了百炼仍判为不可用走降级）。

## 三、测试（真实通义千问输出，非 mock）
- `AIClientService.generate_solution` → qwen3.7-plus 返回真实专业答案（含 reasoning tokens）。
- **销售 AI 谈判建议**（服务层 + HTTP `/sales/ai/opportunities/250/negotiation-advice`）：返回客户画像、价值导向策略、阶梯报价（引用 360万预算/TCO）、4 条话术 —— 真实、贴合业务。
- **销售 AI 流失预测**：risk_score 95/HIGH + 具体风险因子/建议（准确识别客户信息缺失）。

## 三点五、深做旗舰特色：售前 AI 一键出「需求分析 + 三档报价」
端到端测通（HTTP，真实通义千问），修复 3 个阻断问题：
1. **需求分析绕过了共享客户端**：`presale_ai_requirement_service` 自带 `_call_openai_api` 硬编码 `api.openai.com`（无 key→异常→回退"未识别/待澄清"占位）。改为走百炼端点（`settings.ALIBABA_*`），超时 30s→90s。→ 现真实抽取："整机FCT功能测试系统/家电制造业/通电·按键·显示·通讯测试·快速换型·扫码追溯·MES对接"。
2. **重推理模型串行超时**：需求分析、三档报价（3 档串行）默认用 `qwen3.7-plus`（推理模型，慢）→ 120~180s 超时。改用 `qwen3-coder-plus`（结构化 JSON 任务，快）。
3. **Decimal 无法 JSON 序列化**：报价项含 Decimal 存入 `items` JSON 列报 500。转 float 后修复。
结果：三档报价返回**贴合非标行业**的真实方案（basic 档：FCT主机系统¥85万 + 双工位测试治具¥12万×2 + 扫码追溯MES对接软件¥6.5万…），非旧的"标准ERP系统"占位。

> 模型选择原则：结构化/多次调用（需求分析、报价）用 `qwen3-coder-plus`（快）；单次深度分析（销售谈判/流失）用默认 `qwen3.7-plus`（推理更强）。

## 三点六、AI 调用统一加固（超时/重试/降级/用量日志）
- **统一可配超时**：新增 `ALIBABA_TIMEOUT`（默认 60s，Settings + .env.local）。`_call_qwen`、`ai_assessment_service`（原 30s→配置）、需求分析（原 90s→配置）全部改读该值。
- **重试 + 超时降级**：`_call_qwen` 失败/超时自动重试 1 次，并降级到快模型 `ALIBABA_FAST_MODEL`（默认 qwen3-coder-plus）；两次都失败才优雅回退 mock。
- **用量日志**：每次调用输出 `[AI用量] model=… tokens=…(prompt/completion) 耗时=…s 尝试=…`（logger `ai.usage`）；重试输出 `[AI重试] …`。
- **实测**：正常调用记录 `[AI用量] model=qwen3.7-plus tokens=352 耗时=8.56s 尝试=1`；强制 5s 超时时 `qwen3.7-plus` 首次超时→重试降级 `qwen3-coder-plus`→耗尽后 mock，日志完整。

## 三点七、重的 AI 生成改后台任务（提交 + 轮询）
- **动机**：三档报价等重生成耗时数十秒~数分钟，同步 HTTP 易被浏览器/网关中断、占住 worker。
- **实现（无 Celery，进程内线程池 + DB 任务表）**：
  - 表 `ai_generation_jobs`（`migrations/20260702_create_ai_generation_jobs_sqlite.sql`）：job_type/status(PENDING/RUNNING/SUCCESS/FAILED)/params/result/progress/error/时间戳。
  - `app/services/ai_job_service.py`：`ThreadPoolExecutor(4)` 执行；`register_handler(job_type, fn)` 可扩展；后台线程用独立 Session 更新状态/结果，异常安全回退 FAILED。已注册 `three_tier_quotation`。
  - `app/api/v1/endpoints/ai_jobs.py`：`POST /ai-jobs/three-tier-quotations`（提交，立即返回 job_id）+ `GET /ai-jobs/{job_id}`（轮询状态/结果）。
- **实测**：提交 **0.07s** 立即返回 → 轮询 RUNNING→SUCCESS（约 37s）→ 结果含 basic/standard/premium 三档（¥136.7万/¥105.8万/¥140万，各5项）。原同步端点保留，非破坏性。
- **扩展**：其他重 AI（方案生成等）只需 `register_handler` + 一个提交端点即可复用。

## 三点八、新特色：会议纪要 AI 解读 → 关联商机/项目
- **能力**：销售把会议纪要文本提交 → 后台 AI（qwen3-coder-plus）抽取结构化要点 + 按客户自动匹配候选商机/项目 → 销售确认后归档为客户沟通记录并关联。复用后台任务 + AI 客户端。
- **端点**：`POST /sales/activities/parse-minutes`（提交，返回 job_id）→ `GET /ai-jobs/{id}`（轮询）→ `POST /sales/activities/confirm-minutes`（确认落库 + 关联）。
- **抽取字段**：客户、参会人、主题、关键诉求、竞品、预算、下一步行动、我方承诺、重要度、摘要。
- **实测**：小米 FCT 项目纪要 → 准确抽出"整机FCT/15秒节拍/3机型/MES对接、竞品华测、预算200万、下一步行动"；自动匹配到小米的商机(id26)与项目(id61)；确认后生成沟通记录 `COMM-20260702-001` 并关联项目/商机、填充跟进任务。
- **文件**：`app/services/ai_job_service.py`(+handler)、`app/api/v1/endpoints/sales/activity_minutes.py`。

## 四、涉及文件
`app/core/config.py`、`app/services/ai_client_service.py`、`app/services/ai_assessment_service.py`、`app/services/sales_ai_assistant_service.py`、`.env.local`（密钥，未纳入版本库）。

> 密钥安全：仅存于 `.env.local`（gitignored）。如泄漏可在百炼控制台重置。
