#!/bin/bash
# 项目成本列表前端功能 - 快速部署脚本
# 使用方法: bash setup_cost_feature.sh

set -e

echo "🚀 开始部署项目成本列表前端功能..."
echo ""

# 检查当前目录
if [ ! -f "package.json" ]; then
  echo "❌ 错误: 请在 frontend 目录下运行此脚本"
  exit 1
fi

# 步骤1: 安装依赖
echo "📦 步骤1: 安装依赖..."
if command -v pnpm &> /dev/null; then
  echo "  使用 pnpm 安装 xlsx..."
  pnpm add xlsx
elif command -v npm &> /dev/null; then
  echo "  使用 npm 安装 xlsx..."
  npm install xlsx
else
  echo "❌ 错误: 未找到 npm 或 pnpm"
  exit 1
fi

echo "✅ 依赖安装完成"
echo ""

# 步骤2: 备份现有路由配置
echo "📝 步骤2: 备份路由配置..."
ROUTES_FILE="src/routes/modules/projectRoutes.jsx"
if [ -f "$ROUTES_FILE" ]; then
  cp "$ROUTES_FILE" "${ROUTES_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
  echo "✅ 已备份到: ${ROUTES_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
else
  echo "⚠️  警告: 路由文件不存在: $ROUTES_FILE"
fi
echo ""

# 步骤3: 更新路由配置
echo "🔧 步骤3: 更新路由配置..."
echo "  请手动执行以下步骤:"
echo ""
echo "  1. 编辑 src/routes/modules/projectRoutes.jsx"
echo "  2. 在文件顶部添加导入:"
echo "     import ProjectListWithCost from \"../../pages/ProjectListWithCost\";"
echo ""
echo "  3. 在 ProjectRoutes() 函数中添加路由:"
echo "     <Route path=\"/projects-cost\" element={<ProjectListWithCost />} />"
echo ""
echo "  或者替换现有的项目列表路由:"
echo "     <Route path=\"/projects\" element={<ProjectListWithCost />} />"
echo ""

# 步骤4: 检查文件是否存在
echo "🔍 步骤4: 检查文件完整性..."
FILES=(
  "src/lib/utils/cost.js"
  "src/components/project/ProjectCostFilter.jsx"
  "src/components/project/ProjectCostDetailDialog.jsx"
  "src/pages/ProjectListWithCost.jsx"
)

ALL_OK=true
for FILE in "${FILES[@]}"; do
  if [ -f "$FILE" ]; then
    echo "  ✅ $FILE"
  else
    echo "  ❌ $FILE (缺失)"
    ALL_OK=false
  fi
done
echo ""

if [ "$ALL_OK" = true ]; then
  echo "✅ 所有文件检查完成"
else
  echo "⚠️  部分文件缺失，请检查"
fi
echo ""

# 步骤5: 提示启动开发服务器
echo "🎉 部署准备完成！"
echo ""
echo "📖 接下来的步骤:"
echo "  1. 手动更新路由配置（见上方说明）"
echo "  2. 启动开发服务器: npm run dev 或 pnpm dev"
echo "  3. 访问 http://localhost:5173/projects-cost"
echo "  4. 测试功能"
echo ""
echo "📚 参考文档:"
echo "  - ../PROJECT_COST_FRONTEND_IMPLEMENTATION.md"
echo "  - ../docs/guides/project_cost_list_usage.md"
echo ""
