import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";

export function useMoveDocument() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ documentId, targetFolderId }: { documentId: string; targetFolderId: number | null }) => {
            await axios.patch(`http://local0/api/v1/documents/${documentId}/move`, {
                target_folder_id: targetFolderId
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["documents"] });
            toast.success("File moved successfully");
        },
        onError: () => {
            toast.error("Failed to move file");
        },
    });
}
