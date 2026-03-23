/**
 * 登录页面
 * 项目进度管理系统入口，支持快捷登录
 */

import { cn } from '../../lib/utils';
import { useLogin } from './hooks/useLogin';
import { FEATURES, DEMO_ACCOUNTS } from './constants';

export default function Login({ onLoginSuccess }) {
  const login = useLogin(onLoginSuccess);

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* 动画背景 */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-surface-100 via-surface-50 to-[#16213e]" />
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
            maskImage: "radial-gradient(ellipse at center, black 0%, transparent 70%)"
          }}
        />
        <motion.div animate={{ y: [0, -20, 0], scale: [1, 1.05, 1] }} transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }} className="absolute -top-32 -left-16 w-[500px] h-[500px] rounded-full bg-violet-600/20 blur-[100px]" />
        <motion.div animate={{ y: [0, 20, 0], scale: [1, 1.05, 1] }} transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }} className="absolute -bottom-32 -right-16 w-[400px] h-[400px] rounded-full bg-indigo-600/15 blur-[80px]" />
        <motion.div animate={{ y: [0, -10, 0], scale: [1, 1.05, 1] }} transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 4 }} className="absolute top-[10%] left-[5%] w-[300px] h-[300px] rounded-full border border-white/5" />
      </div>

      {/* 主内容 */}
      <div className="flex w-full min-h-screen relative z-10">
        {/* 左侧品牌 */}
        <div className="hidden lg:flex flex-col justify-between flex-1 max-w-[580px] p-12 text-white">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/10 mb-8">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-medium">项目进度管理系统</span>
            </div>
            <h1 className="text-5xl font-bold leading-tight mb-6">让每个项目<br /><span className="text-gradient-primary">尽在掌控</span></h1>
            <p className="text-lg text-slate-400 mb-12 max-w-md">专为非标自动化设备企业打造的智能项目管理平台，实现项目全生命周期的精细化管控。</p>
            <div className="space-y-5">
              {(FEATURES || []).map((feature, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.4 + i * 0.1 }} className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-primary/15 border border-primary/25"><feature.icon className="h-5 w-5 text-primary" /></div>
                  <div><h4 className="font-semibold mb-1">{feature.title}</h4><p className="text-sm text-slate-500">{feature.desc}</p></div>
                </motion.div>
              ))}
            </div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.8 }}>
              <p className="text-sm text-slate-500">受到 <span className="text-white font-medium">200+</span> 家企业的信赖</p>
            </motion.div>
          </motion.div>
        </div>

        {/* 右侧表单 */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-white">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }} className="w-full max-w-md">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">欢迎回来</h2>
              <p className="text-gray-500">登录您的账户以继续</p>
            </div>

            <form onSubmit={login.handleSubmit} className="space-y-5">
              {/* 用户名 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"><User className="h-5 w-5" /></div>
                  <input type="text" value={login.username} onChange={(e) => login.setUsername(e.target.value)} placeholder="请输入用户名" required className={cn("w-full h-[52px] pl-12 pr-4 rounded-xl", "bg-gray-50 border-2 border-transparent", "text-gray-900 placeholder:text-gray-400", "transition-all duration-200", "hover:bg-gray-100", "focus:bg-white focus:border-primary focus:outline-none", "focus:ring-4 focus:ring-primary/10")} />
                </div>
              </div>

              {/* 密码 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">密码</label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"><Lock className="h-5 w-5" /></div>
                  <input type={login.showPassword ? "text" : "password"} value={login.password} onChange={(e) => login.setPassword(e.target.value)} placeholder="请输入密码" required className={cn("w-full h-[52px] pl-12 pr-12 rounded-xl", "bg-gray-50 border-2 border-transparent", "text-gray-900 placeholder:text-gray-400", "transition-all duration-200", "hover:bg-gray-100", "focus:bg-white focus:border-primary focus:outline-none", "focus:ring-4 focus:ring-primary/10")} />
                  <button type="button" onClick={() => login.setShowPassword(!login.showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors">
                    {login.showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              {/* 选项 */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={login.rememberMe} onChange={(e) => login.setRememberMe(e.target.checked)} className="sr-only" />
                  <div className={cn("w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all", login.rememberMe ? "bg-primary border-primary" : "border-gray-300")}>
                    {login.rememberMe && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" /></svg>}
                  </div>
                  <span className="text-sm text-gray-600">记住登录状态</span>
                </label>
                <a href="#" className="text-sm font-medium text-primary hover:text-primary-dark underline">忘记密码？</a>
              </div>

              {/* 错误提示 */}
              {login.error && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-sm text-red-500 text-center space-y-2">
                  <p>{login.error}</p>
                  <button type="button" onClick={() => { login.diagnoseLogin(); alert("请查看浏览器控制台（F12）查看详细诊断信息"); }} className="text-xs text-blue-500 hover:text-blue-700 underline">点击运行诊断工具</button>
                </motion.div>
              )}

              {/* 登录按钮 */}
              <motion.button type="submit" disabled={login.loading} whileTap={{ scale: 0.98 }} className={cn("relative w-full h-[52px] rounded-xl", "bg-gradient-to-r from-violet-600 to-indigo-600", "text-white font-semibold", "flex items-center justify-center gap-2", "shadow-lg shadow-violet-500/30", "hover:shadow-violet-500/50 hover:scale-[1.02]", "active:scale-[0.98]", "transition-all duration-200", "disabled:opacity-70 disabled:cursor-not-allowed")}>
                {login.loading ? (
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (<><span>登录</span><ArrowRight className="h-5 w-5" /></>)}
              </motion.button>
            </form>

            {/* 快捷登录 */}
            <div className="mt-8">
              <div className="relative">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
                <div className="relative flex justify-center text-sm"><span className="px-4 bg-white text-gray-500">快捷登录</span></div>
              </div>
              <div className="mt-4 grid grid-cols-4 gap-2">
                {DEMO_ACCOUNTS.map((account) => (
                  <motion.button
                    key={account.username}
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => { login.setUsername(account.username); login.setPassword('123456'); }}
                    className={cn("flex items-center gap-1.5 p-2.5 rounded-lg", `bg-gradient-to-br ${account.colorClass}`, "transition-all duration-200", "group text-xs")}
                  >
                    <div className={cn("p-1.5 rounded-lg transition-colors flex-shrink-0", account.iconBg)}>
                      <account.icon className={cn("h-3.5 w-3.5", account.iconColor)} />
                    </div>
                    <div className="text-left min-w-0">
                      <p className="font-medium text-gray-900 truncate">{account.name}</p>
                      <p className="text-xs text-gray-500">{account.role}</p>
                    </div>
                  </motion.button>
                ))}
              </div>
              <p className="mt-3 text-xs text-gray-400 text-center">点击上方按钮自动填充账号，然后点击登录</p>
            </div>

            <p className="mt-6 text-xs text-gray-400 text-center">&copy; 2026 项目进度管理系统 &middot; 安全登录</p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
