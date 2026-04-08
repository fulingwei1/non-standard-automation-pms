const fs = require('fs');
const path = require('path');

const testDir = path.join(__dirname, 'src/pages/__tests__');

// 递归查找所有测试文件
function findTestFiles(dir) {
    const files = [];
    function walk(dir) {
        try {
            const items = fs.readdirSync(dir);
            for (const item of items) {
                const fullPath = path.join(dir, item);
                const stat = fs.statSync(fullPath);
                if (stat.isDirectory()) {
                    if (!item.includes('node_modules')) {
                        walk(fullPath);
                    }
                } else if (item.match(/\.test\.(js|jsx|ts|tsx)$/)) {
                    files.push(fullPath);
                }
            }
        } catch (e) {
            // skip
        }
    }
    walk(dir);
    return files;
}

function fixMockData(content) {
    let modified = false;
    let result = content;

    // 修复: Promise.resolve({ data: {} }) => Promise.resolve({ data: { items: [] } })
    // 使用简单的字符串替换
    if (result.includes('{ data: {} }')) {
        // 确保只替换 Promise.resolve 中的
        result = result.split('Promise.resolve({ data: {} })').join('Promise.resolve({ data: { items: [] } })');
        modified = true;
    }

    return { content: result, modified };
}

function main() {
    console.log('查找测试文件...');
    const testFiles = findTestFiles(testDir);
    console.log(`找到 ${testFiles.length} 个测试文件`);

    let fixed = 0;
    const errors = [];

    for (const file of testFiles) {
        try {
            const content = fs.readFileSync(file, 'utf8');
            const { content: newContent, modified } = fixMockData(content);

            if (modified) {
                fs.writeFileSync(file, newContent, 'utf8');
                console.log(`修复: ${path.relative(__dirname, file)}`);
                fixed++;
            }
        } catch (e) {
            errors.push({ file, error: e.message });
        }
    }

    console.log(`\n修复了 ${fixed} 个测试文件`);

    if (errors.length > 0) {
        console.log(`\n错误:`);
        for (const { file, error } of errors) {
            console.log(`  ${path.relative(__dirname, file)}: ${error}`);
        }
    }
}

main();