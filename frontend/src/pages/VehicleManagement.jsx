/**
 * Vehicle Management - Administrative vehicle management
 * Features: Vehicle list, usage tracking, maintenance records, fuel management
 */

import { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Search,
  Filter,
  Plus,
  Car,
  Fuel,
  Wrench,
  MapPin,
  Clock,
  User,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Edit,
  Eye,
  Calendar,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { SimpleBarChart, MonthlyTrendChart, SimplePieChart, TrendComparisonCard } from '../components/administrative/StatisticsCharts'
import { adminApi } from '../services/api'

// Mock data
const mockVehicles = [
  {
    id: 1,
    plateNumber: '粤B12345',
    brand: '丰田凯美瑞',
    model: '2020款',
    purchaseDate: '2020-06-15',
    mileage: 85600,
    status: 'in_use',
    driver: '张师傅',
    purpose: '客户现场服务',
    destination: '深圳XX科技',
    startTime: '2025-01-07 08:00',
    endTime: '2025-01-07 18:00',
  },
  {
    id: 2,
    plateNumber: '粤B67890',
    brand: '大众帕萨特',
    model: '2021款',
    purchaseDate: '2021-03-20',
    mileage: 65200,
    status: 'in_use',
    driver: '李师傅',
    purpose: '供应商拜访',
    destination: '东莞XX电子',
    startTime: '2025-01-07 09:00',
    endTime: '2025-01-07 17:00',
  },
  {
    id: 3,
    plateNumber: '粤B11111',
    brand: '本田雅阁',
    model: '2019款',
    purchaseDate: '2019-08-10',
    mileage: 125000,
    status: 'available',
    nextMaintenance: '2025-01-20',
    nextMaintenanceMileage: 130000,
  },
  {
    id: 4,
    plateNumber: '粤B22222',
    brand: '别克GL8',
    model: '2022款',
    purchaseDate: '2022-05-12',
    mileage: 45200,
    status: 'maintenance',
    maintenanceReason: '定期保养',
    returnDate: '2025-01-08',
  },
]

export default function VehicleManagement() {
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [vehicles, setVehicles] = useState(mockVehicles)

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await adminApi.vehicles.list()
        if (res.data?.items) {
          setVehicles(res.data.items)
        } else if (Array.isArray(res.data)) {
          setVehicles(res.data)
        }
      } catch (err) {
        console.log('Vehicle API unavailable, using mock data')
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  const filteredVehicles = useMemo(() => {
    return vehicles.filter(vehicle => {
      const matchSearch = vehicle.plateNumber.includes(searchText) ||
        vehicle.brand.includes(searchText) ||
        (vehicle.driver && vehicle.driver.includes(searchText))
      const matchStatus = statusFilter === 'all' || vehicle.status === statusFilter
      return matchSearch && matchStatus
    })
  }, [vehicles, searchText, statusFilter])

  const stats = useMemo(() => {
    const total = vehicles.length
    const inUse = vehicles.filter(v => v.status === 'in_use').length
    const available = vehicles.filter(v => v.status === 'available').length
    const maintenance = vehicles.filter(v => v.status === 'maintenance').length
    return { total, inUse, available, maintenance }
  }, [vehicles])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="车辆管理"
        description="车辆使用管理、维护记录、燃油管理"
        actions={
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            新增车辆
          </Button>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">车辆总数</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
              </div>
              <Car className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">使用中</p>
                <p className="text-2xl font-bold text-blue-400 mt-1">{stats.inUse}</p>
              </div>
              <MapPin className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">可用</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.available}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">保养中</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">{stats.maintenance}</p>
              </div>
              <Wrench className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="vehicles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="vehicles">车辆列表</TabsTrigger>
          <TabsTrigger value="usage">使用记录</TabsTrigger>
          <TabsTrigger value="maintenance">维护记录</TabsTrigger>
          <TabsTrigger value="fuel">燃油管理</TabsTrigger>
        </TabsList>

        <TabsContent value="vehicles" className="space-y-4">
          {/* Statistics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>车辆状态分布</CardTitle>
              </CardHeader>
              <CardContent>
                <SimplePieChart
                  data={[
                    { label: '使用中', value: stats.inUse, color: '#3b82f6' },
                    { label: '可用', value: stats.available, color: '#10b981' },
                    { label: '保养中', value: stats.maintenance, color: '#f59e0b' },
                  ]}
                  size={180}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>月度使用率趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <MonthlyTrendChart
                  data={[
                    { month: '2024-10', amount: 75 },
                    { month: '2024-11', amount: 68 },
                    { month: '2024-12', amount: 72 },
                    { month: '2025-01', amount: (stats.inUse / stats.total) * 100 },
                  ]}
                  valueKey="amount"
                  labelKey="month"
                  height={150}
                />
              </CardContent>
            </Card>
          </div>

          {/* Trend Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TrendComparisonCard
              title="车辆使用率"
              current={(stats.inUse / stats.total) * 100}
              previous={72}
              unit="%"
            />
            <TrendComparisonCard
              title="在用车辆数"
              current={stats.inUse}
              previous={9}
            />
            <TrendComparisonCard
              title="可用车辆数"
              current={stats.available}
              previous={3}
            />
          </div>

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-4">
                <Input
                  placeholder="搜索车牌号、品牌、驾驶员..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="flex-1"
                />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white"
                >
                  <option value="all">全部状态</option>
                  <option value="in_use">使用中</option>
                  <option value="available">可用</option>
                  <option value="maintenance">保养中</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Vehicles List */}
          <div className="grid grid-cols-1 gap-4">
            {filteredVehicles.map((vehicle) => (
              <Card key={vehicle.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">{vehicle.plateNumber}</h3>
                        <Badge
                          variant="outline"
                          className={cn(
                            vehicle.status === 'in_use' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                            vehicle.status === 'available' && 'bg-green-500/20 text-green-400 border-green-500/30',
                            vehicle.status === 'maintenance' && 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                          )}
                        >
                          {vehicle.status === 'in_use' ? '使用中' : 
                           vehicle.status === 'available' ? '可用' : '保养中'}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                        <div>
                          <p className="text-slate-400">品牌型号</p>
                          <p className="text-white font-medium">{vehicle.brand} {vehicle.model}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">里程数</p>
                          <p className="text-white font-medium">{vehicle.mileage.toLocaleString()} km</p>
                        </div>
                        <div>
                          <p className="text-slate-400">购置日期</p>
                          <p className="text-white font-medium">{vehicle.purchaseDate}</p>
                        </div>
                        {vehicle.driver && (
                          <div>
                            <p className="text-slate-400">驾驶员</p>
                            <p className="text-white font-medium">{vehicle.driver}</p>
                          </div>
                        )}
                      </div>
                      {vehicle.purpose && (
                        <div className="text-sm text-slate-400 mb-2">
                          用途: {vehicle.purpose} · 目的地: {vehicle.destination}
                        </div>
                      )}
                      {vehicle.startTime && (
                        <div className="text-xs text-slate-500">
                          使用时间: {vehicle.startTime} - {vehicle.endTime}
                        </div>
                      )}
                      {vehicle.nextMaintenance && (
                        <div className="text-xs text-amber-400 mt-2">
                          下次保养: {vehicle.nextMaintenance} (里程: {vehicle.nextMaintenanceMileage.toLocaleString()} km)
                        </div>
                      )}
                      {vehicle.maintenanceReason && (
                        <div className="text-xs text-amber-400 mt-2">
                          {vehicle.maintenanceReason} · 预计归还: {vehicle.returnDate}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>使用记录</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {vehicles
                  .filter(v => v.status === 'in_use')
                  .map((vehicle) => (
                    <div
                      key={vehicle.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="font-medium text-white">{vehicle.plateNumber}</span>
                            <Badge variant="outline" className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                              使用中
                            </Badge>
                          </div>
                          <div className="grid grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">驾驶员</p>
                              <p className="text-white font-medium">{vehicle.driver}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">使用目的</p>
                              <p className="text-white font-medium">{vehicle.purpose}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">目的地</p>
                              <p className="text-white font-medium">{vehicle.destination}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">使用时间</p>
                              <p className="text-white font-medium">{vehicle.startTime} - {vehicle.endTime}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="maintenance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>维护记录</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {vehicles
                  .filter(v => v.status === 'maintenance')
                  .map((vehicle) => (
                    <div
                      key={vehicle.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="font-medium text-white">{vehicle.plateNumber}</span>
                            <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                              保养中
                            </Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-slate-400">保养原因</p>
                              <p className="text-white font-medium">{vehicle.maintenanceReason}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">预计归还</p>
                              <p className="text-white font-medium">{vehicle.returnDate}</p>
                            </div>
                            <div>
                              <p className="text-slate-400">当前里程</p>
                              <p className="text-white font-medium">{vehicle.mileage?.toLocaleString()} km</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                {vehicles
                  .filter(v => v.nextMaintenance)
                  .map((vehicle) => (
                    <div
                      key={vehicle.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="font-medium text-white">{vehicle.plateNumber}</span>
                            <Badge variant="outline" className="bg-green-500/20 text-green-400 border-green-500/30">
                              待保养
                            </Badge>
                          </div>
                          <div className="text-sm text-slate-400">
                            下次保养: {vehicle.nextMaintenance} (里程: {vehicle.nextMaintenanceMileage?.toLocaleString()} km)
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fuel" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>燃油管理</CardTitle>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  添加记录
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { id: 1, plateNumber: '粤B12345', date: '2025-01-05', amount: 500, price: 7.8, total: 3900, mileage: 85000 },
                  { id: 2, plateNumber: '粤B67890', date: '2025-01-04', amount: 450, price: 7.8, total: 3510, mileage: 65000 },
                  { id: 3, plateNumber: '粤B11111', date: '2025-01-03', amount: 400, price: 7.8, total: 3120, mileage: 124500 },
                ].map((record) => (
                  <div
                    key={record.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-medium text-white">{record.plateNumber}</span>
                          <span className="text-sm text-slate-400">{record.date}</span>
                        </div>
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-slate-400">加油量</p>
                            <p className="text-white font-medium">{record.amount} 升</p>
                          </div>
                          <div>
                            <p className="text-slate-400">单价</p>
                            <p className="text-white font-medium">¥{record.price}/升</p>
                          </div>
                          <div>
                            <p className="text-slate-400">金额</p>
                            <p className="text-white font-medium">{formatCurrency(record.total)}</p>
                          </div>
                          <div>
                            <p className="text-slate-400">里程数</p>
                            <p className="text-white font-medium">{record.mileage.toLocaleString()} km</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}

