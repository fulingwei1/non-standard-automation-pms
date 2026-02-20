/**
 * 分析哪些hooks需要参数，哪些使用useParams
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 检查hook是否使用useParams
function usesUseParams(hookPath) {
  const fullPath = path.join(process.cwd(), hookPath);
  if (!fs.existsSync(fullPath)) return null;
  
  const content = fs.readFileSync(fullPath, 'utf8');
  return content.includes('useParams');
}

// 检查hook是否接受参数
function acceptsParam(hookPath) {
  const fullPath = path.join(process.cwd(), hookPath);
  if (!fs.existsSync(fullPath)) return null;
  
  const content = fs.readFileSync(fullPath, 'utf8');
  
  // 查找函数定义
  const match = content.match(/export function use\w+Detail\s*\((.*?)\)/);
  if (!match) return null;
  
  return match[1].trim().length > 0;  // 有参数返回true
}

const detailHooks = [
  'src/pages/ArrivalDetail/hooks/useArrivalDetail.js',
  'src/pages/SubstitutionDetail/hooks/useSubstitutionDetail.js',
  'src/pages/ShortageReportDetail/hooks/useShortageReportDetail.js',
  'src/pages/BiddingDetail/hooks/useBiddingDetail.js',
  'src/pages/TechnicalReviewDetail/hooks/useTechnicalReviewDetail.js',
  'src/pages/PurchaseRequestDetail/hooks/usePurchaseRequestDetail.js',
  'src/pages/RdProjectDetail/hooks/useRdProjectDetail.js',
  'src/pages/PurchaseOrderDetail/hooks/usePurchaseOrderDetail.js',
  'src/pages/ProjectReviewDetail/hooks/useProjectReviewDetail.js',
  'src/pages/SolutionDetail/hooks/useSolutionDetail.js',
];

console.log('\n📊 Detail Hooks 分析：\n');
console.log('需要参数的hooks (传入ID):');
const needsParam = [];
const needsUseParams = [];

detailHooks.forEach(hookPath => {
  const hasParam = acceptsParam(hookPath);
  const hasUseParams = usesUseParams(hookPath);
  
  if (hasParam) {
    needsParam.push(hookPath);
    console.log(`  ✓ ${hookPath.split('/').slice(-3).join('/')}`);
  } else if (hasUseParams) {
    needsUseParams.push(hookPath);
  }
});

console.log('\n使用 useParams() 的hooks (不需要参数):');
needsUseParams.forEach(hookPath => {
  console.log(`  ✓ ${hookPath.split('/').slice(-3).join('/')}`);
});

console.log(`\n总计: ${needsParam.length} 需要参数, ${needsUseParams.length} 使用useParams\n`);
