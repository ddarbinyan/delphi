import { useQuery } from "@tanstack/react-query";
import axios from "axios";

export interface Document {
    id: string;
    title: string;
    type: 'invoice' | 'letter' | 'receipt' | 'contract' | 'image' | 'document';
    sender: string;
    summary: string;
    url: string;
    createdAt: string;
    size: string;
}

const MOCK_DOCUMENTS: Document[] = [
    {
        id: "1",
        title: "Q4 Financial Report",
        type: "invoice",
        sender: "Acme Corp",
        summary: "Quarterly financial summary showing 15% growth in revenue.",
        url: "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&q=80&w=300&h=400",
        createdAt: "2023-11-15T10:00:00Z",
        size: "2.4 MB"
    },
    {
        id: "2",
        title: "Lease Agreement",
        type: "contract",
        sender: "Real Estate Co",
        summary: "Signed lease agreement for the new office space.",
        url: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&q=80&w=300&h=400",
        createdAt: "2023-11-10T14:30:00Z",
        size: "1.1 MB"
    },
    {
        id: "3",
        title: "Team Lunch Receipt",
        type: "receipt",
        sender: "The Burger Joint",
        summary: "Receipt for team lunch on Friday.",
        url: "https://images.unsplash.com/photo-1554224154-26032ffc0d07?auto=format&fit=crop&q=80&w=300&h=400",
        createdAt: "2023-11-18T12:45:00Z",
        size: "450 KB"
    },
    {
        id: "4",
        title: "Project Proposal",
        type: "letter",
        sender: "Client X",
        summary: "Proposal for the new marketing campaign.",
        url: "https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&q=80&w=300&h=400",
        createdAt: "2023-11-20T09:15:00Z",
        size: "3.2 MB"
    },
    {
        id: "5",
        title: "Server Logs",
        type: "image",
        sender: "System",
        summary: "Screenshot of server error logs.",
        url: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=300&h=400",
        createdAt: "2023-11-21T16:20:00Z",
        size: "890 KB"
    }
];

export function useDocuments(folderId: number | null = null) {
    return useQuery({
        queryKey: ["documents", folderId],
        queryFn: async () => {
            console.log("Fetching documents...")
            const params = folderId !== null ? `?folder_id=${folderId}` : "";
            const { data } = await axios.get<Document[]>(`http://localhost:8000/api/v1/documents${params}`);
            console.log(data)
            return data;
        },
    });
}
