import { useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { authApi } from '../services/api'
import { diagnoseLogin } from '../utils/diagnose'
import { logger } from '../utils/logger'
import {
  User,
  Lock,
  ArrowRight,
  Eye,
  EyeOff,
  BarChart3,
  Clock,
  Users,
  AlertTriangle,
  Building2,
  Wrench,
  ShoppingCart,
  ClipboardList,
  Cog,
  Zap,
  Code,
  TestTube,
  Target,
  Lightbulb,
  FileText,
  Factory,
  Headphones,
  UserCog,
  Briefcase,
  Crown,
  TrendingUp,
  Settings,
  GitBranch,
  CircuitBoard,
  Hammer,
  ShoppingBag,
  Shield,
  Award,
  DollarSign,
  UserCircle,
} from 'lucide-react'

const features = [
  {
    icon: BarChart3,
    title: "实时进度追踪",
    desc: "甘特图、看板多视图",
  },
  {
    icon: Clock,
    title: "智能工时管理",
    desc: "自动统计、负荷预警",
  },
  {
    icon: Users,
    title: "团队高效协作",
    desc: "任务分配、实时同步",
  },
  {
    icon: AlertTriangle,
    title: "AI 智能预警",
    desc: "风险识别、提前预警",
  },
]

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(true)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const formData = new URLSearchParams()
      formData.append("username", username)
      formData.append("password", password)

      // 纯真实 API 登录
      const response = await authApi.login(formData)

      // 处理响应数据
      const token =
        response.data?.access_token ||
        response.data?.data?.access_token ||
        response.access_token

      if (!token) {
        logger.error("登录响应格式错误:", response)
        throw new Error("服务器返回格式错误，请检查后端服务")
      }

      // 清理之前的用户信息
      localStorage.removeItem("user")

      // 保存 token
      localStorage.setItem("token", token)

      // 获取用户信息
      try {
        const userResponse = await authApi.me()
        const userData = userResponse.data

        if (userData) {
          // 将后端返回的用户数据转换为前端需要的格式
          // 确保权限列表被保存到 localStorage
          if (userData.permissions && Array.isArray(userData.permissions)) {
            // 权限列表已从后端获取，直接使用
            logger.debug(
              "[Login] 用户权限列表:",
              userData.permissions.length,
              "个权限",
            )
          } else {
            // 如果没有权限列表，初始化为空数组
            userData.permissions = []
          }

          // 确定用户角色
          let userRole = "user"

          // 优先从角色名称中提取角色代码
          if (userData.roles && userData.roles.length > 0) {
            const roleName = userData.roles[0]
            // 尝试匹配角色代码（支持中英文和常见变体）
            const roleMap = {
              "系统管理员": "admin",
              ADMIN: "admin",
              Administrator: "admin",
              SUPER_ADMIN: "super_admin",
              SuperAdmin: "super_admin",
              总经理: "gm",
              GM: "gm",
              GeneralManager: "gm",
              项目经理: "pm",
              PM: "pm",
              ProjectManager: "pm",
              销售总监: "sales_director",
              SALES_DIR: "sales_director",
              SalesDirector: "sales_director",
              生产部经理: "production_manager",
              电机生产部经理: "production_manager",
              ProductionManager: "production_manager",
              PRODUCTION_MANAGER: "production_manager",
              制造总监: "manufacturing_director",
              ManufacturingDirector: "manufacturing_director",
              MANUFACTURING_DIRECTOR: "manufacturing_director",
              计划管理: "pmc",
              PMC: "pmc",
              采购部经理: "procurement_manager",
              采购经理: "procurement_manager",
              ProcurementManager: "procurement_manager",
              PROCUREMENT_MANAGER: "procurement_manager",
              采购工程师: "procurement_engineer",
              ProcurementEngineer: "procurement_engineer",
              PROCUREMENT_ENGINEER: "procurement_engineer",
              采购员: "buyer",
              Buyer: "buyer",
              BUYER: "buyer",
            }

            // 先尝试精确匹配
            userRole =
              roleMap[roleName] ||
              // 尝试忽略大小写匹配
              Object.keys(roleMap).find(
                (key) => key.toLowerCase() === roleName.toLowerCase()
              ) ||
              // 智能匹配：如果角色名称包含特定关键词，映射到对应角色
              (roleName.includes("总经理") ||
                roleName.includes("GeneralManager") ||
                roleName === "GM"
                  ? "gm"
                  : roleName.includes("生产") && !roleName.includes("制造")
                    ? "production_manager"
                    : roleName.includes("制造") && roleName.includes("总监")
                      ? "manufacturing_director"
                      : roleName.includes("采购") &&
                          (roleName.includes("经理") ||
                            roleName.includes("Manager"))
                        ? "procurement_manager"
                        : roleName.includes("采购") &&
                            (roleName.includes("工程师") || roleName.includes("Engineer"))
                          ? "procurement_engineer"
                          : roleName.includes("采购") && roleName.includes("员")
                            ? "buyer"
                            : roleName.toLowerCase().replace(/\s+/g, "_").replace(/-/g, "_"));
          } else if (userData.is_superuser) {
            // 如果没有角色信息但 is_superuser 为 true，默认使用 super_admin
            userRole = "super_admin";
          }

          const frontendUser = {
            id: userData.id,
            username: userData.username,
            real_name: userData.real_name || userData.username,
            email: userData.email,
            phone: userData.phone,
            department: userData.department,
            position: userData.position,
            is_superuser: userData.is_superuser || false,
            isSuperuser: userData.is_superuser || false, // 兼容两种命名
            is_active: userData.is_active,
            roles: userData.roles || [],
            role: userRole,
            permissions: userData.permissions || [], // 保存权限列表
          }

          localStorage.setItem("user", JSON.stringify(frontendUser))
          logger.debug(
            "[Login] 用户权限已保存:",
            frontendUser.permissions.length,
            "个权限",
          )
          onLoginSuccess()
          return
        }
      } catch (userErr) {
        logger.warn("获取用户信息失败，使用备用信息:", userErr)
        // 如果获取用户信息失败，创建基本用户信息（默认为管理员）
        const fallbackUser = {
          id: 1,
          username: username,
          name: username,
          role: "admin",
          is_superuser: true,
          isSuperuser: true,
          department: "系统",
          roles: ["系统管理员"],
        }

        localStorage.setItem("user", JSON.stringify(fallbackUser))
        onLoginSuccess()
        return
      }

      onLoginSuccess()
    } catch (err) {
      logger.error("登录错误:", err)

      // 更详细的错误信息
      let errorMessage = "登录失败，请检查用户名和密码"
      let errorCode = ""

      if (err.code === "ECONNABORTED" || err.message?.includes("timeout")) {
        // 超时错误
        errorMessage = "登录请求超时，请检查网络连接或稍后重试"
      } else if (err.response) {
        // 服务器返回了错误响应
        const detail = err.response.data?.detail

        // 检查是否是新的错误响应格式（包含 error_code 和 message）
        if (detail && typeof detail === "object" && detail.error_code) {
          errorCode = detail.error_code
          errorMessage = detail.message

          // 根据错误码添加额外提示
          switch (detail.error_code) {
            case "USER_NOT_FOUND":
              // 账号不存在
              errorMessage = "该员工尚未开通系统账号，请联系管理员"
              break
            case "USER_INACTIVE":
              // 账号未激活
              errorMessage = "账号待激活，请联系管理员开通系统访问权限"
              break
            case "USER_DISABLED":
              // 账号已禁用
              errorMessage = "账号已被禁用，如有疑问请联系管理员"
              break
            case "WRONG_PASSWORD":
              // 密码错误
              errorMessage = "密码错误，忘记密码请联系管理员重置"
              break
            default:
              errorMessage = detail.message || errorMessage
              break
          }
        } else if (typeof detail === "string") {
          errorMessage = detail
        } else if (err.response.data?.message) {
          errorMessage = err.response.data.message || errorMessage
        }
      } else if (err.request) {
        // 请求已发出但没有收到响应
        errorMessage = "无法连接到服务器，请检查后端服务是否启动"
      } else {
        // 其他错误
        errorMessage = err.message || errorMessage
      }

      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Base gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-surface-100 via-surface-50 to-[#16213e]" />

        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
            `,
            backgroundSize: "60px 60px",
            maskImage: "radial-gradient(ellipse at center, black 0%, transparent 70%)"
          }}
        />

        {/* Animated glow orbs */}
        <motion.div
          animate={{ y: [0, -20, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-32 -left-16 w-[500px] h-[500px] rounded-full bg-violet-600/20 blur-[100px]"
        />
        <motion.div
          animate={{ y: [0, 20, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute -bottom-32 -right-16 w-[400px] h-[400px] rounded-full bg-indigo-600/15 blur-[80px]"
        />
        <motion.div
          animate={{ y: [0, -10, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 4 }}
          className="absolute top-[10%] left-[5%] w-[300px] h-[300px] rounded-full border border-white/5"
        />
      </div>

      {/* Main Content */}
      <div className="flex w-full min-h-screen relative z-10">
        {/* Left - Brand Section */}
        <div className="hidden lg:flex flex-col justify-between flex-1 max-w-[580px] p-12 text-white">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/10 mb-8">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-medium">项目进度管理系统</span>
            </div>

            {/* Title */}
            <h1 className="text-5xl font-bold leading-tight mb-6">
              让每个项目
              <br />
              <span className="text-gradient-primary">尽在掌控</span>
            </h1>

            {/* Description */}
            <p className="text-lg text-slate-400 mb-12 max-w-md">
              专为非标自动化设备企业打造的智能项目管理平台，实现项目全生命周期的精细化管控。
            </p>

            {/* Features */}
            <div className="space-y-5">
              {features.map((feature, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 + i * 0.1 }}
                  className="flex items-start gap-4"
                >
                  <div className="p-3 rounded-xl bg-primary/15 border border-primary/25">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">{feature.title}</h4>
                    <p className="text-sm text-slate-500">{feature.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Stats */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <p className="text-sm text-slate-500">
                受到 <span className="text-white font-medium">200+</span> {" "}
                家企业的信赖
              </p>
            </motion.div>
          </motion.div>
        </div>

        {/* Right - Form Section */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-white">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="w-full max-w-md"
          >
            {/* Form Header */}
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                欢迎回来
              </h2>
              <p className="text-gray-500">登录您的账户以继续</p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  用户名
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                    <User className="h-5 w-5" />
                  </div>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="请输入用户名"
                    required
                    className={cn(
                      "w-full h-[52px] pl-12 pr-4 rounded-xl",
                      "bg-gray-50 border-2 border-transparent",
                      "text-gray-900 placeholder:text-gray-400",
                      "transition-all duration-200",
                      "hover:bg-gray-100",
                      "focus:bg-white focus:border-primary focus:outline-none",
                      "focus:ring-4 focus:ring-primary/10"
                    )}
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  密码
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                    <Lock className="h-5 w-5" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                    required
                    className={cn(
                      "w-full h-[52px] pl-12 pr-12 rounded-xl",
                      "bg-gray-50 border-2 border-transparent",
                      "text-gray-900 placeholder:text-gray-400",
                      "transition-all duration-200",
                      "hover:bg-gray-100",
                      "focus:bg-white focus:border-primary focus:outline-none",
                      "focus:ring-4 focus:ring-primary/10"
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              {/* Options */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={cn(
                    "w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all",
                    rememberMe
                      ? "bg-primary border-primary"
                      : "border-gray-300"
                  )}>
                    {rememberMe && (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <span className="text-sm text-gray-600">记住登录状态</span>
                </label>
                <a href="#" className="text-sm font-medium text-primary hover:text-primary-dark underline">
                  忘记密码？
                </a>
              </div>

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-red-500 text-center space-y-2"
                >
                  <p>{error}</p>
                  <button
                    type="button"
                    onClick={() => {
                      diagnoseLogin()
                      alert("请查看浏览器控制台（F12）查看详细诊断信息")
                    }}
                    className="text-xs text-blue-500 hover:text-blue-700 underline"
                  >
                    点击运行诊断工具
                  </button>
                </motion.div>
              )}

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={loading}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "relative w-full h-[52px] rounded-xl",
                  "bg-gradient-to-r from-violet-600 to-indigo-600",
                  "text-white font-semibold",
                  "flex items-center justify-center gap-2",
                  "shadow-lg shadow-violet-500/30",
                  "hover:shadow-violet-500/50 hover:scale-[1.02]",
                  "active:scale-[0.98]",
                  "transition-all duration-200",
                  "disabled:opacity-70 disabled:cursor-not-allowed"
                )}
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0c5.373 0 8-8 4v16h8c3.042 0 8-8 4v16h8z" />
                  </svg>
                ) : (
                  <>
                    <span>登录</span>
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </motion.button>
            </form>

            {/* Footer */}
            <p className="mt-8 text-xs text-gray-400 text-center">
              © 2026 项目进度管理系统 · 安全登录
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
