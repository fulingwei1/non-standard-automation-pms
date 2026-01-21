# 项目目录结构说明

## 目录组织

```
non-standard-automation-pm/
├── app/                    # 后端应用代码
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # 数据验证模式
│   └── services/          # 业务逻辑服务
│
├── frontend/              # 前端应用代码
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── services/      # API服务
│   │   └── routes/        # 路由配置
│
├── tests/                 # 测试代码
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   ├── api/               # API测试
│   ├── e2e/               # 端到端测试
│   └── performance/       # 性能测试
│
├── docs/                  # 文档
│   ├── reports/           # 项目报告（分析、重构、优化报告）
│   └── ...                # 其他文档
│
├── scripts/               # 工具脚本
│   ├── splitting/         # 代码拆分脚本
│   ├── analysis/          # 分析脚本
│   ├── deployment/        # 部署脚本
│   └── ...                # 其他脚本
│
├── migrations/            # 数据库迁移文件
├── data/                  # 数据文件
├── logs/                  # 日志文件
├── config/                # 配置文件（如需要）
│
├── README.md              # 项目说明
├── CLAUDE.md              # AI助手开发指南
├── STARTUP.md             # 启动指南
├── DEPLOYMENT_GUIDE.md    # 部署指南
├── requirements.txt       # Python依赖
└── package.json           # Node.js依赖
```

## 主要目录说明

### 核心代码目录
- **app/**: 后端FastAPI应用代码
- **frontend/**: 前端React应用代码

### 测试目录
- **tests/unit/**: 单元测试（212个文件）
- **tests/integration/**: 集成测试（45个文件）
- **tests/api/**: API端点测试（42个文件）
- **tests/e2e/**: 端到端测试（2个文件）
- **tests/performance/**: 性能测试（2个文件）

### 文档目录
- **docs/reports/**: 项目报告文档（31个文件）
  - 代码质量报告
  - 重构报告
  - 性能优化报告
  - 测试覆盖率报告

### 脚本目录
- **scripts/splitting/**: 代码拆分脚本（21个文件）
- **scripts/analysis/**: 分析脚本（4个文件）
- **scripts/deployment/**: 部署脚本（4个文件）

### 其他目录
- **migrations/**: 数据库迁移文件
- **data/**: 数据文件
- **logs/**: 日志文件
- **templates/**: 模板文件
- **monitoring/**: 监控配置

## 根目录文件

根目录仅保留必要的配置和说明文件：
- `README.md` - 项目说明
- `CLAUDE.md` - AI助手开发指南
- `STARTUP.md` - 启动指南
- `DEPLOYMENT_GUIDE.md` - 部署指南
- `requirements.txt` - Python依赖
- `package.json` - Node.js依赖
- `pytest.ini` - pytest配置
- `docker-compose.yml` - Docker配置
- `vercel.json` - Vercel部署配置
- `start.sh`, `stop.sh`, `quick_start.sh` - 启动脚本

## 文件查找指南

- **查找报告**: `docs/reports/`
- **查找拆分脚本**: `scripts/splitting/`
- **查找分析工具**: `scripts/analysis/`
- **查找部署脚本**: `scripts/deployment/`
- **查找日志**: `logs/`

## 维护建议

1. **新报告**: 放在 `docs/reports/`
2. **新脚本**: 根据用途放在相应的 `scripts/` 子目录
3. **临时文件**: 放在 `logs/` 或删除
4. **配置文件**: 放在根目录或 `config/` 目录
5. **保持根目录整洁**: 只保留必要的配置和说明文件
