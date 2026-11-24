import ChatArea from "./components/ChatArea";
import ChatInput from "./components/ChatInput";
import Sidebar from "./components/Sidebar";
import { useChat } from "./hooks/useChat";

export default function App() {
  const chat = useChat();

  return (
    <div className="app">
      <Sidebar
        sessionId={chat.sessionId}
        messageCount={chat.messages.length}
        connection={chat.connection}
        systemPrompt={chat.systemPrompt}
        onSystemPromptChange={chat.setSystemPrompt}
        onNewChat={chat.newChat}
      />
      <main className="main">
        <ChatArea messages={chat.messages} sending={chat.sending} onSuggestedPrompt={chat.sendMessage} />
        <ChatInput onSend={chat.sendMessage} disabled={chat.sending} />
      </main>
    </div>
  );
}
