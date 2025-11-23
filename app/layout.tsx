import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { Toaster } from "@/components/ui/sonner";
import { FolderProvider } from "@/contexts/FolderContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Delphi - AI-Powered Personal Drive",
    description: "Your intelligent document management system",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <QueryProvider>
                    <FolderProvider>
                        <div className="flex h-screen bg-background">
                            <Sidebar />
                            <main className="flex-1 overflow-y-auto p-8">
                                {children}
                            </main>
                        </div>
                        <Toaster />
                    </FolderProvider>
                </QueryProvider>
            </body>
        </html>
    );
}
