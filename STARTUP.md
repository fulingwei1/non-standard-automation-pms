# 系统启动指南

## 快速启动

### 一键启动系统

```bash
./start.sh
```

如需指定 Python 版本（例如 3.13）：
```bash
PYTHON_BIN=python3.13 ./start.sh
```

该脚本会：
1. 检查Python和Node.js环境
2. 自动初始化数据库（如果不存在）
3. 自动安装前端依赖（如果不存在）
4. 启动后端服务（端口8000）
5. 启动前端服务（端口5173）
6. 输出访问地址和日志位置

### 停止系统

```bash
./stop.sh
```

### 查看系统状态

```bash
./status.sh
```

## 访问地址

- **前端页面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 日志文件

所有日志文件位于 `logs/` 目录：

- `logs/backend.log` - 后端服务日志
- `logs/frontend.log` - 前端服务日志

### 实时查看日志

```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log
```

## 手动启动（备用方案）

如果一键启动脚本无法使用，可以手动启动：

### 启动后端

```bash
python3 -m uvicorn app.main:app --reload
```

### 启动前端

```bash
cd frontend
pnpm dev
```

## 环境要求

- Python 3.8+
- Node.js 16+
- pnpm（使用 `npm install -g pnpm` 安装）

## 常见问题

### 端口被占用

如果提示端口被占用，可以：

1. 停止占用端口的进程：
   ```bash
   # 查找占用8000端口的进程
   lsof -i :8000
   # 查找占用5173端口的进程
   lsof -i :5173
   
   # 杀死进程
   kill -9 <PID>
   ```

2. 或者修改端口配置

### 数据库初始化失败

手动初始化数据库：

```bash
python3 init_db.py
```

如需直接运行脚本本体：
```bash
python3 scripts/init_db.py
```

### 前端依赖安装失败

手动安装前端依赖：

```bash
cd frontend
pnpm install
```

## 工程师绩效评价系统

新集成的工程师绩效评价系统访问地址：

- **总览**: http://localhost:5173/engineer-performance
- **排名**: http://localhost:5173/engineer-performance/ranking
- **跨部门协作**: http://localhost:5173/engineer-performance/collaboration
- **知识贡献**: http://localhost:5173/engineer-performance/knowledge

## 技术支持

如遇问题，请查看：
1. 日志文件（`logs/` 目录）
2. 系统状态（运行 `./status.sh`）
3. 项目文档（`docs/` 目录）
