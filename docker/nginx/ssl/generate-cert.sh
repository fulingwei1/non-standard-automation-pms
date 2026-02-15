#!/bin/bash
# SSL证书生成脚本
# 版本: 1.0.0
# 日期: 2026-02-15
# 用途: 生成自签名SSL证书（开发/测试环境）或申请Let's Encrypt证书（生产环境）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="${DOMAIN:-pms.example.com}"
CERT_TYPE="${CERT_TYPE:-selfsigned}"  # selfsigned | letsencrypt
EMAIL="${EMAIL:-admin@example.com}"

echo "==================================="
echo "SSL证书生成脚本"
echo "==================================="
echo "域名: $DOMAIN"
echo "证书类型: $CERT_TYPE"
echo "==================================="

# 创建SSL目录
mkdir -p "$SCRIPT_DIR"

if [ "$CERT_TYPE" = "selfsigned" ]; then
    echo "生成自签名证书..."
    
    # 生成私钥
    openssl genrsa -out "$SCRIPT_DIR/pms.key" 2048
    
    # 生成证书签名请求（CSR）
    openssl req -new -key "$SCRIPT_DIR/pms.key" -out "$SCRIPT_DIR/pms.csr" -subj "/C=CN/ST=Beijing/L=Beijing/O=PMS/OU=IT/CN=$DOMAIN"
    
    # 生成自签名证书（有效期365天）
    openssl x509 -req -days 365 -in "$SCRIPT_DIR/pms.csr" -signkey "$SCRIPT_DIR/pms.key" -out "$SCRIPT_DIR/pms.crt"
    
    # 创建chain文件（自签名证书链指向自己）
    cp "$SCRIPT_DIR/pms.crt" "$SCRIPT_DIR/chain.pem"
    
    # 创建默认证书
    cp "$SCRIPT_DIR/pms.crt" "$SCRIPT_DIR/default.crt"
    cp "$SCRIPT_DIR/pms.key" "$SCRIPT_DIR/default.key"
    
    echo "✅ 自签名证书生成成功！"
    echo "   证书: $SCRIPT_DIR/pms.crt"
    echo "   私钥: $SCRIPT_DIR/pms.key"
    echo ""
    echo "⚠️  警告: 自签名证书仅用于开发/测试环境！"
    echo "   浏览器会显示安全警告，生产环境请使用Let's Encrypt证书。"
    
elif [ "$CERT_TYPE" = "letsencrypt" ]; then
    echo "申请Let's Encrypt证书..."
    
    # 检查certbot是否安装
    if ! command -v certbot &> /dev/null; then
        echo "❌ 错误: certbot未安装"
        echo "请先安装certbot:"
        echo "  Ubuntu/Debian: sudo apt-get install certbot"
        echo "  CentOS/RHEL: sudo yum install certbot"
        echo "  macOS: brew install certbot"
        exit 1
    fi
    
    # 检查域名是否解析
    echo "检查域名DNS解析..."
    if ! nslookup "$DOMAIN" &> /dev/null; then
        echo "⚠️  警告: 域名 $DOMAIN 无法解析"
        echo "请确保域名已正确解析到服务器IP地址"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    echo "申请证书..."
    echo "域名: $DOMAIN"
    echo "邮箱: $EMAIL"
    echo ""
    
    # 使用standalone模式申请证书
    # 注意：需要停止Nginx或使用webroot模式
    sudo certbot certonly --standalone \
        --preferred-challenges http \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"
    
    # 复制证书到Nginx SSL目录
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SCRIPT_DIR/pms.crt"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SCRIPT_DIR/pms.key"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/chain.pem" "$SCRIPT_DIR/chain.pem"
    
    # 创建默认证书
    sudo cp "$SCRIPT_DIR/pms.crt" "$SCRIPT_DIR/default.crt"
    sudo cp "$SCRIPT_DIR/pms.key" "$SCRIPT_DIR/default.key"
    
    # 设置权限
    sudo chown $(whoami):$(whoami) "$SCRIPT_DIR"/*.{crt,key,pem}
    sudo chmod 600 "$SCRIPT_DIR"/*.key
    sudo chmod 644 "$SCRIPT_DIR"/*.{crt,pem}
    
    echo "✅ Let's Encrypt证书申请成功！"
    echo "   证书: $SCRIPT_DIR/pms.crt"
    echo "   私钥: $SCRIPT_DIR/pms.key"
    echo "   证书链: $SCRIPT_DIR/chain.pem"
    echo ""
    echo "📅 证书有效期: 90天"
    echo "💡 建议设置自动续期："
    echo "   sudo crontab -e"
    echo "   添加: 0 0 * * * certbot renew --quiet --deploy-hook 'systemctl reload nginx'"
    
else
    echo "❌ 错误: 未知的证书类型 '$CERT_TYPE'"
    echo "支持的类型: selfsigned, letsencrypt"
    exit 1
fi

# 验证证书
echo ""
echo "验证证书..."
openssl x509 -in "$SCRIPT_DIR/pms.crt" -text -noout | grep -E '(Subject:|Issuer:|Not Before|Not After)'

echo ""
echo "==================================="
echo "证书生成完成！"
echo "==================================="
