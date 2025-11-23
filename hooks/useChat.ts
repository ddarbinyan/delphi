import { useMutation } from "@tanstack/react-query";
import axios from "axios";

export interface Citation {
    id: number;
    title: string;
    type: string;
    url: string;
    summary: string;
}

export interface ChatResponse {
    answer: string;
    citations: Citation[];
    documentsFound: number;
}

export interface ChatRequest {
    message: string;
    semantic_ratio?: number;
    limit?: number;
}

export function useChat() {
    return useMutation({
        mutationFn: async (request: ChatRequest): Promise<ChatResponse> => {
            const { data } = await axios.post<ChatResponse>(
                "http://localhost:8000/api/v1/chat",
                request
            );
            return data;
        },
    });
}
