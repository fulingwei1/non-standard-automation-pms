# 贡献指南

## 环境准备

### 系统要求
- Python 3.10+（推荐 3.11-3.12）
- Node.js 18+
- pnpm（前端包管理器）

### 后端启动

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements-dev.txt

# 3. 初始化数据库（SQLite 自动创建）
# 数据文件位于 data/app.db

# 4. 启动开发服务器
uvicorn app.main:app --reload --port 8002

# 5. 访问 API 文档（DEBUG=true 时可用）
# http://localhost:8002/docs
```

### 前端启动

```bash
cd frontend
pnpm install
pnpm dev
# 默认 http://localhost:5173
```

### 环境变量

复制 `.env.example` 为 `.env`，按需修改：

```bash
cp .env.example .env
# 开发环境通常只需确保 DEBUG=true
```

## 开发流程

### 1. 创建分支

```bash
git checkout -b feature/模块名-功能描述
# 或
git checkout -b fix/模块名-问题描述
```

### 2. 编码规范

**后端:**
- Black 格式化（行宽 100）：`black --line-length 100 app/`
- isort 排序：`isort --profile black app/`
- 业务逻辑写在 `app/services/`，端点只做参数校验
- 所有中文注释解释 Why，不只是 How

**前端:**
- ESLint 检查：`pnpm lint`
- Tailwind CSS 样式，不写内联样式
- 状态管理用 Zustand，服务端状态用 React Query

### 3. 测试要求

**提交前必须:**
- 新功能必须有对应测试
- Bug 修复先写复现测试，再修代码
- 后端测试覆盖率目标 80%+

```bash
# 后端测试
pytest tests/ -v
pytest tests/ -m unit         # 单元测试
pytest tests/ -m api          # API 测试

# 前端测试
cd frontend
pnpm test:run                 # 单次运行
pnpm coverage                 # 覆盖率
pnpm e2e                      # E2E 测试
```

### 4. 提交规范

```
<type>: <描述>

<可选正文>
```

**type 类型:** feat, fix, refactor, docs, test, chore, perf, ci

**示例:**
```
feat: 添加项目风险评估 AI 模型
fix: 修复多租户查询未过滤 tenant_id 的问题
test: 补充审批引擎边界条件测试
```

## 项目结构

详见 [CLAUDE.md](CLAUDE.md) 和 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 路由注册

新增 API 端点时，在 `app/api/v1/api.py` 的路由注册表中添加：

```python
# 在 ROUTE_REGISTRY 中添加
("app.api.v1.endpoints.your_module", "/your-prefix", ["YourTag"]),
```

使用 `_safe_include()` 确保模块加载失败不影响其他模块。

## 常见问题

**Q: 启动报 import 错误？**
A: 路由使用 `_safe_include` 安全加载，单个模块失败不阻塞启动。检查日志中的 warning。

**Q: 测试数据库冲突？**
A: 测试使用独立的 SQLite 内存数据库，与开发数据互不影响。

**Q: 多租户如何测试？**
A: 参考 `docs/development/多租户开发指南.md`，测试 fixture 自动注入 tenant_id。
