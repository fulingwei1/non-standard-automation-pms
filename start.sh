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

# 首次运行需先初始化数据库
if [ ! -f "data/app.db" ]; then
  echo "首次运行，正在初始化数据库..."
  python3 scripts/init_db.py
  echo ""
fi

echo "启动后端服务: http://127.0.0.1:8000"
echo "API 文档: http://127.0.0.1:8000/docs"
echo "测试账号: admin / password123"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
