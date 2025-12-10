import type { RankedCourse } from "../types/chat";

interface RecommendationsListProps {
    recommendations: RankedCourse[];
    selectedCourseCode?: string | null;
    onSelectCourse?: (code: string) => void;
}

export function RecommendationsList({
    recommendations,
    selectedCourseCode,
    onSelectCourse,
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
            {recommendations.map((c) => {
                const isSelected = c.code === selectedCourseCode;
                const baseStyle = {
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "0.5rem",
                    padding: "0.75rem",
                    marginBottom: "0.75rem",
                    cursor: onSelectCourse ? "pointer" : "default",
                    transition: "all 0.2s ease-in-out"
                };

                const selectedStyle = isSelected ? {
                    backgroundColor: "rgba(245, 158, 11, 0.2)", // amber-900/20 equivalent
                    borderColor: "rgba(251, 191, 36, 0.8)", // amber-400
                    boxShadow: "0 0 10px rgba(251, 191, 36, 0.1)"
                } : {
                    backgroundColor: "rgba(255, 255, 255, 0.05)",
                };

                return (
                    <div
                        key={c.code}
                        className="course-card"
                        style={{ ...baseStyle, ...selectedStyle }}
                        onClick={() => onSelectCourse && onSelectCourse(c.code)}
                    >
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
                                borderTop: isSelected ? "1px solid rgba(251, 191, 36, 0.3)" : "1px solid rgba(255,255,255,0.05)",
                                paddingTop: "0.5rem",
                                marginTop: "0.25rem"
                            }}>
                                {c.explanation}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
