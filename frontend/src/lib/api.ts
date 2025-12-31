/**
 * API client for making authenticated requests to the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface ApiOptions {
    method?: HttpMethod;
    body?: unknown;
    headers?: Record<string, string>;
}

interface ApiError extends Error {
    status: number;
    detail: string;
}

function getAccessToken(): string | null {
    const tokens = localStorage.getItem("voiceai_tokens");
    if (tokens) {
        const parsed = JSON.parse(tokens);
        return parsed.access_token;
    }
    return null;
}

/**
 * Make an authenticated API request
 */
export async function apiRequest<T>(
    endpoint: string,
    options: ApiOptions = {}
): Promise<T> {
    const { method = "GET", body, headers = {} } = options;

    const token = getAccessToken();

    const requestHeaders: Record<string, string> = {
        "Content-Type": "application/json",
        ...headers,
    };

    if (token) {
        requestHeaders["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : undefined,
    });

    if (response.status === 401) {
        // Token expired, clear auth and redirect to login
        localStorage.removeItem("voiceai_user");
        localStorage.removeItem("voiceai_tokens");
        window.location.href = "/login";
        throw new Error("Session expired. Please login again.");
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(errorData.detail || "API request failed") as ApiError;
        error.status = response.status;
        error.detail = errorData.detail || "Unknown error";
        throw error;
    }

    return response.json();
}

// Convenience methods
export const api = {
    get: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: "GET" }),
    post: <T>(endpoint: string, body?: unknown) => apiRequest<T>(endpoint, { method: "POST", body }),
    put: <T>(endpoint: string, body?: unknown) => apiRequest<T>(endpoint, { method: "PUT", body }),
    patch: <T>(endpoint: string, body?: unknown) => apiRequest<T>(endpoint, { method: "PATCH", body }),
    delete: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: "DELETE" }),
};

// API endpoint functions
export const assistantsApi = {
    list: () => api.get<{ assistants: unknown[]; count: number }>("/api/assistants"),
    get: (id: string) => api.get<unknown>(`/api/assistants/${id}`),
    create: (data: unknown) => api.post<unknown>("/api/assistants", data),
    update: (id: string, data: unknown) => api.patch<unknown>(`/api/assistants/${id}`, data),
    delete: (id: string) => api.delete<unknown>(`/api/assistants/${id}`),
};

export const campaignsApi = {
    list: () => api.get<{ campaigns: unknown[]; count: number }>("/api/campaigns"),
    get: (id: string) => api.get<unknown>(`/api/campaigns/${id}`),
    create: (data: unknown) => api.post<unknown>("/api/campaigns", data),
    start: (id: string) => api.post<unknown>(`/api/campaigns/${id}/start`),
    pause: (id: string) => api.post<unknown>(`/api/campaigns/${id}/pause`),
    cancel: (id: string) => api.post<unknown>(`/api/campaigns/${id}/cancel`),
    delete: (id: string) => api.delete<unknown>(`/api/campaigns/${id}`),
};

export const callsApi = {
    list: () => api.get<{ calls: unknown[]; count: number }>("/api/calls"),
    get: (id: string) => api.get<unknown>(`/api/calls/${id}`),
    create: (data: unknown) => api.post<unknown>("/api/calls", data),
    getAnalysis: (id: string) => api.get<unknown>(`/api/calls/${id}/analysis`),
};

export const phoneNumbersApi = {
    list: () => api.get<{ phone_numbers: unknown[]; count: number }>("/api/phone-numbers"),
    create: (data: unknown) => api.post<unknown>("/api/phone-numbers", data),
    createInbound: (data: unknown) => api.post<unknown>("/api/phone-numbers/inbound", data),
    delete: (id: string) => api.delete<unknown>(`/api/phone-numbers/${id}`),
};

export const sipConfigsApi = {
    list: () => api.get<{ sip_configs: unknown[]; count: number }>("/api/sip-configs"),
    get: (id: string) => api.get<unknown>(`/api/sip-configs/${id}`),
    create: (data: unknown) => api.post<unknown>("/api/sip-configs", data),
    update: (id: string, data: unknown) => api.patch<unknown>(`/api/sip-configs/${id}`, data),
    delete: (id: string) => api.delete<unknown>(`/api/sip-configs/${id}`),
};

export const analyticsApi = {
    getCalls: () => api.get<unknown>("/api/analytics/calls"),
    getSummary: (days = 7) => api.get<unknown>(`/api/analytics/summary?days=${days}`),
};

export const apiKeysApi = {
    list: () => api.get<unknown[]>("/api/auth/api-keys"),
    create: (name: string) => api.post<unknown>("/api/auth/api-keys", { name }),
    delete: (id: string) => api.delete<unknown>(`/api/auth/api-keys/${id}`),
};
