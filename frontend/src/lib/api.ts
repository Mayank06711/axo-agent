import type {
  AgentEvent,
  APIResponse,
  SimulationReport,
  SimulationStartResponse,
} from "./types";

const API_BASE = "/api";

// SSE connects directly to backend to avoid Vite proxy buffering issues.
// In production, both are served from same origin so this falls back to /api.
const SSE_BASE = import.meta.env.VITE_SSE_BASE || API_BASE;

// ── Generic request helper ──────────────────────────────────

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<APIResponse<T>> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const json: APIResponse<T> = await res.json();

  if (!res.ok || json.status_code >= 400) {
    throw new Error(json.message || `Request failed: ${res.status}`);
  }

  return json;
}

// ── API functions ───────────────────────────────────────────

export async function startSimulation(url: string): Promise<SimulationStartResponse> {
  const res = await request<SimulationStartResponse>("/simulate", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
  return res.data!;
}

export async function getReport(simulationId: string): Promise<SimulationReport> {
  const res = await request<SimulationReport>(`/simulate/${simulationId}`);
  return res.data!;
}

export async function getEvents(simulationId: string): Promise<AgentEvent[]> {
  const res = await request<AgentEvent[]>(`/simulate/${simulationId}/events`);
  return res.data || [];
}

// ── SSE subscription ────────────────────────────────────────

export function subscribeToSimulation(
  simulationId: string,
  onEvent: (event: AgentEvent) => void,
  onComplete: () => void,
  onError: (error: string) => void
): EventSource {
  const url = `${SSE_BASE}/simulate/${simulationId}/stream`;
  const es = new EventSource(url);
  let receivedAny = false;
  let closed = false;

  es.onmessage = (e) => {
    try {
      const event: AgentEvent = JSON.parse(e.data);
      receivedAny = true;
      onEvent(event);

      if (
        event.event_type === "SIMULATION_COMPLETE" ||
        event.event_type === "SIMULATION_ERROR"
      ) {
        closed = true;
        es.close();
        if (event.event_type === "SIMULATION_COMPLETE") {
          onComplete();
        } else {
          onError(String(event.data?.error || "Simulation failed"));
        }
      }
    } catch {
      // Heartbeat comments or unparseable data — ignore
    }
  };

  es.onerror = () => {
    // EventSource fires onerror on reconnect attempts too.
    // Only treat as fatal if readyState is CLOSED (browser gave up).
    if (!closed && es.readyState === EventSource.CLOSED) {
      es.close();
      if (!receivedAny) {
        onError("Could not connect to simulation stream");
      } else {
        onError("Connection to server lost during simulation");
      }
    }
  };

  return es;
}
