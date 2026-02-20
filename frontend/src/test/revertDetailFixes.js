/**
 * 撤销之前的修复 - 这些hooks使用useParams，不需要参数
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const detailTests = [
  'src/pages/SolutionDetail/hooks/__tests__/useSolutionDetail.test.js',
  'src/pages/SubstitutionDetail/hooks/__tests__/useSubstitutionDetail.test.js',
  'src/pages/ShortageReportDetail/hooks/__tests__/useShortageReportDetail.test.js',
  'src/pages/TechnicalReviewDetail/hooks/__tests__/useTechnicalReviewDetail.test.js',
  'src/pages/RdProjectDetail/hooks/__tests__/useRdProjectDetail.test.js',
  'src/pages/PurchaseRequestDetail/hooks/__tests__/usePurchaseRequestDetail.test.js',
  'src/pages/PurchaseOrderDetail/hooks/__tests__/usePurchaseOrderDetail.test.js',
  'src/pages/ProjectReviewDetail/hooks/__tests__/useProjectReviewDetail.test.js',
];

function revertTestFile(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  
  if (!fs.existsSync(fullPath)) {
    console.log(`⏭️  跳过 ${filePath} (文件不存在)`);
    return;
  }

  let content = fs.readFileSync(fullPath, 'utf8');
  
  // 提取hook名称
  const hookMatch = content.match(/import \{ (use\w+Detail) \}/);
  if (!hookMatch) {
    console.log(`⚠️  跳过 ${filePath} (找不到hook导入)`);
    return;
  }
  
  const hookName = hookMatch[1];
  
  // 撤销：renderHook(() => useXxxDetail(1)) → renderHook(() => useXxxDetail())
  content = content.replace(
    new RegExp(`renderHook\\(\\(\\) => ${hookName}\\(1\\)\\)`, 'g'),
    `renderHook(() => ${hookName}())`
  );
  
  fs.writeFileSync(fullPath, content, 'utf8');
  console.log(`✅ 撤销 ${filePath}`);
}

console.log('🔄 撤销之前的修复...\n');
detailTests.forEach(revertTestFile);
console.log('\n✅ 完成！');
