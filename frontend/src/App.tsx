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
import { postChat, getHealth, getRunSnapshot, deleteProfile } from "./api/client";
import { DEMO_SCENARIOS, type DemoScenario } from "./demo/scenarios";
import type { ChatResponsePayload } from "./types/chat";
import { supabase } from "./lib/supabase";
import { LoginPage } from "./components/LoginPage";
import type { Session } from "@supabase/supabase-js";

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
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
  const [lastRunId, setLastRunId] = useState<string | null>(() => localStorage.getItem("lastRunId"));

  // Check auth session
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setAuthLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!session) return;
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
  }, [session]);

  const updateStateFromResponse = (response: ChatResponsePayload, appendMessage: boolean = true) => {
    if (appendMessage) {
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.reply,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }
    setProfile(response.updated_profile ?? null);
    setRecommendations(response.recommendations ?? []);
    setGraphView(response.graph_view ?? null);
    setSelectedCourseCode(null);

    if (response.run_id) {
      setLastRunId(response.run_id);
      localStorage.setItem("lastRunId", response.run_id);
    }
  };

  const handleSendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (isLoading) return;

    if (backendOnline === false) {
      setError("Backend is offline. Start the API on the backend and reload this page.");
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
      updateStateFromResponse(response);
    } catch (err) {
      console.error("Chat error:", err);
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReplayLastRun = async () => {
    if (!lastRunId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await getRunSnapshot(lastRunId);
      // For replay, we just replace current state
      setMessages([{ role: "assistant", content: `(Replayed run ${lastRunId}) ${response.reply}` }]);
      updateStateFromResponse(response, false);
    } catch (err) {
      console.error("Replay error:", err);
      setError("Failed to replay last run.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunScenario = (scenario: DemoScenario) => {
    handleSendMessage(scenario.initialMessage);
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  const handleNewChat = async () => {
    setIsLoading(true);
    try {
      await deleteProfile();
    } catch (err) {
      console.error("Failed to reset profile in backend:", err);
      // We still clear local state even if backend fails
    } finally {
      setIsLoading(false);
    }

    setMessages([
      {
        role: "assistant",
        content:
          "Hi! I’m your course advisor. Tell me what you like, what you hate, and what your goals are, and I’ll suggest PoliMi courses for you.",
      },
    ]);
    setProfile(null);
    setRecommendations([]);
    setGraphView(null);
    setSelectedCourseCode(null);
    setError(null);
  };

  if (authLoading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!session) {
    return <LoginPage />;
  }

  const statusLabel =
    backendOnline === null ? "Checking API…" : backendOnline ? "API online" : "API offline";

  const statusClass =
    backendOnline === null ? "status-unknown" : backendOnline ? "status-online" : "status-offline";

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-main">
          <h1>PoliMi Course Advisor</h1>
          <div className="demo-controls">
            <span className="demo-label">Demos:</span>
            {DEMO_SCENARIOS.map((s) => (
              <button key={s.id} onClick={() => handleRunScenario(s)} disabled={isLoading} className="demo-btn">
                {s.label}
              </button>
            ))}
            {lastRunId && (
              <button onClick={handleReplayLastRun} disabled={isLoading} className="replay-btn">
                Replay Last Run
              </button>
            )}
            <button onClick={handleNewChat} disabled={isLoading} className="new-chat-btn">
              New Chat
            </button>
            <button onClick={handleSignOut} className="signout-btn">
              Sign Out
            </button>
          </div>
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
