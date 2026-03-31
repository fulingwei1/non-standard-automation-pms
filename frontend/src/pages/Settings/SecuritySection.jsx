import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Key,
  Eye,
  EyeOff,
  Monitor,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { authApi } from "../../services/api";

export default function SecuritySection() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [passwords, setPasswords] = useState({
    current: "",
    new: "",
    confirm: "",
  });

  const handleChangePassword = async () => {
    // 重置状态
    setError("");
    setSuccess("");

    // 表单验证
    if (!passwords.current) {
      setError("请输入当前密码");
      return;
    }

    if (!passwords.new) {
      setError("请输入新密码");
      return;
    }

    if (passwords.new?.length < 6) {
      setError("新密码长度至少6位");
      return;
    }

    if (passwords.new !== passwords.confirm) {
      setError("两次输入的新密码不一致");
      return;
    }

    if (passwords.current === passwords.new) {
      setError("新密码不能与当前密码相同");
      return;
    }

    setLoading(true);

    try {
      const response = await authApi.changePassword({
        old_password: passwords.current,
        new_password: passwords.new,
      });

      if (response.code === 200) {
        setSuccess(response.message || "密码修改成功，请重新登录");
        // 清空表单
        setPasswords({
          current: "",
          new: "",
          confirm: "",
        });
        // 3秒后跳转到登录页
        setTimeout(() => {
          navigate("/login");
        }, 3000);
      } else {
        setError(response.message || "密码修改失败");
      }
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "密码修改失败，请稍后重试";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Change Password */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            修改密码
          </CardTitle>
          <CardDescription>定期更换密码可以提高账户安全性</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm">
              {success}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              当前密码
            </label>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                value={passwords.current}
                onChange={(e) =>
                  setPasswords({ ...passwords, current: e.target.value })
                }
                placeholder="请输入当前密码"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">新密码</label>
            <Input
              type={showPassword ? "text" : "password"}
              value={passwords.new}
              onChange={(e) =>
                setPasswords({ ...passwords, new: e.target.value })
              }
              placeholder="请输入新密码（至少6位）"
              disabled={loading}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              确认新密码
            </label>
            <Input
              type={showPassword ? "text" : "password"}
              value={passwords.confirm}
              onChange={(e) =>
                setPasswords({ ...passwords, confirm: e.target.value })
              }
              placeholder="请再次输入新密码"
              disabled={loading}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  handleChangePassword();
                }
              }}
            />
          </div>
          <Button onClick={handleChangePassword} disabled={loading}>
            {loading ? "修改中..." : "更新密码"}
          </Button>
        </CardContent>
      </Card>

      {/* Login Sessions */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle>登录设备</CardTitle>
          <CardDescription>管理您的登录会话</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            {
              device: "Chrome on Windows",
              location: "深圳市",
              time: "当前会话",
              current: true,
            },
            {
              device: "企业微信",
              location: "深圳市",
              time: "2天前",
              current: false,
            },
          ].map((session, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 rounded-lg bg-surface-2/50"
            >
              <div className="flex items-center gap-3">
                <Monitor className="w-5 h-5 text-slate-400" />
                <div>
                  <div className="font-medium text-white text-sm">
                    {session.device}
                  </div>
                  <div className="text-xs text-slate-500">
                    {session.location} · {session.time}
                  </div>
                </div>
              </div>
              {session.current ? (
                <Badge variant="success">当前</Badge>
              ) : (
                <Button variant="ghost" size="sm" className="text-red-400">
                  登出
                </Button>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
