import { useState, useEffect } from "react";
import { SidebarDocuments } from "@/components/SidebarDocuments";
import { SidebarChats } from "@/components/SidebarChats";
import { Chat } from "@/components/Chat";
import { getSessionId, generateSessionId, setSessionId as saveSessionId } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string>("");
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [sidebarTab, setSidebarTab] = useState<"chats" | "documents">("chats");

  useEffect(() => {
    // Initialize with session from localStorage or create new one
    const currentSession = getSessionId();
    setSessionId(currentSession);
  }, []);

  const handleNewChat = () => {
    const newSession = generateSessionId();
    saveSessionId(newSession); // Save to localStorage
    setSessionId(newSession); // Update state
    setSidebarTab("chats");
  };

  const handleSelectSession = (newSessionId: string) => {
    saveSessionId(newSessionId); // Save to localStorage
    setSessionId(newSessionId); // Update state
  };

  if (!sessionId) return null;

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background transition-colors duration-300">
      {/* Desktop Sidebar */}
      <aside className="hidden md:block w-80 border-r border-border">
        <Tabs value={sidebarTab} onValueChange={(v) => setSidebarTab(v as "chats" | "documents")} className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-2 m-2">
            <TabsTrigger value="chats">Chats</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
          </TabsList>
          <TabsContent value="chats" className="flex-1 m-0 mt-2 overflow-hidden">
            <SidebarChats
              activeSessionId={sessionId}
              onSelectSession={handleSelectSession}
              onNewChat={handleNewChat}
            />
          </TabsContent>
          <TabsContent value="documents" className="flex-1 m-0 mt-2 overflow-hidden">
            <SidebarDocuments
              activeDocumentId={activeDocumentId}
              onSelectDocument={setActiveDocumentId}
            />
          </TabsContent>
        </Tabs>
      </aside>

      {/* Mobile Sidebar */}
      <Sheet>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="fixed top-4 left-4 z-50 md:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-80 p-0">
          <Tabs value={sidebarTab} onValueChange={(v) => setSidebarTab(v as "chats" | "documents")} className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2 m-2">
              <TabsTrigger value="chats">Chats</TabsTrigger>
              <TabsTrigger value="documents">Documents</TabsTrigger>
            </TabsList>
            <TabsContent value="chats" className="flex-1 m-0 mt-2 overflow-hidden">
              <SidebarChats
                activeSessionId={sessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
              />
            </TabsContent>
            <TabsContent value="documents" className="flex-1 m-0 mt-2 overflow-hidden">
              <SidebarDocuments
                activeDocumentId={activeDocumentId}
                onSelectDocument={setActiveDocumentId}
              />
            </TabsContent>
          </Tabs>
        </SheetContent>
      </Sheet>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-hidden">
        <Chat 
          sessionId={sessionId} 
          activeDocumentId={activeDocumentId} 
          onNewChat={handleNewChat}
          key={sessionId} 
        />
      </main>
    </div>
  );
}
