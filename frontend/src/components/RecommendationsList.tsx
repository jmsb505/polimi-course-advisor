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
            <table>
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Course</th>
                        <th>CFU</th>
                        <th>Group</th>
                        <th>Lang</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {recommendations.map((c) => (
                        <tr key={c.code}>
                            <td>{c.code}</td>
                            <td>{c.name}</td>
                            <td>{c.cfu}</td>
                            <td>{c.group}</td>
                            <td>{c.language}</td>
                            <td>{c.score.toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
