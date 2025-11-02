import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchChatSessions, deleteChatSession, generateSessionId, setSessionId } from "@/lib/api";
import { MessageSquare, Plus, Trash2, AlertCircle, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import { formatDistanceToNow } from "date-fns";

interface SidebarChatsProps {
  activeSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
}

export function SidebarChats({
  activeSessionId,
  onSelectSession,
  onNewChat,
}: SidebarChatsProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string>("");
  
  const { data, isLoading, error } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: fetchChatSessions,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const sessions = data?.sessions || [];

  const handleDeleteClick = (sessionId: string, sessionTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessionToDelete(sessionId);
    setSessionTitle(sessionTitle);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!sessionToDelete) return;

    try {
      await deleteChatSession(sessionToDelete);
      await queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      
      // If deleting active session, switch to new chat
      if (sessionToDelete === activeSessionId) {
        onNewChat();
      }
      
      toast({ title: "Deleted", description: "Chat session removed" });
      setDeleteDialogOpen(false);
      setSessionToDelete(null);
      setSessionTitle("");
    } catch (err) {
      toast({
        title: "Delete failed",
        description: err instanceof Error ? err.message : "",
        variant: "destructive",
      });
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return "Recently";
    }
  };

  const truncateTitle = (title: string, maxLength: number = 15) => {
    if (!title || title.length <= maxLength) return title || "New Chat";
    return title.slice(0, maxLength) + "...";
  };

  return (
    <div className="flex h-full flex-col border-r border-border bg-sidebar">
      <div className="flex items-center justify-between border-b border-sidebar-border p-4">
        <h2 className="text-lg font-semibold text-sidebar-foreground">Chats</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onNewChat}
          className="hover:bg-sidebar-accent hover:scale-110 transition-all duration-300"
          title="New Chat"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-2">
          {isLoading && (
            <>
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </>
          )}

          {error && (
            <Card className="border-destructive/50 bg-destructive/10 p-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <div className="flex-1 text-sm text-destructive">
                  Failed to load chat sessions
                </div>
              </div>
            </Card>
          )}

          {sessions.length === 0 && !isLoading && (
            <Card className="p-6 text-center border-dashed">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No chat sessions yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Start a new conversation to begin
              </p>
            </Card>
          )}

          {sessions.map((session, idx) => (
            <Card
              key={session.id}
              className={cn(
                "cursor-pointer p-3 transition-all duration-300 hover:bg-sidebar-accent hover:translate-x-1 hover:shadow-md animate-fade-in group relative overflow-visible",
                activeSessionId === session.id &&
                  "border-sidebar-primary bg-sidebar-accent scale-[1.02]"
              )}
              style={{ animationDelay: `${idx * 0.05}s` }}
            >
              <div className="flex items-start gap-2 relative pr-8">
                <MessageSquare className="h-5 w-5 text-sidebar-primary shrink-0 mt-0.5" />
                <div 
                  className="flex-1 min-w-0 cursor-pointer"
                  onClick={() => onSelectSession(session.id)}
                >
                  <h3 
                    className="font-medium text-sm text-sidebar-foreground break-words line-clamp-2"
                    title={session.title || "New Chat"}
                  >
                    {truncateTitle(session.title, 15)}
                  </h3>
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{session.message_count} messages</span>
                    <span>•</span>
                    <span>{formatTime(session.last_activity)}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-7 w-7 opacity-80 hover:opacity-100 hover:text-destructive hover:bg-destructive/10 transition-all shrink-0 z-10 flex-shrink-0"
                  onClick={(e) => handleDeleteClick(session.id, session.title || "New Chat", e)}
                  aria-label="Delete chat"
                  title="Delete this chat"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              <AlertDialogTitle>Delete Chat Session</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="text-left pt-2">
              Are you sure you want to delete this chat session?
              {sessionTitle && (
                <div className="mt-3 p-3 rounded-md bg-muted border border-border">
                  <p className="text-sm font-medium text-foreground mb-1">Chat:</p>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    "{truncateTitle(sessionTitle, 50)}"
                  </p>
                </div>
              )}
              <p className="mt-3 text-destructive font-medium">
                This action cannot be undone. All messages in this conversation will be permanently deleted.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Chat
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

