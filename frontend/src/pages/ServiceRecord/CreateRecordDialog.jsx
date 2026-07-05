import { Upload, FileCheck, X } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import { Textarea } from "../../components/ui/textarea";
import { SERVICE_TYPES } from "../../components/service-record";

export default function CreateRecordDialog({
  open,
  onOpenChange,
  formData,
  setFormData,
  onSubmit,
  onPhotoUpload,
  onRemovePhoto,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建服务记录</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-slate-300">
              服务类型
            </label>
            <select
              value={formData.service_type}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  service_type: e.target.value,
                }))
              }
              className="w-full mt-1 p-2 bg-slate-800 border border-slate-700 rounded text-white"
            >
              {Object.entries(SERVICE_TYPES).map(([key, type]) => (
                <option key={key} value={key}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              项目名称
            </label>
            <Input
              value={formData.project_name}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  project_name: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
              placeholder="请输入项目名称"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              客户名称
            </label>
            <Input
              value={formData.customer_name}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  customer_name: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
              placeholder="请输入客户名称"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              服务地点
            </label>
            <Input
              value={formData.service_location}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  service_location: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
              placeholder="请输入服务地点"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              服务日期
            </label>
            <Input
              type="date"
              value={formData.service_date}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  service_date: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              服务工程师
            </label>
            <Input
              value={formData.service_engineer}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  service_engineer: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
              placeholder="请输入工程师姓名"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              客户联系人
            </label>
            <Input
              value={formData.customer_contact}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  customer_contact: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
              placeholder="请输入联系人姓名"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              联系电话
            </label>
            <Input
              value={formData.customer_phone}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  customer_phone: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
              placeholder="请输入联系电话"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div>
            <label className="text-sm font-medium text-slate-300">
              开始时间
            </label>
            <Input
              type="datetime-local"
              value={formData.service_start_time}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  service_start_time: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">
              结束时间
            </label>
            <Input
              type="datetime-local"
              value={formData.service_end_time}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  service_end_time: e.target.value,
                }))
              }
              className="mt-1 bg-slate-800 border-slate-700"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="text-sm font-medium text-slate-300">服务内容</label>
          <Textarea
            value={formData.service_content}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                service_content: e.target.value,
              }))
            }
            className="mt-1 bg-slate-800 border-slate-700"
            rows={4}
            placeholder="请详细描述服务内容..."
          />
        </div>

        <div className="mt-4">
          <label className="text-sm font-medium text-slate-300">服务结果</label>
          <Textarea
            value={formData.service_result}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                service_result: e.target.value,
              }))
            }
            className="mt-1 bg-slate-800 border-slate-700"
            rows={3}
            placeholder="请描述服务结果..."
          />
        </div>

        <div className="mt-4">
          <label className="text-sm font-medium text-slate-300">照片上传</label>
          <div className="mt-2">
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={onPhotoUpload}
              className="hidden"
              id="photo-upload"
            />
            <label htmlFor="photo-upload">
              <Button type="button" variant="outline" className="cursor-pointer">
                <Upload className="h-4 w-4 mr-2" />
                选择照片
              </Button>
            </label>
          </div>

          {formData.photos?.length > 0 && (
            <div className="mt-4 grid grid-cols-4 gap-2">
              {(formData.photos || []).map((photo, index) => (
                <div key={index} className="relative">
                  <img
                    src={photo.url}
                    alt={photo.name}
                    className="w-full h-20 object-cover rounded border border-slate-700"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    className="absolute -top-2 -right-2 h-6 w-6 p-0"
                    onClick={() => onRemovePhoto(index)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={onSubmit}
            className="bg-blue-500 hover:bg-blue-600"
          >
            <FileCheck className="h-4 w-4 mr-2" />
            创建记录
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
