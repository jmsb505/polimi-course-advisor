import type {
    ChatRequestPayload,
    ChatResponsePayload,
} from "../types/chat";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function buildUrl(path: string): string {
    const base = API_BASE_URL.replace(/\/+$/, "");
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    return `${base}${cleanPath}`;
}

export async function getHealth(): Promise<unknown> {
    const res = await fetch(buildUrl("/api/health"));
    if (!res.ok) {
        throw new Error(`Health check failed with status ${res.status}`);
    }
    return res.json();
}

export async function postChat(
    payload: ChatRequestPayload,
): Promise<ChatResponsePayload> {
    const res = await fetch(buildUrl("/api/chat"), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
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
