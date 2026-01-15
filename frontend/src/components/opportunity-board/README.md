# Opportunity Board Components

商机看板组件集，提供完整的商机管理功能，包括看板视图、过滤器和商机卡片。

## 组件列表

### 1. OpportunityBoardConstants.js
商机看板常量配置文件，包含：
- 商机状态配置
- 商机阶段配置（线索获取、资格确认、方案提交、商务谈判、成交、流失）
- 优先级配置（高、中、低）
- 商机来源配置（官网、推荐、展会、电话、社交媒体、合作伙伴）
- 商机类型配置（标准设备、定制设备、设备升级、技术服务、耗材销售）
- 商机规模配置（小、中、大、特大）
- 预计成交时间配置（本周、本月、下月、下季度、更晚）
- 快速过滤器配置
- 工具函数（过滤、排序、健康度计算等）

### 2. OpportunityCard.jsx
单个商机卡片组件，功能包括：
- 显示商机基本信息（名称、客户、联系人、预计金额等）
- 优先级和阶段标签
- 成交进度条
- 健康度指示器
- 预计成交时间提醒
- 拖拽功能支持
- 右键菜单操作（编辑、查看、阶段变更、删除等）
- 详情对话框

### 3. OpportunityFilters.jsx
商机过滤器组件，提供：
- 搜索功能（支持商机名称、客户公司搜索）
- 快速过滤器（我的商机、高价值、紧急、重点跟进）
- 高级过滤选项：
  - 状态过滤
  - 阶段过滤
  - 优先级过滤
  - 来源过滤
  - 类型过滤
  - 规模过滤
  - 金额范围过滤
  - 创建时间范围过滤
  - 排序选项

### 4. OpportunityPipeline.jsx
商机管道视图组件，支持：
- 看板视图（按阶段分列显示）
- 列表视图
- 统计视图（阶段分布、金额分布、转化漏斗）
- 拖拽阶段变更
- 商机批量选择
- 实时统计信息显示
- 响应式设计

## 使用示例

### 基本使用

```jsx
import OpportunityPipeline from './components/opportunity-board';

function OpportunityBoardPage() {
  const [opportunities, setOpportunities] = useState([]);

  const handleStageChange = (opportunityId, newStage) => {
    // 更新商机的阶段
    setOpportunities(prev => prev.map(opp =>
      opp.id === opportunityId ? { ...opp, stage: newStage } : opp
    ));
  };

  const handleEdit = (opportunity) => {
    // 编辑商机
    console.log('Edit opportunity:', opportunity);
  };

  const handleDelete = (opportunity) => {
    // 删除商机
    if (window.confirm('确定要删除这个商机吗？')) {
      setOpportunities(prev => prev.filter(opp => opp.id !== opportunity.id));
    }
  };

  const handleView = (opportunity) => {
    // 查看商机详情
    console.log('View opportunity:', opportunity);
  };

  return (
    <div className="h-screen p-4">
      <OpportunityPipeline
        opportunities={opportunities}
        onStageChange={handleStageChange}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onView={handleView}
        refreshTrigger={refreshTrigger}
        onRefresh={fetchOpportunities}
      />
    </div>
  );
}
```

### 自定义过滤器

```jsx
import OpportunityFilters from './components/opportunity-board';

function CustomFilterSection() {
  const [filters, setFilters] = useState({});

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    // 应用过滤器到商机列表
    applyFilters(newFilters);
  };

  return (
    <OpportunityFilters
      onFilterChange={handleFilterChange}
      initialFilters={filters}
      showQuickFilters={true}
      showAdvancedFilters={true}
    />
  );
}
```

### 独立使用商机卡片

```jsx
import OpportunityCard from './components/opportunity-board';

function SingleOpportunityCard() {
  const opportunity = {
    id: 1,
    name: '自动化测试设备项目',
    company_name: 'XX科技有限公司',
    contact_person: '张三',
    contact_phone: '13800138000',
    contact_email: 'zhangsan@example.com',
    stage: 'negotiation',
    priority: 'high',
    source: 'exhibition',
    type: 'custom_equipment',
    size: 'large',
    expected_amount: 2500000,
    win_probability: 75,
    created_at: '2024-01-15',
    expected_close_date: '2024-03-01',
    description: '客户需要一套定制化的自动化测试设备...',
    notes: '需要重点关注客户的技术要求...'
  };

  return (
    <div className="max-w-md">
      <OpportunityCard
        opportunity={opportunity}
        onEdit={(opp) => console.log('Edit:', opp)}
        onDelete={(opp) => console.log('Delete:', opp)}
        onView={(opp) => console.log('View:', opp)}
        onStageChange={(id, stage) => console.log('Stage change:', id, stage)}
      />
    </div>
  );
}
```

## 商机数据结构示例

```javascript
const opportunityData = {
  // 基础信息
  id: 1,
  name: "自动化测试设备项目",

  // 客户信息
  company_name: "XX科技有限公司",
  contact_person: "张三",
  contact_phone: "13800138000",
  contact_email: "zhangsan@example.com",

  // 商机信息
  stage: "negotiation",           // 阶段：lead, qualification, proposal, negotiation, closed_won, closed_lost
  status: "CONTACTING",           // 状态：NEW, CONTACTING, QUALIFIED, PROPOSAL, NEGOTIATING, CLOSED_WON, CLOSED_LOST, ON_HOLD
  priority: "high",               // 优先级：high, medium, low
  source: "exhibition",          // 来源：website, referral, exhibition, cold_call, social_media, partner, other
  type: "custom_equipment",      // 类型：standard_equipment, custom_equipment, upgrade, service, consumables
  size: "large",                 // 规模：small, medium, large, xlarge

  // 金额信息
  expected_amount: 2500000,      // 预计金额
  win_probability: 75,           // 成交概率（百分比）

  // 时间信息
  created_at: "2024-01-15",
  last_contact_date: "2024-01-20",
  expected_close_date: "2024-03-01",

  // 描述信息
  description: "客户需要一套定制化的自动化测试设备，用于ICT测试",
  notes: "重点关注客户的技术要求，需要与研发部门沟通"
};
```

## 配置自定义

可以通过修改 `opportunityBoardConstants.js` 来自定义：

```javascript
// 自定义阶段配置
const customStageConfig = {
  qualification: {
    label: "初步筛选",
    color: "bg-blue-400 bg-blue-400/10 text-blue-600 border-blue-400/30"
    // ...其他配置
  }
};

// 自定义优先级配置
const customPriorityConfig = {
  urgent: {
    label: "紧急",
    color: "bg-red-600 bg-red-600/10 text-red-700 border-red-600/30"
    // ...其他配置
  }
};

// 在组件中使用自定义配置
import { OpportunityPipeline } from './components/opportunity-board';
```

## 注意事项

1. **拖拽功能**：需要安装 `react-dnd` 和 `react-dnd-html5-backend`
2. **样式依赖**：使用了 Tailwind CSS 和 shadcn/ui 组件
3. **图标**：使用 Lucide React 图标库
4. **动画**：使用 Framer Motion 实现动画效果
5. **响应式**：组件支持响应式布局

## 依赖安装

```bash
npm install react-dnd react-dnd-html5-backend framer-motion
```