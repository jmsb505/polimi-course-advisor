import type { RankedCourse } from "../types/chat";

interface RecommendationsListProps {
    recommendations: RankedCourse[];
}

export function RecommendationsList({
    recommendations,
}: RecommendationsListProps) {
    if (!recommendations || recommendations.length === 0) {
        return (
            <p className="recommendations-empty">
                No recommendations yet. Once you send a message, suggested courses will appear here.
            </p>
        );
    }

    return (
        <div className="recommendations-list">
            {recommendations.map((c) => (
                <div key={c.code} className="course-card" style={{
                    backgroundColor: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "0.5rem",
                    padding: "0.75rem",
                    marginBottom: "0.75rem"
                }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.25rem" }}>
                        <div style={{ fontWeight: "600", color: "#fff" }}>{c.name}</div>
                        <div style={{ fontSize: "0.75rem", color: "#bbb", fontFamily: "monospace" }}>{c.code}</div>
                    </div>

                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", fontSize: "0.75rem", color: "#999", marginBottom: "0.5rem" }}>
                        <span>Score: {c.score.toFixed(2)}</span>
                        <span>•</span>
                        <span>{c.cfu} CFU</span>
                        <span>•</span>
                        <span>{c.group || "Gen"}</span>
                        <span>•</span>
                        <span>{c.language}</span>
                    </div>

                    {c.explanation && (
                        <div style={{
                            fontSize: "0.85rem",
                            color: "#ddd",
                            lineHeight: "1.4",
                            borderTop: "1px solid rgba(255,255,255,0.05)",
                            paddingTop: "0.5rem",
                            marginTop: "0.25rem"
                        }}>
                            {c.explanation}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}

// Add simple CSS for scrollable list if needed or assume App.css handles .recommendations-list overflow
