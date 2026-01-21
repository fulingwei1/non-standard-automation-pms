import { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';
import { authApi } from '../services/api';
import { diagnoseLogin } from '../utils/diagnose';
import { logger } from '../utils/logger';
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
  UserCircle } from
'lucide-react';

const features = [
{
  icon: BarChart3,
  title: "实时进度追踪",
  desc: "甘特图、看板多视图"
},
{
  icon: Clock,
  title: "智能工时管理",
  desc: "自动统计、负荷预警"
},
{
  icon: Users,
  title: "团队高效协作",
  desc: "任务分配、实时同步"
},
{
  icon: AlertTriangle,
  title: "AI 智能预警",
  desc: "风险识别、提前预警"
}];


export default function Login({ onLoginSuccess }) {const _errorCode_1 = null;
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      // 纯真实 API 登录
      const response = await authApi.login(formData);

      // 处理响应数据
      const token =
      response.data?.access_token ||
      response.data?.data?.access_token ||
      response.access_token;

      if (!token) {
        logger.error("登录响应格式错误:", response);
        throw new Error("服务器返回格式错误，请检查后端服务");
      }

      // 清理之前的用户信息
      localStorage.removeItem("user");

      // 保存 token
      localStorage.setItem("token", token);

      // 获取用户信息
      try {
        const userResponse = await authApi.me();
        const userData = userResponse.data;

        if (userData) {
          // 将后端返回的用户数据转换为前端需要的格式
          // 确保权限列表被保存到 localStorage
          if (userData.permissions && Array.isArray(userData.permissions)) {
            // 权限列表已从后端获取，直接使用
            logger.debug(
              "[Login] 用户权限列表:",
              userData.permissions.length,
              "个权限"
            );
          } else {
            // 如果没有权限列表，初始化为空数组
            userData.permissions = [];
          }

          // 确定用户角色
          let userRole = "user";

          // 优先从角色名称中提取角色代码
          if (userData.roles && userData.roles.length > 0) {
            const roleName = userData.roles[0];
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
              BUYER: "buyer"
            };

            // 先尝试精确匹配
            userRole =
            roleMap[roleName] ||
            // 尝试忽略大小写匹配
            Object.keys(roleMap).find(
              (key) => key.toLowerCase() === roleName.toLowerCase()
            ) || (
            // 智能匹配：如果角色名称包含特定关键词，映射到对应角色
            roleName.includes("总经理") ||
            roleName.includes("GeneralManager") ||
            roleName === "GM" ?
            "gm" :
            roleName.includes("生产") && !roleName.includes("制造") ?
            "production_manager" :
            roleName.includes("制造") && roleName.includes("总监") ?
            "manufacturing_director" :
            roleName.includes("采购") && (
            roleName.includes("经理") ||
            roleName.includes("Manager")) ?
            "procurement_manager" :
            roleName.includes("采购") && (
            roleName.includes("工程师") || roleName.includes("Engineer")) ?
            "procurement_engineer" :
            roleName.includes("采购") && roleName.includes("员") ?
            "buyer" :
            // 最后转换为下划线格式
            roleName.
            toLowerCase().
            replace(/\s+/g, "_").
            replace(/-/g, "_"));
          } else if (userData.is_superuser) {
            // 如果没有角色信息但 is_superuser 为 true，默认使用 super_admin
            userRole = "super_admin";
          } else {
            // 用户没有分配角色且不是超级管理员，显示警告
            logger.warn("[Login] 用户没有分配角色:", userData.username);
            // 清除 token
            localStorage.removeItem("token");
            setError("您的账号尚未分配角色，请联系管理员进行角色配置");
            setLoading(false);
            return;
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
            permissions: userData.permissions || [] // 保存权限列表
          };

          localStorage.setItem("user", JSON.stringify(frontendUser));
          logger.debug(
            "[Login] 用户权限已保存:",
            frontendUser.permissions.length,
            "个权限"
          );
          onLoginSuccess();
          return;
        }
      } catch (userErr) {
        logger.error("获取用户信息失败:", userErr);
        // 清除已保存的 token，因为无法获取用户信息
        localStorage.removeItem("token");

        // 根据错误类型给出不同提示
        let userErrMessage = "获取用户信息失败，请重新登录";

        if (userErr.response?.status === 500) {
          // 服务器内部错误，可能是数据库问题或角色未配置
          userErrMessage = "系统错误：无法加载用户角色信息，请联系管理员检查账号配置";
        } else if (userErr.response?.status === 401) {
          // Token 无效
          userErrMessage = "登录凭证已过期，请重新登录";
        } else if (userErr.response?.status === 404) {
          // 用户不存在
          userErrMessage = "用户账号不存在或已被删除，请联系管理员";
        } else if (!userErr.response) {
          // 网络错误
          userErrMessage = "网络连接失败，请检查网络后重试";
        }

        setError(userErrMessage);
        setLoading(false);
        return;
      }

      onLoginSuccess();
    } catch (err) {
      logger.error("登录错误:", err);

      // 更详细的错误信息
      let errorMessage = "登录失败，请检查用户名和密码";
      let _errorCode_1 = "";

      if (err.code === "ECONNABORTED" || err.message?.includes("timeout")) {
        // 超时错误
        errorMessage = "登录请求超时，请检查网络连接或稍后重试";
      } else if (err.response) {
        // 服务器返回了错误响应
        const detail = err.response.data?.detail;
        const status = err.response.status;
        const rawData = err.response.data;
        const contentType =
        err.response.headers?.["content-type"] ||
        err.response.headers?.["Content-Type"];

        // Vite 代理错误/后端不可达时，常见是 500 且返回文本包含 ECONNREFUSED 等关键字
        if (
        status === 500 && (
        typeof rawData === "string" && (
        rawData.includes("ECONNREFUSED") ||
        rawData.includes("proxy") ||
        rawData.includes("connect") ||
        rawData.includes("127.0.0.1:8000")) ||
        typeof contentType === "string" && (
        contentType.includes("text/html") ||
        contentType.includes("text/plain"))))
        {
          errorMessage =
          "无法连接到后端服务（127.0.0.1:8000），请确认后端已启动（运行 ./start.sh）";
          setError(errorMessage);
          return;
        }

        // 检查是否是新的错误响应格式（包含 error_code 和 message）
        if (detail && typeof detail === "object" && detail.error_code) {
          const _errorCode = detail.error_code;
          errorMessage = detail.message;

          // 根据错误码添加额外提示
          switch (_errorCode) {
            case "USER_NOT_FOUND":
              // 账号不存在
              errorMessage = "该员工尚未开通系统账号，请联系管理员";
              break;
            case "USER_INACTIVE":
              // 账号未激活
              errorMessage = "账号待激活，请联系管理员开通系统访问权限";
              break;
            case "USER_DISABLED":
              // 账号已禁用
              errorMessage = "账号已被禁用，如有疑问请联系管理员";
              break;
            case "WRONG_PASSWORD":
              // 密码错误
              errorMessage = "密码错误，忘记密码请联系管理员重置";
              break;
            default:
              errorMessage = detail.message || errorMessage;
              break;
          }
        } else if (typeof detail === "string") {
          errorMessage = detail;
        } else if (err.response.data?.message) {
          errorMessage = err.response.data.message || errorMessage;
        } else if (status === 500) {
          errorMessage =
          "后端服务发生内部错误(500)。请查看后端日志 logs/backend.log 获取具体报错";
        }
      } else if (err.request) {
        // 请求已发出但没有收到响应
        errorMessage = "无法连接到服务器，请检查后端服务是否启动";
      } else {
        // 其他错误
        errorMessage = err.message || errorMessage;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

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
          }} />


        {/* Animated glow orbs */}
        <motion.div
          animate={{ y: [0, -20, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-32 -left-16 w-[500px] h-[500px] rounded-full bg-violet-600/20 blur-[100px]" />

        <motion.div
          animate={{ y: [0, 20, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          className="absolute -bottom-32 -right-16 w-[400px] h-[400px] rounded-full bg-indigo-600/15 blur-[80px]" />

        <motion.div
          animate={{ y: [0, -10, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 4 }}
          className="absolute top-[10%] left-[5%] w-[300px] h-[300px] rounded-full border border-white/5" />

      </div>

      {/* Main Content */}
      <div className="flex w-full min-h-screen relative z-10">
        {/* Left - Brand Section */}
        <div className="hidden lg:flex flex-col justify-between flex-1 max-w-[580px] p-12 text-white">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}>

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
              {features.map((feature, i) =>
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.4 + i * 0.1 }}
                className="flex items-start gap-4">

                  <div className="p-3 rounded-xl bg-primary/15 border border-primary/25">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">{feature.title}</h4>
                    <p className="text-sm text-slate-500">{feature.desc}</p>
                  </div>
              </motion.div>
              )}
            </div>

            {/* Stats */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.8 }}>

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
            className="w-full max-w-md">

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
                    )} />

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
                    )} />

                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors">

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
                    className="sr-only" />

                  <div className={cn(
                    "w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all",
                    rememberMe ?
                    "bg-primary border-primary" :
                    "border-gray-300"
                  )}>
                    {rememberMe &&
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                    </svg>
                    }
                  </div>
                  <span className="text-sm text-gray-600">记住登录状态</span>
                </label>
                <a href="#" className="text-sm font-medium text-primary hover:text-primary-dark underline">
                  忘记密码？
                </a>
              </div>

              {/* Error */}
              {error &&
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-red-500 text-center space-y-2">

                  <p>{error}</p>
                  <button
                  type="button"
                  onClick={() => {
                    diagnoseLogin();
                    alert("请查看浏览器控制台（F12）查看详细诊断信息");
                  }}
                  className="text-xs text-blue-500 hover:text-blue-700 underline">

                    点击运行诊断工具
                  </button>
              </motion.div>
              }

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
                )}>

                {loading ?
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg> :

                <>
                    <span>登录</span>
                    <ArrowRight className="h-5 w-5" />
                </>
                }
              </motion.button>
            </form>

            {/* Quick Login Buttons */}
            <div className="mt-8">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white text-gray-500">快捷登录</span>
                </div>
              </div>

              {/* Demo Accounts */}
              <div className="mt-4 grid grid-cols-3 gap-2">
                {/* 郑汝才 - 常务副总 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('zhengrucai');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-emerald-50 to-emerald-100",
                    "border border-emerald-200 hover:border-emerald-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-emerald-100 group-hover:bg-emerald-200 transition-colors flex-shrink-0">
                    <Award className="h-3.5 w-3.5 text-emerald-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">郑汝才</p>
                    <p className="text-xs text-gray-500">常务副总</p>
                  </div>
                </motion.button>

                {/* 骆奕兴 - 副总经理 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('luoyixing');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-cyan-50 to-cyan-100",
                    "border border-cyan-200 hover:border-cyan-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-cyan-100 group-hover:bg-cyan-200 transition-colors flex-shrink-0">
                    <Settings className="h-3.5 w-3.5 text-cyan-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">骆奕兴</p>
                    <p className="text-xs text-gray-500">副总经理</p>
                  </div>
                </motion.button>

                {/* 宋魁 - 营销中心总监 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('songkui');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-rose-50 to-rose-100",
                    "border border-rose-200 hover:border-rose-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-rose-100 group-hover:bg-rose-200 transition-colors flex-shrink-0">
                    <TrendingUp className="h-3.5 w-3.5 text-rose-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">宋魁</p>
                    <p className="text-xs text-gray-500">营销总监</p>
                  </div>
                </motion.button>

                {/* 郑琴 - 销售经理 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('zhengqin');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-teal-50 to-teal-100",
                    "border border-teal-200 hover:border-teal-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-teal-100 group-hover:bg-teal-200 transition-colors flex-shrink-0">
                    <DollarSign className="h-3.5 w-3.5 text-teal-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">郑琴</p>
                    <p className="text-xs text-gray-500">销售经理</p>
                  </div>
                </motion.button>

                {/* 姚洪 - 销售工程师 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('yaohong');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-pink-50 to-pink-100",
                    "border border-pink-200 hover:border-pink-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-pink-100 group-hover:bg-pink-200 transition-colors flex-shrink-0">
                    <Briefcase className="h-3.5 w-3.5 text-pink-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">姚洪</p>
                    <p className="text-xs text-gray-500">销售工程师</p>
                  </div>
                </motion.button>

                {/* 常雄 - PMC主管 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('changxiong');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-green-50 to-green-100",
                    "border border-green-200 hover:border-green-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-green-100 group-hover:bg-green-200 transition-colors flex-shrink-0">
                    <ShoppingCart className="h-3.5 w-3.5 text-green-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">常雄</p>
                    <p className="text-xs text-gray-500">PMC主管</p>
                  </div>
                </motion.button>

                {/* 高勇 - 生产部经理 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('gaoyong');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-amber-50 to-amber-100",
                    "border border-amber-200 hover:border-amber-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-amber-100 group-hover:bg-amber-200 transition-colors flex-shrink-0">
                    <Hammer className="h-3.5 w-3.5 text-amber-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">高勇</p>
                    <p className="text-xs text-gray-500">生产部经理</p>
                  </div>
                </motion.button>

                {/* 陈亮 - 项目管理部总监 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('chenliang');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-indigo-50 to-indigo-100",
                    "border border-indigo-200 hover:border-indigo-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-indigo-100 group-hover:bg-indigo-200 transition-colors flex-shrink-0">
                    <Target className="h-3.5 w-3.5 text-indigo-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">陈亮</p>
                    <p className="text-xs text-gray-500">项目管理部总监</p>
                  </div>
                </motion.button>

                {/* 谭章斌 - 项目经理 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('tanzhangbin');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-blue-50 to-blue-100",
                    "border border-blue-200 hover:border-blue-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-blue-100 group-hover:bg-blue-200 transition-colors flex-shrink-0">
                    <GitBranch className="h-3.5 w-3.5 text-blue-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">谭章斌</p>
                    <p className="text-xs text-gray-500">项目经理</p>
                  </div>
                </motion.button>

                {/* 于振华 - 经理 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('yuzhenhua');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-slate-50 to-slate-100",
                    "border border-slate-200 hover:border-slate-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-slate-100 group-hover:bg-slate-200 transition-colors flex-shrink-0">
                    <UserCog className="h-3.5 w-3.5 text-slate-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">于振华</p>
                    <p className="text-xs text-gray-500">经理</p>
                  </div>
                </motion.button>

                {/* 王俊 - 经理 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('wangjun');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-violet-50 to-violet-100",
                    "border border-violet-200 hover:border-violet-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-violet-100 group-hover:bg-violet-200 transition-colors flex-shrink-0">
                    <UserCircle className="h-3.5 w-3.5 text-violet-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">王俊</p>
                    <p className="text-xs text-gray-500">经理</p>
                  </div>
                </motion.button>

                {/* 王志红 - 客服主管 */}
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setUsername('wangzhihong');
                    setPassword('123456');
                  }}
                  className={cn(
                    "flex items-center gap-1.5 p-2.5 rounded-lg",
                    "bg-gradient-to-br from-teal-50 to-teal-100",
                    "border border-teal-200 hover:border-teal-300",
                    "transition-all duration-200",
                    "group text-xs"
                  )}>

                  <div className="p-1.5 rounded-lg bg-teal-100 group-hover:bg-teal-200 transition-colors flex-shrink-0">
                    <Headphones className="h-3.5 w-3.5 text-teal-600" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-medium text-gray-900 truncate">王志红</p>
                    <p className="text-xs text-gray-500">客服主管</p>
                  </div>
                </motion.button>
              </div>

              <p className="mt-3 text-xs text-gray-400 text-center">
                点击上方按钮自动填充账号，然后点击登录
              </p>
            </div>

            {/* Footer */}
            <p className="mt-6 text-xs text-gray-400 text-center">
              © 2026 项目进度管理系统 · 安全登录
            </p>
          </motion.div>
        </div>
      </div>
    </div>);

}
