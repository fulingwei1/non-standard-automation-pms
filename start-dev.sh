#!/bin/bash
# 非标自动化 PMS 开发环境启动脚本
# 用法: ./start-dev.sh

set -e

echo "🚀 启动非标自动化 PMS 开发环境..."

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${YELLOW}📍 项目目录: $PROJECT_DIR${NC}"

# ========== 步骤0: 检查数据库同步 ==========
echo -e "\n${YELLOW}🔄 步骤0: 检查数据库同步...${NC}"
if [ -f "sync-db.sh" ]; then
    # 检查是否有更新的备份需要导入
    if [ -f "db-backups/backup-latest.sql" ] && [ -f "data/app.db" ]; then
        local backup_time=$(stat -f%m "db-backups/backup-latest.sql" 2>/dev/null || stat -c%Y "db-backups/backup-latest.sql" 2>/dev/null)
        local db_time=$(stat -f%m "data/app.db" 2>/dev/null || stat -c%Y "data/app.db" 2>/dev/null)
        
        if [ "$backup_time" -gt "$db_time" ]; then
            echo -e "${YELLOW}⚠️  检测到新的数据库备份，正在导入...${NC}"
            ./sync-db.sh import
        else
            echo -e "${GREEN}✅ 数据库已是最新${NC}"
        fi
    elif [ -f "db-backups/backup-latest.sql" ] && [ ! -f "data/app.db" ]; then
        echo -e "${YELLOW}⚠️  首次运行，导入数据库备份...${NC}"
        ./sync-db.sh import
    else
        echo -e "${GREEN}✅ 使用本地数据库${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  同步脚本不存在，跳过同步检查${NC}"
fi

# ========== 步骤1: 同步种子数据（如果数据库为空） ==========
echo -e "\n${YELLOW}🌱 步骤1: 同步演示数据...${NC}"
if [ ! -f "data/app.db" ]; then
    if [ -f "scripts/seed_blm_bem.py" ]; then
        echo "运行种子数据脚本..."
        python3 scripts/seed_blm_bem.py
        echo -e "${GREEN}✅ 演示数据同步完成${NC}"
    else
        echo -e "${RED}❌ 种子脚本不存在: scripts/seed_blm_bem.py${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 数据库已存在，跳过种子数据${NC}"
fi

# ========== 步骤2: 启动后端 ==========
echo -e "\n${YELLOW}🔧 步骤2: 启动后端服务 (端口 8002)...${NC}"

# 检查端口是否被占用
if lsof -i :8002 -sTCP:LISTEN > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 8002 已被占用，尝试关闭现有进程...${NC}"
    lsof -ti :8002 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 启动后端
source .env 2>/dev/null || true
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端已启动 (PID: $BACKEND_PID)${NC}"

# 等待后端启动
sleep 3

# ========== 步骤3: 启动前端 ==========
echo -e "\n${YELLOW}💻 步骤3: 启动前端服务...${NC}"
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端
export VITE_BACKEND_PORT="${VITE_BACKEND_PORT:-8002}"
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✅ 前端已启动 (PID: $FRONTEND_PID)${NC}"

cd "$PROJECT_DIR"

# ========== 完成 ==========
echo -e "\n${GREEN}🎉 所有服务已启动!${NC}"
echo ""
echo "📊 访问地址:"
echo "   后端 API: http://localhost:8002"
echo "   API 文档: http://localhost:8002/docs"
echo "   前端页面: http://localhost:5173 或 http://localhost:5175"
echo ""
echo "👤 默认登录账户:"
echo "   fulingwei / admin123 (总经理)"
echo "   zhangzq / 123456 (销售总监)"
echo "   limh / 123456 (技术总监)"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"

# 等待用户中断
trap "echo ''; echo -e '${YELLOW}🛑 正在停止服务...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
