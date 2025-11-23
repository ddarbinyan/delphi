import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";

export function useUpload() {
    const queryClient = useQueryClient();

    const uploadFile = async (file: File, folderId: number | null = null) => {
        const toastId = toast.loading("Uploading file...");

        try {
            const formData = new FormData();
            formData.append("file", file);
            if (folderId !== null) {
                formData.append("folder_id", folderId.toString());
            }

            await axios.post("http://localhost:8000/api/v1/ingest", formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });

            toast.dismiss(toastId);
            toast.success("File uploaded successfully");

            queryClient.invalidateQueries({ queryKey: ["documents"] });
        } catch (error) {
            toast.dismiss(toastId);
            toast.error("Failed to upload file");
            console.error("Upload error:", error);
        }
    };

    return { uploadFile };
}
