import { useCallback, useEffect, useRef, useState } from "react";
import {
  getEvents,
  getReport,
  startSimulation,
  subscribeToSimulation,
} from "../lib/api";
import type {
  AgentEvent,
  SimulationReport,
  SimulationStatus,
} from "../lib/types";

const STORAGE_KEY = "axo_simulation_history";
const MAX_HISTORY = 20;

// ── localStorage helpers (simulation ID list only) ──────────

function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveToHistory(simId: string): void {
  const history = loadHistory().filter((id) => id !== simId);
  history.unshift(simId);
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(history.slice(0, MAX_HISTORY))
  );
}

function removeFromHistory(simId: string): void {
  const history = loadHistory().filter((id) => id !== simId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

// ── Hook ────────────────────────────────────────────────────

export function useSimulation() {
  const [status, setStatus] = useState<SimulationStatus>("idle");
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [report, setReport] = useState<SimulationReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>(loadHistory);
  const esRef = useRef<EventSource | null>(null);

  // Sync history from localStorage on mount
  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const start = useCallback(async (url: string) => {
    setEvents([]);
    setReport(null);
    setError(null);
    setStatus("running");

    try {
      const { simulation_id } = await startSimulation(url);
      setSimulationId(simulation_id);

      esRef.current = subscribeToSimulation(
        simulation_id,
        (event) => setEvents((prev) => [...prev, event]),
        async () => {
          try {
            const fullReport = await getReport(simulation_id);
            setReport(fullReport);
            setStatus("completed");
            // Persist ID to localStorage on completion
            saveToHistory(simulation_id);
            setHistory(loadHistory());
          } catch (e) {
            setError(String(e));
            setStatus("error");
          }
        },
        (errMsg) => {
          setError(errMsg);
          setStatus("error");
        }
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStatus("error");
    }
  }, []);

  const loadPastSimulation = useCallback(async (simId: string) => {
    setError(null);
    setSimulationId(simId);

    try {
      const [fullReport, storedEvents] = await Promise.all([
        getReport(simId),
        getEvents(simId).catch(() => [] as AgentEvent[]),
      ]);
      setReport(fullReport);
      setEvents(storedEvents);
      setStatus("completed");
    } catch {
      // Expired in Redis -- remove from localStorage and stay on idle
      removeFromHistory(simId);
      setHistory(loadHistory());
      setSimulationId(null);
      setStatus("idle");
    }
  }, []);

  const reset = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    setStatus("idle");
    setSimulationId(null);
    setEvents([]);
    setReport(null);
    setError(null);
  }, []);

  return {
    status,
    simulationId,
    events,
    report,
    error,
    history,
    start,
    reset,
    loadPastSimulation,
  };
}
