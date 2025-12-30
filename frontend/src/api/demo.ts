import type { DemoCompany, RankedCandidate } from "../types/demo";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function buildUrl(path: string): string {
    const base = API_BASE_URL.replace(/\/+$/, "");
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    return `${base}${cleanPath}`;
}

export async function getDemoCompanies(): Promise<DemoCompany[]> {
    const res = await fetch(buildUrl("/api/demo/companies"));
    if (!res.ok) {
        throw new Error(`Failed to fetch demo companies: ${res.status}`);
    }
    return res.json();
}

export async function getRankedCandidates(companyId: string): Promise<RankedCandidate[]> {
    const res = await fetch(buildUrl(`/api/demo/companies/${companyId}/candidates`));
    if (!res.ok) {
        throw new Error(`Failed to fetch ranked candidates: ${res.status}`);
    }
    return res.json();
}
