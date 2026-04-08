const fs = require('fs');
const path = require('path');

const testDir = path.join(__dirname, 'src');

// Find all test files that have the problematic mock pattern
function findTestFiles() {
  const files = [];
  
  function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory() && entry.name !== 'node_modules') {
        walk(fullPath);
      } else if (entry.name.endsWith('.test.js') || entry.name.endsWith('.test.jsx')) {
        files.push(fullPath);
      }
    }
  }
  
  walk(path.join(testDir, 'pages'));
  walk(path.join(testDir, 'hooks'));
  
  return files;
}

// Extract API imports from a test file
function extractApiImports(content, testFilePath) {
  const importRegex = /import\s+\{([^}]+)\}\s+from\s+['"]([^'"]*services\/api)['"]/g;
  const apis = [];
  const apiPathMatch = content.match(/vi\.mock\(['"]([^'"]*services\/api)['"]/);
  const mockPath = apiPathMatch ? apiPathMatch[1] : null;
  
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    const importContent = match[1];
    for (const item of importContent.split(',')) {
      const trimmed = item.trim();
      if (trimmed.includes(' as ')) {
        const alias = trimmed.split(' as ')[1].trim();
        apis.push(alias);
      } else {
        apis.push(trimmed);
      }
    }
  }
  
  return { apis, mockPath };
}

// Common API methods to mock
const commonMethods = [
  'list', 'get', 'create', 'update', 'delete', 'query',
  'getAll', 'getById', 'getDetail', 'export', 'import',
  'submit', 'approve', 'reject', 'cancel', 'reset',
  'getStatistics', 'getOptions', 'batch', 'upload', 'download',
  'getWeightConfig', 'updateWeightConfig',
  'getWeek', 'aiMatch', 'getWorkspace', 'getBonuses', 'getMeetings',
  'getIssues', 'getSolutions', 'getTasks', 'getEmployees',
  'getProjects', 'getSummary', 'getTrend', 'getDistribution',
  'getItems', 'getTotal', 'getPending', 'getActive',
  'linkMeeting', 'getCost', 'getBudget', 'getActual',
  'getRevenue', 'getCostSummary', 'getProfit',
  'getMaterials', 'getBom', 'getInventory'
];

// Generate mock configuration
function generateMockConfig(apis) {
  const config = {};
  
  for (const api of apis) {
    config[api] = {};
    for (const method of commonMethods) {
      config[api][method] = 'vi.fn()';
    }
  }
  
  return config;
}

// Format mock code
function formatMockCode(mockPath, config) {
  const lines = [
    `vi.mock('${mockPath}', async (importOriginal) => {`,
    `  const actual = await importOriginal();`,
    `  return {`,
    `    ...actual,`,
    `    default: {`,
    `      get: vi.fn(),`,
    `      post: vi.fn(),`,
    `      put: vi.fn(),`,
    `      delete: vi.fn(),`,
    `      patch: vi.fn(),`,
    `      defaults: { baseURL: '/api' },`,
    `    },`
  ];
  
  for (const [apiName, methods] of Object.entries(config)) {
    lines.push(`    ${apiName}: {`);
    for (const [method, fn] of Object.entries(methods)) {
      lines.push(`      ${method}: ${fn},`);
    }
    lines.push(`    },`);
  }
  
  lines.push(`  };`);
  lines.push(`});`);
  
  return lines.join('\n');
}

// Process each test file
function processTestFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Check if this file has the problematic mock pattern
  if (!content.includes('api.list.mockResolvedValue') && 
      !content.includes('api.get.mockResolvedValue') &&
      !content.includes('api.query.mockResolvedValue')) {
    return false;
  }
  
  // Extract API imports
  const { apis, mockPath } = extractApiImports(content, filePath);
  
  if (apis.length === 0 || !mockPath) {
    console.log(`  Skipping ${filePath} - no APIs found or no mock path`);
    return false;
  }
  
  // Generate mock configuration
  const config = generateMockConfig(apis);
  const mockCode = formatMockCode(mockPath, config);
  
  // Replace the existing mock
  const mockRegex = /vi\.mock\(['"][^'"]*services\/api['"],\s*async\s*\(importOriginal\)\s*=>\s*\{[\s\S]*?^\}\);/m;
  const newContent = content.replace(mockRegex, mockCode);
  
  if (newContent !== content) {
    fs.writeFileSync(filePath, newContent);
    console.log(`Fixed: ${filePath}`);
    console.log(`  APIs: ${apis.join(', ')}`);
    return true;
  }
  
  return false;
}

// Main
console.log('Finding test files...');
const testFiles = findTestFiles();
console.log(`Found ${testFiles.length} test files`);

let fixed = 0;
for (const file of testFiles) {
  if (processTestFile(file)) {
    fixed++;
  }
}

console.log(`\nFixed ${fixed} test files`);