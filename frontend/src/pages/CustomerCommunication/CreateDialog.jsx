


export default function CreateDialog({ open, onOpenChange, formData, setFormData, customers, users, onSubmit }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white">新建沟通记录</DialogTitle>
        </DialogHeader>
        <CommunicationFormFields
          formData={formData}
          setFormData={setFormData}
          customers={customers}
          users={users}
        />
        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
