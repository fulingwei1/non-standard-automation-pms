import DeleteConfirmDialog from "../common/DeleteConfirmDialog";

export default function DeleteTemplateDialog({
  open,
  onOpenChange,
  template,
  onConfirm,
}) {
  return (
    <DeleteConfirmDialog
      open={open}
      onOpenChange={onOpenChange}
      title="确认删除"
      description={`确定要删除模板 "${template?.template_name}" 吗？删除后无法恢复。`}
      confirmText="删除"
      onConfirm={onConfirm}
      contentClassName="bg-surface-50 border-white/10"
      titleClassName="text-white"
      descriptionClassName="text-slate-300"
      cancelButtonClassName="border-white/10 text-slate-300"
    />
  );
}
