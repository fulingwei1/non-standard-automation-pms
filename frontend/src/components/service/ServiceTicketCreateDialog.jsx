/**
 * Service Ticket Create Dialog Component
 * 服务工单创建对话框组件
 */

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter } from
"../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Send, Plus, X } from "lucide-react";
import { problemTypeConfigs, urgencyConfigs } from "@/lib/constants/service";import { toast } from "sonner";

export function ServiceTicketCreateDialog({ onClose, onSubmit, submitting }) {
  const [formData, setFormData] = useState({
    project_id: "",
    project_ids: [],
    customer_id: "",
    problem_type: "",
    problem_desc: "",
    urgency: "普通",
    reported_by: "",
    reported_phone: "",
    remark: "",
    assignee_id: null,
    cc_user_ids: []
  });

  const [customers, setCustomers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [_loadingCustomers, setLoadingCustomers] = useState(false);
  const [_loadingProjects, setLoadingProjects] = useState(false);
  const [_loadingUsers, setLoadingUsers] = useState(false);

  // Load data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoadingCustomers(true);
        setLoadingProjects(true);
        setLoadingUsers(true);

        // Load customers
        const customerResponse = await fetch('/api/v1/customers/', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const customerData = await customerResponse.json();
        setCustomers(customerData.items || []);

        // Load projects
        const projectResponse = await fetch('/api/v1/projects/', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const projectData = await projectResponse.json();
        setProjects(projectData.items || []);

        // Load users
        const userResponse = await fetch(
          '/api/v1/users/?is_active=true&page=1&page_size=100',
          { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
        );
        const userData = await userResponse.json();
        setUsers(userData?.items ?? []);

      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoadingCustomers(false);
        setLoadingProjects(false);
        setLoadingUsers(false);
      }
    };

    loadData();
  }, []);

  const handleSubmit = async () => {
    if (submitting) {return;}

    // 验证必填字段
    if (!formData.project_id || !formData.project_ids || formData.project_ids?.length === 0) {
      toast.warning("请至少选择一个关联项目");
      return;
    }
    if (!formData.customer_id) {
      toast.warning("请选择客户");
      return;
    }
    if (!formData.problem_type) {
      toast.warning("请选择问题类型");
      return;
    }
    if (!formData.problem_desc || !formData.problem_desc.trim()) {
      toast.warning("请填写问题描述");
      return;
    }
    if (!formData.reported_by || !formData.reported_by.trim()) {
      toast.warning("请填写报告人");
      return;
    }

    try {
      const createData = {
        project_id: parseInt(formData.project_id),
        project_ids: (formData.project_ids || []).map((id) => parseInt(id)),
        customer_id: parseInt(formData.customer_id),
        problem_type: formData.problem_type,
        problem_desc: formData.problem_desc,
        urgency: formData.urgency,
        reported_by: formData.reported_by,
        reported_phone: formData.reported_phone,
        remark: formData.remark,
        assignee_id: formData.assignee_id ? parseInt(formData.assignee_id) : null,
        cc_user_ids: (formData.cc_user_ids || []).map((id) => parseInt(id)),
        reported_time: new Date().toISOString()
      };

      await onSubmit(createData);
    } catch (error) {
      console.error("Submit failed:", error);
    }
  };

  const addProject = (projectId) => {
    if (projectId && !formData.project_ids.includes(projectId)) {
      setFormData((prev) => ({
        ...prev,
        project_ids: [...prev.project_ids, projectId]
      }));
    }
  };

  const removeProject = (projectId) => {
    setFormData((prev) => ({
      ...prev,
      project_ids: (prev.project_ids || []).filter((id) => id !== projectId)
    }));
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Send className="w-5 h-5" />
            创建服务工单
          </DialogTitle>
          <DialogDescription>
            填写工单信息，创建新的服务工单
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Customer Selection */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                客户 *
              </label>
              <Select
                value={formData.customer_id}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, customer_id: value }))}>

                <SelectTrigger className="bg-slate-800/50 border-slate-700 text-white">
                  <SelectValue placeholder="选择客户" />
                </SelectTrigger>
                <SelectContent>
                  {(customers || []).map((customer) =>
                  <SelectItem key={customer.id} value={customer.id.toString()}>
                      {customer.customer_name} ({customer.customer_code})
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Project Selection */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                关联项目 *
              </label>
              <div className="space-y-2">
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => {
                    setFormData((prev) => ({ ...prev, project_id: value }));
                    addProject(value);
                  }}>

                  <SelectTrigger className="bg-slate-800/50 border-slate-700 text-white">
                    <SelectValue placeholder="选择主要项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {(projects || []).map((project) =>
                    <SelectItem key={project.id} value={project.id.toString()}>
                        {project.project_code} - {project.project_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>

                {/* Selected Projects */}
                {formData.project_ids?.length > 0 &&
                <div className="flex flex-wrap gap-2">
                    {(formData.project_ids || []).map((projectId) => {
                    const project = (projects || []).find((p) => p.id.toString() === projectId);
                    return project ?
                    <div
                      key={projectId}
                      className="flex items-center gap-1 bg-blue-500/20 text-blue-300 px-2 py-1 rounded text-sm">

                          <span>{project.project_code}</span>
                          {formData.project_ids?.length > 1 &&
                      <button
                        onClick={() => removeProject(projectId)}
                        className="hover:text-blue-100">

                              <X className="w-3 h-3" />
                      </button>
                      }
                    </div> :
                    null;
                  })}
                </div>
                }
              </div>
            </div>

            {/* Problem Type and Urgency */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  问题类型 *
                </label>
                <select
                  value={formData.problem_type}
                  onChange={(e) => setFormData((prev) => ({ ...prev, problem_type: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white">

                  <option value="">选择问题类型</option>
                  {Object.entries(problemTypeConfigs).map(([key, config]) =>
                  <option key={key} value={key || "unknown"}>
                      {config.icon} {config.label}
                  </option>
                  )}
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  紧急程度 *
                </label>
                <select
                  value={formData.urgency}
                  onChange={(e) => setFormData((prev) => ({ ...prev, urgency: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white">

                  {Object.entries(urgencyConfigs).map(([key, config]) =>
                  <option key={key} value={key || "unknown"}>
                      {config.label}
                  </option>
                  )}
                </select>
              </div>
            </div>

            {/* Problem Description */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                问题描述 *
              </label>
              <Textarea
                value={formData.problem_desc}
                onChange={(e) => setFormData((prev) => ({ ...prev, problem_desc: e.target.value }))}
                placeholder="请详细描述问题情况..."
                rows={4}
                className="bg-slate-800/50 border-slate-700" />

            </div>

            {/* Reporter Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  报告人 *
                </label>
                <Input
                  value={formData.reported_by}
                  onChange={(e) => setFormData((prev) => ({ ...prev, reported_by: e.target.value }))}
                  placeholder="输入报告人姓名"
                  className="bg-slate-800/50 border-slate-700" />

              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  报告人电话
                </label>
                <Input
                  value={formData.reported_phone}
                  onChange={(e) => setFormData((prev) => ({ ...prev, reported_phone: e.target.value }))}
                  placeholder="输入报告人电话"
                  className="bg-slate-800/50 border-slate-700" />

              </div>
            </div>

            {/* Assignment */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                指派处理人
              </label>
              <Select
                value={formData.assignee_id || ""}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, assignee_id: value }))}>

                <SelectTrigger className="bg-slate-800/50 border-slate-700 text-white">
                  <SelectValue placeholder="选择处理人（可选）" />
                </SelectTrigger>
                <SelectContent>
                  {(users || []).map((user) =>
                  <SelectItem key={user.id} value={user.id.toString()}>
                      {user.real_name || user.username} ({user.position || '工程师'})
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Remarks */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">备注</label>
              <Textarea
                value={formData.remark}
                onChange={(e) => setFormData((prev) => ({ ...prev, remark: e.target.value }))}
                placeholder="其他备注信息..."
                rows={2}
                className="bg-slate-800/50 border-slate-700" />

            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            <Send className="w-4 h-4 mr-2" />
            {submitting ? "创建中..." : "创建工单"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}