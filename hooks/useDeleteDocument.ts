import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";

export function useDeleteDocument() {
    const queryClient = useQueryClient();

    const deleteDocument = useCallback(async (documentId: string) => {
        try {
            toast.loading("Deleting document...");

            await axios.delete(`http://localhost:8000/api/v1/documents/${documentId}`);

            toast.dismiss();
            toast.success("Document deleted successfully");

            // Invalidate cache to refresh the list
            queryClient.invalidateQueries({ queryKey: ["documents"] });

            return true;
        } catch (error) {
            toast.dismiss();
            toast.error("Failed to delete document");
            console.error("Delete error:", error);
            return false;
        }
    }, [queryClient]);

    return { deleteDocument };
}
