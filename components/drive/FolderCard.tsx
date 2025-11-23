"use client";

import { Folder, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Folder as FolderType } from "@/hooks/useFolders";

interface FolderCardProps {
    folder: FolderType;
    onClick: () => void;
    isSelected?: boolean;
    onToggleSelection?: (id: string) => void;
}

export function FolderCard({ folder, onClick, isSelected = false, onToggleSelection }: FolderCardProps) {
    return (
        <div
            className={cn(
                "group relative flex items-center gap-3 p-4 rounded-lg border bg-card cursor-pointer hover:shadow-md transition-all",
                isSelected && "ring-2 ring-primary shadow-md"
            )}
            onClick={(e) => {
                if ((e.target as HTMLElement).closest('[data-checkbox]')) {
                    e.stopPropagation();
                    onToggleSelection?.(folder.id);
                } else {
                    onClick();
                }
            }}
            onDoubleClick={onClick}
        >
            {/* Selection Checkbox */}
            {onToggleSelection && (
                <div
                    className={cn(
                        "absolute top-2 right-2 z-10 transition-opacity",
                        isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                    )}
                    data-checkbox
                    onClick={(e) => {
                        e.stopPropagation();
                        onToggleSelection(folder.id);
                    }}
                >
                    <div className={cn(
                        "flex items-center justify-center w-5 h-5 rounded border-2 cursor-pointer bg-background/90 backdrop-blur shadow-sm",
                        isSelected ? "border-primary bg-primary" : "border-muted-foreground/30"
                    )}>
                        {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-primary-foreground" />}
                    </div>
                </div>
            )}

            <div className="p-3 bg-primary/10 rounded-lg text-primary">
                <Folder className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
                <h3 className="font-medium truncate">{folder.name}</h3>
                <p className="text-xs text-muted-foreground">
                    {new Date(folder.createdAt).toLocaleDateString()}
                </p>
            </div>
        </div>
    );
}
