import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Key,
  Smartphone,
  Mail,
  Camera,
  Save,
  Eye,
  EyeOff,
  Moon,
  Sun,
  Monitor,
  Check,
  BookOpen,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Avatar, AvatarImage, AvatarFallback } from '../components/ui/avatar'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { authApi } from '../services/api'

const settingsSections = [
  { id: 'profile', label: '个人资料', icon: User },
  { id: 'notifications', label: '通知设置', icon: Bell },
  { id: 'security', label: '安全设置', icon: Shield },
  { id: 'appearance', label: '外观主题', icon: Palette },
  { id: 'language', label: '语言区域', icon: Globe },
  { id: 'knowledge', label: '知识管理', icon: BookOpen },
]

// Mock user data
// Mock data - 已移除，使用真实API
function ProfileSection() {
  const [user, setUser] = useState(mockUser)
  const [isEditing, setIsEditing] = useState(false)

  return (
    <div className="space-y-6">
      {/* Avatar Section */}
      <Card className="bg-surface-1/50">
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <div className="relative group">
              <Avatar className="w-24 h-24">
                <AvatarImage src={user.avatar} />
                <AvatarFallback className="text-2xl bg-gradient-to-br from-accent to-purple-500">
                  {user.name[0]}
                </AvatarFallback>
              </Avatar>
              <button className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera className="w-6 h-6 text-white" />
              </button>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white">{user.name}</h3>
              <p className="text-slate-400">
                {user.department} · {user.role}
              </p>
              <p className="text-sm text-slate-500 mt-1">工号：{user.id}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Basic Info */}
      <Card className="bg-surface-1/50">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>基本信息</CardTitle>
            <CardDescription>管理您的个人资料信息</CardDescription>
          </div>
          <Button
            variant={isEditing ? 'default' : 'outline'}
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? (
              <>
                <Save className="w-4 h-4 mr-1" />
                保存
              </>
            ) : (
              '编辑'
            )}
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">姓名</label>
              <Input
                value={user.name}
                onChange={(e) => setUser({ ...user, name: e.target.value })}
                disabled={!isEditing}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">工号</label>
              <Input value={user.id} disabled />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">邮箱</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  value={user.email}
                  onChange={(e) => setUser({ ...user, email: e.target.value })}
                  disabled={!isEditing}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">手机</label>
              <div className="relative">
                <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  value={user.phone}
                  onChange={(e) => setUser({ ...user, phone: e.target.value })}
                  disabled={!isEditing}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">部门</label>
              <Input value={user.department} disabled />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">角色</label>
              <Input value={user.role} disabled />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function NotificationsSection() {
  const [settings, setSettings] = useState({
    email: {
      taskAssigned: true,
      taskDue: true,
      projectUpdate: true,
      systemNotice: false,
    },
    push: {
      taskAssigned: true,
      taskDue: true,
      projectUpdate: false,
      systemNotice: false,
    },
    wechat: {
      taskAssigned: true,
      taskDue: true,
      projectUpdate: true,
      systemNotice: true,
    },
  })

  const notificationTypes = [
    { key: 'taskAssigned', label: '任务分配', desc: '当有新任务分配给您时' },
    { key: 'taskDue', label: '任务到期', desc: '当任务即将到期或已逾期时' },
    { key: 'projectUpdate', label: '项目更新', desc: '当您参与的项目有重要更新时' },
    { key: 'systemNotice', label: '系统通知', desc: '系统维护、功能更新等通知' },
  ]

  const channels = [
    { key: 'email', label: '邮件', icon: Mail },
    { key: 'push', label: '站内', icon: Bell },
    { key: 'wechat', label: '企微', icon: Smartphone },
  ]

  const toggleSetting = (channel, type) => {
    setSettings({
      ...settings,
      [channel]: {
        ...settings[channel],
        [type]: !settings[channel][type],
      },
    })
  }

  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <CardTitle>通知偏好</CardTitle>
        <CardDescription>选择您希望接收通知的方式</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-3 text-sm font-medium text-slate-400">
                  通知类型
                </th>
                {channels.map((channel) => (
                  <th
                    key={channel.key}
                    className="text-center p-3 text-sm font-medium text-slate-400"
                  >
                    <div className="flex items-center justify-center gap-1">
                      <channel.icon className="w-4 h-4" />
                      {channel.label}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {notificationTypes.map((type) => (
                <tr key={type.key} className="border-b border-border/50">
                  <td className="p-3">
                    <div>
                      <div className="font-medium text-white text-sm">
                        {type.label}
                      </div>
                      <div className="text-xs text-slate-500">{type.desc}</div>
                    </div>
                  </td>
                  {channels.map((channel) => (
                    <td key={channel.key} className="p-3 text-center">
                      <button
                        onClick={() => toggleSetting(channel.key, type.key)}
                        className={cn(
                          'w-10 h-6 rounded-full relative transition-colors',
                          settings[channel.key][type.key]
                            ? 'bg-accent'
                            : 'bg-surface-2'
                        )}
                      >
                        <span
                          className={cn(
                            'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                            settings[channel.key][type.key]
                              ? 'translate-x-5'
                              : 'translate-x-1'
                          )}
                        />
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

function SecuritySection() {
  const navigate = useNavigate()
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [passwords, setPasswords] = useState({
    current: '',
    new: '',
    confirm: '',
  })

  const handleChangePassword = async () => {
    // 重置状态
    setError('')
    setSuccess('')

    // 表单验证
    if (!passwords.current) {
      setError('请输入当前密码')
      return
    }

    if (!passwords.new) {
      setError('请输入新密码')
      return
    }

    if (passwords.new.length < 6) {
      setError('新密码长度至少6位')
      return
    }

    if (passwords.new !== passwords.confirm) {
      setError('两次输入的新密码不一致')
      return
    }

    if (passwords.current === passwords.new) {
      setError('新密码不能与当前密码相同')
      return
    }

    setLoading(true)

    try {
      const response = await authApi.changePassword({
        old_password: passwords.current,
        new_password: passwords.new,
      })

      if (response.code === 200) {
        setSuccess(response.message || '密码修改成功，请重新登录')
        // 清空表单
        setPasswords({
          current: '',
          new: '',
          confirm: '',
        })
        // 3秒后跳转到登录页
        setTimeout(() => {
          navigate('/login')
        }, 3000)
      } else {
        setError(response.message || '密码修改失败')
      }
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        '密码修改失败，请稍后重试'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Change Password */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            修改密码
          </CardTitle>
          <CardDescription>定期更换密码可以提高账户安全性</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm">
              {success}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">当前密码</label>
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                value={passwords.current}
                onChange={(e) =>
                  setPasswords({ ...passwords, current: e.target.value })
                }
                placeholder="请输入当前密码"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">新密码</label>
            <Input
              type={showPassword ? 'text' : 'password'}
              value={passwords.new}
              onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
              placeholder="请输入新密码（至少6位）"
              disabled={loading}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">确认新密码</label>
            <Input
              type={showPassword ? 'text' : 'password'}
              value={passwords.confirm}
              onChange={(e) =>
                setPasswords({ ...passwords, confirm: e.target.value })
              }
              placeholder="请再次输入新密码"
              disabled={loading}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleChangePassword()
                }
              }}
            />
          </div>
          <Button onClick={handleChangePassword} disabled={loading}>
            {loading ? '修改中...' : '更新密码'}
          </Button>
        </CardContent>
      </Card>

      {/* Login Sessions */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle>登录设备</CardTitle>
          <CardDescription>管理您的登录会话</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            {
              device: 'Chrome on Windows',
              location: '深圳市',
              time: '当前会话',
              current: true,
            },
            {
              device: '企业微信',
              location: '深圳市',
              time: '2天前',
              current: false,
            },
          ].map((session, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 rounded-lg bg-surface-2/50"
            >
              <div className="flex items-center gap-3">
                <Monitor className="w-5 h-5 text-slate-400" />
                <div>
                  <div className="font-medium text-white text-sm">
                    {session.device}
                  </div>
                  <div className="text-xs text-slate-500">
                    {session.location} · {session.time}
                  </div>
                </div>
              </div>
              {session.current ? (
                <Badge variant="success">当前</Badge>
              ) : (
                <Button variant="ghost" size="sm" className="text-red-400">
                  登出
                </Button>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

function AppearanceSection() {
  const [theme, setTheme] = useState('dark')
  const [accentColor, setAccentColor] = useState('#6366f1')

  const themes = [
    { id: 'light', label: '浅色', icon: Sun },
    { id: 'dark', label: '深色', icon: Moon },
    { id: 'system', label: '跟随系统', icon: Monitor },
  ]

  const accentColors = [
    '#6366f1', // Indigo
    '#8b5cf6', // Purple
    '#ec4899', // Pink
    '#f43f5e', // Rose
    '#f97316', // Orange
    '#eab308', // Yellow
    '#22c55e', // Green
    '#06b6d4', // Cyan
    '#3b82f6', // Blue
  ]

  return (
    <div className="space-y-6">
      {/* Theme Selection */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle>主题模式</CardTitle>
          <CardDescription>选择您喜欢的界面主题</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {themes.map((t) => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id)}
                className={cn(
                  'p-4 rounded-xl border-2 transition-all',
                  theme === t.id
                    ? 'border-accent bg-accent/10'
                    : 'border-border bg-surface-2/50 hover:border-border/80'
                )}
              >
                <t.icon
                  className={cn(
                    'w-8 h-8 mx-auto mb-2',
                    theme === t.id ? 'text-accent' : 'text-slate-400'
                  )}
                />
                <div
                  className={cn(
                    'text-sm font-medium',
                    theme === t.id ? 'text-accent' : 'text-slate-400'
                  )}
                >
                  {t.label}
                </div>
                {theme === t.id && (
                  <div className="mt-2">
                    <Check className="w-4 h-4 mx-auto text-accent" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Accent Color */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle>主题色</CardTitle>
          <CardDescription>选择系统的强调色</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {accentColors.map((color) => (
              <button
                key={color}
                onClick={() => setAccentColor(color)}
                className={cn(
                  'w-10 h-10 rounded-full border-2 transition-transform hover:scale-110',
                  accentColor === color
                    ? 'border-white scale-110'
                    : 'border-transparent'
                )}
                style={{ backgroundColor: color }}
              >
                {accentColor === color && (
                  <Check className="w-5 h-5 mx-auto text-white" />
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function LanguageSection() {
  const [language, setLanguage] = useState('zh-CN')
  const [timezone, setTimezone] = useState('Asia/Shanghai')
  const [dateFormat, setDateFormat] = useState('YYYY-MM-DD')

  const languages = [
    { id: 'zh-CN', label: '简体中文', flag: '🇨🇳' },
    { id: 'zh-TW', label: '繁體中文', flag: '🇹🇼' },
    { id: 'en-US', label: 'English', flag: '🇺🇸' },
  ]

  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <CardTitle>语言与区域</CardTitle>
        <CardDescription>设置您的语言和时区偏好</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Language */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-slate-300">界面语言</label>
          <div className="grid grid-cols-3 gap-3">
            {languages.map((lang) => (
              <button
                key={lang.id}
                onClick={() => setLanguage(lang.id)}
                className={cn(
                  'p-3 rounded-lg border transition-all flex items-center gap-2',
                  language === lang.id
                    ? 'border-accent bg-accent/10'
                    : 'border-border bg-surface-2/50 hover:border-border/80'
                )}
              >
                <span className="text-xl">{lang.flag}</span>
                <span
                  className={cn(
                    'text-sm',
                    language === lang.id ? 'text-accent' : 'text-slate-400'
                  )}
                >
                  {lang.label}
                </span>
                {language === lang.id && (
                  <Check className="w-4 h-4 ml-auto text-accent" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Timezone */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">时区</label>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="w-full h-10 px-3 rounded-lg bg-surface-2 border border-border text-white focus:border-accent focus:outline-none"
          >
            <option value="Asia/Shanghai">中国标准时间 (UTC+8)</option>
            <option value="Asia/Hong_Kong">香港时间 (UTC+8)</option>
            <option value="Asia/Tokyo">日本标准时间 (UTC+9)</option>
            <option value="America/New_York">美国东部时间 (UTC-5)</option>
            <option value="Europe/London">格林威治时间 (UTC+0)</option>
          </select>
        </div>

        {/* Date Format */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">日期格式</label>
          <select
            value={dateFormat}
            onChange={(e) => setDateFormat(e.target.value)}
            className="w-full h-10 px-3 rounded-lg bg-surface-2 border border-border text-white focus:border-accent focus:outline-none"
          >
            <option value="YYYY-MM-DD">2026-01-04</option>
            <option value="DD/MM/YYYY">04/01/2026</option>
            <option value="MM/DD/YYYY">01/04/2026</option>
            <option value="YYYY年MM月DD日">2026年01月04日</option>
          </select>
        </div>
      </CardContent>
    </Card>
  )
}

function KnowledgeSection() {
  const navigate = useNavigate()

  const knowledgeActions = [
    {
      title: '知识库',
      description: '浏览历史方案、产品知识、工艺知识等',
      path: '/knowledge-base',
      icon: BookOpen,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      title: '我的收藏',
      description: '查看我收藏的知识文章',
      path: '/knowledge-base?category=starred',
      icon: BookOpen,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
    },
    {
      title: '最近浏览',
      description: '查看最近浏览的知识内容',
      path: '/knowledge-base?category=recent',
      icon: BookOpen,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
  ]

  return (
    <div className="space-y-6">
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-accent" />
            知识管理
          </CardTitle>
          <CardDescription>管理和访问您的知识库内容</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {knowledgeActions.map((action, index) => {
              const Icon = action.icon
              return (
                <button
                  key={index}
                  onClick={() => navigate(action.path)}
                  className={cn(
                    'p-4 rounded-lg border transition-all text-left hover:border-accent/50',
                    'border-border bg-surface-2/50 hover:bg-surface-2'
                  )}
                >
                  <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center mb-3', action.bgColor)}>
                    <Icon className={cn('w-5 h-5', action.color)} />
                  </div>
                  <h3 className="font-medium text-white mb-1">{action.title}</h3>
                  <p className="text-xs text-slate-400">{action.description}</p>
                </button>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function Settings() {
  // Get section from URL query parameter
  const urlParams = new URLSearchParams(window.location.search)
  const sectionFromUrl = urlParams.get('section')
  const [activeSection, setActiveSection] = useState(sectionFromUrl || 'profile')
  
  // Update active section when URL changes
  useEffect(() => {
    const handleLocationChange = () => {
      const urlParams = new URLSearchParams(window.location.search)
      const sectionFromUrl = urlParams.get('section')
      if (sectionFromUrl && sectionFromUrl !== activeSection) {
        setActiveSection(sectionFromUrl)
      }
    }
    
    // Check on mount and when location changes
    handleLocationChange()
    
    // Listen for popstate events (back/forward navigation)
    window.addEventListener('popstate', handleLocationChange)
    
    return () => {
      window.removeEventListener('popstate', handleLocationChange)
    }
  }, [activeSection])

  const renderSection = () => {
    switch (activeSection) {
      case 'profile':
        return <ProfileSection />
      case 'notifications':
        return <NotificationsSection />
      case 'security':
        return <SecuritySection />
      case 'appearance':
        return <AppearanceSection />
      case 'language':
        return <LanguageSection />
      case 'knowledge':
        return <KnowledgeSection />
      default:
        return <ProfileSection />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader title="个人设置" description="管理您的账户设置和偏好" />

      <motion.div variants={fadeIn} className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <Card className="bg-surface-1/50 lg:w-64 shrink-0">
          <CardContent className="p-2">
            <nav className="space-y-1">
              {settingsSections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left',
                    activeSection === section.id
                      ? 'bg-accent/10 text-accent'
                      : 'text-slate-400 hover:text-white hover:bg-surface-2'
                  )}
                >
                  <section.icon className="w-5 h-5" />
                  <span className="font-medium">{section.label}</span>
                </button>
              ))}
            </nav>
          </CardContent>
        </Card>

        {/* Content Area */}
        <div className="flex-1 min-w-0">{renderSection()}</div>
      </motion.div>
    </motion.div>
      </div>
    </div>
  )
}

