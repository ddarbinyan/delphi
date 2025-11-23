import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";

export interface Folder {
    id: string;
    name: string;
    parentId: number | null;
    createdAt: string;
    type: "folder";
}

export function useFolders(parentId: number | null = null) {
    return useQuery({
        queryKey: ["folders", parentId],
        queryFn: async () => {
            const params = parentId !== null ? `?parent_id=${parentId}` : "";
            const { data } = await axios.get<Folder[]>(`http://localhost:8000/api/v1/folders${params}`);
            return data;
        },
    });
}

export function useCreateFolder() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ name, parentId }: { name: string; parentId?: number | null }) => {
            const { data } = await axios.post("http://localhost:8000/api/v1/folders", {
                name,
                parent_id: parentId
            });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["folders"] });
            toast.success("Folder created successfully");
        },
        onError: () => {
            toast.error("Failed to create folder");
        },
    });
}
