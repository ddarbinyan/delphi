"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, Clock, Trash2, Cloud, FolderPlus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useUpload } from "@/hooks/useUpload";
import { useCurrentFolder } from "@/contexts/FolderContext";
import { useState } from "react";
import { CreateFolderDialog } from "@/components/drive/CreateFolderDialog";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

export function Sidebar() {
    const pathname = usePathname();
    const { uploadFile } = useUpload();
    const { currentFolderId } = useCurrentFolder();
    const [showCreateFolder, setShowCreateFolder] = useState(false);
    
    // Fetch reminders count (filter out completed ones)
    const { data: reminders } = useQuery({
        queryKey: ["reminders"],
        queryFn: async () => {
            const response = await axios.get("http://localhost:8000/api/v1/reminders");
            return response.data;
        },
    });
    
    const activeRemindersCount = reminders?.filter((r: any) => r.status !== 'completed').length || 0;
    
    const navItems = [
        { icon: LayoutGrid, label: "All Files", href: "/" },
        { icon: Clock, label: "Reminders", href: "/reminders", count: activeRemindersCount },
    ];

    return (
        <>
            <div className="w-64 border-r bg-card h-screen flex flex-col p-4">
                <div className="flex items-center gap-2 px-2 mb-8">
                    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                        <img src="/logo-square.webp" alt="Delphi Logo" className="w-full h-full object-cover" />
                    </div>
                    <span className="font-bold text-xl tracking-tight">Delphi</span>
                </div>

                <div className="px-2 mb-4 space-y-2">
                    <Button
                        className="w-full justify-start gap-2"
                        onClick={() => document.getElementById('file-upload')?.click()}
                    >
                        <Cloud className="w-4 h-4" />
                        Upload File
                    </Button>
                    <Button
                        className="w-full justify-start gap-2"
                        onClick={() => setShowCreateFolder(true)}
                    >
                        <FolderPlus className="w-4 h-4" />
                        New Folder
                    </Button>
                    <input
                        type="file"
                        id="file-upload"
                        className="hidden"
                        onChange={async (e) => {
                            const file = e.target.files?.[0];
                            if (file) {
                                await uploadFile(file, currentFolderId);
                                // Reset input so same file can be selected again
                                e.target.value = '';
                            }
                        }}
                    />
                </div>

            <nav className="flex-1 space-y-1">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link key={item.href} href={item.href}>
                            <Button
                                variant={isActive ? "secondary" : "ghost"}
                                className={cn(
                                    "w-full justify-start gap-3 font-medium",
                                    isActive && "bg-secondary text-secondary-foreground"
                                )}
                            >
                                <item.icon className="w-5 h-5" />
                                {item.label}
                                {item.count !== undefined && item.count > 0 && (
                                    <span className="ml-auto bg-primary/10 text-primary text-xs px-2 py-0.5 rounded-full">
                                        {item.count}
                                    </span>
                                )}
                            </Button>
                        </Link>
                    );
                })}
            </nav>
            </div>
            <CreateFolderDialog
                open={showCreateFolder}
                onOpenChange={setShowCreateFolder}
            />
        </>
    );
}
