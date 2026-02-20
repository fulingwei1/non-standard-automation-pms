/**
 * 批量修复Detail测试的脚本
 * 问题：Detail hooks需要ID参数，但测试中没有提供
 * 解决：为每个测试添加mock ID参数
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 需要修复的测试文件列表
const detailTests = [
  'src/pages/ArrivalDetail/hooks/__tests__/useArrivalDetail.test.js',
  'src/pages/SubstitutionDetail/hooks/__tests__/useSubstitutionDetail.test.js',
  'src/pages/ShortageReportDetail/hooks/__tests__/useShortageReportDetail.test.js',
  'src/pages/BiddingDetail/hooks/__tests__/useBiddingDetail.test.js',
  'src/pages/TechnicalReviewDetail/hooks/__tests__/useTechnicalReviewDetail.test.js',
  'src/pages/PurchaseRequestDetail/hooks/__tests__/usePurchaseRequestDetail.test.js',
  'src/pages/RdProjectDetail/hooks/__tests__/useRdProjectDetail.test.js',
  'src/pages/PurchaseOrderDetail/hooks/__tests__/usePurchaseOrderDetail.test.js',
  'src/pages/ProjectReviewDetail/hooks/__tests__/useProjectReviewDetail.test.js',
  'src/pages/SolutionDetail/hooks/__tests__/useSolutionDetail.test.js',
];

// 修复单个测试文件
function fixTestFile(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  
  if (!fs.existsSync(fullPath)) {
    console.log(`⏭️  跳过 ${filePath} (文件不存在)`);
    return;
  }

  let content = fs.readFileSync(fullPath, 'utf8');
  
  // 检查是否已经修复过
  if (content.includes('renderHook(() => use') && content.includes('(1)')) {
    console.log(`⏭️  跳过 ${filePath} (已修复)`);
    return;
  }

  // 提取hook名称 (如 useArrivalDetail)
  const hookMatch = content.match(/import \{ (use\w+Detail) \}/);
  if (!hookMatch) {
    console.log(`⚠️  跳过 ${filePath} (找不到hook导入)`);
    return;
  }
  
  const hookName = hookMatch[1];
  
  // 修复：renderHook(() => useXxxDetail()) → renderHook(() => useXxxDetail(1))
  content = content.replace(
    new RegExp(`renderHook\\(\\(\\) => ${hookName}\\(\\)\\)`, 'g'),
    `renderHook(() => ${hookName}(1))`
  );
  
  // 写回文件
  fs.writeFileSync(fullPath, content, 'utf8');
  console.log(`✅ 修复 ${filePath}`);
}

// 批量修复
console.log('🔧 开始批量修复Detail测试...\n');
detailTests.forEach(fixTestFile);
console.log('\n✅ 修复完成！');
