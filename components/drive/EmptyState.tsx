"use client";

import { Upload, FolderPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { CreateFolderDialog } from "./CreateFolderDialog";

interface EmptyStateProps {
    currentFolderId?: number | null;
}

export function EmptyState({ currentFolderId = null }: EmptyStateProps) {
    const [showCreateFolder, setShowCreateFolder] = useState(false);

    return (
        <>
            <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
                <div className="p-6 bg-muted/30 rounded-full">
                    <Upload className="w-12 h-12 text-muted-foreground" />
                </div>
                <div className="text-center space-y-2">
                    <h3 className="text-xl font-semibold">No files yet</h3>
                    <p className="text-muted-foreground max-w-sm">
                        Get started by uploading your first file or creating a folder to organize your documents
                    </p>
                </div>
                <div className="flex gap-3">
                    <Button onClick={() => setShowCreateFolder(true)}>
                        <FolderPlus className="w-4 h-4 mr-2" />
                        Create Folder
                    </Button>
                </div>
            </div>

            <CreateFolderDialog
                open={showCreateFolder}
                onOpenChange={setShowCreateFolder}
                currentFolderId={currentFolderId}
            />
        </>
    );
}
