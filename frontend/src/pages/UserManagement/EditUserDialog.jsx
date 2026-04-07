



import {
  USER_STATUS,
  USER_STATUS_LABELS,
  USER_ROLE,
  USER_ROLE_LABELS,
  USER_DEPARTMENT,
  USER_DEPARTMENT_LABELS,
} from "../../components/user-management";

export default function EditUserDialog({
  open,
  onOpenChange,
  selectedUser,
  setSelectedUser,
  onUpdateUser,
}) {
  if (!open || !selectedUser) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>编辑用户</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-username">用户名</Label>
                <Input
                  id="edit-username"
                  value={selectedUser.username}
                  onChange={(e) =>
                    setSelectedUser({
                      ...selectedUser,
                      username: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-email">邮箱</Label>
                <Input
                  id="edit-email"
                  type="email"
                  value={selectedUser.email}
                  onChange={(e) =>
                    setSelectedUser({
                      ...selectedUser,
                      email: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-full_name">姓名</Label>
                <Input
                  id="edit-full_name"
                  value={selectedUser.full_name}
                  onChange={(e) =>
                    setSelectedUser({
                      ...selectedUser,
                      full_name: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-phone">电话</Label>
                <Input
                  id="edit-phone"
                  value={selectedUser.phone}
                  onChange={(e) =>
                    setSelectedUser({
                      ...selectedUser,
                      phone: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-role">角色</Label>
                <Select
                  value={selectedUser.role}
                  onValueChange={(value) =>
                    setSelectedUser({ ...selectedUser, role: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择角色" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(USER_ROLE).map(([_key, value]) => (
                      <SelectItem key={value} value={value || "unknown"}>
                        {USER_ROLE_LABELS[value]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="edit-department">部门</Label>
                <Select
                  value={selectedUser.department}
                  onValueChange={(value) =>
                    setSelectedUser({
                      ...selectedUser,
                      department: value,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择部门" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(USER_DEPARTMENT).map(
                      ([_key, value]) => (
                        <SelectItem key={value} value={value || "unknown"}>
                          {USER_DEPARTMENT_LABELS[value]}
                        </SelectItem>
                      ),
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="edit-status">状态</Label>
                <Select
                  value={selectedUser.status}
                  onValueChange={(value) =>
                    setSelectedUser({ ...selectedUser, status: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择状态" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(USER_STATUS).map(([_key, value]) => (
                      <SelectItem key={value} value={value || "unknown"}>
                        {USER_STATUS_LABELS[value]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <Button onClick={onUpdateUser}>更新</Button>
          </DialogFooter>
        </DialogContent>
      </motion.div>
    </Dialog>
  );
}
