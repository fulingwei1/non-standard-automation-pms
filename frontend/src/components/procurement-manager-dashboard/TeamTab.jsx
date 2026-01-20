import { Card, CardContent } from "../../components/ui";

export default function TeamTab() {
  return (
    <div className="grid grid-cols-1 gap-4">
      {/* 团队成员 - 需要从API获取数据 */}
      <div className="text-center py-8 text-slate-500">
        <p>团队成员数据需要从API获取</p>
      </div>
    </div>
  );
}
