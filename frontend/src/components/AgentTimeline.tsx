import { useEffect, useRef, useState } from "react";
import type { AgentEvent } from "../lib/types";

interface AgentTimelineProps {
  events: AgentEvent[];
  isStreaming: boolean;
}

function EventDot({ type }: { type: string }) {
  if (type === "TASK_START")
    return <div className="h-3 w-3 rounded-full bg-blue-500 animate-pulse ring-4 ring-blue-500/20" />;
  if (type === "TASK_COMPLETE")
    return <div className="h-3 w-3 rounded-full bg-emerald-500" />;
  if (type === "TASK_ERROR")
    return <div className="h-3 w-3 rounded-full bg-red-500" />;
  if (type === "TOOL_CALL")
    return <div className="h-2.5 w-2.5 rounded-full bg-violet-500" />;
  if (type === "TOOL_RESULT")
    return <div className="h-2.5 w-2.5 rounded-full bg-violet-400" />;
  if (type === "LLM_THINKING")
    return <div className="h-2 w-2 rounded-full bg-gray-500" />;
  if (type === "STANDARDS_CHECK_RESULT")
    return <div className="h-2.5 w-2.5 rounded-full bg-sky-400" />;
  return <div className="h-2 w-2 rounded-full bg-gray-600" />;
}

function cleanText(raw: string): string {
  let text = raw;

  // Strip JSON fragments that leak from structured output
  // Match patterns like "findings":[{...}] or {"content":"...",...}
  text = text.replace(/[{[]["']?(found|confidence|findings|issues|summary|content|source_url)["']?\s*[:=].*$/s, "");

  // Strip content='...' wrapper from tool results
  text = text.replace(/^content='(.*)'$/s, "$1");
  text = text.replace(/^content="(.*)"$/s, "$1");

  // Strip markdown bold/italic
  text = text.replace(/\*\*(.*?)\*\*/g, "$1");
  text = text.replace(/\*(.*?)\*/g, "$1");

  // Strip escape sequences
  text = text.replace(/\\n/g, " ");
  text = text.replace(/\\t/g, " ");
  text = text.replace(/\\r/g, "");
  text = text.replace(/\\"/g, '"');
  text = text.replace(/\n/g, " ");

  // Collapse whitespace
  text = text.replace(/\s{2,}/g, " ");

  return text.trim();
}

function formatEvent(event: AgentEvent): string {
  const d = event.data;
  switch (event.event_type) {
    case "SIMULATION_START":
      return `Starting simulation for ${d.url}`;
    case "TASK_START":
      return String(d.task_display_name);
    case "TOOL_CALL":
      return `Calling ${d.tool}${d.input && d.input !== "{}" ? `: ${cleanText(String(d.input)).slice(0, 80)}` : ""}`;
    case "TOOL_RESULT": {
      let out = String(d.output);
      // Extract content from LangChain ToolMessage repr: content='actual text' name=...
      const match = out.match(/content=['"](.+?)['"](?:\s+name=|\s*$)/s);
      if (match) out = match[1];
      return `${d.tool} returned: ${cleanText(out).slice(0, 150)}`;
    }
    case "LLM_THINKING":
      return cleanText(String(d.text));
    case "TASK_COMPLETE":
      return `${d.found ? "Found" : "Not found"} -- confidence: ${d.confidence} (${d.tool_calls_used} steps)`;
    case "TASK_ERROR":
      return `Error: ${d.error}`;
    case "STANDARDS_CHECK_START":
      return "Running standards checks...";
    case "STANDARDS_CHECK_RESULT":
      return `${d.check_name}: ${d.score}/100`;
    case "STANDARDS_CHECK_DONE":
      return "Standards checks complete";
    case "SIMULATION_COMPLETE":
      return `Score: ${d.overall_score} -- Grade: ${d.grade} (${d.duration_seconds}s)`;
    case "SIMULATION_ERROR":
      return `Simulation failed: ${d.error}`;
    default:
      return JSON.stringify(d);
  }
}

function fullEventText(event: AgentEvent): string {
  const d = event.data;
  if (event.event_type === "TOOL_RESULT") {
    let out = String(d.output);
    const match = out.match(/content=['"](.+?)['"](?:\s+name=|\s*$)/s);
    if (match) out = match[1];
    return `${d.tool} returned: ${cleanText(out)}`;
  }
  if (event.event_type === "LLM_THINKING") return cleanText(String(d.text));
  return formatEvent(event);
}

const TRUNCATE_LIMIT = 150;

function isMainEvent(type: string): boolean {
  return [
    "TASK_START", "TASK_COMPLETE", "TASK_ERROR",
    "SIMULATION_START", "SIMULATION_COMPLETE", "SIMULATION_ERROR",
    "STANDARDS_CHECK_START", "STANDARDS_CHECK_DONE",
  ].includes(type);
}

function ExpandableText({ event }: { event: AgentEvent }) {
  const [expanded, setExpanded] = useState(false);
  const short = formatEvent(event);
  const full = fullEventText(event);
  const isLong = full.length > TRUNCATE_LIMIT;
  const main = isMainEvent(event.event_type);

  return (
    <div className="min-w-0 flex-1">
      <p className={`text-xs leading-relaxed ${
        main ? "text-gray-200 font-medium" : "text-gray-400"
      } ${event.event_type === "LLM_THINKING" ? "italic text-gray-500" : ""}`}>
        {expanded ? full : short}
        {isLong && !expanded && (
          <button
            onClick={() => setExpanded(true)}
            className="ml-1.5 text-blue-400 hover:text-blue-300 transition-colors"
          >
            ...more
          </button>
        )}
        {isLong && expanded && (
          <button
            onClick={() => setExpanded(false)}
            className="ml-1.5 text-blue-400 hover:text-blue-300 transition-colors"
          >
            less
          </button>
        )}
      </p>
    </div>
  );
}

export function AgentTimeline({ events, isStreaming }: AgentTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  if (events.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-800 bg-gray-900">
        <div className="flex gap-1.5">
          <div className="h-3 w-3 rounded-full bg-red-500/80" />
          <div className="h-3 w-3 rounded-full bg-amber-500/80" />
          <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
        </div>
        <span className="text-xs text-gray-500 font-mono ml-2">agent output</span>
        {isStreaming && (
          <div className="ml-auto flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-emerald-400">Live</span>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div ref={scrollRef} className="p-4 max-h-96 overflow-y-auto">
        <div className="relative">
          <div className="absolute left-[5px] top-0 bottom-0 w-px bg-gray-800" />

          <div className="space-y-2">
            {events.map((event, i) => {
              const main = isMainEvent(event.event_type);
              return (
                <div key={i} className={`relative flex gap-3 ${main ? "pl-0" : "pl-4"}`}>
                  <div className={`flex-shrink-0 mt-1.5 ${main ? "" : "ml-0.5"}`}>
                    <EventDot type={event.event_type} />
                  </div>
                  <ExpandableText event={event} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
