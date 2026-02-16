#!/bin/bash

echo "停止现有服务..."
pkill -f "uvicorn app.main:app"
sleep 2

echo ""
echo "重新启动服务并捕获启动日志..."
cd ~/.openclaw/workspace/non-standard-automation-pms

# 启动服务并捕获输出
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > startup.log 2>&1 &

echo "等待服务启动..."
sleep 8

echo ""
echo "==================== 启动日志 ===================="
grep -E "(开始加载|加载成功|加载失败|个路由)" startup.log | head -30

echo ""
echo "==================== 服务状态 ===================="
curl -s http://127.0.0.1:8000/api/v1/health 2>/dev/null | head -c 100
echo ""
