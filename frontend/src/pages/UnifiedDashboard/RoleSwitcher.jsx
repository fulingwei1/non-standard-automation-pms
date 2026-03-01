/**
 * 角色切换器组件 (Role Switcher)
 *
 * 当用户拥有多个角色时，显示下拉框供用户切换角色视图
 * 单角色用户不显示此组件
 */

import { useMemo } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { Badge } from '../../components/ui/badge';
import { User, ChevronDown } from 'lucide-react';

/**
 * 角色切换器
 *
 * @param {Object} props
 * @param {Array} props.roles - 用户角色列表 [{ role_code, role_name }]
 * @param {string} props.currentRole - 当前选中的角色编码
 * @param {function} props.onChange - 角色变更回调
 * @param {string} props.className - 额外样式类
 */
export function RoleSwitcher({
  roles = [],
  currentRole,
  onChange,
  className = '',
}) {
  const currentRoleName = useMemo(() => {
    const role = (roles || []).find(r => r.role_code === currentRole);
    return role?.role_name || '选择角色视图';
  }, [roles, currentRole]);

  // 单角色或无角色时不显示切换器
  if (!roles || roles.length <= 1) {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Badge variant="outline" className="gap-1 px-2 py-1">
        <User className="h-3 w-3" />
        <span className="text-xs">视图</span>
      </Badge>

      <Select value={currentRole || "unknown"} onValueChange={onChange}>
        <SelectTrigger className="w-48 h-9">
          <SelectValue placeholder="选择角色视图">
            {currentRoleName}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          {(roles || []).map((role) => (
            <SelectItem
              key={role.role_code}
              value={role.role_code}
              className="cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <span>{role.role_name}</span>
                {role.is_primary && (
                  <Badge variant="secondary" className="text-xs px-1 py-0">
                    主
                  </Badge>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

/**
 * 简化版角色切换器（用于狭窄空间）
 */
export function RoleSwitcherCompact({
  roles = [],
  currentRole,
  onChange,
  className = '',
}) {
  const currentRoleName = useMemo(() => {
    const role = (roles || []).find(r => r.role_code === currentRole);
    return role?.role_name || '选择';
  }, [roles, currentRole]);

  if (!roles || roles.length <= 1) {
    return null;
  }

  return (
    <Select value={currentRole || "unknown"} onValueChange={onChange}>
      <SelectTrigger className={`w-32 h-8 text-sm ${className}`}>
        <SelectValue>{currentRoleName}</SelectValue>
      </SelectTrigger>
      <SelectContent>
        {(roles || []).map((role) => (
          <SelectItem key={role.role_code} value={role.role_code}>
            {role.role_name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export default RoleSwitcher;
