"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Sparkles } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
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
    const [isTyping, setIsTyping] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: inputValue,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInputValue("");
        setIsTyping(true);

        // Simulate API call
        setTimeout(() => {
            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "I can help you find that document. Searching through your files...",
            };
            setMessages((prev) => [...prev, aiMessage]);
            setIsTyping(false);
        }, 1500);
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
                        className="fixed bottom-24 right-6 w-96 h-[500px] bg-card border rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50"
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
                        <ScrollArea className="flex-1 p-4">
                            <div className="space-y-4">
                                {messages.map((message) => (
                                    <div
                                        key={message.id}
                                        className={cn(
                                            "flex gap-3 max-w-[85%]",
                                            message.role === "user" ? "ml-auto flex-row-reverse" : ""
                                        )}
                                    >
                                        <Avatar className="w-8 h-8 shrink-0">
                                            {message.role === "assistant" ? (
                                                <>
                                                    <AvatarImage src="/bot-avatar.png" />
                                                    <AvatarFallback className="bg-primary text-primary-foreground">
                                                        AI
                                                    </AvatarFallback>
                                                </>
                                            ) : (
                                                <>
                                                    <AvatarImage src="https://github.com/shadcn.png" />
                                                    <AvatarFallback>ME</AvatarFallback>
                                                </>
                                            )}
                                        </Avatar>
                                        <div
                                            className={cn(
                                                "p-3 rounded-2xl text-sm",
                                                message.role === "user"
                                                    ? "bg-primary text-primary-foreground rounded-tr-none"
                                                    : "bg-muted rounded-tl-none"
                                            )}
                                        >
                                            {message.content}
                                        </div>
                                    </div>
                                ))}
                                {isTyping && (
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
                        <div className="p-4 border-t bg-background">
                            <form onSubmit={handleSubmit} className="flex gap-2">
                                <Input
                                    placeholder="Ask anything..."
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    className="flex-1"
                                />
                                <Button type="submit" size="icon" disabled={!inputValue.trim() || isTyping}>
                                    <Send className="w-4 h-4" />
                                </Button>
                            </form>
                        </div>
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
