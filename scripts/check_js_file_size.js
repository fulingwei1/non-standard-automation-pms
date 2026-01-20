/**
 * JavaScript/JSX 文件大小检查脚本
 * 
 * 用于CI检查前端文件是否超过行数限制
 */

const fs = require('fs');
const path = require('path');

// 配置
const LIMITS = {
    '.js': 500,
    '.jsx': 500,
    '.ts': 500,
    '.tsx': 500,
    '.css': 300,
};

const EXCLUDE_DIRS = new Set([
    'node_modules',
    'dist',
    'build',
    '.next',
    '.git',
]);

const EXCLUDE_FILES = new Set([
    'index.js',
    'constants.js',
]);

/**
 * 计算文件行数
 */
function countLines(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return content.split('\n').length;
    } catch (e) {
        return 0;
    }
}

/**
 * 递归检查目录
 */
function checkDirectory(dir, violations = []) {
    const items = fs.readdirSync(dir);

    for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
            if (!EXCLUDE_DIRS.has(item)) {
                checkDirectory(fullPath, violations);
            }
        } else {
            const ext = path.extname(item);
            const limit = LIMITS[ext];

            if (limit && !EXCLUDE_FILES.has(item)) {
                const lines = countLines(fullPath);

                if (lines > limit) {
                    violations.push({
                        path: fullPath,
                        lines,
                        limit,
                        over: lines - limit,
                    });
                }
            }
        }
    }

    return violations;
}

/**
 * 主函数
 */
function main() {
    console.log('📏 检查JavaScript/JSX文件大小限制...\n');

    const srcDir = path.join(__dirname, '..', 'frontend', 'src');

    if (!fs.existsSync(srcDir)) {
        console.log('⚠️ 前端源码目录不存在\n');
        return 0;
    }

    const violations = checkDirectory(srcDir);

    if (violations.length > 0) {
        // 按超出行数排序
        violations.sort((a, b) => b.over - a.over);

        console.log(`❌ 发现 ${violations.length} 个文件超过行数限制:\n`);

        for (const v of violations) {
            console.log(`  📄 ${v.path}`);
            console.log(`     行数: ${v.lines} (限制: ${v.limit}, 超出: +${v.over}行)\n`);
        }

        console.log('💡 建议: 请参考 docs/CODE_STANDARDS.md 进行重构\n');
        return 1;
    } else {
        console.log('✅ 所有文件都在行数限制内\n');
        return 0;
    }
}

process.exit(main());
