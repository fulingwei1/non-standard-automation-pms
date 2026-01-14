#!/bin/bash

# 非标自动化项目管理系统 - Docker Compose 部署脚本
# 使用方法: ./deploy.sh

set -e

echo "=========================================="
echo "非标自动化项目管理系统 - 部署脚本"
echo "=========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行"
    echo "请先启动 Docker Desktop，然后重新运行此脚本"
    exit 1
fi

echo "✓ Docker 正在运行"
echo ""

# 检查环境变量文件
if [ ! -f .env.production ]; then
    echo "❌ 错误: .env.production 文件不存在"
    echo "正在创建默认配置文件..."
    
    cat > .env.production << 'EOF'
# 数据库配置
DB_ROOT_PASSWORD=RootPass2026!SecureDB
DB_PASSWORD=PMSPass2026!AppDB
SECRET_KEY=Nb+cWzRHBeCbboAsAeaEeYn216fNvQknCsbvKWimDJ0=

# Redis 配置
REDIS_URL=redis://redis:6379/0

# 应用配置
DEBUG=false
CORS_ORIGINS=http://localhost,http://localhost:80
EOF
    
    echo "✓ 已创建 .env.production 文件"
fi

echo "✓ 环境配置文件存在"
echo ""

# 构建前端
echo "📦 开始构建前端..."
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend && npm ci && cd ..
fi

cd frontend && npm run build && cd ..
echo "✓ 前端构建完成"
echo ""

# 停止现有容器
echo "🛑 停止现有容器..."
docker compose -f docker-compose.production.yml --env-file .env.production down 2>/dev/null || true
echo ""

# 构建 Docker 镜像
echo "🏗️  构建 Docker 镜像..."
docker compose -f docker-compose.production.yml --env-file .env.production build --no-cache
echo "✓ Docker 镜像构建完成"
echo ""

# 启动服务
echo "🚀 启动服务..."
docker compose -f docker-compose.production.yml --env-file .env.production up -d
echo ""

# 等待服务启动
echo "⏳ 等待服务启动（约30秒）..."
sleep 5

# 显示服务状态
echo ""
echo "📊 服务状态:"
docker compose -f docker-compose.production.yml --env-file .env.production ps
echo ""

# 等待健康检查
echo "⏳ 等待健康检查..."
for i in {1..30}; do
    if curl -s http://localhost/health > /dev/null 2>&1; then
        echo "✓ 服务健康检查通过"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# 显示日志（最后 20 行）
echo ""
echo "📋 最近日志:"
docker compose -f docker-compose.production.yml --env-file .env.production logs --tail=20
echo ""

echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  - 前端界面: http://localhost"
echo "  - API文档:  http://localhost/docs"
echo "  - 健康检查: http://localhost/health"
echo ""
echo "管理命令:"
echo "  查看日志: docker compose -f docker-compose.production.yml logs -f"
echo "  停止服务: docker compose -f docker-compose.production.yml down"
echo "  重启服务: docker compose -f docker-compose.production.yml restart"
echo "  查看状态: docker compose -f docker-compose.production.yml ps"
echo ""
echo "数据库信息:"
echo "  主机: localhost:3306"
echo "  数据库: pms"
echo "  用户名: pms"
echo "  密码: 见 .env.production 文件"
echo ""
echo "默认管理员账号:"
echo "  用户名: admin"
echo "  密码: admin123 （首次登录后请修改）"
echo ""
