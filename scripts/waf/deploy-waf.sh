#!/bin/bash
# WAF一键部署脚本
# 版本: 1.0.0
# 日期: 2026-02-15
# 用途: 快速部署Nginx + ModSecurity WAF

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  WAF一键部署脚本${NC}"
echo -e "${GREEN}  版本: 1.0.0${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查Docker和Docker Compose
check_requirements() {
    echo -e "${YELLOW}[1/8] 检查系统要求...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ 错误: Docker未安装${NC}"
        echo "请先安装Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ 错误: Docker Compose未安装${NC}"
        echo "请先安装Docker Compose"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker和Docker Compose已安装${NC}"
}

# 创建必要的目录
create_directories() {
    echo -e "${YELLOW}[2/8] 创建必要目录...${NC}"
    
    mkdir -p \
        docker/nginx/conf.d \
        docker/nginx/modsecurity \
        docker/nginx/ssl \
        docker/nginx/errors \
        logs/nginx \
        logs/waf \
        frontend/dist \
        static \
        media \
        data
    
    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 生成环境变量文件
setup_env() {
    echo -e "${YELLOW}[3/8] 配置环境变量...${NC}"
    
    if [ ! -f .env.waf ]; then
        if [ -f .env.waf.example ]; then
            cp .env.waf.example .env.waf
            echo -e "${YELLOW}已创建.env.waf文件，请根据实际情况修改配置${NC}"
            echo -e "${YELLOW}是否现在编辑配置文件？(y/N)${NC}"
            read -p "> " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ${EDITOR:-nano} .env.waf
            fi
        else
            echo -e "${RED}❌ 错误: .env.waf.example文件不存在${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ .env.waf文件已存在${NC}"
    fi
    
    # 加载环境变量
    source .env.waf || source .env.waf.example
}

# 生成SSL证书
generate_ssl_cert() {
    echo -e "${YELLOW}[4/8] 生成SSL证书...${NC}"
    
    if [ -f docker/nginx/ssl/pms.crt ] && [ -f docker/nginx/ssl/pms.key ]; then
        echo -e "${GREEN}✅ SSL证书已存在，跳过生成${NC}"
        return
    fi
    
    if [ -f docker/nginx/ssl/generate-cert.sh ]; then
        chmod +x docker/nginx/ssl/generate-cert.sh
        
        # 设置环境变量
        export DOMAIN=${DOMAIN:-pms.example.com}
        export CERT_TYPE=${CERT_TYPE:-selfsigned}
        export EMAIL=${LETSENCRYPT_EMAIL:-admin@example.com}
        
        # 执行证书生成脚本
        bash docker/nginx/ssl/generate-cert.sh
    else
        echo -e "${RED}❌ 错误: 证书生成脚本不存在${NC}"
        exit 1
    fi
}

# 创建错误页面
create_error_pages() {
    echo -e "${YELLOW}[5/8] 创建错误页面...${NC}"
    
    # 403错误页面
    cat > docker/nginx/errors/403.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>403 Forbidden</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
        h1 { color: #e74c3c; font-size: 72px; margin: 0; }
        p { color: #7f8c8d; font-size: 18px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <h1>403</h1>
        <p><strong>Access Forbidden</strong></p>
        <p>Your request was blocked by our Web Application Firewall.</p>
        <p>If you believe this is an error, please contact the administrator.</p>
    </div>
</body>
</html>
EOF

    # 404错误页面
    cat > docker/nginx/errors/404.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>404 Not Found</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
        h1 { color: #3498db; font-size: 72px; margin: 0; }
        p { color: #7f8c8d; font-size: 18px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <p><strong>Page Not Found</strong></p>
        <p>The page you are looking for does not exist.</p>
    </div>
</body>
</html>
EOF

    # 50x错误页面
    cat > docker/nginx/errors/50x.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Server Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
        h1 { color: #e67e22; font-size: 72px; margin: 0; }
        p { color: #7f8c8d; font-size: 18px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <h1>500</h1>
        <p><strong>Internal Server Error</strong></p>
        <p>Something went wrong on our end. Please try again later.</p>
    </div>
</body>
</html>
EOF

    echo -e "${GREEN}✅ 错误页面创建完成${NC}"
}

# 验证配置文件
validate_config() {
    echo -e "${YELLOW}[6/8] 验证配置文件...${NC}"
    
    # 检查必要文件是否存在
    required_files=(
        "docker/nginx/nginx.conf"
        "docker/nginx/conf.d/pms.conf"
        "docker/nginx/modsecurity/main.conf"
        "docker/nginx/modsecurity/custom-rules.conf"
        "docker-compose.waf.yml"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ 错误: 文件不存在 - $file${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ 配置文件验证通过${NC}"
}

# 启动WAF服务
start_waf() {
    echo -e "${YELLOW}[7/8] 启动WAF服务...${NC}"
    
    # 停止旧容器（如果存在）
    echo "停止旧容器..."
    docker-compose -f docker-compose.waf.yml down 2>/dev/null || true
    
    # 启动新容器
    echo "启动新容器..."
    docker-compose -f docker-compose.waf.yml up -d
    
    # 等待服务启动
    echo "等待服务启动..."
    sleep 5
    
    # 检查容器状态
    if docker-compose -f docker-compose.waf.yml ps | grep -q "Up"; then
        echo -e "${GREEN}✅ WAF服务启动成功${NC}"
    else
        echo -e "${RED}❌ WAF服务启动失败${NC}"
        echo "查看日志:"
        docker-compose -f docker-compose.waf.yml logs --tail=50
        exit 1
    fi
}

# 运行测试
run_tests() {
    echo -e "${YELLOW}[8/8] 运行基础测试...${NC}"
    
    # 等待服务完全启动
    sleep 3
    
    # 测试健康检查
    echo "测试健康检查..."
    if curl -f http://localhost/health &> /dev/null; then
        echo -e "${GREEN}✅ 健康检查通过${NC}"
    else
        echo -e "${RED}❌ 健康检查失败${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  WAF部署完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "📊 服务状态:"
    docker-compose -f docker-compose.waf.yml ps
    echo ""
    echo -e "📝 下一步操作:"
    echo -e "  1. 运行完整测试: ${YELLOW}bash scripts/waf/test-waf.sh${NC}"
    echo -e "  2. 查看日志: ${YELLOW}docker-compose -f docker-compose.waf.yml logs -f nginx-waf${NC}"
    echo -e "  3. 监控WAF: ${YELLOW}bash scripts/waf/monitor-waf.sh${NC}"
    echo -e "  4. 查看文档: ${YELLOW}docs/security/WAF部署指南.md${NC}"
    echo ""
    echo -e "⚠️  重要提示:"
    echo -e "  - 如使用自签名证书，浏览器会显示安全警告"
    echo -e "  - 生产环境建议使用Let's Encrypt证书"
    echo -e "  - 首次部署建议先使用DetectionOnly模式测试"
    echo -e "  - 定期检查WAF日志并调整规则"
    echo ""
}

# 主函数
main() {
    check_requirements
    create_directories
    setup_env
    generate_ssl_cert
    create_error_pages
    validate_config
    start_waf
    run_tests
}

# 执行主函数
main
