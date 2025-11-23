"use client";

import { Document } from "@/hooks/useDocuments";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
import { FileText, Image as ImageIcon, FileCode, Receipt, File, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileListProps {
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

export function FileList({ documents, onDocumentClick, selectedIds, onToggleSelection }: FileListProps) {
    return (
        <div className="rounded-md border bg-card">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-12"></TableHead>
                        <TableHead className="w-[40%]">Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="text-right">Size</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {documents.map((doc) => {
                        const Icon = getIcon(doc.type);
                        const isSelected = selectedIds.has(doc.id);

                        return (
                            <TableRow
                                key={doc.id}
                                className={cn(
                                    "cursor-pointer hover:bg-muted/50 transition-colors",
                                    isSelected && "bg-primary/10"
                                )}
                                onClick={(e) => {
                                    if ((e.target as HTMLElement).closest('[data-checkbox]')) {
                                        e.stopPropagation();
                                        onToggleSelection(doc.id);
                                    } else {
                                        onDocumentClick(doc);
                                    }
                                }}
                            >
                                <TableCell>
                                    <div
                                        className="flex items-center justify-center"
                                        data-checkbox
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onToggleSelection(doc.id);
                                        }}
                                    >
                                        <div className={cn(
                                            "flex items-center justify-center w-5 h-5 rounded border-2 transition-all cursor-pointer",
                                            isSelected ? "bg-primary border-primary" : "border-muted-foreground/30 hover:border-primary/50"
                                        )}>
                                            {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-primary-foreground" />}
                                        </div>
                                    </div>
                                </TableCell>
                                <TableCell>
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                            <Icon className="w-4 h-4" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-sm">{doc.title}</p>
                                            <p className="text-xs text-muted-foreground">{doc.sender}</p>
                                        </div>
                                    </div>
                                </TableCell>
                                <TableCell className="capitalize text-sm">{doc.type}</TableCell>
                                <TableCell className="text-sm">
                                    {new Date(doc.createdAt).toLocaleDateString()}
                                </TableCell>
                                <TableCell className="text-right text-sm font-mono">
                                    {doc.size}
                                </TableCell>
                            </TableRow>
                        );
                    })}
                </TableBody>
            </Table>
        </div>
    );
}
