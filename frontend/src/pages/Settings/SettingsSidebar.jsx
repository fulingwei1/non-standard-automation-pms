import {
  User,
  Bell,
  Shield,
  Palette,
  Globe,
} from "lucide-react";


import { cn } from "../../lib/utils";

export const settingsSections = [
  { id: "profile", label: "个人资料", icon: User },
  { id: "notifications", label: "通知设置", icon: Bell },
  { id: "security", label: "安全设置", icon: Shield },
  { id: "appearance", label: "外观主题", icon: Palette },
  { id: "language", label: "语言区域", icon: Globe },
];

export default function SettingsSidebar({ activeSection, onSectionChange }) {
  return (
    <Card className="bg-surface-1/50 lg:w-64 shrink-0">
      <CardContent className="p-2">
        <nav className="space-y-1">
          {(settingsSections || []).map((section) => (
            <button
              key={section.id}
              onClick={() => onSectionChange(section.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left",
                activeSection === section.id
                  ? "bg-accent/10 text-accent"
                  : "text-slate-400 hover:text-white hover:bg-surface-2",
              )}
            >
              <section.icon className="w-5 h-5"  />
              <span className="font-medium">{section.label}</span>
            </button>
          ))}
        </nav>
      </CardContent>
    </Card>
  );
}
