/**
 * 权限调试页面
 * 用于检查当前用户的角色和权限状态
 */

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui";
import { hasFinanceAccess } from "../lib/roleConfig";

export default function PermissionDebug() {
  const userStr = localStorage.getItem("user");

  const userInfo = useMemo(() => {
    if (!userStr) {
      return { error: "未找到用户信息" };
    }

    try {
      const user = JSON.parse(userStr);
      return {
        user,
        role: user.role,
        isSuperuser: user.is_superuser === true || user.isSuperuser === true,
        hasFinance: hasFinanceAccess(user.role, user.is_superuser),
      };
    } catch (e) {
      return { error: `解析用户信息失败: ${e.message}` };
    }
  }, [userStr]);

  if (userInfo.error) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>权限调试</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-400">{userInfo.error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>当前用户信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <span className="text-slate-400">用户名: </span>
            <span className="text-white">
              {userInfo.user.username || userInfo.user.name}
            </span>
          </div>
          <div>
            <span className="text-slate-400">角色代码: </span>
            <span className="text-white font-mono">
              {userInfo.role || "未设置"}
            </span>
          </div>
          <div>
            <span className="text-slate-400">是否超级管理员: </span>
            <span
              className={
                userInfo.isSuperuser ? "text-green-400" : "text-red-400"
              }
            >
              {userInfo.isSuperuser ? "是" : "否"}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>权限检查结果</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <span className="text-slate-400">财务模块权限: </span>
            <span
              className={
                userInfo.hasFinance ? "text-green-400" : "text-red-400"
              }
            >
              {userInfo.hasFinance ? "✅ 有权限" : "❌ 无权限"}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>原始用户数据</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="text-xs text-slate-400 bg-slate-900 p-4 rounded overflow-auto">
            {JSON.stringify(userInfo.user, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>权限检查函数</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-400 space-y-1">
            <div>
              hasFinanceAccess('{userInfo.role}', {String(userInfo.isSuperuser)}
              )
            </div>
            <div className="text-white">= {String(userInfo.hasFinance)}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
