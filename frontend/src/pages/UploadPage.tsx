import { UploadDropzone } from "@/components/UploadDropzone";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function UploadPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background transition-colors duration-300">
      <header className="border-b border-border bg-gradient-to-r from-background to-secondary/20">
        <div className="container max-w-4xl mx-auto px-4 py-4">
          <Button
            variant="ghost"
            onClick={() => navigate("/")}
            className="gap-2 hover:translate-x-[-4px] transition-transform duration-300"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Chat
          </Button>
        </div>
      </header>

      <main className="container max-w-4xl mx-auto px-4 py-12">
        <div className="space-y-6">
          <div className="animate-fade-in">
            <h1 className="text-3xl font-bold text-foreground">Upload Document</h1>
            <p className="text-muted-foreground mt-2">
              Upload a PDF document to start asking questions about it
            </p>
          </div>

          <UploadDropzone />

          <div className="rounded-lg bg-muted/50 p-4">
            <h3 className="font-semibold text-sm mb-2">Tips:</h3>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Only PDF files are supported</li>
              <li>Larger documents may take longer to process</li>
              <li>You can upload multiple documents and switch between them</li>
              <li>Documents with tables and images are fully supported</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
