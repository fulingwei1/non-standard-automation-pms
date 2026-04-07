import { useState } from "react";





export default function ProfileSection() {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    const defaultUser = {
      name: "用户",
      id: "-",
      email: "",
      phone: "",
      department: "未知部门",
      role: "用户",
    };
    if (!stored) {return defaultUser;}
    try {
      const parsed = JSON.parse(stored);
      return { ...defaultUser, ...parsed };
    } catch {
      return defaultUser;
    }
  });
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="space-y-6">
      {/* Avatar Section */}
      <Card className="bg-surface-1/50">
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <div className="relative group">
              <Avatar className="w-24 h-24">
                <AvatarImage src={user.avatar} />
                <AvatarFallback className="text-2xl bg-gradient-to-br from-accent to-purple-500">
                  {user.name?.[0] || "U"}
                </AvatarFallback>
              </Avatar>
              <button className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera className="w-6 h-6 text-white" />
              </button>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white">{user.name}</h3>
              <p className="text-slate-400">
                {user.department} · {user.role}
              </p>
              <p className="text-sm text-slate-500 mt-1">工号：{user.id}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Basic Info */}
      <Card className="bg-surface-1/50">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>基本信息</CardTitle>
            <CardDescription>管理您的个人资料信息</CardDescription>
          </div>
          <Button
            variant={isEditing ? "default" : "outline"}
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? (
              <>
                <Save className="w-4 h-4 mr-1" />
                保存
              </>
            ) : (
              "编辑"
            )}
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">姓名</label>
              <Input
                value={user.name}
                onChange={(e) => setUser({ ...user, name: e.target.value })}
                disabled={!isEditing}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">工号</label>
              <Input value={user.id} disabled />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">邮箱</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  value={user.email}
                  onChange={(e) => setUser({ ...user, email: e.target.value })}
                  disabled={!isEditing}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">手机</label>
              <div className="relative">
                <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  value={user.phone}
                  onChange={(e) => setUser({ ...user, phone: e.target.value })}
                  disabled={!isEditing}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">部门</label>
              <Input value={user.department} disabled />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">角色</label>
              <Input value={user.role} disabled />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
