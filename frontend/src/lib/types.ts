// ── Standard API response (matches backend APIResponse) ──

export interface ResponseMetadata {
  request_id: string;
  timestamp: string;
}

export interface APIResponse<T = unknown> {
  status_code: number;
  message: string;
  data: T | null;
  metadata: ResponseMetadata;
}

// ── Simulation request / response ──

export interface SimulationStartResponse {
  simulation_id: string;
  status: string;
  stream_url: string;
}

// ── SSE events (matches backend AgentEvent) ──

export type EventType =
  | "SIMULATION_START"
  | "SIMULATION_COMPLETE"
  | "SIMULATION_ERROR"
  | "TASK_START"
  | "TASK_COMPLETE"
  | "TASK_ERROR"
  | "TOOL_CALL"
  | "TOOL_RESULT"
  | "LLM_THINKING"
  | "STANDARDS_CHECK_START"
  | "STANDARDS_CHECK_RESULT"
  | "STANDARDS_CHECK_DONE";

export interface AgentEvent {
  simulation_id: string;
  timestamp: string;
  event_type: EventType;
  task_name: string | null;
  agent_name: string | null;
  data: Record<string, unknown>;
}

// ── Task result (matches backend TaskResult) ──

export interface TaskResult {
  task_name: string;
  found: boolean;
  confidence: number;
  accessibility: number;
  data_quality: number;
  score: number;
  findings: string[];
  issues: string[];
  steps_taken: number;
  raw_data: Record<string, unknown>;
}

// ── Standards check result ──

export interface StandardsCheckResult {
  check_name: string;
  score: number;
  details: Record<string, unknown>;
  issues: string[];
}

// ── Full simulation report ──

export interface SimulationReport {
  simulation_id: string;
  url: string;
  status: string;
  overall_score: number;
  grade: string;
  task_results: TaskResult[];
  standards_results: StandardsCheckResult[];
  issues: string[];
  recommendations: string[];
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  llm_provider: string;
  llm_model: string;
}

// ── Frontend state ──

export type SimulationStatus = "idle" | "running" | "completed" | "error";
