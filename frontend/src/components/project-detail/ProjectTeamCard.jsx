import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Button,
  Avatar,
  Progress,
  ScrollArea,
  Separator,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger } from
'@/components/ui';
import {
  PROJECT_ROLES } from
'./projectDetailConstants';
import { format } from 'date-fns';
import { zhCN as _zhCN } from 'date-fns/locale';
import { Mail, Phone, Calendar, UserCheck, UserX } from 'lucide-react';

const ProjectTeamCard = ({ project, onAssignMember, onRemoveMember, onUpdateRole }) => {
  const [selectedMember, setSelectedMember] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);

  // Get role info
  const getRoleInfo = (roleCode) => {
    const roleMap = {
      'PM': PROJECT_ROLES.PROJECT_MANAGER,
      'TM': PROJECT_ROLES.TECHNICAL_MANAGER,
      'ENG': PROJECT_ROLES.ENGINEER,
      'PUR': PROJECT_ROLES.PURCHASING,
      'QA': PROJECT_ROLES.QUALITY,
      'SALE': PROJECT_ROLES.SALES
    };
    return roleMap[roleCode] || PROJECT_ROLES.ENGINEER;
  };

  // Calculate team workload
  const calculateWorkload = (member) => {
    if (!member.assigned_projects || member.assigned_projects.length === 0) {
      return 0;
    }

    const activeProjects = member.assigned_projects.filter((p) =>
    p.status === 'ACTIVE' || p.status === 'DELAYED'
    ).length;

    return Math.min(activeProjects * 20, 100);
  };

  // Format workload text
  const formatWorkload = (workload) => {
    if (workload === 0) {return '空闲';}
    if (workload < 30) {return '轻度';}
    if (workload < 60) {return '中度';}
    if (workload < 80) {return '繁忙';}
    return '过载';
  };

  // Get workload color
  const getWorkloadColor = (workload) => {
    if (workload === 0) {return '#10B981';}
    if (workload < 30) {return '#3B82F6';}
    if (workload < 60) {return '#F59E0B';}
    if (workload < 80) {return '#EF4444';}
    return '#DC2626';
  };

  // Render member card
  const renderMemberCard = (member, _index) => {
    const roleInfo = getRoleInfo(member.role);
    const workload = calculateWorkload(member);
    const workloadText = formatWorkload(workload);

    return (
      <div
        key={member.id}
        className="group p-4 rounded-lg border bg-white hover:border-gray-300 transition-all cursor-pointer"
        onClick={() => {
          setSelectedMember(member);
          setIsDialogOpen(true);
        }}>

        <div className="flex items-start gap-3">
          <div className="relative">
            <Avatar className="w-12 h-12">
              {member.name?.charAt(0).toUpperCase() || 'U'}
            </Avatar>
            <div
              className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-2 border-white flex items-center justify-center text-xs"
              style={{ backgroundColor: roleInfo.color }}>

              {roleInfo.code}
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <h4 className="font-semibold text-gray-900 truncate">
                  {member.name}
                </h4>
                <p className="text-sm text-gray-600 truncate">
                  {roleInfo.name}
                </p>
              </div>
              <Badge
                variant="outline"
                className="text-xs flex-shrink-0"
                style={{
                  borderColor: getWorkloadColor(workload),
                  color: getWorkloadColor(workload)
                }}>

                {workloadText}
              </Badge>
            </div>

            <div className="mt-2 space-y-1">
              {member.email &&
              <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Mail className="w-3 h-3" />
                  <span className="truncate">{member.email}</span>
              </div>
              }
              {member.phone &&
              <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Phone className="w-3 h-3" />
                  <span>{member.phone}</span>
              </div>
              }
              {member.join_date &&
              <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Calendar className="w-3 h-3" />
                  <span>
                    加入于 {format(new Date(member.join_date), 'yyyy-MM-dd')}
                  </span>
              </div>
              }
            </div>

            <div className="mt-2">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-gray-500">工作负载</span>
                <span className="font-medium">{workload}%</span>
              </div>
              <Progress value={workload} className="h-1.5" />
            </div>

            {member.assigned_projects && member.assigned_projects.length > 0 &&
            <div className="mt-2">
                <div className="text-xs text-gray-500 mb-1">负责项目</div>
                <div className="flex flex-wrap gap-1">
                  {member.assigned_projects.slice(0, 3).map((proj) =>
                <Badge
                  key={proj.id}
                  variant="secondary"
                  className="text-xs">

                      {proj.name}
                </Badge>
                )}
                  {member.assigned_projects.length > 3 &&
                <Badge variant="secondary" className="text-xs">
                      +{member.assigned_projects.length - 3}
                </Badge>
                }
                </div>
            </div>
            }
          </div>
        </div>
      </div>);

  };

  // Render team statistics
  const renderTeamStats = () => {
    const totalMembers = project.team_members?.length || 0;
    const roleCounts = {};

    project.team_members?.forEach((member) => {
      const role = getRoleInfo(member.role);
      roleCounts[role.code] = (roleCounts[role.code] || 0) + 1;
    });

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{totalMembers}</div>
              <div className="text-sm text-gray-500">团队成员</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {roleCounts.PM || 0}
              </div>
              <div className="text-sm text-gray-500">项目经理</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {roleCounts.ENG || 0}
              </div>
              <div className="text-sm text-gray-500">工程师</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {roleCounts.PUR + (roleCounts.QA || 0) + (roleCounts.SALE || 0)}
              </div>
              <div className="text-sm text-gray-500">支持人员</div>
            </div>
          </CardContent>
        </Card>
      </div>);

  };

  return (
    <div className="space-y-6">
      {renderTeamStats()}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>项目团队</CardTitle>
              <CardDescription>
                点击成员查看详细信息
              </CardDescription>
            </div>
            <Button onClick={() => onAssignMember()}>
              + 添加成员
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4">
            {project.team_members && project.team_members.length > 0 ?
            <div className="space-y-3">
                {project.team_members.map((member, index) =>
              <React.Fragment key={member.id}>
                    {renderMemberCard(member, index)}
                    {index < project.team_members.length - 1 &&
                <Separator />
                }
              </React.Fragment>
              )}
            </div> :

            <div className="text-center py-12 text-gray-500">
                <UserX className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">暂无团队成员</p>
                <p className="text-sm">点击"添加成员"按钮邀请团队成员</p>
            </div>
            }
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Member Detail Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          {selectedMember &&
          <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <Avatar className="w-10 h-10">
                    {selectedMember.name?.charAt(0).toUpperCase() || 'U'}
                  </Avatar>
                  <div>
                    <div>{selectedMember.name}</div>
                    <Badge
                    variant="outline"
                    className="mt-1"
                    style={{
                      borderColor: getRoleInfo(selectedMember.role).color,
                      color: getRoleInfo(selectedMember.role).color
                    }}>

                      {getRoleInfo(selectedMember.role).name}
                    </Badge>
                  </div>
                </DialogTitle>
                <DialogDescription>
                  成员详细信息
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">基本信息</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-gray-400" />
                      <span>{selectedMember.email || '未设置邮箱'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-gray-400" />
                      <span>{selectedMember.phone || '未设置电话'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span>
                        加入于 {selectedMember.join_date ?
                      format(new Date(selectedMember.join_date), 'yyyy-MM-dd') :
                      '未知'
                      }
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">工作负载</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>当前负载</span>
                      <span className="font-medium">{calculateWorkload(selectedMember)}%</span>
                    </div>
                    <Progress value={calculateWorkload(selectedMember)} />
                    <div className="text-xs text-gray-500">
                      状态: {formatWorkload(calculateWorkload(selectedMember))}
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">负责项目</h4>
                  {selectedMember.assigned_projects && selectedMember.assigned_projects.length > 0 ?
                <div className="space-y-2">
                      {selectedMember.assigned_projects.map((proj) =>
                  <div
                    key={proj.id}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded">

                          <span className="text-sm">{proj.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {proj.status}
                          </Badge>
                  </div>
                  )}
                </div> :

                <p className="text-sm text-gray-500">暂无其他项目</p>
                }
                </div>
              </div>

              <DialogFooter className="flex gap-2">
                <Button
                variant="outline"
                onClick={() => {
                  onUpdateRole(selectedMember);
                  setRoleDialogOpen(true);
                }}>

                  更新角色
                </Button>
                <Button
                variant="outline"
                onClick={() => onRemoveMember(selectedMember.id)}>

                  移除成员
                </Button>
              </DialogFooter>
          </>
          }
        </DialogContent>
      </Dialog>

      {/* Role Update Dialog */}
      <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>更新成员角色</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {Object.values(PROJECT_ROLES).map((role) =>
            <Button
              key={role.code}
              variant="outline"
              className="w-full justify-start"
              style={{
                borderColor: role.color,
                color: role.color
              }}
              onClick={() => {
                onUpdateRole(selectedMember, role.code);
                setRoleDialogOpen(false);
              }}>

                {role.icon} {role.name}
            </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>);

};

export default ProjectTeamCard;