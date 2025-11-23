import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";

export function useDeleteFolder() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (folderId: string) => {
            await axios.delete(`http://localhost:8000/api/v1/folders/${folderId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["folders"] });
            queryClient.invalidateQueries({ queryKey: ["documents"] });
            toast.success("Folder deleted successfully");
        },
        onError: () => {
            toast.error("Failed to delete folder");
        },
    });
}
