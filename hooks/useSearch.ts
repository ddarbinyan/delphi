import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useState, useEffect } from "react";

export interface SearchResult {
    id: string;
    title: string;
    url: string;
    type: string;
    size: string;
    sender: string;
    summary: string;
    uploadDate: string;
    parentFolderId: number | null;
    content: string;
    _score: number;
    _semanticScore: number;
}

export interface SearchResponse {
    hits: SearchResult[];
    totalHits: number;
    processingTimeMs: number;
    query: string;
    semanticRatio: number;
}

export function useSearch(
    query: string,
    semanticRatio: number = 0.0,
    filters?: { folderId?: number; type?: string }
) {
    // Debounce query to avoid excessive API calls
    const [debouncedQuery, setDebouncedQuery] = useState(query);

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedQuery(query), 300);
        return () => clearTimeout(timer);
    }, [query]);

    return useQuery<SearchResponse>({
        queryKey: ["search", debouncedQuery, semanticRatio, filters],
        queryFn: async () => {
            if (!debouncedQuery || debouncedQuery.length < 2) {
                return {
                    hits: [],
                    totalHits: 0,
                    processingTimeMs: 0,
                    query: debouncedQuery,
                    semanticRatio
                };
            }

            const params: any = {
                q: debouncedQuery,
                semantic_ratio: semanticRatio,
                limit: 20
            };

            if (filters?.folderId !== undefined) {
                params.folder_id = filters.folderId;
            }
            if (filters?.type) {
                params.type = filters.type;
            }

            const { data } = await axios.get<SearchResponse>(
                "http://localhost:8000/api/v1/search",
                { params }
            );

            return data;
        },
        enabled: debouncedQuery.length >= 2,
        staleTime: 60000, // 1 minute
    });
}
