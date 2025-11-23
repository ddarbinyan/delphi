"use client";

import { FileText, Image, FileIcon, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SearchResult } from "@/hooks/useSearch";

interface SearchResultsProps {
    results?: {
        hits: SearchResult[];
        totalHits: number;
        processingTimeMs: number;
    };
    isLoading?: boolean;
    onResultClick: (result: SearchResult) => void;
}

export function SearchResults({ results, isLoading, onResultClick }: SearchResultsProps) {
    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!results || results.hits.length === 0) {
        return (
            <div className="text-center py-12">
                <FileIcon className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-medium mb-2">No results found</h3>
                <p className="text-muted-foreground">
                    Try different keywords or check your spelling
                </p>
            </div>
        );
    }

    const getIcon = (type: string) => {
        if (type === "image") return Image;
        return FileText;
    };

    return (
        <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
                Found {results.totalHits} result{results.totalHits !== 1 ? "s" : ""}
                {results.processingTimeMs ? ` in ${results.processingTimeMs}ms` : ""}
            </div>

            <div className="grid gap-3">
                {results.hits.map((result) => {
                    const Icon = getIcon(result.type);
                    const contentPreview = result.content?.substring(0, 150) || "No content available";

                    return (
                        <Card
                            key={result.id}
                            className="p-4 hover:shadow-md transition-all cursor-pointer"
                            onClick={() => onResultClick(result)}
                        >
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-primary/10 rounded-lg">
                                    <Icon className="w-5 h-5 text-primary" />
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="font-medium truncate">
                                            {result.title}
                                        </h3>
                                        <Badge variant="secondary" className="text-xs">
                                            {result.type}
                                        </Badge>
                                        {result._score > 0 && (
                                            <span className="text-xs text-muted-foreground">
                                                {(result._score * 100).toFixed(0)}% match
                                            </span>
                                        )}
                                    </div>

                                    <p className="text-sm text-muted-foreground line-clamp-2">
                                        {contentPreview}
                                        {result.content && result.content.length > 150 && "..."}
                                    </p>

                                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                        <span>{result.size}</span>
                                        <span>•</span>
                                        <span>
                                            {new Date(result.uploadDate).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
