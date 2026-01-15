#!/bin/bash

# 快速修复严重安全问题脚本

set -e

echo "=========================================="
echo "🔐 紧急安全修复脚本"
echo "=========================================="
echo ""

# 1. 检查 .env 文件
if [ -f ".env" ]; then
    echo "⚠️  发现 .env 文件（包含敏感信息）"
    echo ""
    
    # 备份
    cp .env .env.backup
    echo "✓ 已备份到 .env.backup"
    
    # 从 Git 移除
    git rm --cached .env 2>/dev/null || true
    echo "✓ 已从 Git 缓存移除"
    
    # 更新 .gitignore
    if ! grep -q "^\.env$" .gitignore; then
        echo ".env" >> .gitignore
        echo "✓ 已添加到 .gitignore"
    fi
    
    echo ""
    echo "⚠️  重要：.env 文件仍在本地，请手动删除或移动到安全位置"
    echo "   mv .env ~/.env.non-standard-pm"
    echo ""
fi

# 2. 生成新的 SECRET_KEY
echo "🔑 生成新的 SECRET_KEY..."
NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo ""
echo "新的 SECRET_KEY（请保存）:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$NEW_SECRET"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 3. 创建 .env.local 模板
cat > .env.local.template << EOF
# 本地开发环境配置
# 复制此文件为 .env.local 并填入实际值

# JWT 密钥（请使用上面生成的新密钥）
SECRET_KEY=$NEW_SECRET

# 开发模式
DEBUG=true

# 数据库（开发环境使用 SQLite）
# DATABASE_URL=sqlite:///data/app.db

# Redis（可选）
# REDIS_URL=redis://localhost:6379/0
EOF

echo "✓ 已创建 .env.local.template"
echo ""

# 4. 检查其他敏感文件
echo "🔍 检查其他敏感文件..."

SENSITIVE_FILES=(
    ".env.production"
    ".env.vercel"
    "data/*.db"
    "*.key"
    "*.pem"
)

for pattern in "${SENSITIVE_FILES[@]}"; do
    if ls $pattern 2>/dev/null; then
        echo "⚠️  发现: $pattern"
        if ! grep -q "^${pattern}$" .gitignore 2>/dev/null; then
            echo "$pattern" >> .gitignore
            echo "   已添加到 .gitignore"
        fi
    fi
done
echo ""

# 5. 提交更改
echo "💾 准备提交更改..."
git add .gitignore
git add .env.local.template

if git diff --staged --quiet; then
    echo "没有需要提交的更改"
else
    git commit -m "security: Remove sensitive files and regenerate keys

- Remove .env from repository
- Update .gitignore to exclude sensitive files
- Add .env.local.template for development
- Regenerate SECRET_KEY for security

⚠️  IMPORTANT: 
- Old SECRET_KEY is compromised, all JWT tokens are invalidated
- Users need to re-login after deployment
- Update SECRET_KEY in production environment" || true
    
    echo "✓ 已提交更改"
fi
echo ""

# 6. 生成修复报告
cat > SECURITY_FIX_REPORT.txt << EOF
========================================
安全修复报告
========================================
执行时间: $(date)

✅ 已完成:
1. 从 Git 仓库移除 .env 文件
2. 更新 .gitignore 排除敏感文件
3. 生成新的 SECRET_KEY
4. 创建 .env.local.template 模板

⚠️  需要手动操作:

1. 删除或移动本地 .env 文件:
   mv .env ~/.env.non-standard-pm

2. 更新生产环境的 SECRET_KEY:
   新密钥: $NEW_SECRET
   
   # Vercel
   - 访问 Vercel Dashboard
   - Settings → Environment Variables
   - 更新 SECRET_KEY
   
   # Docker
   - 更新 .env.production
   - 重新部署: docker-compose restart

3. 通知所有用户重新登录:
   ⚠️  所有现有 JWT Token 将失效

4. 审查代码中的硬编码密钥:
   grep -r "SECRET_KEY\|PASSWORD" app/ --exclude-dir=__pycache__

5. 推送更改到 GitHub:
   git push origin main

========================================
EOF

echo "✓ 已生成修复报告: SECURITY_FIX_REPORT.txt"
echo ""

# 7. 显示下一步
echo "=========================================="
echo "✅ 安全修复完成！"
echo "=========================================="
echo ""
echo "📋 下一步操作:"
echo ""
echo "1️⃣  查看修复报告:"
echo "   cat SECURITY_FIX_REPORT.txt"
echo ""
echo "2️⃣  移动敏感文件:"
echo "   mv .env ~/.env.non-standard-pm"
echo ""
echo "3️⃣  创建本地配置:"
echo "   cp .env.local.template .env.local"
echo "   # 编辑 .env.local 填入实际配置"
echo ""
echo "4️⃣  更新生产环境 SECRET_KEY:"
echo "   新密钥: $NEW_SECRET"
echo ""
echo "5️⃣  推送到 GitHub:"
echo "   git push origin main"
echo ""
echo "⚠️  重要提醒:"
echo "   - 所有用户需要重新登录"
echo "   - 更新 Vercel/Docker 环境变量"
echo "   - 检查其他硬编码密钥"
echo ""
