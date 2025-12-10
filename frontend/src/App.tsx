import { useEffect, useState } from "react";
import "./App.css";
import type {
  ChatMessage,
  StudentProfile,
  RankedCourse,
  GraphView,
} from "./types/chat";
import { ChatPane } from "./components/ChatPane";
import { ProfileSummary } from "./components/ProfileSummary";
import { RecommendationsList } from "./components/RecommendationsList";
import { GraphPanel } from "./components/GraphPanel";
import { postChat, getHealth } from "./api/client";

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I’m your course advisor. Tell me what you like, what you hate, and what your goals are, and I’ll suggest PoliMi courses for you.",
    },
  ]);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [recommendations, setRecommendations] = useState<RankedCourse[]>([]);
  const [graphView, setGraphView] = useState<GraphView | null>(null);
  const [selectedCourseCode, setSelectedCourseCode] = useState<string | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        await getHealth();
        if (!cancelled) {
          setBackendOnline(true);
        }
      } catch (err) {
        console.error("API health check failed:", err);
        if (!cancelled) {
          setBackendOnline(false);
          setError((prev) =>
            prev ?? "Backend is not reachable. Make sure the API is running.",
          );
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleSendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (isLoading) return;

    if (backendOnline === false) {
      setError(
        "Backend is offline. Start the API on the backend and reload this page.",
      );
      return;
    }

    setError(null);

    const userMessage: ChatMessage = {
      role: "user",
      content: trimmed,
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await postChat({
        messages: newMessages,
        current_profile: profile ?? undefined,
      });

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.reply,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setProfile(response.updated_profile ?? null);
      setRecommendations(response.recommendations ?? []);
      setGraphView(response.graph_view ?? null);
      setSelectedCourseCode(null);
    } catch (err) {
      console.error("Chat error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while talking to the advisor.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const statusLabel =
    backendOnline === null
      ? "Checking API…"
      : backendOnline
        ? "API online"
        : "API offline";

  const statusClass =
    backendOnline === null
      ? "status-unknown"
      : backendOnline
        ? "status-online"
        : "status-offline";

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-main">
          <h1>PoliMi Course Advisor (PoC)</h1>
          <p className="app-subtitle">
            Chat about your interests and see tailored course suggestions for
            the first semester.
          </p>
        </div>
        <div className={`backend-status ${statusClass}`}>
          <span className="dot" />
          <span className="status-text">{statusLabel}</span>
        </div>
      </header>
      <main className="main-layout">
        <section className="chat-section panel">
          <div className="panel-header">
            <h2>Chat</h2>
          </div>
          {error && <div className="error-banner">{error}</div>}
          <ChatPane
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            disabled={backendOnline === false}
          />
        </section>
        <aside className="context-section">
          <section className="panel">
            <div className="panel-header">
              <h2>Your profile</h2>
            </div>
            <ProfileSummary profile={profile} />
          </section>
          <section className="panel" style={{ flex: 1.5 }}>
            <div className="panel-header">
              <h2>Course Graph</h2>
            </div>
            <GraphPanel
              graphView={graphView}
              selectedCourseCode={selectedCourseCode}
              onSelectCourse={setSelectedCourseCode}
            />
          </section>
          <section className="panel" style={{ flex: 2 }}>
            <div className="panel-header">
              <h2>Recommended courses</h2>
            </div>
            <RecommendationsList
              recommendations={recommendations}
              selectedCourseCode={selectedCourseCode}
              onSelectCourse={setSelectedCourseCode}
            />
          </section>
        </aside>
      </main>
    </div>
  );
}

export default App;
