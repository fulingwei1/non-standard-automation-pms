#!/bin/bash

echo "================================================"
echo "  跨部门进度可见性功能 - 快速启动"
echo "================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 检查后端服务
echo -e "${YELLOW}[1/4] 检查后端服务...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务已运行${NC}"
else
    echo -e "${YELLOW}启动后端服务...${NC}"
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    echo $! > backend.pid
    sleep 5
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务启动成功 (PID: $(cat backend.pid))${NC}"
    else
        echo -e "${RED}❌ 后端服务启动失败，请查看 backend.log${NC}"
        exit 1
    fi
fi

echo ""

# 2. 检查演示数据
echo -e "${YELLOW}[2/4] 检查演示数据...${NC}"
if python3 -c "from app.models.base import get_db_session; from app.models.user import User; from app.models.project import Project; db = get_db_session().__enter__(); u = db.query(User).filter(User.username=='demo_pm_liu').first(); p = db.query(Project).filter(Project.project_code.like('DEMO%')).first(); exit(0 if u and p else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ 演示数据已存在${NC}"
else
    echo -e "${YELLOW}生成演示数据...${NC}"
    python3 create_demo_data.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 演示数据生成成功${NC}"
    else
        echo -e "${RED}❌ 演示数据生成失败${NC}"
        exit 1
    fi
fi

echo ""

# 3. 测试API
echo -e "${YELLOW}[3/4] 测试API连接...${NC}"
RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  --data-urlencode 'username=demo_pm_liu' \
  --data-urlencode 'password=demo123')

if echo "$RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ API认证成功${NC}"
    TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    
    # 测试跨部门进度API
    PROGRESS_RESPONSE=$(curl -s -X GET 'http://localhost:8000/api/v1/engineers/projects/27/progress-visibility' \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$PROGRESS_RESPONSE" | grep -q "project_name"; then
        echo -e "${GREEN}✅ 跨部门进度API正常${NC}"
    else
        echo -e "${RED}❌ 跨部门进度API异常${NC}"
        echo "响应: $PROGRESS_RESPONSE"
    fi
else
    echo -e "${RED}❌ API认证失败${NC}"
    echo "响应: $RESPONSE"
    exit 1
fi

echo ""

# 4. 显示访问信息
echo -e "${YELLOW}[4/4] 系统就绪${NC}"
echo ""
echo "================================================"
echo -e "${GREEN}✅ 所有服务已启动并就绪！${NC}"
echo "================================================"
echo ""
echo "📍 访问地址:"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo "   前端界面: http://localhost:5173"
echo ""
echo "🔐 登录信息:"
echo "   用户名: demo_pm_liu"
echo "   密码:   demo123"
echo "   角色:   项目经理"
echo ""
echo "📊 演示项目:"
echo "   项目27: BMS老化测试设备 (H2, 45.67%, 2个延期任务)"
echo "   项目28: EOL功能测试设备 (H1, 72.30%, 0个延期任务)"
echo "   项目29: ICT测试设备 (H3, 28.50%, 5个延期任务)"
echo ""
echo "🚀 使用步骤:"
echo "   1. 打开浏览器访问 http://localhost:5173"
echo "   2. 使用上述账号登录"
echo "   3. 点击左侧菜单 'PMO 驾驶舱'"
echo "   4. 滚动到底部查看'跨部门进度视图'"
echo "   5. 选择项目查看实时进度"
echo ""
echo "📖 详细文档:"
echo "   查看 CROSS_DEPARTMENT_PROGRESS_SETUP_COMPLETE.md"
echo ""
echo "================================================"
