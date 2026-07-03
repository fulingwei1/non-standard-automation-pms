#!/bin/bash
# 非标自动化项目管理系统 - 本地开发启动脚本

set -e
cd "$(dirname "$0")"

# 开发环境变量（可覆盖 .env 中的配置）
export DEBUG=true
export ENABLE_SCHEDULER=false
export PYTHONPATH=.

# SECRET_KEY：未设置时使用开发用临时密钥
if [ -z "$SECRET_KEY" ]; then
  export SECRET_KEY="dev-secret-key-for-local-testing-only-32chars"
fi

# 使用项目 venv 的 Python（需 3.10+，系统 python3 可能过旧导致模块加载失败）
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
  echo "⚠️  未找到 .venv/bin/python，回退使用系统 python3（需 3.10+，否则部分模块会加载失败）"
fi

# 首次运行需先初始化数据库
if [ ! -f "data/app.db" ]; then
  echo "首次运行，正在初始化数据库..."
  "$PYTHON" scripts/init_db.py
  echo ""
fi

echo "启动后端服务: http://127.0.0.1:8002"
echo "API 文档: http://127.0.0.1:8002/docs"
echo "测试账号: admin / admin123"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

"$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
