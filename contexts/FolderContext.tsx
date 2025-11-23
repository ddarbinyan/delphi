"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface FolderContextType {
    currentFolderId: number | null;
    setCurrentFolderId: (id: number | null) => void;
}

const FolderContext = createContext<FolderContextType | undefined>(undefined);

export function FolderProvider({ children }: { children: ReactNode }) {
    const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);

    return (
        <FolderContext.Provider value={{ currentFolderId, setCurrentFolderId }}>
            {children}
        </FolderContext.Provider>
    );
}

export function useCurrentFolder() {
    const context = useContext(FolderContext);
    if (context === undefined) {
        throw new Error("useCurrentFolder must be used within a FolderProvider");
    }
    return context;
}
