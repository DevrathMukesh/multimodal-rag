import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDocument } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, CheckCircle2, XCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";

export function UploadDropzone() {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
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

      // Simulate progress - slower and more realistic
      let progressValue = 0;
      const progressInterval = setInterval(() => {
        progressValue += 2; // Increment by 2% instead of 10%
        if (progressValue >= 95) {
          clearInterval(progressInterval);
          setProgress(95); // Cap at 95% until upload completes
        } else {
          setProgress(progressValue);
        }
      }, 500); // Update every 500ms instead of 200ms for slower progression

      try {
        const document = await uploadDocument(file);
        clearInterval(progressInterval);
        setProgress(100);
        setUploadedFile(document.name);

        toast({
          title: "Upload successful",
          description: `${document.name} has been uploaded (${document.pages} pages)`,
        });

        // Navigate back to chat after a short delay
        setTimeout(() => {
          navigate("/");
        }, 2000);
      } catch (err) {
        clearInterval(progressInterval);
        const errorMessage = err instanceof Error ? err.message : "Failed to upload file";
        setError(errorMessage);
        toast({
          title: "Upload failed",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setIsUploading(false);
      }
    },
    [toast, navigate]
  );

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
              <FileText className="h-5 w-5 text-primary animate-pulse" />
              <div className="flex-1">
                <p className="text-sm font-medium">Uploading...</p>
              </div>
              <span className="text-sm font-mono text-muted-foreground">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </Card>
      )}

      {uploadedFile && (
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
