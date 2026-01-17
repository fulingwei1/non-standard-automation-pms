#!/bin/bash

# 非标自动化项目管理系统 - 状态检查脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  非标自动化项目管理系统 - 状态${NC}"
echo -e "${BLUE}========================================${NC}"

# 切换到项目根目录
cd "$(dirname "$0")"

BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
BACKEND_PORT=${BACKEND_PORT:-8000}

# 检查后端状态
echo -e "\n${YELLOW}后端服务状态：${NC}"
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ 运行中${NC} (PID: $BACKEND_PID)"
        if curl -s "http://$BACKEND_HOST:$BACKEND_PORT/health" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ 健康检查通过${NC}"
            echo -e "  ${BLUE}  API地址: http://$BACKEND_HOST:$BACKEND_PORT${NC}"
            echo -e "  ${BLUE}  API文档: http://$BACKEND_HOST:$BACKEND_PORT/docs${NC}"
        else
            echo -e "  ${RED}✗ 健康检查失败${NC}"
        fi
    else
        echo -e "  ${RED}✗ 未运行${NC} (PID文件存在但进程不存在)"
    fi
else
    echo -e "  ${RED}✗ 未运行${NC}"
fi

# 检查前端状态
echo -e "\n${YELLOW}前端服务状态：${NC}"
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ 运行中${NC} (PID: $FRONTEND_PID)"
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ 服务可访问${NC}"
            echo -e "  ${BLUE}  访问地址: http://localhost:5173${NC}"
        else
            echo -e "  ${YELLOW}⚠ 服务可能正在启动...${NC}"
        fi
    else
        echo -e "  ${RED}✗ 未运行${NC} (PID文件存在但进程不存在)"
    fi
else
    echo -e "  ${RED}✗ 未运行${NC}"
fi

# 检查日志文件
echo -e "\n${YELLOW}日志文件：${NC}"
if [ -f "logs/backend.log" ]; then
    BACKEND_LOG_SIZE=$(ls -lh logs/backend.log | awk '{print $5}')
    echo -e "  后端日志: ${BLUE}logs/backend.log${NC} ($BACKEND_LOG_SIZE)"
    echo -e "  最新10行:"
    tail -n 3 logs/backend.log | sed 's/^/    /'
else
    echo -e "  后端日志: ${YELLOW}不存在${NC}"
fi

if [ -f "logs/frontend.log" ]; then
    FRONTEND_LOG_SIZE=$(ls -lh logs/frontend.log | awk '{print $5}')
    echo -e "  前端日志: ${BLUE}logs/frontend.log${NC} ($FRONTEND_LOG_SIZE)"
    echo -e "  最新10行:"
    tail -n 3 logs/frontend.log | sed 's/^/    /'
else
    echo -e "  前端日志: ${YELLOW}不存在${NC}"
fi

# 数据库状态
echo -e "\n${YELLOW}数据库状态：${NC}"
if [ -f "data/app.db" ]; then
    DB_SIZE=$(ls -lh data/app.db | awk '{print $5}')
    echo -e "  ${GREEN}✓ 数据库文件存在${NC} (大小: $DB_SIZE)"
else
    echo -e "  ${RED}✗ 数据库文件不存在${NC}"
fi

echo -e "\n${BLUE}========================================${NC}"
