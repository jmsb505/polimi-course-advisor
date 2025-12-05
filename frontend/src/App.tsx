import React, { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  service: string;
  phase: number;
};

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/health");
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data: HealthResponse = await res.json();
        setHealth(data);
      } catch (err: any) {
        setError(err?.message ?? "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <h1>Hello, AI Advisor PoC</h1>
        <p>
          Frontend and backend scaffolds are running. This page also checks the backend
          health endpoint.
        </p>
        <div
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: "0.5rem",
            border: "1px solid #ddd",
            display: "inline-block",
            fontFamily: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
            fontSize: "0.9rem",
          }}
        >
          {loading && <span>Checking backend health...</span>}
          {!loading && error && (
            <span>Backend health error: {error}</span>
          )}
          {!loading && health && (
            <span>
              Backend: {health.status} | service: {health.service} | phase:{" "}
              {health.phase}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;