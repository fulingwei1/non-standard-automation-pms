import { useNavigate } from "react-router-dom";



export default function DocumentsTab({ id }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            研发项目文档
          </h3>
          <Button
            onClick={() => navigate(`/rd-projects/${id}/documents`)}
          >
            查看全部
          </Button>
        </div>
        <div className="text-center py-12 text-slate-500">
          <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
          <p>文档管理</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => navigate(`/rd-projects/${id}/documents`)}
          >
            进入文档管理页面
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
