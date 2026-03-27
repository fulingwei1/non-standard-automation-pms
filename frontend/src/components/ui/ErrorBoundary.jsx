import React from "react";
import { AlertTriangle, RefreshCw, Home, Lightbulb } from "lucide-react";
import { Button } from "./button";
import { Card, CardContent } from "./card";

const isDev = import.meta.env.DEV;

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleReset);
      }

      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full">
            <CardContent className="p-8">
              <div className="text-center space-y-4">
                <div className="flex justify-center">
                  <div className="w-16 h-16 rounded-full bg-amber-500/10 flex items-center justify-center">
                    <AlertTriangle className="w-8 h-8 text-amber-400" />
                  </div>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">
                    页面出了点问题
                  </h2>
                  <p className="text-slate-400 mb-4">
                    很抱歉，当前页面遇到了一些意外情况，无法正常显示。
                  </p>
                </div>

                <div className="flex items-start gap-2 mx-auto max-w-md p-4 rounded-lg bg-white/[0.03] border border-white/5 text-left">
                  <Lightbulb className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-slate-300 space-y-1">
                    <p>您可以尝试：</p>
                    <ul className="list-disc list-inside text-slate-400 space-y-1">
                      <li>点击"重试"刷新当前页面</li>
                      <li>返回首页后重新进入</li>
                      <li>如果问题持续出现，请联系管理员</li>
                    </ul>
                  </div>
                </div>

                {isDev && this.state.error && (
                  <div className="mt-4 p-4 bg-slate-800/50 rounded-lg text-left">
                    <p className="text-sm text-red-400 font-mono mb-2">
                      {this.state.error.toString()}
                    </p>
                    {this.state.errorInfo && (
                      <details className="text-xs text-slate-500">
                        <summary className="cursor-pointer mb-2">
                          开发者调试信息
                        </summary>
                        <pre className="overflow-auto max-h-40">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </details>
                    )}
                  </div>
                )}
                <div className="flex gap-3 justify-center">
                  <Button onClick={this.handleReset} className="gap-2">
                    <RefreshCw className="w-4 h-4" />
                    重试
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => (window.location.href = "/")}
                    className="gap-2"
                  >
                    <Home className="w-4 h-4" />
                    返回首页
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
