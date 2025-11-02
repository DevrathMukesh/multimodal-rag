import { Source } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { FileText, Table2, Image as ImageIcon, ExternalLink } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toImageUrl, truncateText } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface SourceCardProps {
  source: Source;
}

export function SourceCard({ source }: SourceCardProps) {
  const getIcon = () => {
    switch (source.type) {
      case "text":
        return <FileText className="h-4 w-4" />;
      case "table":
        return <Table2 className="h-4 w-4" />;
      case "image":
        return <ImageIcon className="h-4 w-4" />;
    }
  };

  const renderTextSource = () => {
    const text = source.text || source.summary;
    const truncated = truncateText(text);
    const needsExpansion = text.length > 300;

    return (
      <div className="space-y-2">
        <div className="text-sm text-foreground prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {truncated}
          </ReactMarkdown>
        </div>
        {needsExpansion && (
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="link" size="sm" className="h-auto p-0 text-primary">
                View more <ExternalLink className="ml-1 h-3 w-3" />
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>Full Text</DialogTitle>
              </DialogHeader>
              <ScrollArea className="max-h-[60vh]">
                <div className="text-sm text-foreground prose prose-sm dark:prose-invert max-w-none p-4">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {text}
                  </ReactMarkdown>
                </div>
              </ScrollArea>
            </DialogContent>
          </Dialog>
        )}
      </div>
    );
  };

  const renderTableSource = () => {
    if (source.table_html) {
      return (
        <div className="rounded-md border border-border overflow-auto max-h-64">
          <div
            className="text-sm"
            dangerouslySetInnerHTML={{ __html: source.table_html }}
          />
        </div>
      );
    }
    return renderTextSource();
  };

  const renderImageSource = () => {
    if (!source.image_b64) return null;
    const imageUrl = toImageUrl(source.image_b64);

    return (
      <Dialog>
        <DialogTrigger asChild>
          <div className="cursor-pointer">
            <img
              src={imageUrl}
              alt={source.summary}
              className="w-40 rounded-md border border-border object-cover hover:opacity-80 transition-opacity"
            />
          </div>
        </DialogTrigger>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Image Source</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center">
            <img
              src={imageUrl}
              alt={source.summary}
              className="max-h-[70vh] rounded-md"
            />
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  const renderContent = () => {
    switch (source.type) {
      case "text":
        return renderTextSource();
      case "table":
        return renderTableSource();
      case "image":
        return renderImageSource();
    }
  };

  return (
    <Card className="p-4 space-y-3 transition-all duration-300 hover:shadow-md hover:scale-[1.01] animate-scale-in">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="secondary" className="gap-1">
            {getIcon()}
            <span className="capitalize">{source.type}</span>
          </Badge>
          {source.page_number && (
            <Badge variant="outline" className="font-mono">
              Page {source.page_number}
            </Badge>
          )}
          {source.score !== undefined && (
            <Badge variant="outline" className="font-mono">
              Score: {source.score.toFixed(2)}
            </Badge>
          )}
        </div>
      </div>

      {source.summary && source.type !== "text" && (
        <div className="text-sm text-muted-foreground prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {source.summary}
          </ReactMarkdown>
        </div>
      )}

      {renderContent()}

      {source.source && (
        <p className="text-xs text-muted-foreground truncate">
          Source: {source.source}
        </p>
      )}
    </Card>
  );
}
