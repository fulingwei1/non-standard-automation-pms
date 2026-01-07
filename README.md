# 非标自动化项目管理系统

## 项目简介

非标自动化项目管理系统，专为定制自动化设备制造企业设计，适用于：
- ICT/FCT/EOL 测试设备
- 烧录设备、老化设备
- 视觉检测设备
- 自动化组装线体

系统管理从签单到售后的完整项目生命周期。

## 技术栈

- **后端框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: SQLite (开发环境) / MySQL (生产环境)
- **数据验证**: Pydantic
- **身份认证**: JWT (python-jose)
- **密码加密**: passlib + bcrypt

## 环境准备

1. **Python 3.9+** (推荐 3.10-3.13，3.14 可能存在部分依赖兼容性问题)
2. **SQLite** (开发环境，已包含在 Python 中)
3. **MySQL** (生产环境，可选)

## 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

如果遇到 Python 3.14 的兼容性问题，可以尝试：
```bash
pip3 install fastapi "uvicorn[standard]" sqlalchemy pydantic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" python-multipart redis
```

### 2. 数据库初始化

运行以下脚本初始化 SQLite 数据库：

```bash
python3 init_db.py
```

该脚本会自动执行 `migrations/` 目录下的所有 SQL 迁移脚本，并创建 `data/app.db`。

### 3. 启动应用

**方式一：使用启动脚本（推荐）**

```bash
./start.sh
```

**方式二：直接运行**

```bash
python3 -m app.main
```

**方式三：使用 uvicorn**

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 访问地址

- **API 根地址**: http://127.0.0.1:8000
- **健康检查**: http://127.0.0.1:8000/health
- **API 文档 (Swagger)**: http://127.0.0.1:8000/docs
- **API 文档 (ReDoc)**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/api/v1/openapi.json

## 项目结构

```
.
├── app/                    # 主应用程序包
│   ├── main.py            # FastAPI 应用入口
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── models/            # SQLAlchemy ORM 模型
│   ├── schemas/           # Pydantic 数据模式
│   ├── services/          # 业务服务层
│   └── utils/             # 工具函数
├── data/                  # 数据库文件存储
├── migrations/            # SQL 迁移文件
├── templates/             # 模板文件
├── uploads/               # 文件上传目录
├── requirements.txt       # Python 依赖
├── init_db.py            # 数据库初始化脚本
└── start.sh              # 启动脚本
```

## 配置说明

环境变量可在 `.env` 文件中设置（如果存在）：

```
DEBUG=true
DATABASE_URL=mysql://user:pass@host:3306/dbname
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]
```

详细配置说明请参考 `app/core/config.py`。

## 常见问题

### 1. 端口被占用

如果 8000 端口被占用，可以：
- 停止占用端口的进程
- 或修改 `app/main.py` 中的端口号

### 2. 依赖安装失败

如果遇到依赖安装问题：
- 检查 Python 版本（推荐 3.10-3.13）
- 尝试升级 pip: `pip3 install --upgrade pip`
- 单独安装有问题的依赖包

### 3. 数据库初始化失败

- 确保 `data/` 目录存在且有写权限
- 检查 `migrations/` 目录下的 SQL 文件是否完整

## 开发文档

详细的设计文档和 API 说明请参考：
- `CLAUDE.md` - AI 助手开发指南
- `docs/` - 详细设计文档
- `非标自动化项目管理系统_设计文档.md` - 系统设计文档

## 许可证

[待添加]
