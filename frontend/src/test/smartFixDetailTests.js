/**
 * 智能修复：根据hook类型选择修复策略
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 需要传参数的hooks
const needsParamTests = [
  'src/pages/ArrivalDetail/hooks/__tests__/useArrivalDetail.test.js',
  'src/pages/SubstitutionDetail/hooks/__tests__/useSubstitutionDetail.test.js',
  'src/pages/ShortageReportDetail/hooks/__tests__/useShortageReportDetail.test.js',
  'src/pages/BiddingDetail/hooks/__tests__/useBiddingDetail.test.js',
  'src/pages/TechnicalReviewDetail/hooks/__tests__/useTechnicalReviewDetail.test.js',
  'src/pages/PurchaseRequestDetail/hooks/__tests__/usePurchaseRequestDetail.test.js',
  'src/pages/RdProjectDetail/hooks/__tests__/useRdProjectDetail.test.js',
  'src/pages/PurchaseOrderDetail/hooks/__tests__/usePurchaseOrderDetail.test.js',
  'src/pages/ProjectReviewDetail/hooks/__tests__/useProjectReviewDetail.test.js',
];

function fixTestFile(filePath, addParam = true) {
  const fullPath = path.join(process.cwd(), filePath);
  
  if (!fs.existsSync(fullPath)) {
    console.log(`⏭️  跳过 ${filePath} (文件不存在)`);
    return;
  }

  let content = fs.readFileSync(fullPath, 'utf8');
  
  const hookMatch = content.match(/import \{ (use\w+Detail) \}/);
  if (!hookMatch) {
    console.log(`⚠️  跳过 ${filePath} (找不到hook导入)`);
    return;
  }
  
  const hookName = hookMatch[1];
  
  if (addParam) {
    // 添加参数：renderHook(() => useXxxDetail()) → renderHook(() => useXxxDetail(1))
    content = content.replace(
      new RegExp(`renderHook\\(\\(\\) => ${hookName}\\(\\)\\)`, 'g'),
      `renderHook(() => ${hookName}(1))`
    );
    console.log(`✅ 修复 ${filePath} (添加参数)`);
  }
  
  fs.writeFileSync(fullPath, content, 'utf8');
}

console.log('🔧 智能修复Detail测试...\n');
console.log('修复需要参数的hooks:');
needsParamTests.forEach(f => fixTestFile(f, true));
console.log('\n✅ 完成！');
