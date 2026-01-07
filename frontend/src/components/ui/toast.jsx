import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle2, AlertCircle, Info, XCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

const toastTypes = {
  success: { icon: CheckCircle2, borderColor: 'border-emerald-500/30', iconColor: 'text-emerald-400' },
  error: { icon: XCircle, borderColor: 'border-red-500/30', iconColor: 'text-red-400' },
  warning: { icon: AlertCircle, borderColor: 'border-amber-500/30', iconColor: 'text-amber-400' },
  info: { icon: Info, borderColor: 'border-blue-500/30', iconColor: 'text-blue-400' },
}

export function Toast({ id, message, type = 'info', duration = 3000, onClose }) {
  const [isVisible, setIsVisible] = useState(true)
  const config = toastTypes[type] || toastTypes.info
  const Icon = config.icon

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false)
        setTimeout(() => onClose?.(id), 300)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [duration, id, onClose])

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          className={cn(
            'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg',
            'bg-slate-800 border',
            config.borderColor,
            'min-w-[300px] max-w-md'
          )}
        >
          <Icon className={cn('w-5 h-5 flex-shrink-0', config.iconColor)} />
          <p className="flex-1 text-sm text-white">{message}</p>
          <button
            onClick={() => {
              setIsVisible(false)
              setTimeout(() => onClose?.(id), 300)
            }}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export function ToastContainer({ toasts, onClose }) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} onClose={onClose} />
        ))}
      </AnimatePresence>
    </div>
  )
}

// Toast hook
let toastId = 0
const toastListeners = new Set()

// eslint-disable-next-line react-refresh/only-export-components
export const toast = {
  success: (message, duration) => showToast('success', message, duration),
  error: (message, duration) => showToast('error', message, duration),
  warning: (message, duration) => showToast('warning', message, duration),
  info: (message, duration) => showToast('info', message, duration),
}

function showToast(type, message, duration = 3000) {
  const id = ++toastId
  const toast = { id, type, message, duration }
  toastListeners.forEach((listener) => listener(toast))
  return id
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    const listener = (toast) => {
      setToasts((prev) => [...prev, toast])
    }
    toastListeners.add(listener)
    return () => {
      toastListeners.delete(listener)
    }
  }, [])

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return { toasts, removeToast }
}

