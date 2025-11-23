"use client";

import { useState, useEffect } from "react";
import { LayoutGrid, List as ListIcon, Loader2, CheckSquare, Square, Trash2, X, FolderPlus, FolderInput } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocuments, Document } from "@/hooks/useDocuments";
import { useFolders, Folder } from "@/hooks/useFolders";
import { useDeleteDocument } from "@/hooks/useDeleteDocument";
import { useDeleteFolder } from "@/hooks/useDeleteFolder";
import { useMoveDocument } from "@/hooks/useMoveDocument";
import { useCurrentFolder } from "@/contexts/FolderContext";
import { FileGrid } from "@/components/drive/FileGrid";
import { FileList } from "@/components/drive/FileList";
import { EmptyState } from "@/components/drive/EmptyState";
import { DocumentModal } from "@/components/preview/DocumentModal";
import { FolderCard } from "@/components/drive/FolderCard";
import { Breadcrumb } from "@/components/drive/Breadcrumb";
import { CreateFolderDialog } from "@/components/drive/CreateFolderDialog";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { useSearch } from "@/hooks/useSearch";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
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

interface BreadcrumbItem {
    id: number | null;
    name: string;
}

export default function DrivePage() {
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
    const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [breadcrumbPath, setBreadcrumbPath] = useState<BreadcrumbItem[]>([]);
    const [showCreateFolder, setShowCreateFolder] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    const { currentFolderId, setCurrentFolderId } = useCurrentFolder();
    const { data: documents, isLoading: docsLoading } = useDocuments(currentFolderId);
    const { data: folders, isLoading: foldersLoading } = useFolders(currentFolderId);
    const { data: allFolders } = useFolders(null); // Get all root folders for move dropdown
    const { deleteDocument } = useDeleteDocument();
    const deleteFolder = useDeleteFolder();
    const moveDocument = useMoveDocument();
    const { data: searchResults, isLoading: searchLoading } = useSearch(searchQuery, 0.0); // Keyword search only

    const isLoading = docsLoading || foldersLoading;
    const showSearch = searchQuery.length >= 2;

    const toggleSelection = (id: string) => {
        setSelectedIds(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    const selectAll = () => {
        if (documents) {
            setSelectedIds(new Set(documents.map(doc => doc.id)));
        }
    };

    const clearSelection = () => {
        setSelectedIds(new Set());
    };

    const handleBulkDelete = async () => {
        for (const id of selectedIds) {
            // Check if it's a folder (starts with 'folder-') or a document
            if (id.startsWith('folder-')) {
                const folderId = id.replace('folder-', '');
                await deleteFolder.mutateAsync(folderId);
            } else {
                await deleteDocument(id);
            }
        }
        setSelectedIds(new Set());
        setShowDeleteConfirm(false);
    };

    const handleMoveToFolder = async (targetFolderId: string) => {
        const targetId = targetFolderId === "root" ? null : Number(targetFolderId);

        for (const id of selectedIds) {
            await moveDocument.mutateAsync({
                documentId: id,
                targetFolderId: targetId
            });
        }

        clearSelection();
    };

    const handleFolderClick = (folder: Folder) => {
        setCurrentFolderId(Number(folder.id));
        setBreadcrumbPath([...breadcrumbPath, { id: Number(folder.id), name: folder.name }]);
    };

    const handleBreadcrumbNavigate = (folderId: number | null) => {
        setCurrentFolderId(folderId);
        if (folderId === null) {
            setBreadcrumbPath([]);
        } else {
            const index = breadcrumbPath.findIndex(item => item.id === folderId);
            if (index !== -1) {
                setBreadcrumbPath(breadcrumbPath.slice(0, index + 1));
            }
        }
    };

    if (isLoading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    const isEmpty = (!documents || documents.length === 0) && (!folders || folders.length === 0);

    // If empty and searching, don't show empty state
    if (isEmpty && currentFolderId === null && !showSearch) {
        return (
            <div className="space-y-6">
                {/* Search Bar - always visible */}
                <div className="flex justify-center">
                    <SearchBar value={searchQuery} onChange={setSearchQuery} />
                </div>

                {searchQuery.length >= 2 ? (
                    <SearchResults
                        results={searchResults}
                        isLoading={searchLoading}
                        onResultClick={(result) => {
                            // Try to find in current documents first
                            let doc = documents?.find(d => d.id === result.id);

                            // If not found (e.g. from another folder), construct it from result
                            if (!doc) {
                                doc = {
                                    id: result.id,
                                    title: result.title,
                                    type: result.type as any,
                                    sender: result.sender || "Unknown",
                                    summary: result.summary || (result.content ? result.content.substring(0, 200) + "..." : "No content preview"),
                                    url: result.url,
                                    createdAt: result.uploadDate,
                                    size: result.size
                                };
                            }

                            setSelectedDoc(doc);
                        }}
                    />
                ) : (
                    <EmptyState currentFolderId={currentFolderId} />
                )}

                {/* Document Preview Modal for search results */}
                <DocumentModal
                    document={selectedDoc}
                    open={selectedDoc !== null}
                    onOpenChange={(open) => !open && setSelectedDoc(null)}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                    <h1 className="text-2xl font-bold tracking-tight">
                        {breadcrumbPath.length > 0 ? breadcrumbPath[breadcrumbPath.length - 1].name : "All Files"}
                    </h1>
                    {breadcrumbPath.length > 0 && (
                        <Breadcrumb path={breadcrumbPath} onNavigate={handleBreadcrumbNavigate} />
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowCreateFolder(true)}
                    >
                        <FolderPlus className="w-4 h-4 mr-2" />
                        New Folder
                    </Button>
                    <div className="flex items-center gap-2 bg-card p-1 rounded-lg border">
                        <Button
                            variant={viewMode === "grid" ? "secondary" : "ghost"}
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setViewMode("grid")}
                        >
                            <LayoutGrid className="w-4 h-4" />
                        </Button>
                        <Button
                            variant={viewMode === "list" ? "secondary" : "ghost"}
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => setViewMode("list")}
                        >
                            <ListIcon className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </div>

            {/* Search Bar */}
            <div className="flex justify-center">
                <SearchBar value={searchQuery} onChange={setSearchQuery} />
            </div>

            {/* Show search results or normal browse view */}
            {showSearch ? (
                <SearchResults
                    results={searchResults}
                    isLoading={searchLoading}
                    onResultClick={(result) => {
                        // Try to find in current documents first
                        let doc = documents?.find(d => d.id === result.id);

                        // If not found (e.g. from another folder), construct it from result
                        if (!doc) {
                            doc = {
                                id: result.id,
                                title: result.title,
                                type: result.type as any,
                                sender: result.sender || "Unknown",
                                summary: result.summary || (result.content ? result.content.substring(0, 200) + "..." : "No content preview"),
                                url: result.url,
                                createdAt: result.uploadDate,
                                size: result.size
                            };
                        }

                        setSelectedDoc(doc);
                    }}
                />
            ) : (
                <>
                    {/* Selection Toolbar */}
                    {selectedIds.size > 0 && (
                        <div className="flex items-center gap-4 bg-primary/10 border border-primary/20 rounded-lg px-4 py-3 animate-in fade-in slide-in-from-top-2">
                            <div className="flex items-center gap-2 flex-1">
                                <CheckSquare className="w-5 h-5 text-primary" />
                                <span className="font-medium">{selectedIds.size} selected</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Select onValueChange={handleMoveToFolder}>
                                    <SelectTrigger className="w-[180px] h-9">
                                        <FolderInput className="w-4 h-4 mr-2" />
                                        <SelectValue placeholder="Move to..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="root">📁 Root Folder</SelectItem>
                                        {allFolders && allFolders.map((folder) => (
                                            <SelectItem key={folder.id} value={folder.id}>
                                                📁 {folder.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={selectAll}
                                >
                                    <CheckSquare className="w-4 h-4 mr-2" />
                                    Select All
                                </Button>
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={clearSelection}
                                >
                                    <X className="w-4 h-4 mr-2" />
                                    Clear
                                </Button>
                                <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => setShowDeleteConfirm(true)}
                                >
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Delete ({selectedIds.size})
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Folders Section */}
                    {folders && folders.length > 0 && viewMode === "grid" && (
                        <div>
                            <h2 className="text-sm font-medium text-muted-foreground mb-3">Folders</h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                {folders.map((folder) => (
                                    <FolderCard
                                        key={folder.id}
                                        folder={folder}
                                        onClick={() => handleFolderClick(folder)}
                                        isSelected={selectedIds.has(`folder-${folder.id}`)}
                                        onToggleSelection={(id) => toggleSelection(`folder-${id}`)}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Files Section */}
                    {documents && documents.length > 0 && (
                        <div>
                            {folders && folders.length > 0 && viewMode === "grid" && (
                                <h2 className="text-sm font-medium text-muted-foreground mb-3">Files</h2>
                            )}
                            {viewMode === "grid" ? (
                                <FileGrid
                                    documents={documents}
                                    onDocumentClick={setSelectedDoc}
                                    selectedIds={selectedIds}
                                    onToggleSelection={toggleSelection}
                                />
                            ) : (
                                <FileList
                                    documents={documents}
                                    onDocumentClick={setSelectedDoc}
                                    selectedIds={selectedIds}
                                    onToggleSelection={toggleSelection}
                                />
                            )}
                        </div>
                    )}

                    {isEmpty && currentFolderId !== null && (
                        <div className="text-center py-12 text-muted-foreground">
                            <p>This folder is empty</p>
                        </div>
                    )}

                    <DocumentModal
                        document={selectedDoc}
                        open={!!selectedDoc}
                        onOpenChange={(open) => !open && setSelectedDoc(null)}
                    />

                    <CreateFolderDialog
                        open={showCreateFolder}
                        onOpenChange={setShowCreateFolder}
                        currentFolderId={currentFolderId}
                    />

                    <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
                        <AlertDialogContent>
                            <AlertDialogHeader>
                                <AlertDialogTitle>Delete {selectedIds.size} {selectedIds.size === 1 ? 'Document' : 'Documents'}</AlertDialogTitle>
                                <AlertDialogDescription>
                                    Are you sure you want to delete {selectedIds.size} {selectedIds.size === 1 ? 'document' : 'documents'}?
                                    This action cannot be undone. The files will be permanently removed from all databases.
                                </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                    onClick={handleBulkDelete}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                    Delete
                                </AlertDialogAction>
                            </AlertDialogFooter>
                        </AlertDialogContent>
                    </AlertDialog>
                </>
            )}

            {/* Document Preview Modal */}
            <DocumentModal
                document={selectedDoc}
                open={selectedDoc !== null}
                onOpenChange={(open) => !open && setSelectedDoc(null)}
            />

            {/* Create Folder Dialog */}
            <CreateFolderDialog
                open={showCreateFolder}
                onOpenChange={setShowCreateFolder}
                currentFolderId={currentFolderId}
            />
        </div>
    );
}
