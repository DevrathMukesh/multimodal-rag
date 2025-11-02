import { Message as MessageType } from "@/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown, ChevronUp, User, Bot } from "lucide-react";
import { SourceCard } from "./SourceCard";
import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MessageProps {
  message: MessageType;
  autoShowSources?: boolean;
}

export function Message({ message, autoShowSources = true }: MessageProps) {
  const isUser = message.role === "user";
  const [sourcesOpen, setSourcesOpen] = useState(false);

  useEffect(() => {
    if (autoShowSources && message.sources && message.sources.length > 0) {
      setSourcesOpen(true);
    }
  }, [autoShowSources, message.sources]);

  const sortedSources = message.sources
    ? [...message.sources].sort((a, b) => (b.score || 0) - (a.score || 0))
    : [];

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} animate-fade-in-up`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg animate-pulse-glow">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div className={`flex flex-col gap-2 max-w-[85%] md:max-w-[75%]`}>
        <Card
          className={`p-4 transition-all duration-300 hover:shadow-lg ${
            isUser
              ? "bg-primary text-primary-foreground hover:scale-[1.02]"
              : "bg-card text-card-foreground hover:scale-[1.01]"
          }`}
        >
          <div className={`text-sm break-words prose prose-sm max-w-none ${
            isUser ? "prose-invert" : "dark:prose-invert"
          }`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        </Card>

        {!isUser && sortedSources.length > 0 && (
          <Collapsible open={sourcesOpen} onOpenChange={setSourcesOpen}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="w-fit gap-2 text-muted-foreground hover:text-foreground"
              >
                {sourcesOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
                Sources ({sortedSources.length})
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-2 mt-2">
              {sortedSources.map((source, idx) => (
                <SourceCard key={`${source.parent_id}-${idx}`} source={source} />
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}

        <span className="text-xs text-muted-foreground px-1">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground shadow-lg">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
