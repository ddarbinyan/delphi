"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Calendar, Clock, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";

interface Reminder {
    id: number;
    documentId: number;
    title: string;
    description: string;
    dueDate: string;
    category: string;
    status: string;
    createdAt: string;
    filename: string;
    documentType: string;
}

export default function RemindersPage() {
    const queryClient = useQueryClient();
    
    const { data: reminders, isLoading } = useQuery<Reminder[]>({
        queryKey: ["reminders"],
        queryFn: async () => {
            const response = await axios.get("http://localhost:8000/api/v1/reminders");
            return response.data;
        },
    });

    const completeReminderMutation = useMutation({
        mutationFn: async (reminderId: number) => {
            await axios.patch(`http://localhost:8000/api/v1/reminders/${reminderId}/complete`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["reminders"] });
        },
    });

    const getCategoryColor = (category: string) => {
        const colors: Record<string, string> = {
            bill: "bg-red-500/10 text-red-500 border-red-500/20",
            payment: "bg-red-500/10 text-red-500 border-red-500/20",
            subscription: "bg-blue-500/10 text-blue-500 border-blue-500/20",
            renewal: "bg-blue-500/10 text-blue-500 border-blue-500/20",
            appointment: "bg-green-500/10 text-green-500 border-green-500/20",
            deadline: "bg-orange-500/10 text-orange-500 border-orange-500/20",
            other: "bg-gray-500/10 text-gray-500 border-gray-500/20",
        };
        return colors[category] || colors.other;
    };

    const getDaysUntilDue = (dueDate: string) => {
        const due = new Date(dueDate);
        const today = new Date();
        const diffTime = due.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    };

    const getUrgencyLabel = (daysUntil: number) => {
        if (daysUntil < 0) return { label: "Overdue", color: "text-red-600" };
        if (daysUntil === 0) return { label: "Due Today", color: "text-red-600" };
        if (daysUntil === 1) return { label: "Due Tomorrow", color: "text-orange-600" };
        if (daysUntil <= 7) return { label: `${daysUntil} days left`, color: "text-orange-600" };
        return { label: `${daysUntil} days left`, color: "text-muted-foreground" };
    };

    if (isLoading) {
        return (
            <div className="p-8 space-y-4">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Reminders</h1>
                    <p className="text-muted-foreground">Upcoming actions and deadlines</p>
                </div>
                <div className="grid gap-4">
                    {[1, 2, 3].map((i) => (
                        <Card key={i}>
                            <CardContent className="p-6">
                                <Skeleton className="h-6 w-3/4 mb-2" />
                                <Skeleton className="h-4 w-1/2" />
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        );
    }

    // Filter out completed reminders
    const activeReminders = reminders?.filter(r => r.status !== 'completed') || [];
    const upcomingReminders = activeReminders.filter(r => r.dueDate && getDaysUntilDue(r.dueDate) >= 0);
    const overdueReminders = activeReminders.filter(r => r.dueDate && getDaysUntilDue(r.dueDate) < 0);
    const noDueDateReminders = activeReminders.filter(r => !r.dueDate);

    return (
        <div className="p-8 space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2">Reminders</h1>
                <p className="text-muted-foreground">
                    {activeReminders.length} active reminders for your documents
                </p>
            </div>

            {activeReminders.length === 0 && (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <CheckCircle2 className="w-16 h-16 text-muted-foreground mb-4" />
                        <h3 className="text-xl font-semibold mb-2">No reminders</h3>
                        <p className="text-muted-foreground text-center max-w-md">
                            When you upload documents with deadlines like bills or appointments, 
                            they will automatically appear here.
                        </p>
                    </CardContent>
                </Card>
            )}

            {overdueReminders.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-red-600 flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        Overdue ({overdueReminders.length})
                    </h2>
                    <div className="grid gap-4">
                        {overdueReminders.map((reminder) => {
                            const daysUntil = getDaysUntilDue(reminder.dueDate);
                            const urgency = getUrgencyLabel(daysUntil);

                            return (
                                <Card key={reminder.id} className="border-red-500/50">
                                    <CardHeader>
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex items-center gap-3 flex-1">
                                                <Checkbox
                                                    checked={false}
                                                    onCheckedChange={() => completeReminderMutation.mutate(reminder.id)}
                                                    className="mt-1"
                                                />
                                                <div className="flex-1 space-y-1">
                                                    <CardTitle className="text-lg">{reminder.title}</CardTitle>
                                                    <CardDescription>{reminder.description}</CardDescription>
                                                </div>
                                            </div>
                                            <Badge className={getCategoryColor(reminder.category)}>
                                                {reminder.category}
                                            </Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        <div className="flex items-center gap-6 text-sm">
                                            <div className="flex items-center gap-2">
                                                <Calendar className="w-4 h-4 text-muted-foreground" />
                                                <span>
                                                    {new Date(reminder.dueDate).toLocaleDateString('en-US', {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        year: 'numeric'
                                                    })}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Clock className="w-4 h-4 text-muted-foreground" />
                                                <span className={urgency.color}>{urgency.label}</span>
                                            </div>
                                        </div>
                                        {reminder.filename && (
                                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                <FileText className="w-4 h-4" />
                                                <span className="truncate">{reminder.filename}</span>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                </div>
            )}

            {noDueDateReminders.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5" />
                        Action Required ({noDueDateReminders.length})
                    </h2>
                    <div className="grid gap-4">
                        {noDueDateReminders.map((reminder) => (
                            <Card key={reminder.id}>
                                <CardHeader>
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex items-center gap-3 flex-1">
                                            <Checkbox
                                                checked={false}
                                                onCheckedChange={() => completeReminderMutation.mutate(reminder.id)}
                                                className="mt-1"
                                            />
                                            <div className="flex-1 space-y-1">
                                                <CardTitle className="text-lg">{reminder.title}</CardTitle>
                                                <CardDescription>{reminder.description}</CardDescription>
                                            </div>
                                        </div>
                                        <Badge className={getCategoryColor(reminder.category)}>
                                            {reminder.category}
                                        </Badge>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {reminder.filename && (
                                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                            <FileText className="w-4 h-4" />
                                            <span className="truncate">{reminder.filename}</span>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {upcomingReminders.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Calendar className="w-5 h-5" />
                        Upcoming ({upcomingReminders.length})
                    </h2>
                    <div className="grid gap-4">
                        {upcomingReminders.map((reminder) => {
                            const daysUntil = getDaysUntilDue(reminder.dueDate);
                            const urgency = getUrgencyLabel(daysUntil);

                            return (
                                <Card key={reminder.id}>
                                    <CardHeader>
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex items-center gap-3 flex-1">
                                                <Checkbox
                                                    checked={false}
                                                    onCheckedChange={() => completeReminderMutation.mutate(reminder.id)}
                                                    className="mt-1"
                                                />
                                                <div className="flex-1 space-y-1">
                                                    <CardTitle className="text-lg">{reminder.title}</CardTitle>
                                                    <CardDescription>{reminder.description}</CardDescription>
                                                </div>
                                            </div>
                                            <Badge className={getCategoryColor(reminder.category)}>
                                                {reminder.category}
                                            </Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        <div className="flex items-center gap-6 text-sm">
                                            <div className="flex items-center gap-2">
                                                <Calendar className="w-4 h-4 text-muted-foreground" />
                                                <span>
                                                    {new Date(reminder.dueDate).toLocaleDateString('en-US', {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        year: 'numeric'
                                                    })}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Clock className="w-4 h-4 text-muted-foreground" />
                                                <span className={urgency.color}>{urgency.label}</span>
                                            </div>
                                        </div>
                                        {reminder.filename && (
                                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                <FileText className="w-4 h-4" />
                                                <span className="truncate">{reminder.filename}</span>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
