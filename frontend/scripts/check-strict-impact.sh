#!/bin/bash
# 检查启用严格 ESLint 配置后的影响

echo "🔍 检查严格 ESLint 配置的影响..."
echo ""

# 备份当前配置
echo "📋 步骤 1: 备份当前配置..."
cp eslint.config.js eslint.config.backup.js 2>/dev/null || true
echo "✅ 已备份到 eslint.config.backup.js"
echo ""

# 临时启用严格配置
echo "📋 步骤 2: 临时启用严格配置..."
cp eslint.config.strict.js eslint.config.js
echo "✅ 已临时启用严格配置"
echo ""

# 运行 ESLint 检查
echo "📋 步骤 3: 运行 ESLint 检查..."
npm run lint > eslint-strict-report.txt 2>&1 || true

# 统计错误和警告
ERRORS=$(grep -oE "[0-9]+ error\(s\)" eslint-strict-report.txt | grep -oE "[0-9]+" | head -1 || echo "0")
WARNINGS=$(grep -oE "[0-9]+ warning\(s\)" eslint-strict-report.txt | grep -oE "[0-9]+" | head -1 || echo "0")

# 恢复原配置
echo "📋 步骤 4: 恢复原配置..."
cp eslint.config.backup.js eslint.config.js
echo "✅ 已恢复原配置"
echo ""

# 输出统计
echo "============================================================"
echo "📊 检查结果统计"
echo "============================================================"
echo "❌ 错误数量: ${ERRORS:-0}"
echo "⚠️  警告数量: ${WARNINGS:-0}"
echo "📝 总计: $(( ${ERRORS:-0} + ${WARNINGS:-0} ))"
echo "============================================================"
echo ""
echo "📄 详细报告已保存到: eslint-strict-report.txt"
echo ""

# 给出建议
if [ "${ERRORS:-0}" -eq 0 ] && [ "${WARNINGS:-0}" -eq 0 ]; then
    echo "✅ 可以安全启用严格配置！"
    echo "   运行: cp eslint.config.strict.js eslint.config.js"
elif [ "${ERRORS:-0}" -lt 50 ]; then
    echo "⚠️  发现少量问题，建议先修复后再启用"
    echo "   1. 查看详细报告: cat eslint-strict-report.txt"
    echo "   2. 运行自动修复: npm run lint -- --fix"
    echo "   3. 手动修复剩余问题"
    echo "   4. 启用严格配置: cp eslint.config.strict.js eslint.config.js"
elif [ "${ERRORS:-0}" -lt 200 ]; then
    echo "⚠️  发现较多问题，建议分阶段修复"
    echo "   参考: frontend/ENABLE_STRICT_ESLINT.md"
else
    echo "❌ 发现大量问题，建议渐进式启用"
    echo "   参考: frontend/ENABLE_STRICT_ESLINT.md"
fi
echo ""
