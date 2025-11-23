"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Sparkles, FileText, ExternalLink, Eye } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useChat, Citation } from "@/hooks/useChat";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    citations?: Citation[];
}

export function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "1",
            role: "assistant",
            content: "Hi! I'm Delphi. How can I help you with your documents today?",
        },
    ]);
    const [inputValue, setInputValue] = useState("");
    const [previewCitation, setPreviewCitation] = useState<Citation | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const chatMutation = useChat();

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages]);

    // Handle ESC key to close chat widget or preview modal
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                if (previewCitation) {
                    setPreviewCitation(null);
                } else if (isOpen) {
                    setIsOpen(false);
                }
            }
        };

        document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, [isOpen, previewCitation]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || chatMutation.isPending) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: inputValue,
        };

        setMessages((prev) => [...prev, userMessage]);
        const queryText = inputValue;
        setInputValue("");

        try {
            const response = await chatMutation.mutateAsync({
                message: queryText,
                semantic_ratio: 0.7,  // Higher semantic search for better concept matching
                limit: 10,  // More documents for comprehensive answers
            });

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: response.answer,
                citations: response.citations,
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "Sorry, I encountered an error while processing your request. Please try again.",
            };
            setMessages((prev) => [...prev, errorMessage]);
        }
    };

    return (
        <>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="fixed bottom-24 right-6 w-[420px] max-h-[600px] h-[85vh] bg-card border rounded-2xl shadow-2xl flex flex-col z-50"
                    >
                        {/* Header */}
                        <div className="p-4 border-b bg-primary text-primary-foreground flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                    <Sparkles className="w-4 h-4" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-sm">Delphi AI</h3>
                                    <p className="text-xs text-primary-foreground/80">
                                        Always here to help
                                    </p>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="text-primary-foreground hover:bg-white/20"
                                onClick={() => setIsOpen(false)}
                            >
                                <X className="w-5 h-5" />
                            </Button>
                        </div>

                        {/* Messages */}
                        <ScrollArea className="flex-1 p-4 overflow-y-auto">
                            <div className="space-y-4 pb-4">
                                {messages.map((message) => (
                                    <div
                                        key={message.id}
                                        className={cn(
                                            "flex gap-2 w-full",
                                            message.role === "user" ? "justify-end" : "justify-start"
                                        )}
                                    >
                                        {message.role === "assistant" && (
                                            <Avatar className="w-7 h-7 shrink-0 mt-0.5">
                                                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                                                    AI
                                                </AvatarFallback>
                                            </Avatar>
                                        )}
                                        <div className={cn(
                                            "flex flex-col gap-2 max-w-[85%]",
                                            message.role === "user" ? "items-end" : "items-start"
                                        )}>
                                            <div
                                                className={cn(
                                                    "p-3 rounded-2xl text-sm break-words",
                                                    message.role === "user"
                                                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                                                        : "bg-muted rounded-tl-sm"
                                                )}
                                            >
                                                <p className="whitespace-pre-wrap">{message.content}</p>
                                            </div>
                                            {message.citations && message.citations.length > 0 && (
                                                <div className="flex flex-col gap-1.5 w-full">
                                                    <p className="text-xs text-muted-foreground font-medium px-1">
                                                        📎 {message.citations.length} {message.citations.length === 1 ? 'source' : 'sources'}
                                                    </p>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {message.citations.map((citation) => (
                                                            <TooltipProvider key={citation.id}>
                                                                <Tooltip delayDuration={200}>
                                                                    <TooltipTrigger asChild>
                                                                        <button
                                                                            onClick={() => {
                                                                                console.log('Citation clicked:', citation);
                                                                                setPreviewCitation(citation);
                                                                            }}
                                                                            className="flex items-center gap-1.5 px-2 py-1.5 bg-background border rounded-lg hover:bg-accent transition-colors text-xs group"
                                                                        >
                                                                            <FileText className="w-3 h-3 text-primary shrink-0" />
                                                                            <span className="font-medium truncate max-w-[120px]">
                                                                                {citation.title || 'Unknown'}
                                                                            </span>
                                                                            <Eye className="w-3 h-3 text-muted-foreground group-hover:text-primary shrink-0" />
                                                                        </button>
                                                                    </TooltipTrigger>
                                                                    <TooltipContent side="top" className="max-w-xs">
                                                                        <div className="space-y-1">
                                                                            <p className="font-semibold text-xs">{citation.title || 'Unknown'}</p>
                                                                            {citation.summary && (
                                                                                <p className="text-xs text-muted-foreground">
                                                                                    {citation.summary.slice(0, 100)}...
                                                                                </p>
                                                                            )}
                                                                            <Badge variant="secondary" className="text-xs">
                                                                                {citation.type || 'document'}
                                                                            </Badge>
                                                                        </div>
                                                                    </TooltipContent>
                                                                </Tooltip>
                                                            </TooltipProvider>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        {message.role === "user" && (
                                            <Avatar className="w-7 h-7 shrink-0 mt-0.5">
                                                <AvatarFallback className="text-xs">ME</AvatarFallback>
                                            </Avatar>
                                        )}
                                    </div>
                                ))}
                                {chatMutation.isPending && (
                                    <div className="flex gap-3 max-w-[85%]">
                                        <Avatar className="w-8 h-8 shrink-0">
                                            <AvatarFallback className="bg-primary text-primary-foreground">
                                                AI
                                            </AvatarFallback>
                                        </Avatar>
                                        <div className="bg-muted p-3 rounded-2xl rounded-tl-none flex items-center gap-1">
                                            <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                            <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                            <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                        </div>
                                    </div>
                                )}
                                <div ref={scrollRef} />
                            </div>
                        </ScrollArea>

                        {/* Input */}
                        <div className="p-4 border-t bg-background/95 backdrop-blur-sm">
                            <form onSubmit={handleSubmit} className="flex gap-2">
                                <Input
                                    placeholder="Ask about your documents..."
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    disabled={chatMutation.isPending}
                                    className="flex-1"
                                    autoComplete="off"
                                />
                                <Button 
                                    type="submit" 
                                    size="icon" 
                                    disabled={!inputValue.trim() || chatMutation.isPending}
                                    className="shrink-0"
                                >
                                    <Send className="w-4 h-4" />
                                </Button>
                            </form>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Citation Preview Modal */}
            <AnimatePresence>
                {previewCitation && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4"
                        onClick={() => setPreviewCitation(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="bg-card border rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Modal Header */}
                            <div className="p-4 border-b bg-muted/50 flex items-center justify-between">
                                <div className="flex items-center gap-3 min-w-0 flex-1">
                                    <div className="p-2 bg-primary/10 rounded-lg">
                                        <FileText className="w-5 h-5 text-primary" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <h3 className="font-semibold text-sm truncate">
                                            {previewCitation.title}
                                        </h3>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <Badge variant="secondary" className="text-xs">
                                                {previewCitation.type}
                                            </Badge>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 shrink-0">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => window.open(previewCitation.url, '_blank')}
                                    >
                                        <ExternalLink className="w-4 h-4 mr-2" />
                                        Open
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setPreviewCitation(null)}
                                    >
                                        <X className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>

                            {/* Modal Content */}
                            <div className="flex-1 overflow-auto p-6">
                                {previewCitation.summary && (
                                    <div className="mb-4 p-4 bg-muted/50 rounded-lg">
                                        <h4 className="text-sm font-medium mb-2">Summary</h4>
                                        <p className="text-sm text-muted-foreground leading-relaxed">
                                            {previewCitation.summary}
                                        </p>
                                    </div>
                                )}
                                
                                {/* Preview iframe for documents */}
                                <div className="bg-muted/30 rounded-lg overflow-hidden" style={{ height: '500px' }}>
                                    {previewCitation.url && previewCitation.url.toLowerCase().endsWith('.pdf') ? (
                                        <iframe
                                            src={previewCitation.url}
                                            className="w-full h-full border-0"
                                            title={previewCitation.title || 'Document preview'}
                                            onError={(e) => {
                                                console.error('Failed to load PDF:', e);
                                            }}
                                        />
                                    ) : previewCitation.url && (previewCitation.type === 'image' || /\.(jpg|jpeg|png|gif|webp)$/i.test(previewCitation.url)) ? (
                                        <div className="w-full h-full flex items-center justify-center p-4">
                                            <img 
                                                src={previewCitation.url} 
                                                alt={previewCitation.title || 'Image'}
                                                className="max-w-full max-h-full object-contain"
                                                onError={(e) => {
                                                    console.error('Failed to load image:', e);
                                                }}
                                            />
                                        </div>
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center">
                                            <div className="text-center p-8">
                                                <FileText className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                                                <p className="text-sm text-muted-foreground mb-4">
                                                    {previewCitation.url 
                                                        ? 'Preview not available for this file type'
                                                        : 'No preview URL available'}
                                                </p>
                                                {previewCitation.url && (
                                                    <Button
                                                        variant="outline"
                                                        onClick={() => window.open(previewCitation.url, '_blank')}
                                                    >
                                                        <ExternalLink className="w-4 h-4 mr-2" />
                                                        Open in new tab
                                                    </Button>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="fixed bottom-6 right-6 z-50"
            >
                <Button
                    size="lg"
                    className={cn(
                        "h-14 w-14 rounded-full shadow-lg transition-all duration-300",
                        isOpen ? "rotate-90 scale-0 opacity-0" : "scale-100 opacity-100"
                    )}
                    onClick={() => setIsOpen(true)}
                >
                    <MessageSquare className="w-6 h-6" />
                </Button>
            </motion.div>
        </>
    );
}
