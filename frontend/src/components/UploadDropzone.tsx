import { useState, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDocument, getUploadStatus } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, CheckCircle2, XCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";

export function UploadDropzone() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const startPolling = (uploadId: string) => {
    // Clear any existing polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await getUploadStatus(uploadId);
        setProgress(status.progress || 0);

        if (status.status === "completed") {
          setIsUploading(false);
          setError(null); // Clear any errors
          setUploadedFile(status.name);
          setProgress(100);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          toast({
            title: "Upload completed",
            description: `${status.name} has been processed successfully`,
          });
          setTimeout(() => navigate("/"), 2000);
        } else if (status.status === "failed") {
          setIsUploading(false);
          setUploadedFile(null); // Clear success message
          setError("Upload processing failed. Check backend logs for details.");
          setProgress(0);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          toast({
            title: "Upload failed",
            description: "Processing failed. Please check your API configuration.",
            variant: "destructive",
          });
        }
      } catch (err) {
        // Stop polling on error
        setIsUploading(false);
        setUploadedFile(null); // Clear success message
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setError("Failed to check upload status");
      }
    }, 2000); // Poll every 2 seconds
  };

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    if (!file.type.includes("pdf")) {
      toast({
        title: "Invalid file type",
        description: "Only PDF files are supported",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setError(null);
    setProgress(0);

    try {
      const document = await uploadDocument(file);
      setProgress(document.progress || 0);

      if (document.status === "completed") {
        setIsUploading(false);
        setError(null); // Clear any errors
        setUploadedFile(document.name);
        setProgress(100);
        toast({
          title: "Upload successful",
          description: `${document.name} has been uploaded (${document.pages} pages)`,
        });
        setTimeout(() => navigate("/"), 2000);
      } else {
        // Processing in background - don't show success yet
        setUploadedFile(null); // Clear any previous success
        setError(null); // Clear any previous errors
        toast({
          title: "Upload started",
          description: `${document.name} is being processed...`,
        });
        startPolling(document.id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to upload file";
      setUploadedFile(null); // Clear success message
      setError(errorMessage);
      setIsUploading(false);
      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div className="space-y-4">
      <Card
        {...getRootProps()}
        className={`border-2 border-dashed p-12 text-center transition-all duration-300 cursor-pointer animate-fade-in hover:shadow-lg
          ${
            isDragActive
              ? "border-primary bg-primary/10 scale-105"
              : "border-border hover:border-primary/50 hover:bg-accent/50"
          }
          ${isUploading ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className="rounded-full bg-primary/10 p-4 animate-scale-in hover:scale-110 transition-transform duration-300">
            <Upload className="h-8 w-8 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold">
              {isDragActive ? "Drop your PDF here" : "Upload a document"}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Drag and drop a PDF file or click to browse
            </p>
          </div>
          {!isUploading && (
            <Button type="button" variant="outline">
              Choose File
            </Button>
          )}
        </div>
      </Card>

      {isUploading && (
        <Card className="p-6 animate-fade-in">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Processing document...</p>
                {uploadedFile && (
                  <p className="text-xs text-muted-foreground mt-0.5">{uploadedFile}</p>
                )}
              </div>
              <div className="text-sm font-medium text-muted-foreground min-w-[3rem] text-right">
                {progress}%
              </div>
            </div>
            <Progress value={progress} className="h-2" />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {progress < 10 
                  ? "Parsing PDF..." 
                  : progress < 30 
                    ? "Summarizing images..." 
                    : progress < 90 
                      ? "Summarizing text..." 
                      : progress < 100
                        ? "Saving and indexing..."
                        : "Completed"}
              </span>
              <span>{progress}% complete</span>
            </div>
          </div>
        </Card>
      )}

      {uploadedFile && !isUploading && (
        <Card className="p-6 border-success animate-scale-in bg-success/5">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-success animate-pulse" />
            <div className="flex-1">
              <p className="text-sm font-medium text-success">Upload successful!</p>
              <p className="text-sm text-muted-foreground">{uploadedFile}</p>
            </div>
          </div>
        </Card>
      )}

      {error && (
        <Card className="p-6 border-destructive">
          <div className="flex items-center gap-3">
            <XCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="text-sm font-medium text-destructive">Upload failed</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
