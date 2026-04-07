import { Search } from "lucide-react";


export function FilterBar({
  categories,
  selectedCategory,
  onSelectCategory,
  keyword,
  onKeywordChange,
}) {
  return (
    <Card className="bg-surface-1/50">
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-2">
            {(categories || []).map((category) => (
              <Button
                key={category.key}
                size="sm"
                variant={selectedCategory === category.key ? "default" : "outline"}
                onClick={() => onSelectCategory(category.key)}
              >
                {category.label}
                <span className="ml-1 text-xs text-slate-300">
                  {category.count}
                </span>
              </Button>
            ))}
          </div>

          <div className="w-full lg:w-80">
            <Input
              value={keyword}
              onChange={(event) => onKeywordChange(event.target.value)}
              placeholder="搜索模板名称、标签或应用场景"
              icon={Search}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
