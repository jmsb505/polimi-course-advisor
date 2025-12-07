import {
    useRef,
    useEffect,
    useState,
} from "react";
import type { KeyboardEvent, FormEvent } from "react";
import type { ChatMessage } from "../types/chat";

interface ChatPaneProps {
    messages: ChatMessage[];
    isLoading: boolean;
    onSendMessage: (text: string) => void;
    disabled?: boolean;
}

export function ChatPane({
    messages,
    isLoading,
    onSendMessage,
    disabled = false,
}: ChatPaneProps) {
    const [input, setInput] = useState("");
    const messagesEndRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    const handleSubmit = () => {
        if (disabled || isLoading) return;
        const trimmed = input.trim();
        if (!trimmed) return;
        onSendMessage(trimmed);
        setInput("");
    };

    const handleFormSubmit = (event: FormEvent) => {
        event.preventDefault();
        handleSubmit();
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSubmit();
        }
    };

    const placeholder = disabled
        ? "Backend is offline. Start the API service, then reload this page."
        : "Tell me about your interests, dislikes, and goals… (Enter to send, Shift+Enter for a new line)";

    return (
        <div className="chat-pane">
            <div className="chat-messages">
                {messages.map((m, idx) => (
                    <div
                        key={idx}
                        className={`message ${m.role === "user" ? "message-user" : "message-assistant"
                            }`}
                    >
                        <div className="message-role">
                            {m.role === "user" ? "You" : "Advisor"}
                        </div>
                        <div className="message-content">{m.content}</div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message message-assistant message-loading">
                        <div className="message-role">Advisor</div>
                        <div className="message-content">Thinking…</div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>
            <form className="chat-input-row" onSubmit={handleFormSubmit}>
                <textarea
                    className="chat-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    rows={2}
                    disabled={disabled}
                />
                <button
                    type="submit"
                    className="send-button"
                    disabled={disabled || isLoading || !input.trim()}
                >
                    Send
                </button>
            </form>
        </div>
    );
}
