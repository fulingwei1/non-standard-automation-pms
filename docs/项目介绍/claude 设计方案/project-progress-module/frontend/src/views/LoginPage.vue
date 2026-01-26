<template>
  <div class="login-page" :class="{ 'is-loaded': isLoaded }">
    <!-- 动态背景 -->
    <div class="login-bg">
      <div class="bg-gradient"></div>
      <div class="bg-grid"></div>
      <div class="bg-glow bg-glow-1"></div>
      <div class="bg-glow bg-glow-2"></div>
      <div class="bg-glow bg-glow-3"></div>
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
    </div>

    <!-- 主容器 -->
    <div class="login-container">
      <!-- 左侧品牌区 -->
      <div class="login-brand">
        <div class="brand-content">
          <div class="brand-badge">
            <span class="badge-dot"></span>
            <span>项目进度管理系统</span>
          </div>
          
          <h1 class="brand-title">
            让每个项目<br/>
            <span class="gradient-text">尽在掌控</span>
          </h1>
          
          <p class="brand-desc">
            专为非标自动化设备企业打造的智能项目管理平台，
            实现项目全生命周期的精细化管控。
          </p>

          <div class="brand-features">
            <div class="feature-item" v-for="(feature, index) in features" :key="index"
                 :style="{ animationDelay: `${0.4 + index * 0.1}s` }">
              <div class="feature-icon" v-html="feature.icon"></div>
              <div class="feature-text">
                <h4>{{ feature.title }}</h4>
                <p>{{ feature.desc }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="brand-footer">
          <p>受到 <strong>200+</strong> 家企业的信赖</p>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="login-form-section">
        <div class="login-form-wrapper">
          <!-- 移动端Logo -->
          <div class="mobile-brand">
            <div class="mobile-logo">
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <rect width="40" height="40" rx="10" fill="url(#logo-grad)"/>
                <path d="M12 20L18 26L28 14" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                <defs>
                  <linearGradient id="logo-grad" x1="0" y1="0" x2="40" y2="40">
                    <stop stop-color="#6172F3"/>
                    <stop offset="1" stop-color="#444CE7"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <span class="mobile-title">项目进度管理</span>
          </div>

          <!-- 登录卡片 -->
          <div class="login-card">
            <div class="card-header">
              <h2>欢迎回来</h2>
              <p>登录您的账户以继续</p>
            </div>

            <form class="login-form" @submit.prevent="handleLogin">
              <div class="form-group" :class="{ 'has-error': errors.username, 'is-focused': focused === 'username' }">
                <label class="form-label">用户名</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  </div>
                  <input 
                    type="text" 
                    class="form-input"
                    v-model="form.username"
                    placeholder="请输入用户名"
                    @focus="focused = 'username'"
                    @blur="focused = null"
                  />
                  <div class="input-check" v-if="form.username && !errors.username">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                </div>
                <span class="error-text" v-if="errors.username">{{ errors.username }}</span>
              </div>

              <div class="form-group" :class="{ 'has-error': errors.password, 'is-focused': focused === 'password' }">
                <label class="form-label">密码</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  </div>
                  <input 
                    :type="showPassword ? 'text' : 'password'" 
                    class="form-input"
                    v-model="form.password"
                    placeholder="请输入密码"
                    @focus="focused = 'password'"
                    @blur="focused = null"
                  />
                  <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                    <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
                <span class="error-text" v-if="errors.password">{{ errors.password }}</span>
              </div>

              <div class="form-options">
                <label class="checkbox-wrapper">
                  <input type="checkbox" v-model="form.remember" />
                  <span class="checkbox-custom"></span>
                  <span class="checkbox-label">记住登录状态</span>
                </label>
                <a href="#" class="forgot-link">忘记密码？</a>
              </div>

              <button type="submit" class="submit-btn" :class="{ 'is-loading': loading }" :disabled="loading">
                <span class="btn-text">{{ loading ? '登录中...' : '登 录' }}</span>
                <span class="btn-icon" v-if="!loading">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                </span>
                <span class="btn-loader" v-else></span>
              </button>
            </form>

            <!-- 快速登录 -->
            <div class="quick-login">
              <div class="divider"><span>演示账号</span></div>
              <div class="demo-accounts">
                <button v-for="account in demoAccounts" :key="account.role"
                        class="demo-btn" @click="fillDemo(account)">
                  <span class="demo-avatar" :style="{ background: account.color }">{{ account.avatar }}</span>
                  <span class="demo-info">
                    <span class="demo-role">{{ account.role }}</span>
                    <span class="demo-user">{{ account.username }}</span>
                  </span>
                </button>
              </div>
            </div>
          </div>

          <div class="login-footer">
            <p>© 2025 项目进度管理系统</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores'

const router = useRouter()
const userStore = useUserStore()

const isLoaded = ref(false)
const loading = ref(false)
const showPassword = ref(false)
const focused = ref(null)

const form = reactive({ username: '', password: '', remember: true })
const errors = reactive({ username: '', password: '' })

const features = [
  { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>', title: '实时进度追踪', desc: '甘特图、看板多视图' },
  { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>', title: '智能工时管理', desc: '自动统计、负荷预警' },
  { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>', title: '团队高效协作', desc: '任务分配、实时同步' },
  { icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>', title: 'AI 智能预警', desc: '风险识别、提前预警' },
]

const demoAccounts = [
  { role: '管理员', username: 'admin', password: 'admin123', avatar: '管', color: 'linear-gradient(135deg, #6366F1, #4F46E5)' },
  { role: '项目经理', username: 'pm001', password: '123456', avatar: '项', color: 'linear-gradient(135deg, #F59E0B, #D97706)' },
  { role: '工程师', username: 'eng001', password: '123456', avatar: '工', color: 'linear-gradient(135deg, #10B981, #059669)' },
]

const validate = () => {
  errors.username = form.username.trim() ? '' : '请输入用户名'
  errors.password = form.password ? '' : '请输入密码'
  return !errors.username && !errors.password
}

const handleLogin = async () => {
  if (!validate()) return
  loading.value = true
  await new Promise(r => setTimeout(r, 1200))
  try {
    const result = await userStore.login(form)
    if (result.success) router.push('/')
    else errors.password = result.message || '登录失败'
  } catch (e) {
    errors.password = e.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const fillDemo = (account) => {
  form.username = account.username
  form.password = account.password
}

onMounted(() => setTimeout(() => isLoaded.value = true, 100))
</script>

<style scoped>
/* === Login Page === */
.login-page {
  min-height: 100vh;
  display: flex;
  position: relative;
  overflow: hidden;
  background: #0a0a0f;
}

/* === Background === */
.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 0%, transparent 70%);
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
  animation: glow-float 8s ease-in-out infinite;
}

.bg-glow-1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.4) 0%, transparent 70%);
  top: -200px; left: -100px;
}

.bg-glow-2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  bottom: -150px; right: -100px;
  animation-delay: 2s;
}

.bg-glow-3 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.25) 0%, transparent 70%);
  top: 40%; left: 30%;
  animation-delay: 4s;
}

@keyframes glow-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(20px, -20px) scale(1.05); }
}

.floating-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 50%;
  animation: orbit 25s linear infinite;
}

.shape-1 { width: 300px; height: 300px; top: 10%; left: 5%; }
.shape-2 { width: 200px; height: 200px; top: 60%; left: 15%; animation-direction: reverse; }
.shape-3 { width: 150px; height: 150px; top: 30%; right: 10%; animation-duration: 30s; }

@keyframes orbit {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* === Container === */
.login-container {
  display: flex;
  width: 100%;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* === Brand Section === */
.login-brand {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 60px;
  color: white;
  max-width: 580px;
}

.brand-content {
  opacity: 0;
  transform: translateY(30px);
  animation: fadeUp 0.8s ease-out 0.2s forwards;
}

@keyframes fadeUp {
  to { opacity: 1; transform: translateY(0); }
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50px;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 32px;
}

.badge-dot {
  width: 8px;
  height: 8px;
  background: #10B981;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.brand-title {
  font-size: 52px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -2px;
  margin-bottom: 24px;
}

.gradient-text {
  background: linear-gradient(135deg, #818CF8 0%, #6366F1 50%, #4F46E5 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-desc {
  font-size: 17px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.6);
  max-width: 400px;
  margin-bottom: 48px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  opacity: 0;
  transform: translateX(-20px);
  animation: slideIn 0.5s ease-out forwards;
}

@keyframes slideIn {
  to { opacity: 1; transform: translateX(0); }
}

.feature-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 12px;
  flex-shrink: 0;
}

.feature-icon :deep(svg) {
  width: 20px;
  height: 20px;
  color: #818CF8;
}

.feature-text h4 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}

.feature-text p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.brand-footer {
  opacity: 0;
  animation: fadeUp 0.6s ease-out 0.8s forwards;
}

.brand-footer p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.brand-footer strong {
  color: white;
}

/* === Form Section === */
.login-form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: white;
}

.login-form-wrapper {
  width: 100%;
  max-width: 400px;
}

.mobile-brand {
  display: none;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
  justify-content: center;
}

.mobile-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

/* === Login Card === */
.login-card {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeUp 0.6s ease-out 0.3s forwards;
}

.card-header {
  margin-bottom: 32px;
  text-align: center;
}

.card-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.card-header p {
  font-size: 15px;
  color: #6B7280;
}

/* === Form === */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  width: 20px;
  height: 20px;
  color: #9CA3AF;
  transition: color 0.2s;
  pointer-events: none;
}

.input-icon svg {
  width: 100%;
  height: 100%;
}

.form-input {
  width: 100%;
  height: 52px;
  padding: 0 44px 0 48px;
  font-size: 15px;
  color: #1a1a2e;
  background: #F9FAFB;
  border: 2px solid transparent;
  border-radius: 14px;
  outline: none;
  transition: all 0.25s;
}

.form-input::placeholder {
  color: #9CA3AF;
}

.form-input:hover {
  background: #F3F4F6;
}

.form-input:focus {
  background: white;
  border-color: #6366F1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.form-group.is-focused .input-icon {
  color: #6366F1;
}

.form-group.has-error .form-input {
  border-color: #EF4444;
}

.input-check {
  position: absolute;
  right: 14px;
  width: 20px;
  height: 20px;
  color: #10B981;
}

.input-check svg {
  width: 100%;
  height: 100%;
}

.password-toggle {
  position: absolute;
  right: 12px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #9CA3AF;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.password-toggle:hover {
  background: #F3F4F6;
  color: #6B7280;
}

.password-toggle svg {
  width: 18px;
  height: 18px;
}

.error-text {
  display: block;
  font-size: 12px;
  color: #EF4444;
  margin-top: 6px;
}

/* === Options === */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-wrapper input {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #D1D5DB;
  border-radius: 6px;
  position: relative;
  transition: all 0.2s;
}

.checkbox-wrapper input:checked + .checkbox-custom {
  background: #6366F1;
  border-color: #6366F1;
}

.checkbox-custom::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 6px;
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) scale(0);
  transition: transform 0.2s;
}

.checkbox-wrapper input:checked + .checkbox-custom::after {
  transform: rotate(45deg) scale(1);
}

.checkbox-label {
  font-size: 14px;
  color: #6B7280;
}

.forgot-link {
  font-size: 14px;
  color: #6366F1;
  text-decoration: none;
  font-weight: 500;
}

.forgot-link:hover {
  color: #4F46E5;
}

/* === Submit Button === */
.submit-btn {
  height: 52px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.submit-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #818CF8 0%, #6366F1 100%);
  opacity: 0;
  transition: opacity 0.3s;
}

.submit-btn:hover::before {
  opacity: 1;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

.submit-btn:active {
  transform: translateY(0);
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-text, .btn-icon {
  position: relative;
  z-index: 1;
}

.btn-icon svg {
  width: 18px;
  height: 18px;
  transition: transform 0.3s;
}

.submit-btn:hover .btn-icon svg {
  transform: translateX(4px);
}

.btn-loader {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  position: relative;
  z-index: 1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* === Quick Login === */
.quick-login {
  margin-top: 32px;
}

.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #E5E7EB;
}

.divider span {
  font-size: 12px;
  color: #9CA3AF;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.demo-accounts {
  display: flex;
  gap: 10px;
}

.demo-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.demo-btn:hover {
  background: white;
  border-color: #D1D5DB;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.demo-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
  border-radius: 10px;
  flex-shrink: 0;
}

.demo-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.demo-role {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.demo-user {
  font-size: 11px;
  color: #9CA3AF;
}

/* === Footer === */
.login-footer {
  margin-top: 40px;
  text-align: center;
  opacity: 0;
  animation: fadeUp 0.6s ease-out 0.6s forwards;
}

.login-footer p {
  font-size: 12px;
  color: #9CA3AF;
}

/* === Responsive === */
@media (max-width: 1024px) {
  .login-brand {
    display: none;
  }
  
  .mobile-brand {
    display: flex;
  }
}

@media (max-width: 640px) {
  .login-page {
    background: white;
  }
  
  .login-bg {
    display: none;
  }
  
  .login-form-section {
    padding: 24px;
  }
  
  .card-header h2 {
    font-size: 24px;
  }
  
  .demo-accounts {
    flex-direction: column;
  }
  
  .form-input {
    height: 50px;
    font-size: 16px;
  }
  
  .submit-btn {
    height: 50px;
  }
}
</style>
