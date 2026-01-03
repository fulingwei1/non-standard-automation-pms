import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Briefcase,
  Users,
  Settings,
  LogOut,
  Bell,
  Search,
  Plus,
  Box,
  FileText,
  DollarSign
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import Login from './pages/Login'

// Placeholder Pages
const Dashboard = () => (
  <div className="animate-fade">
    <div className="header">
      <div>
        <h1 className="text-gradient" style={{ fontSize: '2rem', fontWeight: 700 }}>项目概览</h1>
        <p style={{ color: 'var(--text-dim)', marginTop: '4px' }}>欢迎回来，这是您的系统实时摘要</p>
      </div>
      <div style={{ display: 'flex', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Search size={18} color="var(--text-dim)" />
          <input
            type="text"
            placeholder="搜索项目..."
            style={{ background: 'none', border: 'none', outline: 'none', color: 'white' }}
          />
        </div>
        <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Plus size={18} /> 新建项目
        </button>
      </div>
    </div>

    <div className="stats-grid">
      {[
        { label: '执行中项目', value: '12', icon: Briefcase, color: 'var(--primary-color)' },
        { label: '总预算', value: '¥2.4M', icon: DollarSign, color: 'var(--accent-color)' },
        { label: '活跃团队', value: '8', icon: Users, color: 'var(--secondary-color)' },
        { label: '待处理异常', value: '3', icon: Bell, color: '#f43f5e' }
      ].map((stat, i) => (
        <div key={i} className="glass-card stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ padding: '10px', background: `${stat.color}20`, borderRadius: '12px' }}>
              <stat.icon size={24} color={stat.color} />
            </div>
          </div>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem' }}>{stat.label}</p>
          <h2 style={{ fontSize: '1.8rem', marginTop: '8px' }}>{stat.value}</h2>
        </div>
      ))}
    </div>

    <h2 style={{ marginBottom: '24px', fontSize: '1.4rem' }}>最近更新</h2>
    <div className="project-grid">
      {[1, 2, 3].map(i => (
        <div key={i} className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <span style={{ fontSize: '0.8rem', padding: '4px 10px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary-color)', borderRadius: '20px', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
              设计阶段
            </span>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>H1 状态正常</span>
          </div>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>上海某汽车厂非标自动化线</h3>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', marginBottom: '20px' }}>客户: 特斯拉 (Tesla Shanghai)</p>
          <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px', overflow: 'hidden', marginBottom: '8px' }}>
            <div style={{ width: '65%', height: '100%', background: 'linear-gradient(to right, var(--primary-color), var(--secondary-color))' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            <span>进度: 65%</span>
            <span>交付: 2026-03-20</span>
          </div>
        </div>
      ))}
    </div>
  </div>
)

const Layout = ({ children, onLogout }) => {
  const location = useLocation()

  const navItems = [
    { name: '仪表盘', path: '/', icon: LayoutDashboard },
    { name: '项目管理', path: '/projects', icon: Briefcase },
    { name: '设备列表', path: '/machines', icon: Box },
    { name: '组织架构', path: '/org', icon: Users },
    { name: '文件中心', path: '/docs', icon: FileText },
    { name: '设置', path: '/settings', icon: Settings },
  ]

  return (
    <div>
      <div className="glass-panel sidebar" style={{ borderRadius: '0 24px 24px 0', borderLeft: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px' }}>
          <div style={{ width: '32px', height: '32px', background: 'var(--primary-color)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Box color="white" size={20} />
          </div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>PMS 系统</h2>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <item.icon size={20} />
              <span>{item.name}</span>
            </Link>
          ))}
        </nav>

        <div style={{ marginTop: 'auto' }}>
          <div className="nav-item" style={{ cursor: 'pointer' }} onClick={onLogout}>
            <LogOut size={20} />
            <span>注销退出</span>
          </div>
        </div>
      </div>

      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'))

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />
  }

  return (
    <Router>
      <Layout onLogout={() => {
        localStorage.removeItem('token')
        setIsAuthenticated(false)
      }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/machines" element={<div className="animate-fade"><h1>设备列表</h1><p>功能开发中...</p></div>} />
          <Route path="/org" element={<div className="animate-fade"><h1>组织架构</h1><p>功能开发中...</p></div>} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
