import { useState } from "react";
import { Check } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { cn } from "../../lib/utils";

const languages = [
  { id: "zh-CN", label: "简体中文", flag: "🇨🇳" },
  { id: "zh-TW", label: "繁體中文", flag: "🇹🇼" },
  { id: "en-US", label: "English", flag: "🇺🇸" },
];

export default function LanguageSection() {
  const [language, setLanguage] = useState("zh-CN");
  const [timezone, setTimezone] = useState("Asia/Shanghai");
  const [dateFormat, setDateFormat] = useState("YYYY-MM-DD");

  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <CardTitle>语言与区域</CardTitle>
        <CardDescription>设置您的语言和时区偏好</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Language */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-slate-300">界面语言</label>
          <div className="grid grid-cols-3 gap-3">
            {(languages || []).map((lang) => (
              <button
                key={lang.id}
                onClick={() => setLanguage(lang.id)}
                className={cn(
                  "p-3 rounded-lg border transition-all flex items-center gap-2",
                  language === lang.id
                    ? "border-accent bg-accent/10"
                    : "border-border bg-surface-2/50 hover:border-border/80",
                )}
              >
                <span className="text-xl">{lang.flag}</span>
                <span
                  className={cn(
                    "text-sm",
                    language === lang.id ? "text-accent" : "text-slate-400",
                  )}
                >
                  {lang.label}
                </span>
                {language === lang.id && (
                  <Check className="w-4 h-4 ml-auto text-accent" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Timezone */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">时区</label>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="w-full h-10 px-3 rounded-lg bg-surface-2 border border-border text-white focus:border-accent focus:outline-none"
          >
            <option value="Asia/Shanghai">中国标准时间 (UTC+8)</option>
            <option value="Asia/Hong_Kong">香港时间 (UTC+8)</option>
            <option value="Asia/Tokyo">日本标准时间 (UTC+9)</option>
            <option value="America/New_York">美国东部时间 (UTC-5)</option>
            <option value="Europe/London">格林威治时间 (UTC+0)</option>
          </select>
        </div>

        {/* Date Format */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">日期格式</label>
          <select
            value={dateFormat}
            onChange={(e) => setDateFormat(e.target.value)}
            className="w-full h-10 px-3 rounded-lg bg-surface-2 border border-border text-white focus:border-accent focus:outline-none"
          >
            <option value="YYYY-MM-DD">2026-01-04</option>
            <option value="DD/MM/YYYY">04/01/2026</option>
            <option value="MM/DD/YYYY">01/04/2026</option>
            <option value="YYYY年MM月DD日">2026年01月04日</option>
          </select>
        </div>
      </CardContent>
    </Card>
  );
}
