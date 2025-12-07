import type { StudentProfile } from "../types/chat";

interface ProfileSummaryProps {
    profile: StudentProfile | null;
}

function renderChipList(label: string, items?: string[]) {
    if (!items || items.length === 0) return null;
    return (
        <div className="profile-row">
            <span className="profile-label">{label}</span>
            <div className="profile-chips">
                {items.map((item) => (
                    <span key={item} className="chip">
                        {item}
                    </span>
                ))}
            </div>
        </div>
    );
}

export function ProfileSummary({ profile }: ProfileSummaryProps) {
    if (!profile) {
        return (
            <p className="profile-empty">
                No profile yet. Start chatting on the left and I&apos;ll infer your
                preferences here.
            </p>
        );
    }

    return (
        <div className="profile-summary">
            {renderChipList("Interests", profile.interests)}
            {renderChipList("Avoid", profile.avoid)}
            {renderChipList("Goals", profile.goals)}
            {profile.language_preference && (
                <div className="profile-row">
                    <span className="profile-label">Language</span>
                    <span className="chip">
                        {profile.language_preference.toUpperCase()}
                    </span>
                </div>
            )}
            {profile.workload_tolerance && (
                <div className="profile-row">
                    <span className="profile-label">Workload</span>
                    <span className="chip">
                        {profile.workload_tolerance.toLowerCase()}
                    </span>
                </div>
            )}
            {renderChipList("Preferred exams", profile.preferred_exam_types)}
            {renderChipList("Liked courses", profile.liked_courses)}
            {renderChipList("Disliked courses", profile.disliked_courses)}
        </div>
    );
}
