"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  ImageIcon,
  FileUp,
  Figma,
  MonitorIcon,
  CircleUserRound,
  ArrowUpIcon,
  Paperclip,
  PlusIcon,
} from "lucide-react";
import { runAgent } from "@/lib/api";
import toast from "react-hot-toast";

interface UseAutoResizeTextareaProps {
  minHeight: number;
  maxHeight?: number;
}

function useAutoResizeTextarea({
  minHeight,
  maxHeight,
}: UseAutoResizeTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      if (reset) {
        textarea.style.height = `${minHeight}px`;
        return;
      }

      textarea.style.height = `${minHeight}px`;

      const newHeight = Math.max(
        minHeight,
        Math.min(textarea.scrollHeight, maxHeight ?? Number.POSITIVE_INFINITY)
      );

      textarea.style.height = `${newHeight}px`;
    },
    [minHeight, maxHeight]
  );

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = `${minHeight}px`;
    }
  }, [minHeight]);

  useEffect(() => {
    const handleResize = () => adjustHeight();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [adjustHeight]);

  return { textareaRef, adjustHeight };
}

type ChatMessage = { role: "user" | "assistant"; content: string };

export function VercelV0Chat() {
  const [value, setValue] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 200,
  });

  // Load persisted messages on mount
  useEffect(() => {
    try {
      const raw = typeof window !== "undefined" ? window.localStorage.getItem("dashboardChatMessages") : null;
      if (raw) {
        const parsed = JSON.parse(raw) as ChatMessage[];
        if (Array.isArray(parsed)) setMessages(parsed);
      }
    } catch {}
  }, []);

  // Persist messages and scroll to bottom on update
  useEffect(() => {
    try {
      if (typeof window !== "undefined") {
        window.localStorage.setItem("dashboardChatMessages", JSON.stringify(messages));
      }
    } catch {}
    // scroll to bottom
    const el = listRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    const prompt = value.trim();
    if (!prompt || isSending) return;
    setMessages((m) => [...m, { role: "user", content: prompt }]);
    setValue("");
    adjustHeight(true);
    setIsSending(true);
    try {
      const res = await runAgent("user_chat", prompt);
      const assistantText = typeof res === "string" ? res : JSON.stringify(res, null, 2);
      setMessages((m) => [...m, { role: "assistant", content: assistantText }]);
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      toast.error(`Failed to send: ${message}`);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  return (
    <div className="flex flex-col items-center w-full max-w-4xl mx-auto p-4 space-y-8">
      <h1 className="text-4xl font-bold text-black dark:text-white">
        What can I help you ship?
      </h1>

      <div className="w-full">
        <div className="relative bg-neutral-900 rounded-2xl border border-neutral-800 shadow-lg">
          <div ref={listRef} className="overflow-y-auto max-h-[440px] p-4 space-y-3">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={cn("w-full flex", m.role === "user" ? "justify-end" : "justify-start")}
              >
                <div
                  className={cn(
                    "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                    m.role === "user"
                      ? "bg-blue-600 text-white rounded-br-sm shadow-blue-900/20 shadow"
                      : "bg-neutral-800 text-neutral-200 border border-neutral-700 rounded-bl-sm shadow-black/10 shadow"
                  )}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {isSending && (
              <div className="w-full flex justify-start">
                <div className="bg-neutral-800 text-neutral-300 border border-neutral-700 rounded-2xl rounded-bl-sm px-4 py-2 text-sm shadow-black/10 shadow">
                  <span className="inline-flex items-center gap-2">
                    Thinking
                    <span className="inline-flex gap-1">
                      <span className="w-1 h-1 bg-neutral-400 rounded-full animate-bounce [animation-delay:0ms]"></span>
                      <span className="w-1 h-1 bg-neutral-400 rounded-full animate-bounce [animation-delay:150ms]"></span>
                      <span className="w-1 h-1 bg-neutral-400 rounded-full animate-bounce [animation-delay:300ms]"></span>
                    </span>
                  </span>
                </div>
              </div>
            )}
          </div>
          <div className="overflow-y-auto border-t border-neutral-800">
            <Textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => {
                setValue(e.target.value);
                adjustHeight();
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask v0 a question..."
              className={cn(
                "w-full px-4 py-3",
                "resize-none",
                "bg-transparent",
                "border-none",
                "text-white text-sm",
                "focus:outline-none",
                "focus-visible:ring-0 focus-visible:ring-offset-0",
                "placeholder:text-neutral-500 placeholder:text-sm",
                "min-h-[60px]"
              )}
              style={{ overflow: "hidden" }}
            />
          </div>

          <div className="flex items-center justify-between p-3">
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="group p-2 hover:bg-neutral-800 rounded-xl transition-colors flex items-center gap-1"
              >
                <Paperclip className="w-4 h-4 text-white" />
                <span className="text-xs text-zinc-400 hidden group-hover:inline transition-opacity">
                  Attach
                </span>
              </button>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="px-2 py-1 rounded-xl text-sm text-zinc-400 transition-colors border border-dashed border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800 flex items-center justify-between gap-1"
              >
                <PlusIcon className="w-4 h-4" />
                Project
              </button>
              <button
                type="button"
                className={cn(
                  "px-1.5 py-1.5 rounded-xl text-sm transition-colors border border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800 flex items-center justify-between gap-1",
                  value.trim() && !isSending ? "bg-white text-black shadow" : "text-zinc-400"
                )}
                onClick={() => void sendMessage()}
                disabled={!value.trim() || isSending}
              >
                <ArrowUpIcon
                  className={cn(
                    "w-4 h-4",
                    value.trim() && !isSending ? "text-black" : "text-zinc-400"
                  )}
                />
                <span className="sr-only">Send</span>
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center gap-3 mt-4">
          <ActionButton icon={<ImageIcon className="w-4 h-4" />} label="Clone a Screenshot" />
          <ActionButton icon={<Figma className="w-4 h-4" />} label="Import from Figma" />
          <ActionButton icon={<FileUp className="w-4 h-4" />} label="Upload a Project" />
          <ActionButton icon={<MonitorIcon className="w-4 h-4" />} label="Landing Page" />
          <ActionButton icon={<CircleUserRound className="w-4 h-4" />} label="Sign Up Form" />
        </div>
      </div>
    </div>
  );
}

interface ActionButtonProps {
  icon: React.ReactNode;
  label: string;
}

function ActionButton({ icon, label }: ActionButtonProps) {
  return (
    <button
      type="button"
      className="flex items-center gap-2 px-4 py-2 bg-neutral-900 hover:bg-neutral-800 rounded-full border border-neutral-800 text-neutral-400 hover:text-white transition-colors"
    >
      {icon}
      <span className="text-xs">{label}</span>
    </button>
  );
}


