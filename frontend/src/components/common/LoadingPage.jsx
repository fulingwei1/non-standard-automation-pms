import { LoadingSpinner } from './LoadingSpinner'

export default function LoadingPage({ message = '加载中...' }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
      <LoadingSpinner size="xl" text={message} />
    </div>
  )
}


