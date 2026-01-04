/**
 * Supplier Management Page - Complete supplier lifecycle management
 * Supplier evaluation, performance tracking, and relationship management
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Building2,
  Phone,
  Mail,
  MapPin,
  Star,
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  Plus,
  Eye,
  Edit,
  Award,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
  Users,
  FileText,
  Zap,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock supplier data
const mockSuppliers = [
  {
    id: 'SUPP-001',
    name: '深圳电子元器件有限公司',
    category: '电子元器件',
    level: 'A级', // A级 | B级 | C级 | D级
    status: 'active', // active | inactive | review
    contactPerson: '张三',
    phone: '13800000001',
    email: 'contact@supplier1.com',
    address: '深圳市龙华区',
    website: 'www.supplier1.com',
    yearOfEstablishment: 2010,
    employeeCount: 150,
    mainProducts: ['半导体芯片', '电子元器件', '模块'],
    certifications: ['ISO9001', 'ISO14001', '质量体系认证'],
    paymentTerm: '2/10 N30',
    leadTime: '5-7天',
    minimumOrderQuantity: '100个',
    discountPolicy: '数量折扣可协议',
    totalOrders: 25,
    completedOrders: 23,
    failureRate: 2,
    onTimeDeliveryRate: 96,
    qualityPassRate: 98.5,
    overallRating: 4.8,
    ratingDetails: {
      quality: 4.9,
      delivery: 4.7,
      service: 4.8,
      price: 4.7,
    },
    recentOrders: [
      { poNo: 'PO-2025-0001', date: '2025-11-15', amount: 22750, status: 'delivered' },
      { poNo: 'PO-2025-0005', date: '2025-11-10', amount: 5680, status: 'delivered' },
      { poNo: 'PO-2025-0009', date: '2025-11-05', amount: 3450, status: 'delivered' },
    ],
    issues: [],
    riskLevel: 'low', // low | medium | high
    annualSpend: 185000,
    yearToDateSpend: 156000,
    growthRate: 12,
  },
  {
    id: 'SUPP-002',
    name: '日本太阳诱电代理商',
    category: '被动元件',
    level: 'A级',
    status: 'active',
    contactPerson: '李四',
    phone: '0755-12345678',
    email: 'contact@supplier2.com',
    address: '深圳市福田区',
    website: 'www.supplier2.com',
    yearOfEstablishment: 2005,
    employeeCount: 200,
    mainProducts: ['电容', '电感', '贴片元件'],
    certifications: ['ISO9001', 'ISO13485', 'RoHS认证'],
    paymentTerm: '30天信用期',
    leadTime: '3-5天',
    minimumOrderQuantity: '50个',
    discountPolicy: '年度返利',
    totalOrders: 18,
    completedOrders: 18,
    failureRate: 0,
    onTimeDeliveryRate: 100,
    qualityPassRate: 99.8,
    overallRating: 4.9,
    ratingDetails: {
      quality: 5.0,
      delivery: 5.0,
      service: 4.8,
      price: 4.8,
    },
    recentOrders: [
      { poNo: 'PO-2025-0002', date: '2025-11-16', amount: 850, status: 'delivered' },
      { poNo: 'PO-2025-0008', date: '2025-11-08', amount: 600, status: 'delivered' },
    ],
    issues: [],
    riskLevel: 'low',
    annualSpend: 95000,
    yearToDateSpend: 85000,
    growthRate: 8,
  },
  {
    id: 'SUPP-003',
    name: '深圳电源厂商',
    category: '电源模块',
    level: 'A级',
    status: 'active',
    contactPerson: '王五',
    phone: '13900000001',
    email: 'sales@supplier3.com',
    address: '深圳市南山区',
    website: 'www.supplier3.com',
    yearOfEstablishment: 2012,
    employeeCount: 100,
    mainProducts: ['AC/DC电源', 'DC/DC模块', '高效率电源'],
    certifications: ['ISO9001', 'CCC认证', 'CE认证'],
    paymentTerm: '预付50% 交货50%',
    leadTime: '7-10天',
    minimumOrderQuantity: '1套',
    discountPolicy: '大订单可议',
    totalOrders: 12,
    completedOrders: 10,
    failureRate: 2,
    onTimeDeliveryRate: 90,
    qualityPassRate: 97.0,
    overallRating: 4.5,
    ratingDetails: {
      quality: 4.6,
      delivery: 4.3,
      service: 4.6,
      price: 4.4,
    },
    recentOrders: [
      { poNo: 'PO-2025-0003', date: '2025-11-18', amount: 14000, status: 'pending' },
      { poNo: 'PO-2025-0010', date: '2025-10-25', amount: 8500, status: 'delivered' },
    ],
    issues: [{ date: '2025-11-18', issue: '交期延迟3天', severity: 'medium' }],
    riskLevel: 'medium',
    annualSpend: 125000,
    yearToDateSpend: 105000,
    growthRate: 5,
  },
  {
    id: 'SUPP-004',
    name: '连接器制造商',
    category: '连接器',
    level: 'B级',
    status: 'review',
    contactPerson: '赵六',
    phone: '0755-98765432',
    email: 'contact@supplier4.com',
    address: '深圳市龙岗区',
    website: 'www.supplier4.com',
    yearOfEstablishment: 2015,
    employeeCount: 80,
    mainProducts: ['USB连接器', '电源连接器', '信号连接器'],
    certifications: ['ISO9001'],
    paymentTerm: '30天付款',
    leadTime: '5-8天',
    minimumOrderQuantity: '50个',
    discountPolicy: '数量折扣',
    totalOrders: 8,
    completedOrders: 6,
    failureRate: 4,
    onTimeDeliveryRate: 85,
    qualityPassRate: 95.0,
    overallRating: 4.2,
    ratingDetails: {
      quality: 4.1,
      delivery: 4.0,
      service: 4.3,
      price: 4.3,
    },
    recentOrders: [
      { poNo: 'PO-2025-0001', date: '2025-11-15', amount: 320, status: 'delivered' },
    ],
    issues: [
      { date: '2025-10-15', issue: '质量问题，部分退货', severity: 'high' },
      { date: '2025-09-20', issue: '交期延迟', severity: 'medium' },
    ],
    riskLevel: 'medium',
    annualSpend: 45000,
    yearToDateSpend: 32000,
    growthRate: -5,
  },
]

const levelConfig = {
  'A级': { label: 'A级', color: 'bg-emerald-500/20 text-emerald-400', description: '优秀供应商' },
  'B级': { label: 'B级', color: 'bg-amber-500/20 text-amber-400', description: '合格供应商' },
  'C级': { label: 'C级', color: 'bg-orange-500/20 text-orange-400', description: '待改进' },
  'D级': { label: 'D级', color: 'bg-red-500/20 text-red-400', description: '需淘汰' },
}

const statusConfig = {
  'active': { label: '活跃', color: 'bg-blue-500/20 text-blue-400' },
  'inactive': { label: '停用', color: 'bg-slate-500/20 text-slate-400' },
  'review': { label: '评审中', color: 'bg-amber-500/20 text-amber-400' },
}

const SupplierCard = ({ supplier, onView }) => {
  const levelCfg = levelConfig[supplier.level]
  const statusCfg = statusConfig[supplier.status]

  return (
    <motion.div variants={fadeIn} className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden hover:bg-slate-800/70 transition-all">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-semibold text-slate-100 text-lg">{supplier.name}</h3>
            <p className="text-sm text-slate-400 mt-1">{supplier.category}</p>
          </div>
          <div className="flex flex-col gap-1">
            <Badge className={cn('text-xs', levelCfg.color)}>
              <Award className="w-3 h-3 mr-1" />
              {levelCfg.label}
            </Badge>
            <Badge className={cn('text-xs', statusCfg.color)}>
              {statusCfg.label}
            </Badge>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Contact Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2 text-slate-300">
            <Users className="w-4 h-4 text-slate-500" />
            <span>{supplier.contactPerson}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Phone className="w-4 h-4 text-slate-500" />
            <span>{supplier.phone}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Mail className="w-4 h-4 text-slate-500" />
            <span className="truncate">{supplier.email}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <MapPin className="w-4 h-4 text-slate-500" />
            <span>{supplier.address}</span>
          </div>
        </div>

        {/* Rating Section */}
        <div className="border-t border-slate-700/50 pt-4">
          <div className="flex items-center justify-between mb-3">
            <p className="font-medium text-slate-100">综合评分</p>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <Star
                  key={i}
                  className={cn('w-4 h-4', i < Math.floor(supplier.overallRating) ? 'fill-amber-400 text-amber-400' : 'text-slate-600')}
                />
              ))}
              <span className="ml-2 text-sm font-semibold text-amber-400">{supplier.overallRating.toFixed(1)}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div>
              <p className="text-slate-500 mb-1">质量</p>
              <div className="flex items-center gap-1">
                <Progress value={supplier.ratingDetails.quality * 20} className="flex-1 h-1.5" />
                <span className="font-medium text-slate-300 w-8">{supplier.ratingDetails.quality}</span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">交期</p>
              <div className="flex items-center gap-1">
                <Progress value={supplier.ratingDetails.delivery * 20} className="flex-1 h-1.5" />
                <span className="font-medium text-slate-300 w-8">{supplier.ratingDetails.delivery}</span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">服务</p>
              <div className="flex items-center gap-1">
                <Progress value={supplier.ratingDetails.service * 20} className="flex-1 h-1.5" />
                <span className="font-medium text-slate-300 w-8">{supplier.ratingDetails.service}</span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">价格</p>
              <div className="flex items-center gap-1">
                <Progress value={supplier.ratingDetails.price * 20} className="flex-1 h-1.5" />
                <span className="font-medium text-slate-300 w-8">{supplier.ratingDetails.price}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm border-t border-slate-700/50 pt-4">
          <div>
            <p className="text-slate-500 text-xs mb-1">交期准时率</p>
            <p className="font-semibold text-slate-100 flex items-center gap-1">
              {supplier.onTimeDeliveryRate}%
              {supplier.onTimeDeliveryRate >= 95 ? (
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
            </p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">质量合格率</p>
            <p className="font-semibold text-slate-100">{supplier.qualityPassRate}%</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">总订单</p>
            <p className="font-semibold text-slate-100">{supplier.completedOrders}/{supplier.totalOrders}</p>
          </div>
        </div>

        {/* Financial Info */}
        <div className="grid grid-cols-2 gap-3 text-sm border-t border-slate-700/50 pt-4">
          <div>
            <p className="text-slate-500 text-xs mb-1">年度采购额</p>
            <p className="font-semibold text-amber-400">{formatCurrency(supplier.annualSpend)}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">年增长率</p>
            <p className={cn('font-semibold', supplier.growthRate > 0 ? 'text-emerald-400' : 'text-red-400')}>
              {supplier.growthRate > 0 ? '+' : ''}{supplier.growthRate}%
            </p>
          </div>
        </div>

        {/* Issues or Risk Alert */}
        {(supplier.issues.length > 0 || supplier.riskLevel !== 'low') && (
          <div className={cn('rounded-lg p-3 border text-sm',
            supplier.riskLevel === 'high' ? 'bg-red-500/10 border-red-500/30' : 'bg-amber-500/10 border-amber-500/30'
          )}>
            {supplier.issues.length > 0 && (
              <div>
                <p className={cn('text-xs font-medium mb-2', supplier.riskLevel === 'high' ? 'text-red-400' : 'text-amber-400')}>
                  <AlertTriangle className="w-3 h-3 mr-1 inline" />
                  最近问题
                </p>
                <ul className="space-y-1 text-xs text-slate-300">
                  {supplier.issues.slice(0, 2).map((issue, idx) => (
                    <li key={idx} className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                      {issue.issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Action Bar */}
        <div className="flex gap-2 pt-2 border-t border-slate-700/50">
          <Button
            size="sm"
            className="flex-1"
            onClick={() => onView(supplier)}
          >
            <Eye className="w-4 h-4 mr-1" />
            查看详情
          </Button>
          <Button
            size="sm"
            variant="outline"
          >
            <Edit className="w-4 h-4 mr-1" />
            编辑
          </Button>
        </div>
      </div>
    </motion.div>
  )
}

export default function SupplierManagement() {
  const [suppliers] = useState(mockSuppliers)
  const [searchText, setSearchText] = useState('')
  const [filterLevel, setFilterLevel] = useState('all')

  const filteredSuppliers = useMemo(() => {
    return suppliers.filter(s => {
      const matchSearch =
        s.name.toLowerCase().includes(searchText.toLowerCase()) ||
        s.category.toLowerCase().includes(searchText.toLowerCase()) ||
        s.contactPerson.toLowerCase().includes(searchText.toLowerCase())

      const matchLevel = filterLevel === 'all' || s.level === filterLevel

      return matchSearch && matchLevel
    })
  }, [suppliers, searchText, filterLevel])

  const stats = useMemo(() => {
    return {
      total: suppliers.length,
      aGrade: suppliers.filter(s => s.level === 'A级').length,
      bGrade: suppliers.filter(s => s.level === 'B级').length,
      active: suppliers.filter(s => s.status === 'active').length,
      avgRating: (suppliers.reduce((sum, s) => sum + s.overallRating, 0) / suppliers.length).toFixed(2),
    }
  }, [suppliers])

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="供应商管理"
        description="供应商评估、性能跟踪和关系管理"
        action={{
          label: '新增供应商',
          icon: Plus,
          onClick: () => console.log('New supplier'),
        }}
      />

      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5"
      >
        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">供应商总数</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">{stats.total}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">A级供应商</p>
              <p className="text-3xl font-bold text-emerald-400 mt-2">{stats.aGrade}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">B级供应商</p>
              <p className="text-3xl font-bold text-amber-400 mt-2">{stats.bGrade}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">活跃供应商</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">{stats.active}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">平均评分</p>
              <div className="flex items-center gap-1 mt-2">
                <p className="text-3xl font-bold text-amber-400">{stats.avgRating}</p>
                <Star className="w-6 h-6 fill-amber-400 text-amber-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder="搜索供应商名称、分类、联系人..."
                value={searchText}
                onChange={e => setSearchText(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterLevel === 'all' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilterLevel('all')}
              >
                全部等级
              </Button>
              {Object.entries(levelConfig).map(([key, cfg]) => (
                <Button
                  key={key}
                  variant={filterLevel === key ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setFilterLevel(key)}
                  className={cn(filterLevel === key && cfg.color)}
                >
                  {cfg.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Suppliers Grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        <AnimatePresence>
          {filteredSuppliers.length > 0 ? (
            filteredSuppliers.map(supplier => (
              <SupplierCard
                key={supplier.id}
                supplier={supplier}
                onView={s => console.log('View supplier', s)}
              />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="col-span-full py-12 text-center"
            >
              <Building2 className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">没有符合条件的供应商</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Supplier Risk Summary */}
      {suppliers.some(s => s.riskLevel !== 'low') && (
        <Card className="bg-amber-500/5 border-amber-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
              风险供应商预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {suppliers
                .filter(s => s.riskLevel === 'high')
                .map(s => (
                  <div key={s.id} className="flex items-start gap-3 p-3 rounded-lg bg-red-500/5 border border-red-500/20">
                    <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-100 text-sm">{s.name}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        {s.issues.length > 0 ? `${s.issues[0].issue}` : '存在多项问题需要关注'}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
