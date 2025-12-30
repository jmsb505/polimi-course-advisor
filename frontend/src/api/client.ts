import type {
    ChatRequestPayload,
    ChatResponsePayload,
} from "../types/chat";

import { supabase } from "../lib/supabase";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function getAuthHeaders(): Promise<Record<string, string>> {
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    return token ? { "Authorization": `Bearer ${token}` } : {};
}

function buildUrl(path: string): string {
    const base = API_BASE_URL.replace(/\/+$/, "");
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    return `${base}${cleanPath}`;
}

export async function getHealth(): Promise<unknown> {
    const authHeaders = await getAuthHeaders();
    const res = await fetch(buildUrl("/api/health"), {
        headers: authHeaders
    });
    if (!res.ok) {
        throw new Error(`Health check failed with status ${res.status}`);
    }
    return res.json();
}

export async function postChat(
    payload: ChatRequestPayload,
): Promise<ChatResponsePayload> {
    const authHeaders = await getAuthHeaders();
    const res = await fetch(buildUrl("/api/chat"), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...authHeaders,
        },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(
            `Chat request failed with status ${res.status}${text ? `: ${text}` : ""
            }`,
        );
    }

    return (await res.json()) as ChatResponsePayload;
}

export async function getRunSnapshot(
    runId: string,
): Promise<ChatResponsePayload> {
    const authHeaders = await getAuthHeaders();
    const res = await fetch(buildUrl(`/api/runs/${runId}`), {
        headers: authHeaders,
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(
            `Failed to load run ${runId} with status ${res.status}${text ? `: ${text}` : ""
            }`,
        );
    }

    return (await res.json()) as ChatResponsePayload;
}

export async function deleteProfile(): Promise<void> {
    const authHeaders = await getAuthHeaders();
    const res = await fetch(buildUrl("/api/talent/profile"), {
        method: "DELETE",
        headers: authHeaders,
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(
            `Failed to reset profile with status ${res.status}${text ? `: ${text}` : ""
            }`,
        );
    }
}
