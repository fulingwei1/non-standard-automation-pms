/**
 * 需求调研表单组件
 * 用于填写客户需求调研信息
 */
import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Building2,
  User,
  Phone,
  MapPin,
  Calendar,
  Package,
  Settings,
  Target,
  DollarSign,
  Clock,
  Shield,
  Plus,
  X,
  Save,
} from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

const surveyMethods = [
  { id: "onsite", name: "现场调研", icon: MapPin },
  { id: "remote", name: "远程调研", icon: Building2 },
  { id: "phone", name: "电话调研", icon: Phone },
];

export function SurveyForm({ initialData, onSubmit, onCancel, className }) {
  const [formData, setFormData] = useState({
    customer: initialData?.customer || "",
    contactPerson: initialData?.contactPerson || "",
    contactPhone: initialData?.contactPhone || "",
    method: initialData?.method || "onsite",
    scheduledDate: initialData?.scheduledDate || "",
    location: initialData?.location || "",
    opportunity: initialData?.opportunity || "",
    productName: initialData?.productInfo?.name || "",
    productModel: initialData?.productInfo?.model || "",
    productSize: initialData?.productInfo?.size || "",
    testRequirements: initialData?.testRequirements || [],
    annualCapacity: initialData?.capacityRequirements?.annual || "",
    dailyCapacity: initialData?.capacityRequirements?.daily || "",
    uph: initialData?.capacityRequirements?.uph || "",
    budget: initialData?.budget || "",
    timeline: initialData?.timeline || "",
    competitors: initialData?.competitors || [],
    summary: initialData?.summary || "",
  });

  const [newTestReq, setNewTestReq] = useState("");
  const [newCompetitor, setNewCompetitor] = useState("");

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAddTestReq = () => {
    if (newTestReq.trim()) {
      setFormData((prev) => ({
        ...prev,
        testRequirements: [...prev.testRequirements, newTestReq.trim()],
      }));
      setNewTestReq("");
    }
  };

  const handleRemoveTestReq = (index) => {
    setFormData((prev) => ({
      ...prev,
      testRequirements: prev.testRequirements.filter((_, i) => i !== index),
    }));
  };

  const handleAddCompetitor = () => {
    if (newCompetitor.trim()) {
      setFormData((prev) => ({
        ...prev,
        competitors: [...prev.competitors, newCompetitor.trim()],
      }));
      setNewCompetitor("");
    }
  };

  const handleRemoveCompetitor = (index) => {
    setFormData((prev) => ({
      ...prev,
      competitors: prev.competitors.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit?.(formData);
  };

  return (
    <motion.form
      variants={fadeIn}
      className={cn("space-y-6", className)}
      onSubmit={handleSubmit}
    >
      {/* 基本信息 */}
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Building2 className="w-5 h-5 text-primary" />
            基本信息
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">客户名称 *</label>
            <Input
              value={formData.customer}
              onChange={(e) => handleChange("customer", e.target.value)}
              placeholder="请输入客户名称"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">关联商机</label>
            <Input
              value={formData.opportunity}
              onChange={(e) => handleChange("opportunity", e.target.value)}
              placeholder="请输入关联商机"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">联系人 *</label>
            <Input
              value={formData.contactPerson}
              onChange={(e) => handleChange("contactPerson", e.target.value)}
              placeholder="请输入联系人"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">联系电话 *</label>
            <Input
              value={formData.contactPhone}
              onChange={(e) => handleChange("contactPhone", e.target.value)}
              placeholder="请输入联系电话"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">调研方式 *</label>
            <div className="flex gap-2">
              {surveyMethods.map((method) => {
                const MethodIcon = method.icon;
                return (
                  <Button
                    key={method.id}
                    type="button"
                    variant={
                      formData.method === method.id ? "default" : "outline"
                    }
                    size="sm"
                    onClick={() => handleChange("method", method.id)}
                    className="flex items-center gap-2"
                  >
                    <MethodIcon className="w-4 h-4" />
                    {method.name}
                  </Button>
                );
              })}
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">计划日期 *</label>
            <Input
              type="date"
              value={formData.scheduledDate}
              onChange={(e) => handleChange("scheduledDate", e.target.value)}
              required
            />
          </div>
          <div className="md:col-span-2 space-y-2">
            <label className="text-sm text-slate-400">调研地点</label>
            <Input
              value={formData.location}
              onChange={(e) => handleChange("location", e.target.value)}
              placeholder="请输入调研地点"
            />
          </div>
        </CardContent>
      </Card>

      {/* 产品信息 */}
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Package className="w-5 h-5 text-primary" />
            产品信息
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">产品名称</label>
            <Input
              value={formData.productName}
              onChange={(e) => handleChange("productName", e.target.value)}
              placeholder="请输入产品名称"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">型号规格</label>
            <Input
              value={formData.productModel}
              onChange={(e) => handleChange("productModel", e.target.value)}
              placeholder="请输入型号规格"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">外形尺寸</label>
            <Input
              value={formData.productSize}
              onChange={(e) => handleChange("productSize", e.target.value)}
              placeholder="请输入外形尺寸"
            />
          </div>
        </CardContent>
      </Card>

      {/* 测试需求 */}
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Settings className="w-5 h-5 text-primary" />
            测试需求
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={newTestReq}
              onChange={(e) => setNewTestReq(e.target.value)}
              placeholder="输入测试项目"
              onKeyPress={(e) =>
                e.key === "Enter" && (e.preventDefault(), handleAddTestReq())
              }
            />
            <Button type="button" variant="outline" onClick={handleAddTestReq}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.testRequirements.map((req, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="flex items-center gap-1"
              >
                {req}
                <X
                  className="w-3 h-3 cursor-pointer hover:text-red-400"
                  onClick={() => handleRemoveTestReq(index)}
                />
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 产能需求 */}
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            产能需求
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">年产量</label>
            <Input
              value={formData.annualCapacity}
              onChange={(e) => handleChange("annualCapacity", e.target.value)}
              placeholder="请输入年产量"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">日产量</label>
            <Input
              value={formData.dailyCapacity}
              onChange={(e) => handleChange("dailyCapacity", e.target.value)}
              placeholder="请输入日产量"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">UPH</label>
            <Input
              value={formData.uph}
              onChange={(e) => handleChange("uph", e.target.value)}
              placeholder="请输入UPH"
            />
          </div>
        </CardContent>
      </Card>

      {/* 预算和时间 */}
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-primary" />
            预算与时间
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">预算范围</label>
            <Input
              value={formData.budget}
              onChange={(e) => handleChange("budget", e.target.value)}
              placeholder="如：80-100万"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">交付时间</label>
            <Input
              value={formData.timeline}
              onChange={(e) => handleChange("timeline", e.target.value)}
              placeholder="如：2026年3月前"
            />
          </div>
        </CardContent>
      </Card>

      {/* 竞争情况 */}
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />
            竞争情况
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={newCompetitor}
              onChange={(e) => setNewCompetitor(e.target.value)}
              placeholder="输入竞争对手"
              onKeyPress={(e) =>
                e.key === "Enter" && (e.preventDefault(), handleAddCompetitor())
              }
            />
            <Button
              type="button"
              variant="outline"
              onClick={handleAddCompetitor}
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.competitors.map((comp, index) => (
              <Badge
                key={index}
                variant="destructive"
                className="flex items-center gap-1"
              >
                {comp}
                <X
                  className="w-3 h-3 cursor-pointer hover:text-white"
                  onClick={() => handleRemoveCompetitor(index)}
                />
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 调研摘要 */}
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardHeader>
          <CardTitle className="text-lg">调研摘要</CardTitle>
        </CardHeader>
        <CardContent>
          <textarea
            className="w-full h-32 bg-surface-50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            value={formData.summary}
            onChange={(e) => handleChange("summary", e.target.value)}
            placeholder="请输入调研摘要..."
          />
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex justify-end gap-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          取消
        </Button>
        <Button type="submit" className="flex items-center gap-2">
          <Save className="w-4 h-4" />
          保存
        </Button>
      </div>
    </motion.form>
  );
}

export default SurveyForm;
