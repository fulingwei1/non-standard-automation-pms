/**
 * 用户表单对话框（创建/编辑复用）
 */

import { AnimatePresence, motion } from "framer-motion";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogBody, DialogFooter,
} from "../../../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../../../components/ui/select";
import {
  USER_STATUS, USER_STATUS_LABELS,
  USER_ROLE, USER_ROLE_LABELS,
  USER_DEPARTMENT, USER_DEPARTMENT_LABELS,
} from "../../../components/user-management";

export function UserFormDialog({
  open, onOpenChange,
  title,
  userData, setUserData,
  onSubmit, submitLabel,
  showPassword = false,
}) {
  const update = (field) => (e) =>
    setUserData({ ...userData, [field]: e.target.value });
  const updateSelect = (field) => (value) =>
    setUserData({ ...userData, [field]: value });

  return (
    <AnimatePresence>
      {open && (
        <Dialog open={open} onOpenChange={onOpenChange}>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>{title}</DialogTitle>
              </DialogHeader>
              <DialogBody>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>用户名</Label>
                    <Input value={userData.username} onChange={update("username")} />
                  </div>
                  <div>
                    <Label>邮箱</Label>
                    <Input type="email" value={userData.email} onChange={update("email")} />
                  </div>
                  {showPassword && (
                    <div>
                      <Label>密码</Label>
                      <Input type="password" value={userData.password} onChange={update("password")} />
                    </div>
                  )}
                  <div>
                    <Label>姓名</Label>
                    <Input value={userData.full_name} onChange={update("full_name")} />
                  </div>
                  <div>
                    <Label>电话</Label>
                    <Input value={userData.phone} onChange={update("phone")} />
                  </div>
                  <div>
                    <Label>角色</Label>
                    <Select value={userData.role} onValueChange={updateSelect("role")}>
                      <SelectTrigger><SelectValue placeholder="选择角色" /></SelectTrigger>
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
                    <Label>部门</Label>
                    <Select value={userData.department} onValueChange={updateSelect("department")}>
                      <SelectTrigger><SelectValue placeholder="选择部门" /></SelectTrigger>
                      <SelectContent>
                        {Object.entries(USER_DEPARTMENT).map(([_key, value]) => (
                          <SelectItem key={value} value={value || "unknown"}>
                            {USER_DEPARTMENT_LABELS[value]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>状态</Label>
                    <Select value={userData.status} onValueChange={updateSelect("status")}>
                      <SelectTrigger><SelectValue placeholder="选择状态" /></SelectTrigger>
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
                <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
                <Button onClick={onSubmit}>{submitLabel}</Button>
              </DialogFooter>
            </DialogContent>
          </motion.div>
        </Dialog>
      )}
    </AnimatePresence>
  );
}
