const fs = require('fs');
const path = require('path');

const testDir = path.join(__dirname, 'src');

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

    // 关键：只修复 { data: {} } 这种情况，不修改 { data: { success: true } } 等情况
    // 精确匹配: mockResolvedValue({ data: {} }) 后面是 ) 或 ,
    // 使用负向前瞻确保不是 { data: { ... } } 格式
    
    // 修复: { data: {} } => { data: { items: [] } } 
    // 只匹配 data: {} 后面没有其他属性的情况（即只有 data: {}）
    
    // 方案：匹配 "data: {}" 前面是空格或换行，后面是 "})" 或 "},"
    const pattern1 = /(\.mockResolvedValue\(\{)\s*data:\s*\{\}\s*(\}\))/g;
    result = result.replace(pattern1, (match, prefix, suffix) => {
        modified = true;
        return `${prefix}data: { items: [] }${suffix}`;
    });

    // 针对 mockResolvedValueOnce
    const pattern2 = /(\.mockResolvedValueOnce\(\{)\s*data:\s*\{\}\s*(\}\))/g;
    result = result.replace(pattern2, (match, prefix, suffix) => {
        modified = true;
        return `${prefix}data: { items: [] }${suffix}`;
    });

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