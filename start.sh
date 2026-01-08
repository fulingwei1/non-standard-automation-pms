#!/bin/bash
# 非标自动化项目管理系统启动脚本

echo "=========================================="
echo "非标自动化项目管理系统"
echo "=========================================="

# 检查Python版本
python3 --version

# 检查依赖
echo ""
echo "检查依赖..."
python3 -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>/dev/null && echo "✓ 核心依赖已安装" || echo "✗ 缺少依赖，请运行: pip3 install -r requirements.txt"

# 检查数据库
if [ -f "data/app.db" ]; then
    echo "✓ 数据库文件存在"
else
    echo "⚠ 数据库文件不存在，正在初始化..."
    python3 init_db.py
fi

# 启动服务
echo ""
echo "启动服务..."
echo "API地址: http://127.0.0.1:8000"
echo "API文档: http://127.0.0.1:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

python3 -m app.main












