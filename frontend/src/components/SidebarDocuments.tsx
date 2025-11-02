import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchDocuments, deleteDocumentById } from "@/lib/api";
import { FileText, Upload, AlertCircle, Trash2, Loader2, XCircle, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
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
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface SidebarDocumentsProps {
  activeDocumentId: string | null;
  onSelectDocument: (id: string | null) => void;
}

export function SidebarDocuments({ activeDocumentId, onSelectDocument }: SidebarDocumentsProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<{ id: string; name: string } | null>(null);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    refetchInterval: (query) => {
      // If there are processing documents, refresh more frequently (every 5 seconds)
      const docs = query.state.data?.documents || [];
      const hasProcessing = docs.some((doc) => doc.status === "processing");
      return hasProcessing ? 5000 : 30000;
    },
  });

  const documents = data?.documents || [];

  const truncateName = (name: string, maxLength: number = 30) => {
    if (!name || name.length <= maxLength) return name;
    return name.slice(0, maxLength) + "...";
  };

  const handleDeleteClick = (docId: string, docName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDocumentToDelete({ id: docId, name: docName });
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return;

    try {
      await deleteDocumentById(documentToDelete.id);
      if (activeDocumentId === documentToDelete.id) {
        onSelectDocument(null);
      }
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast({ 
        title: "Document Deleted", 
        description: `"${documentToDelete.name}" has been permanently removed.` 
      });
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
    } catch (err) {
      toast({
        title: "Delete Failed",
        description: err instanceof Error ? err.message : "Failed to delete document. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Get status icon and badge
  const getStatusIndicator = (status?: string) => {
    switch (status) {
      case "processing":
        return {
          icon: <Loader2 className="h-3 w-3 animate-spin text-primary" />,
          badge: (
            <Badge variant="secondary" className="text-xs">
              Processing
            </Badge>
          ),
        };
      case "failed":
        return {
          icon: <XCircle className="h-3 w-3 text-destructive" />,
          badge: (
            <Badge variant="destructive" className="text-xs">
              Failed
            </Badge>
          ),
        };
      case "completed":
      default:
        return {
          icon: null,
          badge: null,
        };
    }
  };

  return (
    <div className="flex h-full flex-col border-r border-border bg-sidebar animate-slide-in-left">
      <div className="flex items-center justify-between border-b border-sidebar-border p-4">
        <h2 className="text-lg font-semibold text-sidebar-foreground">Documents</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/upload")}
          className="hover:bg-sidebar-accent hover:scale-110 transition-all duration-300"
        >
          <Upload className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-2">
          <Button
            variant={activeDocumentId === null ? "default" : "ghost"}
            className={cn(
              "w-full justify-start transition-all duration-300 hover:translate-x-1",
              activeDocumentId === null && "bg-sidebar-primary text-sidebar-primary-foreground"
            )}
            onClick={() => onSelectDocument(null)}
          >
            <FileText className="mr-2 h-4 w-4" />
            All Documents
          </Button>

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
                  Failed to load documents
                </div>
              </div>
            </Card>
          )}

          {documents.map((doc, idx) => {
            const isProcessing = doc.status === "processing";
            const isFailed = doc.status === "failed";
            const statusIndicator = getStatusIndicator(doc.status);
            
            return (
            <Card
              key={doc.id}
              className={cn(
                  "p-3 transition-all duration-300 hover:shadow-md animate-fade-in group relative overflow-visible",
                  !isProcessing && "cursor-pointer hover:bg-sidebar-accent hover:translate-x-1",
                  isProcessing && "opacity-75 cursor-not-allowed bg-muted/30",
                  isFailed && "border-destructive/50",
                  activeDocumentId === doc.id && !isProcessing && "border-sidebar-primary bg-sidebar-accent scale-[1.02]"
              )}
              style={{ animationDelay: `${idx * 0.1}s` }}
                onClick={() => {
                  if (!isProcessing) {
                    onSelectDocument(doc.id);
                  } else {
                    toast({
                      title: "Processing",
                      description: "This document is still being processed. Please wait until it's completed.",
                      variant: "default",
                    });
                  }
                }}
            >
              <div className="flex items-start gap-2 relative pr-8">
                  <div className="relative shrink-0">
                    <FileText className={cn(
                      "h-5 w-5",
                      isProcessing ? "text-muted-foreground" : "text-sidebar-primary"
                    )} />
                    {statusIndicator.icon && (
                      <div className="absolute -bottom-0.5 -right-0.5 bg-background rounded-full">
                        {statusIndicator.icon}
                      </div>
                    )}
                  </div>
                <div className="flex-1 min-w-0 cursor-pointer">
                    <div className="flex items-start justify-between gap-2 min-w-0">
                      <h3 
                        className={cn(
                          "font-medium text-sm break-words line-clamp-2 flex-1 min-w-0",
                          isProcessing && "text-muted-foreground",
                          isFailed && "text-destructive"
                        )}
                        title={doc.name}
                      >
                        {truncateName(doc.name, 30)}
                      </h3>
                      {statusIndicator.badge && (
                        <div className="shrink-0 flex-shrink-0 ml-2">
                          {statusIndicator.badge}
                        </div>
                      )}
                    </div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-mono shrink-0">{doc.pages} pages</span>
                    <span className="shrink-0">•</span>
                    <span className="shrink-0">{new Date(doc.createdAt).toLocaleDateString()}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-7 w-7 opacity-80 hover:opacity-100 hover:text-destructive hover:bg-destructive/10 transition-all shrink-0 z-10 flex-shrink-0"
                  disabled={isProcessing}
                  onClick={(e) => {
                    if (isProcessing) {
                      toast({
                        title: "Processing",
                        description: "Cannot delete a document that is currently processing.",
                        variant: "default",
                      });
                      return;
                    }
                    handleDeleteClick(doc.id, doc.name, e);
                  }}
                  aria-label="Delete document"
                  title={isProcessing ? "Cannot delete while processing" : "Delete document"}
                >
                  <Trash2 className={cn("h-4 w-4", isProcessing && "opacity-50")} />
                </Button>
              </div>
            </Card>
            );
          })}
        </div>
      </ScrollArea>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              <AlertDialogTitle>Delete Document</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="text-left pt-2">
              Are you sure you want to delete this document?
              {documentToDelete && (
                <div className="mt-3 p-3 rounded-md bg-muted border border-border">
                  <p className="text-sm font-medium text-foreground mb-1">Document:</p>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    "{documentToDelete.name}"
                  </p>
                </div>
              )}
              <p className="mt-3 text-destructive font-medium">
                This action cannot be undone. The document, its content, embeddings, and all associated data will be permanently deleted.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDocumentToDelete(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Document
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
