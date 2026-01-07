# 项目进度管理模块

> 面向非标自动化设备企业的项目进度管理系统

## 🚀 快速开始

### Docker部署（推荐）

```bash
# 解压项目
unzip project-progress-module.zip
cd project-progress-module

# 启动所有服务
docker-compose up -d

# 访问
# 前端: http://localhost
# API文档: http://localhost:8000/api/docs
```

### 手动启动

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

## 📁 项目结构

```
project-progress-module/
├── backend/                    # 后端 (FastAPI + Python)
│   ├── app/
│   │   ├── main.py            # 应用入口
│   │   ├── api/v1/            # API接口
│   │   ├── models/            # 数据库模型
│   │   └── services/          # 业务服务
│   ├── tests/                 # 单元测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # 前端 (Vue3 + Element Plus)
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 通用组件
│   │   ├── stores/            # Pinia状态管理
│   │   ├── api/               # API封装
│   │   └── router/            # 路由配置
│   ├── package.json
│   └── Dockerfile
├── database/                   # 数据库脚本
│   └── ddl_script.sql
├── docs/                       # 文档
│   ├── DEPLOYMENT.md          # 部署指南
│   └── API.md                 # API文档
├── docker-compose.yml
└── README.md
```

## ✨ 功能特性

### 核心功能
- **项目管理**: 项目列表、看板、进度跟踪
- **WBS任务分解**: 多级任务结构、里程碑管理
- **甘特图**: 可视化进度、拖拽编辑、依赖关系、关键路径
- **工时管理**: 周报填报、审批流程、统计分析
- **负荷管理**: 资源分配、热力图、可用资源查询
- **预警系统**: 自动检测、分级预警、企微通知

### 技术亮点
- 关键路径法(CPM)自动计算
- SPI进度绩效指数
- 项目健康度三色灯
- 多维度报表分析

## 📊 页面预览

| 页面 | 功能 |
|------|------|
| 工作台 | KPI卡片、项目概览、今日待办、预警提醒 |
| 项目列表 | 表格/卡片视图、筛选搜索、新建项目 |
| 项目看板 | 阶段进度、任务分布、S曲线、团队负荷 |
| 甘特图 | 任务条拖拽、依赖线、关键路径、基线对比 |
| 我的任务 | 列表/看板/日历视图、进度更新 |
| 工时填报 | 周视图、按任务分行、自动汇总 |
| 负荷管理 | 成员列表、热力图、可用资源 |
| 预警中心 | 分级显示、处理操作、统计分析 |
| 报表中心 | 项目汇总、工时统计、绩效排名 |

## 🔌 API接口

- `GET /api/v1/projects` - 项目列表
- `GET /api/v1/projects/{id}/progress` - 项目进度
- `GET /api/v1/tasks/gantt` - 甘特图数据
- `GET /api/v1/tasks/critical-path` - 关键路径
- `POST /api/v1/timesheets` - 工时填报
- `GET /api/v1/workload/team` - 团队负荷
- `GET /api/v1/alerts` - 预警列表

详细API文档: [docs/API.md](docs/API.md)

## 🧪 测试

```bash
# 后端测试
cd backend
pytest -v

# 前端测试
cd frontend
npm run test
```

## 📦 技术栈

**后端**
- Python 3.11+
- FastAPI
- SQLAlchemy
- Celery + Redis
- MySQL 8.0

**前端**
- Vue 3.4
- Vite 5
- Element Plus 2.5
- Pinia
- ECharts 5

## 📄 文档

- [部署指南](docs/DEPLOYMENT.md)
- [API接口文档](docs/API.md)

## 📝 License

MIT License

非标自动化设备企业项目进度管理系统的核心模块，支持200+并发项目管理。

## 功能特性

### 核心功能
- **WBS任务管理**：三级任务分解结构（阶段→任务→子任务）
- **甘特图**：可视化进度展示、拖拽调整、依赖线绘制
- **关键路径(CPM)**：自动计算关键路径、浮动时间
- **进度计算**：支持工时法、完成百分比法、里程碑法
- **工时填报**：每日工时填报、审核流程
- **负荷管理**：工程师负荷计算、超负荷预警
- **进度预警**：任务逾期、进度滞后、里程碑风险自动预警
- **企微通知**：预警消息实时推送到企业微信

### 技术特点
- 前后端分离架构
- RESTful API设计
- 异步任务处理（Celery）
- 实时通知（企业微信）

## 技术栈

### 后端
- **框架**: Python 3.11+ / FastAPI
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0
- **异步任务**: Celery + Redis
- **API文档**: Swagger / ReDoc

### 前端
- **框架**: Vue 3 + TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts
- **构建工具**: Vite

## 目录结构

```
project-progress-module/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/v1/            # API接口
│   │   │   ├── project.py     # 项目接口
│   │   │   ├── task.py        # 任务接口
│   │   │   ├── timesheet.py   # 工时接口
│   │   │   ├── workload.py    # 负荷接口
│   │   │   ├── dashboard.py   # 看板接口
│   │   │   └── alert.py       # 预警接口
│   │   ├── models/            # 数据模型
│   │   │   └── models.py      # ORM模型定义
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务服务
│   │   │   ├── progress_service.py  # 进度计算
│   │   │   ├── cpm_service.py       # 关键路径算法
│   │   │   ├── alert_service.py     # 预警服务
│   │   │   └── wechat_service.py    # 企微通知
│   │   ├── tasks/             # Celery异步任务
│   │   ├── utils/             # 工具函数
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 单元测试
│   └── requirements.txt       # Python依赖
│
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── api/              # API接口
│   │   ├── components/       # 公共组件
│   │   │   └── GanttChart.vue # 甘特图组件
│   │   ├── views/            # 页面
│   │   ├── stores/           # Pinia状态
│   │   └── utils/            # 工具函数
│   └── package.json
│
└── database/                  # 数据库脚本
    └── ddl_script.sql        # 建表脚本
```

## 快速开始

### 1. 环境准备

```bash
# 安装 Python 3.11+
# 安装 Node.js 18+
# 安装 MySQL 8.0+
# 安装 Redis
```

### 2. 数据库初始化

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE project_progress DEFAULT CHARSET utf8mb4;"

# 执行DDL脚本
mysql -u root -p project_progress < database/ddl_script.sql
```

### 3. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（创建 .env 文件）
cat > .env << EOF
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/project_progress
REDIS_URL=redis://localhost:6379/0
WECHAT_CORP_ID=your_corp_id
WECHAT_AGENT_ID=1000002
WECHAT_SECRET=your_secret
EOF

# 启动服务
uvicorn app.main:app --reload --port 8000

# 启动Celery Worker（新终端）
celery -A app.tasks worker -l info

# 启动Celery Beat（新终端）
celery -A app.tasks beat -l info
```

### 4. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 访问系统

- 前端界面: http://localhost:5173
- API文档: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API接口概览

### 项目管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/projects | 项目列表 |
| POST | /api/v1/projects | 创建项目 |
| GET | /api/v1/projects/{id} | 项目详情 |
| PUT | /api/v1/projects/{id} | 更新项目 |
| GET | /api/v1/projects/{id}/progress | 进度汇总 |

### 任务管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tasks/{project_id}/wbs | WBS树 |
| POST | /api/v1/tasks | 创建任务 |
| PUT | /api/v1/tasks/{id}/progress | 更新进度 |
| PUT | /api/v1/tasks/batch-progress | 批量更新 |
| GET | /api/v1/tasks/{project_id}/gantt | 甘特图数据 |
| POST | /api/v1/tasks/{project_id}/calculate-cpm | 计算关键路径 |

### 工时管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/timesheets | 填报工时 |
| GET | /api/v1/timesheets | 工时列表 |
| PUT | /api/v1/timesheets/{id}/approve | 审核工时 |

### 我的任务
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tasks/my-tasks | 我的任务列表 |
| GET | /api/v1/tasks/my-tasks/today | 今日任务 |

## 核心算法

### 进度计算逻辑

```
1. 叶子任务进度更新
   ↓
2. 递归更新父任务（加权平均）
   父进度 = Σ(子进度 × 子权重) / Σ子权重
   ↓
3. 更新项目进度
   项目进度 = Σ(阶段进度 × 阶段权重) / Σ阶段权重
   ↓
4. 计算SPI
   SPI = 实际进度 / 计划进度
   ↓
5. 更新健康状态
   SPI ≥ 0.95 → 绿
   SPI ≥ 0.85 → 黄
   SPI < 0.85 → 红
```

### 关键路径算法(CPM)

```
1. 构建任务依赖图
2. 拓扑排序（检测环路）
3. 前向遍历：计算ES和EF
   ES = MAX(前置任务EF + lag)
   EF = ES + duration - 1
4. 后向遍历：计算LF和LS
   LF = MIN(后置任务LS - lag)
   LS = LF - duration + 1
5. 计算浮动时间
   Float = LS - ES
6. 标记关键路径
   Float = 0 的任务为关键任务
```

## 预警规则

| 预警类型 | 触发条件 | 级别 | 通知对象 |
|----------|----------|------|----------|
| 任务逾期 | 计划结束日 < 今天 且 未完成 | 黄/橙/红 | 负责人、PM |
| 任务即将到期 | 3天内到期 且 进度<100% | 黄 | 负责人 |
| 进度滞后 | SPI < 0.9 | 黄/橙/红 | PM、TE |
| 里程碑风险 | 7天内到期 且 前置任务未完成 | 橙 | PM、TE |
| 负荷过高 | 负荷率 > 120% | 黄/橙 | 工程师、部门经理 |

## 企业微信配置

1. 登录企业微信管理后台
2. 创建自建应用，获取：
   - 企业ID (corp_id)
   - 应用ID (agent_id)
   - 应用Secret (secret)
3. 配置可信IP
4. 在 `.env` 文件中配置以上参数

## 部署说明

### Docker部署

```bash
# 构建镜像
docker build -t project-progress-backend ./backend
docker build -t project-progress-frontend ./frontend

# 使用docker-compose启动
docker-compose up -d
```

### 生产环境建议

- 使用 Nginx 反向代理
- 配置 HTTPS
- 使用连接池管理数据库连接
- 配置 Redis 集群
- 设置合理的日志级别
- 配置监控告警

## 开发计划

| Sprint | 周期 | 功能模块 |
|--------|------|----------|
| Sprint 1 | 2周 | 项目管理基础 |
| Sprint 2 | 2周 | WBS任务管理 |
| Sprint 3 | 2周 | 任务依赖 |
| Sprint 4 | 2周 | 甘特图 |
| Sprint 5 | 2周 | 任务分配 |
| Sprint 6 | 2周 | 工时填报 |
| Sprint 7 | 2周 | 进度算法+CPM |
| Sprint 8 | 2周 | 负荷管理 |
| Sprint 9 | 2周 | 看板与报表 |
| Sprint 10 | 2周 | 预警与通知 |

## License

MIT License

## 联系方式

如有问题，请联系项目负责人。
