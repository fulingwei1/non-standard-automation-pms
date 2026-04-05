import { useState } from "react";
import { Bell, Mail, Smartphone } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { cn } from "../../lib/utils";

const notificationTypes = [
  { key: "taskAssigned", label: "任务分配", desc: "当有新任务分配给您时" },
  { key: "taskDue", label: "任务到期", desc: "当任务即将到期或已逾期时" },
  {
    key: "projectUpdate",
    label: "项目更新",
    desc: "当您参与的项目有重要更新时",
  },
  {
    key: "systemNotice",
    label: "系统通知",
    desc: "系统维护、功能更新等通知",
  },
];

const channels = [
  { key: "email", label: "邮件", icon: Mail },
  { key: "push", label: "站内", icon: Bell },
  { key: "wechat", label: "企微", icon: Smartphone },
];

export default function NotificationsSection() {
  const [settings, setSettings] = useState({
    email: {
      taskAssigned: true,
      taskDue: true,
      projectUpdate: true,
      systemNotice: false,
    },
    push: {
      taskAssigned: true,
      taskDue: true,
      projectUpdate: false,
      systemNotice: false,
    },
    wechat: {
      taskAssigned: true,
      taskDue: true,
      projectUpdate: true,
      systemNotice: true,
    },
  });

  const toggleSetting = (channel, type) => {
    setSettings({
      ...settings,
      [channel]: {
        ...settings[channel],
        [type]: !settings[channel][type],
      },
    });
  };

  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <CardTitle>通知偏好</CardTitle>
        <CardDescription>选择您希望接收通知的方式</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-3 text-sm font-medium text-slate-400">
                  通知类型
                </th>
                {(channels || []).map((channel) => (
                  <th
                    key={channel.key}
                    className="text-center p-3 text-sm font-medium text-slate-400"
                  >
                    <div className="flex items-center justify-center gap-1">
                      <channel.icon className="w-4 h-4"  />
                      {channel.label}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(notificationTypes || []).map((type) => (
                <tr key={type.key} className="border-b border-border/50">
                  <td className="p-3">
                    <div>
                      <div className="font-medium text-white text-sm">
                        {type.label}
                      </div>
                      <div className="text-xs text-slate-500">{type.desc}</div>
                    </div>
                  </td>
                  {(channels || []).map((channel) => (
                    <td key={channel.key} className="p-3 text-center">
                      <button
                        onClick={() => toggleSetting(channel.key, type.key)}
                        className={cn(
                          "w-10 h-6 rounded-full relative transition-colors",
                          settings[channel.key][type.key]
                            ? "bg-accent"
                            : "bg-surface-2",
                        )}
                      >
                        <span
                          className={cn(
                            "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                            settings[channel.key][type.key]
                              ? "translate-x-5"
                              : "translate-x-1",
                          )}
                        />
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
