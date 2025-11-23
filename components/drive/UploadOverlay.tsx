"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud } from "lucide-react";
import { useUpload } from "@/hooks/useUpload";

export function UploadOverlay() {
    const { uploadFile } = useUpload();

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        if (acceptedFiles.length === 0) return;
        await uploadFile(acceptedFiles[0]);
    }, [uploadFile]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        noClick: true,
        noKeyboard: true,
    });

    if (!isDragActive) return null;

    return (
        <div
            {...getRootProps()}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center"
        >
            <input {...getInputProps()} />
            <div className="bg-card p-10 rounded-xl shadow-2xl border-2 border-dashed border-primary flex flex-col items-center animate-in fade-in zoom-in duration-300">
                <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mb-6">
                    <UploadCloud className="w-10 h-10 text-primary animate-bounce" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Drop files to upload</h2>
                <p className="text-muted-foreground">
                    Release your files here to add them to your drive
                </p>
            </div>
        </div>
    );
}
