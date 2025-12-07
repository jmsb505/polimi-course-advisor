export type ChatRole = "system" | "user" | "assistant";

export interface ChatMessage {
    role: ChatRole;
    content: string;
}

export interface StudentProfile {
    interests?: string[];
    avoid?: string[];
    goals?: string[];
    language_preference?: string;      // e.g. "EN" | "IT" | "ANY"
    workload_tolerance?: string;       // e.g. "low" | "medium" | "high"
    preferred_exam_types?: string[];
    liked_courses?: string[];          // course codes
    disliked_courses?: string[];
    // allow extra fields just in case backend evolves
    [key: string]: unknown;
}

export interface RankedCourse {
    code: string;
    name: string;
    cfu: number;
    semester: number;
    language: string;
    group: string;
    score: number;
    // allow additional backend fields without breaking typing
    [key: string]: unknown;
}

export interface ChatRequestPayload {
    messages: ChatMessage[];
    current_profile?: StudentProfile;
}

export interface ChatResponsePayload {
    reply: string;
    updated_profile: StudentProfile;
    recommendations: RankedCourse[];
}
