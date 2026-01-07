<template>
  <div class="business-support-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>商务支持工作台</h1>
        <p class="subtitle">合同管理 · 订单处理 · 回款跟踪</p>
      </div>
      <div class="header-right">
        <div class="quick-search">
          <input type="text" v-model="searchKeyword" placeholder="搜索合同/客户/订单..." />
          <span class="search-icon">🔍</span>
        </div>
      </div>
    </header>

    <!-- 待办事项卡片 -->
    <section class="todo-section">
      <h2>待办事项 <span class="todo-count">{{ todos.length }}</span></h2>
      <div class="todo-cards">
        <div class="todo-card urgent" v-for="todo in urgentTodos" :key="todo.id" @click="handleTodo(todo)">
          <div class="todo-header">
            <span class="todo-type">{{ todo.type_label }}</span>
            <span class="todo-priority">紧急</span>
          </div>
          <h4 class="todo-title">{{ todo.title }}</h4>
          <p class="todo-desc">{{ todo.description }}</p>
          <div class="todo-meta">
            <span>{{ todo.customer_name }}</span>
            <span v-if="todo.amount">¥{{ formatMoney(todo.amount) }}</span>
          </div>
        </div>
        
        <div class="todo-card important" v-for="todo in importantTodos" :key="todo.id" @click="handleTodo(todo)">
          <div class="todo-header">
            <span class="todo-type">{{ todo.type_label }}</span>
            <span class="todo-priority">重要</span>
          </div>
          <h4 class="todo-title">{{ todo.title }}</h4>
          <p class="todo-desc">{{ todo.description }}</p>
          <div class="todo-meta">
            <span>{{ todo.customer_name }}</span>
            <span v-if="todo.due_date">{{ todo.due_date }}</span>
          </div>
        </div>
      </div>
      <button class="view-all-btn" @click="showAllTodos = true">
        查看全部待办 ({{ todos.length }})
      </button>
    </section>

    <!-- 关键指标 -->
    <section class="metrics-section">
      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-icon">📝</span>
          <span class="metric-title">本月合同</span>
        </div>
        <div class="metric-body">
          <div class="metric-main">
            <span class="metric-value">{{ metrics.contract.newCount }}</span>
            <span class="metric-unit">份</span>
          </div>
          <div class="metric-sub">
            <span>金额 ¥{{ formatMoney(metrics.contract.newAmount) }}</span>
          </div>
        </div>
        <div class="metric-footer">
          <span class="pending">待审核 {{ metrics.contract.pendingReview }}</span>
          <span class="pending">待盖章 {{ metrics.contract.pendingSeal }}</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-icon">📄</span>
          <span class="metric-title">本月开票</span>
        </div>
        <div class="metric-body">
          <div class="metric-main">
            <span class="metric-value">¥{{ formatMoney(metrics.invoice.monthAmount) }}</span>
          </div>
          <div class="metric-sub">
            <span>待开票 {{ metrics.invoice.pending }} 笔</span>
          </div>
        </div>
        <div class="metric-footer">
          <span>待开金额 ¥{{ formatMoney(metrics.invoice.pendingAmount) }}</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-icon">💰</span>
          <span class="metric-title">本月回款</span>
        </div>
        <div class="metric-body">
          <div class="metric-main">
            <span class="metric-value">¥{{ formatMoney(metrics.collection.monthAmount) }}</span>
          </div>
          <div class="metric-sub">
            <span>回款率 {{ metrics.collection.collectionRate }}%</span>
          </div>
        </div>
        <div class="metric-footer warning">
          <span>逾期 {{ metrics.collection.overdue }} 笔</span>
          <span>¥{{ formatMoney(metrics.collection.overdueAmount) }}</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-header">
          <span class="metric-icon">✅</span>
          <span class="metric-title">验收跟踪</span>
        </div>
        <div class="metric-body">
          <div class="metric-main">
            <span class="metric-value">{{ metrics.acceptance.pending }}</span>
            <span class="metric-unit">待验收</span>
          </div>
          <div class="metric-sub">
            <span>跟踪中 {{ metrics.acceptance.tracking }}</span>
          </div>
        </div>
        <div class="metric-footer">
          <span>质保即将到期 {{ metrics.acceptance.warrantyExpiring }}</span>
        </div>
      </div>
    </section>

    <!-- 主要功能区 -->
    <section class="main-section">
      <!-- 标签页 -->
      <div class="tab-header">
        <button :class="{ active: activeTab === 'contracts' }" @click="activeTab = 'contracts'">
          合同管理
        </button>
        <button :class="{ active: activeTab === 'delivery' }" @click="activeTab = 'delivery'">
          出货审批
        </button>
        <button :class="{ active: activeTab === 'collection' }" @click="activeTab = 'collection'">
          回款跟踪
        </button>
        <button :class="{ active: activeTab === 'acceptance' }" @click="activeTab = 'acceptance'">
          验收管理
        </button>
      </div>

      <!-- 合同管理 -->
      <div class="tab-content" v-if="activeTab === 'contracts'">
        <div class="content-toolbar">
          <div class="filter-group">
            <select v-model="contractFilter.status">
              <option value="">全部状态</option>
              <option value="reviewing">审核中</option>
              <option value="pending_seal">待盖章</option>
              <option value="executing">执行中</option>
            </select>
            <select v-model="contractFilter.riskLevel">
              <option value="">全部风险</option>
              <option value="high">高风险</option>
              <option value="medium">中风险</option>
              <option value="low">低风险</option>
            </select>
          </div>
        </div>

        <div class="contract-list">
          <div class="contract-item" v-for="contract in contracts" :key="contract.id" @click="showContractDetail(contract)">
            <div class="contract-main">
              <div class="contract-header">
                <span class="contract-no">{{ contract.contract_no }}</span>
                <span class="contract-status" :class="contract.contract_status">
                  {{ contract.contract_status_label }}
                </span>
                <span class="seal-status" :class="contract.seal_status">
                  {{ contract.seal_status_label }}
                </span>
              </div>
              <h4 class="contract-name">{{ contract.contract_name }}</h4>
              <div class="contract-info">
                <span class="customer">{{ contract.customer_name }}</span>
                <span class="amount">¥{{ formatMoney(contract.contract_amount) }}</span>
              </div>
              <div class="payment-summary">
                <span class="label">付款条款:</span>
                <span class="value">{{ contract.payment_summary }}</span>
              </div>
            </div>
            
            <!-- 风险提示 -->
            <div class="risk-panel" v-if="contract.risk_items?.length">
              <span class="risk-level" :class="contract.risk_level">
                {{ contract.risk_level === 'high' ? '高风险' : contract.risk_level === 'medium' ? '中风险' : '低风险' }}
              </span>
              <div class="risk-items">
                <span class="risk-item" v-for="(risk, idx) in contract.risk_items" :key="idx">
                  ⚠️ {{ risk.desc }}
                </span>
              </div>
            </div>

            <div class="contract-actions">
              <button class="btn-action" v-if="contract.business_review_status === 'pending'" @click.stop="reviewContract(contract)">
                商务审核
              </button>
              <button class="btn-action" v-if="contract.seal_status === 'pending'" @click.stop="requestSeal(contract)">
                申请盖章
              </button>
              <button class="btn-action" v-if="contract.seal_status === 'sealed'" @click.stop="requestMail(contract)">
                申请邮寄
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 出货审批 -->
      <div class="tab-content" v-if="activeTab === 'delivery'">
        <div class="delivery-list">
          <div class="delivery-item" v-for="delivery in deliveryApprovals" :key="delivery.id">
            <div class="delivery-main">
              <div class="delivery-header">
                <span class="delivery-no">{{ delivery.delivery_no }}</span>
                <span class="approval-status" :class="delivery.approval_status">
                  {{ delivery.approval_status === 'pending' ? '待审批' : '已审批' }}
                </span>
                <span class="special-tag" v-if="delivery.special_approval_required">需特殊审批</span>
              </div>
              <div class="delivery-info">
                <span class="customer">{{ delivery.customer_name }}</span>
                <span class="amount">发货金额: ¥{{ formatMoney(delivery.delivery_amount) }}</span>
              </div>
            </div>

            <!-- 应收情况 -->
            <div class="receivable-panel" :class="{ warning: delivery.receivable_status.prepayment_gap > 0 }">
              <div class="receivable-row">
                <span>应收预付款:</span>
                <span>¥{{ formatMoney(delivery.receivable_status.prepayment_required) }}</span>
              </div>
              <div class="receivable-row">
                <span>已收预付款:</span>
                <span>¥{{ formatMoney(delivery.receivable_status.prepayment_received) }}</span>
              </div>
              <div class="receivable-row gap" v-if="delivery.receivable_status.prepayment_gap > 0">
                <span>预付款缺口:</span>
                <span class="warning-text">¥{{ formatMoney(delivery.receivable_status.prepayment_gap) }}</span>
              </div>
            </div>

            <div class="delivery-actions">
              <button class="btn-reject" @click="rejectDelivery(delivery)">驳回</button>
              <button class="btn-approve" @click="approveDelivery(delivery)">
                {{ delivery.special_approval_required ? '特殊审批通过' : '审批通过' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 回款跟踪 -->
      <div class="tab-content" v-if="activeTab === 'collection'">
        <div class="content-toolbar">
          <div class="filter-group">
            <select v-model="collectionFilter.type">
              <option value="">全部类型</option>
              <option value="prepayment">预付款</option>
              <option value="delivery">发货款</option>
              <option value="acceptance">验收款</option>
              <option value="warranty">质保款</option>
            </select>
            <select v-model="collectionFilter.status">
              <option value="">全部状态</option>
              <option value="due_soon">即将到期</option>
              <option value="overdue">已逾期</option>
            </select>
          </div>
        </div>

        <div class="collection-list">
          <div class="collection-item" v-for="plan in paymentPlans" :key="plan.id" :class="{ overdue: plan.is_overdue }">
            <div class="collection-main">
              <div class="collection-header">
                <span class="contract-no">{{ plan.contract_no }}</span>
                <span class="payment-type">{{ plan.payment_name }}</span>
                <span class="payment-status" :class="plan.payment_status">
                  {{ plan.is_overdue ? `逾期${plan.overdue_days}天` : `${plan.days_until_due}天后到期` }}
                </span>
              </div>
              <div class="collection-info">
                <span class="customer">{{ plan.customer_name }}</span>
                <span class="amount">¥{{ formatMoney(plan.remaining_amount) }}</span>
              </div>
              <div class="collection-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: (plan.received_amount / plan.plan_amount * 100) + '%' }"></div>
                </div>
                <span class="progress-text">
                  已收 ¥{{ formatMoney(plan.received_amount) }} / ¥{{ formatMoney(plan.plan_amount) }}
                </span>
              </div>
              <div class="collection-meta">
                <span>计划日期: {{ plan.plan_date }}</span>
                <span v-if="plan.invoiced">已开票 {{ plan.invoice_no }}</span>
                <span v-else class="warning-text">未开票</span>
                <span>催款{{ plan.reminder_count }}次</span>
              </div>
            </div>

            <div class="collection-actions">
              <button class="btn-action" @click="recordReminder(plan)">记录催款</button>
              <button class="btn-action" v-if="!plan.invoiced" @click="requestInvoice(plan)">申请开票</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 验收管理 -->
      <div class="tab-content" v-if="activeTab === 'acceptance'">
        <div class="acceptance-list">
          <div class="acceptance-item" v-for="acc in acceptances" :key="acc.id">
            <div class="acceptance-main">
              <div class="acceptance-header">
                <span class="contract-no">{{ acc.contract_no }}</span>
                <span class="acceptance-status" :class="acc.status">{{ acc.status_label }}</span>
              </div>
              <div class="acceptance-info">
                <span class="customer">{{ acc.customer_name }}</span>
                <span class="project">{{ acc.project_name }}</span>
              </div>
              <div class="acceptance-progress">
                <div class="condition-list">
                  <span class="condition" v-for="(cond, idx) in acc.conditions" :key="idx" :class="{ met: cond.met }">
                    {{ cond.met ? '✅' : '⏳' }} {{ cond.name }}
                  </span>
                </div>
              </div>
              <div class="acceptance-meta">
                <span v-if="acc.submit_date">提交日期: {{ acc.submit_date }}</span>
                <span v-if="acc.tracking_days">跟踪{{ acc.tracking_days }}天</span>
              </div>
            </div>

            <div class="warranty-info" v-if="acc.warranty_end_date">
              <span class="warranty-label">质保期:</span>
              <span class="warranty-date" :class="{ expiring: acc.warranty_expiring }">
                {{ acc.warranty_end_date }} {{ acc.warranty_expiring ? '(即将到期)' : '' }}
              </span>
            </div>

            <div class="acceptance-actions">
              <button class="btn-action" v-if="acc.status === 'submitted'" @click="remindAcceptance(acc)">
                催签验收单
              </button>
              <button class="btn-action" v-if="acc.status === 'signed'" @click="confirmReceived(acc)">
                确认收到原件
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 合同详情弹窗 -->
    <div class="modal-overlay" v-if="showContractModal" @click.self="showContractModal = false">
      <div class="modal-content contract-detail-modal">
        <div class="modal-header">
          <h3>合同详情</h3>
          <button class="close-btn" @click="showContractModal = false">×</button>
        </div>
        <div class="modal-body">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="info-grid">
              <div class="info-item"><span>合同编号</span><span>{{ currentContract?.contract_no }}</span></div>
              <div class="info-item"><span>客户名称</span><span>{{ currentContract?.customer_name }}</span></div>
              <div class="info-item"><span>合同金额</span><span>¥{{ formatMoney(currentContract?.contract_amount) }}</span></div>
              <div class="info-item"><span>业务员</span><span>{{ currentContract?.sales_person_name }}</span></div>
            </div>
          </div>

          <!-- 付款条款审核 -->
          <div class="detail-section">
            <h4>付款条款 <span class="section-badge">商务审核重点</span></h4>
            <div class="payment-terms">
              <div class="term-item" v-for="(term, key) in currentContract?.payment_terms" :key="key">
                <span class="term-name">{{ term.name || key }}</span>
                <span class="term-ratio">{{ term.ratio }}%</span>
                <span class="term-amount">¥{{ formatMoney(term.amount) }}</span>
                <span class="term-condition">{{ term.condition }}</span>
              </div>
            </div>
          </div>

          <!-- 风险检查 -->
          <div class="detail-section" v-if="currentContract?.business_review?.checklist">
            <h4>商务审核检查项</h4>
            <div class="checklist">
              <div class="check-item" v-for="item in currentContract.business_review.checklist" :key="item.item" :class="{ passed: item.passed, failed: !item.passed }">
                <span class="check-icon">{{ item.passed ? '✅' : '❌' }}</span>
                <span class="check-name">{{ item.item }}</span>
                <span class="check-standard">标准: {{ item.standard }}</span>
                <span class="check-actual">实际: {{ item.actual }}</span>
              </div>
            </div>
          </div>

          <!-- 风险项 -->
          <div class="detail-section risk-section" v-if="currentContract?.business_review?.risk_items?.length">
            <h4>风险提示</h4>
            <div class="risk-list">
              <div class="risk-item" v-for="(risk, idx) in currentContract.business_review.risk_items" :key="idx" :class="risk.level">
                <span class="risk-level-badge">{{ risk.level === 'high' ? '高' : '中' }}</span>
                <div class="risk-content">
                  <p class="risk-desc">{{ risk.description }}</p>
                  <p class="risk-suggestion">建议: {{ risk.suggestion }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showContractModal = false">关闭</button>
          <button class="btn-reject" v-if="currentContract?.business_review_status === 'pending'" @click="submitReview('rejected')">
            驳回
          </button>
          <button class="btn-primary" v-if="currentContract?.business_review_status === 'pending'" @click="submitReview('passed')">
            审核通过
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

// 搜索
const searchKeyword = ref('')

// 标签页
const activeTab = ref('contracts')

// 待办事项
const todos = ref([
  { id: 1, type: 'contract_review', type_label: '合同待审核', priority: 'urgent', title: 'XX汽车采购合同待商务审核', description: '新客户无预付款，需重点审核', customer_name: 'XX汽车股份有限公司', amount: 850000 },
  { id: 2, type: 'delivery_approval', type_label: '出货待审批', priority: 'urgent', title: 'YY新能源发货申请待审批', description: '预付款未收，需特殊审批', customer_name: 'YY新能源科技有限公司', amount: 500000 },
  { id: 3, type: 'payment_reminder', type_label: '回款提醒', priority: 'important', title: 'ZZ公司验收款即将到期', description: '验收款340,000元将于3天后到期', customer_name: 'ZZ精密制造有限公司', due_date: '2025-01-06' }
])

const urgentTodos = computed(() => todos.value.filter(t => t.priority === 'urgent'))
const importantTodos = computed(() => todos.value.filter(t => t.priority === 'important'))

// 指标
const metrics = reactive({
  contract: { newCount: 8, newAmount: 5800000, pendingReview: 3, pendingSeal: 2 },
  invoice: { monthAmount: 3200000, pending: 5, pendingAmount: 1500000 },
  collection: { monthAmount: 4500000, collectionRate: 85, overdue: 5, overdueAmount: 350000 },
  acceptance: { pending: 6, tracking: 4, warrantyExpiring: 3 }
})

// 合同筛选
const contractFilter = reactive({ status: '', riskLevel: '' })

// 合同列表
const contracts = ref([
  {
    id: 1,
    contract_no: 'HT-2025-0001',
    contract_name: 'XX汽车传感器自动测试设备采购合同',
    customer_name: 'XX汽车股份有限公司',
    contract_amount: 850000,
    contract_status: 'reviewing',
    contract_status_label: '审核中',
    seal_status: 'pending',
    seal_status_label: '待盖章',
    business_review_status: 'pending',
    risk_level: 'medium',
    risk_items: [
      { type: 'payment', desc: '新客户无预付款' },
      { type: 'penalty', desc: '违约金比例偏高(0.1%/天)' }
    ],
    payment_summary: '0%预付+50%发货+40%验收+10%质保'
  }
])

// 出货审批
const deliveryApprovals = ref([
  {
    id: 1,
    delivery_no: 'DO-2025-0005',
    customer_name: 'YY新能源科技有限公司',
    delivery_amount: 500000,
    approval_status: 'pending',
    special_approval_required: true,
    receivable_status: {
      prepayment_required: 450000,
      prepayment_received: 0,
      prepayment_gap: 450000
    }
  }
])

// 回款筛选
const collectionFilter = reactive({ type: '', status: '' })

// 回款计划
const paymentPlans = ref([
  {
    id: 1,
    contract_no: 'HT-2024-0088',
    customer_name: 'ZZ精密制造有限公司',
    payment_name: '验收款',
    plan_amount: 340000,
    received_amount: 0,
    remaining_amount: 340000,
    plan_date: '2025-01-06',
    invoiced: true,
    invoice_no: 'FP-2024-1215',
    reminder_count: 2,
    payment_status: 'pending',
    days_until_due: 3,
    is_overdue: false
  },
  {
    id: 2,
    contract_no: 'HT-2024-0076',
    customer_name: 'CC智能装备有限公司',
    payment_name: '质保款',
    plan_amount: 120000,
    received_amount: 0,
    remaining_amount: 120000,
    plan_date: '2024-12-20',
    invoiced: false,
    reminder_count: 3,
    payment_status: 'overdue',
    overdue_days: 14,
    is_overdue: true
  }
])

// 验收列表
const acceptances = ref([
  {
    id: 1,
    contract_no: 'HT-2024-0095',
    customer_name: 'AA电子科技有限公司',
    project_name: 'AA传感器测试设备',
    status: 'submitted',
    status_label: '已提交',
    submit_date: '2024-12-20',
    tracking_days: 14,
    conditions: [
      { name: '设备调试完成', met: true },
      { name: '测试报告提交', met: true },
      { name: '操作培训完成', met: true }
    ],
    warranty_end_date: '2026-01-15',
    warranty_expiring: false
  }
])

// 弹窗
const showAllTodos = ref(false)
const showContractModal = ref(false)
const currentContract = ref(null)

// 方法
const formatMoney = (val) => {
  if (!val) return '0'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const handleTodo = (todo) => {
  console.log('处理待办:', todo)
}

const showContractDetail = (contract) => {
  currentContract.value = {
    ...contract,
    payment_terms: {
      prepayment: { name: '预付款', ratio: 0, amount: 0, condition: '合同签订后' },
      delivery: { name: '发货款', ratio: 50, amount: 425000, condition: '发货前' },
      acceptance: { name: '验收款', ratio: 40, amount: 340000, condition: '验收后30天内' },
      warranty: { name: '质保款', ratio: 10, amount: 85000, condition: '质保期满后' }
    },
    business_review: {
      checklist: [
        { item: '预付款比例', standard: '新客户≥30%', actual: '0%', passed: false },
        { item: '账期', standard: '≤90天', actual: '30天', passed: true },
        { item: '违约金比例', standard: '≤0.05%/天', actual: '0.1%/天', passed: false },
        { item: '验收期限', standard: '需约定', actual: '未约定', passed: false }
      ],
      risk_items: [
        { level: 'high', description: '新客户无预付款，资金风险较高', suggestion: '建议要求至少20%预付款' },
        { level: 'medium', description: '我方违约金比例0.1%/天高于行业标准', suggestion: '建议协商降至0.05%/天' }
      ]
    }
  }
  showContractModal.value = true
}

const reviewContract = (contract) => {
  showContractDetail(contract)
}

const requestSeal = (contract) => {
  alert(`申请盖章: ${contract.contract_no}`)
}

const requestMail = (contract) => {
  alert(`申请邮寄: ${contract.contract_no}`)
}

const submitReview = (result) => {
  alert(`审核结果: ${result}`)
  showContractModal.value = false
}

const approveDelivery = (delivery) => {
  alert(`审批通过: ${delivery.delivery_no}`)
}

const rejectDelivery = (delivery) => {
  alert(`驳回: ${delivery.delivery_no}`)
}

const recordReminder = (plan) => {
  alert(`记录催款: ${plan.contract_no}`)
}

const requestInvoice = (plan) => {
  alert(`申请开票: ${plan.contract_no}`)
}

const remindAcceptance = (acc) => {
  alert(`催签验收单: ${acc.contract_no}`)
}

const confirmReceived = (acc) => {
  alert(`确认收到原件: ${acc.contract_no}`)
}
</script>

<style scoped>
.business-support-page {
  min-height: 100vh;
  background: #0f172a;
  color: white;
  padding: 24px 32px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h1 { font-size: 28px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.quick-search { position: relative; }
.quick-search input {
  padding: 10px 16px 10px 40px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  color: white;
  width: 300px;
}
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); }

/* 待办事项 */
.todo-section { margin-bottom: 24px; }
.todo-section h2 { font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.todo-count { background: #EF4444; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
.todo-cards { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 8px; }
.todo-card {
  min-width: 280px;
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.1);
}
.todo-card.urgent { border-left: 3px solid #EF4444; }
.todo-card.important { border-left: 3px solid #F59E0B; }
.todo-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.todo-type { font-size: 12px; color: #94A3B8; }
.todo-priority { font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.todo-card.urgent .todo-priority { background: rgba(239,68,68,0.2); color: #F87171; }
.todo-card.important .todo-priority { background: rgba(245,158,11,0.2); color: #F59E0B; }
.todo-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
.todo-desc { font-size: 13px; color: #94A3B8; margin-bottom: 12px; }
.todo-meta { display: flex; justify-content: space-between; font-size: 12px; color: #64748B; }
.view-all-btn { padding: 8px 16px; background: rgba(255,255,255,0.05); border: none; border-radius: 8px; color: #94A3B8; cursor: pointer; margin-top: 12px; }

/* 指标卡片 */
.metrics-section { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.metric-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 16px;
}
.metric-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.metric-icon { font-size: 20px; }
.metric-title { font-size: 14px; color: #94A3B8; }
.metric-body { margin-bottom: 12px; }
.metric-main { display: flex; align-items: baseline; gap: 4px; }
.metric-value { font-size: 28px; font-weight: 700; }
.metric-unit { font-size: 14px; color: #94A3B8; }
.metric-sub { font-size: 13px; color: #64748B; margin-top: 4px; }
.metric-footer { font-size: 12px; color: #64748B; display: flex; gap: 16px; }
.metric-footer.warning { color: #F59E0B; }
.metric-footer .pending { color: #6366F1; }

/* 主要功能区 */
.main-section { background: rgba(255,255,255,0.02); border-radius: 16px; padding: 20px; }
.tab-header { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; }
.tab-header button {
  padding: 10px 20px;
  background: transparent;
  border: none;
  color: #94A3B8;
  cursor: pointer;
  border-radius: 8px;
  font-size: 14px;
}
.tab-header button.active { background: rgba(99,102,241,0.2); color: white; }

.content-toolbar { display: flex; justify-content: space-between; margin-bottom: 16px; }
.filter-group { display: flex; gap: 12px; }
.filter-group select {
  padding: 8px 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  color: white;
}

/* 合同列表 */
.contract-list { display: flex; flex-direction: column; gap: 12px; }
.contract-item {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.contract-item:hover { border-color: rgba(99,102,241,0.5); }
.contract-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.contract-no { font-size: 13px; color: #94A3B8; }
.contract-status, .seal-status { font-size: 11px; padding: 3px 8px; border-radius: 4px; }
.contract-status.reviewing { background: rgba(245,158,11,0.2); color: #F59E0B; }
.contract-status.executing { background: rgba(16,185,129,0.2); color: #10B981; }
.seal-status.pending { background: rgba(100,116,139,0.2); color: #94A3B8; }
.seal-status.archived { background: rgba(16,185,129,0.2); color: #10B981; }
.contract-name { font-size: 15px; margin-bottom: 8px; }
.contract-info { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
.contract-info .customer { color: #94A3B8; }
.contract-info .amount { color: #6366F1; font-weight: 600; }
.payment-summary { font-size: 13px; color: #64748B; }
.payment-summary .label { margin-right: 8px; }

.risk-panel { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.05); }
.risk-level { font-size: 11px; padding: 3px 8px; border-radius: 4px; margin-right: 12px; }
.risk-level.high { background: rgba(239,68,68,0.2); color: #F87171; }
.risk-level.medium { background: rgba(245,158,11,0.2); color: #F59E0B; }
.risk-items { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.risk-item { font-size: 12px; color: #F59E0B; }

.contract-actions { display: flex; gap: 8px; margin-top: 12px; }
.btn-action { padding: 8px 16px; background: rgba(99,102,241,0.2); border: none; border-radius: 6px; color: #A5B4FC; cursor: pointer; font-size: 13px; }

/* 出货审批 */
.delivery-list { display: flex; flex-direction: column; gap: 12px; }
.delivery-item { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; }
.delivery-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.delivery-no { font-size: 14px; font-weight: 500; }
.approval-status { font-size: 11px; padding: 3px 8px; border-radius: 4px; }
.approval-status.pending { background: rgba(245,158,11,0.2); color: #F59E0B; }
.special-tag { font-size: 11px; padding: 3px 8px; background: rgba(239,68,68,0.2); color: #F87171; border-radius: 4px; }
.delivery-info { display: flex; justify-content: space-between; font-size: 14px; }
.receivable-panel { margin-top: 12px; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; }
.receivable-panel.warning { border: 1px solid rgba(245,158,11,0.3); }
.receivable-row { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.receivable-row.gap { font-weight: 600; }
.warning-text { color: #F59E0B; }
.delivery-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 16px; }
.btn-reject { padding: 10px 20px; background: rgba(239,68,68,0.2); border: none; border-radius: 8px; color: #F87171; cursor: pointer; }
.btn-approve { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 8px; color: white; cursor: pointer; }

/* 回款跟踪 */
.collection-list { display: flex; flex-direction: column; gap: 12px; }
.collection-item { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; }
.collection-item.overdue { border-color: rgba(239,68,68,0.3); }
.collection-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.payment-type { font-size: 12px; color: #6366F1; background: rgba(99,102,241,0.2); padding: 2px 8px; border-radius: 4px; }
.payment-status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.payment-status.pending { background: rgba(245,158,11,0.2); color: #F59E0B; }
.payment-status.overdue { background: rgba(239,68,68,0.2); color: #F87171; }
.collection-info { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 14px; }
.collection-progress { margin-bottom: 8px; }
.collection-progress .progress-bar { height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; margin-bottom: 4px; }
.collection-progress .progress-fill { height: 100%; background: #10B981; }
.collection-progress .progress-text { font-size: 12px; color: #64748B; }
.collection-meta { display: flex; gap: 16px; font-size: 12px; color: #64748B; }
.collection-actions { display: flex; gap: 8px; margin-top: 12px; }

/* 验收列表 */
.acceptance-list { display: flex; flex-direction: column; gap: 12px; }
.acceptance-item { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; }
.acceptance-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.acceptance-status { font-size: 11px; padding: 3px 8px; border-radius: 4px; }
.acceptance-status.submitted { background: rgba(245,158,11,0.2); color: #F59E0B; }
.acceptance-info { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 14px; }
.acceptance-info .customer { color: #94A3B8; }
.condition-list { display: flex; flex-wrap: wrap; gap: 8px; }
.condition { font-size: 12px; padding: 4px 10px; background: rgba(255,255,255,0.02); border-radius: 4px; }
.condition.met { color: #10B981; }
.acceptance-meta { display: flex; gap: 16px; font-size: 12px; color: #64748B; margin-top: 8px; }
.warranty-info { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
.warranty-label { color: #64748B; margin-right: 8px; }
.warranty-date.expiring { color: #F59E0B; }
.acceptance-actions { display: flex; gap: 8px; margin-top: 12px; }

/* 弹窗 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.contract-detail-modal { width: 700px; max-height: 85vh; background: #1E293B; border-radius: 16px; overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.modal-header h3 { font-size: 18px; }
.close-btn { width: 32px; height: 32px; border: none; background: rgba(255,255,255,0.1); border-radius: 8px; color: #94A3B8; cursor: pointer; }
.modal-body { padding: 24px; max-height: 60vh; overflow-y: auto; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.1); }
.btn-secondary { padding: 10px 20px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; cursor: pointer; }
.btn-primary { padding: 10px 20px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 8px; color: white; cursor: pointer; }

.detail-section { margin-bottom: 24px; }
.detail-section h4 { font-size: 14px; color: #94A3B8; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.section-badge { font-size: 11px; padding: 2px 8px; background: rgba(245,158,11,0.2); color: #F59E0B; border-radius: 4px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
.info-item span:first-child { color: #64748B; }

.payment-terms { display: flex; flex-direction: column; gap: 8px; }
.term-item { display: flex; gap: 16px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; font-size: 13px; }
.term-name { width: 80px; color: #94A3B8; }
.term-ratio { width: 50px; color: #6366F1; }
.term-amount { width: 100px; }
.term-condition { flex: 1; color: #64748B; }

.checklist { display: flex; flex-direction: column; gap: 8px; }
.check-item { display: flex; align-items: center; gap: 12px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; font-size: 13px; }
.check-item.failed { border: 1px solid rgba(239,68,68,0.3); }
.check-icon { font-size: 16px; }
.check-name { width: 100px; }
.check-standard { flex: 1; color: #64748B; }
.check-actual { width: 100px; }
.check-item.failed .check-actual { color: #F87171; }

.risk-section .risk-list { display: flex; flex-direction: column; gap: 12px; }
.risk-section .risk-item { display: flex; gap: 12px; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; }
.risk-section .risk-item.high { border-left: 3px solid #EF4444; }
.risk-section .risk-item.medium { border-left: 3px solid #F59E0B; }
.risk-level-badge { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-size: 12px; font-weight: 600; }
.risk-item.high .risk-level-badge { background: rgba(239,68,68,0.2); color: #F87171; }
.risk-item.medium .risk-level-badge { background: rgba(245,158,11,0.2); color: #F59E0B; }
.risk-content { flex: 1; }
.risk-desc { font-size: 14px; margin-bottom: 4px; }
.risk-suggestion { font-size: 13px; color: #10B981; }
</style>
