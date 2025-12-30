export interface DemoCompany {
    id: string;
    name: string;
    industry: string;
    tagline: string;
}

export interface RankedCandidate {
    public_handle: string;
    skills: string[];
    interests: string[];
    goals: string[];
    preferred_roles: string[];
    language_preferences: string[];
    score: number;
    matched_terms: string[];
}
