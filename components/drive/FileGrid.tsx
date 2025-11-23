"use client";

import { Document } from "@/hooks/useDocuments";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { FileText, Image as ImageIcon, FileCode, Receipt, File, CheckCircle2 } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

interface FileGridProps {
    documents: Document[];
    onDocumentClick: (doc: Document) => void;
    selectedIds: Set<string>;
    onToggleSelection: (id: string) => void;
}

const getIcon = (type: Document['type']) => {
    switch (type) {
        case 'invoice': return FileText;
        case 'receipt': return Receipt;
        case 'image': return ImageIcon;
        case 'contract': return FileCode;
        default: return File;
    }
};

const isImage = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '');
};

const isPdf = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    return ext === 'pdf';
};

export function FileGrid({ documents, onDocumentClick, selectedIds, onToggleSelection }: FileGridProps) {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {documents.map((doc) => {
                const Icon = getIcon(doc.type);
                const isImg = isImage(doc.title);
                const isPdfFile = isPdf(doc.title);
                const isSelected = selectedIds.has(doc.id);

                return (
                    <Card
                        key={doc.id}
                        className={cn(
                            "cursor-pointer hover:shadow-md transition-all group overflow-hidden relative",
                            isSelected && "ring-2 ring-primary shadow-md"
                        )}
                        onClick={(e) => {
                            // Check if clicking checkbox or its label
                            if ((e.target as HTMLElement).closest('[data-checkbox]')) {
                                e.stopPropagation();
                                onToggleSelection(doc.id);
                            } else {
                                onDocumentClick(doc);
                            }
                        }}
                    >
                        {/* Selection Checkbox */}
                        <div
                            className={cn(
                                "absolute top-2 left-2 z-10 transition-opacity",
                                isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                            )}
                            data-checkbox
                            onClick={(e) => {
                                e.stopPropagation();
                                onToggleSelection(doc.id);
                            }}
                        >
                            <div className={cn(
                                "flex items-center justify-center w-6 h-6 rounded-md bg-background/90 border-2 backdrop-blur shadow-sm cursor-pointer",
                                isSelected ? "border-primary bg-primary" : "border-muted-foreground/30"
                            )}>
                                {isSelected && <CheckCircle2 className="w-4 h-4 text-primary-foreground" />}
                            </div>
                        </div>

                        <div className="aspect-[4/3] bg-muted relative overflow-hidden flex items-center justify-center">
                            {isImg ? (
                                /* eslint-disable-next-line @next/next/no-img-element */
                                <img
                                    src={doc.url}
                                    alt={doc.title}
                                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                                />
                            ) : isPdfFile ? (
                                <div className="relative w-full h-full bg-white">
                                    <iframe
                                        src={`${doc.url}#page=1&view=FitH`}
                                        className="w-full h-full pointer-events-none scale-110"
                                        title={doc.title}
                                    />
                                    <div className="absolute inset-0 pointer-events-none" />
                                </div>
                            ) : (
                                <Icon className="w-16 h-16 text-muted-foreground/50" />
                            )}
                            <div className={cn(
                                "absolute inset-0 transition-colors",
                                isSelected ? "bg-primary/20" : "bg-black/0 group-hover:bg-black/10"
                            )} />
                        </div>
                        <CardContent className="p-3">
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-primary/10 rounded-lg text-primary shrink-0">
                                    <Icon className="w-5 h-5" />
                                </div>
                                <div className="min-w-0">
                                    <h3 className="font-medium truncate text-sm" title={doc.title}>
                                        {doc.title}
                                    </h3>
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="p-3 pt-0 flex justify-between text-xs text-muted-foreground">
                            <span>{new Date(doc.createdAt).toLocaleDateString()}</span>
                            <span>{doc.size}</span>
                        </CardFooter>
                    </Card>
                );
            })}
        </div>
    );
}
