import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import PositionFormFields from "./PositionFormFields";

export default function EditDialog({
  open,
  onOpenChange,
  formData,
  handleFormChange,
  setFormData,
  orgUnits,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>编辑岗位</DialogTitle>
        </DialogHeader>
        <PositionFormFields
          formData={formData}
          handleFormChange={handleFormChange}
          setFormData={setFormData}
          orgUnits={orgUnits}
          isEdit={true}
        />
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={onSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
