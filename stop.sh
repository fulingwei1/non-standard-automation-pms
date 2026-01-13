#!/bin/bash

# 非标自动化项目管理系统 - 停止脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  停止非标自动化项目管理系统...${NC}"
echo -e "${BLUE}========================================${NC}"

# 切换到项目根目录
cd "$(dirname "$0")"

# 停止后端
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "\n${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        sleep 2
        # 如果还在运行，强制杀死
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}强制停止后端服务...${NC}"
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    else
        echo -e "${YELLOW}后端服务未运行${NC}"
    fi
    rm -f logs/backend.pid
else
    echo -e "${YELLOW}未找到后端进程ID文件${NC}"
fi

# 停止前端
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "\n${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        sleep 2
        # 如果还在运行，强制杀死
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}强制停止前端服务...${NC}"
            kill -9 $FRONTEND_PID 2>/dev/null || true
        fi
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    else
        echo -e "${YELLOW}前端服务未运行${NC}"
    fi
    rm -f logs/frontend.pid
else
    echo -e "${YELLOW}未找到前端进程ID文件${NC}"
fi

# 额外清理：杀死所有可能的残留进程
echo -e "\n${YELLOW}清理残留进程...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null && echo -e "${GREEN}✓ 清理后端残留进程${NC}" || true
pkill -f "vite.*frontend" 2>/dev/null && echo -e "${GREEN}✓ 清理前端残留进程${NC}" || true

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 系统已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
