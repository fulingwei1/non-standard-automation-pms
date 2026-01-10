import React from "react";
import { AlertCircle, RefreshCw, Home } from "lucide-react";
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
                  <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
                    <AlertCircle className="w-8 h-8 text-red-400" />
                  </div>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">
                    出现错误
                  </h2>
                  <p className="text-slate-400 mb-4">
                    {this.props.message || "页面加载时发生错误，请刷新页面重试"}
                  </p>
                </div>
                {isDev && this.state.error && (
                  <div className="mt-4 p-4 bg-slate-800/50 rounded-lg text-left">
                    <p className="text-sm text-red-400 font-mono mb-2">
                      {this.state.error.toString()}
                    </p>
                    {this.state.errorInfo && (
                      <details className="text-xs text-slate-500">
                        <summary className="cursor-pointer mb-2">
                          错误堆栈
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
