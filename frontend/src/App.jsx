import { useState, useEffect, Suspense } from 'react'
import { BrowserRouter as Router } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { cn } from './lib/utils'
import ErrorBoundary from './components/common/ErrorBoundary'

// Layout Components
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'

// Pages
import Login from './pages/Login'

// Routes
import AppRoutes from './routes'

// Loading fallback
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
  </div>
)

// Main Layout
function MainLayout({ children, onLogout }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [user, setUser] = useState(() => {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        return JSON.parse(userStr)
      }
    } catch {
      // ignore
    }
    return null
  })

  useEffect(() => {
    const handleStorageChange = () => {
      try {
        const userStr = localStorage.getItem('user')
        if (userStr) {
          setUser(JSON.parse(userStr))
        } else {
          setUser(null)
        }
      } catch {
        setUser(null)
      }
    }

    window.addEventListener('storage', handleStorageChange)
    handleStorageChange()

    return () => {
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [])

  return (
    <div className="min-h-screen bg-surface-0">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onLogout={onLogout}
      />

      <Header
        sidebarCollapsed={sidebarCollapsed}
        user={user}
        onLogout={onLogout}
      />

      <main
        className={cn(
          'pt-16 min-h-screen transition-all duration-300',
          sidebarCollapsed ? 'pl-[72px]' : 'pl-60'
        )}
      >
        <div className="p-6">
          <AnimatePresence mode="wait">
            <Suspense fallback={<LoadingFallback />}>
              {children}
            </Suspense>
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  )

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('token')
      setIsAuthenticated(!!token)
    }

    checkAuth()
    window.addEventListener('storage', checkAuth)
    const interval = setInterval(checkAuth, 1000)

    return () => {
      window.removeEventListener('storage', checkAuth)
      clearInterval(interval)
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setIsAuthenticated(false)
    window.location.href = '/'
  }

  const handleLoginSuccess = () => {
    setIsAuthenticated(true)
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <ErrorBoundary>
      <Router>
        <MainLayout onLogout={handleLogout}>
          <AppRoutes />
        </MainLayout>
      </Router>
    </ErrorBoundary>
  )
}

export default App
