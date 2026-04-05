import { useState } from "react";
import { Sun, Moon, Monitor, Check } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { cn } from "../../lib/utils";

const themes = [
  { id: "light", label: "浅色", icon: Sun },
  { id: "dark", label: "深色", icon: Moon },
  { id: "system", label: "跟随系统", icon: Monitor },
];

const accentColors = [
  "#6366f1", // Indigo
  "#8b5cf6", // Purple
  "#ec4899", // Pink
  "#f43f5e", // Rose
  "#f97316", // Orange
  "#eab308", // Yellow
  "#22c55e", // Green
  "#06b6d4", // Cyan
  "#3b82f6", // Blue
];

export default function AppearanceSection() {
  const [theme, setTheme] = useState("dark");
  const [accentColor, setAccentColor] = useState("#6366f1");

  return (
    <div className="space-y-6">
      {/* Theme Selection */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle>主题模式</CardTitle>
          <CardDescription>选择您喜欢的界面主题</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {(themes || []).map((t) => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id)}
                className={cn(
                  "p-4 rounded-xl border-2 transition-all",
                  theme === t.id
                    ? "border-accent bg-accent/10"
                    : "border-border bg-surface-2/50 hover:border-border/80",
                )}
              >
                <t.icon
                  className={cn(
                    "w-8 h-8 mx-auto mb-2",
                    theme === t.id ? "text-accent" : "text-slate-400",
                  )}
                 />
                <div
                  className={cn(
                    "text-sm font-medium",
                    theme === t.id ? "text-accent" : "text-slate-400",
                  )}
                >
                  {t.label}
                </div>
                {theme === t.id && (
                  <div className="mt-2">
                    <Check className="w-4 h-4 mx-auto text-accent" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Accent Color */}
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle>主题色</CardTitle>
          <CardDescription>选择系统的强调色</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {(accentColors || []).map((color) => (
              <button
                key={color}
                onClick={() => setAccentColor(color)}
                className={cn(
                  "w-10 h-10 rounded-full border-2 transition-transform hover:scale-110",
                  accentColor === color
                    ? "border-white scale-110"
                    : "border-transparent",
                )}
                style={{ backgroundColor: color }}
              >
                {accentColor === color && (
                  <Check className="w-5 h-5 mx-auto text-white" />
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
