#!/bin/bash

# Vercel + Supabase 部署辅助脚本

set -e

echo "=========================================="
echo "Vercel + Supabase 部署准备"
echo "=========================================="
echo ""

# 检查必要工具
echo "🔍 检查环境..."

if ! command -v git &> /dev/null; then
    echo "❌ Git 未安装"
    exit 1
fi
echo "✓ Git 已安装"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi
echo "✓ Node.js 已安装"

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi
echo "✓ npm 已安装"
echo ""

# 检查前端构建
echo "📦 构建前端..."
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend && npm ci && cd ..
fi

cd frontend && npm run build && cd ..
echo "✓ 前端构建完成"
echo ""

# 检查 Git 状态
echo "📋 检查 Git 状态..."
if [ -d ".git" ]; then
    echo "✓ Git 仓库已存在"
    
    # 显示当前状态
    if git remote -v | grep -q "origin"; then
        echo "✓ Git remote 已配置"
        git remote -v
    else
        echo "⚠️  Git remote 未配置"
        echo ""
        echo "请在 GitHub 创建仓库，然后运行："
        echo "  git remote add origin https://github.com/你的用户名/仓库名.git"
    fi
else
    echo "初始化 Git 仓库..."
    git init
    echo "✓ Git 仓库已初始化"
    echo ""
    echo "⚠️  需要配置 Git remote:"
    echo "  1. 在 GitHub 创建新仓库"
    echo "  2. 运行: git remote add origin https://github.com/你的用户名/仓库名.git"
fi
echo ""

# 检查部署文件
echo "📁 检查部署文件..."
files=("vercel.json" "api/index.py" "api/requirements.txt" "supabase-setup.sql")
all_exist=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "❌ 缺少: $file"
        all_exist=false
    fi
done
echo ""

if [ "$all_exist" = false ]; then
    echo "❌ 部分文件缺失，请检查项目完整性"
    exit 1
fi

# 生成 SECRET_KEY
echo "🔐 生成 SECRET_KEY..."
SECRET_KEY=$(openssl rand -base64 32)
echo "你的 SECRET_KEY（请保存）:"
echo "$SECRET_KEY"
echo ""

# 创建环境变量模板
echo "📝 创建环境变量配置..."
cat > .env.vercel.example << EOF
# Vercel 环境变量配置（复制到 Vercel Dashboard）

# 1. DATABASE_URL（从 Supabase 获取）
DATABASE_URL=postgresql://postgres:你的密码@db.xxx.supabase.co:5432/postgres

# 2. SECRET_KEY（已生成）
SECRET_KEY=$SECRET_KEY

# 3. 可选配置
DEBUG=false
CORS_ORIGINS=https://your-app.vercel.app
EOF

echo "✓ 已创建 .env.vercel.example"
echo ""

# 提交代码
echo "💾 准备提交代码..."
git add .

if git diff --staged --quiet; then
    echo "没有新的更改需要提交"
else
    echo "有新的更改，创建提交..."
    git commit -m "chore: prepare for Vercel + Supabase deployment" || true
    echo "✓ 代码已提交"
fi
echo ""

# 显示下一步指令
echo "=========================================="
echo "✅ 准备完成！"
echo "=========================================="
echo ""
echo "📋 下一步操作："
echo ""
echo "1️⃣  配置 Supabase 数据库"
echo "   • 访问: https://supabase.com"
echo "   • 创建项目，获取数据库连接字符串"
echo "   • 在 SQL Editor 执行 supabase-setup.sql"
echo ""
echo "2️⃣  推送代码到 GitHub"
echo "   • 创建 GitHub 仓库（如果还没有）"
echo "   • git remote add origin <你的仓库URL>"
echo "   • git push -u origin main"
echo ""
echo "3️⃣  部署到 Vercel"
echo "   • 访问: https://vercel.com"
echo "   • Import GitHub 仓库"
echo "   • 添加环境变量（见 .env.vercel.example）"
echo "   • 点击 Deploy"
echo ""
echo "📄 详细步骤请查看:"
echo "   • 免费云部署指南.md（中文）"
echo "   • VERCEL_SUPABASE_DEPLOYMENT.md（详细）"
echo ""
echo "🔑 你的 SECRET_KEY（请复制到 Vercel）:"
echo "$SECRET_KEY"
echo ""
