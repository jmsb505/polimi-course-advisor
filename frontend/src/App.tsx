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
import { DEMO_SCENARIOS } from "./demo/scenarios";
import { supabase } from "./lib/supabase";
import { LoginPage } from "./components/LoginPage";
import { CompanyDemoView } from "./components/CompanyDemoView";
import type { DemoCompany } from "./types/demo";
import type { Session } from "@supabase/supabase-js";

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [selectedDemoCompany, setSelectedDemoCompany] = useState<DemoCompany | null>(null);
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

    getHealth()
      .then((data: unknown) => {
        if (!cancelled && data && typeof data === "object" && "database" in data) {
          setBackendOnline((data as { database: string }).database === "ok");
        }
      })
      .catch(() => {
        if (!cancelled) setBackendOnline(false);
      });

    return () => {
      cancelled = true;
    };
  }, [session]);

  const handleSendMessage = async (text: string) => {
    setIsLoading(true);
    setError(null);

    const newMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: text },
    ];
    setMessages(newMessages);

    try {
      const resp = await postChat({ messages: newMessages });
      setMessages([...newMessages, { role: "assistant", content: resp.reply }]);
      setProfile(resp.updated_profile);
      setRecommendations(resp.recommendations);
      setGraphView(resp.graph_view || null);

      if (resp.run_id) {
        setLastRunId(resp.run_id);
        localStorage.setItem("lastRunId", resp.run_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReplayLastRun = async () => {
    if (!lastRunId) return;
    setIsLoading(true);
    setError(null);
    try {
      const resp = await getRunSnapshot(lastRunId);
      setMessages([
        {
          role: "assistant",
          content: "Replayed last advisor snapshot:",
        },
        { role: "assistant", content: resp.reply },
      ]);
      setProfile(resp.updated_profile);
      setRecommendations(resp.recommendations);
      setGraphView(resp.graph_view || null);
    } catch (_err) {
      setError("Failed to replay run");
    } finally {
      setIsLoading(false);
    }
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
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading PoliMi Course Advisor...</p>
      </div>
    );
  }

  if (!session) {
    if (selectedDemoCompany) {
      return (
        <CompanyDemoView
          company={selectedDemoCompany}
          onBack={() => setSelectedDemoCompany(null)}
        />
      );
    }
    return <LoginPage onSelectCompany={setSelectedDemoCompany} />;
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-left">
          <h1>PoliMi Course Advisor</h1>
          {backendOnline === false && (
            <span className="badge error">Backend Offline</span>
          )}
          {backendOnline === true && (
            <span className="badge success">Database Ready</span>
          )}
        </div>
        <div className="header-actions">
          <button className="new-chat-btn" onClick={handleNewChat} disabled={isLoading}>
            New Chat
          </button>
          {lastRunId && (
            <button
              className="replay-btn"
              onClick={handleReplayLastRun}
              disabled={isLoading}
            >
              Replay Last
            </button>
          )}
          <div className="demo-group">
            <span className="demo-label">Demo:</span>
            {DEMO_SCENARIOS.map((s) => (
              <button
                key={s.label}
                className="demo-btn"
                onClick={() => handleSendMessage(s.initialMessage)}
                disabled={isLoading}
              >
                {s.label}
              </button>
            ))}
          </div>
          <button className="signout-btn" onClick={handleSignOut}>
            Sign Out
          </button>
        </div>
      </header>

      <main className="main-layout">
        <section className="chat-section">
          <ChatPane
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </section>

        <section className="context-section">
          <div className="context-card profile">
            <h3>Student Profile</h3>
            <ProfileSummary profile={profile} />
          </div>
          <div className="context-card graph">
            <GraphPanel
              graphView={graphView}
              selectedCourseCode={selectedCourseCode}
              onSelectCourse={setSelectedCourseCode}
            />
          </div>
          <div className="context-card recommendations">
            <h3>Recommendations</h3>
            <RecommendationsList
              recommendations={recommendations}
              selectedCourseCode={selectedCourseCode}
              onSelectCourse={setSelectedCourseCode}
            />
          </div>
        </section>
      </main>

      {error && <div className="toast error">{error}</div>}
    </div>
  );
}

export default App;
