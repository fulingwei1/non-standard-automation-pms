import React from 'react';
import { CheckCircle2, Eye } from 'lucide-react';
import { Card, CardContent, Button } from '../../../components/ui';

export function ProjectClosureActions({ closure, onReview, onViewDetail }) {
    if (closure.status === "REVIEWED") return null;

    return (
        <Card>
            <CardContent className="p-5">
                <div className="flex items-center gap-2">
                    {closure.status === "DRAFT" && (
                        <Button onClick={() => onReview(closure.id)}>
                            <CheckCircle2 className="h-4 w-4 mr-2" />
                            提交评审
                        </Button>
                    )}
                    <Button
                        variant="outline"
                        onClick={() => onViewDetail(closure)}
                    >
                        <Eye className="h-4 w-4 mr-2" />
                        查看详情
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
