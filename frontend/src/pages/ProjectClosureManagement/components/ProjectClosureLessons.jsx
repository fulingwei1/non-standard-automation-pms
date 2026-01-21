import React from 'react';
import { Edit } from 'lucide-react';
import { Card, CardContent, Button } from '../../../components/ui';

export function ProjectClosureLessons({ closure, onEdit }) {
    return (
        <Card>
            <CardContent className="p-5">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">经验教训</h3>
                    {closure.status !== "REVIEWED" && (
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onEdit(closure.id)}
                        >
                            <Edit className="h-4 w-4 mr-2" />
                            编辑
                        </Button>
                    )}
                </div>
                {closure.lessons_learned ? (
                    <p className="text-white whitespace-pre-wrap">
                        {closure.lessons_learned}
                    </p>
                ) : (
                    <p className="text-slate-500">暂无经验教训记录</p>
                )}
                {closure.improvement_suggestions && (
                    <div className="mt-4">
                        <h4 className="text-sm font-medium text-white mb-2">
                            改进建议
                        </h4>
                        <p className="text-white whitespace-pre-wrap">
                            {closure.improvement_suggestions}
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
