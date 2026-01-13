#!/bin/bash

# 非标自动化项目管理系统 - 一键启动脚本
# 同时启动后端和前端服务

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  非标自动化项目管理系统 - 启动中...${NC}"
echo -e "${BLUE}========================================${NC}"

# 切换到项目根目录
cd "$(dirname "$0")"

# 检查数据库
if [ ! -f "data/app.db" ]; then
    echo -e "\n${YELLOW}⚠ 数据库文件不存在，正在初始化...${NC}"
    python3 init_db.py
    echo -e "${GREEN}✓ 数据库初始化完成${NC}"
fi

# 检查Python环境
echo -e "\n${YELLOW}[1/4] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3，请先安装 Python 3${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python环境正常${NC}"

# 检查Node.js和pnpm
echo -e "\n${YELLOW}[2/4] 检查Node.js和pnpm环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 node，请先安装 Node.js${NC}"
    exit 1
fi
if ! command -v pnpm &> /dev/null; then
    echo -e "${RED}错误: 未找到 pnpm，请运行: npm install -g pnpm${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js和pnpm环境正常${NC}"

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo -e "\n${YELLOW}⚠ 前端依赖未安装，正在安装...${NC}"
    cd frontend
    pnpm install
    cd ..
    echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
fi

# 创建日志目录
mkdir -p logs

# 启动后端
echo -e "\n${YELLOW}[3/4] 启动后端服务...${NC}"
echo -e "${BLUE}后端日志将输出到: logs/backend.log${NC}"
nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid
echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
echo -e "${GREEN}  API地址: http://localhost:8000${NC}"
echo -e "${GREEN}  API文档: http://localhost:8000/docs${NC}"

# 等待后端启动
echo -e "${YELLOW}等待后端服务就绪...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务已就绪${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}错误: 后端服务启动超时，请查看 logs/backend.log${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 启动前端
echo -e "\n${YELLOW}[4/4] 启动前端服务...${NC}"
echo -e "${BLUE}前端日志将输出到: logs/frontend.log${NC}"
cd frontend
nohup pnpm dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo $FRONTEND_PID > logs/frontend.pid
echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

# 等待前端启动
echo -e "${YELLOW}等待前端服务就绪...${NC}"
sleep 5

# 检查前端是否成功启动
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${RED}错误: 前端服务启动失败，请查看 logs/frontend.log${NC}"
    # 停止后端
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 系统启动成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${BLUE}访问地址：${NC}"
echo -e "  ${GREEN}前端页面: http://localhost:5173${NC}"
echo -e "  ${GREEN}后端API:  http://localhost:8000${NC}"
echo -e "  ${GREEN}API文档:  http://localhost:8000/docs${NC}"
echo -e "\n${BLUE}进程信息：${NC}"
echo -e "  后端PID: $BACKEND_PID"
echo -e "  前端PID: $FRONTEND_PID"
echo -e "\n${YELLOW}使用说明：${NC}"
echo -e "  - 查看后端日志: ${BLUE}tail -f logs/backend.log${NC}"
echo -e "  - 查看前端日志: ${BLUE}tail -f logs/frontend.log${NC}"
echo -e "  - 停止系统: ${BLUE}./stop.sh${NC}"
echo -e "  - 查看系统状态: ${BLUE}./status.sh${NC}"
echo -e "\n${YELLOW}提示: 日志文件位于 logs/ 目录${NC}"
echo ""
