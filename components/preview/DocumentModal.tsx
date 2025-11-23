"use client";

import { useState, useEffect } from "react";
import { Document } from "@/hooks/useDocuments";
import { useDeleteDocument } from "@/hooks/useDeleteDocument";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, Share2, Trash2, X } from "lucide-react";

interface DocumentModalProps {
    document: Document | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function DocumentModal({ document, open, onOpenChange }: DocumentModalProps) {
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const { deleteDocument } = useDeleteDocument();

    // Handle Escape key to close modal
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape" && open) {
                onOpenChange(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [open, onOpenChange]);

    if (!document) return null;

    const isImage = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase();
        return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '');
    };

    const isPdf = (filename: string) => {
        const ext = filename.split('.').pop()?.toLowerCase();
        return ext === 'pdf';
    };

    const handleDelete = async () => {
        const success = await deleteDocument(document.id);
        if (success) {
            setShowDeleteConfirm(false);
            onOpenChange(false); // Close the modal after successful deletion
        }
    };

    const handleIframeLoad = (e: React.SyntheticEvent<HTMLIFrameElement, Event>) => {
        try {
            const iframe = e.currentTarget;
            const iframeWindow = iframe.contentWindow;
            if (iframeWindow) {
                iframeWindow.addEventListener("keydown", (e: KeyboardEvent) => {
                    if (e.key === "Escape") {
                        onOpenChange(false);
                    }
                });
            }
        } catch (err) {
            // Ignore cross-origin errors if any (though we are proxied now)
            console.log("Could not attach event listener to iframe", err);
        }
    };

    return (
        <>
            <Dialog open={open} onOpenChange={onOpenChange}>
                <DialogContent className="max-w-4xl h-[80vh] p-0 flex flex-col overflow-hidden gap-0">
                    <div className="flex-1 flex overflow-hidden">
                        {/* Left: Preview */}
                        <div className="flex-1 bg-muted/30 flex items-center justify-center p-8 border-r relative">
                            {isImage(document.title) ? (
                                /* eslint-disable-next-line @next/next/no-img-element */
                                <img
                                    src={document.url}
                                    alt={document.title}
                                    className="max-w-full max-h-full object-contain shadow-lg rounded-md"
                                />
                            ) : isPdf(document.title) ? (
                                <iframe
                                    src={document.url}
                                    className="w-full h-full shadow-lg rounded-md bg-white"
                                    title={document.title}
                                    onLoad={handleIframeLoad}
                                />
                            ) : (
                                <div className="text-center p-8 bg-background rounded-lg shadow border">
                                    <p className="text-muted-foreground">Preview not available</p>
                                    <Button variant="outline" className="mt-4" onClick={() => window.open(document.url, '_blank')}>
                                        Download to view
                                    </Button>
                                </div>
                            )}
                        </div>

                        {/* Right: Metadata */}
                        <div className="w-80 bg-background flex flex-col">
                            <DialogHeader className="p-6 pb-2 border-b">
                                <div className="flex items-start justify-between gap-4">
                                    <DialogTitle className="text-lg font-semibold leading-tight">
                                        {document.title}
                                    </DialogTitle>
                                </div>
                                <div className="flex gap-2 mt-2">
                                    <Badge variant="secondary" className="capitalize">
                                        {document.type}
                                    </Badge>
                                    <Badge variant="outline">{document.size}</Badge>
                                </div>
                            </DialogHeader>

                            <ScrollArea className="flex-1 p-6">
                                <div className="space-y-6">
                                    <div>
                                        <h4 className="text-sm font-medium text-muted-foreground mb-2">
                                            Summary
                                        </h4>
                                        <p className="text-sm leading-relaxed">{document.summary}</p>
                                    </div>

                                    <div className="space-y-4">
                                        <div>
                                            <h4 className="text-sm font-medium text-muted-foreground mb-1">
                                                Sender
                                            </h4>
                                            <p className="text-sm font-medium">{document.sender}</p>
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-medium text-muted-foreground mb-1">
                                                Date
                                            </h4>
                                            <p className="text-sm font-medium">
                                                {new Date(document.createdAt).toLocaleDateString(undefined, {
                                                    weekday: "long",
                                                    year: "numeric",
                                                    month: "long",
                                                    day: "numeric",
                                                })}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                                        <h4 className="text-sm font-medium">Extracted Data</h4>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Amount</span>
                                            <span className="font-mono font-medium">$1,250.00</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Due Date</span>
                                            <span className="font-medium">Nov 30, 2023</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Invoice #</span>
                                            <span className="font-mono text-xs">INV-2023-001</span>
                                        </div>
                                    </div>
                                </div>
                            </ScrollArea>

                            <div className="p-4 border-t bg-muted/10 flex gap-2">
                                <Button className="flex-1" variant="outline" onClick={() => window.open(document.url, '_blank')}>
                                    <Download className="w-4 h-4 mr-2" />
                                    Download
                                </Button>
                                <Button variant="ghost" size="icon">
                                    <Share2 className="w-4 h-4" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="text-destructive hover:bg-destructive/10"
                                    onClick={() => setShowDeleteConfirm(true)}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>

            <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Document</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete "{document.title}"? This action cannot be undone.
                            The file will be permanently removed from all databases.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
