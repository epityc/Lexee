const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ClientInfo {
  id: number;
  name: string;
  status: string;
  credits: number;
}

interface FormulaMeta {
  name: string;
  description: string;
  category: string;
  variables: {
    name: string;
    label: string;
    type: string;
    required: boolean;
    placeholder: string;
  }[];
}

interface CalculationResponse {
  formula: string;
  result: Record<string, unknown>;
  credits_remaining: number;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body.detail || `Erreur ${res.status}`;
    throw new Error(msg);
  }

  return res.json();
}

export function login(apiKey: string): Promise<ClientInfo> {
  return request<ClientInfo>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ api_key: apiKey }),
  });
}

export function getMe(apiKey: string): Promise<ClientInfo> {
  return request<ClientInfo>("/me", {
    headers: { "X-API-KEY": apiKey },
  });
}

export function getFormulas(
  apiKey: string
): Promise<{ formulas: Record<string, FormulaMeta> }> {
  return request("/formulas", {
    headers: { "X-API-KEY": apiKey },
  });
}

export function calculate(
  apiKey: string,
  formula: string,
  variables: Record<string, unknown>
): Promise<CalculationResponse> {
  return request<CalculationResponse>("/calculate", {
    method: "POST",
    headers: { "X-API-KEY": apiKey },
    body: JSON.stringify({ formula, variables }),
  });
}

export type { ClientInfo, FormulaMeta, CalculationResponse };
