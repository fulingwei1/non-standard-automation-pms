import { Upload, FileSpreadsheet, Download } from "lucide-react";
import {
    Card,
    CardHeader,
    CardTitle,
    CardContent,
    Button,
    Input,
    Select,
    SelectTrigger,
    SelectValue,
    SelectContent,
    SelectItem,
    Checkbox,
    Label
} from "../../../components/ui";

export function DataImportPanel({
    loading,
    templateTypes,
    selectedTemplateType,
    setSelectedTemplateType,
    importFile,
    setImportFile,
    updateExisting,
    setUpdateExisting,
    onDownloadTemplate,
    onPreviewImport,
    onUploadImport
}) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>导入数据</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <Label>模板类型</Label>
                        <Select
                            value={selectedTemplateType}
                            onValueChange={setSelectedTemplateType}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="选择模板类型" />
                            </SelectTrigger>
                            <SelectContent>
                                {templateTypes.map((type) => (
                                    <SelectItem key={type.type} value={type.type}>
                                        {type.name} - {type.description}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div>
                        <Label>选择文件</Label>
                        <Input
                            type="file"
                            accept=".xlsx,.xls"
                            onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                        />
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                    <Checkbox
                        id="update-existing"
                        checked={updateExisting}
                        onCheckedChange={setUpdateExisting}
                    />
                    <Label htmlFor="update-existing" className="cursor-pointer">
                        更新已存在的数据
                    </Label>
                </div>

                <div className="flex gap-2">
                    {selectedTemplateType && (
                        <Button
                            variant="outline"
                            onClick={() => onDownloadTemplate(selectedTemplateType)}
                            disabled={loading}
                        >
                            <Download className="h-4 w-4 mr-2" />
                            下载模板
                        </Button>
                    )}
                    <Button
                        onClick={onPreviewImport}
                        disabled={loading || !importFile || !selectedTemplateType}
                    >
                        <FileSpreadsheet className="h-4 w-4 mr-2" />
                        预览数据
                    </Button>
                    <Button
                        onClick={onUploadImport}
                        disabled={loading || !importFile || !selectedTemplateType}
                    >
                        <Upload className="h-4 w-4 mr-2" />
                        导入数据
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
