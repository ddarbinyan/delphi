"use client";

import { ChevronRight, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

interface BreadcrumbItem {
    id: number | null;
    name: string;
}

interface BreadcrumbProps {
    path: BreadcrumbItem[];
    onNavigate: (id: number | null) => void;
}

export function Breadcrumb({ path, onNavigate }: BreadcrumbProps) {
    return (
        <div className="flex items-center gap-1 text-sm">
            <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2"
                onClick={() => onNavigate(null)}
            >
                <Home className="w-4 h-4" />
            </Button>

            {path.map((item, index) => {
                const isLast = index === path.length - 1;
                return (
                    <div key={item.id || "root"} className="flex items-center gap-1">
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                        <Button
                            variant="ghost"
                            size="sm"
                            className={cn(
                                "h-8 px-2",
                                isLast ? "font-medium" : "text-muted-foreground"
                            )}
                            onClick={() => !isLast && onNavigate(item.id)}
                            disabled={isLast}
                        >
                            {item.name}
                        </Button>
                    </div>
                );
            })}
        </div>
    );
}

import { cn } from "@/lib/utils";
