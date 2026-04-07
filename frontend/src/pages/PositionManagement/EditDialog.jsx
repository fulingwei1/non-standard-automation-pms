


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
