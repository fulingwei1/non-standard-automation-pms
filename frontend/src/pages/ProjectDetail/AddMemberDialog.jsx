


export default function AddMemberDialog({
  open,
  onOpenChange,
  availableUsers,
  loadingUsers,
  newMember,
  setNewMember,
  addingMember,
  onAdd,
}) {
  return (
    <AnimatePresence>
      {open && (
        <Dialog open={open} onOpenChange={onOpenChange}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>添加项目成员</DialogTitle>
              <DialogDescription>为项目添加团队成员</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">选择成员</label>
                <select
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  value={newMember.user_id}
                  onChange={(e) => setNewMember({ ...newMember, user_id: e.target.value })}
                  disabled={loadingUsers}
                >
                  <option value="">-- 选择用户 --</option>
                  {(availableUsers || []).map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.real_name || user.username} ({user.username})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">角色</label>
                <select
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  value={newMember.role}
                  onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                >
                  <option value="member">成员</option>
                  <option value="lead">负责人</option>
                </select>
              </div>

              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  取消
                </Button>
                <Button
                  onClick={onAdd}
                  disabled={loadingUsers || addingMember || !newMember.user_id}
                >
                  {addingMember ? "添加中..." : "添加"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </AnimatePresence>
  );
}
