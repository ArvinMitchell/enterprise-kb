"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User, Bot, Loader2, BookOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { cn } from "../lib/utils";

type Message = {
  id: string;
  role: "user" | "ai";
  content: string;
  sources?: string[];
};

export default function ChatInterface() {
  const [mounted, setMounted] = useState(false);
  const [messages, setMessages] = useState<Message[]>([{
    id: "welcome",
    role: "ai",
    content: "你好！我是你的智能知识库助手。我已经学习了你上传的文档，有什么我可以帮你的吗？"
  }]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage.content })
      });

      if (!response.ok) throw new Error("API request failed");

      const data = await response.json();
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content: data.answer,
        sources: data.sources
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content: "抱歉，服务器出现错误，无法获取回答。请检查后端是否正常运行。"
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!mounted) return <div className="h-[600px] w-full max-w-2xl mx-auto mt-12 glass rounded-3xl" />;

  return (
    <div 
      suppressHydrationWarning
      className="flex flex-col h-[600px] w-full max-w-2xl mx-auto mt-12 glass rounded-3xl overflow-hidden border-border/50 shadow-2xl relative"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/50 bg-surface flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
            <Bot className="text-primary w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">DeepSeek 知识库助手</h3>
            <p className="text-xs text-green-400 font-medium tracking-wider flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
              RAG 引擎已连接
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 z-10 custom-scrollbar">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex gap-4 max-w-[85%]",
                msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
              )}
            >
              <div className={cn(
                "w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center mt-1",
                msg.role === "user" ? "bg-purple-500/20 text-purple-300" : "bg-primary/20 text-primary"
              )}>
                {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className="space-y-2 flex-1">
                <div className={cn(
                  "p-4 rounded-2xl text-sm leading-relaxed",
                  msg.role === "user" 
                    ? "bg-purple-600 text-white rounded-tr-sm" 
                    : "bg-surface border border-border/50 text-gray-200 rounded-tl-sm"
                )}>
                  {msg.role === "ai" ? (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
                        ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>,
                        ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>,
                        li: ({ children }) => <li className="text-gray-200">{children}</li>,
                        code: ({ children }) => <code className="bg-black/40 px-1.5 py-0.5 rounded text-blue-300 font-mono text-xs">{children}</code>,
                        h1: ({ children }) => <h1 className="text-lg font-bold text-white mt-3 mb-1">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-base font-bold text-white mt-3 mb-1">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-sm font-bold text-white mt-2 mb-1">{children}</h3>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
                
                {msg.role === "ai" && msg.sources && msg.sources.length > 0 && (
                  <div className="flex items-start gap-2 text-xs text-gray-400 bg-black/20 p-2.5 rounded-xl border border-border/30">
                    <BookOpen size={14} className="mt-0.5 text-primary" />
                    <div>
                      <span className="font-medium text-gray-300 mb-1 block">参考知识来源:</span>
                      <ul className="list-disc list-inside space-y-0.5">
                        {msg.sources.map((source, idx) => (
                          <li key={idx} className="truncate max-w-[200px] hover:text-primary transition-colors cursor-default" title={source}>
                            {source}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-4 max-w-[80%] mr-auto"
          >
            <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex-shrink-0 flex items-center justify-center mt-1">
              <Bot size={16} />
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border/50 text-gray-200 rounded-tl-sm flex items-center gap-2">
              <Loader2 size={16} className="animate-spin text-primary" />
              <span className="text-sm">正在检索知识库并思考...</span>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-surface border-t border-border/50 z-10">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="询问知识库中有关的问题..."
            className="w-full bg-black/50 border border-border/50 text-white placeholder:text-gray-500 rounded-full pl-6 pr-14 py-3.5 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2 bg-primary hover:bg-primary-hover disabled:bg-primary/50 disabled:cursor-not-allowed text-white rounded-full transition-colors"
          >
            <Send size={18} className={cn("transform transition-transform", input.trim() ? "translate-x-0.5 -translate-y-0.5" : "")} />
          </button>
        </form>
      </div>
    </div>
  );
}
