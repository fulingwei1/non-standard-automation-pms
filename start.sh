#!/bin/bash
# 非标自动化项目管理系统启动脚本

cd /Users/flw/non-standard-automation-pm

echo "=========================================="
echo "非标自动化项目管理系统"
echo "=========================================="

# 检查数据库
if [ ! -f "data/app.db" ]; then
    echo "⚠ 数据库文件不存在，正在初始化..."
    python3 init_db.py
fi

# 启动后端
echo "启动后端服务..."
uvicorn app.main:app --reload &
BACKEND_PID=$!

sleep 2

# 启动前端
echo "启动前端服务..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "服务已启动："
echo "  前端: http://localhost:5173"
echo "  后端: http://127.0.0.1:8000"
echo "  API文档: http://127.0.0.1:8000/docs"
echo "=========================================="
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait












