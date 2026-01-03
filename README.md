# 非标自动化项目管理系统

## 项目简介

非标自动化项目管理系统。

## 环境准备

1. Python 3.9+
2. SQLite (开发环境)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 数据库初始化

运行以下脚本初始化 SQLite 数据库：

```bash
python3 init_db.py
```

该脚本会自动执行 `migrations/` 目录下的所有 SQL 迁移脚本，并创建 `data/app.db`。

## 启动应用

```bash
python3 -m app.main
```

或使用 uvicorn:

```bash
uvicorn app.main:app --reload
```

API 文档地址: <http://127.0.0.1:8000/docs>
