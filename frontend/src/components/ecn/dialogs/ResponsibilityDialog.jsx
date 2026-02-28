/**
 * ResponsibilityDialog Component
 * 责任分摊对话框
 */
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  DialogDescription,
} from "../../ui/dialog";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Textarea } from "../../ui/textarea";
import { Card } from "../../ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../ui/select";
import { Plus, X } from "lucide-react";

export default function ResponsibilityDialog({
  open,
  onOpenChange,
  form,
  setForm,
  onSubmit,
}) {
  const totalRatio = (form || []).reduce(
    (sum, r) => sum + parseFloat(r.responsibility_ratio || 0),
    0,
  );
  const isValid = Math.abs(totalRatio - 100) < 0.01;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>责任分摊配置</DialogTitle>
          <DialogDescription>
            配置多部门责任分摊比例，总和必须为100%
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-4">
          {(form || []).map((resp, index) => (
            <Card key={index} className="p-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium">责任部门 {index + 1}</div>
                  {form.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newForm = (form || []).filter((_, i) => i !== index);
                        setForm(newForm);
                      }}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      部门名称 *
                    </label>
                    <Input
                      value={resp.dept}
                      onChange={(e) => {
                        const newForm = [...form];
                        newForm[index].dept = e.target.value;
                        setForm(newForm);
                      }}
                      placeholder="如：机械部、电气部等"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      责任比例 (%) *
                    </label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={resp.responsibility_ratio}
                      onChange={(e) => {
                        const newForm = [...form];
                        newForm[index].responsibility_ratio =
                          parseFloat(e.target.value) || 0;
                        setForm(newForm);
                      }}
                      placeholder="0-100"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    责任类型
                  </label>
                  <Select
                    value={resp.responsibility_type}
                    onValueChange={(value) => {
                      const newForm = [...form];
                      newForm[index].responsibility_type = value;
                      setForm(newForm);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PRIMARY">主要责任</SelectItem>
                      <SelectItem value="SECONDARY">次要责任</SelectItem>
                      <SelectItem value="SUPPORT">支持责任</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    影响描述
                  </label>
                  <Textarea
                    value={resp.impact_description}
                    onChange={(e) => {
                      const newForm = [...form];
                      newForm[index].impact_description = e.target.value;
                      setForm(newForm);
                    }}
                    placeholder="描述该部门受到的影响"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    责任范围
                  </label>
                  <Textarea
                    value={resp.responsibility_scope}
                    onChange={(e) => {
                      const newForm = [...form];
                      newForm[index].responsibility_scope = e.target.value;
                      setForm(newForm);
                    }}
                    placeholder="描述该部门的责任范围"
                    rows={2}
                  />
                </div>
              </div>
            </Card>
          ))}
          <Button
            variant="outline"
            className="w-full"
            onClick={() => {
              setForm([
                ...form,
                {
                  dept: "",
                  responsibility_ratio: 0,
                  responsibility_type: "PRIMARY",
                  impact_description: "",
                  responsibility_scope: "",
                },
              ]);
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            添加责任部门
          </Button>
          <div className="pt-2 border-t">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">责任比例总和</span>
              <span
                className={`text-lg font-bold ${
                  isValid ? "text-green-600" : "text-red-600"
                }`}
              >
                {totalRatio.toFixed(2)}%
              </span>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit} disabled={!isValid}>
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
