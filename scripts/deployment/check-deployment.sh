#!/bin/bash

# 部署状态检查脚本

echo "=========================================="
echo "部署状态检查"
echo "=========================================="
echo ""

# 检查 Docker
echo "🔍 检查 Docker..."
if docker info > /dev/null 2>&1; then
    echo "✓ Docker 正在运行"
    docker --version
else
    echo "❌ Docker 未运行，请启动 Docker Desktop"
    exit 1
fi
echo ""

# 检查文件
echo "🔍 检查部署文件..."
files=("docker-compose.production.yml" ".env.production" "frontend/dist/index.html" "Dockerfile.fullstack")
for file in "${files[@]}"; do
    if [ -f "$file" ] || [ -d "$(dirname "$file")" ]; then
        echo "✓ $file"
    else
        echo "❌ 缺少: $file"
    fi
done
echo ""

# 检查服务状态
echo "🔍 检查服务状态..."
if docker compose -f docker-compose.production.yml ps > /dev/null 2>&1; then
    docker compose -f docker-compose.production.yml ps
else
    echo "⚠️  服务未启动"
fi
echo ""

# 检查端口
echo "🔍 检查端口占用..."
ports=(80 3306 6379 8000)
for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "✓ 端口 $port 已占用 (正常)"
    else
        echo "⚠️  端口 $port 未占用"
    fi
done
echo ""

# 测试健康检查
echo "🔍 测试服务健康..."
if curl -s http://localhost/health > /dev/null 2>&1; then
    echo "✓ 健康检查通过"
    echo "响应: $(curl -s http://localhost/health)"
else
    echo "❌ 健康检查失败"
fi
echo ""

# 测试前端
echo "🔍 测试前端访问..."
if curl -s http://localhost > /dev/null 2>&1; then
    echo "✓ 前端可访问"
else
    echo "❌ 前端无法访问"
fi
echo ""

# 测试 API 文档
echo "🔍 测试 API 文档..."
if curl -s http://localhost/docs > /dev/null 2>&1; then
    echo "✓ API 文档可访问"
else
    echo "❌ API 文档无法访问"
fi
echo ""

echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  - 系统首页: http://localhost"
echo "  - API文档:  http://localhost/docs"
echo "  - 健康检查: http://localhost/health"
echo ""
