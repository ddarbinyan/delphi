"use client";

import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateFolder } from "@/hooks/useFolders";

interface CreateFolderDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    currentFolderId: number | null;
}

export function CreateFolderDialog({ open, onOpenChange, currentFolderId }: CreateFolderDialogProps) {
    const [folderName, setFolderName] = useState("");
    const createFolder = useCreateFolder();

    const handleCreate = async () => {
        if (!folderName.trim()) return;

        await createFolder.mutateAsync({
            name: folderName.trim(),
            parentId: currentFolderId,
        });

        setFolderName("");
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Create New Folder</DialogTitle>
                    <DialogDescription>
                        Enter a name for your new folder.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="name">Folder Name</Label>
                        <Input
                            id="name"
                            placeholder="Enter folder name"
                            value={folderName}
                            onChange={(e) => setFolderName(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    handleCreate();
                                }
                            }}
                            autoFocus
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleCreate} disabled={!folderName.trim() || createFolder.isPending}>
                        {createFolder.isPending ? "Creating..." : "Create Folder"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
