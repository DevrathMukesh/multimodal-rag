import { useState, useRef, useEffect, useCallback } from "react";
import { Message as MessageType, ChatSettings, Source } from "@/types";
import { sendChatMessage, getChatMessages, buildStreamUrl } from "@/lib/api";
import { Message } from "./Message";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Send, Settings, Loader2, Plus, Clock, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Card } from "@/components/ui/card";
import { ThemeToggle } from "./ThemeToggle";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

interface ChatProps {
  sessionId: string;
  activeDocumentId: string | null;
  onNewChat?: () => void;
}

export function Chat({ sessionId, activeDocumentId, onNewChat }: ChatProps) {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState<ChatSettings>({
    autoShowSources: true,
    includeImages: true,
    streamResponses: true,
  });
  const [rateLimitInfo, setRateLimitInfo] = useState<{
    waitSeconds: number;
    initialWaitSeconds: number; // Store initial value for progress calculation
    retryAttempt: number;
    maxRetries: number;
  } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { toast } = useToast();

  // Load conversation history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await getChatMessages(sessionId);
        if (history.length > 0) {
          setMessages(history);
        }
      } catch (error) {
        // Silently fail - might be a new session
        console.debug("Could not load chat history:", error);
      }
    };
    loadHistory();
  }, [sessionId]);


  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Countdown timer for rate limit (fallback if backend updates are delayed)
  useEffect(() => {
    if (!rateLimitInfo || rateLimitInfo.waitSeconds <= 0) {
      if (rateLimitInfo && rateLimitInfo.waitSeconds <= 0) {
        // Wait finished, clear after a brief delay
        setTimeout(() => setRateLimitInfo(null), 500);
      }
      return;
    }

    // Countdown timer - decreases every second
    // Backend now sends only one event, so we handle countdown locally
    const interval = setInterval(() => {
      setRateLimitInfo((prev) => {
        if (!prev || prev.waitSeconds <= 1) {
          clearInterval(interval);
          // Keep the info for a moment to show completion, then clear
          setTimeout(() => setRateLimitInfo(null), 500);
          return { ...prev, waitSeconds: 0 };
        }
        return { 
          ...prev, 
          waitSeconds: prev.waitSeconds - 1,
          // Preserve initialWaitSeconds if not set
          initialWaitSeconds: prev.initialWaitSeconds || prev.waitSeconds
        };
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [rateLimitInfo?.waitSeconds]); // Only run when waitSeconds changes (will be updated by backend events)

  const eventSourceRef = useRef<EventSource | null>(null);
  const currentAssistantIdRef = useRef<string | null>(null);
  const bufferRef = useRef<string>("");
  const sourcesFetchedRef = useRef(false);

  const fetchSourcesForMessage = useCallback(
    async (assistantId: string, question: string) => {
      if (sourcesFetchedRef.current) return;
      sourcesFetchedRef.current = true;

      try {
        const response = await sendChatMessage({
          question,
          sessionId,
          documentId: activeDocumentId || undefined,
          includeImages: settings.includeImages,
          stream: false,
        });

        if (currentAssistantIdRef.current === assistantId) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, sources: response.sources } : m
            )
          );
        }
      } catch (e) {
        // Sources are optional, ignore errors
        console.debug("Failed to fetch sources:", e);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, activeDocumentId, settings.includeImages]
  );

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    // Close any existing stream
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    const userMessage: MessageType = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const question = userMessage.content;
    setInput("");

    if (!settings.streamResponses) {
      setIsLoading(true);
      try {
        const response = await sendChatMessage({
          question,
          sessionId,
          documentId: activeDocumentId || undefined,
          includeImages: settings.includeImages,
          stream: false,
        });

        const assistantMessage: MessageType = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        toast({
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to send message",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
      return;
    }

    // Streaming mode
    const assistantId = `assistant-${Date.now()}`;
    currentAssistantIdRef.current = assistantId;
    bufferRef.current = "";
    sourcesFetchedRef.current = false;
    setIsLoading(true);

    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", timestamp: new Date() },
    ]);

    const url = buildStreamUrl({
      question,
      sessionId,
      documentId: activeDocumentId || undefined,
      includeImages: settings.includeImages,
    });

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (evt) => {
      const chunk = evt.data || "";
      const cleanChunk = chunk.startsWith("data: ") ? chunk.slice(6) : chunk;

      // Skip rate_limit event data - it's handled by the event listener
      // Check if this looks like a rate limit JSON payload
      try {
        const parsed = JSON.parse(cleanChunk);
        if (parsed && (parsed.wait_seconds !== undefined || parsed.type === "waiting")) {
          // Manually trigger rate limit handler as fallback (in case event listener didn't fire)
          const waitSeconds = Math.ceil(parsed.wait_seconds || 0);
          setRateLimitInfo((prev) => {
            const isNewRateLimit = !prev || (prev.waitSeconds < waitSeconds);
            const initialWaitSeconds = isNewRateLimit 
              ? waitSeconds 
              : (prev?.initialWaitSeconds || waitSeconds);
            
            return {
              waitSeconds,
              initialWaitSeconds,
              retryAttempt: parsed.retry_attempt || 1,
              maxRetries: parsed.max_retries || 4,
            };
          });
          
          // Remove any messages that contain rate limit data
          setMessages((prev) => 
            prev.filter((m) => {
              const content = m.content.toLowerCase();
              // Remove if it contains rate limit indicators
              return !(content.includes("wait_seconds") && content.includes("retry_attempt")) &&
                     !content.includes("event: rate_limit") &&
                     !content.includes('"type":"waiting"');
            })
          );
          
          return; // Don't add rate limit events to message content
        }
      } catch (e) {
        // Not JSON, continue processing
      }

      // Skip raw rate limit event strings
      if (cleanChunk.includes("event: rate_limit") || 
          (cleanChunk.includes("wait_seconds") && cleanChunk.includes("retry_attempt"))) {
        // Try to extract and set rate limit info from the string
        try {
          const jsonMatch = cleanChunk.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            const parsed = JSON.parse(jsonMatch[0]);
            if (parsed.wait_seconds) {
              setRateLimitInfo({
                waitSeconds: Math.ceil(parsed.wait_seconds),
                initialWaitSeconds: Math.ceil(parsed.wait_seconds),
                retryAttempt: parsed.retry_attempt || 1,
                maxRetries: parsed.max_retries || 4,
              });
            }
          }
        } catch (e) {
          // Ignore parsing errors
        }
        return; // Don't add rate limit events to message content
      }

      // Handle end event
      if (cleanChunk.trim() === "event: end" || cleanChunk.includes("event: end")) {
        es.close();
        eventSourceRef.current = null;
        setRateLimitInfo(null); // Clear rate limit info when stream ends
        fetchSourcesForMessage(assistantId, question);
        return;
      }

      // Handle error
      if (cleanChunk.startsWith("[ERROR:")) {
        const errorMsg = cleanChunk.replace("[ERROR:", "").replace("]", "").trim();
        es.close();
        eventSourceRef.current = null;
        setIsLoading(false);
        setRateLimitInfo(null);
        toast({
          title: "Error",
          description: errorMsg,
          variant: "destructive",
        });
        return;
      }

      bufferRef.current += cleanChunk;
      if (currentAssistantIdRef.current === assistantId) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: bufferRef.current } : m
          )
        );
      }
    };

    // Handle rate_limit events
    es.addEventListener("rate_limit", (evt) => {
      try {
        const data = JSON.parse(evt.data);
        const waitSeconds = Math.ceil(data.wait_seconds || 0);
        setRateLimitInfo((prev) => {
          // If this is a new rate limit event (no previous info or wait time is higher than current), 
          // set initialWaitSeconds to the new wait time
          // Otherwise, preserve the existing initialWaitSeconds for progress calculation
          const isNewRateLimit = !prev || (prev.waitSeconds < waitSeconds);
          const initialWaitSeconds = isNewRateLimit 
            ? waitSeconds  // New rate limit - this is the starting wait time
            : (prev.initialWaitSeconds || waitSeconds);  // Preserve initial or use current as fallback
          
          return {
          waitSeconds,
            initialWaitSeconds,
          retryAttempt: data.retry_attempt || 1,
          maxRetries: data.max_retries || 4,
          };
        });
      } catch (e) {
        console.error("Failed to parse rate limit event", e);
      }
    });

    es.addEventListener("end", () => {
      es.close();
      eventSourceRef.current = null;
      fetchSourcesForMessage(assistantId, question);
    });

    es.onerror = () => {
      setTimeout(() => {
        if (es.readyState === EventSource.CLOSED) {
          if (bufferRef.current === "") {
            toast({
              title: "Connection Error",
              description: "Unable to connect to the server. Please try again.",
              variant: "destructive",
            });
          } else {
            toast({
              title: "Stream Interrupted",
              description: "The connection was interrupted. Partial response received.",
              variant: "destructive",
            });
          }
        }
        es.close();
        eventSourceRef.current = null;
        setIsLoading(false);
      }, 100);
    };
  }, [
    input,
    isLoading,
    settings.streamResponses,
    settings.includeImages,
    sessionId,
    activeDocumentId,
    toast,
    fetchSourcesForMessage,
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border p-4 bg-gradient-to-r from-background to-secondary/20">
        <div className="animate-fade-in">
          <h1 className="text-xl font-semibold text-foreground">Chat</h1>
          {activeDocumentId && (
            <p className="text-sm text-muted-foreground animate-fade-in">Chatting with selected document</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {onNewChat && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onNewChat}
              className="gap-2"
              title="New Chat"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New Chat</span>
            </Button>
          )}
          <ThemeToggle />
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="icon" className="hover:rotate-90 transition-transform duration-300">
                <Settings className="h-5 w-5" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="end">
              <div className="space-y-4">
                <h3 className="font-semibold text-sm">Chat Settings</h3>

                <div className="flex items-center justify-between">
                  <Label htmlFor="auto-sources" className="text-sm">
                    Auto-show sources
                  </Label>
                  <Switch
                    id="auto-sources"
                    checked={settings.autoShowSources}
                    onCheckedChange={(checked) =>
                      setSettings((prev) => ({ ...prev, autoShowSources: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="include-images" className="text-sm">
                    Include images
                  </Label>
                  <Switch
                    id="include-images"
                    checked={settings.includeImages}
                    onCheckedChange={(checked) =>
                      setSettings((prev) => ({ ...prev, includeImages: checked }))
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="stream" className="text-sm">
                    Stream responses
                  </Label>
                  <Switch
                    id="stream"
                    checked={settings.streamResponses}
                    onCheckedChange={(checked) =>
                      setSettings((prev) => ({ ...prev, streamResponses: checked }))
                    }
                  />
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      {/* Rate Limit Modal/Popup */}
      <Dialog 
        open={!!rateLimitInfo && rateLimitInfo.waitSeconds > 0} 
        onOpenChange={(open) => {
          // Prevent closing while countdown is active
          if (!open && rateLimitInfo && rateLimitInfo.waitSeconds > 0) {
            return; // Don't allow closing while waiting
          }
          if (!open && rateLimitInfo && rateLimitInfo.waitSeconds <= 0) {
            setRateLimitInfo(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md pointer-events-auto" onPointerDownOutside={(e) => {
          // Prevent closing by clicking outside
          if (rateLimitInfo && rateLimitInfo.waitSeconds > 0) {
            e.preventDefault();
          }
        }} onEscapeKeyDown={(e) => {
          // Prevent closing with Escape key while waiting
          if (rateLimitInfo && rateLimitInfo.waitSeconds > 0) {
            e.preventDefault();
          }
        }}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-500 animate-pulse" />
              Rate Limit - Please Wait
            </DialogTitle>
            <DialogDescription className="pt-2">
              API quota exceeded. The system is waiting before automatically retrying.
            </DialogDescription>
          </DialogHeader>
          {rateLimitInfo && (
            <div className="space-y-4 py-4">
              {/* Countdown Display */}
              <div className="flex flex-col items-center justify-center space-y-2">
                <div className="flex items-center gap-3">
                  <Clock className="h-6 w-6 text-yellow-600 dark:text-yellow-500 animate-pulse" />
                  <div className="text-center">
                    <div className="text-3xl font-bold font-mono text-yellow-600 dark:text-yellow-500">
                      {rateLimitInfo.waitSeconds}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      second{rateLimitInfo.waitSeconds !== 1 ? "s" : ""} remaining
                    </div>
                  </div>
                </div>
              </div>

              {/* Progress Bar - shows decreasing progress */}
              <div className="w-full bg-yellow-200/30 dark:bg-yellow-800/30 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-yellow-500 dark:bg-yellow-400 transition-all duration-1000 ease-linear"
                  style={{
                    width: `${Math.max(0, Math.min(100, rateLimitInfo.initialWaitSeconds 
                      ? ((rateLimitInfo.initialWaitSeconds - rateLimitInfo.waitSeconds) / rateLimitInfo.initialWaitSeconds) * 100
                      : 0))}%`,
                  }}
                />
              </div>

              {/* Retry Info */}
              <div className="text-center text-sm text-muted-foreground">
                Retry attempt {rateLimitInfo.retryAttempt} of {rateLimitInfo.maxRetries}
              </div>

              {/* Message */}
              <div className="text-center text-xs text-muted-foreground italic">
                Chat is temporarily paused. Will automatically continue when ready...
              </div>
        </div>
      )}
        </DialogContent>
      </Dialog>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.length === 0 && (
            <Card className="p-8 text-center border-dashed animate-fade-in bg-gradient-to-br from-card to-secondary/10">
              <p className="text-muted-foreground text-lg">
                Start a conversation by asking a question about your documents
              </p>
            </Card>
          )}

          {messages.map((message) => (
            <Message
              key={message.id}
              message={message}
              autoShowSources={settings.autoShowSources}
            />
          ))}

          {isLoading && (
            <div className="flex gap-3 animate-fade-in">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
              <Card className="p-4 animate-pulse">
                <p className="text-sm text-muted-foreground">Thinking...</p>
              </Card>
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-border p-4">
        <div className="max-w-4xl mx-auto flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question... (Shift+Enter for new line)"
            className="min-h-[60px] resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="icon"
            className="h-[60px] w-[60px] shrink-0 transition-all duration-300 hover:scale-110 hover:shadow-lg"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
