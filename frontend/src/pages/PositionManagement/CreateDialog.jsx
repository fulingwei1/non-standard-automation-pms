


export default function CreateDialog({
  open,
  onOpenChange,
  formData,
  handleFormChange,
  setFormData,
  orgUnits,
  resetForm,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) { resetForm(); } }}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>新增岗位</DialogTitle>
        </DialogHeader>
        <PositionFormFields
          formData={formData}
          handleFormChange={handleFormChange}
          setFormData={setFormData}
          orgUnits={orgUnits}
          isEdit={false}
        />
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={onSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
